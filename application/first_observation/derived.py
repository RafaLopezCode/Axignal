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


def _focus_proof(proof: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if proof is None or proof.get("target", {}).get("kind") != "FOCUS":
        return None
    return proof


def derived_scopes(proof: Mapping[str, Any] | None) -> tuple[MarketScope, ...]:
    focus = _focus_proof(proof)
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


def derived_capabilities(proof: Mapping[str, Any] | None) -> tuple[CapabilityHypothesis, ...]:
    focus = _focus_proof(proof)
    if focus is None:
        return ()
    out: list[CapabilityHypothesis] = []
    for item in focus.get("capabilities", ()):
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
