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
from domain.xignal import XignalEpistemicState


def _focus_proof(
    proof: Mapping[str, Any] | None, organization_id: str | None
) -> Mapping[str, Any] | None:
    """Only a registry-verified Focus proof of *this* Organization hands over (ADR-0091 §3)."""
    target = {} if proof is None else proof.get("target", {})
    if (
        proof is None
        or target.get("kind") != "FOCUS"
        or target.get("identityLink") != "REGISTRY_VERIFIED"
        or (organization_id is not None and target.get("organizationId") != organization_id)
    ):
        return None
    return proof


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
        if item.get("method") not in {"LEXICON", "SCHEMA_ORG_TYPE"}:
            continue  # a judgment chooses where to look, it never founds a capability
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
