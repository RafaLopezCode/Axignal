"""Common Crawl index: which of a site's pages an open web crawl captured (spec 101).

Common Crawl publishes a free, open crawl of the web roughly monthly; many language models
are trained on it. Its CDX index answers, per crawl, which URLs of a domain were captured
(a 404 means none were). Only counts are kept: captures and successful (HTTP 200) captures
in the latest crawl, and whether each of the previous crawls captured the domain at all.
The index is a shared, often busy public service: 5xx answers raise (unknown, retried
later) and are never read as absence.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

COLLECTIONS = "https://index.commoncrawl.org/collinfo.json"
INSTRUMENT = "common-crawl-cdx-index"
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"
LIMIT = 1000


class NotCaptured(Exception):
    """The crawl holds no capture of the domain (the index answered 404)."""


Transport = Callable[[str], bytes]


def _http(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body: bytes = response.read(20_000_000)
            return body
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise NotCaptured from error
        raise


@dataclass(frozen=True, slots=True)
class Captures:
    crawl: str
    captures: int  # capped at LIMIT
    ok: int  # captures answered with HTTP 200
    capped: bool


class CommonCrawlIndex:
    instrument = INSTRUMENT

    def __init__(self, *, transport: Transport | None = None) -> None:
        self._transport = transport or _http

    def crawls(self) -> list[str]:
        """Crawl ids, newest first."""
        data = json.loads(self._transport(COLLECTIONS))
        return [str(c["id"]) for c in data if isinstance(c, dict) and c.get("id")]

    def captures(self, crawl: str, domain: str, *, limit: int = LIMIT) -> Captures:
        """Captures of the domain (subdomains included) in one crawl; 0 when none."""
        query = urllib.parse.urlencode(
            {"url": domain, "matchType": "domain", "output": "json", "fl": "status",
             "limit": str(limit)}
        )  # fmt: skip
        try:
            body = self._transport(f"https://index.commoncrawl.org/{crawl}-index?{query}")
        except NotCaptured:
            return Captures(crawl, 0, 0, False)
        rows = [json.loads(line) for line in body.decode("utf-8").splitlines() if line.strip()]
        ok = sum(1 for row in rows if str(row.get("status")) == "200")
        return Captures(crawl, len(rows), ok, len(rows) >= limit)
