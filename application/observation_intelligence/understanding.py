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
    """Return one POTENTIAL hypothesis per declared capability, with exact excerpts."""

    folded = text.casefold()
    hypotheses: list[CapabilityHypothesis] = []
    for entry in lexicon:
        excerpts: list[str] = []
        for term in entry.terms:
            index = folded.find(term.casefold())
            if index >= 0:
                excerpt = _sentence_containing(text, index)
                if excerpt and excerpt not in excerpts:
                    excerpts.append(excerpt)
        if not excerpts:
            continue
        hypotheses.append(
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
            )
        )
    return tuple(hypotheses)


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
