"""Open, global registries of organizations with a website, per persona and country.

OpenStreetMap (Overpass API, ODbL) lists small and mid-sized offices by ``office=*`` with
their own website; Wikidata (CC0) lists larger organizations by class and country. Both
are public and keyless; nothing is scraped, and a source that refuses is skipped.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from application.marketing_pool.personas import Persona
from application.marketing_pool.policy import Market
from pipeline.marketing_pool.sqlite_store import Candidate, domain_of

USER_AGENT = "AXIGNAL/1.0 (+https://axignal.com; first-party discovery)"
OVERPASS = "https://overpass-api.de/api/interpreter"
WIKIDATA = "https://query.wikidata.org/sparql"

Fetch = Callable[[urllib.request.Request, float], bytes]


def _urlopen(request: urllib.request.Request, timeout: float) -> bytes:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return bytes(response.read(8_000_000))


def _website(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip().split(";")[0].strip()
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value if domain_of(value) else None


class OverpassDiscovery:
    name = "OSM"

    def __init__(self, fetch: Fetch = _urlopen, *, limit: int = 400) -> None:
        self._fetch = fetch
        self._limit = limit

    def find(self, persona: Persona, market: Market) -> list[Candidate]:
        selectors = "".join(
            f'nwr(area.a)["office"="{office}"]["website"];' for office in persona.osm_offices
        )
        query = (
            f'[out:json][timeout:120];area["ISO3166-1"="{market.iso}"][admin_level=2]->.a;'
            f"({selectors});out tags {self._limit};"
        )
        request = urllib.request.Request(
            OVERPASS,
            data=urllib.parse.urlencode({"data": query}).encode(),
            headers={"User-Agent": USER_AGENT},
        )
        payload: dict[str, Any] = json.loads(self._fetch(request, 150.0))
        out: list[Candidate] = []
        for element in payload.get("elements", []):
            tags = element.get("tags") or {}
            website = _website(tags.get("website") or tags.get("contact:website"))
            name = str(tags.get("name") or "").strip()
            if website and name:
                ref = f"osm:{element.get('type')}/{element.get('id')}"
                out.append(Candidate(name, website, market.iso, persona.id, self.name, ref))
        return out


class WikidataDiscovery:
    name = "WIKIDATA"

    def __init__(self, fetch: Fetch = _urlopen, *, limit: int = 300) -> None:
        self._fetch = fetch
        self._limit = limit

    def find(self, persona: Persona, market: Market) -> list[Candidate]:
        if not persona.wikidata_classes:
            return []
        classes = " ".join(f"wd:{q}" for q in persona.wikidata_classes)
        query = (
            "SELECT ?o ?oLabel ?site WHERE { VALUES ?c {" + classes + "} "
            f"?o wdt:P31 ?c; wdt:P17 wd:{market.wikidata}; wdt:P856 ?site. "
            "FILTER NOT EXISTS { ?o wdt:P576 ?end } "
            'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } '
            f"LIMIT {self._limit}"
        )
        request = urllib.request.Request(
            WIKIDATA + "?" + urllib.parse.urlencode({"query": query}),
            headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
        )
        payload: dict[str, Any] = json.loads(self._fetch(request, 90.0))
        out: list[Candidate] = []
        for row in payload.get("results", {}).get("bindings", []):
            website = _website(row.get("site", {}).get("value"))
            name = str(row.get("oLabel", {}).get("value") or "").strip()
            item = str(row.get("o", {}).get("value") or "")
            if website and name and not name.startswith("Q"):
                ref = "wikidata:" + item.rsplit("/", 1)[-1]
                out.append(Candidate(name, website, market.iso, persona.id, self.name, ref))
        return out
