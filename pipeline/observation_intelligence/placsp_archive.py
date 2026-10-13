"""Backfill of public contract awards from PLACSP's official monthly archives.

The live feed is read incrementally, so it only brings awards published from now on.
The platform also publishes, per month, a zip of every entry updated in that month
(open data, same CODICE/ATOM format). Reading the recent months once gives the awards
history that clients, competitors, recurrent buyers and partners are computed from.

One month at a time, newest first, resumable: each month is downloaded to a temporary
file, its awards are kept (only with a plausible award date), the file is deleted, and
the month is recorded. A failed month is retried the next day.
"""

from __future__ import annotations

import sqlite3
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from application.world_demand.awards import AwardRecord
from pipeline.observation_intelligence.placsp import HOSTS, parse_feed_awards

ARCHIVE = (
    "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/"
    "licitacionesPerfilesContratanteCompleto3_{month}.zip"
)
MAX_ARCHIVE_BYTES = 2_000_000_000
EARLIEST_AWARD = date(2015, 1, 1)
RETRY_AFTER = timedelta(days=1)

Download = Callable[[str, Path], None]


def _download(url: str, target: Path) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in HOSTS:
        raise ValueError("PLACSP archives only come from the platform's own hosts")
    request = urllib.request.Request(
        url, headers={"User-Agent": "AXIGNAL-SourceObserver/0.2 (awards backfill)"}
    )
    written = 0
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as out:
        while chunk := response.read(1 << 20):
            written += len(chunk)
            if written > MAX_ARCHIVE_BYTES:
                raise ValueError("PLACSP archive too large")
            out.write(chunk)


def months_back(today: date, count: int) -> list[str]:
    """The last ``count`` complete months, newest first (``YYYYMM``)."""
    year, month = today.year, today.month
    out: list[str] = []
    for _ in range(count):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        out.append(f"{year:04d}{month:02d}")
    return out


class PlacspAwardsBackfill:
    def __init__(
        self,
        sink: Callable[[Sequence[AwardRecord]], int],
        state_path: str | Path,
        work_dir: str | Path,
        *,
        months: int = 12,
        download: Download = _download,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._sink = sink
        self._months = months
        self._download = download
        self._clock = clock
        self._work = Path(work_dir)
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS wd_awards_backfill (
                    month TEXT PRIMARY KEY, state TEXT NOT NULL, at TEXT NOT NULL,
                    awards INTEGER NOT NULL DEFAULT 0, error TEXT)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=30)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def pending(self) -> list[str]:
        now = self._clock()
        with self._connect() as db:
            rows = {r[0]: (r[1], r[2]) for r in db.execute(
                "SELECT month, state, at FROM wd_awards_backfill")}  # fmt: skip
        out = []
        for month in months_back(now.date(), self._months):
            state = rows.get(month)
            if state is None or (
                state[0] == "FAILED" and now - datetime.fromisoformat(state[1]) >= RETRY_AFTER
            ):
                out.append(month)
        return out

    def status(self) -> list[tuple[str, str, int, str | None]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT month, state, awards, error FROM wd_awards_backfill ORDER BY month DESC"
            ).fetchall()
        return [(str(m), str(st), int(n), None if e is None else str(e)) for m, st, n, e in rows]

    def run_one(self) -> int | None:
        """Backfill the newest pending month; the awards kept, or None when none is due."""
        pending = self.pending()
        if not pending:
            return None
        month = pending[0]
        self._work.mkdir(parents=True, exist_ok=True)
        horizon = self._clock().date() + timedelta(days=31)
        kept = 0
        try:
            with tempfile.TemporaryDirectory(dir=self._work) as scratch:
                archive = Path(scratch) / f"{month}.zip"
                self._download(ARCHIVE.format(month=month), archive)
                with zipfile.ZipFile(archive) as bundle:
                    for member in bundle.namelist():
                        if not member.endswith(".atom"):
                            continue
                        awards = [
                            a
                            for a in parse_feed_awards(bundle.read(member))
                            if a.awarded_on is None or EARLIEST_AWARD <= a.awarded_on <= horizon
                        ]
                        kept += self._sink(awards)
        except Exception as error:  # a failed month is retried tomorrow
            self._record(month, "FAILED", kept, type(error).__name__)
            return 0
        self._record(month, "DONE", kept, None)
        return kept

    def _record(self, month: str, state: str, awards: int, error: str | None) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO wd_awards_backfill VALUES (?,?,?,?,?)",
                (month, state, self._clock().isoformat(), awards, error),
            )
