"""Explainable-basis contracts for every subscriber-visible AXIGNAL assertion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("explanation identity and provenance are required")


class BasisContribution(StrEnum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"


@dataclass(frozen=True, slots=True)
class BasisDatum:
    datum_id: str
    observation_id: str
    source_ref: str
    source_type: str
    observed_at: datetime
    excerpt_or_summary: str
    contribution: BasisContribution
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        _required(
            self.datum_id,
            self.observation_id,
            self.source_ref,
            self.source_type,
            self.excerpt_or_summary,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("basis datum time must be timezone-aware")
        if self.evidence_ref is not None and not self.evidence_ref.strip():
            raise ValueError("basis evidence ref must be non-empty when provided")


@dataclass(frozen=True, slots=True)
class ExplainableBasis:
    basis_id: str
    subject_id: str
    candidate_id: str
    semantic_target: str
    state_fingerprint: str
    contract_fingerprint: str
    evaluated_at: datetime
    data: tuple[BasisDatum, ...]
    interpretation: str
    uncertainty: str

    def __post_init__(self) -> None:
        _required(
            self.basis_id,
            self.subject_id,
            self.candidate_id,
            self.semantic_target,
            self.state_fingerprint,
            self.contract_fingerprint,
            self.interpretation,
            self.uncertainty,
        )
        if self.evaluated_at.tzinfo is None:
            raise ValueError("basis evaluation time must be timezone-aware")
        if not self.data:
            raise ValueError("subscriber-visible semantic attribution requires basis data")
        datum_ids = [datum.datum_id for datum in self.data]
        if len(datum_ids) != len(set(datum_ids)):
            raise ValueError("basis datum ids must be unique")
        if not any(item.contribution is BasisContribution.SUPPORTS for item in self.data):
            raise ValueError("visible attribution requires at least one supporting datum")


@dataclass(frozen=True, slots=True)
class ExplainableAssociation:
    association_id: str
    xeed_id: str
    candidate_id: str
    semantic_target: str
    basis: ExplainableBasis
    presentation_label: str

    def __post_init__(self) -> None:
        _required(
            self.association_id,
            self.xeed_id,
            self.candidate_id,
            self.semantic_target,
            self.presentation_label,
        )
        if self.basis.subject_id != self.xeed_id:
            raise ValueError("basis subject must match association Xeed")
        if self.basis.candidate_id != self.candidate_id:
            raise ValueError("basis candidate must match association candidate")
        if self.basis.semantic_target != self.semantic_target:
            raise ValueError("basis semantic target must match visible association")


def require_explainable_basis(
    *,
    association_id: str,
    xeed_id: str,
    candidate_id: str,
    semantic_target: str,
    presentation_label: str,
    basis: ExplainableBasis | None,
) -> ExplainableAssociation:
    """Fail closed before a semantic association becomes subscriber-visible."""
    if basis is None:
        raise ValueError("subscriber-visible association requires explainable basis")
    return ExplainableAssociation(
        association_id=association_id,
        xeed_id=xeed_id,
        candidate_id=candidate_id,
        semantic_target=semantic_target,
        basis=basis,
        presentation_label=presentation_label,
    )
