"""Durable AO-22 provider selection and compliance evidence store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_fiscal_compliance import (
    FiscalApprovalDecision,
    FiscalApprovalEvent,
    FiscalArchitectureRoute,
    FiscalComplianceEvidence,
    FiscalEvidenceKind,
    FiscalProviderSelection,
)


class FiscalComplianceStoreConflict(ValueError):
    pass


class SqliteFiscalComplianceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS fiscal_provider_selection (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fiscal_compliance_evidence (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    evidence_id TEXT NOT NULL UNIQUE,
                    integration_id TEXT NOT NULL,
                    provider_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fiscal_approval_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    approval_event_id TEXT NOT NULL UNIQUE,
                    integration_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _selection_payload(selection: FiscalProviderSelection) -> str:
        return json.dumps(
            {
                "selection_id": selection.selection_id,
                "integration_id": selection.integration_id,
                "route": selection.route.value,
                "selected_at": selection.selected_at.isoformat(),
                "decision_ref": selection.decision_ref,
                "provider_product_version": selection.provider_product_version,
                "adapter_version": selection.adapter_version,
                "integration_definition_version": selection.integration_definition_version,
                "ruleset_id": selection.ruleset_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def put_selection(self, selection: FiscalProviderSelection) -> bool:
        payload = self._selection_payload(selection)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM fiscal_provider_selection WHERE singleton = 1"
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise FiscalComplianceStoreConflict(
                    "SIF provider selection is immutable; change requires new governed migration"
                )
            connection.execute(
                "INSERT INTO fiscal_provider_selection(singleton, payload_json) VALUES (1, ?)",
                (payload,),
            )
        return True

    def selection(self) -> FiscalProviderSelection | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM fiscal_provider_selection WHERE singleton = 1"
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(str(row["payload_json"]))
        return FiscalProviderSelection(
            selection_id=payload["selection_id"],
            integration_id=payload["integration_id"],
            route=FiscalArchitectureRoute(payload["route"]),
            selected_at=datetime.fromisoformat(payload["selected_at"]),
            decision_ref=payload["decision_ref"],
            provider_product_version=payload["provider_product_version"],
            adapter_version=payload["adapter_version"],
            integration_definition_version=int(payload["integration_definition_version"]),
            ruleset_id=payload["ruleset_id"],
        )

    @staticmethod
    def _evidence_payload(evidence: FiscalComplianceEvidence) -> str:
        return json.dumps(
            {
                "evidence_id": evidence.evidence_id,
                "integration_id": evidence.integration_id,
                "kind": evidence.kind.value,
                "provider_product_version": evidence.provider_product_version,
                "adapter_version": evidence.adapter_version,
                "integration_definition_version": evidence.integration_definition_version,
                "ruleset_id": evidence.ruleset_id,
                "observed_at": evidence.observed_at.isoformat(),
                "source_ref": evidence.source_ref,
                "artifact_ref": evidence.artifact_ref,
                "artifact_fingerprint": evidence.artifact_fingerprint,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_evidence(self, evidence: FiscalComplianceEvidence) -> bool:
        payload = self._evidence_payload(evidence)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM fiscal_compliance_evidence WHERE evidence_id = ?",
                (evidence.evidence_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise FiscalComplianceStoreConflict(
                    "fiscal evidence id reused with different content"
                )
            connection.execute(
                "INSERT INTO fiscal_compliance_evidence("
                "evidence_id, integration_id, provider_version, payload_json"
                ") VALUES (?, ?, ?, ?)",
                (
                    evidence.evidence_id,
                    evidence.integration_id,
                    evidence.provider_product_version,
                    payload,
                ),
            )
        return True

    def evidence(self) -> tuple[FiscalComplianceEvidence, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM fiscal_compliance_evidence ORDER BY sequence"
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            result.append(
                FiscalComplianceEvidence(
                    evidence_id=payload["evidence_id"],
                    integration_id=payload["integration_id"],
                    kind=FiscalEvidenceKind(payload["kind"]),
                    provider_product_version=payload["provider_product_version"],
                    adapter_version=payload["adapter_version"],
                    integration_definition_version=int(payload["integration_definition_version"]),
                    ruleset_id=payload["ruleset_id"],
                    observed_at=datetime.fromisoformat(payload["observed_at"]),
                    source_ref=payload["source_ref"],
                    artifact_ref=payload["artifact_ref"],
                    artifact_fingerprint=payload["artifact_fingerprint"],
                )
            )
        return tuple(result)

    @staticmethod
    def _approval_payload(event: FiscalApprovalEvent) -> str:
        return json.dumps(
            {
                "approval_event_id": event.approval_event_id,
                "integration_id": event.integration_id,
                "provider_product_version": event.provider_product_version,
                "adapter_version": event.adapter_version,
                "integration_definition_version": event.integration_definition_version,
                "ruleset_id": event.ruleset_id,
                "decision": event.decision.value,
                "occurred_at": event.occurred_at.isoformat(),
                "actor_ref": event.actor_ref,
                "decision_ref": event.decision_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_approval(self, event: FiscalApprovalEvent) -> bool:
        payload = self._approval_payload(event)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM fiscal_approval_events WHERE approval_event_id = ?",
                (event.approval_event_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise FiscalComplianceStoreConflict(
                    "fiscal approval event id reused with different content"
                )
            connection.execute(
                "INSERT INTO fiscal_approval_events("
                "approval_event_id, integration_id, occurred_at, payload_json"
                ") VALUES (?, ?, ?, ?)",
                (
                    event.approval_event_id,
                    event.integration_id,
                    event.occurred_at.isoformat(),
                    payload,
                ),
            )
        return True

    def approvals(self) -> tuple[FiscalApprovalEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM fiscal_approval_events ORDER BY sequence"
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            result.append(
                FiscalApprovalEvent(
                    approval_event_id=payload["approval_event_id"],
                    integration_id=payload["integration_id"],
                    provider_product_version=payload["provider_product_version"],
                    adapter_version=payload["adapter_version"],
                    integration_definition_version=int(payload["integration_definition_version"]),
                    ruleset_id=payload["ruleset_id"],
                    decision=FiscalApprovalDecision(payload["decision"]),
                    occurred_at=datetime.fromisoformat(payload["occurred_at"]),
                    actor_ref=payload["actor_ref"],
                    decision_ref=payload["decision_ref"],
                )
            )
        return tuple(result)
