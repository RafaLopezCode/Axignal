"""Sector context runner: prefiltered headlines judged for relevance, per activity and country.

Shared across organizations (one judgment per activity, country and UTC day), queued on
read and run in the background through the model router; nothing is asked inline.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.context.sector import (
    INSTRUCTION,
    MAX_CANDIDATES,
    SCHEMA,
    is_headline,
    judgment_prompt,
    mentions_keyword,
    sector_keywords,
    sector_label,
)
from cognition.jobs.model import CognitiveJob, JobKind
from pipeline.press.sqlite_store import SqlitePressIndex

WINDOW = timedelta(days=30)
MAX_PER_DAY = 60


class SectorContextRunner:
    def __init__(
        self,
        complete: Callable[[CognitiveJob], Any],
        model: str,
        press: SqlitePressIndex,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_per_day: int = MAX_PER_DAY,
    ) -> None:
        self._complete = complete
        self._model = model
        self._press = press
        self._clock = clock
        self._max_per_day = max_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS sector_context (
                    key TEXT PRIMARY KEY, capability_id TEXT, country TEXT, day TEXT,
                    state TEXT NOT NULL, result TEXT)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _key(self, capability_id: str, country: str, day: str) -> str:
        return f"{capability_id}|{country}|{day}"

    def latest(self, capability_id: str, country: str) -> Mapping[str, object] | None:
        """The most recent judged context for this activity and country (any earlier day)."""
        with self._connect() as db:
            row = db.execute(
                """SELECT result FROM sector_context WHERE capability_id=? AND country=?
                AND state='JUDGED' ORDER BY day DESC LIMIT 1""",
                (capability_id, country),
            ).fetchone()
        return None if row is None else dict(json.loads(row["result"]))

    def request(self, capability_id: str, country: str) -> None:
        if not sector_keywords(capability_id):
            return
        day = self._clock().date().isoformat()
        with self._connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO sector_context (key, capability_id, country, day, state)
                VALUES (?,?,?,?,'QUEUED')""",
                (self._key(capability_id, country, day), capability_id, country, day),
            )

    def run(self, *, max_runs: int = 3) -> int:
        now = self._clock()
        day = now.date().isoformat()
        with self._connect() as db:
            done = db.execute(
                "SELECT COUNT(*) FROM sector_context WHERE day=? AND state='JUDGED'", (day,)
            ).fetchone()[0]
            queued = db.execute(
                "SELECT key, capability_id, country FROM sector_context WHERE state='QUEUED' LIMIT ?",
                (max(0, min(max_runs, self._max_per_day - done)),),
            ).fetchall()
        ran = 0
        for row in queued:
            capability_id, country = str(row["capability_id"]), str(row["country"])
            keywords = sector_keywords(capability_id)
            candidates = [
                item
                for item in self._press.items_matching(keywords, since=now - WINDOW, limit=400)
                if item.country == country
                and is_headline(item.title)  # section labels never reach the judgment
                and mentions_keyword(item.title, keywords)
            ][:MAX_CANDIDATES]
            relevant: list[dict[str, object]] = []
            if candidates:
                try:
                    result = self._complete(
                        CognitiveJob(
                            id=f"sector-context:{uuid.uuid4().hex}",
                            kind=JobKind.SEMANTIC_DECISION,
                            instruction=INSTRUCTION,
                            context={
                                "schema": SCHEMA,
                                "user": judgment_prompt(
                                    str(sector_label(capability_id)), [c.title for c in candidates]
                                ),
                                "max_output_tokens": 300,
                            },
                        )
                    )
                except Exception:  # unavailable: stays queued for a later tick
                    continue
                payload = result.payload if hasattr(result, "payload") else {}
                answer = payload.get("answer") if isinstance(payload, Mapping) else None
                indexes = answer.get("relevant") if isinstance(answer, Mapping) else None
                for index in indexes if isinstance(indexes, list) else []:
                    if isinstance(index, int) and 0 <= index < len(candidates):
                        item = candidates[index]
                        relevant.append({"title": item.title, "url": item.url, "outlet": item.outlet,
                                         "publishedAt": item.published_at.isoformat()})  # fmt: skip
            stored = {
                "relevant": sorted(relevant, key=lambda r: str(r["publishedAt"]), reverse=True),
                "candidates": len(candidates),
                "judgedAt": now.isoformat(),
                "instrument": {"model": self._model, "router": "cognition/router"},
            }
            with self._connect() as db:
                db.execute(
                    "UPDATE sector_context SET state='JUDGED', result=? WHERE key=?",
                    (json.dumps(stored), row["key"]),
                )
            ran += 1
        return ran
