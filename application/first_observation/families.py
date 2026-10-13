"""The family each subscriber finding belongs to (mirrors the web facets).

One place for every consumer outside the web (MCP, marketing pool, evaluation): a
finding belongs to the family it speaks for, never to the producer that emitted it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

FAMILIES: tuple[str, ...] = (
    "presence", "reputation", "value", "markets", "relationships",
    "demand", "activity", "economics", "organization", "context",
)  # fmt: skip

BY_KIND: dict[str, str] = {
    "PUBLIC_PRESENCE": "presence",
    "WEB_REPRESENTATION": "presence",
    "REPRESENTATION_GAP": "presence",
    "LANGUAGES": "presence",
    "SEARCH_VISIBILITY": "presence",
    "GENERATIVE_VISIBILITY": "presence",
    "ACTIVITY": "value",
    "CREDENTIAL": "value",
    "DECLARED_LOCATION": "markets",
    "DECLARED_SERVICE_AREA": "markets",
    "IDENTITY_HINT": "organization",
    "DEMAND": "demand",
    "MENTION": "reputation",
    "RATING": "reputation",
    "RELATIONSHIP": "relationships",
    "COMPETITION": "relationships",
    "CONTEXT_SIGNAL": "context",
    "ECONOMIC_FACT": "economics",
    "OPERATING_SIGNAL": "activity",
}
#: A grounded unknown names what is unknown through its code (":<jurisdiction>" suffix).
BY_UNKNOWN_CODE: dict[str, str] = {
    "ROBOTS_DISALLOWED": "presence",
    "NOT_AN_OPERATING_BUSINESS_SITE": "presence",
    "IDENTITY_NOT_VERIFIED": "organization",
    "ACTIVITY_NOT_ESTABLISHED": "value",
    "NO_GOVERNED_DEMAND_SOURCE": "demand",
    "NO_RELEVANT_DEMAND_FOUND": "demand",
    "NO_PRESS_MENTION_FOUND": "reputation",
    "NO_PUBLIC_AWARDS_FOUND": "relationships",
}


def family_of(discovery: Mapping[str, Any]) -> str | None:
    kind = str(discovery.get("kind") or "")
    code = str(discovery.get("code") or "")
    if kind == "SIGNIFICANT_UNKNOWN":
        return BY_UNKNOWN_CODE.get(code.split(":")[0])
    if kind in {"INXIGHT", "CHANGE"}:  # crossings and changes speak for their family
        prefix = code.split(":")[0]
        return prefix if prefix in FAMILIES else None
    if kind == "MENTION" and code in {"OWN_PUBLICATION", "PRESS_RELEASE"}:
        return "activity"  # its own channels are its activity
    return BY_KIND.get(kind)
