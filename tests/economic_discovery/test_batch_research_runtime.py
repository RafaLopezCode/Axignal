from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.batch_research_runtime import (
    ResearchBatchItemResult,
    execute_governed_research_batch,
)
from application.economic_discovery.continuous_observation import SharedObservationIntent
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionReservationRejected,
    GovernedExecutionController,
)
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 6, 0, tzinfo=UTC)


def _intent(dimension: str) -> SharedObservationIntent:
    return SharedObservationIntent(
        subject_id="org:acme",
        state_fingerprint="state:1",
        dimension_id=dimension,
        missing_requirements=(f"{dimension}.missing",),
        research_policy_id="research:value",
        research_policy_version="1",
        research_context_fingerprint=f"context:{dimension}",
    )


def _memory(tmp_path, *dimensions: str):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intents = tuple(_intent(dimension) for dimension in dimensions)
    for intent in intents:
        memory.enqueue(intent, "prime:test")
    return memory, intents


def _controller(max_requests: int = 10) -> GovernedExecutionController:
    return GovernedExecutionController(
        ExecutionBudgetPolicy(
            policy_id="pb07",
            version="1",
            max_requests=max_requests,
            max_loops=4,
            max_no_progress_streak=2,
            stop_on_unknown_cost=False,
        )
    )


class _Executor:
    def __init__(self, *, no_progress: frozenset[str] = frozenset(), invalid=False, fail=False):
        self.no_progress = no_progress
        self.invalid = invalid
        self.fail = fail
        self.calls = []

    def execute_batch(self, claimed):
        self.calls.append(claimed)
        if self.fail:
            raise RuntimeError("provider batch failed")
        results = tuple(
            ResearchBatchItemResult(
                work_key=item.lease.work_key,
                output_fingerprint=f"output:{item.work.intent.dimension_id}",
                objective_resolved=item.work.intent.dimension_id not in self.no_progress,
                provider="luna-batch",
                provider_version="fixture/1",
            )
            for item in reversed(claimed)
        )
        return results[:-1] if self.invalid else results


def test_batch_executes_once_and_settles_progress_independently(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo", "market")
    controller = _controller()
    executor = _Executor(no_progress=frozenset({"geo"}))

    trace = execute_governed_research_batch(
        memory=memory,
        execution_controller=controller,
        executor=executor,
        work_keys=tuple(intent.work_key for intent in intents),
        now=NOW,
        lease_for=timedelta(minutes=5),
        max_batch_size=3,
        execution_id="pb07:1",
    )

    assert len(executor.calls) == 1
    assert set(trace.completed_work_keys) == {intents[0].work_key, intents[2].work_key}
    assert trace.released_work_keys == (intents[1].work_key,)
    assert trace.made_progress is True
    assert controller.state.requests == 3
    assert controller.state.loops == 1
    later = memory.claim(
        intents[1].work_key,
        now=NOW + timedelta(seconds=1),
        lease_for=timedelta(minutes=1),
    )
    assert later is not None


def test_budget_rejection_releases_all_claims_without_provider_call(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo")
    executor = _Executor()

    with pytest.raises(ExecutionReservationRejected):
        execute_governed_research_batch(
            memory=memory,
            execution_controller=_controller(max_requests=1),
            executor=executor,
            work_keys=tuple(intent.work_key for intent in intents),
            now=NOW,
            lease_for=timedelta(minutes=5),
            max_batch_size=2,
            execution_id="pb07:budget",
        )

    assert executor.calls == []
    assert all(
        memory.claim(
            intent.work_key,
            now=NOW + timedelta(seconds=1),
            lease_for=timedelta(minutes=1),
        )
        is not None
        for intent in intents
    )


@pytest.mark.parametrize(("invalid", "fail"), [(True, False), (False, True)])
def test_batch_failure_releases_leases_and_records_no_progress(tmp_path, invalid, fail) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo")
    controller = _controller()

    with pytest.raises((ValueError, RuntimeError)):
        execute_governed_research_batch(
            memory=memory,
            execution_controller=controller,
            executor=_Executor(invalid=invalid, fail=fail),
            work_keys=tuple(intent.work_key for intent in intents),
            now=NOW,
            lease_for=timedelta(minutes=5),
            max_batch_size=2,
            execution_id="pb07:failure",
        )

    assert controller.active_reservation_ids == ()
    assert controller.state.requests == 2
    assert controller.state.loops == 1
    assert controller.state.no_progress_streak == 1
    assert all(
        memory.claim(
            intent.work_key,
            now=NOW + timedelta(seconds=1),
            lease_for=timedelta(minutes=1),
        )
        is not None
        for intent in intents
    )


def test_empty_claim_is_a_true_noop(tmp_path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    controller = _controller()
    executor = _Executor()

    trace = execute_governed_research_batch(
        memory=memory,
        execution_controller=controller,
        executor=executor,
        work_keys=("missing",),
        now=NOW,
        lease_for=timedelta(minutes=1),
        max_batch_size=2,
        execution_id="pb07:empty",
    )

    assert trace.reservation_id is None
    assert executor.calls == []
    assert controller.state.requests == 0
    assert controller.state.loops == 0
