"""SQLite call reservations: restart-safe quotas; no prompts, evidence or credentials."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from application.axent.grounded.answer import ReasoningRequest, ReasoningResult


class SqliteModelAudit:
    def __init__(self, path: Path, *, max_tenant_calls: int = 50, max_global_calls: int = 500):
        if min(max_tenant_calls, max_global_calls) < 1:
            raise ValueError("model quotas must be positive")
        self.path, self.max_tenant_calls, self.max_global_calls = (
            path,
            max_tenant_calls,
            max_global_calls,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS axent_model_calls (
                call_id TEXT PRIMARY KEY, request_ref TEXT NOT NULL, tenant_ref TEXT NOT NULL, focus_ref TEXT NOT NULL,
                day TEXT NOT NULL, started_at TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
                purpose TEXT NOT NULL, ceiling TEXT NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
                cost TEXT, latency_ms INTEGER, outcome TEXT NOT NULL, error_class TEXT, verification TEXT, dropped INTEGER)""")
            db.execute(
                "CREATE INDEX IF NOT EXISTS axent_model_quota ON axent_model_calls(day, tenant_ref)"
            )

    def reserve(
        self,
        request: ReasoningRequest,
        *,
        now: datetime,
        provider: str,
        model: str,
        ceiling: Decimal,
    ) -> str | None:
        day = now.astimezone(UTC).date().isoformat()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            total, tenant = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(tenant_ref=?),0) FROM axent_model_calls WHERE day=?",
                (request.tenant_ref, day),
            ).fetchone()
            if total >= self.max_global_calls or tenant >= self.max_tenant_calls:
                return None
            ref = uuid4().hex
            db.execute(
                "INSERT INTO axent_model_calls VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'GROUNDED_ANSWER', ?, NULL, NULL, NULL, NULL, 'RESERVED', NULL, NULL, NULL)",
                (
                    ref,
                    request.request_id,
                    request.tenant_ref,
                    request.focus_ref,
                    day,
                    now.astimezone(UTC).isoformat(),
                    provider,
                    model,
                    str(ceiling),
                ),
            )
            return ref

    def result(self, ref: str, result: ReasoningResult, *, cost: Decimal | None) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "UPDATE axent_model_calls SET input_tokens=?, output_tokens=?, cost=?, latency_ms=?, outcome=?, error_class=? WHERE call_id=?",
                (
                    result.input_tokens,
                    result.output_tokens,
                    None if cost is None else str(cost),
                    result.latency_ms,
                    "UNAVAILABLE" if result.error_class else "RESULT_RECEIVED",
                    result.error_class,
                    ref,
                ),
            )

    def verified(self, ref: str, *, route: str, dropped: int) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "UPDATE axent_model_calls SET verification=?, dropped=? WHERE call_id=?",
                (route, dropped, ref),
            )
