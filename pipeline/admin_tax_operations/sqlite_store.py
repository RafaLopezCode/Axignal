"""SQLite persistence for AO-23 tax operations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_tax_operations import (
    TaxApplicabilityState,
    TaxEvidence,
    TaxEvidenceKind,
    TaxObligation,
    TaxPeriodicity,
    TaxRuleDefinition,
)


class TaxOperationsStoreConflict(ValueError):
    pass


class SqliteTaxOperationsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tax_rules (
                    rule_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tax_obligations (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    obligation_id TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tax_evidence (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    evidence_id TEXT NOT NULL UNIQUE,
                    obligation_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_tax_evidence_obligation
                    ON tax_evidence(obligation_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _insert_immutable(
        connection: sqlite3.Connection,
        *,
        table: str,
        key: str,
        value: str,
        payload: str,
    ) -> bool:
        row = connection.execute(
            f"SELECT payload_json FROM {table} WHERE {key} = ?",
            (value,),
        ).fetchone()
        if row is not None:
            if str(row["payload_json"]) == payload:
                return False
            raise TaxOperationsStoreConflict(f"{table} identity reused with different content")
        connection.execute(
            f"INSERT INTO {table}({key}, payload_json) VALUES (?, ?)",
            (value, payload),
        )
        return True

    def append_rule(self, rule: TaxRuleDefinition) -> bool:
        payload = json.dumps(
            {
                "rule_id": rule.rule_id,
                "jurisdiction": rule.jurisdiction,
                "model_code": rule.model_code,
                "periodicity": rule.periodicity.value,
                "effective_at": rule.effective_at.isoformat(),
                "deadline_policy": rule.deadline_policy,
                "applicability_policy": rule.applicability_policy,
                "source_refs": list(rule.source_refs),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            return self._insert_immutable(
                connection, table="tax_rules", key="rule_id", value=rule.rule_id, payload=payload
            )

    def rules(self) -> tuple[TaxRuleDefinition, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM tax_rules ORDER BY rule_id"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                TaxRuleDefinition(
                    rule_id=p["rule_id"],
                    jurisdiction=p["jurisdiction"],
                    model_code=p["model_code"],
                    periodicity=TaxPeriodicity(p["periodicity"]),
                    effective_at=datetime.fromisoformat(p["effective_at"]),
                    deadline_policy=p["deadline_policy"],
                    applicability_policy=p["applicability_policy"],
                    source_refs=tuple(p["source_refs"]),
                )
            )
        return tuple(result)

    def append_obligation(self, obligation: TaxObligation) -> bool:
        payload = json.dumps(
            {
                "obligation_id": obligation.obligation_id,
                "taxpayer_ref": obligation.taxpayer_ref,
                "rule_id": obligation.rule_id,
                "model_code": obligation.model_code,
                "period_start": obligation.period_start.isoformat(),
                "period_end": obligation.period_end.isoformat(),
                "due_at": obligation.due_at.isoformat(),
                "deadline_source_ref": obligation.deadline_source_ref,
                "applicability": obligation.applicability.value,
                "created_at": obligation.created_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            return self._insert_immutable(
                connection,
                table="tax_obligations",
                key="obligation_id",
                value=obligation.obligation_id,
                payload=payload,
            )

    def obligations(self) -> tuple[TaxObligation, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM tax_obligations ORDER BY sequence"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                TaxObligation(
                    obligation_id=p["obligation_id"],
                    taxpayer_ref=p["taxpayer_ref"],
                    rule_id=p["rule_id"],
                    model_code=p["model_code"],
                    period_start=datetime.fromisoformat(p["period_start"]),
                    period_end=datetime.fromisoformat(p["period_end"]),
                    due_at=datetime.fromisoformat(p["due_at"]),
                    deadline_source_ref=p["deadline_source_ref"],
                    applicability=TaxApplicabilityState(p["applicability"]),
                    created_at=datetime.fromisoformat(p["created_at"]),
                )
            )
        return tuple(result)

    def append_evidence(self, evidence: TaxEvidence) -> bool:
        payload = json.dumps(
            {
                "evidence_id": evidence.evidence_id,
                "obligation_id": evidence.obligation_id,
                "kind": evidence.kind.value,
                "observed_at": evidence.observed_at.isoformat(),
                "source_ref": evidence.source_ref,
                "artifact_fingerprint": evidence.artifact_fingerprint,
                "actor_ref": evidence.actor_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM tax_evidence WHERE evidence_id = ?",
                (evidence.evidence_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise TaxOperationsStoreConflict("tax evidence id reused with different content")
            connection.execute(
                "INSERT INTO tax_evidence(evidence_id, obligation_id, payload_json) "
                "VALUES (?, ?, ?)",
                (evidence.evidence_id, evidence.obligation_id, payload),
            )
        return True

    def evidence_for(self, obligation_id: str) -> tuple[TaxEvidence, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM tax_evidence WHERE obligation_id = ? ORDER BY sequence",
                (obligation_id,),
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                TaxEvidence(
                    evidence_id=p["evidence_id"],
                    obligation_id=p["obligation_id"],
                    kind=TaxEvidenceKind(p["kind"]),
                    observed_at=datetime.fromisoformat(p["observed_at"]),
                    source_ref=p["source_ref"],
                    artifact_fingerprint=p["artifact_fingerprint"],
                    actor_ref=p["actor_ref"],
                )
            )
        return tuple(result)
