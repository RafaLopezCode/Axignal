"""SQLite operational state for PB-09 research runtime."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
    ResearchRuntimeSnapshot,
    ResearchRuntimeStatus,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("runtime time must be timezone-aware")
    return value.astimezone(UTC)


class SqliteResearchRuntimeStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runtime_control (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    kill_switch INTEGER NOT NULL,
                    global_inflight INTEGER NOT NULL,
                    last_started_at TEXT,
                    last_finished_at TEXT,
                    next_wake_at TEXT,
                    last_error_type TEXT,
                    cycles_started INTEGER NOT NULL,
                    cycles_completed INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                INSERT OR IGNORE INTO research_runtime_control VALUES
                (1, 0, 0, NULL, NULL, NULL, NULL, 0, 0, 'DISABLED', 'DISABLED')
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runtime_subject_inflight (
                    subject_id TEXT NOT NULL,
                    lease_token TEXT PRIMARY KEY,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._path)
        db.row_factory = sqlite3.Row
        return db

    def snapshot(self) -> ResearchRuntimeSnapshot:
        with self._connect() as db:
            row = db.execute("SELECT * FROM research_runtime_control WHERE singleton=1").fetchone()
        assert row is not None

        def parse(value: object) -> datetime | None:
            return None if value is None else datetime.fromisoformat(str(value))

        return ResearchRuntimeSnapshot(
            mode=ResearchRuntimeMode(str(row["mode"])),
            status=ResearchRuntimeStatus(str(row["status"])),
            kill_switch=bool(row["kill_switch"]),
            global_inflight=int(row["global_inflight"]),
            last_started_at=parse(row["last_started_at"]),
            last_finished_at=parse(row["last_finished_at"]),
            next_wake_at=parse(row["next_wake_at"]),
            last_error_type=None if row["last_error_type"] is None else str(row["last_error_type"]),
            cycles_started=int(row["cycles_started"]),
            cycles_completed=int(row["cycles_completed"]),
        )

    def set_kill_switch(self, enabled: bool) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                UPDATE research_runtime_control
                SET kill_switch=?, status=?
                WHERE singleton=1
                """,
                (
                    int(enabled),
                    ResearchRuntimeStatus.DISABLED.value
                    if enabled
                    else ResearchRuntimeStatus.IDLE.value,
                ),
            )

    def try_acquire(self, *, subject_id: str, now: datetime, policy: ResearchRuntimePolicy) -> bool:
        current = _utc(now)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute(
                "SELECT COUNT(*) FROM research_runtime_subject_inflight WHERE expires_at<=?",
                (current.isoformat(),),
            ).fetchone()
            expired_count = 0 if expired is None else int(expired[0])
            if expired_count:
                db.execute(
                    "DELETE FROM research_runtime_subject_inflight WHERE expires_at<=?",
                    (current.isoformat(),),
                )
                db.execute(
                    """
                    UPDATE research_runtime_control
                    SET global_inflight=MAX(0, global_inflight-?)
                    WHERE singleton=1
                    """,
                    (expired_count,),
                )
            control = db.execute(
                "SELECT kill_switch, global_inflight FROM research_runtime_control WHERE singleton=1"
            ).fetchone()
            assert control is not None
            if (
                bool(control["kill_switch"])
                or int(control["global_inflight"]) >= policy.max_global_inflight
            ):
                return False
            subject_inflight = int(
                db.execute(
                    "SELECT COUNT(*) FROM research_runtime_subject_inflight WHERE subject_id=?",
                    (subject_id,),
                ).fetchone()[0]
            )
            if subject_inflight >= policy.max_subject_inflight:
                return False
            db.execute(
                """
                INSERT INTO research_runtime_subject_inflight(subject_id, lease_token, expires_at)
                VALUES (?, ?, ?)
                """,
                (
                    subject_id,
                    f"runtime:{uuid.uuid4().hex}",
                    (current + policy.inflight_lease_for).isoformat(),
                ),
            )
            db.execute(
                """
                UPDATE research_runtime_control
                SET global_inflight=global_inflight+1, last_started_at=?,
                    cycles_started=cycles_started+1, mode=?, status=?
                WHERE singleton=1
                """,
                (
                    current.isoformat(),
                    policy.mode.value,
                    ResearchRuntimeStatus.RUNNING.value,
                ),
            )
        return True

    def finish(
        self,
        *,
        subject_id: str,
        now: datetime,
        policy: ResearchRuntimePolicy,
        error_type: str | None,
    ) -> None:
        current = _utc(now)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """
                SELECT lease_token FROM research_runtime_subject_inflight
                WHERE subject_id=? ORDER BY expires_at LIMIT 1
                """,
                (subject_id,),
            ).fetchone()
            if row is None:
                raise ValueError("runtime subject lease is not active")
            db.execute(
                "DELETE FROM research_runtime_subject_inflight WHERE lease_token=?",
                (str(row["lease_token"]),),
            )
            status = ResearchRuntimeStatus.ERROR if error_type else ResearchRuntimeStatus.IDLE
            db.execute(
                """
                UPDATE research_runtime_control
                SET global_inflight=global_inflight-1, last_finished_at=?,
                    next_wake_at=?, last_error_type=?, cycles_completed=cycles_completed+1,
                    mode=?, status=?
                WHERE singleton=1
                """,
                (
                    current.isoformat(),
                    (current + policy.wake_interval).isoformat(),
                    error_type,
                    policy.mode.value,
                    status.value,
                ),
            )
