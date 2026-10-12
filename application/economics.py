"""Economic magnitudes as discoveries, each with its source, date and attribution.

A figure read from a secondary, community-edited source (Wikidata) is shown as what that
source states, with its reference year; it is not an official account. Attribution to this
organization is OBSERVED only through its verified LEI; through an LEI its website merely
declares, it stays POTENTIAL. A magnitude without a reference year says so.
"""

from __future__ import annotations

from collections.abc import Mapping

ORDER = (
    "revenue",
    "netProfit",
    "employees",
    "marketCapitalization",
    "inception",
    "stockExchange",
    "industry",
)


def economic_discoveries(
    facts: Mapping[str, object], *, verified: bool, observed_at: str
) -> list[dict[str, object]]:
    item = facts.get("item")
    values = facts.get("facts")
    if not item or not isinstance(values, Mapping):
        return []
    out: list[dict[str, object]] = []
    for name in ORDER:
        fact = values.get(name)
        if not isinstance(fact, Mapping) or fact.get("value") is None:
            continue
        out.append(
            {
                "kind": "ECONOMIC_FACT",
                "code": f"WIKIDATA:{name}",
                "statement": str(fact.get("valueLabel") or fact.get("value")),
                "epistemicState": "OBSERVED" if verified else "POTENTIAL",
                "sourceUrl": f"https://www.wikidata.org/wiki/{item}",
                "excerpt": None,
                "observedAt": observed_at,
                "detail": {
                    "fact": name,
                    "value": fact.get("value"),
                    "unit": fact.get("unitLabel") or fact.get("unit"),
                    "year": fact.get("year"),
                    "source": "Wikidata",
                    "sourceKind": "SECONDARY_COMMUNITY_EDITED",
                    "item": item,
                    "alsoCarryingLei": facts.get("alsoCarryingLei"),
                    "attributedBy": "VERIFIED_LEI" if verified else "LEI_DECLARED_ON_WEBSITE",
                    "rights": facts.get("rights"),
                    "readAt": facts.get("readAt"),
                    "limitation": "What Wikidata states, with its reference year; not an official "
                    "account and possibly outdated.",
                },
            }
        )
    return out
