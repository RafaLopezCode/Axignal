"""Common Crawl runner: open-corpus capture of the organizations' domains, off the read path (spec 101).

Requests are queued when an observation is read; a background stage asks the public index
about one domain per tick (three crawls: the latest counted, two previous for presence),
gently, because the index is a shared and often busy service. Crawls are monthly: a
measurement is kept 30 days and shared by every subscriber. A busy index (5xx, timeout)
is retried hours later; a 404 is a crawl without captures. Free, no key; on unless
AXIGNAL_COMMON_CRAWL_ENABLED=false.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from pipeline.open_corpus.common_crawl import Captures

TTL = timedelta(days=30)
RETRY_AFTER = timedelta(hours=3)
CRAWLS = 3


class CaptureIndex(Protocol):
    instrument: str

    def crawls(self) -> list[str]: ...

    def captures(self, crawl: str, domain: str, *, limit: int) -> Captures: ...


class CommonCrawlRunner:
    def __init__(
        self,
        index: CaptureIndex,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._index = index
        self._clock = clock
        self._crawls: tuple[str, list[str]] | None = None  # (day, ids)
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS corpus (
                    domain TEXT PRIMARY KEY, state TEXT NOT NULL, measurement TEXT,
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

    def measurement(self, domain: str) -> Mapping[str, object] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT measurement FROM corpus WHERE domain=? AND measurement IS NOT NULL",
                (domain,),
            ).fetchone()
        return None if row is None else dict(json.loads(row["measurement"]))

    def request(self, domain: str) -> None:
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT state, measured_at FROM corpus WHERE domain=?", (domain,)
            ).fetchone()
            if row is not None and (
                row["state"] == "QUEUED"
                or (row["measured_at"] and now - datetime.fromisoformat(row["measured_at"]) < TTL)
            ):
                return
            db.execute(
                """INSERT INTO corpus (domain, state, requested_at) VALUES (?,'QUEUED',?)
                ON CONFLICT(domain) DO UPDATE SET state='QUEUED', requested_at=excluded.requested_at""",
                (domain, now.isoformat()),
            )

    def _latest_crawls(self) -> list[str]:
        day = self._clock().date().isoformat()
        if self._crawls is None or self._crawls[0] != day:
            self._crawls = (day, self._index.crawls()[:CRAWLS])
        return self._crawls[1]

    def run(self, *, max_runs: int = 1) -> int:
        now = self._clock()
        retry = (now - RETRY_AFTER).isoformat()
        with self._connect() as db:
            queued = db.execute(
                """SELECT domain FROM corpus WHERE state='QUEUED'
                AND (failed_at IS NULL OR failed_at < ?) ORDER BY requested_at LIMIT ?""",
                (retry, max_runs),
            ).fetchall()
        ran = 0
        for row in queued:
            domain = row["domain"]
            try:
                crawls = self._latest_crawls()
                found = [
                    asdict(self._index.captures(crawl, domain, limit=1000 if i == 0 else 1))
                    for i, crawl in enumerate(crawls)
                ]
            except Exception:  # the index is busy: unknown, retried hours later
                with self._connect() as db:
                    db.execute(
                        "UPDATE corpus SET failed_at=? WHERE domain=?",
                        (self._clock().isoformat(), domain),
                    )
                continue
            if not found:
                continue
            measured_at = self._clock().isoformat()
            measurement = {
                "instrument": self._index.instrument,
                "domain": domain,
                "measuredAt": measured_at,
                "crawls": found,
            }
            with self._connect() as db:
                db.execute(
                    """UPDATE corpus SET state='MEASURED', measurement=?, measured_at=?,
                    failed_at=NULL WHERE domain=?""",
                    (json.dumps(measurement), measured_at, domain),
                )
            ran += 1
        return ran


ENABLED = "AXIGNAL_COMMON_CRAWL_ENABLED"


def common_crawl_from_values(values: Mapping[str, str], root: Path) -> CommonCrawlRunner | None:
    if values.get(ENABLED, "true").strip().lower() == "false":
        return None
    from pipeline.open_corpus.common_crawl import CommonCrawlIndex

    return CommonCrawlRunner(CommonCrawlIndex(), root / "common-crawl.sqlite3")
