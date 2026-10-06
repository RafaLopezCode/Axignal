from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.economic_discovery.async_research_runtime import LiveResearchBudgetPolicy
from pipeline.continuous_observation.live_budget_store import SqliteLiveResearchBudgetStore

NOW = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)


def _policy(**overrides):
    values = {
        "policy_id": "pb11-budget",
        "version": "1",
        "currency": "USD",
        "max_cost_upper_bound_microunits": 300,
        "per_batch_cost_upper_bound_microunits": 100,
        "max_batches": 3,
        "max_jobs": 4,
        "reservation_lease_for": timedelta(minutes=30),
    }
    values.update(overrides)
    return LiveResearchBudgetPolicy(**values)


def test_budget_reservation_is_atomic_persistent_and_committable(tmp_path) -> None:
    path = tmp_path / "budget.sqlite3"
    store = SqliteLiveResearchBudgetStore(path)
    assert store.try_reserve(
        execution_id="pb11:1",
        job_count=2,
        now=NOW,
        policy=_policy(),
    )
    snapshot = SqliteLiveResearchBudgetStore(path).snapshot(currency="USD")
    assert snapshot.reserved_cost_upper_bound_microunits == 100
    assert snapshot.reserved_jobs == 2

    reopened = SqliteLiveResearchBudgetStore(path)
    reopened.commit("pb11:1")
    snapshot = reopened.snapshot(currency="USD")
    assert snapshot.committed_cost_upper_bound_microunits == 100
    assert snapshot.committed_batches == 1
    assert snapshot.committed_jobs == 2
    assert snapshot.reserved_batches == 0


def test_budget_fails_closed_before_exceeding_cost_or_job_limit(tmp_path) -> None:
    store = SqliteLiveResearchBudgetStore(tmp_path / "budget.sqlite3")
    assert store.try_reserve(
        execution_id="pb11:1",
        job_count=2,
        now=NOW,
        policy=_policy(max_jobs=2),
    )
    store.commit("pb11:1")
    assert not store.try_reserve(
        execution_id="pb11:2",
        job_count=1,
        now=NOW + timedelta(minutes=1),
        policy=_policy(max_jobs=2),
    )

    cost_store = SqliteLiveResearchBudgetStore(tmp_path / "cost.sqlite3")
    assert cost_store.try_reserve(
        execution_id="pb11:a",
        job_count=1,
        now=NOW,
        policy=_policy(max_cost_upper_bound_microunits=100),
    )
    cost_store.commit("pb11:a")
    assert not cost_store.try_reserve(
        execution_id="pb11:b",
        job_count=1,
        now=NOW + timedelta(minutes=1),
        policy=_policy(max_cost_upper_bound_microunits=100),
    )


def test_expired_uncommitted_reservation_is_reaped_after_crash(tmp_path) -> None:
    store = SqliteLiveResearchBudgetStore(tmp_path / "budget.sqlite3")
    policy = _policy(
        max_batches=1,
        reservation_lease_for=timedelta(minutes=5),
    )
    assert store.try_reserve(
        execution_id="pb11:crashed",
        job_count=1,
        now=NOW,
        policy=policy,
    )
    assert store.try_reserve(
        execution_id="pb11:replacement",
        job_count=1,
        now=NOW + timedelta(minutes=6),
        policy=policy,
    )
    snapshot = store.snapshot(currency="USD")
    assert snapshot.reserved_batches == 1
