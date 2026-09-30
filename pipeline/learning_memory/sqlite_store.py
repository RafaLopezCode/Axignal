"""SQLite adapter for governed AXIGNAL Learning Memory."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningMemoryConflict,
    LearningOutcome,
    LearningYield,
)


class SqliteLearningMemory:
    """Durable append-only learning ledger with replay-safe identities."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    xeed_id TEXT,
                    occurred_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    activity_ref TEXT NOT NULL,
                    corrects_event_id TEXT,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (corrects_event_id)
                        REFERENCES learning_events(event_id)
                        ON DELETE RESTRICT
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_subject_time
                ON learning_events(subject_id, occurred_at, event_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_xeed_time
                ON learning_events(xeed_id, occurred_at, event_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_learning_activity
                ON learning_events(activity_ref, occurred_at, event_id)
                """
            )

    @staticmethod
    def _payload(event: LearningEvent) -> str:
        data = {
            "event_id": event.event_id,
            "kind": event.kind.value,
            "outcome": event.outcome.value,
            "occurred_at": event.occurred_at.astimezone(UTC).isoformat(),
            "subject_id": event.subject_id,
            "activity_ref": event.activity_ref,
            "policy_id": event.policy_id,
            "policy_version": event.policy_version,
            "code_sha": event.code_sha,
            "mechanism": event.mechanism.value,
            "input_fingerprint": event.input_fingerprint,
            "reason_code": event.reason_code,
            "xeed_id": event.xeed_id,
            "provider": event.provider,
            "provider_version": event.provider_version,
            "before_state_fingerprint": event.before_state_fingerprint,
            "after_state_fingerprint": event.after_state_fingerprint,
            "output_fingerprint": event.output_fingerprint,
            "corrects_event_id": event.corrects_event_id,
            "cost": {
                "amount_microunits": event.cost.amount_microunits,
                "currency": event.cost.currency,
                "latency_ms": event.cost.latency_ms,
                "input_units": event.cost.input_units,
                "output_units": event.cost.output_units,
            },
            "yield": {
                "observations_added": event.yield_.observations_added,
                "state_fields_changed": event.yield_.state_fields_changed,
                "dimensions_became_answerable": event.yield_.dimensions_became_answerable,
                "semantic_judgments_produced": event.yield_.semantic_judgments_produced,
                "research_objectives_resolved": event.yield_.research_objectives_resolved,
                "xignals_emitted": event.yield_.xignals_emitted,
                "canonical_admissions": event.yield_.canonical_admissions,
            },
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _deserialize(payload: str) -> LearningEvent:
        data = json.loads(payload)
        cost = data["cost"]
        yield_data = data["yield"]
        return LearningEvent(
            event_id=data["event_id"],
            kind=LearningEventKind(data["kind"]),
            outcome=LearningOutcome(data["outcome"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            subject_id=data["subject_id"],
            activity_ref=data["activity_ref"],
            policy_id=data["policy_id"],
            policy_version=data["policy_version"],
            code_sha=data["code_sha"],
            mechanism=LearningMechanism(data["mechanism"]),
            input_fingerprint=data["input_fingerprint"],
            reason_code=data["reason_code"],
            xeed_id=data["xeed_id"],
            provider=data["provider"],
            provider_version=data["provider_version"],
            before_state_fingerprint=data["before_state_fingerprint"],
            after_state_fingerprint=data["after_state_fingerprint"],
            output_fingerprint=data["output_fingerprint"],
            corrects_event_id=data["corrects_event_id"],
            cost=LearningCost(
                amount_microunits=cost["amount_microunits"],
                currency=cost["currency"],
                latency_ms=cost["latency_ms"],
                input_units=cost["input_units"],
                output_units=cost["output_units"],
            ),
            yield_=LearningYield(
                observations_added=yield_data["observations_added"],
                state_fields_changed=yield_data["state_fields_changed"],
                dimensions_became_answerable=yield_data["dimensions_became_answerable"],
                semantic_judgments_produced=yield_data["semantic_judgments_produced"],
                research_objectives_resolved=yield_data["research_objectives_resolved"],
                xignals_emitted=yield_data["xignals_emitted"],
                canonical_admissions=yield_data["canonical_admissions"],
            ),
        )

    def _load(
        self,
        connection: sqlite3.Connection,
        event_id: str,
    ) -> LearningEvent | None:
        row = connection.execute(
            "SELECT payload_json FROM learning_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return None if row is None else self._deserialize(str(row[0]))

    def append(self, event: LearningEvent) -> bool:
        if not isinstance(event, LearningEvent):
            raise TypeError("Learning Memory accepts LearningEvent instances only")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = self._load(connection, event.event_id)
            if existing is not None:
                if existing == event:
                    return False
                raise LearningMemoryConflict(
                    "learning event id already exists with different governed content"
                )

            if event.corrects_event_id is not None:
                corrected = self._load(connection, event.corrects_event_id)
                if corrected is None:
                    raise LearningMemoryConflict("correction references an unknown learning event")
                if corrected.subject_id != event.subject_id:
                    raise LearningMemoryConflict("correction cannot cross canonical subjects")

            connection.execute(
                """
                INSERT INTO learning_events (
                    event_id, subject_id, xeed_id, occurred_at, kind, outcome,
                    activity_ref, corrects_event_id, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.subject_id,
                    event.xeed_id,
                    event.occurred_at.astimezone(UTC).isoformat(),
                    event.kind.value,
                    event.outcome.value,
                    event.activity_ref,
                    event.corrects_event_id,
                    self._payload(event),
                ),
            )
        return True

    def get(self, event_id: str) -> LearningEvent | None:
        if not event_id.strip():
            raise ValueError("learning event identity is required")
        with self._connect() as connection:
            return self._load(connection, event_id)

    def _query(self, clause: str, value: str) -> tuple[LearningEvent, ...]:
        if not value.strip():
            raise ValueError("learning-memory query identity is required")
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT payload_json
                FROM learning_events
                WHERE {clause} = ?
                ORDER BY occurred_at, event_id
                """,
                (value,),
            ).fetchall()
        return tuple(self._deserialize(str(row[0])) for row in rows)

    def for_subject(self, subject_id: str) -> tuple[LearningEvent, ...]:
        return self._query("subject_id", subject_id)

    def for_xeed(self, xeed_id: str) -> tuple[LearningEvent, ...]:
        return self._query("xeed_id", xeed_id)
