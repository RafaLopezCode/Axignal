"""Append-only ledger of AXENT research requests: attention, never conclusions.

One row per tenant, Xeed, family, geographies and day (idempotent). Reads are
always scoped to one tenant and Xeed. Nothing here is canonical state.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from application.axent.grounded.answer import ResearchRequest


class SqliteResearchRequestLedger:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as db, db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS axent_research_requests (
                    request_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL,
                    family TEXT, geographies TEXT NOT NULL, reason TEXT NOT NULL,
                    question_kind TEXT NOT NULL, created_at TEXT NOT NULL)"""
            )

    def request(self, item: ResearchRequest) -> bool:
        with closing(sqlite3.connect(self._path)) as db, db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO axent_research_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.request_id,
                    item.tenant_id,
                    item.xeed_id,
                    None if item.family is None else item.family.value,
                    json.dumps(list(item.geographies)),
                    item.reason,
                    item.question_kind,
                    item.created_at.isoformat(),
                ),
            )
            return cursor.rowcount == 1

    def pending(self, *, tenant_id: str, xeed_id: str) -> tuple[dict[str, object], ...]:
        with closing(sqlite3.connect(self._path)) as db:
            rows = db.execute(
                """SELECT request_id, family, geographies, reason, created_at
                FROM axent_research_requests WHERE tenant_id=? AND xeed_id=? ORDER BY created_at""",
                (tenant_id, xeed_id),
            ).fetchall()
        return tuple(
            {
                "requestId": r[0],
                "family": r[1],
                "geographies": json.loads(r[2]),
                "reason": r[3],
                "createdAt": r[4],
            }
            for r in rows
        )
