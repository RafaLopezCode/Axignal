"""SQLite persistence for PB-10 asynchronous governed canary executions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from cognition.async_research_canary import (
    DurableCanaryClaim,
    DurableCanaryExecution,
)


class SqliteDurableCanaryExecutionStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS async_research_canary (
                    provider_batch_id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    claims_json TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    active INTEGER NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_async_canary_active_subject
                ON async_research_canary(subject_id) WHERE active=1
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._path)
        db.row_factory = sqlite3.Row
        return db

    def active_for_subject(self, subject_id: str) -> DurableCanaryExecution | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM async_research_canary WHERE subject_id=? AND active=1",
                (subject_id,),
            ).fetchone()
        if row is None:
            return None
        claims = tuple(
            DurableCanaryClaim(
                work_key=str(item["work_key"]),
                lease_token=str(item["lease_token"]),
                acquired_at=datetime.fromisoformat(str(item["acquired_at"])),
                expires_at=datetime.fromisoformat(str(item["expires_at"])),
                job_id=str(item["job_id"]),
            )
            for item in json.loads(str(row["claims_json"]))
        )
        return DurableCanaryExecution(
            execution_id=str(row["execution_id"]),
            subject_id=str(row["subject_id"]),
            provider_batch_id=str(row["provider_batch_id"]),
            claims=claims,
            submitted_at=datetime.fromisoformat(str(row["submitted_at"])),
        )

    def save(self, execution: DurableCanaryExecution) -> None:
        claims = [
            {
                "work_key": item.work_key,
                "lease_token": item.lease_token,
                "acquired_at": item.acquired_at.isoformat(),
                "expires_at": item.expires_at.isoformat(),
                "job_id": item.job_id,
            }
            for item in execution.claims
        ]
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO async_research_canary(
                    provider_batch_id, execution_id, subject_id, claims_json,
                    submitted_at, active
                ) VALUES (?, ?, ?, ?, ?, 1)
                """,
                (
                    execution.provider_batch_id,
                    execution.execution_id,
                    execution.subject_id,
                    json.dumps(claims, sort_keys=True, separators=(",", ":")),
                    execution.submitted_at.isoformat(),
                ),
            )

    def settle(self, provider_batch_id: str) -> None:
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE async_research_canary SET active=0 WHERE provider_batch_id=? AND active=1",
                (provider_batch_id,),
            )
        if cursor.rowcount != 1:
            raise ValueError("durable canary execution is not active")
