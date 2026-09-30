"""Provider-neutral contracts for the measurable Economic Discovery Engine."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum


class DiscoveryStage(StrEnum):
    OBSERVE = "OBSERVE"
    REPRESENT = "REPRESENT"
    RETRIEVE = "RETRIEVE"
    FILTER = "FILTER"
    COMPILE_STATE = "COMPILE_STATE"
    BUILD_CHOICE_SPACE = "BUILD_CHOICE_SPACE"
    STRUCTURED_EVALUATE = "STRUCTURED_EVALUATE"
    INTERPRET = "INTERPRET"
    INVESTIGATE = "INVESTIGATE"
    ADMIT = "ADMIT"


class DiscoveryFailureClass(StrEnum):
    OBSERVATION_MISS = "OBSERVATION_MISS"
    REPRESENTATION_LOSS = "REPRESENTATION_LOSS"
    RETRIEVAL_MISS = "RETRIEVAL_MISS"
    FILTER_FALSE_REJECT = "FILTER_FALSE_REJECT"
    STATE_INSUFFICIENT = "STATE_INSUFFICIENT"
    CHOICE_SPACE_MISS = "CHOICE_SPACE_MISS"
    EVALUATOR_MISCLASSIFICATION = "EVALUATOR_MISCLASSIFICATION"
    INTERPRETATION_ERROR = "INTERPRETATION_ERROR"
    INVESTIGATION_MISS = "INVESTIGATION_MISS"
    ADMISSION_REJECT = "ADMISSION_REJECT"
    GROUND_TRUTH_AMBIGUOUS = "GROUND_TRUTH_AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class ChoiceOption:
    option_id: str
    meaning: str

    def __post_init__(self) -> None:
        if not self.option_id.strip() or not self.meaning.strip():
            raise ValueError("choice option id and meaning are required")


@dataclass(frozen=True, slots=True)
class ChoiceSpaceContract:
    choice_space_id: str
    version: str
    semantic_target: str
    options: tuple[ChoiceOption, ...]
    mutually_exclusive: bool
    coverage_policy: str
    scope: str
    composition_policy: str

    def __post_init__(self) -> None:
        fields = (
            self.choice_space_id,
            self.version,
            self.semantic_target,
            self.coverage_policy,
            self.scope,
            self.composition_policy,
        )
        if any(not field.strip() for field in fields):
            raise ValueError("choice-space semantic fields are required")
        if len(self.options) < 2:
            raise ValueError("choice space requires at least two options")
        ids = [option.option_id for option in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("choice option ids must be unique")

    @property
    def fingerprint(self) -> str:
        payload = {
            "choice_space_id": self.choice_space_id,
            "version": self.version,
            "semantic_target": self.semantic_target,
            "options": [(option.option_id, option.meaning) for option in self.options],
            "mutually_exclusive": self.mutually_exclusive,
            "coverage_policy": self.coverage_policy,
            "scope": self.scope,
            "composition_policy": self.composition_policy,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class StructuredJudgment:
    selected_option: str
    distribution: tuple[tuple[str, float], ...]
    evaluator: str
    evaluator_version: str
    decision_contract_id: str
    state_fingerprint: str
    question_fingerprint: str
    choice_space_fingerprint: str
    confidence: float | None = None
    replay_reference: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.selected_option,
            self.evaluator,
            self.evaluator_version,
            self.decision_contract_id,
            self.state_fingerprint,
            self.question_fingerprint,
            self.choice_space_fingerprint,
        )
        if any(not value.strip() for value in required):
            raise ValueError("structured judgment provenance is required")
        labels = [label for label, _ in self.distribution]
        if len(labels) != len(set(labels)) or self.selected_option not in labels:
            raise ValueError("structured judgment distribution is inconsistent")
        if any(
            not label.strip() or not math.isfinite(p) or p < 0.0 or p > 1.0
            for label, p in self.distribution
        ):
            raise ValueError("structured judgment distribution is invalid")
        if not math.isclose(sum(p for _, p in self.distribution), 1.0, abs_tol=1e-6):
            raise ValueError("structured judgment probabilities must sum to one")
        if self.confidence is not None and (
            not math.isfinite(self.confidence) or self.confidence < 0.0 or self.confidence > 1.0
        ):
            raise ValueError("structured judgment confidence is invalid")


@dataclass(frozen=True, slots=True)
class CandidateLineageEvent:
    candidate_id: str
    stage: DiscoveryStage
    outcome: str
    reason_code: str
    contract_version: str
    input_fingerprint: str
    output_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.candidate_id,
                self.outcome,
                self.reason_code,
                self.contract_version,
                self.input_fingerprint,
            )
        ):
            raise ValueError("candidate lineage requires explicit provenance")


@dataclass(frozen=True, slots=True)
class DiscoveryRunTrace:
    run_id: str
    code_sha: str
    config_fingerprint: str
    events: tuple[CandidateLineageEvent, ...]

    def __post_init__(self) -> None:
        if (
            not self.run_id.strip()
            or not self.code_sha.strip()
            or not self.config_fingerprint.strip()
        ):
            raise ValueError("discovery run identity is required")

    def lineage_for(self, candidate_id: str) -> tuple[CandidateLineageEvent, ...]:
        return tuple(event for event in self.events if event.candidate_id == candidate_id)
