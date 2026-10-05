"""Derived economic opportunity projection for EB-07.

An opportunity is non-canonical, POTENTIAL/UNKNOWN, temporal and explainable.
It never creates a FAXT, customer, lead or observed relationship.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.brain_contracts import AttentionDisposition
from application.economic_discovery.explanation import ExplainableBasis
from application.economic_discovery.first_vertical import EconomicReasoningResult
from domain.xignal import XignalEpistemicState

_DEFAULT_UNASSESSED = (
    "commercial_access",
    "capacity",
    "incumbent",
    "price",
)


@dataclass(frozen=True, slots=True)
class EconomicOpportunity:
    opportunity_id: str
    subject_id: str
    activity_id: str
    candidate_id: str
    state_fingerprint: str
    epistemic_state: XignalEpistemicState
    attention: AttentionDisposition
    derived_at: datetime
    basis: ExplainableBasis
    missing_context: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.opportunity_id,
                self.subject_id,
                self.activity_id,
                self.candidate_id,
                self.state_fingerprint,
            )
        ):
            raise ValueError("economic opportunity identity is required")
        if self.epistemic_state not in (
            XignalEpistemicState.POTENTIAL,
            XignalEpistemicState.UNKNOWN,
        ):
            raise ValueError("economic opportunity can never assert OBSERVED")
        if self.derived_at.tzinfo is None:
            raise ValueError("economic opportunity time must be timezone-aware")
        if self.basis.state_fingerprint != self.state_fingerprint:
            raise ValueError("economic opportunity must preserve its explanation state")
        if self.basis.candidate_id != self.candidate_id:
            raise ValueError("economic opportunity must preserve candidate lineage")
        if not self.reason_codes:
            raise ValueError("economic opportunity requires explicit reasoning")


def _id(result: EconomicReasoningResult) -> str:
    payload = {
        "candidate_id": result.candidate.candidate_id,
        "subject_id": result.candidate.subject.state.subject_id,
        "activity_id": result.candidate.activity.state.subject_id,
        "state_fingerprint": result.vector.state_fingerprint,
        "policy_version": result.interpretation.policy_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "opportunity:" + hashlib.sha256(encoded.encode()).hexdigest()[:32]


def derive_economic_opportunity(result: EconomicReasoningResult) -> EconomicOpportunity:
    """Project EB-04 reasoning into an inspectable opportunity, never truth."""

    missing = set(_DEFAULT_UNASSESSED)
    for evaluation in result.vector.evaluations:
        if evaluation.selected_option != "YES":
            missing.add(evaluation.dimension_id)

    return EconomicOpportunity(
        opportunity_id=_id(result),
        subject_id=result.candidate.subject.state.subject_id,
        activity_id=result.candidate.activity.state.subject_id,
        candidate_id=result.candidate.candidate_id,
        state_fingerprint=result.vector.state_fingerprint,
        epistemic_state=result.interpretation.epistemic_state,
        attention=result.interpretation.attention,
        derived_at=result.vector.evaluated_at,
        basis=result.basis,
        missing_context=tuple(sorted(missing)),
        reason_codes=result.interpretation.reason_codes,
    )
