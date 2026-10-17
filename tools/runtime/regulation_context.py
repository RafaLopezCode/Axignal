"""Regulation runner: official journal entries about an activity, judged per country and day.

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

from application.context.headline_judgment import REGULATION, HeadlineJudge
from application.context.sector import sector_keywords, sector_label
from application.regulation import (
    INSTRUCTION,
    MAX_CANDIDATES,
    SCHEMA,
    judgment_prompt,
    regulation_phrases,
)
from cognition.jobs.model import CognitiveJob, JobKind
from pipeline.regulation.sqlite_store import SqliteRegulationIndex

WINDOW = timedelta(days=60)
MAX_PER_DAY = 60


class RegulationContextRunner:
    def __init__(
        self,
        complete: Callable[[CognitiveJob], Any] | None,
        model: str | None,
        index: SqliteRegulationIndex,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_per_day: int = MAX_PER_DAY,
        judge: HeadlineJudge | None = None,
    ) -> None:
        # Spec 082: Jev judges each entry when configured; the assistant is the fallback.
        self._judge = judge
        self._complete = complete
        self._model = model
        self.index = index
        self._clock = clock
        self._max_per_day = max_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS regulation_context (
                    key TEXT PRIMARY KEY, capability_id TEXT, country TEXT, language TEXT,
                    day TEXT, state TEXT NOT NULL, result TEXT)"""
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

    def latest(self, capability_id: str, country: str) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                """SELECT result FROM regulation_context WHERE capability_id=? AND country=?
                AND state='JUDGED' ORDER BY day DESC LIMIT 1""",
                (capability_id, country),
            ).fetchone()
        return None if row is None else dict(json.loads(row["result"]))

    def request(self, capability_id: str, country: str, language: str) -> None:
        if not regulation_phrases(capability_id):
            return
        day = self._clock().date().isoformat()
        with self._connect() as db:
            db.execute(
                """INSERT OR IGNORE INTO regulation_context
                (key, capability_id, country, language, day, state) VALUES (?,?,?,?,?,'QUEUED')""",
                (f"{capability_id}|{country}|{day}", capability_id, country, language, day),
            )

    def run(self, *, max_runs: int = 3) -> int:
        now = self._clock()
        day = now.date().isoformat()
        with self._connect() as db:
            done = db.execute(
                "SELECT COUNT(*) FROM regulation_context WHERE day=? AND state='JUDGED'", (day,)
            ).fetchone()[0]
            queued = db.execute(
                """SELECT key, capability_id, country, language FROM regulation_context
                WHERE state='QUEUED' LIMIT ?""",
                (max(0, min(max_runs, self._max_per_day - done)),),
            ).fetchall()
        ran = 0
        for row in queued:
            capability_id, country = str(row["capability_id"]), str(row["country"])
            candidates = self.index.candidates(
                country, regulation_phrases(capability_id),
                keywords=sector_keywords(capability_id), since=(now - WINDOW).date(),
                language=str(row["language"] or "en"), limit=MAX_CANDIDATES,
            )  # fmt: skip
            relevant: list[Mapping[str, object]] = []
            instrument: dict[str, object] = {"model": self._model, "router": "cognition/router"}
            verdict = None
            if candidates and self._judge is not None:
                try:
                    verdict = self._judge(str(sector_label(capability_id)),
                                          [str(c["title"]) for c in candidates], REGULATION, now)  # fmt: skip
                except Exception:
                    verdict = None  # unavailable: the assistant may still answer
            if verdict is not None:
                instrument = dict(verdict.instrument)
                relevant += [candidates[index] for index in verdict.kept]
            elif candidates:
                if self._complete is None:
                    continue  # nothing can judge now: stays queued for a later tick
                try:
                    result = self._complete(
                        CognitiveJob(
                            id=f"regulation-context:{uuid.uuid4().hex}",
                            kind=JobKind.SEMANTIC_DECISION,
                            instruction=INSTRUCTION,
                            context={
                                "schema": SCHEMA,
                                "user": judgment_prompt(
                                    str(sector_label(capability_id)),
                                    [str(c["title"]) for c in candidates],
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
                        relevant.append(candidates[index])
            stored = {
                "relevant": relevant,
                "candidates": len(candidates),
                "judgedAt": now.isoformat(),
                "instrument": instrument,
            }
            with self._connect() as db:
                db.execute(
                    "UPDATE regulation_context SET state='JUDGED', result=? WHERE key=?",
                    (json.dumps(stored), row["key"]),
                )
            ran += 1
        return ran
