"""GEO measured: what an AI assistant answers when asked about an organization's category.

A probe is a measurement, declared as such (MASTER §54): the instrument (provider and
model), the conditions (the exact questions, their language, the date, no live web
search), the sample (how many questions) and its uncertainty (answers vary between runs
and between assistants). A mention is not a citation and a citation is not an endorsement;
a name absent from one answer is not absent from the assistant's knowledge. Competitors the
assistant names are POTENTIAL: the assistant's reading, never a market fact.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

#: Fixed question templates per language: six category questions (the intents a buyer asks
#: an assistant with: recommend, main providers, best for an SME, best reputation, who to ask
#: for a quote, alternatives to the big ones) and, last, one brand question. Six category
#: questions measure presence and share of voice against competitors, as specialist GEO tools
#: do (CTO, 2026-10-17: agencies); another set of questions is another instrument.
TEMPLATES: dict[str, tuple[str, ...]] = {
    "es": ("¿Qué empresas recomiendas para {activity} en {place}?",
           "¿Quiénes son los principales proveedores de {activity} en {place}?",
           "¿Cuáles son las mejores empresas de {activity} en {place} para una pyme?",
           "¿Qué empresas de {activity} en {place} tienen mejor reputación?",
           "Necesito contratar {activity} en {place}: ¿a quién debería pedir presupuesto?",
           "¿Qué alternativas hay a las grandes empresas de {activity} en {place}?",
           "¿Qué sabes de la empresa {name}?"),
    "en": ("Which companies do you recommend for {activity} in {place}?",
           "Who are the main providers of {activity} in {place}?",
           "What are the best {activity} companies in {place} for a small business?",
           "Which {activity} companies in {place} have the best reputation?",
           "I need to hire {activity} in {place}: who should I ask for a quote?",
           "What are the alternatives to the big {activity} companies in {place}?",
           "What do you know about the company {name}?"),
    "de": ("Welche Unternehmen empfiehlst du für {activity} in {place}?",
           "Wer sind die wichtigsten Anbieter für {activity} in {place}?",
           "Welche Anbieter für {activity} in {place} sind für ein KMU am besten?",
           "Welche Anbieter für {activity} in {place} haben den besten Ruf?",
           "Ich möchte {activity} in {place} beauftragen: Wen sollte ich um ein Angebot bitten?",
           "Welche Alternativen gibt es zu den großen Anbietern für {activity} in {place}?",
           "Was weißt du über das Unternehmen {name}?"),
    "fr": ("Quelles entreprises recommandes-tu pour {activity} en {place} ?",
           "Quels sont les principaux fournisseurs de {activity} en {place} ?",
           "Quelles sont les meilleures entreprises de {activity} en {place} pour une PME ?",
           "Quelles entreprises de {activity} en {place} ont la meilleure réputation ?",
           "Je dois faire appel à {activity} en {place} : à qui demander un devis ?",
           "Quelles alternatives aux grandes entreprises de {activity} en {place} ?",
           "Que sais-tu de l'entreprise {name} ?"),
    "it": ("Quali aziende consigli per {activity} in {place}?",
           "Quali sono i principali fornitori di {activity} in {place}?",
           "Quali sono le migliori aziende di {activity} in {place} per una PMI?",
           "Quali aziende di {activity} in {place} hanno la migliore reputazione?",
           "Devo affidare {activity} in {place}: a chi dovrei chiedere un preventivo?",
           "Quali alternative ci sono alle grandi aziende di {activity} in {place}?",
           "Cosa sai dell'azienda {name}?"),
    "pt": ("Que empresas recomendas para {activity} em {place}?",
           "Quem são os principais fornecedores de {activity} em {place}?",
           "Quais são as melhores empresas de {activity} em {place} para uma PME?",
           "Que empresas de {activity} em {place} têm melhor reputação?",
           "Preciso de contratar {activity} em {place}: a quem devo pedir orçamento?",
           "Que alternativas existem às grandes empresas de {activity} em {place}?",
           "O que sabes sobre a empresa {name}?"),
}  # fmt: skip

INSTRUCTION = (
    "Answer the user's question as a helpful assistant would, from your own knowledge, "
    "without browsing. Then list every organization you named and every website you cited, "
    "exactly as written in your answer. If the question asks about a specific organization, "
    "set recognizes_subject to true only if you have specific knowledge of that organization "
    "(not of others with similar names); otherwise false."
)
SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["answer", "organizations_named", "websites_cited", "recognizes_subject"],
    "properties": {
        "answer": {"type": "string"},
        "organizations_named": {"type": "array", "items": {"type": "string"}},
        "websites_cited": {"type": "array", "items": {"type": "string"}},
        # True only when the assistant has specific knowledge of the organization asked about.
        "recognizes_subject": {"type": "boolean"},
    },
}


@dataclass(frozen=True, slots=True)
class ProbeSubject:
    name: str
    domain: str | None
    activity: str
    place: str
    language: str

    @property
    def key(self) -> str:
        return "|".join(
            (
                _fold(self.name),
                self.domain or "",
                _fold(self.activity),
                _fold(self.place),
                self.language,
            )
        )


def _fold(text: str) -> str:
    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold(),
        )
    )


def questions(subject: ProbeSubject) -> tuple[str, ...]:
    templates = TEMPLATES.get(subject.language, TEMPLATES["en"])
    return tuple(
        t.format(activity=subject.activity, place=subject.place, name=subject.name)
        for t in templates
    )


def _strings(value: object) -> list[str]:
    return [str(v) for v in value if isinstance(v, str)] if isinstance(value, list | tuple) else []


def _rows(value: object) -> list[Mapping[str, object]]:
    return [r for r in value if isinstance(r, Mapping)] if isinstance(value, list | tuple) else []


def _named(text: str, name: str) -> bool:
    folded = f" {_fold(text)} "
    words = _fold(name).split()
    return bool(words) and f" {' '.join(words)} " in folded


def _site(value: str) -> str | None:
    host = re.sub(r"^[a-z]+://", "", value.strip().casefold()).split("/")[0].removeprefix("www.")
    return host if "." in host and " " not in host else None


def evaluate(subject: ProbeSubject, answers: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Per question: named, its position, website cited, others named and websites cited.

    Over the category questions (all but the last, the brand question): presence (share of
    answers naming it), share of voice (its mentions among every organization named), its
    average position when named, the competitors named most and the websites cited most.
    """
    rows: list[dict[str, object]] = []
    for question, answer in zip(questions(subject), answers, strict=False):
        text = str(answer.get("answer") or "")
        names = _strings(answer.get("organizations_named"))
        sites = _strings(answer.get("websites_cited"))
        named = _named(text, subject.name) or any(_named(n, subject.name) for n in names)
        position = next((i for i, n in enumerate(names, 1) if _named(n, subject.name)), None)
        domain = subject.domain
        cited = domain is not None and any(domain in s.casefold() for s in [*sites, text])
        others = [n for n in names if not _named(n, subject.name)][:10]
        rows.append({"question": question, "named": named, "position": position, "cited": cited,
                     "othersNamed": others,
                     "sitesCited": sorted({h for s in sites if (h := _site(s))})[:10]})  # fmt: skip
    category = rows[:-1] if len(rows) > 1 else rows
    rivals = Counter(n for r in category for n in _strings(r.get("othersNamed")))
    mentions = sum(1 for r in category if r["named"])
    positions = [int(str(r["position"])) for r in category if r.get("position")]
    cited_sites = Counter(h for r in category for h in _strings(r.get("sitesCited")))
    brand = answers[len(rows) - 1] if len(rows) > 1 and len(answers) >= len(rows) else None
    return {
        "questions": rows,
        "categoryQuestions": len(category),
        "namedInCategory": mentions,
        "citedInCategory": sum(1 for r in category if r["cited"]),
        "shareOfVoice": (
            round(mentions / (mentions + sum(rivals.values())), 3)
            if mentions + sum(rivals.values())
            else None
        ),
        "averagePosition": round(sum(positions) / len(positions), 1) if positions else None,
        "competitorFrequency": [[name, n] for name, n in rivals.most_common(10)],
        "sitesCited": [[site, n] for site, n in cited_sites.most_common(10)],
        "brandKnown": (brand.get("recognizes_subject") is True if brand is not None else None),
    }


def geo_discoveries(
    measurement: Mapping[str, object], *, observed_at: str
) -> list[dict[str, object]]:
    """GENERATIVE_VISIBILITY discoveries from one stored measurement."""
    result = measurement.get("result")
    if not isinstance(result, Mapping):
        return []
    named = int(result.get("namedInCategory") or 0)
    asked = int(result.get("categoryQuestions") or 0)
    rows = _rows(result.get("questions"))
    category = rows[:-1] if len(rows) > 1 else rows
    frequency = result.get("competitorFrequency")
    competitors = (
        [str(row[0]) for row in frequency if isinstance(row, list | tuple) and row][:10]
        if isinstance(frequency, list) and frequency
        else sorted({n for r in category for n in _strings(r.get("othersNamed"))})[:10]
    )
    basis: dict[str, object] = {
        "instrument": measurement.get("instrument"),
        "conditions": {
            "questions": [r.get("question") for r in rows],
            "language": measurement.get("language"),
            "liveWebSearch": False,
        },
        "measuredAt": measurement.get("measuredAt"),
        "sample": f"{len(rows)} questions, 1 answer each",
        "uncertainty": "Answers vary between runs and assistants; one measurement is a sample, "
        "not the assistant's whole knowledge.",
        "notEndorsement": True,
    }
    out: list[dict[str, object]] = [
        {
            "kind": "GENERATIVE_VISIBILITY",
            "code": "AI_NAMED_FOR_CATEGORY" if named else "AI_NOT_NAMED_FOR_CATEGORY",
            "statement": f"{named}/{asked}",
            "epistemicState": "OBSERVED",
            "sourceUrl": None,
            "excerpt": None,
            "observedAt": str(measurement.get("measuredAt") or observed_at),
            "detail": {
                **basis,
                "cited": int(result.get("citedInCategory") or 0),
                "competitorsNamed": competitors,
                # Specialist GEO measures (spec 090): share of voice and position, shown as
                # measured with their conditions; never a universal score.
                "shareOfVoice": result.get("shareOfVoice"),
                "averagePosition": result.get("averagePosition"),
                "competitorFrequency": result.get("competitorFrequency"),
                "rows": [dict(r) for r in rows],
            },
        }
    ]
    if result.get("brandKnown") is not None:
        out.append(
            {
                "kind": "GENERATIVE_VISIBILITY",
                "code": "AI_KNOWS_BRAND" if result.get("brandKnown") else "AI_DOES_NOT_KNOW_BRAND",
                "statement": str(rows[2].get("question") if len(rows) > 2 else ""),
                "epistemicState": "OBSERVED",
                "sourceUrl": None,
                "excerpt": None,
                "observedAt": str(measurement.get("measuredAt") or observed_at),
                "detail": basis,
            }
        )
    cited = result.get("sitesCited")
    if isinstance(cited, list) and cited:
        out.append(
            {
                "kind": "GENERATIVE_VISIBILITY",
                "code": "AI_CITED_SOURCES",
                "statement": ", ".join(
                    str(row[0]) for row in cited[:5] if isinstance(row, list | tuple) and row
                ),
                "epistemicState": "OBSERVED",
                "sourceUrl": None,
                "excerpt": None,
                "observedAt": str(measurement.get("measuredAt") or observed_at),
                "detail": {
                    **basis,
                    "sitesCited": cited,
                    "meaning": "Websites the assistant cites when asked about the activity: "
                    "where an organization needs to be present to be found.",
                },
            }
        )
    return out
