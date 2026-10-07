"""Append-only continuity checkpoints in the subscriber economic-output database.

Tables are additive and created idempotently next to the immutable output snapshots;
nothing here copies AXIGLAND or evidence payloads (dependencies are identities).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from application.subscriber_continuity.dependencies import DependencyEvaluation
from application.subscriber_continuity.model import (
    ContinuityCheckpoint,
    ContinuityItem,
    ContinuityOrigin,
    ContinuityState,
    DeclaredDependency,
    DependencyKind,
    OpenQuestion,
    QuestionKind,
    checkpoint_id,
)

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS subscriber_continuity_checkpoints (
        tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL, checkpoint_id TEXT NOT NULL,
        sequence INTEGER NOT NULL, organization_id TEXT NOT NULL,
        previous_checkpoint_id TEXT, temporal_cut TEXT NOT NULL,
        dependency_fingerprint TEXT NOT NULL, semantic_fingerprint TEXT NOT NULL,
        state_json TEXT NOT NULL,
        PRIMARY KEY (tenant_id, xeed_id, checkpoint_id),
        UNIQUE (tenant_id, xeed_id, sequence))""",
    """CREATE INDEX IF NOT EXISTS subscriber_continuity_cut
        ON subscriber_continuity_checkpoints (tenant_id, xeed_id, temporal_cut, sequence)""",
    # Index of the latest checkpoint's subjects -> dependent Foci (fan-out without scans).
    """CREATE TABLE IF NOT EXISTS subscriber_continuity_dependents (
        subject_id TEXT NOT NULL, tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL,
        checkpoint_id TEXT NOT NULL,
        PRIMARY KEY (subject_id, tenant_id, xeed_id))""",
    """CREATE TABLE IF NOT EXISTS subscriber_continuity_invalidations (
        tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL, checkpoint_id TEXT NOT NULL,
        dependency_key TEXT NOT NULL, status TEXT NOT NULL, action TEXT NOT NULL,
        reason TEXT NOT NULL, first_evaluated_at TEXT NOT NULL,
        PRIMARY KEY (tenant_id, xeed_id, checkpoint_id, dependency_key, status))""",
    """CREATE TABLE IF NOT EXISTS subscriber_continuity_recompute (
        tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL, checkpoint_id TEXT NOT NULL,
        family TEXT NOT NULL, dependency_keys_json TEXT NOT NULL, owed_at TEXT NOT NULL,
        delivered_at TEXT,
        PRIMARY KEY (tenant_id, xeed_id, checkpoint_id, family))""",
)


def _utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("continuity times must be timezone-aware")
    return value.astimezone(UTC).isoformat()


def _encode(state: ContinuityState) -> str:
    payload = {
        "organization_id": state.organization_id,
        "snapshot_refs": list(state.snapshot_refs),
        "temporal_cut": _utc(state.temporal_cut),
        "items": [item.to_wire() for item in state.items],
        "questions": [item.to_wire() for item in state.questions],
        "dependencies": [item.identity() for item in state.dependencies],
        "trace": state.trace,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _decode(raw: str) -> ContinuityState:
    data = json.loads(raw)
    return ContinuityState(
        organization_id=str(data["organization_id"]),
        snapshot_refs=tuple(data["snapshot_refs"]),
        temporal_cut=datetime.fromisoformat(data["temporal_cut"]),
        items=tuple(
            ContinuityItem(
                key=item["key"],
                kind=item["kind"],
                family=item["family"],
                epistemic=item["epistemic"],
                currentness=item["currentness"],
                value_fingerprint=item["valueFingerprint"],
                dependency_keys=tuple(item["dependencyKeys"]),
            )
            for item in data["items"]
        ),
        questions=tuple(
            OpenQuestion(
                key=item["key"],
                kind=QuestionKind(item["kind"]),
                about=item["about"],
                reason=item["reason"],
                dependency_keys=tuple(item["dependencyKeys"]),
            )
            for item in data["questions"]
        ),
        dependencies=tuple(
            DeclaredDependency(
                key=item["key"],
                kind=DependencyKind(item["kind"]),
                source_ref=item["source_ref"],
                observed_at=datetime.fromisoformat(item["observed_at"]),
                subject_id=item["subject_id"],
                content_fingerprint=item["content_fingerprint"],
                fields=tuple((str(f[0]), str(f[1]), str(f[2])) for f in item["fields"]),
            )
            for item in data["dependencies"]
        ),
        trace=dict(data["trace"]),
    )


class SqliteSubscriberContinuityStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as db:
            for statement in _SCHEMA:
                db.execute(statement)

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path, isolation_level=None, timeout=10)) as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.execute("ROLLBACK")
                raise
            db.execute("COMMIT")

    def _read(self, sql: str, params: tuple[object, ...]) -> list[sqlite3.Row]:
        with closing(sqlite3.connect(self._path, timeout=10)) as db:
            db.row_factory = sqlite3.Row
            return db.execute(sql, params).fetchall()

    @staticmethod
    def _checkpoint(row: sqlite3.Row) -> ContinuityCheckpoint:
        state = _decode(str(row["state_json"]))
        return ContinuityCheckpoint(
            checkpoint_id=str(row["checkpoint_id"]),
            tenant_id=str(row["tenant_id"]),
            xeed_id=str(row["xeed_id"]),
            sequence=int(row["sequence"]),
            origin=ContinuityOrigin(
                previous_checkpoint_id=row["previous_checkpoint_id"],
                organization_id=str(row["organization_id"]),
                snapshot_refs=state.snapshot_refs,
                temporal_cut=datetime.fromisoformat(str(row["temporal_cut"])),
                dependency_fingerprint=str(row["dependency_fingerprint"]),
            ),
            state=state,
        )

    def append(
        self, tenant_id: str, xeed_id: str, state: ContinuityState
    ) -> tuple[ContinuityCheckpoint, bool]:
        with self._transaction() as db:
            latest = db.execute(
                """SELECT * FROM subscriber_continuity_checkpoints
                   WHERE tenant_id=? AND xeed_id=? ORDER BY sequence DESC LIMIT 1""",
                (tenant_id, xeed_id),
            ).fetchone()
            if latest is not None and latest["semantic_fingerprint"] == state.semantic_fingerprint:
                # Same economic meaning (replay, clock or serialization only): no new history.
                return self._checkpoint(latest), False
            if latest is not None and latest["organization_id"] != state.organization_id:
                # A replaced Focus target starts its own lineage; never splice histories.
                previous = None
            else:
                previous = None if latest is None else str(latest["checkpoint_id"])
            if latest is not None and datetime.fromisoformat(
                str(latest["temporal_cut"])
            ) > state.temporal_cut.astimezone(UTC):
                raise ValueError("continuity cannot be recorded before its latest checkpoint")
            identifier = checkpoint_id(
                tenant_id=tenant_id,
                xeed_id=xeed_id,
                previous=previous,
                semantic_fingerprint=state.semantic_fingerprint,
            )
            sequence = 1 if latest is None else int(latest["sequence"]) + 1
            db.execute(
                "INSERT INTO subscriber_continuity_checkpoints VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    tenant_id,
                    xeed_id,
                    identifier,
                    sequence,
                    state.organization_id,
                    previous,
                    _utc(state.temporal_cut),
                    state.dependency_fingerprint,
                    state.semantic_fingerprint,
                    _encode(state),
                ),
            )
            db.execute(
                "DELETE FROM subscriber_continuity_dependents WHERE tenant_id=? AND xeed_id=?",
                (tenant_id, xeed_id),
            )
            subjects = {state.organization_id} | {
                item.subject_id for item in state.dependencies if item.subject_id
            }
            db.executemany(
                "INSERT OR REPLACE INTO subscriber_continuity_dependents VALUES (?,?,?,?)",
                [(subject, tenant_id, xeed_id, identifier) for subject in sorted(subjects)],
            )
            row = db.execute(
                """SELECT * FROM subscriber_continuity_checkpoints
                   WHERE tenant_id=? AND xeed_id=? AND checkpoint_id=?""",
                (tenant_id, xeed_id, identifier),
            ).fetchone()
        return self._checkpoint(row), True

    def latest(
        self, tenant_id: str, xeed_id: str, *, as_of: datetime | None = None
    ) -> ContinuityCheckpoint | None:
        if as_of is None:
            rows = self._read(
                """SELECT * FROM subscriber_continuity_checkpoints
                   WHERE tenant_id=? AND xeed_id=? ORDER BY sequence DESC LIMIT 1""",
                (tenant_id, xeed_id),
            )
        else:
            rows = self._read(
                """SELECT * FROM subscriber_continuity_checkpoints
                   WHERE tenant_id=? AND xeed_id=? AND temporal_cut<=?
                   ORDER BY sequence DESC LIMIT 1""",
                (tenant_id, xeed_id, _utc(as_of)),
            )
        return self._checkpoint(rows[0]) if rows else None

    def get(self, tenant_id: str, xeed_id: str, checkpoint_id: str) -> ContinuityCheckpoint | None:
        rows = self._read(
            """SELECT * FROM subscriber_continuity_checkpoints
               WHERE tenant_id=? AND xeed_id=? AND checkpoint_id=?""",
            (tenant_id, xeed_id, checkpoint_id),
        )
        return self._checkpoint(rows[0]) if rows else None

    def history(self, tenant_id: str, xeed_id: str) -> tuple[ContinuityCheckpoint, ...]:
        rows = self._read(
            """SELECT * FROM subscriber_continuity_checkpoints
               WHERE tenant_id=? AND xeed_id=? ORDER BY sequence""",
            (tenant_id, xeed_id),
        )
        return tuple(self._checkpoint(row) for row in rows)

    def dependents(self, subject_id: str) -> tuple[tuple[str, str], ...]:
        rows = self._read(
            """SELECT tenant_id, xeed_id FROM subscriber_continuity_dependents
               WHERE subject_id=? ORDER BY tenant_id, xeed_id""",
            (subject_id,),
        )
        return tuple((str(row["tenant_id"]), str(row["xeed_id"])) for row in rows)

    def record_invalidations(
        self,
        checkpoint: ContinuityCheckpoint,
        evaluations: tuple[DependencyEvaluation, ...],
        *,
        evaluated_at: datetime,
    ) -> int:
        with self._transaction() as db:
            before = db.total_changes
            db.executemany(
                "INSERT OR IGNORE INTO subscriber_continuity_invalidations VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        checkpoint.tenant_id,
                        checkpoint.xeed_id,
                        checkpoint.checkpoint_id,
                        item.key,
                        item.status.value,
                        item.action.value,
                        item.reason,
                        _utc(evaluated_at),
                    )
                    for item in evaluations
                ],
            )
            return db.total_changes - before

    def invalidations(
        self, tenant_id: str, xeed_id: str, checkpoint_id: str
    ) -> tuple[dict[str, str], ...]:
        rows = self._read(
            """SELECT dependency_key, status, action, reason, first_evaluated_at
               FROM subscriber_continuity_invalidations
               WHERE tenant_id=? AND xeed_id=? AND checkpoint_id=?
               ORDER BY first_evaluated_at, dependency_key, status""",
            (tenant_id, xeed_id, checkpoint_id),
        )
        return tuple(
            {
                "dependencyKey": str(row["dependency_key"]),
                "status": str(row["status"]),
                "action": str(row["action"]),
                "reason": str(row["reason"]),
                "firstEvaluatedAt": str(row["first_evaluated_at"]),
            }
            for row in rows
        )

    def owe(
        self,
        checkpoint: ContinuityCheckpoint,
        family: str,
        dependency_keys: tuple[str, ...],
        *,
        owed_at: datetime,
    ) -> bool:
        with self._transaction() as db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO subscriber_continuity_recompute VALUES (?,?,?,?,?,?,NULL)",
                (
                    checkpoint.tenant_id,
                    checkpoint.xeed_id,
                    checkpoint.checkpoint_id,
                    family,
                    json.dumps(sorted(dependency_keys)),
                    _utc(owed_at),
                ),
            )
            return cursor.rowcount == 1

    def undelivered(
        self, tenant_id: str, xeed_id: str
    ) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        rows = self._read(
            """SELECT checkpoint_id, family, dependency_keys_json
               FROM subscriber_continuity_recompute
               WHERE tenant_id=? AND xeed_id=? AND delivered_at IS NULL
               ORDER BY owed_at, family""",
            (tenant_id, xeed_id),
        )
        return tuple(
            (
                str(row["checkpoint_id"]),
                str(row["family"]),
                tuple(json.loads(str(row["dependency_keys_json"]))),
            )
            for row in rows
        )

    def mark_delivered(
        self, tenant_id: str, xeed_id: str, checkpoint_id: str, family: str, *, at: datetime
    ) -> None:
        with self._transaction() as db:
            db.execute(
                """UPDATE subscriber_continuity_recompute SET delivered_at=?
                   WHERE tenant_id=? AND xeed_id=? AND checkpoint_id=? AND family=?
                     AND delivered_at IS NULL""",
                (_utc(at), tenant_id, xeed_id, checkpoint_id, family),
            )

    def recompute_ledger(self, tenant_id: str, xeed_id: str) -> tuple[dict[str, object], ...]:
        rows = self._read(
            """SELECT checkpoint_id, family, owed_at, delivered_at
               FROM subscriber_continuity_recompute
               WHERE tenant_id=? AND xeed_id=? ORDER BY owed_at, family""",
            (tenant_id, xeed_id),
        )
        return tuple(
            {
                "checkpointId": str(row["checkpoint_id"]),
                "family": str(row["family"]),
                "owedAt": str(row["owed_at"]),
                "deliveredAt": row["delivered_at"],
            }
            for row in rows
        )
