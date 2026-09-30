from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.learning_memory import LearningOutcome
from application.economic_discovery.policy_experiment import (
    PolicyCandidate,
    PolicyComparisonReport,
    PolicyDecision,
    PolicyDecisionState,
    PolicyEvaluationStatus,
    ReplayEvaluation,
    policy_counter_metrics,
)
from application.economic_discovery.policy_governance import (
    ActivePolicyRef,
    GovernanceAction,
    GovernanceApproval,
    GovernanceDecision,
    PolicyDecisionKind,
    PolicyGovernanceConflict,
    PromotionGatePolicy,
    RolloutMode,
    RolloutPlan,
    comparison_fingerprint,
    promote_policy,
    rollback_policy,
)
from pipeline.policy_governance import SqliteActivePolicyStore

NOW = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)


def _candidate(
    *,
    candidate_id: str = "candidate:routing-v2",
    baseline_version: str = "v1",
    candidate_version: str = "v2",
) -> PolicyCandidate:
    return PolicyCandidate(
        candidate_id=candidate_id,
        policy_family="prime-routing",
        baseline_policy_id="prime-routing",
        baseline_policy_version=baseline_version,
        candidate_version=candidate_version,
        code_sha="candidate-sha",
        split_id="split:fr20",
        split_fingerprint="split-fingerprint",
        created_at=NOW,
        created_from_event_ids=("learn:dev:1", "learn:dev:2"),
        parameters=(("market-mode", "DETERMINISTIC"),),
    )


def _evaluations(
    *,
    evaluated: int = 3,
    non_replayable: int = 0,
    unknown_lost: int = 0,
    abstention_lost: int = 0,
    failure_introduced: int = 0,
) -> tuple[ReplayEvaluation, ...]:
    if unknown_lost + abstention_lost + failure_introduced > evaluated:
        raise ValueError("fixture regressions cannot exceed evaluated cases")

    items: list[ReplayEvaluation] = []
    index = 0
    for _ in range(unknown_lost):
        items.append(
            ReplayEvaluation(
                event_id=f"learn:holdout:{index}",
                subject_id="org:hold",
                occurred_at=NOW + timedelta(days=2, minutes=index),
                source_outcome=LearningOutcome.COMPLETED,
                status=PolicyEvaluationStatus.EVALUATED,
                baseline=PolicyDecision(
                    state=PolicyDecisionState.UNKNOWN,
                    reason_code="INSUFFICIENT_EVIDENCE",
                ),
                candidate=PolicyDecision(
                    state=PolicyDecisionState.VALUE,
                    reason_code="CANDIDATE_VALUE",
                    value="STRUCTURED_EVALUATOR",
                ),
                reason_code="SHADOW_EVALUATED",
            )
        )
        index += 1
    for _ in range(abstention_lost):
        items.append(
            ReplayEvaluation(
                event_id=f"learn:holdout:{index}",
                subject_id="org:hold",
                occurred_at=NOW + timedelta(days=2, minutes=index),
                source_outcome=LearningOutcome.COMPLETED,
                status=PolicyEvaluationStatus.EVALUATED,
                baseline=PolicyDecision(
                    state=PolicyDecisionState.ABSTAIN,
                    reason_code="OUT_OF_SCOPE",
                ),
                candidate=PolicyDecision(
                    state=PolicyDecisionState.VALUE,
                    reason_code="CANDIDATE_VALUE",
                    value="DETERMINISTIC",
                ),
                reason_code="SHADOW_EVALUATED",
            )
        )
        index += 1
    for _ in range(failure_introduced):
        items.append(
            ReplayEvaluation(
                event_id=f"learn:holdout:{index}",
                subject_id="org:hold",
                occurred_at=NOW + timedelta(days=2, minutes=index),
                source_outcome=LearningOutcome.COMPLETED,
                status=PolicyEvaluationStatus.EVALUATED,
                baseline=PolicyDecision(
                    state=PolicyDecisionState.VALUE,
                    reason_code="BASELINE_VALUE",
                    value="DETERMINISTIC",
                ),
                candidate=PolicyDecision(
                    state=PolicyDecisionState.FAILED,
                    reason_code="EVALUATOR_FAILED:RuntimeError",
                ),
                reason_code="SHADOW_EVALUATED",
            )
        )
        index += 1
    while index < evaluated:
        items.append(
            ReplayEvaluation(
                event_id=f"learn:holdout:{index}",
                subject_id="org:hold",
                occurred_at=NOW + timedelta(days=2, minutes=index),
                source_outcome=LearningOutcome.COMPLETED,
                status=PolicyEvaluationStatus.EVALUATED,
                baseline=PolicyDecision(
                    state=PolicyDecisionState.VALUE,
                    reason_code="BASELINE_VALUE",
                    value="DETERMINISTIC",
                ),
                candidate=PolicyDecision(
                    state=PolicyDecisionState.VALUE,
                    reason_code="CANDIDATE_VALUE",
                    value="DETERMINISTIC",
                ),
                reason_code="SHADOW_EVALUATED",
            )
        )
        index += 1
    for offset in range(non_replayable):
        items.append(
            ReplayEvaluation(
                event_id=f"learn:non-replayable:{offset}",
                subject_id="org:hold",
                occurred_at=NOW + timedelta(days=3, minutes=offset),
                source_outcome=LearningOutcome.COMPLETED,
                status=PolicyEvaluationStatus.NON_REPLAYABLE,
                baseline=None,
                candidate=None,
                reason_code="PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE",
            )
        )
    return tuple(items)


def _report(
    candidate: PolicyCandidate,
    *,
    evaluated: int = 3,
    non_replayable: int = 0,
    unknown_lost: int = 0,
    abstention_lost: int = 0,
    failure_introduced: int = 0,
) -> PolicyComparisonReport:
    evaluations = _evaluations(
        evaluated=evaluated,
        non_replayable=non_replayable,
        unknown_lost=unknown_lost,
        abstention_lost=abstention_lost,
        failure_introduced=failure_introduced,
    )
    return PolicyComparisonReport(
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint,
        split_id=candidate.split_id,
        split_fingerprint=candidate.split_fingerprint,
        evaluations=evaluations,
        metrics=policy_counter_metrics(evaluations),
    )


def _gate(*, require_canary: bool = True) -> PromotionGatePolicy:
    return PromotionGatePolicy(
        policy_id="promotion-gate",
        version="1",
        min_evaluated_holdout_cases=2,
        max_non_replayable_cases=0,
        require_zero_regressions=True,
        require_canary=require_canary,
    )


def _approval(
    candidate: PolicyCandidate,
    report: PolicyComparisonReport,
    gate: PromotionGatePolicy,
    *,
    action: GovernanceAction,
    decision: GovernanceDecision = GovernanceDecision.APPROVE,
    target_decision_id: str | None = None,
    approval_id: str = "approval:1",
) -> GovernanceApproval:
    return GovernanceApproval(
        approval_id=approval_id,
        action=action,
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint,
        comparison_fingerprint=comparison_fingerprint(report),
        gate_policy_id=gate.policy_id,
        gate_policy_version=gate.version,
        decision=decision,
        approved_by="governance:human:1",
        approved_at=NOW + timedelta(hours=2),
        rationale="Reviewed held-out evidence and explicit counter-metrics.",
        target_decision_id=target_decision_id,
    )


def _baseline() -> ActivePolicyRef:
    return ActivePolicyRef(
        policy_family="prime-routing",
        policy_id="prime-routing",
        policy_version="v1",
        code_sha="baseline-sha",
    )


def test_governed_promotion_is_durable_canary_and_rollback_appends_history(tmp_path) -> None:
    path = tmp_path / "policy-governance.sqlite3"
    store = SqliteActivePolicyStore(path)
    baseline = _baseline()
    assert store.seed_active(baseline) is True

    candidate = _candidate()
    report = _report(candidate)
    gate = _gate()
    approval = _approval(
        candidate,
        report,
        gate,
        action=GovernanceAction.PROMOTE,
    )
    promotion = promote_policy(
        candidate=candidate,
        report=report,
        approval=approval,
        gate=gate,
        rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
        store=store,
        decision_id="decision:promote:v2",
        decided_at=NOW + timedelta(hours=3),
    )

    assert promotion.kind is PolicyDecisionKind.PROMOTION
    assert promotion.rollout.mode is RolloutMode.CANARY
    assert promotion.rollout.canary_percent == 10
    assert promotion.approved_by == "governance:human:1"
    assert promotion.approval_rationale == approval.rationale
    assert promotion.from_policy == baseline
    assert promotion.to_policy.policy_version == "v2"
    assert store.current("prime-routing") == promotion.to_policy
    assert store.history("prime-routing") == (promotion,)

    rollback_approval = _approval(
        candidate,
        report,
        gate,
        action=GovernanceAction.ROLLBACK,
        target_decision_id=promotion.decision_id,
        approval_id="approval:rollback:v2",
    )
    rollback = rollback_policy(
        promotion_decision_id=promotion.decision_id,
        approval=rollback_approval,
        gate=gate,
        store=store,
        decision_id="decision:rollback:v2",
        decided_at=NOW + timedelta(hours=4),
    )

    assert rollback.kind is PolicyDecisionKind.ROLLBACK
    assert rollback.rollback_of == promotion.decision_id
    assert rollback.previous_decision_id == promotion.decision_id
    assert rollback.from_policy == promotion.to_policy
    assert rollback.to_policy == baseline
    assert store.current("prime-routing") == baseline
    assert store.history("prime-routing") == (promotion, rollback)

    reopened = SqliteActivePolicyStore(path)
    assert reopened.current("prime-routing") == baseline
    assert reopened.get_decision(promotion.decision_id) == promotion
    assert reopened.get_decision(rollback.decision_id) == rollback
    assert reopened.history("prime-routing") == (promotion, rollback)


def test_runtime_or_rejected_approval_cannot_self_promote(tmp_path) -> None:
    store = SqliteActivePolicyStore(tmp_path / "policy.sqlite3")
    store.seed_active(_baseline())
    candidate = _candidate()
    report = _report(candidate)
    gate = _gate()

    rejected = _approval(
        candidate,
        report,
        gate,
        action=GovernanceAction.PROMOTE,
        decision=GovernanceDecision.REJECT,
    )
    with pytest.raises(ValueError, match="explicit APPROVE"):
        promote_policy(
            candidate=candidate,
            report=report,
            approval=rejected,
            gate=gate,
            rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            store=store,
            decision_id="decision:rejected",
            decided_at=NOW + timedelta(hours=3),
        )

    assert store.current("prime-routing") == _baseline()
    assert store.history("prime-routing") == ()


def test_promotion_gate_blocks_regression_insufficient_holdout_and_missing_canary(
    tmp_path,
) -> None:
    candidate = _candidate()
    gate = _gate()

    cases = (
        (
            _report(candidate, unknown_lost=1),
            RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            "governed regressions",
        ),
        (
            _report(candidate, evaluated=1),
            RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            "insufficient evaluated holdout",
        ),
        (
            _report(candidate),
            RolloutPlan(mode=RolloutMode.DIRECT),
            "requires canary",
        ),
    )
    for index, (report, rollout, message) in enumerate(cases):
        store = SqliteActivePolicyStore(tmp_path / f"gate-{index}.sqlite3")
        store.seed_active(_baseline())
        approval = _approval(
            candidate,
            report,
            gate,
            action=GovernanceAction.PROMOTE,
            approval_id=f"approval:{index}",
        )
        with pytest.raises(ValueError, match=message):
            promote_policy(
                candidate=candidate,
                report=report,
                approval=approval,
                gate=gate,
                rollout=rollout,
                store=store,
                decision_id=f"decision:{index}",
                decided_at=NOW + timedelta(hours=3),
            )
        assert store.current("prime-routing") == _baseline()


def test_stale_baseline_and_evidence_mismatch_fail_closed(tmp_path) -> None:
    store = SqliteActivePolicyStore(tmp_path / "policy.sqlite3")
    store.seed_active(
        ActivePolicyRef(
            policy_family="prime-routing",
            policy_id="prime-routing",
            policy_version="v9",
            code_sha="newer-sha",
        )
    )
    candidate = _candidate()
    report = _report(candidate)
    gate = _gate()
    approval = _approval(candidate, report, gate, action=GovernanceAction.PROMOTE)

    with pytest.raises(ValueError, match="baseline is stale"):
        promote_policy(
            candidate=candidate,
            report=report,
            approval=approval,
            gate=gate,
            rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            store=store,
            decision_id="decision:stale",
            decided_at=NOW + timedelta(hours=3),
        )

    store2 = SqliteActivePolicyStore(tmp_path / "policy-2.sqlite3")
    store2.seed_active(_baseline())
    wrong_approval = GovernanceApproval(
        approval_id="approval:wrong",
        action=GovernanceAction.PROMOTE,
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint,
        comparison_fingerprint="wrong-report",
        gate_policy_id=gate.policy_id,
        gate_policy_version=gate.version,
        decision=GovernanceDecision.APPROVE,
        approved_by="governance:human:1",
        approved_at=NOW + timedelta(hours=2),
        rationale="Wrong evidence fixture.",
    )
    with pytest.raises(ValueError, match="comparison evidence mismatch"):
        promote_policy(
            candidate=candidate,
            report=report,
            approval=wrong_approval,
            gate=gate,
            rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            store=store2,
            decision_id="decision:wrong-evidence",
            decided_at=NOW + timedelta(hours=3),
        )


def test_rollback_requires_rollback_scoped_approval_for_exact_promotion(tmp_path) -> None:
    store = SqliteActivePolicyStore(tmp_path / "policy.sqlite3")
    store.seed_active(_baseline())
    candidate = _candidate()
    report = _report(candidate)
    gate = _gate()
    promotion_approval = _approval(
        candidate,
        report,
        gate,
        action=GovernanceAction.PROMOTE,
    )
    promotion = promote_policy(
        candidate=candidate,
        report=report,
        approval=promotion_approval,
        gate=gate,
        rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
        store=store,
        decision_id="decision:promote",
        decided_at=NOW + timedelta(hours=3),
    )

    with pytest.raises(ValueError, match="rollback-scoped"):
        rollback_policy(
            promotion_decision_id=promotion.decision_id,
            approval=promotion_approval,
            gate=gate,
            store=store,
            decision_id="decision:bad-rollback",
            decided_at=NOW + timedelta(hours=4),
        )

    wrong_target = _approval(
        candidate,
        report,
        gate,
        action=GovernanceAction.ROLLBACK,
        target_decision_id="decision:other",
        approval_id="approval:wrong-target",
    )
    with pytest.raises(ValueError, match="different promotion"):
        rollback_policy(
            promotion_decision_id=promotion.decision_id,
            approval=wrong_target,
            gate=gate,
            store=store,
            decision_id="decision:wrong-target",
            decided_at=NOW + timedelta(hours=4),
        )

    assert store.current("prime-routing") == promotion.to_policy
    assert store.history("prime-routing") == (promotion,)


def test_store_is_append_only_and_baseline_cannot_be_reseeded(tmp_path) -> None:
    store = SqliteActivePolicyStore(tmp_path / "policy.sqlite3")
    assert store.seed_active(_baseline()) is True
    assert store.seed_active(_baseline()) is False

    with pytest.raises(PolicyGovernanceConflict, match="already initialized"):
        store.seed_active(
            ActivePolicyRef(
                policy_family="prime-routing",
                policy_id="prime-routing",
                policy_version="other",
                code_sha="other-sha",
            )
        )


def test_rollout_contract_rejects_invalid_canary_shapes() -> None:
    with pytest.raises(ValueError, match="1 through 99"):
        RolloutPlan(mode=RolloutMode.CANARY, canary_percent=100)
    with pytest.raises(ValueError, match="1 through 99"):
        RolloutPlan(mode=RolloutMode.CANARY, canary_percent=0)
    with pytest.raises(ValueError, match="direct rollout"):
        RolloutPlan(mode=RolloutMode.DIRECT, canary_percent=10)


def test_promotion_recomputes_report_metrics_instead_of_trusting_caller(tmp_path) -> None:
    store = SqliteActivePolicyStore(tmp_path / "policy-metrics.sqlite3")
    store.seed_active(_baseline())
    candidate = _candidate()
    report = _report(candidate)
    forged = PolicyComparisonReport(
        candidate_id=report.candidate_id,
        candidate_fingerprint=report.candidate_fingerprint,
        split_id=report.split_id,
        split_fingerprint=report.split_fingerprint,
        evaluations=report.evaluations,
        metrics=replace(report.metrics, evaluated_cases=report.metrics.evaluated_cases + 1),
    )
    gate = _gate()
    approval = _approval(
        candidate,
        forged,
        gate,
        action=GovernanceAction.PROMOTE,
        approval_id="approval:forged-metrics",
    )

    with pytest.raises(ValueError, match="metrics do not match sealed evaluations"):
        promote_policy(
            candidate=candidate,
            report=forged,
            approval=approval,
            gate=gate,
            rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            store=store,
            decision_id="decision:forged-metrics",
            decided_at=NOW + timedelta(hours=3),
        )

    assert store.current("prime-routing") == _baseline()
    assert store.history("prime-routing") == ()
