"""Internet Archive's CDX index: the archived history of a website's home page (spec 102).

The Wayback Machine has archived public web pages since 1996 and publishes, per URL, when
it captured them and a digest of each capture's content. Only that is kept: capture dates,
HTTP status and content digest, collapsed to one capture per month. Nothing is fetched
from the archived pages here. The archive is a shared public service: errors raise
(unknown, retried later) and are never read as "no history".
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable

ENDPOINT = "https://web.archive.org/cdx/search/cdx"
INSTRUMENT = "internet-archive-wayback-cdx"
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"
LIMIT = 5000

Transport = Callable[[str], bytes]


def _http(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        body: bytes = response.read(20_000_000)
        return body


class WaybackIndex:
    instrument = INSTRUMENT

    def __init__(self, *, transport: Transport | None = None) -> None:
        self._transport = transport or _http

    def monthly_captures(self, host: str) -> list[tuple[str, str, str]]:
        """(timestamp, status, digest) of the home page, one capture per month, oldest first."""
        query = urllib.parse.urlencode(
            {"url": host, "output": "json", "fl": "timestamp,statuscode,digest",
             "collapse": "timestamp:6", "limit": str(LIMIT)}
        )  # fmt: skip
        body = self._transport(f"{ENDPOINT}?{query}")
        rows = json.loads(body or b"[]")
        return [
            (str(r[0]), str(r[1]), str(r[2]))
            for r in rows[1:]  # the first row names the fields
            if isinstance(r, list) and len(r) >= 3
        ]
