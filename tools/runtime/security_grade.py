"""HTTP security grade runner: Mozilla's Observatory for the organizations' sites, off the read path (spec 106).

Requests are queued when an observation is read; a background stage scans two hosts per tick
(a scan takes a few seconds). Security headers change rarely: a scan is kept 30 days and
shared by every subscriber. A failed scan is retried hours later, never read as a grade.
Free, no key; on unless AXIGNAL_SECURITY_GRADE_ENABLED=false.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

TTL = timedelta(days=30)
RETRY_AFTER = timedelta(hours=6)


class SecurityScanner(Protocol):
    instrument: str

    def scan(self, host: str) -> dict[str, object]: ...


class SecurityGradeRunner:
    def __init__(
        self,
        scanner: SecurityScanner,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._scanner = scanner
        self._clock = clock
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS security (
                    host TEXT PRIMARY KEY, state TEXT NOT NULL, measurement TEXT,
                    requested_at TEXT NOT NULL, measured_at TEXT, failed_at TEXT)"""
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

    def measurement(self, host: str) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT measurement FROM security WHERE host=? AND measurement IS NOT NULL",
                (host,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["measurement"]))

    def request(self, host: str) -> None:
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, measured_at FROM security WHERE host=?", (host,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (row["measured_at"] and now - datetime.fromisoformat(row["measured_at"]) < TTL)
            ):
                return
            db.execute(
                """INSERT INTO security (host, state, requested_at) VALUES (?,'QUEUED',?)
                ON CONFLICT(host) DO UPDATE SET state='QUEUED', requested_at=excluded.requested_at""",
                (host, now.isoformat()),
            )

    def run(self, *, max_runs: int = 2) -> int:
        now = self._clock()
        retry = (now - RETRY_AFTER).isoformat()
        with self._connect() as db:
            queued = db.execute(
                """SELECT host FROM security WHERE state='QUEUED'
                AND (failed_at IS NULL OR failed_at < ?) ORDER BY requested_at LIMIT ?""",
                (retry, max_runs),
            ).fetchall()
        ran = 0
        for row in queued:
            host = row["host"]
            try:
                scan = self._scanner.scan(host)
            except Exception:  # refused or failed: unknown, retried hours later
                with self._connect() as db:
                    db.execute(
                        "UPDATE security SET failed_at=? WHERE host=?",
                        (self._clock().isoformat(), host),
                    )
                continue
            measured_at = self._clock().isoformat()
            measurement = {
                "instrument": self._scanner.instrument,
                "host": host,
                "measuredAt": measured_at,
                "scan": scan,
            }
            with self._connect() as db:
                db.execute(
                    """UPDATE security SET state='MEASURED', measurement=?, measured_at=?,
                    failed_at=NULL WHERE host=?""",
                    (json.dumps(measurement), measured_at, host),
                )
            ran += 1
        return ran


ENABLED = "AXIGNAL_SECURITY_GRADE_ENABLED"


def security_grade_from_values(values: Mapping[str, str], root: Path) -> SecurityGradeRunner | None:
    if values.get(ENABLED, "true").strip().lower() == "false":
        return None
    from pipeline.web_quality.observatory import HttpObservatory

    return SecurityGradeRunner(HttpObservatory(), root / "security-grade.sqlite3")
