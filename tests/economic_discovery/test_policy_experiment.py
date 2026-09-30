from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.policy_experiment import (
    HeldOutPolicySplit,
    PolicyDecision,
    PolicyDecisionState,
    PolicyEvaluationStatus,
    ShadowPolicy,
    compare_policy_candidate,
    create_policy_candidate,
)

NOW = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)


def _event(
    event_id: str,
    *,
    subject_id: str,
    occurred_at: datetime,
    outcome: LearningOutcome = LearningOutcome.COMPLETED,
    replayable: bool = True,
) -> LearningEvent:
    replay = (
        LearningReplayReference.replayable(
            artifact_ref="cas:sha256:" + event_id.replace(":", "")[:8].ljust(8, "a"),
            code_sha="abc123",
        )
        if replayable
        else LearningReplayReference.non_replayable("FIXTURE_NON_REPLAYABLE")
    )
    return LearningEvent(
        event_id=event_id,
        kind=LearningEventKind.DETERMINISTIC_EVALUATION,
        outcome=outcome,
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id="xeed:1",
        activity_ref="market-mode",
        policy_id="prime-routing",
        policy_version="baseline-v1",
        code_sha="abc123",
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=f"input:{event_id}",
        output_fingerprint=None if outcome is LearningOutcome.FAILED else f"output:{event_id}",
        reason_code="FIXTURE",
        replay=replay,
        cost=LearningCost(),
        yield_=LearningYield(),
    )


def _split() -> HeldOutPolicySplit:
    return HeldOutPolicySplit(
        split_id="split:fr19",
        development_organization_ids=frozenset({"org:dev-a", "org:dev-b"}),
        holdout_organization_ids=frozenset({"org:hold-a", "org:hold-b"}),
        development_end_at=NOW,
        holdout_start_at=NOW + timedelta(days=1),
    )


def _candidate(split: HeldOutPolicySplit, *events: LearningEvent):
    return create_policy_candidate(
        candidate_id="candidate:routing-v2",
        policy_family="prime-routing",
        baseline_policy_id="prime-routing",
        baseline_policy_version="baseline-v1",
        candidate_version="candidate-v2",
        code_sha="def456",
        split=split,
        development_events=tuple(events),
        created_at=NOW + timedelta(hours=1),
        parameters=(("market-mode", "DETERMINISTIC"),),
    )


class _Evaluator:
    def __init__(self, decisions: dict[str, PolicyDecision]) -> None:
        self.decisions = decisions
        self.seen: list[tuple[str, bool]] = []

    def evaluate(self, event: LearningEvent, candidate) -> PolicyDecision:
        self.seen.append((event.event_id, candidate is not None))
        return self.decisions[event.event_id]


class _FailingEvaluator:
    def evaluate(self, event: LearningEvent, candidate) -> PolicyDecision:
        raise RuntimeError("fixture evaluator failure")


def test_candidate_is_immutable_offline_only_and_cannot_use_holdout_evidence() -> None:
    split = _split()
    dev = _event("learn:dev", subject_id="org:dev-a", occurred_at=NOW)
    holdout = _event(
        "learn:hold",
        subject_id="org:hold-a",
        occurred_at=NOW + timedelta(days=2),
    )

    candidate = _candidate(split, dev)
    assert candidate.production_authority is False
    assert candidate.created_from_event_ids == ("learn:dev",)
    assert candidate.split_fingerprint == split.fingerprint

    with pytest.raises(FrozenInstanceError):
        candidate.candidate_version = "mutated"  # type: ignore[misc]

    with pytest.raises(ValueError, match="cannot use holdout"):
        _candidate(split, holdout)


def test_split_requires_disjoint_organizations_and_forward_time_holdout() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        HeldOutPolicySplit(
            split_id="split:bad",
            development_organization_ids=frozenset({"org:x"}),
            holdout_organization_ids=frozenset({"org:x"}),
            development_end_at=NOW,
            holdout_start_at=NOW + timedelta(days=1),
        )

    with pytest.raises(ValueError, match="forward temporal holdout"):
        HeldOutPolicySplit(
            split_id="split:bad-time",
            development_organization_ids=frozenset({"org:dev"}),
            holdout_organization_ids=frozenset({"org:hold"}),
            development_end_at=NOW,
            holdout_start_at=NOW,
        )


def test_shadow_comparison_preserves_unknown_abstention_and_reports_regressions() -> None:
    split = _split()
    dev = _event("learn:dev", subject_id="org:dev-a", occurred_at=NOW)
    candidate = _candidate(split, dev)
    hold_unknown = _event(
        "learn:hold:unknown",
        subject_id="org:hold-a",
        occurred_at=NOW + timedelta(days=2),
    )
    hold_abstain = _event(
        "learn:hold:abstain",
        subject_id="org:hold-b",
        occurred_at=NOW + timedelta(days=2, minutes=1),
    )
    hold_same = _event(
        "learn:hold:same",
        subject_id="org:hold-a",
        occurred_at=NOW + timedelta(days=2, minutes=2),
    )

    baseline = _Evaluator(
        {
            hold_unknown.event_id: PolicyDecision(
                state=PolicyDecisionState.UNKNOWN,
                reason_code="INSUFFICIENT_EVIDENCE",
            ),
            hold_abstain.event_id: PolicyDecision(
                state=PolicyDecisionState.ABSTAIN,
                reason_code="OUT_OF_SCOPE",
            ),
            hold_same.event_id: PolicyDecision(
                state=PolicyDecisionState.VALUE,
                value="DETERMINISTIC",
                reason_code="ROUTED",
            ),
        }
    )
    challenger = _Evaluator(
        {
            hold_unknown.event_id: PolicyDecision(
                state=PolicyDecisionState.VALUE,
                value="STRUCTURED_EVALUATOR",
                reason_code="CANDIDATE_ROUTED",
            ),
            hold_abstain.event_id: PolicyDecision(
                state=PolicyDecisionState.VALUE,
                value="DETERMINISTIC",
                reason_code="CANDIDATE_ROUTED",
            ),
            hold_same.event_id: PolicyDecision(
                state=PolicyDecisionState.VALUE,
                value="STRUCTURED_EVALUATOR",
                reason_code="CANDIDATE_ROUTED",
            ),
        }
    )

    report = compare_policy_candidate(
        candidate=candidate,
        split=split,
        events=(hold_unknown, hold_abstain, hold_same),
        baseline_evaluator=baseline,
        candidate_evaluator=challenger,
    )

    assert report.production_authority is False
    assert report.metrics.total_holdout_cases == 3
    assert report.metrics.evaluated_cases == 3
    assert report.metrics.unknown_lost == 1
    assert report.metrics.abstention_lost == 1
    assert report.metrics.value_disagreements == 1
    assert report.metrics.regression_count == 2
    assert report.metrics.has_regression is True


def test_non_replayable_and_failed_source_cases_are_retained_not_dropped() -> None:
    split = _split()
    dev = _event("learn:dev", subject_id="org:dev-a", occurred_at=NOW)
    candidate = _candidate(split, dev)
    non_replayable = _event(
        "learn:hold:nr",
        subject_id="org:hold-a",
        occurred_at=NOW + timedelta(days=2),
        replayable=False,
    )
    failed = _event(
        "learn:hold:failed",
        subject_id="org:hold-b",
        occurred_at=NOW + timedelta(days=2, minutes=1),
        outcome=LearningOutcome.FAILED,
    )
    baseline = _Evaluator(
        {
            failed.event_id: PolicyDecision(
                state=PolicyDecisionState.FAILED,
                reason_code="BASELINE_FAILED",
            )
        }
    )
    challenger = _Evaluator(
        {
            failed.event_id: PolicyDecision(
                state=PolicyDecisionState.UNKNOWN,
                reason_code="PRESERVE_UNKNOWN",
            )
        }
    )

    report = compare_policy_candidate(
        candidate=candidate,
        split=split,
        events=(non_replayable, failed),
        baseline_evaluator=baseline,
        candidate_evaluator=challenger,
    )

    assert report.metrics.total_holdout_cases == 2
    assert report.metrics.non_replayable_cases == 1
    assert report.metrics.source_failed_cases == 1
    assert report.evaluations[0].status is PolicyEvaluationStatus.NON_REPLAYABLE
    assert report.evaluations[0].reason_code == "FIXTURE_NON_REPLAYABLE"
    assert report.evaluations[1].status is PolicyEvaluationStatus.EVALUATED


def test_shadow_evaluator_failure_becomes_failed_counter_metric() -> None:
    split = _split()
    dev = _event("learn:dev", subject_id="org:dev-a", occurred_at=NOW)
    candidate = _candidate(split, dev)
    hold = _event(
        "learn:hold",
        subject_id="org:hold-a",
        occurred_at=NOW + timedelta(days=2),
    )
    baseline = _Evaluator(
        {
            hold.event_id: PolicyDecision(
                state=PolicyDecisionState.UNKNOWN,
                reason_code="UNKNOWN",
            )
        }
    )

    report = compare_policy_candidate(
        candidate=candidate,
        split=split,
        events=(hold,),
        baseline_evaluator=baseline,
        candidate_evaluator=_FailingEvaluator(),
    )

    assert report.metrics.candidate_failed_cases == 1
    assert report.metrics.failure_introduced == 1
    assert report.metrics.has_regression is True
    assert report.evaluations[0].candidate is not None
    assert report.evaluations[0].candidate.state is PolicyDecisionState.FAILED
    assert report.evaluations[0].candidate.reason_code == "EVALUATOR_FAILED:RuntimeError"


def test_comparison_rejects_development_evidence_and_has_no_promotion_api() -> None:
    split = _split()
    dev = _event("learn:dev", subject_id="org:dev-a", occurred_at=NOW)
    candidate = _candidate(split, dev)
    evaluator = _Evaluator(
        {
            dev.event_id: PolicyDecision(
                state=PolicyDecisionState.UNKNOWN,
                reason_code="UNKNOWN",
            )
        }
    )

    with pytest.raises(ValueError, match="cannot inspect development evidence"):
        compare_policy_candidate(
            candidate=candidate,
            split=split,
            events=(dev,),
            baseline_evaluator=evaluator,
            candidate_evaluator=evaluator,
        )

    shadow = ShadowPolicy(candidate)
    assert shadow.production_authority is False
    assert not hasattr(candidate, "promote")
    assert not hasattr(shadow, "promote")
