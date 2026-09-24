"""Evidence and epistemic-state primitives.

Doctrine: MASTER §15 (CLAIM != WRITE, epistemic states), §19 (no single magic
percentage), §21 (observability states), §23 (anti-poisoning by design).
"""

from __future__ import annotations

from domain.evidence.admission import (
    AdmissionDecision,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionError,
    EvidenceAdmissionRequired,
    SourceAuthority,
)
from domain.evidence.epistemics import (
    Currentness,
    EpistemicState,
    Observability,
    UnknownIsNotFalseError,
    require_boolean,
    truth_value,
)

__all__ = [
    "AdmissionDecision",
    "Currentness",
    "EpistemicState",
    "Evidence",
    "EvidenceAdmission",
    "EvidenceAdmissionError",
    "EvidenceAdmissionRequired",
    "Observability",
    "SourceAuthority",
    "UnknownIsNotFalseError",
    "require_boolean",
    "truth_value",
]
