"""Canonical FAXT model.

FAXT.create requires an exact proposition-bound AdmissionDecision.
Doctrine: MASTER §4.5, §15.1, §15.2, §46.9.
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


@dataclass(frozen=True)
class FAXT:
    """A canonical, evidence-backed unit of knowledge (MASTER §15.2)."""

    id: FaxtId
    subject_id: str
    predicate: str
    object_or_value: str
    evidence_refs: tuple[str, ...]
    observed_at: datetime
    epistemic_state: EpistemicState
    currentness: Currentness = Currentness.UNKNOWN
    contradictions: tuple[str, ...] = ()

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
        """Create a canonical FAXT from one exact admitted proposition."""

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

        return cls(
            id=faxt_id,
            subject_id=subject_id,
            predicate=predicate,
            object_or_value=object_or_value,
            evidence_refs=(evidence.id,),
            observed_at=canonical_observed_at,
            epistemic_state=epistemic_state,
            currentness=currentness,
        )
