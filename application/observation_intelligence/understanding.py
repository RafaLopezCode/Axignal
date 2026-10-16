"""Deterministic business understanding from observed public text.

A matched term is evidence that the organization *declares* something, with the
exact sentence as basis. The capability itself stays POTENTIAL; families are
derived from capabilities and stay governed hypotheses. No model is called.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

from application.observation_intelligence.catalog import (
    CAPABILITY_LEXICON,
    CapabilityLexiconEntry,
)
from application.observation_intelligence.contracts import (
    Band,
    BusinessFamilyHypothesis,
    CapabilityHypothesis,
    EvidenceRef,
)
from domain.xignal import XignalEpistemicState

_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")
#: Footer and legal-link lines: they name policies and documents, never an offer.
_POLICY_LINE = re.compile(
    r"\b(policy|policies|política|políticas|politique|richtlinie|datenschutz|informativa|"
    r"privacy|privacidad|privacité|cookies?|aviso legal|legal notice|mentions légales|"
    r"impressum|terms of use|términos|condiciones de uso)\b",
    re.IGNORECASE,
)
#: A client's success story names what the client does, not what the organization offers.
_CLIENT_STORY = re.compile(
    r"\b(grows?|grew|increased?|boosts?|doubled|tripled|case stud\w*|success stor\w*|"
    r"caso de éxito|casos de éxito|helped|ayudamos a|revenue by|results? for)\b",
    re.IGNORECASE,
)

#: What the organization uses, has, buys or sells through, not what it offers (found on
#: biocultor.com, 2026-10-16: "huerto urbano, autoconsumo" read as solar installation; a trap
#: corpus showed the same for "our offices have CCTV", "we work with a local printer"...).
_OWN_USE = re.compile(
    r"\b(nuestr[ao]s? (sede|sedes|oficinas?|nave|naves|f[aá]brica|almac[eé]n|instalaciones|"
    r"tienda f[ií]sica|cubierta|edificio)|our (offices?|headquarters|warehouse|factory|"
    r"facilities|building|premises|roof)|nos (bureaux|locaux|entrep[oô]ts?)|unser(e|em)? "
    r"(b[uü]ro|lager|geb[aä]ude|halle)|i nostri uffici|os nossos escrit[oó]rios|"
    r"utilizamos|usamos|we use|nous utilisons|wir nutzen|utilizziamo|"
    r"somos clientes|we are (a )?customers?|trabajamos con (un|una)|colaboramos con (un|una)|"
    r"we work with an? |protected by|protegid[ao]s? (por|con)|runs on|powered by|"
    r"funciona con|disponibles? en (supermercados|supermarkets|tiendas|grandes superficies)|"
    r"available (in|at) (supermarkets|stores|retailers)|encuentra nuestros productos|"
    r"find our products|para reducir nuestr[ao]|to reduce our)\b",
    re.IGNORECASE,
)


def _names_an_offer(excerpt: str, term: str) -> bool:
    """A bare menu label ("Legal Services" alone, often a list of industries served), a client
    story or what the organization itself uses is not its own offer; another occurrence may be."""
    if _POLICY_LINE.search(excerpt) or _CLIENT_STORY.search(excerpt) or _OWN_USE.search(excerpt):
        return False
    return len(excerpt.split()) > len(term.split()) + 1


def _sentence_containing(text: str, start: int) -> str:
    for match in _SENTENCE.finditer(text):
        if match.start() <= start < match.end():
            return match.group(0).strip()
    return text[start : start + 120].strip()


def detect_capabilities(
    *,
    text: str,
    observation_id: str,
    source_ref: str,
    observed_at: datetime,
    lexicon: tuple[CapabilityLexiconEntry, ...] = CAPABILITY_LEXICON,
) -> tuple[CapabilityHypothesis, ...]:
    """Return one POTENTIAL hypothesis per declared capability, with exact excerpts.

    Ordered by where the text first says it: what a page leads with (its title and
    description come first) is listed before what it mentions further down.
    """

    folded = text.casefold()
    found: list[tuple[int, CapabilityHypothesis]] = []
    for entry in lexicon:
        excerpts: list[str] = []
        first = len(folded)
        for term in entry.terms:
            needle = term.casefold()
            index = folded.find(needle)
            while index >= 0:
                excerpt = _sentence_containing(text, index)
                # A line of policies or legal links ("Cybersecurity Policy | Cookies")
                # names a document, not an offer: look for the next occurrence instead.
                if excerpt and _names_an_offer(excerpt, term):
                    first = min(first, index)
                    if excerpt not in excerpts:
                        excerpts.append(excerpt)
                    break
                index = folded.find(needle, index + len(needle))
        if not excerpts:
            continue
        found.append(
            (
                first,
                CapabilityHypothesis(
                    capability_id=entry.capability_id,
                    label=entry.label,
                    state=XignalEpistemicState.POTENTIAL,
                    basis=tuple(
                        EvidenceRef(observation_id, source_ref, excerpt, observed_at)
                        for excerpt in excerpts
                    ),
                    demand_codes=entry.demand_codes,
                    buyer_jobs=entry.buyer_jobs,
                ),
            )
        )
    return tuple(hypothesis for _, hypothesis in sorted(found, key=lambda pair: pair[0]))


def derive_families(
    capabilities: tuple[CapabilityHypothesis, ...],
    lexicon: tuple[CapabilityLexiconEntry, ...] = CAPABILITY_LEXICON,
) -> tuple[BusinessFamilyHypothesis, ...]:
    """Many families may hold at once; strength and stability are ordinal and explained."""

    families_by_capability = {entry.capability_id: entry.families for entry in lexicon}
    grouped: dict[str, list[CapabilityHypothesis]] = defaultdict(list)
    for capability in capabilities:
        for family in families_by_capability.get(capability.capability_id, ()):
            grouped[family].append(capability)
    result: list[BusinessFamilyHypothesis] = []
    for family_id, members in sorted(grouped.items()):
        basis = tuple(ref for member in members for ref in member.basis)
        observations = {ref.observation_id for ref in basis}
        result.append(
            BusinessFamilyHypothesis(
                family_id=family_id,
                state=XignalEpistemicState.POTENTIAL,
                strength=Band.HIGH if len(members) >= 2 else Band.MEDIUM,
                # One observation of one page is a fragile basis for any classification.
                stability=Band.MEDIUM if len(observations) >= 2 else Band.LOW,
                capability_ids=tuple(member.capability_id for member in members),
                basis=basis,
            )
        )
    return tuple(result)
