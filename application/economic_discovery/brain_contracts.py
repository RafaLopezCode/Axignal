"""Executable contracts for AXIGNAL's governed cognitive loop."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("explicit non-empty semantic identity is required")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ObservationMode(StrEnum):
    DETERMINISTIC_SENSOR = "DETERMINISTIC_SENSOR"
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    DIRECT_EVENT = "DIRECT_EVENT"


class SemanticPrimitive(StrEnum):
    CHOICE = "CHOICE"
    NOUL = "NOUL"
    SCORE = "SCORE"


class DimensionDisposition(StrEnum):
    ANSWERABLE = "ANSWERABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ANSWERABLE = "NOT_ANSWERABLE"


class AttentionDisposition(StrEnum):
    RETAIN = "RETAIN"
    INVESTIGATE = "INVESTIGATE"
    WARRANTED_ATTENTION = "WARRANTED_ATTENTION"


@dataclass(frozen=True, slots=True)
class ObservationRecord:
    observation_id: str
    subject_id: str
    source_ref: str
    source_type: str
    observed_at: datetime
    content_fingerprint: str
    mode: ObservationMode

    def __post_init__(self) -> None:
        _required(
            self.observation_id,
            self.subject_id,
            self.source_ref,
            self.source_type,
            self.content_fingerprint,
        )
        if self.observed_at.tzinfo is None:
            raise ValueError("observation time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TypingDimensionContract:
    dimension_id: str
    version: str
    semantic_target: str
    primitive: SemanticPrimitive
    question: str
    state_requirements: tuple[str, ...]
    dependencies: tuple[str, ...]
    mutually_exclusive: bool
    abstention_policy: str

    def __post_init__(self) -> None:
        _required(
            self.dimension_id,
            self.version,
            self.semantic_target,
            self.question,
            self.abstention_policy,
        )
        if len(set(self.state_requirements)) != len(self.state_requirements):
            raise ValueError("state requirements must be unique")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("dependencies must be unique")
        if self.primitive is SemanticPrimitive.NOUL and self.mutually_exclusive:
            raise ValueError("independent NOUL dimensions cannot declare mutual exclusivity")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "dimension_id": self.dimension_id,
                "version": self.version,
                "semantic_target": self.semantic_target,
                "primitive": self.primitive,
                "question": self.question,
                "state_requirements": self.state_requirements,
                "dependencies": self.dependencies,
                "mutually_exclusive": self.mutually_exclusive,
                "abstention_policy": self.abstention_policy,
            }
        )


@dataclass(frozen=True, slots=True)
class DimensionEvaluation:
    dimension_id: str
    contract_fingerprint: str
    disposition: DimensionDisposition
    evaluator: str | None = None
    evaluator_version: str | None = None
    distribution: tuple[tuple[str, float], ...] = ()
    score: float | None = None
    confidence: float | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        _required(self.dimension_id, self.contract_fingerprint)
        if self.disposition is not DimensionDisposition.ANSWERABLE:
            if (
                self.evaluator
                or self.distribution
                or self.score is not None
                or self.confidence is not None
            ):
                raise ValueError("non-answerable dimensions cannot fabricate evaluator output")
            _required(self.reason or "")
            return
        _required(self.evaluator or "", self.evaluator_version or "")
        labels = [label for label, _ in self.distribution]
        if len(labels) != len(set(labels)):
            raise ValueError("distribution labels must be unique")
        if any(
            not label.strip() or not math.isfinite(value) or value < 0.0 or value > 1.0
            for label, value in self.distribution
        ):
            raise ValueError("distribution values must be finite probabilities")
        if self.confidence is not None and (
            not math.isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError("confidence must be a finite probability")
        if self.score is not None and not math.isfinite(self.score):
            raise ValueError("score must be finite")


@dataclass(frozen=True, slots=True)
class TypedJudgmentVector:
    subject_id: str
    candidate_id: str
    state_fingerprint: str
    evaluated_at: datetime
    evaluations: tuple[DimensionEvaluation, ...]

    def __post_init__(self) -> None:
        _required(self.subject_id, self.candidate_id, self.state_fingerprint)
        if self.evaluated_at.tzinfo is None:
            raise ValueError("evaluation time must be timezone-aware")
        ids = [item.dimension_id for item in self.evaluations]
        if len(ids) != len(set(ids)):
            raise ValueError("typed judgment vector requires unique dimensions")


@dataclass(frozen=True, slots=True)
class StateChange:
    subject_id: str
    changed_fields: frozenset[str]
    previous_fingerprint: str
    current_fingerprint: str

    def __post_init__(self) -> None:
        _required(self.subject_id, self.previous_fingerprint, self.current_fingerprint)
        if not self.changed_fields:
            raise ValueError("state change requires at least one changed field")
        if self.previous_fingerprint == self.current_fingerprint:
            raise ValueError("state change fingerprints must differ")


def affected_dimensions(
    change: StateChange,
    contracts: tuple[TypingDimensionContract, ...],
) -> tuple[str, ...]:
    """Return only dimensions whose declared dependencies intersect the state change."""
    return tuple(
        contract.dimension_id
        for contract in contracts
        if change.changed_fields.intersection(contract.dependencies)
    )


@dataclass(frozen=True, slots=True)
class EpistemicProfile:
    evidence_support: float
    provenance_quality: float
    currentness: float
    corroboration: float
    contradiction: float
    coverage: float

    def __post_init__(self) -> None:
        values = (
            self.evidence_support,
            self.provenance_quality,
            self.currentness,
            self.corroboration,
            self.contradiction,
            self.coverage,
        )
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("epistemic profile dimensions must be finite probabilities")


@dataclass(frozen=True, slots=True)
class XignalPresentation:
    xignal_id: str
    subject_id: str
    candidate_id: str
    attention: AttentionDisposition
    epistemic_profile: EpistemicProfile
    explanation_ref: str
    policy_version: str
    sale_probability: None = None

    def __post_init__(self) -> None:
        _required(
            self.xignal_id,
            self.subject_id,
            self.candidate_id,
            self.explanation_ref,
            self.policy_version,
        )
        if self.sale_probability is not None:
            raise ValueError("Xignal presentation must never encode sale probability")


@dataclass(frozen=True, slots=True)
class ObservationTask:
    task_id: str
    subject_id: str
    mode: ObservationMode
    objective: str
    source_hint: str | None = None

    def __post_init__(self) -> None:
        _required(self.task_id, self.subject_id, self.objective)
        if self.source_hint is not None:
            _required(self.source_hint)


@dataclass(frozen=True, slots=True)
class ObservationPlan:
    plan_id: str
    subject_id: str
    version: str
    tasks: tuple[ObservationTask, ...]

    def __post_init__(self) -> None:
        _required(self.plan_id, self.subject_id, self.version)
        ids = [task.task_id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("observation task ids must be unique")
        if any(task.subject_id != self.subject_id for task in self.tasks):
            raise ValueError("observation plan cannot mix subjects")


@dataclass(frozen=True, slots=True)
class EconomicAssociationSnapshot:
    association_id: str
    xeed_id: str
    candidate_id: str
    state_fingerprint: str
    judgment_vector: TypedJudgmentVector
    valid_at: datetime
    previous_snapshot_ref: str | None = None

    def __post_init__(self) -> None:
        _required(self.association_id, self.xeed_id, self.candidate_id, self.state_fingerprint)
        if self.valid_at.tzinfo is None:
            raise ValueError("association snapshot time must be timezone-aware")
        if self.judgment_vector.subject_id != self.xeed_id:
            raise ValueError("association Xeed must match judgment subject")
        if self.judgment_vector.candidate_id != self.candidate_id:
            raise ValueError("association candidate must match judgment candidate")
        if self.judgment_vector.state_fingerprint != self.state_fingerprint:
            raise ValueError("association state must match judgment state")
