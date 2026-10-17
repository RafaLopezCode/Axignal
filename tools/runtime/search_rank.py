"""Search ranking runner: reads the searches of an organization's activity, off the read path.

Requests are queued when an observation is read; a background stage measures a few per
tick under a global daily cap (each search is a paid API query). Each organization is
measured at most once every 30 days; the result is stored with its instrument,
conditions, cost and date, and only then shown. Off unless the API key file is mounted.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.search_visibility import SearchSubject, evaluate, keywords
from pipeline.search_visibility.brave import INSTRUMENT, MAX_COUNT, BraveSearch, SearchResult

TTL = timedelta(days=30)
MAX_PER_DAY = 40  # organizations measured per UTC day, all tenants together
USD_PER_QUERY = 0.005  # list price of the API's base plan; recorded with every measurement

Search = Callable[..., list[SearchResult]]


class SearchRankRunner:
    def __init__(
        self,
        search: Search,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_per_day: int = MAX_PER_DAY,
    ) -> None:
        self._search = search
        self._clock = clock
        self._max_per_day = max_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS search_ranks (
                    subject_key TEXT PRIMARY KEY, subject TEXT NOT NULL, state TEXT NOT NULL,
                    measurement TEXT, requested_at TEXT NOT NULL, measured_at TEXT)"""
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

    def measurement(self, subject: SearchSubject) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT measurement FROM search_ranks WHERE subject_key=? AND state='MEASURED'",
                (subject.key,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["measurement"]))

    def request(self, subject: SearchSubject) -> None:
        """Queue a measurement unless a fresh one exists or one is already queued."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, measured_at FROM search_ranks WHERE subject_key=?", (subject.key,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (row["measured_at"] and now - datetime.fromisoformat(row["measured_at"]) < TTL)
            ):
                return
            db.execute(
                """INSERT INTO search_ranks (subject_key, subject, state, requested_at)
                VALUES (?,?,'QUEUED',?) ON CONFLICT(subject_key) DO UPDATE SET
                state='QUEUED', requested_at=excluded.requested_at""",
                (subject.key, json.dumps(_wire(subject)), now.isoformat()),
            )

    def run(self, *, max_runs: int = 2) -> int:
        now = self._clock()
        day = now.date().isoformat()
        with self._connect() as db:
            done_today = db.execute(
                "SELECT COUNT(*) FROM search_ranks WHERE substr(measured_at,1,10)=?", (day,)
            ).fetchone()[0]
            queued = db.execute(
                "SELECT subject_key, subject FROM search_ranks WHERE state='QUEUED' ORDER BY requested_at LIMIT ?",
                (max(0, min(max_runs, self._max_per_day - done_today)),),
            ).fetchall()
        ran = 0
        for row in queued:
            wire = json.loads(row["subject"])
            subject = SearchSubject(**{**wire, "terms": tuple(wire["terms"])})
            searched = keywords(subject)
            try:
                found = [
                    [r.to_wire() for r in self._search(
                        q, country=subject.country, language=subject.language, count=MAX_COUNT
                    )]
                    for q in searched
                ]  # fmt: skip
            except Exception:  # unavailable: stays queued for a later tick, nothing invented
                continue
            measurement = {
                "instrument": {"name": INSTRUMENT, "depth": MAX_COUNT},
                "country": subject.country.upper(),
                "language": subject.language,
                "measuredAt": self._clock().isoformat(),
                "result": evaluate(subject, found),
                "cost": {"queries": len(searched), "usd": round(len(searched) * USD_PER_QUERY, 4)},
            }
            with self._connect() as db:
                db.execute(
                    "UPDATE search_ranks SET state='MEASURED', measurement=?, measured_at=? WHERE subject_key=?",
                    (json.dumps(measurement), measurement["measuredAt"], row["subject_key"]),
                )
            ran += 1
        return ran


def _wire(subject: SearchSubject) -> dict[str, object]:
    return {
        "name": subject.name, "domain": subject.domain, "terms": list(subject.terms),
        "country": subject.country, "language": subject.language,
    }  # fmt: skip


def search_rank_from_values(values: Mapping[str, str], root: Path) -> SearchRankRunner | None:
    """On only when the API key file is mounted and readable; off otherwise (no failure)."""
    filename = values.get("AXIGNAL_BRAVE_SEARCH_KEY_FILE", "").strip()
    if not filename:
        return None
    key_file = Path(filename)
    if not key_file.is_absolute() or not key_file.is_file() or not os.access(key_file, os.R_OK):
        return None
    return SearchRankRunner(BraveSearch(key_file).search, root / "search-ranks.sqlite3")
