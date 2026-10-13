"""Public notoriety from Wikipedia, identified through the organization's official website.

The Wikidata item is accepted only when its official website (P856) is the organization's
own brand domain: never by name alone, so a homonym ("Wise", "Alan") cannot be taken for
it. Monthly pageviews of its articles in every language (Wikimedia REST API, open data)
measure public attention, not opinion. Each organization is refreshed weekly on the
source thread; reads only use what is stored.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from application.first_observation.service import brand_label

INSTRUMENT = "wikipedia-notoriety-v1"
USER_AGENT = "AXIGNAL/1.0 (https://axignal.com; economic observation) notoriety"
WIKIDATA = "https://www.wikidata.org/w/api.php"
PAGEVIEWS = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{lang}.wikipedia/all-access/user/{title}/monthly/{start}/{end}"
)
REFRESH = timedelta(days=7)
MAX_LANGUAGES = 12
MONTHS = 12
#: Larger wikis first: the languages read when an item has many.
_LANGUAGE_ORDER = (
    "en", "de", "fr", "es", "it", "pt", "nl", "sv", "no", "nb", "da", "fi", "pl", "ca",
    "ja", "ru", "zh", "ko", "ar", "tr", "cs", "nn",
)  # fmt: skip

Fetch = Callable[[str], Any]


def _http(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read(3_000_000))


class WikipediaNotoriety:
    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Fetch = _http,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._fetch = fetch
        self._clock = clock
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS notoriety (
                    key TEXT PRIMARY KEY, name TEXT NOT NULL, host TEXT NOT NULL,
                    requested_at TEXT NOT NULL, read_at TEXT, payload TEXT, error TEXT
                );
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    # ---- read side (subscriber views): stored results only ----------------------------
    def request(self, host: str, name: str) -> None:
        key = brand_label(host)
        with self._connect() as db:
            db.execute(
                """INSERT INTO notoriety (key, name, host, requested_at) VALUES (?,?,?,?)
                ON CONFLICT(key) DO UPDATE SET name=excluded.name, host=excluded.host""",
                (key, name[:200], host.lower(), self._clock().isoformat()),
            )

    def latest(self, host: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM notoriety WHERE key=?", (brand_label(host),)
            ).fetchone()
        return None if row is None or row[0] is None else dict(json.loads(row[0]))

    # ---- source thread ----------------------------------------------------------------
    def run(self, *, max_runs: int = 5) -> int:
        now = self._clock()
        with self._connect() as db:
            due = db.execute(
                """SELECT key, name, host FROM notoriety
                WHERE read_at IS NULL OR read_at <= ? ORDER BY read_at IS NOT NULL, read_at
                LIMIT ?""",
                ((now - REFRESH).isoformat(), max_runs),
            ).fetchall()
        done = 0
        for key, name, host in due:
            try:
                payload, error = self._read(name, host), None
            except Exception as failure:  # retried next week; the previous reading stays
                payload, error = None, type(failure).__name__
            with self._connect() as db:
                if payload is None:
                    db.execute(
                        "UPDATE notoriety SET read_at=?, error=? WHERE key=?",
                        (now.isoformat(), error, key),
                    )
                else:
                    db.execute(
                        "UPDATE notoriety SET read_at=?, payload=?, error=NULL WHERE key=?",
                        (now.isoformat(), json.dumps(payload, ensure_ascii=False), key),
                    )
            done += 1
        return done

    def _read(self, name: str, host: str) -> dict[str, Any]:
        now = self._clock()
        item = self._identify(name, host)
        payload: dict[str, Any] = {
            "instrument": INSTRUMENT,
            "readAt": now.isoformat(),
            "item": None,
            "rights": "Wikidata CC0 1.0; Wikimedia pageviews open data",
        }
        if item is None:
            return payload
        qid, website, links = item
        first_day = date(now.year, now.month, 1)
        start = (first_day - timedelta(days=MONTHS * 31)).replace(day=1)
        end = first_day - timedelta(days=1)  # complete months only
        monthly: dict[str, int] = {}
        by_language: dict[str, int] = {}
        for lang, title in links[:MAX_LANGUAGES]:
            url = PAGEVIEWS.format(
                lang=lang, title=urllib.parse.quote(title.replace(" ", "_"), safe=""),
                start=start.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"),
            )  # fmt: skip
            try:
                items = self._fetch(url).get("items") or []
            except Exception:  # an article with no views yet answers 404
                continue
            for point in items:
                month = f"{str(point['timestamp'])[:4]}-{str(point['timestamp'])[4:6]}"
                monthly[month] = monthly.get(month, 0) + int(point.get("views") or 0)
                if month == end.strftime("%Y-%m"):
                    by_language[lang] = int(point.get("views") or 0)
        payload.update(
            {
                "item": qid,
                "officialWebsite": website,
                "articles": [{"language": lang, "title": title} for lang, title in links],
                "monthly": dict(sorted(monthly.items())),
                "lastMonth": end.strftime("%Y-%m"),
                "byLanguage": dict(sorted(by_language.items(), key=lambda kv: -kv[1])),
            }
        )
        return payload

    def _identify(self, name: str, host: str) -> tuple[str, str, list[tuple[str, str]]] | None:
        """The item whose official website is this brand's; the richest when several."""
        bare = host.lower().removeprefix("www.")
        exact = "|".join(
            f"P856={scheme}://{prefix}{bare}{slash}"
            for scheme in ("https", "http")
            for prefix in ("", "www.")
            for slash in ("/", "")
        )
        found = (
            self._fetch(
                f"{WIKIDATA}?"
                + urllib.parse.urlencode(
                    {
                        "action": "query",
                        "list": "search",
                        "srlimit": "5",
                        "format": "json",
                        "srsearch": f"haswbstatement:{exact}",
                    }
                )
            )
            .get("query", {})
            .get("search")
            or []
        )
        # Both routes, always: the exact website may sit on a minor item while the main
        # one (with the articles) is found by name; only official-website matches count.
        search = self._fetch(
            f"{WIKIDATA}?"
            + urllib.parse.urlencode(
                {
                    "action": "wbsearchentities",
                    "search": name,
                    "language": "en",
                    "limit": "10",
                    "format": "json",
                }
            )
        )
        ids = list(
            dict.fromkeys(
                [str(hit["title"]) for hit in found if hit.get("title")]
                + [str(hit["id"]) for hit in search.get("search") or [] if hit.get("id")]
            )
        )
        if not ids:
            return None
        entities = (
            self._fetch(
                f"{WIKIDATA}?"
                + urllib.parse.urlencode(
                    {
                        "action": "wbgetentities",
                        "ids": "|".join(ids[:15]),
                        "props": "claims|sitelinks",
                        "format": "json",
                    }
                )
            ).get("entities")
            or {}
        )
        brand = brand_label(bare)
        best: tuple[int, str, str, list[tuple[str, str]]] | None = None
        for qid, entity in entities.items():
            websites = [
                str((claim.get("mainsnak") or {}).get("datavalue", {}).get("value") or "")
                for claim in (entity.get("claims") or {}).get("P856") or []
            ]
            own = next(
                (w for w in websites
                 if brand_label(urllib.parse.urlsplit(w).hostname or "") == brand),
                None,
            )  # fmt: skip
            if own is None:
                continue
            links = [
                (site[:-4], str(link["title"]))
                for site, link in (entity.get("sitelinks") or {}).items()
                if site.endswith("wiki") and site not in {"commonswiki", "specieswiki"}
            ]
            links.sort(
                key=lambda pair: (
                    _LANGUAGE_ORDER.index(pair[0]) if pair[0] in _LANGUAGE_ORDER else 99,
                    pair[0],
                )
            )
            if best is None or len(links) > best[0]:
                best = (len(links), qid, own, links)
        return None if best is None else (best[1], best[2], best[3])
