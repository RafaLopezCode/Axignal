"""DeepSeek Search API: candidate web pages for a query (spec 098).

A licensed, per-request API (``POST /v1/tools/search``; $0.75 per 1,000 successful
requests, empty or failed ones are not billed). Only what research needs is kept: URL,
title, site name, the index's relevance score and date. The provider's ``summary`` and
``content`` are never kept: they are not evidence, and AXIGNAL reads every page itself.
The key is read from a file mounted as a secret, never from an environment variable or a
log. Replaceable: any :class:`application.web_research.WebSearch` serves the research.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path

from application.web_research import WebHit

ENDPOINT = "https://api.deepseek.com/v1/tools/search"
INSTRUMENT = "deepseek-search-api.v1"
MAX_COUNT = 20
MAX_QUERY_CHARS = 128
USD_PER_REQUEST = 0.00075

Transport = Callable[[str, Mapping[str, str], bytes], bytes]


def _http(url: str, headers: Mapping[str, str], body: bytes) -> bytes:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload: bytes = response.read(4_000_000)
        return payload


class DeepSeekSearch:
    instrument = INSTRUMENT

    def __init__(self, key_file: str | Path, *, transport: Transport | None = None) -> None:
        self._key_file = Path(key_file)
        self._transport = transport or _http

    def search(self, query: str, *, count: int = 10) -> list[WebHit]:
        """Candidate pages in the index's order; raises when the API is unavailable."""
        key = self._key_file.read_text(encoding="utf-8").strip()
        body = json.dumps(
            {"query": query[:MAX_QUERY_CHARS], "count": max(1, min(count, MAX_COUNT))}
        ).encode("utf-8")
        payload = json.loads(
            self._transport(
                ENDPOINT,
                {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                body,
            )
        )
        items = payload.get("results") if isinstance(payload, Mapping) else None
        out: list[WebHit] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, Mapping) or not isinstance(item.get("url"), str):
                continue
            score = item.get("rerank_score")
            out.append(
                WebHit(
                    url=str(item["url"]),
                    title=str(item.get("title") or ""),
                    site_name=str(item["site_name"]) if item.get("site_name") else None,
                    rerank=float(score) if isinstance(score, int | float) else None,
                    indexed_date=str(item["date"])[:10] if item.get("date") else None,
                )
            )
        return out
