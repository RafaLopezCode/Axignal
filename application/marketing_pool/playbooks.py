"""Playbooks: one argument per buyer segment, led by the crossing that matters to it.

An SEO agency, a construction company and a private school do not act on the same
evidence. A playbook says, for one segment: the pain AXIGNAL addresses, which findings
can open the message (its hooks, best first — usually an INXIGHT), the order of the
evidence cards, and its own call to action. No hook, no message: a letter without a
specific, evidenced opening would be generic, and generic letters are not sent.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

PLAYBOOKS_VERSION = "playbooks-v1"


@dataclass(frozen=True, slots=True)
class Playbook:
    segment: str
    personas: tuple[str, ...]
    #: (kind, code) that can open the message, best first; a code ending in "*" is a prefix.
    hooks: tuple[tuple[str, str], ...]
    #: Families of the evidence cards, in order.
    families: tuple[str, ...]
    #: The pain, in the model's brief (English); the message says it in its language.
    pain: str
    #: Where the reading link opens (an anchor of the recipient page).
    anchor: str


PLAYBOOKS: tuple[Playbook, ...] = (
    Playbook(
        "AGENCY",
        ("SEO_GEO_AGENCY", "DIGITAL_MARKETING_AGENCY", "REPUTATION_PR_AGENCY"),
        (
            ("INXIGHT", "presence:AI_NAMES_COMPETITORS_NOT_IT"),
            ("GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY"),
            ("GENERATIVE_VISIBILITY", "AI_DOES_NOT_KNOW_BRAND"),
            ("INXIGHT", "demand:OPEN_DEMAND_OFFER_NOT_DECLARED"),
            ("REPRESENTATION_GAP", "AUDIT:*"),
        ),
        ("presence", "reputation", "relationships"),
        "Agencies must prove, client by client, what changed in how search engines and AI "
        "assistants represent them; what AXIGNAL sees of the agency itself is exactly what "
        "it could measure, independently, for each of its clients.",
        "presence",
    ),
    Playbook(
        "CONSTRUCTION",
        ("CONSTRUCTION",),
        (
            ("INXIGHT", "demand:LOCAL_BUYERS_NEVER_AWARDED"),
            ("INXIGHT", "relationships:COMPETITORS_WIN_WITH_ITS_BUYERS"),
            ("INXIGHT", "economics:PUBLIC_CONTRACTS_WEIGHT"),
            ("INXIGHT", "relationships:PUBLIC_CLIENT_CONCENTRATION"),
            ("DEMAND", "RECURRING_PUBLIC_BUYER"),
        ),
        ("demand", "relationships", "economics"),
        "Construction and installation companies win work by being known to the bodies that "
        "award it nearby, and by seeing tenders and competitors early; that information is "
        "public but scattered.",
        "demand",
    ),
    Playbook(
        "PRIVATE_SCHOOL",
        ("PRIVATE_SCHOOL",),
        (
            ("INXIGHT", "presence:AI_NAMES_COMPETITORS_NOT_IT"),
            ("GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY"),
            ("GENERATIVE_VISIBILITY", "AI_DOES_NOT_KNOW_BRAND"),
            ("INXIGHT", "reputation:SECTOR_IN_NEWS_NOT_IT"),
            ("REPRESENTATION_GAP", "AUDIT:*"),
        ),
        ("presence", "reputation", "context"),
        "Families now ask search engines and AI assistants which school to choose; a school "
        "that is not named there, or is described poorly, loses enrolment it never sees.",
        "presence",
    ),
    Playbook(
        "CONSULTANCY",
        ("B2B_CONSULTANCY",),
        (
            ("INXIGHT", "markets:GROUP_COUNTRIES_DEMAND_UNWATCHED"),
            ("INXIGHT", "demand:LOCAL_BUYERS_NEVER_AWARDED"),
            ("DEMAND", "POTENTIAL_PRIVATE_CUSTOMER"),
            ("RELATIONSHIP", "PUBLIC_CONTRACT_PARTNER"),
            ("DEMAND", "RECURRING_PUBLIC_BUYER"),
        ),
        ("demand", "relationships", "markets"),
        "Consultancies sell understanding of their clients' markets; an evidence-backed map "
        "of demand, buyers, partners and value chain is the raw material of their advice.",
        "demand",
    ),
)


def playbook_for(persona_id: str) -> Playbook | None:
    return next((p for p in PLAYBOOKS if persona_id in p.personas), None)


def _matches(d: Mapping[str, Any], kind: str, code: str) -> bool:
    if d.get("kind") != kind:
        return False
    actual = str(d.get("code") or "")
    return actual.startswith(code[:-1]) if code.endswith("*") else actual == code


def hooks(view: Mapping[str, Any], playbook: Playbook) -> list[Mapping[str, Any]]:
    """The findings that can open this segment's message, best first (never unknowns)."""
    held = view.get("discoveries")
    discoveries = [d for d in (held if isinstance(held, list) else []) if isinstance(d, Mapping)]
    found: list[Mapping[str, Any]] = []
    for kind, code in playbook.hooks:
        for d in discoveries:
            if _matches(d, kind, code) and d.get("epistemicState") != "UNKNOWN" and d not in found:
                if kind == "REPRESENTATION_GAP" and (d.get("detail") or {}).get("impact") != "HIGH":
                    continue  # an audit check opens a message only when its impact is high
                found.append(d)
    return found


def hook_brief(hook: Mapping[str, Any]) -> str:
    """The opening fact as the model must use it: statement, values, why (no invention)."""
    detail = hook.get("detail") if isinstance(hook.get("detail"), Mapping) else {}
    values = detail.get("values") if isinstance(detail, Mapping) else None
    parts = [f"{hook.get('kind')}:{hook.get('code')}", str(hook.get("statement") or "")]
    if isinstance(values, Mapping) and values:
        parts.append("values: " + "; ".join(f"{k}={v}" for k, v in values.items()))
    why = detail.get("why") if isinstance(detail, Mapping) else None
    if why:
        parts.append(f"why it matters: {why}")
    return " | ".join(parts)


#: Call to action and section title per segment, in [es, en, fr, de, it, pt].
COPY: dict[str, dict[str, Sequence[str]]] = {
    "AGENCY": {
        "cta": ("Ver cómo os ven buscadores e IA", "See how search and AI see you",
                "Voir comment la recherche et l'IA vous voient", "So sehen Suche und KI Sie",
                "Vedi come vi vedono ricerca e IA", "Ver como a pesquisa e a IA vos veem"),
        "section": ("Lo que podríais medir para cada cliente", "What you could measure for each client",
                    "Ce que vous pourriez mesurer pour chaque client",
                    "Was Sie für jeden Kunden messen könnten",
                    "Cosa potreste misurare per ogni cliente",
                    "O que poderiam medir para cada cliente"),
    },
    "CONSTRUCTION": {
        "cta": ("Ver compradores y licitaciones abiertas", "See buyers and open tenders",
                "Voir les acheteurs et les appels d'offres", "Auftraggeber und Ausschreibungen ansehen",
                "Vedi acquirenti e gare aperte", "Ver compradores e concursos abertos"),
        "section": ("Quién compra tu obra cerca de ti", "Who buys your work near you",
                    "Qui achète vos travaux près de chez vous", "Wer Ihre Leistungen in Ihrer Nähe kauft",
                    "Chi compra i vostri lavori vicino a voi", "Quem compra a sua obra perto de si"),
    },
    "PRIVATE_SCHOOL": {
        "cta": ("Ver cómo te encuentran las familias", "See how families find you",
                "Voir comment les familles vous trouvent", "So finden Familien Sie",
                "Vedi come vi trovano le famiglie", "Ver como as famílias vos encontram"),
        "section": ("Lo que ven las familias cuando buscan colegio", "What families see when they look for a school",
                    "Ce que voient les familles qui cherchent une école",
                    "Was Familien bei der Schulsuche sehen",
                    "Cosa vedono le famiglie quando cercano una scuola",
                    "O que as famílias veem quando procuram escola"),
    },
    "CONSULTANCY": {
        "cta": ("Ver el mapa de oportunidades", "See the opportunity map",
                "Voir la carte des opportunités", "Die Chancenkarte ansehen",
                "Vedi la mappa delle opportunità", "Ver o mapa de oportunidades"),
        "section": ("El mercado que rodea a tus clientes", "The market around your clients",
                    "Le marché qui entoure vos clients", "Der Markt rund um Ihre Kunden",
                    "Il mercato intorno ai vostri clienti", "O mercado à volta dos seus clientes"),
    },
}  # fmt: skip
_LANGS = ("es", "en", "fr", "de", "it", "pt")


def copy(segment: str, key: str, language: str) -> str | None:
    values = COPY.get(segment, {}).get(key)
    if not values:
        return None
    index = _LANGS.index(language) if language in _LANGS else 1
    return str(values[index])
