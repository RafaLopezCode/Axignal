"""Canonical FAXT model.

``FAXT.create`` requires an admitted ``AdmissionDecision``; there is no public
constructor that bypasses evidence admission.

Doctrine: MASTER §4.5, §15.1 (CLAIM != WRITE), §15.2, §46.9.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.evidence.admission import (
    AdmissionDecision,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionError,
)
from domain.evidence.epistemics import Currentness, EpistemicState


class FAXTCreationError(EvidenceAdmissionError):
    """Raised when a FAXT cannot be created canonically."""


@dataclass(frozen=True)
class FAXT:
    """A canonical, evidence-backed unit of knowledge (MASTER §15.2)."""

    id: str
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
        faxt_id: str,
        subject_id: str,
        predicate: str,
        object_or_value: str,
        evidence: Evidence,
        decision: AdmissionDecision,
        epistemic_state: EpistemicState = EpistemicState.OBSERVED,
        observed_at: datetime | None = None,
        currentness: Currentness = Currentness.UNKNOWN,
    ) -> FAXT:
        """Create a canonical FAXT. Requires evidence admission."""

        EvidenceAdmission.require(decision)
        if decision.evidence_id != evidence.id:
            raise FAXTCreationError("admission decision does not match the supplied evidence")
        if epistemic_state is EpistemicState.UNKNOWN:
            raise FAXTCreationError("a canonical FAXT cannot be created with UNKNOWN state")
        if not predicate.strip():
            raise FAXTCreationError("a FAXT requires a predicate")
        return cls(
            id=faxt_id,
            subject_id=subject_id,
            predicate=predicate,
            object_or_value=object_or_value,
            evidence_refs=(evidence.id,),
            observed_at=observed_at if observed_at is not None else evidence.observed_at,
            epistemic_state=epistemic_state,
            currentness=currentness,
        )
