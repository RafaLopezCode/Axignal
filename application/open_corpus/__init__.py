"""Is the organization's website in the open web corpus language models learn from? (spec 101)

Common Crawl's monthly crawls are an open corpus that many language models are trained on.
Whether a crawl captured a site's pages is a GEO signal an agency can act on (robots.txt
rules for CCBot, crawlability, internal links), measured with its instrument, crawl,
date and limits (MASTER §54). Being captured does not mean any given model learned,
remembers or cites the organization; not being captured may be the crawl's sampling, a
robots.txt rule or the site's size. An unanswered index is UNKNOWN, never absence.
"""

from __future__ import annotations

from collections.abc import Mapping

UNCERTAINTY = (
    "Common Crawl samples the web: being captured does not mean a given AI model learned or "
    "cites it, and not being captured may be the crawl's sampling, a robots.txt rule for "
    "CCBot or the site's size."
)


def corpus_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    """One finding: captured in the latest crawl (with how many pages) or not captured."""
    raw = measurement.get("crawls")
    crawls = [c for c in raw if isinstance(c, Mapping)] if isinstance(raw, list) else []
    if not crawls:
        return []
    latest = crawls[0]
    captured = int(str(latest.get("ok") or 0)) > 0
    previous = [c for c in crawls[1:] if int(str(c.get("captures") or 0)) > 0]
    return [
        {
            "kind": "GENERATIVE_VISIBILITY",
            "code": "OPEN_CORPUS_CAPTURED" if captured else "OPEN_CORPUS_NOT_CAPTURED",
            "statement": str(latest.get("ok") or 0),
            "epistemicState": "OBSERVED",
            "sourceUrl": None,
            "excerpt": None,
            "observedAt": str(measurement.get("measuredAt") or observed_at),
            "detail": {
                "instrument": measurement.get("instrument"),
                "conditions": {
                    "domain": measurement.get("domain"),
                    "crawl": latest.get("crawl"),
                    "subdomainsIncluded": True,
                },
                "measuredAt": measurement.get("measuredAt"),
                "sample": "The domain's captures in the latest crawl, and whether each of the "
                "previous crawls captured it",
                "uncertainty": UNCERTAINTY,
                "captures": latest.get("captures"),
                "okCaptures": latest.get("ok"),
                "capped": latest.get("capped"),
                "previousCrawls": [c.get("crawl") for c in crawls[1:]],
                "capturedInPrevious": len(previous),
            },
        }
    ]
