"""FIRST_MAP readiness policy.

Readiness is a governed qualitative decision over real runtime outputs.
It is intentionally not a score and never uses map/node counts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.subscriber_projection.evidence_narrative import (
    EvidenceNarrative,
    EvidenceNarrativeKind,
)
from application.subscriber_projection.xignal import ExplainableXignalProjection
from application.xeed_access.organization_reader import AuthorizedXeedOrganization
from application.xeed_germination.runtime import FirstXeedReadinessDecision
from domain.xeed.germination import XeedGerminationState
from domain.xignal import XignalEpistemicState


class FirstMapReadinessDisposition(StrEnum):
    FIRST_MAP_READY = "FIRST_MAP_READY"
    PARTIAL_MAP = "PARTIAL_MAP"
    SPARSE_MAP = "SPARSE_MAP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FirstMapReadinessReason(StrEnum):
    READY_EXPLAINABLE_XIGNAL = "READY_EXPLAINABLE_XIGNAL"
    NO_OBSERVATIONS = "NO_OBSERVATIONS"
    FIRST_XIGNAL_MISSING = "FIRST_XIGNAL_MISSING"
    XIGNAL_PROJECTION_MISSING = "XIGNAL_PROJECTION_MISSING"
    XIGNAL_CONTEXT_MISMATCH = "XIGNAL_CONTEXT_MISMATCH"
    XIGNAL_IS_UNKNOWN = "XIGNAL_IS_UNKNOWN"
    EVIDENCE_NARRATIVE_MISSING = "EVIDENCE_NARRATIVE_MISSING"
    EVIDENCE_NARRATIVE_XIGNAL_MISMATCH = "EVIDENCE_NARRATIVE_XIGNAL_MISMATCH"
    EVIDENCE_NARRATIVE_HAS_NO_GROUNDED_STEP = "EVIDENCE_NARRATIVE_HAS_NO_GROUNDED_STEP"
    VERIFIED_RUNTIME_LINEAGE_PRESENT = "VERIFIED_RUNTIME_LINEAGE_PRESENT"
    EXPLICIT_CONTRADICTIONS_PRESERVED = "EXPLICIT_CONTRADICTIONS_PRESERVED"
    EXPLICIT_UNKNOWNS_PRESERVED = "EXPLICIT_UNKNOWNS_PRESERVED"


@dataclass(frozen=True, slots=True)
class FirstMapReadinessPolicy:
    policy_id: str
    version: str
    require_grounded_narrative: bool = True

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("FIRST_MAP readiness policy identity is required")


@dataclass(frozen=True, slots=True)
class FirstMapReadinessAssessment:
    disposition: FirstMapReadinessDisposition
    decision: FirstXeedReadinessDecision | None
    reason_codes: tuple[FirstMapReadinessReason, ...]

    def __post_init__(self) -> None:
        if not self.reason_codes:
            raise ValueError("FIRST_MAP readiness assessment requires reasons")
        if self.disposition is FirstMapReadinessDisposition.FIRST_MAP_READY:
            if self.decision is None or not self.decision.ready:
                raise ValueError("FIRST_MAP_READY must carry a ready decision")
        elif self.decision is not None and self.decision.ready:
            raise ValueError("non-ready map disposition cannot carry ready decision")


def _require_context(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
) -> None:
    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("FIRST_MAP readiness requires AuthorizedXeedOrganization")
    if state.xeed_id != seed.authorized_xeed.xeed.id:
        raise ValueError("FIRST_MAP readiness state does not match authorized Xeed")


def _decision(
    *,
    state: XeedGerminationState,
    policy: FirstMapReadinessPolicy,
    ready: bool,
    reasons: tuple[FirstMapReadinessReason, ...],
) -> FirstXeedReadinessDecision:
    if state.first_xignal_id is None:
        raise ValueError("readiness promotion decision requires a real first Xignal")
    return FirstXeedReadinessDecision(
        xeed_id=state.xeed_id,
        first_xignal_id=state.first_xignal_id,
        observation_depth=state.observation_depth,
        lifecycle_revision=len(state.transitions),
        ready=ready,
        policy_id=policy.policy_id,
        policy_version=policy.version,
        reason_codes=tuple(reason.value for reason in reasons),
    )


def evaluate_first_map_readiness(
    *,
    seed: AuthorizedXeedOrganization,
    state: XeedGerminationState,
    policy: FirstMapReadinessPolicy,
    projection: ExplainableXignalProjection | None,
    narrative: EvidenceNarrative | None,
) -> FirstMapReadinessAssessment:
    """Evaluate FIRST_MAP readiness without scores, quotas, or node counts."""

    _require_context(seed=seed, state=state)
    reasons: tuple[FirstMapReadinessReason, ...]

    if state.observation_depth == 0:
        reasons = (FirstMapReadinessReason.NO_OBSERVATIONS,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.INSUFFICIENT_EVIDENCE,
            decision=None,
            reason_codes=reasons,
        )

    if state.first_xignal_id is None:
        reasons = (FirstMapReadinessReason.FIRST_XIGNAL_MISSING,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.SPARSE_MAP,
            decision=None,
            reason_codes=reasons,
        )

    if projection is None:
        reasons = (FirstMapReadinessReason.XIGNAL_PROJECTION_MISSING,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    xignal = projection.xignal
    if (
        xignal.xeed_id != state.xeed_id
        or xignal.xeed_id != seed.authorized_xeed.xeed.id
        or xignal.subject_id != seed.organization.id
        or xignal.xignal_id != state.first_xignal_id
    ):
        reasons = (FirstMapReadinessReason.XIGNAL_CONTEXT_MISMATCH,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    if xignal.epistemic_state is XignalEpistemicState.UNKNOWN:
        reasons = (
            FirstMapReadinessReason.XIGNAL_IS_UNKNOWN,
            FirstMapReadinessReason.EXPLICIT_UNKNOWNS_PRESERVED,
        )
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    if narrative is None:
        reasons = (FirstMapReadinessReason.EVIDENCE_NARRATIVE_MISSING,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    if narrative.xignal_id != xignal.xignal_id:
        reasons = (FirstMapReadinessReason.EVIDENCE_NARRATIVE_XIGNAL_MISMATCH,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    grounded_kinds = {
        EvidenceNarrativeKind.CLAIM,
        EvidenceNarrativeKind.RELATIONSHIP,
        EvidenceNarrativeKind.PATHX,
        EvidenceNarrativeKind.OBSERVATION,
        EvidenceNarrativeKind.CONTRADICTION,
        EvidenceNarrativeKind.SOURCE,
    }
    grounded_steps = [step for step in narrative.steps if step.kind in grounded_kinds]
    if policy.require_grounded_narrative and not grounded_steps:
        reasons = (FirstMapReadinessReason.EVIDENCE_NARRATIVE_HAS_NO_GROUNDED_STEP,)
        return FirstMapReadinessAssessment(
            disposition=FirstMapReadinessDisposition.PARTIAL_MAP,
            decision=_decision(state=state, policy=policy, ready=False, reasons=reasons),
            reason_codes=reasons,
        )

    ready_reasons: list[FirstMapReadinessReason] = [
        FirstMapReadinessReason.READY_EXPLAINABLE_XIGNAL,
    ]
    if any(step.artifact_verified is True for step in narrative.steps):
        ready_reasons.append(FirstMapReadinessReason.VERIFIED_RUNTIME_LINEAGE_PRESENT)
    if xignal.contradictions or any(
        step.kind is EvidenceNarrativeKind.CONTRADICTION for step in narrative.steps
    ):
        ready_reasons.append(FirstMapReadinessReason.EXPLICIT_CONTRADICTIONS_PRESERVED)
    if xignal.unknowns:
        ready_reasons.append(FirstMapReadinessReason.EXPLICIT_UNKNOWNS_PRESERVED)

    reason_tuple = tuple(ready_reasons)
    return FirstMapReadinessAssessment(
        disposition=FirstMapReadinessDisposition.FIRST_MAP_READY,
        decision=_decision(state=state, policy=policy, ready=True, reasons=reason_tuple),
        reason_codes=reason_tuple,
    )
