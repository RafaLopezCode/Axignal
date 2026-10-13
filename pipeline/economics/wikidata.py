"""Economic facts from Wikidata (CC0), resolved only by the organization's LEI (P1278).

Wikidata is a secondary, community-edited source: each fact is shown as what Wikidata
states, with its reference date and the item link, never as an official figure. Only
the most recent non-deprecated statement per property is kept. Cached 30 days per LEI.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"
#: property -> fact name; quantities keep amount and unit, items keep their label.
PROPERTIES = {
    "P2139": "revenue",
    "P2295": "netProfit",
    "P1128": "employees",
    "P2226": "marketCapitalization",
    "P571": "inception",
    "P414": "stockExchange",
    "P452": "industry",
}
#: Wikidata external identifiers of official business registers.
REGISTER_IDS = {
    "P5531": "SEC_CIK",
    "P1616": "SIREN",
    "P2622": "COMPANIES_HOUSE",
    "P2333": "ORGNR",
}


#: Common currencies by Wikidata item (labels are fetched for any other unit).
CURRENCIES = {
    "Q4916": "EUR", "Q4917": "USD", "Q25224": "GBP", "Q1104069": "CAD", "Q25344": "CHF",
    "Q8146": "JPY", "Q39099": "CNY", "Q173117": "BRL", "Q4730": "MXN", "Q80524": "INR",
    "Q259502": "AUD", "Q122922": "SEK", "Q25417": "DKK", "Q132643": "NOK", "Q123213": "PLN",
}  # fmt: skip


def _full(value: object) -> str:
    text = value.get("time") if isinstance(value, dict) else value
    return text.lstrip("+") if isinstance(text, str) else ""


def _time(value: object) -> str | None:
    text = value.get("time") if isinstance(value, dict) else value
    if not isinstance(text, str):
        return None
    year = text.lstrip("+")[:4]
    return year if year.isdigit() else None


class WikidataEconomics:
    def __init__(
        self,
        database_path: str | Path,
        *,
        fetch: Callable[[dict[str, str]], dict[str, Any]] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        ttl: timedelta = timedelta(days=30),
    ) -> None:
        self._fetch = fetch or self._http
        self._clock = clock
        self._ttl = ttl
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS wikidata_economics (lei TEXT PRIMARY KEY, payload TEXT, read_at TEXT)"
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
    def _http(params: dict[str, str]) -> dict[str, Any]:
        url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=15) as response:
            parsed = json.loads(response.read(3_000_000))
        return parsed if isinstance(parsed, dict) else {}

    def facts(self, lei: str) -> dict[str, object]:
        """{item, label, facts{name: {value, unit, year}}} or {item: None} when not in Wikidata."""
        now = self._clock()
        with self._connect() as db:
            row = db.execute(
                "SELECT payload, read_at FROM wikidata_economics WHERE lei=?", (lei,)
            ).fetchone()
        if row is not None and now - datetime.fromisoformat(row[1]) < self._ttl:
            return dict(json.loads(row[0]))
        if lei.startswith("item:"):  # an item already identified (by its official website)
            hits: list[Any] = [{"title": lei[5:]}]
        else:
            hits = (
                self._fetch(
                    {"action": "query", "list": "search", "srsearch": f"haswbstatement:P1278={lei}"}
                ).get("query")
                or {}
            ).get("search") or []
        payload: dict[str, object] = {
            "item": None,
            "readAt": now.isoformat(),
            "rights": "Wikidata, CC0 1.0",
        }
        candidates = [str(h.get("title")) for h in hits[:3] if h.get("title")]
        if candidates:
            entities = (
                self._fetch(
                    {
                        "action": "wbgetentities",
                        "ids": "|".join(candidates),
                        "props": "claims|labels",
                        "languages": "en",
                    }
                ).get("entities")
                or {}
            )
            # Several items may carry the same LEI (duplicates): the richest in economic
            # statements is read; the others are recorded, so the choice is inspectable.
            qid = max(
                candidates,
                key=lambda q: sum(
                    len((entities.get(q) or {}).get("claims", {}).get(p) or []) for p in PROPERTIES
                ),
            )
            entity = entities.get(qid) or {}
            payload["alsoCarryingLei"] = [q for q in candidates if q != qid]
            claims = entity.get("claims") or {}
            facts: dict[str, dict[str, object]] = {}
            referenced: set[str] = set()
            for prop, name in PROPERTIES.items():
                best: tuple[tuple[bool, str], dict[str, object]] | None = None
                for claim in claims.get(prop) or []:
                    if claim.get("rank") == "deprecated":
                        continue
                    value = (claim.get("mainsnak") or {}).get("datavalue", {}).get("value")
                    point = next(
                        (
                            q.get("datavalue", {}).get("value")
                            for q in (claim.get("qualifiers") or {}).get("P585", [])
                        ),
                        None,
                    )
                    when, exact = _time(point), _full(point)
                    fact: dict[str, object]
                    if isinstance(value, dict) and "amount" in value:
                        unit = str(value.get("unit") or "").rsplit("/", 1)[-1]
                        fact = {
                            "value": float(value["amount"]),
                            "unit": None if unit in {"", "1"} else unit,
                            "year": when,
                        }
                        if fact["unit"] in CURRENCIES:
                            fact["unitLabel"] = CURRENCIES[str(fact["unit"])]
                        elif fact["unit"]:
                            referenced.add(str(fact["unit"]))
                    elif isinstance(value, dict) and "time" in value:
                        fact = {"value": _time(value), "year": _time(value)}
                    elif isinstance(value, dict) and "id" in value:
                        fact = {"value": value["id"], "year": when}
                        referenced.add(str(value["id"]))
                    else:
                        continue
                    rank = (claim.get("rank") == "preferred", exact)
                    if (
                        best is None or rank > best[0]
                    ):  # preferred first, then the latest exact date
                        best = (rank, fact)
                if best is not None:
                    facts[name] = best[1]
            labels = self._labels(sorted(referenced)) if referenced else {}
            for fact in facts.values():
                for key in ("value", "unit"):
                    if isinstance(fact.get(key), str) and str(fact[key]) in labels:
                        fact[f"{key}Label"] = labels[str(fact[key])]
            # Official register identifiers the item carries: a second, LEI-anchored route
            # to official accounts (SEC EDGAR, INSEE/RNE, Companies House, Brønnøysund).
            registers: dict[str, str] = {}
            for prop, scheme in REGISTER_IDS.items():
                for claim in claims.get(prop) or []:
                    value = (claim.get("mainsnak") or {}).get("datavalue", {}).get("value")
                    if isinstance(value, str) and claim.get("rank") != "deprecated":
                        registers.setdefault(scheme, value.strip())
            payload["registers"] = registers
            # Its LEI, when the item states one: the route to GLEIF's group structure.
            stated = [
                (claim.get("mainsnak") or {}).get("datavalue", {}).get("value")
                for claim in claims.get("P1278") or []
                if claim.get("rank") != "deprecated"
            ]
            payload["lei"] = next((v for v in stated if isinstance(v, str) and v.strip()), None)
            payload.update(
                {
                    "item": qid,
                    "label": ((entity.get("labels") or {}).get("en") or {}).get("value"),
                    "facts": facts,
                }
            )
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO wikidata_economics VALUES (?,?,?)",
                (lei, json.dumps(payload), now.isoformat()),
            )
        return payload

    def facts_for_item(self, qid: str) -> dict[str, object]:
        """The same reading for an item identified otherwise (its official website)."""
        return self.facts(f"item:{qid}")

    def _labels(self, ids: list[str]) -> dict[str, str]:
        found: dict[str, str] = {}
        for start in range(0, len(ids), 40):
            entities = (
                self._fetch(
                    {
                        "action": "wbgetentities",
                        "ids": "|".join(ids[start : start + 40]),
                        "props": "labels",
                        "languages": "en",
                    }
                ).get("entities")
                or {}
            )
            for qid, entity in entities.items():
                label = ((entity.get("labels") or {}).get("en") or {}).get("value")
                if isinstance(label, str):
                    found[qid] = label
        return found
