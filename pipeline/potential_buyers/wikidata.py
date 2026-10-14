"""Who an organization's customers are in Wikidata, and which organizations resemble them.

Two lookups, both CC0 Wikidata and both stored at world level (shared by every subscriber,
refreshed monthly on the source thread; subscriber reads only use what is stored):

* A customer named on a website (a logo wall, a public award) is looked up by its exact
  label or alias. It is accepted only when exactly one organization item matches: an item
  with an industry (P452) or an LEI (P1278). A name is not an identity: the match stays
  POTENTIAL and says how it was made (ADR-0099).
* Organizations in the same industry (P452) and country (P17) as a customer: the profile
  of who already buys, never a statement that they buy. Dissolved organizations (P576)
  are left out.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.world_demand.awards import normalized_name

INSTRUMENT = "wikidata-buyer-lookups-v1"
USER_AGENT = "AXIGNAL/1.0 (https://axignal.com; economic observation) buyers"
WIKIDATA = "https://www.wikidata.org/w/api.php"
RIGHTS = "Wikidata, CC0 1.0"
REFRESH = timedelta(days=30)
MAX_PEERS = 20
#: Languages a name is looked up in, after the organization's own published languages.
_LANGUAGES = ("en", "es", "de", "fr", "it", "pt")

Fetch = Callable[[str], Any]


def _http(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read(3_000_000))


def _values(claims: dict[str, Any], prop: str) -> list[Any]:
    out = []
    for claim in claims.get(prop) or []:
        if claim.get("rank") == "deprecated":
            continue
        value = (claim.get("mainsnak") or {}).get("datavalue", {}).get("value")
        if value is not None:
            out.append(value)
    return out


def _ids(claims: dict[str, Any], prop: str) -> list[str]:
    return [str(v["id"]) for v in _values(claims, prop) if isinstance(v, dict) and "id" in v]


def _label(entity: dict[str, Any], languages: Sequence[str]) -> str | None:
    labels = entity.get("labels") or {}
    for lang in (*languages, *_LANGUAGES):
        value = (labels.get(lang) or {}).get("value")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _organization(qid: str, entity: dict[str, Any], languages: Sequence[str]) -> dict[str, Any]:
    claims = entity.get("claims") or {}
    websites = [v for v in _values(claims, "P856") if isinstance(v, str)]
    leis = [v for v in _values(claims, "P1278") if isinstance(v, str)]
    return {
        "item": qid,
        "label": _label(entity, languages),
        "industries": _ids(claims, "P452"),
        "countries": _ids(claims, "P17"),
        "website": websites[0] if websites else None,
        "lei": leis[0] if leis else None,
        "dissolved": bool(_values(claims, "P576")),
    }


class WikidataBuyerLookups:
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
                CREATE TABLE IF NOT EXISTS buyer_lookups (
                    key TEXT PRIMARY KEY, query TEXT NOT NULL, requested_at TEXT NOT NULL,
                    read_at TEXT, payload TEXT, error TEXT
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
    def _request(self, key: str, query: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO buyer_lookups (key, query, requested_at) VALUES (?,?,?)
                ON CONFLICT(key) DO NOTHING""",
                (key, json.dumps(query, ensure_ascii=False), self._clock().isoformat()),
            )

    def _latest(self, key: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM buyer_lookups WHERE key=?", (key,)).fetchone()
        return None if row is None or row[0] is None else dict(json.loads(row[0]))

    @staticmethod
    def _customer_key(name: str) -> str:
        return f"customer:{normalized_name(name)}"

    @staticmethod
    def _peers_key(industry: str, country: str) -> str:
        return f"peers:{industry}:{country}"

    def request_customer(self, name: str, languages: Sequence[str] = ()) -> None:
        if normalized_name(name):
            self._request(
                self._customer_key(name), {"kind": "customer", "name": name[:200],
                                           "languages": list(languages)[:4]},
            )  # fmt: skip

    def customer(self, name: str) -> dict[str, Any] | None:
        return self._latest(self._customer_key(name)) if normalized_name(name) else None

    def request_peers(self, industry: str, country: str) -> None:
        self._request(
            self._peers_key(industry, country),
            {"kind": "peers", "industry": industry, "country": country},
        )

    def peers(self, industry: str, country: str) -> dict[str, Any] | None:
        return self._latest(self._peers_key(industry, country))

    # ---- source thread ----------------------------------------------------------------
    def run(self, *, max_runs: int = 10) -> int:
        now = self._clock()
        with self._connect() as db:
            due = db.execute(
                """SELECT key, query FROM buyer_lookups
                WHERE read_at IS NULL OR read_at <= ? ORDER BY read_at IS NOT NULL, read_at
                LIMIT ?""",
                ((now - REFRESH).isoformat(), max_runs),
            ).fetchall()
        done = 0
        for key, raw in due:
            query = json.loads(raw)
            try:
                payload, error = (
                    (
                        self._read_customer(str(query["name"]), query.get("languages") or [])
                        if query.get("kind") == "customer"
                        else self._read_peers(str(query["industry"]), str(query["country"]))
                    ),
                    None,
                )
            except Exception as failure:  # retried next month; the previous reading stays
                payload, error = None, type(failure).__name__
            with self._connect() as db:
                if payload is None:
                    db.execute(
                        "UPDATE buyer_lookups SET read_at=?, error=? WHERE key=?",
                        (now.isoformat(), error, key),
                    )
                else:
                    db.execute(
                        "UPDATE buyer_lookups SET read_at=?, payload=?, error=NULL WHERE key=?",
                        (now.isoformat(), json.dumps(payload, ensure_ascii=False), key),
                    )
            done += 1
        return done

    def _api(self, params: dict[str, str]) -> dict[str, Any]:
        found = self._fetch(f"{WIKIDATA}?{urllib.parse.urlencode({**params, 'format': 'json'})}")
        return found if isinstance(found, dict) else {}

    def _entities(self, ids: Sequence[str], languages: Sequence[str]) -> dict[str, Any]:
        if not ids:
            return {}
        langs = "|".join(dict.fromkeys((*languages, *_LANGUAGES)))
        return dict(
            self._api({"action": "wbgetentities", "ids": "|".join(ids[:50]),
                       "props": "claims|labels", "languages": langs}).get("entities") or {}
        )  # fmt: skip

    def _base(self) -> dict[str, Any]:
        return {"instrument": INSTRUMENT, "readAt": self._clock().isoformat(), "rights": RIGHTS}

    def _read_customer(self, name: str, languages: Sequence[str]) -> dict[str, Any]:
        """The one organization item whose label or alias is exactly this name."""
        wanted = normalized_name(name)
        hits: dict[str, None] = {}
        for lang in dict.fromkeys((*languages, *_LANGUAGES)):
            for hit in self._api({"action": "wbsearchentities", "search": name[:200],
                                  "language": lang, "type": "item", "limit": "7"}).get("search") or []:  # fmt: skip
                text = str((hit.get("match") or {}).get("text") or hit.get("label") or "")
                if normalized_name(text) == wanted and hit.get("id"):
                    hits[str(hit["id"])] = None
            if hits:
                break
        entities = self._entities(list(hits), languages)
        organizations = [
            _organization(qid, entity, languages)
            for qid, entity in entities.items()
            if isinstance(entity, dict)
        ]
        organizations = [o for o in organizations if o["industries"] or o["lei"]]
        payload = {**self._base(), "name": name, "item": None, "matchedBy": "EXACT_LABEL_OR_ALIAS"}
        if len(organizations) == 1:
            payload["item"] = organizations[0]
        elif len(organizations) > 1:
            payload["ambiguous"] = [o["item"] for o in organizations][:5]
        return payload

    def _read_peers(self, industry: str, country: str) -> dict[str, Any]:
        """Organizations Wikidata places in this industry and country (not dissolved)."""
        found = self._api({"action": "query", "list": "search", "srlimit": "40",
                           "srsearch": f"haswbstatement:P452={industry} haswbstatement:P17={country}"})  # fmt: skip
        titles = [str(h.get("title")) for h in (found.get("query") or {}).get("search") or []]
        wanted = [t for t in titles if t.startswith("Q")]
        entities = self._entities([*wanted, industry, country], ())
        peers = [
            _organization(qid, entities[qid], ())
            for qid in wanted  # in the search's own order
            if isinstance(entities.get(qid), dict)
        ]
        peers = [p for p in peers if p["label"] and not p["dissolved"]]
        return {**self._base(), "industry": industry, "country": country,
                "industryLabel": _label(entities.get(industry) or {}, ()),
                "countryLabel": _label(entities.get(country) or {}, ()),
                "organizations": peers[:MAX_PEERS]}  # fmt: skip
