"""Brave Search API: the web results an independent search index returns for a query.

The API is a licensed product for this use (an account key, per-query pricing, a plan whose
terms allow storing results); Google forbids automated queries and AXIGNAL never scrapes it.
Only what a ranking needs is kept: position, URL and title. The key is read from a file
mounted as a secret, never from an environment variable or a log.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
INSTRUMENT = "brave-search-api.web.v1"
#: Countries the API accepts as a market; any other is searched worldwide ("ALL").
COUNTRIES = frozenset(
    [
        "AR",
        "AU",
        "AT",
        "BE",
        "BR",
        "CA",
        "CL",
        "DK",
        "FI",
        "FR",
        "DE",
        "HK",
        "IN",
        "ID",
        "IT",
        "JP",
        "KR",
        "MY",
        "MX",
        "NL",
        "NZ",
        "NO",
        "PL",
        "PT",
        "PH",
        "SA",
        "ZA",
        "ES",
        "SE",
        "CH",
        "TW",
        "TR",
        "GB",
        "US",
    ]
)
_LANGUAGES = {"es": "es", "en": "en", "fr": "fr", "de": "de", "it": "it", "nl": "nl"}
MAX_COUNT = 20  # the API's page size


@dataclass(frozen=True, slots=True)
class SearchResult:
    position: int
    url: str
    title: str

    def to_wire(self) -> dict[str, object]:
        return {"position": self.position, "url": self.url, "title": self.title}


Transport = Callable[[str, Mapping[str, str]], bytes]


def _http(url: str, headers: Mapping[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=dict(headers))
    with urllib.request.urlopen(request, timeout=15) as response:
        body: bytes = response.read(2_000_000)
        return body


def search_language(language: str, country: str) -> str:
    """The API's language code (Portuguese is split by variety)."""
    if language == "pt":
        return "pt-br" if country.upper() == "BR" else "pt-pt"
    return _LANGUAGES.get(language, "en")


class BraveSearch:
    def __init__(self, key_file: str | Path, *, transport: Transport | None = None) -> None:
        self._key_file = Path(key_file)
        self._transport = transport or _http

    def search(
        self, query: str, *, country: str, language: str, count: int = MAX_COUNT
    ) -> list[SearchResult]:
        """Up to `count` organic web results, in order; raises when the API is unavailable."""
        market = country.upper() if country.upper() in COUNTRIES else "ALL"
        params = {
            "q": query,
            "country": market,
            "search_lang": search_language(language, country),
            "count": str(max(1, min(count, MAX_COUNT))),
            "safesearch": "moderate",
        }
        key = self._key_file.read_text(encoding="utf-8").strip()
        payload = json.loads(
            self._transport(
                f"{ENDPOINT}?{urllib.parse.urlencode(params)}",
                {"Accept": "application/json", "X-Subscription-Token": key},
            )
        )
        web = payload.get("web") if isinstance(payload, Mapping) else None
        items = web.get("results") if isinstance(web, Mapping) else None
        out: list[SearchResult] = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, Mapping) and isinstance(item.get("url"), str):
                out.append(
                    SearchResult(len(out) + 1, str(item["url"]), str(item.get("title") or ""))
                )
        return out
