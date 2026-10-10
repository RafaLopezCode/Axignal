"""Observe the durable budget from inside dispatch, then restart the real store."""

from dataclasses import replace
from pathlib import Path

import pytest

from application.observation_intelligence import SourceRegistry
from application.observation_runtime import (
    DailyObservationBudget,
    ObservationFamily,
    run_daily_tick,
)
from application.observation_runtime.budget import BudgetUsage
from application.observation_runtime.families import FAMILY_POLICIES
from application.observation_runtime.ports import Acquisition
from tests.observation_runtime.harness import ATTENTION, DAY_1, world


@pytest.mark.parametrize("outcome", ["success", "failure", "blocked", "invalid_cost"])
def test_reservation_is_durable_before_dispatch_and_settles_only_known_spend(
    tmp_path: Path,
    outcome: str,
) -> None:
    w = world(tmp_path)
    source = replace(SourceRegistry().get("official-public-website"), cost_per_request_microunits=5)
    seen = []

    class BoundedPort:
        def acquisition_key(self, request):
            return "synthetic:bounded-request"

        def worst_case_requests(self, request):
            return 3

        def acquire(self, request):
            held = w.store().budget_usage(DAY_1.date().isoformat())
            seen.append(held)
            assert held.requests == 3 and held.paid_cost_microunits == 15
            assert held.pending_acquisitions == {
                "synthetic:bounded-request": {"requests": 3, "paid_cost_microunits": 15},
            }
            return Acquisition(
                0 if outcome == "blocked" else 1,
                0 if outcome == "blocked" else 16 if outcome == "invalid_cost" else 5,
                1,
                failure="timeout" if outcome == "failure" else None,
                blocked="RIGHTS_REVOKED" if outcome == "blocked" else None,
            )

    def run():
        return run_daily_tick(
            store=w.store(),
            now=DAY_1,
            attention=ATTENTION,
            acquirers={source.source_id: BoundedPort()},
            recompute=w.downstream,
            policies={ObservationFamily.VALUE: FAMILY_POLICIES[ObservationFamily.VALUE]},
            registry=SourceRegistry((source,)),
            budget=DailyObservationBudget(max_http_requests=3, max_paid_cost_microunits=15),
        )

    if outcome == "invalid_cost":
        with pytest.raises(RuntimeError, match="registered cost bound"):
            run()
        assert w.store().budget_usage(DAY_1.date().isoformat()) == seen[0]
        assert not w.store().receipts(DAY_1.date().isoformat())
        return
    report = run()
    actual = 0 if outcome == "blocked" else 1
    restarted_usage = w.store().budget_usage(DAY_1.date().isoformat())
    assert restarted_usage.requests == actual
    assert restarted_usage.paid_cost_microunits == actual * 5
    assert restarted_usage.actions == 1 and not restarted_usage.pending_acquisitions
    assert restarted_usage.family_requests == {"value": actual}
    assert restarted_usage.source_requests == {source.source_id: actual}
    assert restarted_usage.source_failures == (
        {source.source_id: 1} if outcome == "failure" else {}
    )
    assert report.requests == actual
    assert len(w.store().receipts(DAY_1.date().isoformat())) == 1


def test_legacy_usage_reads_without_migration_or_invented_reservations() -> None:
    old = BudgetUsage("2026-10-06", requests=2, paid_cost_microunits=4).to_payload()
    old.pop("pending_acquisitions")
    restored = BudgetUsage.from_payload(old)
    assert restored.requests == 2 and restored.paid_cost_microunits == 4
    assert restored.pending_acquisitions == {}
