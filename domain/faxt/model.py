"""Canonical FAXT model.

Canonical FAXT values are materialized only through FAXT.create after an exact
proposition-bound EvidenceAdmission decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.evidence.admission import (
    AdmissionDecision,
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionError,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.identity import FaxtId


class FAXTCreationError(EvidenceAdmissionError):
    """Raised when a FAXT cannot be created canonically."""


@dataclass(frozen=True, init=False)
class FAXT:
    """A canonical, evidence-backed unit of knowledge."""

    id: FaxtId
    subject_id: str
    predicate: str
    object_or_value: str
    evidence_refs: tuple[str, ...]
    observed_at: datetime
    epistemic_state: EpistemicState
    currentness: Currentness = Currentness.UNKNOWN
    contradictions: tuple[str, ...] = ()

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("FAXT can only be materialized through FAXT.create")

    @classmethod
    def _materialize(
        cls,
        *,
        faxt_id: FaxtId,
        subject_id: str,
        predicate: str,
        object_or_value: str,
        evidence_refs: tuple[str, ...],
        observed_at: datetime,
        epistemic_state: EpistemicState,
        currentness: Currentness,
        contradictions: tuple[str, ...] = (),
    ) -> FAXT:
        value = object.__new__(cls)
        object.__setattr__(value, "id", faxt_id)
        object.__setattr__(value, "subject_id", subject_id)
        object.__setattr__(value, "predicate", predicate)
        object.__setattr__(value, "object_or_value", object_or_value)
        object.__setattr__(value, "evidence_refs", evidence_refs)
        object.__setattr__(value, "observed_at", observed_at)
        object.__setattr__(value, "epistemic_state", epistemic_state)
        object.__setattr__(value, "currentness", currentness)
        object.__setattr__(value, "contradictions", contradictions)
        return value

    @classmethod
    def create(
        cls,
        *,
        faxt_id: FaxtId,
        subject_id: str,
        predicate: str,
        object_or_value: str,
        evidence: Evidence,
        decision: AdmissionDecision,
        claim_proposition: str | None = None,
        epistemic_state: EpistemicState = EpistemicState.OBSERVED,
        observed_at: datetime | None = None,
        currentness: Currentness = Currentness.UNKNOWN,
    ) -> FAXT:
        """Create canonical state from one exact admitted proposition."""

        if not faxt_id.strip():
            raise FAXTCreationError("a canonical FAXT requires an id")
        if not subject_id.strip():
            raise FAXTCreationError("a FAXT requires a subject id")
        if not object_or_value.strip():
            raise FAXTCreationError("a FAXT requires an object or value")
        if epistemic_state is EpistemicState.UNKNOWN:
            raise FAXTCreationError("a canonical FAXT cannot be created with UNKNOWN state")
        if not predicate.strip():
            raise FAXTCreationError("a FAXT requires a predicate")

        canonical_observed_at = observed_at if observed_at is not None else evidence.observed_at
        if canonical_observed_at != evidence.observed_at:
            raise FAXTCreationError(
                "canonical FAXT observed_at must match admitted evidence observed_at"
            )
        proposition = (
            claim_proposition if claim_proposition is not None else evidence.extracted_claim
        )
        request = AdmissionRequest(
            evidence=evidence,
            subject_id=subject_id,
            predicate=predicate,
            object_or_value=object_or_value,
            claim_proposition=proposition,
        )
        EvidenceAdmission.require_claim(decision, request)

        return cls._materialize(
            faxt_id=faxt_id,
            subject_id=subject_id,
            predicate=predicate,
            object_or_value=object_or_value,
            evidence_refs=(evidence.id,),
            observed_at=canonical_observed_at,
            epistemic_state=epistemic_state,
            currentness=currentness,
        )
