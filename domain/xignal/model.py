"""Concrete Xignal domain payload.

A Xignal is an explainable economic signal emitted by the Brain. It may direct
attention but is never canonical truth and never bypasses EvidenceAdmission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.evidence.epistemics import Currentness


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("Xignal identity and explanation fields are required")


class XignalKind(StrEnum):
    ACTIVITY = "ACTIVITY"
    CHANGE = "CHANGE"
    REPRESENTATION = "REPRESENTATION"
    RELATIONSHIP = "RELATIONSHIP"
    CONTRADICTION = "CONTRADICTION"
    ANOMALY = "ANOMALY"
    DEMAND = "DEMAND"
    SUPPLY = "SUPPLY"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    OTHER = "OTHER"


class XignalEpistemicState(StrEnum):
    OBSERVED = "OBSERVED"
    POTENTIAL = "POTENTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Xignal:
    xignal_id: str
    xeed_id: str
    subject_id: str
    candidate_id: str
    kind: XignalKind
    epistemic_state: XignalEpistemicState
    title: str
    why_attention: str
    basis_ref: str
    emitted_at: datetime
    currentness: Currentness
    policy_version: str
    canonical_support_refs: tuple[str, ...] = ()
    relationship_ref: str | None = None
    pathx_ref: str | None = None
    contradictions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    sale_probability: None = None
    provider_confidence: None = None

    def __post_init__(self) -> None:
        _required(
            self.xignal_id,
            self.xeed_id,
            self.subject_id,
            self.candidate_id,
            self.title,
            self.why_attention,
            self.basis_ref,
            self.policy_version,
        )
        if self.emitted_at.tzinfo is None:
            raise ValueError("Xignal emission time must be timezone-aware")
        if (
            self.epistemic_state is XignalEpistemicState.OBSERVED
            and not self.canonical_support_refs
        ):
            raise ValueError("OBSERVED Xignal requires canonical admitted support")
        if self.epistemic_state is XignalEpistemicState.UNKNOWN and not self.unknowns:
            raise ValueError("UNKNOWN Xignal requires explicit unknowns")
        if self.sale_probability is not None:
            raise ValueError("Xignal must never expose sale probability")
        if self.provider_confidence is not None:
            raise ValueError("provider confidence cannot masquerade as Xignal truth")
        if len(set(self.canonical_support_refs)) != len(self.canonical_support_refs):
            raise ValueError("canonical Xignal support refs must be unique")

    @property
    def is_canonical_truth(self) -> bool:
        return False
