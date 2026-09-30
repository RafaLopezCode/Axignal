"""Offline-only governed policy candidates, replay evaluation and shadow comparison.

FR-19 deliberately has no production-policy mutation port. Candidates are immutable,
created only from the development side of a sealed organization/time split, and may be
compared on held-out Learning Memory events without gaining promotion authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.learning_memory import (
    LearningEvent,
    LearningOutcome,
    ReplayDisposition,
)


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("policy experiment identity is required")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class PolicyDecisionState(StrEnum):
    VALUE = "VALUE"
    UNKNOWN = "UNKNOWN"
    ABSTAIN = "ABSTAIN"
    FAILED = "FAILED"


class PolicyEvaluationStatus(StrEnum):
    EVALUATED = "EVALUATED"
    NON_REPLAYABLE = "NON_REPLAYABLE"


class PolicySplitMembership(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    HOLDOUT = "HOLDOUT"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    state: PolicyDecisionState
    reason_code: str
    value: str | None = None

    def __post_init__(self) -> None:
        _required(self.reason_code)
        if self.state is PolicyDecisionState.VALUE:
            if self.value is None or not self.value.strip():
                raise ValueError("VALUE policy decision requires a value")
        elif self.value is not None:
            raise ValueError("non-VALUE policy decision cannot carry a value")


@dataclass(frozen=True, slots=True)
class HeldOutPolicySplit:
    split_id: str
    development_organization_ids: frozenset[str]
    holdout_organization_ids: frozenset[str]
    development_end_at: datetime
    holdout_start_at: datetime

    def __post_init__(self) -> None:
        _required(self.split_id)
        if not self.development_organization_ids or not self.holdout_organization_ids:
            raise ValueError("policy split requires development and holdout organizations")
        if self.development_organization_ids.intersection(self.holdout_organization_ids):
            raise ValueError("development and holdout organizations must be disjoint")
        if self.development_end_at.tzinfo is None or self.holdout_start_at.tzinfo is None:
            raise ValueError("policy split times must be timezone-aware")
        if self.development_end_at >= self.holdout_start_at:
            raise ValueError("policy split must preserve a forward temporal holdout")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "split_id": self.split_id,
                "development_organization_ids": sorted(self.development_organization_ids),
                "holdout_organization_ids": sorted(self.holdout_organization_ids),
                "development_end_at": self.development_end_at.astimezone(UTC).isoformat(),
                "holdout_start_at": self.holdout_start_at.astimezone(UTC).isoformat(),
            }
        )

    def membership(self, event: LearningEvent) -> PolicySplitMembership | None:
        if (
            event.subject_id in self.development_organization_ids
            and event.occurred_at <= self.development_end_at
        ):
            return PolicySplitMembership.DEVELOPMENT
        if (
            event.subject_id in self.holdout_organization_ids
            and event.occurred_at >= self.holdout_start_at
        ):
            return PolicySplitMembership.HOLDOUT
        return None


@dataclass(frozen=True, slots=True)
class PolicyCandidate:
    candidate_id: str
    policy_family: str
    baseline_policy_id: str
    baseline_policy_version: str
    candidate_version: str
    code_sha: str
    split_id: str
    split_fingerprint: str
    created_at: datetime
    created_from_event_ids: tuple[str, ...]
    parameters: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _required(
            self.candidate_id,
            self.policy_family,
            self.baseline_policy_id,
            self.baseline_policy_version,
            self.candidate_version,
            self.code_sha,
            self.split_id,
            self.split_fingerprint,
        )
        if self.created_at.tzinfo is None:
            raise ValueError("policy candidate creation time must be timezone-aware")
        if not self.created_from_event_ids:
            raise ValueError("policy candidate requires development evidence")
        if len(self.created_from_event_ids) != len(set(self.created_from_event_ids)):
            raise ValueError("policy candidate development event ids must be unique")
        names = [name for name, _ in self.parameters]
        if len(names) != len(set(names)):
            raise ValueError("policy candidate parameters must be unique")
        if any(not name.strip() or not value.strip() for name, value in self.parameters):
            raise ValueError("policy candidate parameters must be non-empty")

    @property
    def production_authority(self) -> bool:
        return False

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "candidate_id": self.candidate_id,
                "policy_family": self.policy_family,
                "baseline": (self.baseline_policy_id, self.baseline_policy_version),
                "candidate_version": self.candidate_version,
                "code_sha": self.code_sha,
                "split_id": self.split_id,
                "split_fingerprint": self.split_fingerprint,
                "created_at": self.created_at.astimezone(UTC).isoformat(),
                "created_from_event_ids": self.created_from_event_ids,
                "parameters": self.parameters,
            }
        )


def create_policy_candidate(
    *,
    candidate_id: str,
    policy_family: str,
    baseline_policy_id: str,
    baseline_policy_version: str,
    candidate_version: str,
    code_sha: str,
    split: HeldOutPolicySplit,
    development_events: tuple[LearningEvent, ...],
    created_at: datetime,
    parameters: tuple[tuple[str, str], ...],
) -> PolicyCandidate:
    """Freeze a candidate from development evidence only.

    Holdout events are rejected rather than silently ignored, which prevents sealed
    holdout evidence from entering candidate construction.
    """

    if not development_events:
        raise ValueError("policy candidate requires development events")
    for event in development_events:
        membership = split.membership(event)
        if membership is not PolicySplitMembership.DEVELOPMENT:
            raise ValueError("policy candidate cannot use holdout or out-of-split evidence")

    return PolicyCandidate(
        candidate_id=candidate_id,
        policy_family=policy_family,
        baseline_policy_id=baseline_policy_id,
        baseline_policy_version=baseline_policy_version,
        candidate_version=candidate_version,
        code_sha=code_sha,
        split_id=split.split_id,
        split_fingerprint=split.fingerprint,
        created_at=created_at,
        created_from_event_ids=tuple(event.event_id for event in development_events),
        parameters=tuple(sorted(parameters)),
    )


@dataclass(frozen=True, slots=True)
class PolicyReplayInput:
    """Sanitized replay input that excludes historical outcome/reason labels."""

    event_id: str
    subject_id: str
    occurred_at: datetime
    kind: str
    mechanism: str
    input_fingerprint: str
    replay_references: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _required(
            self.event_id,
            self.subject_id,
            self.kind,
            self.mechanism,
            self.input_fingerprint,
        )
        if self.occurred_at.tzinfo is None:
            raise ValueError("policy replay input time must be timezone-aware")


class OfflinePolicyEvaluator(Protocol):
    """Pure evaluator over sanitized replay input, never sealed historical labels."""

    def evaluate(
        self,
        replay_input: PolicyReplayInput,
        candidate: PolicyCandidate | None,
    ) -> PolicyDecision:
        """Return a decision without access to production mutation ports."""


@dataclass(frozen=True, slots=True)
class ReplayEvaluation:
    event_id: str
    subject_id: str
    occurred_at: datetime
    source_outcome: LearningOutcome
    status: PolicyEvaluationStatus
    baseline: PolicyDecision | None
    candidate: PolicyDecision | None
    reason_code: str

    def __post_init__(self) -> None:
        _required(self.event_id, self.subject_id, self.reason_code)
        if self.occurred_at.tzinfo is None:
            raise ValueError("replay evaluation time must be timezone-aware")
        if self.status is PolicyEvaluationStatus.EVALUATED:
            if self.baseline is None or self.candidate is None:
                raise ValueError("evaluated replay requires baseline and candidate decisions")
        elif self.baseline is not None or self.candidate is not None:
            raise ValueError("non-replayable evaluation cannot fabricate policy decisions")


@dataclass(frozen=True, slots=True)
class PolicyCounterMetrics:
    total_holdout_cases: int
    evaluated_cases: int
    non_replayable_cases: int
    source_failed_cases: int
    baseline_unknown_cases: int
    candidate_unknown_cases: int
    baseline_abstain_cases: int
    candidate_abstain_cases: int
    baseline_failed_cases: int
    candidate_failed_cases: int
    unknown_lost: int
    abstention_lost: int
    failure_introduced: int
    value_disagreements: int

    @property
    def regression_count(self) -> int:
        return self.unknown_lost + self.abstention_lost + self.failure_introduced

    @property
    def has_regression(self) -> bool:
        return self.regression_count > 0


@dataclass(frozen=True, slots=True)
class PolicyComparisonReport:
    candidate_id: str
    candidate_fingerprint: str
    split_id: str
    split_fingerprint: str
    evaluations: tuple[ReplayEvaluation, ...]
    metrics: PolicyCounterMetrics

    @property
    def production_authority(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ShadowPolicy:
    candidate: PolicyCandidate

    @property
    def production_authority(self) -> bool:
        return False

    def evaluate(
        self,
        *,
        event: LearningEvent,
        baseline_evaluator: OfflinePolicyEvaluator,
        candidate_evaluator: OfflinePolicyEvaluator,
    ) -> ReplayEvaluation:
        if event.replay.disposition is not ReplayDisposition.REPLAYABLE:
            return ReplayEvaluation(
                event_id=event.event_id,
                subject_id=event.subject_id,
                occurred_at=event.occurred_at,
                source_outcome=event.outcome,
                status=PolicyEvaluationStatus.NON_REPLAYABLE,
                baseline=None,
                candidate=None,
                reason_code=event.replay.reason_code or "NON_REPLAYABLE",
            )

        replay_input = PolicyReplayInput(
            event_id=event.event_id,
            subject_id=event.subject_id,
            occurred_at=event.occurred_at,
            kind=event.kind.value,
            mechanism=event.mechanism.value,
            input_fingerprint=event.input_fingerprint,
            replay_references=event.replay.references,
        )
        baseline = _safe_evaluate(baseline_evaluator, replay_input, None)
        candidate = _safe_evaluate(candidate_evaluator, replay_input, self.candidate)
        return ReplayEvaluation(
            event_id=event.event_id,
            subject_id=event.subject_id,
            occurred_at=event.occurred_at,
            source_outcome=event.outcome,
            status=PolicyEvaluationStatus.EVALUATED,
            baseline=baseline,
            candidate=candidate,
            reason_code="SHADOW_EVALUATED",
        )


def _safe_evaluate(
    evaluator: OfflinePolicyEvaluator,
    replay_input: PolicyReplayInput,
    candidate: PolicyCandidate | None,
) -> PolicyDecision:
    try:
        return evaluator.evaluate(replay_input, candidate)
    except Exception as exc:
        return PolicyDecision(
            state=PolicyDecisionState.FAILED,
            reason_code=f"EVALUATOR_FAILED:{type(exc).__name__}",
        )


def _metrics(evaluations: tuple[ReplayEvaluation, ...]) -> PolicyCounterMetrics:
    evaluated = tuple(
        item for item in evaluations if item.status is PolicyEvaluationStatus.EVALUATED
    )
    pairs = tuple((item.baseline, item.candidate) for item in evaluated)
    baseline = tuple(item[0] for item in pairs if item[0] is not None)
    candidate = tuple(item[1] for item in pairs if item[1] is not None)

    def count(items: tuple[PolicyDecision, ...], state: PolicyDecisionState) -> int:
        return sum(item.state is state for item in items)

    unknown_lost = sum(
        left is not None
        and right is not None
        and left.state is PolicyDecisionState.UNKNOWN
        and right.state is PolicyDecisionState.VALUE
        for left, right in pairs
    )
    abstention_lost = sum(
        left is not None
        and right is not None
        and left.state is PolicyDecisionState.ABSTAIN
        and right.state is PolicyDecisionState.VALUE
        for left, right in pairs
    )
    failure_introduced = sum(
        left is not None
        and right is not None
        and left.state is not PolicyDecisionState.FAILED
        and right.state is PolicyDecisionState.FAILED
        for left, right in pairs
    )
    value_disagreements = sum(
        left is not None
        and right is not None
        and left.state is PolicyDecisionState.VALUE
        and right.state is PolicyDecisionState.VALUE
        and left.value != right.value
        for left, right in pairs
    )

    return PolicyCounterMetrics(
        total_holdout_cases=len(evaluations),
        evaluated_cases=len(evaluated),
        non_replayable_cases=sum(
            item.status is PolicyEvaluationStatus.NON_REPLAYABLE for item in evaluations
        ),
        source_failed_cases=sum(
            item.source_outcome is LearningOutcome.FAILED for item in evaluations
        ),
        baseline_unknown_cases=count(baseline, PolicyDecisionState.UNKNOWN),
        candidate_unknown_cases=count(candidate, PolicyDecisionState.UNKNOWN),
        baseline_abstain_cases=count(baseline, PolicyDecisionState.ABSTAIN),
        candidate_abstain_cases=count(candidate, PolicyDecisionState.ABSTAIN),
        baseline_failed_cases=count(baseline, PolicyDecisionState.FAILED),
        candidate_failed_cases=count(candidate, PolicyDecisionState.FAILED),
        unknown_lost=unknown_lost,
        abstention_lost=abstention_lost,
        failure_introduced=failure_introduced,
        value_disagreements=value_disagreements,
    )


def compare_policy_candidate(
    *,
    candidate: PolicyCandidate,
    split: HeldOutPolicySplit,
    events: tuple[LearningEvent, ...],
    baseline_evaluator: OfflinePolicyEvaluator,
    candidate_evaluator: OfflinePolicyEvaluator,
) -> PolicyComparisonReport:
    """Evaluate one immutable candidate on the sealed holdout only."""

    if candidate.split_id != split.split_id or candidate.split_fingerprint != split.fingerprint:
        raise ValueError("policy candidate does not belong to this sealed split")

    holdout: list[LearningEvent] = []
    for event in events:
        membership = split.membership(event)
        if membership is PolicySplitMembership.DEVELOPMENT:
            raise ValueError("replay comparison cannot inspect development evidence")
        if membership is PolicySplitMembership.HOLDOUT:
            holdout.append(event)

    if not holdout:
        raise ValueError("policy comparison requires held-out evidence")

    shadow = ShadowPolicy(candidate)
    evaluations = tuple(
        shadow.evaluate(
            event=event,
            baseline_evaluator=baseline_evaluator,
            candidate_evaluator=candidate_evaluator,
        )
        for event in sorted(holdout, key=lambda item: (item.occurred_at, item.event_id))
    )
    return PolicyComparisonReport(
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint,
        split_id=split.split_id,
        split_fingerprint=split.fingerprint,
        evaluations=evaluations,
        metrics=_metrics(evaluations),
    )
