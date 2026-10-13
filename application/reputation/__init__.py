"""Reputation findings from global sources (any country, any language)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: Months compared for the trend: the latest three against the three before them.
TREND_MONTHS = 3


def notoriety_discoveries(result: Mapping[str, Any] | None) -> list[dict[str, object]]:
    """Public attention measured by Wikipedia pageviews of the organization's articles.

    OBSERVED: the article is identified through the organization's own official website
    in Wikidata, and the views are measured by Wikimedia. Attention is not opinion.
    """
    if not result or not result.get("item"):
        return []
    monthly = {str(k): int(v) for k, v in (result.get("monthly") or {}).items()}
    if not monthly:
        return []
    months = sorted(monthly)
    last = str(result.get("lastMonth") or months[-1])
    views = monthly.get(last, 0)
    recent = sum(monthly[m] for m in months[-TREND_MONTHS:])
    before = sum(monthly[m] for m in months[-2 * TREND_MONTHS : -TREND_MONTHS])
    trend = None if before <= 0 else round(recent / before - 1, 3)
    languages = [
        str(a.get("language")) for a in result.get("articles") or [] if isinstance(a, Mapping)
    ]
    return [
        {
            "kind": "MENTION",
            "code": "WIKIPEDIA_NOTORIETY",
            "statement": f"{views} Wikipedia views in {last}",
            "epistemicState": "OBSERVED",
            "sourceUrl": f"https://www.wikidata.org/wiki/{result['item']}",
            "excerpt": None,
            "observedAt": result.get("readAt"),
            "detail": {
                "views": views,
                "month": last,
                "monthly": monthly,
                "trend": trend,
                "languages": languages[:30],
                "byLanguage": dict(list((result.get("byLanguage") or {}).items())[:8]),
                "item": result["item"],
                "officialWebsite": result.get("officialWebsite"),
                "instrument": result.get("instrument"),
                "limitation": "Pageviews of its Wikipedia articles: public attention, not "
                "opinion or reputation quality. Identified through its official website in "
                "Wikidata.",
            },
        }
    ]
