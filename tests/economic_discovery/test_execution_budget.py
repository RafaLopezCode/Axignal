from datetime import UTC, datetime

import pytest

from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    ExecutionBudgetPolicy,
    ExecutionBudgetReservation,
    ExecutionBudgetState,
    ExecutionReservationRejected,
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
    assert next_state.cost_complete is False


def test_known_lower_bound_survives_unknown_then_known_cost() -> None:
    state = ExecutionBudgetState(amount_microunits=7, currency="USD")

    incomplete = advance_execution_budget(
        policy=_policy(),
        state=state,
        delta=ExecutionBudgetDelta(
            elapsed_ms=5,
            requests=1,
        ),
    )
    recovered = advance_execution_budget(
        policy=_policy(),
        state=incomplete,
        delta=ExecutionBudgetDelta(
            amount_microunits=1,
            currency="USD",
            elapsed_ms=5,
            requests=1,
        ),
    )

    assert incomplete.amount_microunits == 7
    assert incomplete.currency == "USD"
    assert incomplete.cost_complete is False
    assert recovered.amount_microunits == 8
    assert recovered.currency == "USD"
    assert recovered.cost_complete is False


def test_incomplete_known_lower_bound_can_fail_closed_on_unknown_cost_policy() -> None:
    state = ExecutionBudgetState(
        amount_microunits=8,
        currency="USD",
        cost_complete=False,
    )

    decision = evaluate_execution_budget(
        policy=_policy(stop_on_unknown_cost=True),
        state=state,
    )

    assert decision.stop_reason is ExecutionStopReason.COST_UNKNOWN


def test_reservation_rejects_dispatch_that_would_exceed_request_budget() -> None:
    controller = GovernedExecutionController(
        policy=_policy(max_requests=1),
        state=ExecutionBudgetState(amount_microunits=0, currency="USD"),
    )
    controller.reserve(
        ExecutionBudgetReservation(
            reservation_id="source:1",
            requests=1,
        )
    )

    with pytest.raises(ExecutionReservationRejected) as exc_info:
        controller.reserve(
            ExecutionBudgetReservation(
                reservation_id="source:2",
                requests=1,
            )
        )

    assert exc_info.value.decision.stop_reason is ExecutionStopReason.REQUEST_BUDGET_EXHAUSTED
    assert controller.active_reservation_ids == ("source:1",)


def test_resource_specific_reservation_can_continue_after_source_budget_is_exactly_used() -> None:
    controller = GovernedExecutionController(
        policy=_policy(max_sources=2, max_requests=4),
        state=ExecutionBudgetState(
            amount_microunits=0,
            currency="USD",
            sources=2,
            requests=2,
        ),
    )

    semantic = controller.reserve(
        ExecutionBudgetReservation(
            reservation_id="semantic:1",
            requests=1,
            sources=0,
        )
    )
    assert semantic.reservation_id == "semantic:1"
    controller.release("semantic:1")

    with pytest.raises(ExecutionReservationRejected) as exc_info:
        controller.reserve(
            ExecutionBudgetReservation(
                reservation_id="source:3",
                requests=1,
                sources=1,
            )
        )

    assert exc_info.value.decision.stop_reason is ExecutionStopReason.SOURCE_BUDGET_EXHAUSTED


def test_unknown_cost_reservation_fails_closed_when_policy_requires() -> None:
    controller = GovernedExecutionController(
        policy=_policy(stop_on_unknown_cost=True),
        state=ExecutionBudgetState(amount_microunits=0, currency="USD"),
    )

    with pytest.raises(ExecutionReservationRejected) as exc_info:
        controller.reserve(
            ExecutionBudgetReservation(
                reservation_id="provider:1",
                requests=1,
            )
        )

    assert exc_info.value.decision.stop_reason is ExecutionStopReason.COST_UNKNOWN
    assert controller.active_reservation_ids == ()


def test_reconciliation_records_unknown_attempt_and_releases_reservation() -> None:
    controller = GovernedExecutionController(
        policy=_policy(),
        state=ExecutionBudgetState(amount_microunits=7, currency="USD"),
    )
    controller.reserve(
        ExecutionBudgetReservation(
            reservation_id="source:1",
            requests=1,
            sources=1,
            elapsed_ms=50,
        )
    )

    state = controller.reconcile(
        "source:1",
        ExecutionBudgetDelta(
            elapsed_ms=12,
            requests=1,
            sources=1,
            made_progress=False,
        ),
    )

    assert state.amount_microunits == 7
    assert state.cost_complete is False
    assert state.requests == 1
    assert state.sources == 1
    assert state.elapsed_ms == 12
    assert controller.active_reservation_ids == ()


def test_reconciliation_records_actual_usage_even_if_it_exceeds_reservation() -> None:
    controller = GovernedExecutionController(
        policy=_policy(max_requests=2),
        state=ExecutionBudgetState(amount_microunits=0, currency="USD"),
    )
    controller.reserve(
        ExecutionBudgetReservation(
            reservation_id="provider:1",
            amount_microunits=10,
            currency="USD",
            requests=1,
        )
    )

    state = controller.reconcile(
        "provider:1",
        ExecutionBudgetDelta(
            amount_microunits=125,
            currency="USD",
            requests=2,
        ),
    )

    assert state.amount_microunits == 125
    assert state.requests == 2
    assert controller.authorize_next().stop_reason is ExecutionStopReason.MONETARY_BUDGET_EXHAUSTED


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
