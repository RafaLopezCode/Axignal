"""Append-only ledger of AXENT research requests: attention, never conclusions.

One row per tenant, Xeed, subject, scope and dependency fingerprint. Reads are
always scoped to one tenant and Xeed. Nothing here is canonical state.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from application.axent.grounded.answer import ResearchRequest
from application.axent.research import MAX_SELECTED_PER_TICK, ResearchState
from application.observation_runtime.families import ObservationFamily
from application.observation_runtime.ports import LeaseLost, TickClaim


class SqliteResearchRequestLedger:
    def __init__(self, database_path: str | Path, *, runtime_path: Path | None = None) -> None:
        self._path = Path(database_path)
        self._runtime_path = runtime_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self._path)) as db, db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS axent_research_requests (
                    request_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, xeed_id TEXT NOT NULL,
                    family TEXT, geographies TEXT NOT NULL, reason TEXT NOT NULL,
                    question_kind TEXT NOT NULL, created_at TEXT NOT NULL)"""
            )
            columns = {r[1] for r in db.execute("PRAGMA table_info(axent_research_requests)")}
            for name in ("organization_id", "dependency_fingerprint"):
                if name not in columns:
                    db.execute(
                        f"ALTER TABLE axent_research_requests ADD COLUMN {name} TEXT NOT NULL DEFAULT ''"
                    )
            db.execute("""CREATE TABLE IF NOT EXISTS axent_research_lifecycle (
                request_id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL,
                next_eligible TEXT, tick_day TEXT, tick_token TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS axent_research_transitions (
                sequence INTEGER PRIMARY KEY, request_id TEXT NOT NULL,
                observed_at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL,
                tick_day TEXT, tick_token TEXT)""")
            db.execute("""INSERT OR IGNORE INTO axent_research_lifecycle
                SELECT request_id, 'PENDING', '{"attempts":0,"work_ids":[],"evidence_keys":[]}', NULL, NULL, NULL
                FROM axent_research_requests""")

    def request(self, item: ResearchRequest) -> bool:
        with closing(sqlite3.connect(self._path)) as db, db:
            cursor = db.execute(
                "INSERT OR IGNORE INTO axent_research_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item.request_id,
                    item.tenant_id,
                    item.xeed_id,
                    None if item.family is None else item.family.value,
                    json.dumps(list(item.geographies)),
                    item.reason,
                    item.question_kind,
                    item.created_at.isoformat(),
                    item.organization_id,
                    item.dependency_fingerprint,
                ),
            )
            inserted = cursor.rowcount == 1
            if inserted:
                db.execute(
                    "INSERT INTO axent_research_lifecycle VALUES (?, 'PENDING', ?, NULL, NULL, NULL)",
                    (
                        item.request_id,
                        json.dumps({"attempts": 0, "work_ids": [], "evidence_keys": []}),
                    ),
                )
                db.execute(
                    "INSERT INTO axent_research_transitions VALUES (NULL, ?, ?, 'PENDING', ?, NULL, NULL)",
                    (item.request_id, item.created_at.isoformat(), '{"attempts":0}'),
                )
            return inserted

    @staticmethod
    def _state(row: sqlite3.Row) -> ResearchState:
        raw = json.loads(row["payload"])
        return ResearchState(
            ResearchRequest(
                row["request_id"],
                row["tenant_id"],
                row["xeed_id"],
                None if row["family"] is None else ObservationFamily(row["family"]),
                tuple(json.loads(row["geographies"])),
                row["reason"],
                row["question_kind"],
                datetime.fromisoformat(row["created_at"]),
                row["organization_id"],
                row["dependency_fingerprint"],
            ),
            status=row["status"],
            attempts=raw["attempts"],
            last_attempt=None
            if raw.get("last_attempt") is None
            else datetime.fromisoformat(raw["last_attempt"]),
            next_eligible=None
            if row["next_eligible"] is None
            else datetime.fromisoformat(row["next_eligible"]),
            outcome=raw.get("outcome"),
            work_ids=tuple(raw["work_ids"]),
            evidence_keys=tuple(raw["evidence_keys"]),
            shared_work_key=raw.get("shared_work_key"),
        )

    def eligible(self, now: datetime) -> tuple[ResearchState, ...]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """SELECT r.*, l.* FROM axent_research_requests r JOIN axent_research_lifecycle l USING(request_id)
                WHERE l.status IN ('PENDING', 'CLAIMED', 'FAILED_RETRYABLE')
                AND (l.next_eligible IS NULL OR l.next_eligible<=?)
                ORDER BY r.created_at, r.request_id LIMIT ?""",
                (now.astimezone(UTC).isoformat(), MAX_SELECTED_PER_TICK),
            ).fetchall()
        return tuple(self._state(row) for row in rows)

    def save(self, state: ResearchState, claim: TickClaim, *, now: datetime) -> None:
        if self._runtime_path is None:
            raise LeaseLost("research lifecycle requires the existing runtime fence")
        with closing(sqlite3.connect(self._path)) as db, db:
            db.execute("ATTACH DATABASE ? AS runtime", (str(self._runtime_path),))
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT token, completed_at, lease_expires_at FROM runtime.aor_ticks WHERE day=?",
                (claim.day,),
            ).fetchone()
            if (
                row is None
                or row[0] != claim.token
                or row[1] is not None
                or datetime.fromisoformat(row[2]) <= now
            ):
                raise LeaseLost("research lifecycle lost its T12 authority")
            raw = asdict(state)
            raw.pop("request")
            payload = json.dumps(raw, default=lambda value: value.isoformat())
            db.execute(
                """UPDATE axent_research_lifecycle SET status=?, payload=?, next_eligible=?, tick_day=?, tick_token=? WHERE request_id=?""",
                (
                    state.status,
                    payload,
                    None
                    if state.next_eligible is None
                    else state.next_eligible.astimezone(UTC).isoformat(),
                    claim.day,
                    claim.token,
                    state.request.request_id,
                ),
            )
            db.execute(
                "INSERT INTO axent_research_transitions VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                (
                    state.request.request_id,
                    now.isoformat(),
                    state.status,
                    payload,
                    claim.day,
                    claim.token,
                ),
            )

    def states(self, *, tenant_id: str, xeed_id: str) -> tuple[ResearchState, ...]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """SELECT r.*, l.* FROM axent_research_requests r JOIN axent_research_lifecycle l USING(request_id)
                WHERE tenant_id=? AND xeed_id=? ORDER BY created_at, request_id""",
                (tenant_id, xeed_id),
            ).fetchall()
        return tuple(self._state(row) for row in rows)

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
