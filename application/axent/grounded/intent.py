"""Question → (kind, canonical families, geographies), deterministic and multilingual.

No model is involved: the lexicon maps everyday words in the six product
languages to the ten canonical families, so resolution is free, reproducible
and cannot see any tenant data. A follow-up that names no family inherits the
previous turn's family; a new geography narrows it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

from application.axent.grounded.corpus import fold
from application.observation_runtime.families import ObservationFamily

_F = ObservationFamily


class QuestionKind(StrEnum):
    OVERVIEW = "OVERVIEW"
    COUNT = "COUNT"
    WHY = "WHY"
    HOW_KNOWN = "HOW_KNOWN"
    CHANGE = "CHANGE"
    UNKNOWNS = "UNKNOWNS"


#: Stems in es/en/fr/de/it/pt, matched on accent-folded lowercase text.
FAMILY_LEXICON: dict[ObservationFamily, tuple[str, ...]] = {
    _F.PRESENCE: (
        "seo",
        "geo ",
        "posicion",
        "visibil",
        "buscador",
        "google",
        "search",
        "sichtbar",
        "referenc",
        "indexa",
        "web",
        "presenc",
        "presence",
        "chatgpt",
        "generativ",
        "llm",
    ),
    _F.REPUTATION: (
        "reseña",
        "resena",
        "opinion",
        "review",
        "dicen de",
        "say about",
        "reputa",
        "comentari",
        "bewertung",
        "avis",
        "recensi",
        "avalia",
        "ruf ",
    ),
    _F.DEMAND: (
        "oportunidad",
        "opportunit",
        "licitac",
        "tender",
        "demand",
        "concurso",
        "contrat",
        "appel d",
        "ausschreib",
        "gara",
        "bando",
        "concorr",
        "oportunidade",
        "chance",
    ),
    _F.RELATIONSHIPS: (
        "cliente",
        "client",
        "customer",
        "partner",
        "socio",
        "proveedor",
        "supplier",
        "fournisseur",
        "lieferant",
        "fornitor",
        "fornecedor",
        "kunde",
        "distribuid",
    ),
    _F.VALUE: (
        "servicio",
        "service",
        "producto",
        "product",
        "ofrec",
        "offer",
        "capacid",
        "capabil",
        "angebot",
        "leistung",
        "offre",
        "serviz",
        "servic",
        "capacit",
    ),
    _F.ORGANIZATION: (
        "quien es",
        "quienes son",
        "who is",
        "who are",
        "empresa",
        "company",
        "organiza",
        "unternehmen",
        "entreprise",
        "aziend",
        "identidad",
        "identity",
    ),
    _F.ACTIVITY: (
        "actividad",
        "activity",
        "proyecto",
        "project",
        "contrata",
        "hiring",
        "lanzam",
        "launch",
        "aktivit",
        "activit",
        "attivit",
        "atividad",
    ),
    _F.MARKETS: (
        "mercado",
        "market",
        "pais",
        "paises",
        "country",
        "countries",
        "region",
        "markt",
        "marche",
        "mercat",
        "territori",
    ),
    _F.ECONOMICS: (
        "factur",
        "ingreso",
        "revenue",
        "beneficio",
        "profit",
        "empleado",
        "employee",
        "umsatz",
        "chiffre d",
        "fatturat",
        "receita",
        "economic",
        "economi",
    ),
    _F.CONTEXT: (
        "regulac",
        "regulat",
        "normativ",
        "ley ",
        "law",
        "sector",
        "tendenc",
        "trend",
        "regulier",
        "vorschrift",
        "normat",
        "legisla",
    ),
}

_KIND_LEXICON: tuple[tuple[QuestionKind, tuple[str, ...]], ...] = (
    (
        QuestionKind.COUNT,
        (
            "cuant",
            "how many",
            "how much",
            "number of",
            "combien",
            "wie viele",
            "quant",
            "numero de",
        ),
    ),
    (
        QuestionKind.UNKNOWNS,
        (
            "no sabe",
            "no sabemos",
            "don't know",
            "do not know",
            "unknown",
            "desconoc",
            "falta",
            "missing",
            "inconnu",
            "unbekannt",
            "sconosc",
            "nao sabe",
            "todavia no",
            "still",
        ),
    ),
    (
        QuestionKind.HOW_KNOWN,
        (
            "como sab",
            "how do you know",
            "fuente",
            "source",
            "evidenc",
            "comment sav",
            "quelle",
            "fonte",
            "prueba",
            "proof",
            "beleg",
        ),
    ),
    (QuestionKind.WHY, ("por que", "why", "porque", "pourquoi", "warum", "perche", "encaj", "fit")),
    (
        QuestionKind.CHANGE,
        (
            "cambi",
            "change",
            "nuevo",
            "new",
            "novedad",
            "evoluc",
            "changé",
            "geander",
            "neu",
            "mudou",
            "mudanc",
            "cosa e cambiat",
        ),
    ),
)

#: Country names (six languages) → jurisdiction paths used by the readings.
GEOGRAPHY_LEXICON: dict[str, tuple[str, ...]] = {
    "EU/ES": ("espana", "spain", "espagne", "spanien", "spagna", "espanha"),
    "EU/FR": ("francia", "france", "frankreich", "franca"),
    "EU/DE": ("alemania", "germany", "allemagne", "deutschland", "germania", "alemanha"),
    "EU/IT": ("italia", "italy", "italie", "italien"),
    "EU/PT": ("portugal", "portogallo"),
    "US": (
        "estados unidos",
        "united states",
        "usa",
        "etats-unis",
        "vereinigte staaten",
        "stati uniti",
        "eeuu",
    ),
}


@dataclass(frozen=True, slots=True)
class ConversationMemory:
    """Compact, non-authoritative memory of the previous turn. Never a source of truth."""

    focus_id: str
    family: ObservationFamily | None = None
    geographies: tuple[str, ...] = ()
    previous_refs: tuple[str, ...] = ()
    turn: int = 0

    def to_wire(self) -> dict[str, object]:
        return {
            "focusId": self.focus_id,
            "family": None if self.family is None else self.family.value,
            "geographies": list(self.geographies),
            "previousRefs": list(self.previous_refs),
            "turn": self.turn,
        }

    @classmethod
    def from_wire(cls, raw: object, *, focus_id: str) -> ConversationMemory | None:
        """Accept only well-formed memory for this very focus; anything else is dropped."""
        if not isinstance(raw, dict) or raw.get("focusId") != focus_id:
            return None
        family = raw.get("family")
        geographies = raw.get("geographies", [])
        refs = raw.get("previousRefs", [])
        turn = raw.get("turn", 0)
        if family is not None and family not in {f.value for f in _F}:
            return None
        if not isinstance(geographies, list) or not all(
            g in GEOGRAPHY_LEXICON for g in geographies
        ):
            return None
        if (
            not isinstance(refs, list)
            or len(refs) > 12
            or not all(isinstance(r, str) and len(r) < 200 for r in refs)
        ):
            return None
        if not isinstance(turn, int) or not 0 <= turn < 10_000:
            return None
        return cls(
            focus_id, None if family is None else _F(family), tuple(geographies), tuple(refs), turn
        )


@dataclass(frozen=True, slots=True)
class ResolvedQuestion:
    text: str
    kind: QuestionKind
    families: tuple[ObservationFamily, ...]
    geographies: tuple[str, ...]
    #: What came from memory rather than from this question.
    carried: tuple[str, ...] = field(default=())
    #: Proper names in the question; each must be grounded in the authorized corpus.
    named: tuple[str, ...] = field(default=())


def _has(folded: str, stem: str) -> bool:
    if stem.endswith(" ") or " " in stem:
        return stem.strip() in folded
    return re.search(rf"(?<![a-z]){re.escape(stem)}", folded) is not None


def resolve(question: str, memory: ConversationMemory | None = None) -> ResolvedQuestion:
    folded = " " + fold(question) + " "
    families = tuple(
        f for f, stems in FAMILY_LEXICON.items() if any(_has(folded, s) for s in stems)
    )
    geographies = tuple(
        g for g, names in GEOGRAPHY_LEXICON.items() if any(_has(folded, n) for n in names)
    )
    kind = next(
        (k for k, stems in _KIND_LEXICON if any(_has(folded, s) for s in stems)),
        QuestionKind.OVERVIEW,
    )
    carried: list[str] = []
    # Only an elliptical follow-up ("¿Y en Francia?", "¿por qué?") continues the previous
    # topic; a new question with no family word is a new, unscoped question.
    elliptical = (
        folded.strip().startswith(_CONNECTIVES)
        or bool(geographies)
        or kind in {QuestionKind.WHY, QuestionKind.HOW_KNOWN}
    )
    if not families and elliptical and memory is not None and memory.family is not None:
        families = (memory.family,)
        carried.append(f"family:{memory.family.value}")
    if not geographies and memory is not None and memory.geographies and not families:
        geographies = memory.geographies
        carried.append("geographies")
    # "Markets" alone with a country is a question about demand there, if nothing else is named.
    if families == (_F.MARKETS,) and geographies and memory and memory.family is _F.DEMAND:
        families = (_F.DEMAND, _F.MARKETS)
    return ResolvedQuestion(
        question.strip(), kind, families, geographies, tuple(carried), _named(question, geographies)
    )


_CONNECTIVES = ("y ", "e ", "and ", "et ", "und ", "ma ", "mais ", "aber ", "pero ", "but ")
_NAME = re.compile(r"(?<![\w])([A-Z\u00c0-\u00dd][\w'\u2019-]{2,})", re.UNICODE)
_SKIP = frozenset(
    {
        "qué",
        "que",
        "cómo",
        "como",
        "cuál",
        "cual",
        "por",
        "and",
        "what",
        "which",
        "who",
        "how",
        "why",
        "the",
        "quels",
        "quel",
        "welche",
        "wie",
        "was",
        "quale",
        "quali",
        "chi",
        "axignal",
        "axent",
        "seo",
        "geo",
        "google",
        "chatgpt",
    }
)


def _named(question: str, geographies: tuple[str, ...]) -> tuple[str, ...]:
    """Capitalized words after the first one: names the answer must be able to ground."""
    words = _NAME.findall(question.lstrip("¿¡ "))
    first = question.lstrip("¿¡ ").split(" ", 1)[0]
    known_places = {n for g in geographies for n in GEOGRAPHY_LEXICON[g]}
    return tuple(
        dict.fromkeys(
            w for w in words if w != first and fold(w) not in _SKIP and fold(w) not in known_places
        )
    )
