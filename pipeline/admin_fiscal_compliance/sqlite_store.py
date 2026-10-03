"""Durable AO-22 provider selection and compliance evidence store."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_fiscal_compliance import (
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
        )

    @staticmethod
    def _evidence_payload(evidence: FiscalComplianceEvidence) -> str:
        return json.dumps(
            {
                "evidence_id": evidence.evidence_id,
                "integration_id": evidence.integration_id,
                "kind": evidence.kind.value,
                "provider_version": evidence.provider_version,
                "observed_at": evidence.observed_at.isoformat(),
                "source_ref": evidence.source_ref,
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
                    evidence.provider_version,
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
                    provider_version=payload["provider_version"],
                    observed_at=datetime.fromisoformat(payload["observed_at"]),
                    source_ref=payload["source_ref"],
                    artifact_fingerprint=payload["artifact_fingerprint"],
                )
            )
        return tuple(result)
