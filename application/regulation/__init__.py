"""Regulation: new official rules and notices about an organization's activity, where it is.

Official journals only (BOE, EUR-Lex, Federal Register, legislation.gov.uk). Two steps,
kept apart as for sector context: a deterministic prefilter by the activity's governed
vocabulary and by where the rule applies (an EU act applies in every member state), then
a bounded, non-authoritative relevance judgment shared per activity, country and day.
What is shown is a POTENTIAL reading that a rule may concern the sector — never legal
advice, never a statement that it applies to this organization.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

MAX_CANDIDATES = 40
MAX_EU_CANDIDATES = 15


def regulation_phrases(capability_id: str) -> tuple[str, ...]:
    """The activity's own phrases ("seguridad privada"), folded: precise enough for titles
    of official journals, where single words ("seguridad", "desarrollo") are everywhere."""
    import unicodedata

    from application.observation_intelligence.catalog import CAPABILITY_LEXICON

    entry = next((e for e in CAPABILITY_LEXICON if e.capability_id == capability_id), None)
    if entry is None:
        from application.regulation.sectors import section_phrases

        return section_phrases(capability_id)  # known only by its ISIC section
    folded = {
        unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode().casefold().strip()
        for term in entry.terms
    }
    return tuple(sorted(t for t in folded if len(t) >= 5))


MAX_SHOWN = 6

INSTRUCTION = (
    "You screen official journal entries for a regulatory briefing about one economic "
    "sector. Return the indexes of the entries that set or change rules, obligations, "
    "standards, wages (collective agreements), subsidies or taxes for companies of that "
    "sector. Exclude appointments, individual cases, and entries that only share a word."
)
SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["relevant"],
    "properties": {"relevant": {"type": "array", "items": {"type": "integer"}}},
}


@dataclass(frozen=True, slots=True)
class RegulationItem:
    source: str  # BOE | EUR_LEX | FEDERAL_REGISTER | LEGISLATION_GOV_UK
    item_id: str
    title: str
    published: date
    scope: str  # where it applies: "EU/ES", "EU", "US", "GB"
    issuer: str | None
    url: str
    language: str
    kind: str | None = None

    def to_wire(self) -> dict[str, object]:
        return {
            "source": self.source, "id": self.item_id, "title": self.title,
            "published": self.published.isoformat(), "scope": self.scope,
            "issuer": self.issuer, "url": self.url, "language": self.language,
            "kind": self.kind,
        }  # fmt: skip


def applies_in(scope: str, country: str) -> bool:
    """Whether a rule published for ``scope`` applies in ``country`` (a GEO path)."""
    if scope == "EU":
        return country.startswith("EU/")
    return country == scope or country.startswith(scope + "/")


def judgment_prompt(sector: str, titles: Sequence[str]) -> str:
    lines = "\n".join(f"{i}. {t}" for i, t in enumerate(titles))
    return f"Sector: {sector}\nOfficial journal entries:\n{lines}"


def regulation_discoveries(
    result: Mapping[str, object], *, capability_id: str, sector: str | None, country: str,
    observed_at: str,
) -> list[dict[str, object]]:  # fmt: skip
    raw = result.get("relevant")
    items = [i for i in raw if isinstance(i, Mapping)] if isinstance(raw, list | tuple) else []
    basis = {
        "sector": sector,
        "capabilityId": capability_id,
        "country": country,
        "judgedAt": result.get("judgedAt"),
        "method": "Activity vocabulary and place prefilter, then a non-authoritative "
        "relevance judgment",
        "instrument": result.get("instrument"),
        "candidates": result.get("candidates"),
        "limitation": "An official publication that may concern the sector; whether and how it "
        "applies to this organization is not assessed. Not legal advice.",
    }
    return [
        {
            "kind": "CONTEXT_SIGNAL",
            "code": "REGULATION",
            "statement": str(item.get("title")),
            "epistemicState": "POTENTIAL",
            "sourceUrl": item.get("url"),
            "excerpt": None,
            "observedAt": str(item.get("published") or observed_at),
            "detail": {
                "journal": item.get("source"),
                "issuer": item.get("issuer"),
                "published": item.get("published"),
                "scope": item.get("scope"),
                "documentKind": item.get("kind"),
                **basis,
            },
        }
        for item in items[:MAX_SHOWN]
    ]
