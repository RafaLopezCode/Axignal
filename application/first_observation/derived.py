"""Hand a Focus's First Observation to the autonomous runtime (spec 063 §9).

Read back only what the First Proof persisted for a Focus target: POTENTIAL attention
scopes and capability hypotheses whose basis cites observations appended under the
canonical Organization. Downstream readers still re-validate every basis against
Observation Memory, so a stale or forged proof cannot widen what they accept.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from application.observation_intelligence.contracts import (
    CapabilityHypothesis,
    EvidenceRef,
    MarketRole,
    MarketScope,
    TaxonomyCode,
    geo,
)
from domain.identity import is_web_subject
from domain.xignal import XignalEpistemicState


def _focus_proof(
    proof: Mapping[str, Any] | None, organization_id: str | None
) -> Mapping[str, Any] | None:
    """Only a Focus proof of *this* Organization hands over (ADR-0091 §3): registry verified,
    or a web-anchored subject read through its own website (ADR-0087 amendment 2026-10-16),
    where the organization is that website by definition."""
    target = {} if proof is None else proof.get("target", {})
    link = target.get("identityLink")
    web_anchored = link == "SUBSCRIBER_DIRECTED" and is_web_subject(
        str(target.get("organizationId"))
    )
    if (
        proof is None
        or target.get("kind") != "FOCUS"
        or not (link == "REGISTRY_VERIFIED" or web_anchored)
        or (organization_id is not None and target.get("organizationId") != organization_id)
    ):
        return None
    return proof


#: Minimum evaluator confidence for a judged activity to seed attention (spec 079).
JUDGED_SEED_MIN_CONFIDENCE = 0.7


def derived_scopes(
    proof: Mapping[str, Any] | None, organization_id: str | None = None
) -> tuple[MarketScope, ...]:
    focus = _focus_proof(proof, organization_id)
    if focus is None:
        return ()
    scopes: list[MarketScope] = []
    for item in focus.get("attentionScopes", ()):
        try:
            roles = frozenset(MarketRole(str(role)) for role in item["roles"])
        except (KeyError, ValueError):
            continue
        if roles:
            scopes.append(
                MarketScope(geo(str(item["jurisdiction"])), roles, XignalEpistemicState.POTENTIAL)
            )
    return tuple(scopes)


def derived_capabilities(
    proof: Mapping[str, Any] | None, organization_id: str | None = None
) -> tuple[CapabilityHypothesis, ...]:
    focus = _focus_proof(proof, organization_id)
    if focus is None:
        return ()
    out: list[CapabilityHypothesis] = []
    for item in focus.get("capabilities", ()):
        method = item.get("method")
        if method == "SEMANTIC_JUDGMENT":
            # CTO, 2026-10-16: a judged activity may choose where to look when the evaluator
            # is confident and it routes demand. It stays POTENTIAL attention, never a fact.
            confidence = item.get("confidence")
            if not isinstance(confidence, int | float) or confidence < JUDGED_SEED_MIN_CONFIDENCE:
                continue
            if not item.get("demandCodes"):
                continue
        elif method not in {"LEXICON", "SCHEMA_ORG_TYPE"}:
            continue
        try:
            basis = item["basis"]
            out.append(
                CapabilityHypothesis(
                    capability_id=str(item["capabilityId"]),
                    label=str(item["label"]),
                    state=XignalEpistemicState.POTENTIAL,
                    basis=(
                        EvidenceRef(
                            str(basis["observationId"]),
                            str(basis["sourceRef"]),
                            str(basis["excerpt"]),
                            datetime.fromisoformat(str(basis["observedAt"])),
                        ),
                    ),
                    demand_codes=tuple(
                        TaxonomyCode(str(s), str(c)) for s, c in item["demandCodes"]
                    ),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(out)
