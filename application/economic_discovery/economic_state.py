"""Read-only economic inputs after normalization, rights checks and admission.

This module binds existing rich state to its considered evidence. It neither
extracts propositions nor admits them. DECLARED source statements remain so.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.explanation import BasisContribution, BasisDatum
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_effective_currentness,
)
from application.source_representation import (
    RichStateDatum,
    RichSubjectState,
    compile_rich_subject_state,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.representation import TextRepresentation


def fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EconomicObservation:
    datum: RichStateDatum
    basis: BasisDatum
    epistemic_state: EpistemicState
    currentness: Currentness
    rights_basis_ref: str
    canonical_support: FAXT | None = None
    contradicts_fields: tuple[str, ...] = ()
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    representation: TextRepresentation | None = None

    def __post_init__(self) -> None:
        if not self.rights_basis_ref.strip():
            raise ValueError("economic evidence requires an upstream public reuse rights reference")
        span = self.datum.supporting_span
        if self.representation is not None and span is None:
            raise ValueError("economic representation requires exact supporting span")
        if span is not None:
            representation = self.representation
            if representation is None:
                raise ValueError("economic datum span requires its verifiable representation")
            if (
                span.extract(representation) != self.datum.value
                or representation.observation_id != self.datum.observation_id
                or representation.representation_id != self.datum.representation_id
                or representation.source_ref != self.datum.source_ref
                or representation.source_type != self.basis.source_type
                or representation.observed_at != self.datum.observed_at
                or representation.document_fingerprint != self.basis.representation_fingerprint
            ):
                raise ValueError("economic datum exact representation support mismatch")
        if (
            self.datum.observation_id != self.basis.observation_id
            or self.datum.source_ref != self.basis.source_ref
            or self.datum.observed_at != self.basis.observed_at
            or self.datum.value not in self.basis.excerpt_or_summary
            or not self.basis.representation_fingerprint
            or not self.basis.evidence_ref
        ):
            raise ValueError("economic datum must bind exact evidence and representation material")
        if any(not field.strip() for field in self.contradicts_fields):
            raise ValueError("contradiction targets must be explicit fields")
        if (self.basis.contribution is BasisContribution.CONTRADICTS) != bool(
            self.contradicts_fields
        ):
            raise ValueError("contradicting material requires explicit affected fields")
        for time in (self.valid_from, self.valid_until):
            if time is not None and time.tzinfo is None:
                raise ValueError("economic validity times must be timezone-aware")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValueError("economic validity interval is invalid")
        if (
            self.epistemic_state in (EpistemicState.OBSERVED, EpistemicState.CORROBORATED)
            and self.canonical_support is None
        ):
            raise ValueError("OBSERVED business input requires existing admitted FAXT support")
        if self.canonical_support is not None:
            faxt = self.canonical_support
            if (
                faxt.predicate != self.datum.name
                or faxt.object_or_value != self.datum.value
                or self.basis.evidence_ref not in faxt.evidence_refs
                or faxt.observed_at != self.datum.observed_at
                or faxt.epistemic_state is not self.epistemic_state
                or faxt.currentness is not self.currentness
            ):
                raise ValueError("economic input does not match its admitted canonical support")

    def effective_currentness(
        self, *, as_of: datetime, policy: TemporalCurrentnessPolicy
    ) -> Currentness:
        current = evaluate_effective_currentness(
            observation_id=self.datum.observation_id,
            observed_at=self.datum.observed_at,
            previous=self.currentness,
            as_of=as_of,
            policy=policy,
        ).current
        if self.valid_from is not None and as_of < self.valid_from:
            return Currentness.UNKNOWN
        if self.valid_until is not None and as_of >= self.valid_until:
            return Currentness.HISTORICAL
        return current


@dataclass(frozen=True, slots=True)
class EvidenceBackedEconomicState:
    """A public-evidence input, not a new truth store or subscriber authority."""

    state: RichSubjectState
    observations: tuple[EconomicObservation, ...]

    def __post_init__(self) -> None:
        names = [item.datum.name for item in self.observations]
        if len(names) != len(set(names)):
            raise ValueError("retain conflicting material under distinct field names")
        compiled = compile_rich_subject_state(
            subject_id=self.state.subject_id,
            contributions=tuple(item.datum for item in self.observations),
        )
        if compiled != self.state:
            raise ValueError("economic state must retain every considered observation exactly")
        for item in self.observations:
            if (
                item.representation is not None
                and item.representation.subject_id != self.state.subject_id
            ):
                raise ValueError("representation support cannot cross economic subjects")
            if (
                item.canonical_support is not None
                and item.canonical_support.subject_id != self.state.subject_id
            ):
                raise ValueError("canonical support cannot cross economic subjects")
            if not set(item.contradicts_fields).issubset(self.state.available_fields):
                raise ValueError("contradiction targets must resolve within economic state")

    def get(self, name: str) -> EconomicObservation | None:
        return next((item for item in self.observations if item.datum.name == name), None)

    @property
    def fingerprint(self) -> str:
        return fingerprint(
            {
                "state": self.state.fingerprint,
                "observations": [
                    {
                        "field": item.datum.name,
                        "basis_id": item.basis.datum_id,
                        "excerpt": item.basis.excerpt_or_summary,
                        "source_type": item.basis.source_type,
                        "evidence_ref": item.basis.evidence_ref,
                        "representation": item.basis.representation_fingerprint,
                        "extraction": item.basis.extraction_fingerprint,
                        "contribution": item.basis.contribution.value,
                        "epistemic_state": item.epistemic_state.value,
                        "currentness": item.currentness.value,
                        "rights_basis_ref": item.rights_basis_ref,
                        "canonical_ref": (
                            item.canonical_support.id if item.canonical_support else None
                        ),
                        "canonical_contradictions": (
                            item.canonical_support.contradictions if item.canonical_support else ()
                        ),
                        "contradicts": item.contradicts_fields,
                        "valid_from": item.valid_from.isoformat() if item.valid_from else None,
                        "valid_until": item.valid_until.isoformat() if item.valid_until else None,
                    }
                    for item in sorted(self.observations, key=lambda value: value.datum.name)
                ],
            }
        )
