"""Reservation estimates must not be attributed as measured provider charges."""

import pytest

from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    ExecutionReservationRejected,
    GovernedExecutionController,
)
from application.economic_discovery.governed_dispatch import DispatchCost, GovernedDispatchRecorder


def recorder(**limits):
    return GovernedDispatchRecorder(
        GovernedExecutionController(
            ExecutionBudgetPolicy("actual-cost-test", "1", **limits),
            ExecutionBudgetState(amount_microunits=0, currency="USD"),
        )
    )


def dispatch(log, charge, *, success=None):
    return log.execute(
        kind="fixture",
        reservation_id=log.next_id("fixture"),
        requests=1,
        sources=0,
        loops=1,
        cost=DispatchCost(10, "USD"),
        call=lambda: charge,
        reported_cost=lambda result: result,
        success=success,
    )


def test_reported_cost_preserves_lower_bound_across_unknown_actual_charge():
    log = recorder(currency="USD", max_amount_microunits=100)
    for charge in (DispatchCost(7, "USD"), DispatchCost(), DispatchCost(1, "USD")):
        dispatch(log, charge)
    assert log.controller.state.amount_microunits == 8
    assert log.controller.state.cost_complete is False
    assert [item.amount_microunits for item in log.records] == [7, None, 1]
    assert log.controller.active_reservation_ids == ()


def test_transport_failure_does_not_bill_reservation_as_actual():
    log = recorder(currency="USD", max_amount_microunits=100)

    def fail():
        raise TimeoutError("untrusted response")

    with pytest.raises(TimeoutError):
        log.execute(
            kind="fixture",
            reservation_id="fail",
            requests=1,
            sources=0,
            loops=1,
            cost=DispatchCost(10, "USD"),
            call=fail,
            reported_cost=lambda result: result,
        )
    assert log.records[0].amount_microunits is None
    assert log.records[0].succeeded is False
    assert log.controller.state.cost_complete is False
    assert log.controller.active_reservation_ids == ()


def test_semantically_invalid_paid_response_retains_actual_spend():
    log = recorder(currency="USD", max_amount_microunits=100)
    dispatch(log, DispatchCost(7, "USD"), success=lambda result: False)
    assert log.records[0].succeeded is False
    assert log.controller.state.amount_microunits == 7
    assert log.controller.state.cost_complete is True


def test_reservation_rejection_occurs_before_any_provider_work():
    log = recorder(currency="USD", max_amount_microunits=5)
    with pytest.raises(ExecutionReservationRejected):
        dispatch(log, DispatchCost(1, "USD"))
    assert log.records == []
    assert log.controller.state.requests == 0
