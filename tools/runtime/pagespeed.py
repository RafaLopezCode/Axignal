"""PageSpeed runner: Lighthouse runs of the organizations' home pages, off the read path (spec 100).

Requests are queued when an observation is read; a background stage measures a few origins
per tick (each strategy is one lab run of 10-60 s), under a daily cap well inside the free
API quota. Each origin is measured at most once every 14 days and shared by every
subscriber. A refusal (an API key not allowed for this API, a quota) is recorded and retried
hours later, never in a loop. On when a Google API key file is mounted (the PageSpeed key,
else the CrUX key of the same Google project); AXIGNAL_PAGESPEED_ENABLED=false turns it off.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from application.web_quality import STRATEGIES

TTL = timedelta(days=14)
RETRY_AFTER = timedelta(hours=6)
MAX_PER_DAY = 150  # origins per UTC day, two lab runs each: far inside the free quota


class Lighthouse(Protocol):
    instrument: str

    def run(self, url: str, *, strategy: str) -> dict[str, object]: ...


class PageSpeedRunner:
    def __init__(
        self,
        lighthouse: Lighthouse,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        max_per_day: int = MAX_PER_DAY,
    ) -> None:
        self._lighthouse = lighthouse
        self._clock = clock
        self._max_per_day = max_per_day
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS pagespeed (
                    origin TEXT PRIMARY KEY, state TEXT NOT NULL, measurement TEXT,
                    requested_at TEXT NOT NULL, measured_at TEXT, failed_at TEXT, failure TEXT)"""
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

    def measurement(self, origin: str) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT measurement FROM pagespeed WHERE origin=? AND measurement IS NOT NULL",
                (origin,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["measurement"]))

    def request(self, origin: str) -> None:
        """Queue a measurement unless a fresh one exists or one is already queued."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, measured_at FROM pagespeed WHERE origin=?", (origin,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (row["measured_at"] and now - datetime.fromisoformat(row["measured_at"]) < TTL)
            ):
                return
            db.execute(
                """INSERT INTO pagespeed (origin, state, requested_at) VALUES (?,'QUEUED',?)
                ON CONFLICT(origin) DO UPDATE SET state='QUEUED', requested_at=excluded.requested_at""",
                (origin, now.isoformat()),
            )

    def run(self, *, max_runs: int = 2) -> int:
        now = self._clock()
        day = now.date().isoformat()
        retry = (now - RETRY_AFTER).isoformat()
        with self._connect() as db:
            done_today = db.execute(
                "SELECT COUNT(*) FROM pagespeed WHERE substr(measured_at,1,10)=?", (day,)
            ).fetchone()[0]
            queued = db.execute(
                """SELECT origin FROM pagespeed WHERE state='QUEUED'
                AND (failed_at IS NULL OR failed_at < ?) ORDER BY requested_at LIMIT ?""",
                (retry, max(0, min(max_runs, self._max_per_day - done_today))),
            ).fetchall()
        ran = 0
        for row in queued:
            origin = row["origin"]
            try:
                runs = [self._lighthouse.run(origin, strategy=s) for s in STRATEGIES]
            except Exception as error:  # refused or unavailable: retried hours later
                with self._connect() as db:
                    db.execute(
                        "UPDATE pagespeed SET failed_at=?, failure=? WHERE origin=?",
                        (self._clock().isoformat(), _failure(error), origin),
                    )
                continue
            measured_at = self._clock().isoformat()
            measurement = {
                "instrument": self._lighthouse.instrument,
                "origin": origin,
                "measuredAt": measured_at,
                "runs": runs,
                "cost": {"labRuns": len(runs), "usd": 0.0},
            }
            with self._connect() as db:
                db.execute(
                    """UPDATE pagespeed SET state='MEASURED', measurement=?, measured_at=?,
                    failed_at=NULL, failure=NULL WHERE origin=?""",
                    (json.dumps(measurement), measured_at, origin),
                )
            ran += 1
        return ran


def _failure(error: Exception) -> str:
    code = getattr(error, "code", None)
    return f"HTTP_{code}" if isinstance(code, int) else type(error).__name__


KEY_FILE = "AXIGNAL_PAGESPEED_API_KEY_FILE"
ENABLED = "AXIGNAL_PAGESPEED_ENABLED"
CRUX_KEY_FILE_ENV = "AXIGNAL_CRUX_API_KEY_FILE"


def pagespeed_from_values(values: Mapping[str, str], root: Path) -> PageSpeedRunner | None:
    """On when a readable Google API key file is mounted, unless explicitly turned off."""
    if values.get(ENABLED, "true").strip().lower() == "false":
        return None
    filename = values.get(KEY_FILE, "").strip() or os.environ.get(CRUX_KEY_FILE_ENV, "").strip()
    if not filename:
        return None
    key_file = Path(filename)
    if not key_file.is_absolute() or not key_file.is_file() or not os.access(key_file, os.R_OK):
        return None
    from pipeline.web_quality.pagespeed import PageSpeedInsights

    return PageSpeedRunner(PageSpeedInsights(key_file), root / "pagespeed.sqlite3")
