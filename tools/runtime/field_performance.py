"""Real-user performance of an origin from the Chrome UX Report (CrUX), cached per origin.

CrUX publishes, per origin with enough real Chrome traffic, the 75th percentile of Core Web
Vitals over a rolling 28-day window. Many small sites have no record: that is "not enough
real-user traffic observed", never a failing grade. One query per origin a week, shared by
every subscriber (the window moves slowly). The key file is the same governed secret the
SEO truth sync already uses.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from domain.admin_seo_truth import CruxFormFactor

KEY_FILE_ENV = "AXIGNAL_CRUX_API_KEY_FILE"
METRICS = ("largest_contentful_paint", "interaction_to_next_paint", "cumulative_layout_shift")


class CruxFieldPerformance:
    def __init__(
        self,
        query: Callable[[str], dict[str, Any] | None],
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        ttl: timedelta = timedelta(days=7),
    ) -> None:
        self._query = query
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock
        self._ttl = ttl
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS crux_origins (origin TEXT PRIMARY KEY, payload TEXT, read_at TEXT)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def measure(self, origin: str) -> dict[str, object]:
        """{state: MEASURED|NO_DATA, ...}; raises when CrUX cannot be asked (UNKNOWN)."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT payload, read_at FROM crux_origins WHERE origin=?", (origin,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row[1]) < self._ttl:
            return dict(json.loads(row[0]))
        record = self._query(origin)
        payload: dict[str, object]
        if record is None:
            payload = {"state": "NO_DATA", "formFactor": "PHONE"}
        else:
            metrics = record.get("metrics") if isinstance(record.get("metrics"), dict) else {}
            p75: dict[str, float] = {}
            for name in METRICS:
                percentiles = (
                    (metrics.get(name) or {}).get("percentiles")
                    if isinstance(metrics, dict)
                    else None
                )
                if isinstance(percentiles, dict) and percentiles.get("p75") is not None:
                    p75[name] = float(percentiles["p75"])
            period = record.get("collectionPeriod") or {}
            payload = {
                "state": "MEASURED" if p75 else "NO_DATA",
                "formFactor": "PHONE",
                "p75": p75,
                "period": {
                    "first": _date(period.get("firstDate")),
                    "last": _date(period.get("lastDate")),
                },
                "instrument": "Chrome UX Report API (28-day real-user window)",
            }
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO crux_origins VALUES (?,?,?)",
                (origin, json.dumps(payload), now.isoformat()),
            )
        return payload


def _date(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    try:
        return f"{int(value['year']):04d}-{int(value['month']):02d}-{int(value['day']):02d}"
    except (KeyError, TypeError, ValueError):
        return None


def field_performance_from_env(root: Path) -> CruxFieldPerformance | None:
    """Configured only when the governed CrUX key file is mounted and readable."""
    filename = os.environ.get(KEY_FILE_ENV, "").strip()
    if not filename:
        return None
    path = Path(filename)
    if not path.is_file() or not os.access(path, os.R_OK):
        return None
    from tools.runtime.seo_truth_sync import ChromeUxReportClient

    client = ChromeUxReportClient.from_file(path)
    return CruxFieldPerformance(
        lambda origin: client.query(origin=origin, form_factor=CruxFormFactor.PHONE),
        root / "crux-origins.sqlite3",
    )
