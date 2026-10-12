"""Corporate group from GLEIF relationship data (Level 2): parents and subsidiaries, worldwide.

GLEIF publishes, under CC0, who owns whom among LEI holders: direct and ultimate parents
and direct children, each with its legal address. A group read here is registry data,
cached for a week at world level (one read per group, shared by every subscriber).
"""

from __future__ import annotations

import json
import sqlite3
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

API = "https://api.gleif.org/api/v1/lei-records/"
RIGHTS = "GLEIF LEI and relationship data, CC0 1.0"
MAX_BYTES = 2_000_000
CHILDREN_PAGE = 200
MAX_CHILDREN_PAGES = 5


def _entity(item: dict[str, Any]) -> dict[str, object] | None:
    attributes = item.get("attributes") if isinstance(item, dict) else None
    entity = attributes.get("entity") if isinstance(attributes, dict) else None
    if not isinstance(entity, dict):
        return None
    name = (entity.get("legalName") or {}).get("name")
    address = entity.get("legalAddress") or {}
    if not isinstance(name, str) or not name.strip():
        return None
    return {
        "lei": item.get("id"),
        "name": name.strip()[:300],
        "country": address.get("country"),
        "city": address.get("city"),
        "status": entity.get("status"),
    }


class GleifGroupReader:
    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Callable[[str], tuple[int, bytes]] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        ttl: timedelta = timedelta(days=7),
    ) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fetch = fetch or self._http
        self._clock = clock
        self._ttl = ttl
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS gleif_groups (lei TEXT PRIMARY KEY, payload TEXT, read_at TEXT)"
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
    def _http(url: str) -> tuple[int, bytes]:
        if not url.startswith(API):
            raise ValueError("GLEIF group reader only reads the GLEIF API")
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.api+json",
                "User-Agent": "AXIGNAL-SourceObserver/0.2",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return int(response.status), bytes(response.read(MAX_BYTES))
        except urllib.error.HTTPError as error:  # 404: no parent reported
            return int(error.code), b""

    def _json(self, url: str) -> dict[str, Any] | None:
        status, body = self._fetch(url)
        if status == 404:
            return None
        if status != 200:
            raise RuntimeError(f"GLEIF_HTTP_{status}")
        parsed = json.loads(body)
        return parsed if isinstance(parsed, dict) else None

    def group(self, lei: str) -> dict[str, object]:
        """Parents and subsidiaries of an LEI holder (cached); raises when GLEIF fails."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT payload, read_at FROM gleif_groups WHERE lei=?", (lei,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row[1]) < self._ttl:
            return dict(json.loads(row[0]))
        parents: dict[str, object] = {}
        for level in ("direct-parent", "ultimate-parent"):
            data = self._json(f"{API}{lei}/{level}")
            entity = None if data is None else _entity(data.get("data") or {})
            if entity is not None:
                parents[level] = entity
        children: list[dict[str, object]] = []
        total: object = None
        for page in range(1, MAX_CHILDREN_PAGES + 1):  # bounded: up to 1,000 subsidiaries
            doc = (
                self._json(
                    f"{API}{lei}/direct-children?page[size]={CHILDREN_PAGE}&page[number]={page}"
                )
                or {}
            )
            children += [e for i in doc.get("data") or [] if (e := _entity(i))]
            pagination = (doc.get("meta") or {}).get("pagination") or {}
            total = pagination.get("total", total)
            if page >= int(pagination.get("lastPage") or 1):
                break
        payload = {
            "lei": lei,
            "parents": parents,
            "children": children,
            "childrenTotal": total if isinstance(total, int) else len(children),
            "readAt": now.isoformat(),
            "rights": RIGHTS,
        }
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO gleif_groups VALUES (?,?,?)",
                (lei, json.dumps(payload), now.isoformat()),
            )
        return payload
