"""Sector context: recent headlines about an organization's activity in its country.

Two steps, kept apart. A deterministic prefilter finds headlines containing the activity's
own vocabulary (from the governed lexicon) in the country's indexed press. Words are
broad ("seguridad" also matches social security), so a bounded, non-authoritative
judgment keeps only the headlines about that sector; it decides what is shown, never
what is true. Shared per activity and country per day, never per organization.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence

from application.observation_intelligence.catalog import CAPABILITY_LEXICON
from application.regulation.sectors import section_keywords, section_label

MAX_CANDIDATES = 40
MAX_SHOWN = 8
_GENERIC = frozenset(
    {
        "servicios", "services", "service", "servicio", "industrial", "industriales", "empresa",
        "empresas", "company", "companies", "sistemas", "systems", "system", "solutions",
        "soluciones", "instalacion", "installation", "instalaciones", "mantenimiento",
        "maintenance", "gestion", "management", "productos", "products", "proveedor", "provider",
        "dienstleistungen", "entreprise", "prodotti", "servizi", "servicos", "produtos",
        "consulting", "consultoria", "general", "generales", "compania", "azienda", "fabricante",
    }
)  # fmt: skip

INSTRUCTION = (
    "You screen news headlines for a sector briefing. Return the indexes of the headlines "
    "that are about the given sector (its market, prices, regulation, demand, technology, "
    "companies or workforce). Exclude headlines that only share a word with it."
)
SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["relevant"],
    "properties": {"relevant": {"type": "array", "items": {"type": "integer"}}},
}


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()


def sector_keywords(capability_id: str) -> tuple[str, ...]:
    entry = next((e for e in CAPABILITY_LEXICON if e.capability_id == capability_id), None)
    if entry is None:
        return section_keywords(capability_id)  # known only by its ISIC section
    words = {
        word
        for term in entry.terms
        for word in re.findall(r"[a-z]+", _fold(term))
        if len(word) >= 7 and word not in _GENERIC
    }
    return tuple(sorted(words))


def sector_label(capability_id: str) -> str | None:
    entry = next((e for e in CAPABILITY_LEXICON if e.capability_id == capability_id), None)
    return section_label(capability_id) if entry is None else entry.label


#: A section label ("CONSTRUCCIÓN", "Economía") is not a headline.
MIN_HEADLINE_WORDS = 4


def is_headline(title: str) -> bool:
    return len(title.split()) >= MIN_HEADLINE_WORDS


def mentions_keyword(title: str, keywords: Sequence[str]) -> bool:
    folded = _fold(title)
    return any(re.search(rf"\b{re.escape(k)}", folded) for k in keywords)


def judgment_prompt(sector: str, titles: Sequence[str]) -> str:
    lines = "\n".join(f"{i}. {t}" for i, t in enumerate(titles))
    return f"Sector: {sector}\nHeadlines:\n{lines}"


def context_discoveries(
    result: Mapping[str, object], *, capability_id: str, country: str, observed_at: str
) -> list[dict[str, object]]:
    raw = result.get("relevant")
    items = [
        i for i in (raw if isinstance(raw, list | tuple) else [])
        if isinstance(i, Mapping) and is_headline(str(i.get("title") or ""))
    ]  # fmt: skip
    basis = {
        "sector": sector_label(capability_id),
        "country": country,
        "judgedAt": result.get("judgedAt"),
        "method": "Lexicon prefilter, then a non-authoritative relevance judgment",
        "instrument": result.get("instrument"),
        "candidates": result.get("candidates"),
        "limitation": "Headlines from the indexed media about the sector, not about the "
        "organization; relevance is a judgment, not a fact.",
    }
    return [
        {
            "kind": "CONTEXT_SIGNAL",
            "code": "SECTOR_HEADLINE",
            "statement": str(item.get("title")),
            "epistemicState": "POTENTIAL",
            "sourceUrl": item.get("url"),
            "excerpt": None,
            "observedAt": str(item.get("publishedAt") or observed_at),
            "detail": {
                "outlet": item.get("outlet"),
                "publishedAt": item.get("publishedAt"),
                **basis,
            },
        }
        for item in items[:MAX_SHOWN]
    ]
