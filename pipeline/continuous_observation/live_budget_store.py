"""SQLite upper-bound budget ledger for PB-11 live research."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.async_research_runtime import (
    LiveResearchBudgetPolicy,
    LiveResearchBudgetSnapshot,
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("budget time must be timezone-aware")
    return value.astimezone(UTC)


class SqliteLiveResearchBudgetStore:
    """Persist conservative live-provider spend reservations across restarts."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS live_research_budget_reservations (
                    execution_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    cost_upper_bound_microunits INTEGER NOT NULL,
                    job_count INTEGER NOT NULL,
                    batch_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._path)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _snapshot_from_db(db: sqlite3.Connection, currency: str) -> LiveResearchBudgetSnapshot:
        rows = db.execute(
            """
            SELECT state,
                   COALESCE(SUM(cost_upper_bound_microunits), 0) AS cost,
                   COALESCE(SUM(batch_count), 0) AS batches,
                   COALESCE(SUM(job_count), 0) AS jobs
            FROM live_research_budget_reservations
            WHERE currency=?
            GROUP BY state
            """,
            (currency,),
        ).fetchall()
        values = {
            str(row["state"]): (
                int(row["cost"]),
                int(row["batches"]),
                int(row["jobs"]),
            )
            for row in rows
        }
        committed = values.get("COMMITTED", (0, 0, 0))
        reserved = values.get("RESERVED", (0, 0, 0))
        return LiveResearchBudgetSnapshot(
            currency=currency,
            committed_cost_upper_bound_microunits=committed[0],
            reserved_cost_upper_bound_microunits=reserved[0],
            committed_batches=committed[1],
            reserved_batches=reserved[1],
            committed_jobs=committed[2],
            reserved_jobs=reserved[2],
        )

    def snapshot(self, *, currency: str) -> LiveResearchBudgetSnapshot:
        normalized = currency.strip().upper()
        with self._connect() as db:
            return self._snapshot_from_db(db, normalized)

    def try_reserve(
        self,
        *,
        execution_id: str,
        job_count: int,
        now: datetime,
        policy: LiveResearchBudgetPolicy,
    ) -> bool:
        if not execution_id.strip():
            raise ValueError("budget reservation execution id is required")
        if job_count < 1:
            raise ValueError("budget reservation requires at least one job")
        current = _utc(now)
        expires = current + policy.reservation_lease_for
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                DELETE FROM live_research_budget_reservations
                WHERE state='RESERVED' AND expires_at<=?
                """,
                (current.isoformat(),),
            )
            existing = db.execute(
                "SELECT state FROM live_research_budget_reservations WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
            if existing is not None:
                return True

            snapshot = self._snapshot_from_db(db, policy.currency)
            projected_cost = (
                snapshot.total_cost_upper_bound_microunits
                + policy.per_batch_cost_upper_bound_microunits
            )
            projected_batches = snapshot.committed_batches + snapshot.reserved_batches + 1
            projected_jobs = snapshot.committed_jobs + snapshot.reserved_jobs + job_count
            if (
                projected_cost > policy.max_cost_upper_bound_microunits
                or projected_batches > policy.max_batches
                or projected_jobs > policy.max_jobs
            ):
                return False
            db.execute(
                """
                INSERT INTO live_research_budget_reservations(
                    execution_id, state, currency, cost_upper_bound_microunits,
                    job_count, batch_count, created_at, expires_at
                ) VALUES (?, 'RESERVED', ?, ?, ?, 1, ?, ?)
                """,
                (
                    execution_id,
                    policy.currency,
                    policy.per_batch_cost_upper_bound_microunits,
                    job_count,
                    current.isoformat(),
                    expires.isoformat(),
                ),
            )
        return True

    def commit(self, execution_id: str) -> None:
        with self._connect() as db:
            cursor = db.execute(
                """
                UPDATE live_research_budget_reservations
                SET state='COMMITTED'
                WHERE execution_id=? AND state='RESERVED'
                """,
                (execution_id,),
            )
        if cursor.rowcount == 0:
            row = self._existing(execution_id)
            if row != "COMMITTED":
                raise ValueError("live research budget reservation is not active")

    def release(self, execution_id: str) -> None:
        with self._connect() as db:
            db.execute(
                """
                DELETE FROM live_research_budget_reservations
                WHERE execution_id=? AND state='RESERVED'
                """,
                (execution_id,),
            )

    def _existing(self, execution_id: str) -> str | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT state FROM live_research_budget_reservations WHERE execution_id=?",
                (execution_id,),
            ).fetchone()
        return None if row is None else str(row["state"])
