"""Reverse geocoding with OpenStreetMap Nominatim: a point to its country, region and place.

Nominatim's usage policy is honoured: an identifying User-Agent, at most one request per
second, and every answer cached (a world-level cache keyed by the point rounded to ~100 m,
so a place is asked once for every organization). Data © OpenStreetMap contributors (ODbL);
the attribution travels with every answer.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ATTRIBUTION = "© OpenStreetMap contributors (ODbL), via Nominatim"
ENDPOINT = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"


@dataclass(frozen=True, slots=True)
class Place:
    country_code: str | None  # ISO 3166-1 alpha-2, upper-case
    region_code: str | None  # ISO 3166-2 subdivision, e.g. ES-MD, US-CA
    region: str | None
    locality: str | None
    attribution: str = ATTRIBUTION


class NominatimReverseGeocoder:
    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Callable[[str], bytes] | None = None,
        min_interval_s: float = 1.1,
    ) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fetch = fetch or self._http
        self._min_interval_s = min_interval_s
        self._last = 0.0
        self._lock = threading.Lock()
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS geo_reverse (
                    point TEXT PRIMARY KEY, payload TEXT NOT NULL, fetched_at TEXT NOT NULL)"""
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _http(url: str) -> bytes:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return bytes(response.read(200_000))

    def place(self, latitude: float, longitude: float) -> Place | None:
        """The place at a point, from cache or one polite request; None when unknown."""
        key = f"{latitude:.3f},{longitude:.3f}"
        with self._connect() as db:
            row = db.execute("SELECT payload FROM geo_reverse WHERE point=?", (key,)).fetchone()
        if row is None:
            with self._lock:  # one request at a time, at least min_interval apart
                wait = self._min_interval_s - (time.monotonic() - self._last)
                if wait > 0:
                    time.sleep(wait)
                query = urllib.parse.urlencode(
                    {"format": "jsonv2", "lat": f"{latitude:.5f}", "lon": f"{longitude:.5f}", "zoom": "10", "addressdetails": "1"}
                )  # fmt: skip
                try:
                    raw = self._fetch(f"{ENDPOINT}?{query}")
                finally:
                    self._last = time.monotonic()
            address = json.loads(raw).get("address") or {}
            with self._connect() as db:
                db.execute(
                    "INSERT OR REPLACE INTO geo_reverse VALUES (?,?,?)",
                    (key, json.dumps(address), datetime.now(UTC).isoformat()),
                )
        else:
            address = json.loads(row[0])
        if not isinstance(address, dict) or not address.get("country_code"):
            return None
        region_code = address.get("ISO3166-2-lvl4") or address.get("ISO3166-2-lvl6")
        return Place(
            country_code=str(address["country_code"]).upper(),
            region_code=None if not region_code else str(region_code).upper(),
            region=address.get("state") or address.get("region") or address.get("province"),
            locality=address.get("city") or address.get("town") or address.get("village") or address.get("municipality"),
        )  # fmt: skip
