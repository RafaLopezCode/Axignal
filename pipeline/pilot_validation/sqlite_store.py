"""SQLite persistence for append-only FR-27 pilot evidence."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.pilot_validation import (
    PilotAnswer,
    PilotEvidence,
    PilotEvidenceConflict,
    PilotEvidenceKind,
    PilotEvidenceSource,
    PricingEvidenceKind,
)


class SqlitePilotEvidenceMemory:
    """Durable pilot-evidence ledger, separate from canonical economic truth."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pilot_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    pilot_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_pilot_evidence_time
                ON pilot_evidence(pilot_id, occurred_at, evidence_id)
                """
            )

    @staticmethod
    def _payload(evidence: PilotEvidence) -> str:
        data = {
            "evidence_id": evidence.evidence_id,
            "pilot_id": evidence.pilot_id,
            "occurred_at": evidence.occurred_at.astimezone(UTC).isoformat(),
            "kind": evidence.kind.value,
            "source": evidence.source.value,
            "evidence_ref": evidence.evidence_ref,
            "answer": evidence.answer.value,
            "xeed_id": evidence.xeed_id,
            "xignal_id": evidence.xignal_id,
            "learning_event_id": evidence.learning_event_id,
            "pricing_kind": (
                None if evidence.pricing_kind is None else evidence.pricing_kind.value
            ),
            "amount_microunits": evidence.amount_microunits,
            "currency": evidence.currency,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _deserialize(payload: str) -> PilotEvidence:
        data = json.loads(payload)
        pricing_kind = data["pricing_kind"]
        return PilotEvidence(
            evidence_id=data["evidence_id"],
            pilot_id=data["pilot_id"],
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            kind=PilotEvidenceKind(data["kind"]),
            source=PilotEvidenceSource(data["source"]),
            evidence_ref=data["evidence_ref"],
            answer=PilotAnswer(data["answer"]),
            xeed_id=data["xeed_id"],
            xignal_id=data["xignal_id"],
            learning_event_id=data["learning_event_id"],
            pricing_kind=(None if pricing_kind is None else PricingEvidenceKind(pricing_kind)),
            amount_microunits=data["amount_microunits"],
            currency=data["currency"],
        )

    def _load(
        self,
        connection: sqlite3.Connection,
        evidence_id: str,
    ) -> PilotEvidence | None:
        row = connection.execute(
            "SELECT payload_json FROM pilot_evidence WHERE evidence_id = ?",
            (evidence_id,),
        ).fetchone()
        return None if row is None else self._deserialize(str(row[0]))

    def append(self, evidence: PilotEvidence) -> bool:
        if not isinstance(evidence, PilotEvidence):
            raise TypeError("pilot evidence memory accepts PilotEvidence only")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = self._load(connection, evidence.evidence_id)
            if existing is not None:
                if existing == evidence:
                    return False
                raise PilotEvidenceConflict(
                    "pilot evidence id already exists with different content"
                )
            connection.execute(
                """
                INSERT INTO pilot_evidence (
                    evidence_id, pilot_id, occurred_at, kind, payload_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    evidence.evidence_id,
                    evidence.pilot_id,
                    evidence.occurred_at.astimezone(UTC).isoformat(),
                    evidence.kind.value,
                    self._payload(evidence),
                ),
            )
        return True

    def for_pilot(self, pilot_id: str) -> tuple[PilotEvidence, ...]:
        if not pilot_id.strip():
            raise ValueError("pilot id is required")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM pilot_evidence
                WHERE pilot_id = ?
                ORDER BY occurred_at, evidence_id
                """,
                (pilot_id,),
            ).fetchall()
        return tuple(self._deserialize(str(row[0])) for row in rows)
