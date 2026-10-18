"""PageSpeed Insights API: a Lighthouse run of a public page by Google's own service (spec 100).

A licensed, free API (``pagespeedonline/v5/runPagespeed``) that loads the page in Google's
lab, with a fixed, simulated device and network, and returns Lighthouse's category scores
(SEO, performance, accessibility, best practices) and the audits behind them. Only what a
measurement needs is kept: the instrument version, the conditions (strategy, form factor,
throttling), the time, the four scores and the audits that do not pass. The key is read
from a file mounted as a secret, never from an environment variable or a log.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path

ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
INSTRUMENT = "pagespeed-insights-api.v5"
CATEGORIES = {
    "seo": "SEO",
    "performance": "PERFORMANCE",
    "accessibility": "ACCESSIBILITY",
    "best-practices": "BEST_PRACTICES",
}
#: An audit at or above this score passes (Lighthouse shows it green).
PASSING = 0.9
MAX_FAILING = 12

Transport = Callable[[str], bytes]


def _http(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:  # a lab run takes 10-60 s
        body: bytes = response.read(30_000_000)
        return body


class PageSpeedInsights:
    instrument = INSTRUMENT

    def __init__(self, key_file: str | Path, *, transport: Transport | None = None) -> None:
        self._key_file = Path(key_file)
        self._transport = transport or _http

    def run(self, url: str, *, strategy: str) -> dict[str, object]:
        """One lab run (``strategy`` MOBILE or DESKTOP); raises when the API is unavailable."""
        key = self._key_file.read_text(encoding="utf-8").strip()
        params = [("url", url), ("strategy", strategy.lower()), ("key", key)]
        params += [("category", c) for c in CATEGORIES.values()]
        payload = json.loads(self._transport(f"{ENDPOINT}?{urllib.parse.urlencode(params)}"))
        return summarize(payload, strategy=strategy.upper())


def summarize(payload: Mapping[str, object], *, strategy: str) -> dict[str, object]:
    """The measurement kept from one API answer: scores 0-100 and the failing audits."""
    result = payload.get("lighthouseResult")
    if not isinstance(result, Mapping):
        raise ValueError("no Lighthouse result")
    categories = result.get("categories") if isinstance(result.get("categories"), Mapping) else {}
    audits = result.get("audits") if isinstance(result.get("audits"), Mapping) else {}
    assert isinstance(categories, Mapping) and isinstance(audits, Mapping)
    scores: dict[str, int | None] = {}
    failing: dict[str, list[dict[str, object]]] = {}
    for key, name in CATEGORIES.items():
        category = categories.get(key)
        if not isinstance(category, Mapping):
            continue
        score = category.get("score")
        scores[name] = round(float(score) * 100) if isinstance(score, int | float) else None
        rows: list[dict[str, object]] = []
        for ref in category.get("auditRefs") or []:
            if not isinstance(ref, Mapping) or not ref.get("weight"):
                continue
            audit = audits.get(str(ref.get("id")))
            value = audit.get("score") if isinstance(audit, Mapping) else None
            if isinstance(audit, Mapping) and isinstance(value, int | float) and value < PASSING:
                rows.append(
                    {"id": ref.get("id"), "title": audit.get("title"), "score": round(value, 2)}
                )
        failing[name] = rows[:MAX_FAILING]
    settings = (
        result.get("configSettings") if isinstance(result.get("configSettings"), Mapping) else {}
    )
    assert isinstance(settings, Mapping)
    return {
        "strategy": strategy,
        "lighthouseVersion": result.get("lighthouseVersion"),
        "fetchTime": result.get("fetchTime"),
        "finalUrl": result.get("finalDisplayedUrl") or result.get("finalUrl"),
        "formFactor": settings.get("formFactor"),
        "throttling": settings.get("throttlingMethod"),
        "scores": scores,
        "failing": failing,
    }
