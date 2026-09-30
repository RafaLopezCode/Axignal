from datetime import UTC, datetime

import pytest

from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    ExecutionStopReason,
    GovernedExecutionController,
    advance_execution_budget,
    evaluate_execution_budget,
)
from application.economic_discovery.execution_learning import execution_stop_learning_event
from application.economic_discovery.learning_memory import (
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
)

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _policy(**overrides) -> ExecutionBudgetPolicy:
    values = {
        "policy_id": "exec-budget",
        "version": "1",
        "currency": "USD",
        "max_amount_microunits": 100,
        "max_requests": 3,
        "max_sources": 2,
        "max_elapsed_ms": 1_000,
        "max_retries": 2,
        "max_loops": 4,
        "max_no_progress_streak": 2,
        "stop_on_unknown_cost": False,
    }
    values.update(overrides)
    return ExecutionBudgetPolicy(**values)


@pytest.mark.parametrize(
    ("state", "reason"),
    (
        (
            ExecutionBudgetState(amount_microunits=100, currency="USD"),
            ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", requests=3),
            ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", sources=2),
            ExecutionStopReason.SOURCE_BUDGET_EXHAUSTED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", elapsed_ms=1_000),
            ExecutionStopReason.DEADLINE_EXCEEDED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", retries=2),
            ExecutionStopReason.RETRY_LIMIT_REACHED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", loops=4),
            ExecutionStopReason.LOOP_LIMIT_REACHED,
        ),
        (
            ExecutionBudgetState(amount_microunits=0, currency="USD", no_progress_streak=2),
            ExecutionStopReason.NO_PROGRESS,
        ),
    ),
)
def test_budget_stops_deterministically_at_each_limit(
    state: ExecutionBudgetState,
    reason: ExecutionStopReason,
) -> None:
    decision = evaluate_execution_budget(policy=_policy(), state=state)
    assert not decision.may_continue
    assert decision.stop_reason is reason


def test_unknown_cost_remains_unknown_and_can_fail_closed_when_policy_requires() -> None:
    state = ExecutionBudgetState()
    policy = _policy(stop_on_unknown_cost=True)

    decision = evaluate_execution_budget(policy=policy, state=state)

    assert state.amount_microunits is None
    assert decision.stop_reason is ExecutionStopReason.COST_UNKNOWN


def test_progress_resets_no_progress_streak() -> None:
    state = ExecutionBudgetState(
        amount_microunits=10,
        currency="USD",
        no_progress_streak=1,
    )
    next_state = advance_execution_budget(
        policy=_policy(),
        state=state,
        delta=ExecutionBudgetDelta(
            amount_microunits=5,
            currency="USD",
            elapsed_ms=10,
            requests=1,
            loops=1,
            made_progress=True,
        ),
    )

    assert next_state.amount_microunits == 15
    assert next_state.no_progress_streak == 0
    assert next_state.requests == 1
    assert next_state.loops == 1


def test_unknown_cost_is_not_silently_converted_to_zero() -> None:
    state = ExecutionBudgetState()
    next_state = advance_execution_budget(
        policy=_policy(),
        state=state,
        delta=ExecutionBudgetDelta(
            elapsed_ms=5,
            requests=1,
        ),
    )

    assert next_state.amount_microunits is None
    assert next_state.currency is None


def test_governed_controller_cannot_continue_after_loop_limit() -> None:
    controller = GovernedExecutionController(
        policy=_policy(max_loops=2),
        state=ExecutionBudgetState(amount_microunits=0, currency="USD"),
    )

    assert controller.authorize_next().may_continue
    controller.record(
        ExecutionBudgetDelta(amount_microunits=1, currency="USD", made_progress=False)
    )
    assert controller.authorize_next().may_continue
    controller.record(
        ExecutionBudgetDelta(amount_microunits=1, currency="USD", made_progress=False)
    )

    stopped = controller.authorize_next()
    assert not stopped.may_continue
    assert stopped.stop_reason is ExecutionStopReason.LOOP_LIMIT_REACHED

    with pytest.raises(RuntimeError, match="execution already stopped"):
        controller.record(ExecutionBudgetDelta(amount_microunits=1, currency="USD"))


def test_stop_reason_enters_learning_memory_as_partial_outcome() -> None:
    policy = _policy(max_requests=1)
    state = ExecutionBudgetState(
        amount_microunits=25,
        currency="USD",
        requests=1,
        elapsed_ms=80,
    )
    decision = evaluate_execution_budget(policy=policy, state=state)

    event = execution_stop_learning_event(
        event_id="learn:stop:1",
        occurred_at=NOW,
        subject_id="org:1",
        xeed_id="xeed:1",
        activity_ref="research:1",
        code_sha="abc123",
        kind=LearningEventKind.ADAPTIVE_RESEARCH,
        mechanism=LearningMechanism.ADAPTIVE_RESEARCH,
        policy=policy,
        state=state,
        decision=decision,
        before_state_fingerprint="state:before",
        after_state_fingerprint="state:before",
    )

    assert event.outcome is LearningOutcome.PARTIAL
    assert event.reason_code == ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED.value
    assert event.cost.amount_microunits == 25
    assert event.cost.latency_ms == 80
    assert event.before_state_fingerprint == event.after_state_fingerprint
    assert event.yield_.total_observed_output == 0
