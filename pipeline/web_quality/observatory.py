"""MDN HTTP Observatory: how a website protects its visitors over HTTP (spec 106).

Mozilla's public Observatory API (v2, free, no key) scans a host's HTTPS redirection, HSTS,
content security policy and other security headers, and grades it (A+ to F) with a score and
how many of its checks pass. Only that summary is kept, with its scan time and the public
page that details each check. A failed scan raises (unknown, retried later).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping

ENDPOINT = "https://observatory-api.mdn.mozilla.net/api/v2/scan"
INSTRUMENT = "mdn-http-observatory.v2"
USER_AGENT = "AXIGNAL-SourceObserver/0.2 (+https://axignal.com)"

Transport = Callable[[str], bytes]


def _http(url: str) -> bytes:
    request = urllib.request.Request(
        url, data=b"", headers={"User-Agent": USER_AGENT}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body: bytes = response.read(200_000)
        return body


class HttpObservatory:
    instrument = INSTRUMENT

    def __init__(self, *, transport: Transport | None = None) -> None:
        self._transport = transport or _http

    def scan(self, host: str) -> dict[str, object]:
        """The grade summary for a host; raises when the scan failed or was refused."""
        payload = json.loads(
            self._transport(f"{ENDPOINT}?{urllib.parse.urlencode({'host': host})}")
        )
        if not isinstance(payload, Mapping) or payload.get("error") or not payload.get("grade"):
            raise ValueError(
                f"observatory scan failed: {payload.get('error') if isinstance(payload, Mapping) else 'invalid'}"
            )
        return {
            "grade": str(payload.get("grade")),
            "score": payload.get("score"),
            "testsPassed": payload.get("tests_passed"),
            "testsFailed": payload.get("tests_failed"),
            "testsQuantity": payload.get("tests_quantity"),
            "scannedAt": payload.get("scanned_at"),
            "detailsUrl": payload.get("details_url"),
        }
