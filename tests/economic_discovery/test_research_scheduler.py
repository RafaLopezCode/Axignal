from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.economic_discovery.batch_research_runtime import ResearchBatchItemResult
from application.economic_discovery.continuous_observation import SharedObservationIntent
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    ExecutionStopReason,
    GovernedExecutionController,
)
from application.economic_discovery.research_scheduler import (
    AutonomousResearchPolicy,
    ResearchScheduleOutcome,
    run_autonomous_research_cycle,
)
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 7, 0, tzinfo=UTC)


def _policy(max_attempts: int = 3) -> AutonomousResearchPolicy:
    return AutonomousResearchPolicy(
        policy_id="pb08",
        version="1",
        max_batch_size=2,
        max_attempts_per_work=max_attempts,
        base_backoff=timedelta(minutes=5),
        max_backoff=timedelta(hours=1),
        lease_for=timedelta(minutes=10),
    )


def _controller(*, no_progress=0, max_no_progress=4):
    return GovernedExecutionController(
        ExecutionBudgetPolicy(
            policy_id="pb08-budget",
            version="1",
            max_requests=20,
            max_loops=10,
            max_no_progress_streak=max_no_progress,
        ),
        state=ExecutionBudgetState(no_progress_streak=no_progress),
    )


def _memory(tmp_path, *dimensions):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intents = []
    for dimension in dimensions:
        intent = SharedObservationIntent(
            subject_id="org:acme",
            state_fingerprint="state:1",
            dimension_id=dimension,
            missing_requirements=(f"{dimension}.missing",),
            research_policy_id="research:value",
            research_policy_version="1",
            research_context_fingerprint=f"context:{dimension}",
        )
        memory.enqueue(intent, "prime:test")
        intents.append(intent)
    return memory, tuple(intents)


class _Revalidator:
    def __init__(self, blocked=frozenset()):
        self.blocked = blocked

    def may_run(self, work, *, now):
        return work.intent.dimension_id not in self.blocked


class _Executor:
    def __init__(self, resolved=frozenset(), fail=False):
        self.resolved = resolved
        self.fail = fail
        self.calls = []

    def execute_batch(self, claimed):
        self.calls.append(claimed)
        if self.fail:
            raise RuntimeError("batch failed")
        return tuple(
            ResearchBatchItemResult(
                work_key=item.lease.work_key,
                output_fingerprint=f"out:{item.work.intent.dimension_id}",
                objective_resolved=item.work.intent.dimension_id in self.resolved,
                provider="luna-batch",
                provider_version="fixture/1",
            )
            for item in claimed
        )


def test_cycle_discovers_pending_work_and_runs_only_one_bounded_batch(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo", "market")
    executor = _Executor(resolved=frozenset({"seo"}))
    cycle = run_autonomous_research_cycle(
        memory=memory,
        ledger=memory,
        execution_controller=_controller(),
        executor=executor,
        revalidator=_Revalidator(),
        policy=_policy(),
        now=NOW,
        execution_id="pb08:1",
    )
    assert len(cycle.selected_work_keys) == 2
    assert len(executor.calls) == 1
    assert memory.get(intents[0].work_key) is not None
    assert len(memory.pending_work_keys()) == 2


def test_no_progress_is_backed_off_durably_across_store_reopen(tmp_path) -> None:
    path = tmp_path / "work.sqlite3"
    memory, intents = _memory(tmp_path, "seo")
    executor = _Executor()
    run_autonomous_research_cycle(
        memory=memory, ledger=memory, execution_controller=_controller(),
        executor=executor, revalidator=_Revalidator(), policy=_policy(), now=NOW, execution_id="pb08:first",
    )
    state = memory.get_schedule(intents[0].work_key)
    assert state is not None
    assert state.last_outcome is ResearchScheduleOutcome.NO_PROGRESS
    assert state.next_eligible_at == NOW + timedelta(minutes=5)

    reopened = SqliteSharedObservationWorkMemory(path)
    second = run_autonomous_research_cycle(
        memory=reopened, ledger=reopened, execution_controller=_controller(),
        executor=executor, revalidator=_Revalidator(), policy=_policy(), now=NOW + timedelta(minutes=4),
        execution_id="pb08:too-soon",
    )
    assert second.selected_work_keys == ()
    assert len(executor.calls) == 1


def test_backoff_is_exponential_and_capped(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo")
    executor = _Executor()
    policy = _policy(max_attempts=5)
    for index, minute in enumerate((0, 5, 15), start=1):
        run_autonomous_research_cycle(
            memory=memory, ledger=memory, execution_controller=_controller(),
            executor=executor, revalidator=_Revalidator(), policy=policy, now=NOW + timedelta(minutes=minute),
            execution_id=f"pb08:{index}",
        )
    state = memory.get_schedule(intents[0].work_key)
    assert state is not None
    assert state.attempt_count == 3
    assert state.no_progress_count == 3
    assert state.next_eligible_at == NOW + timedelta(minutes=35)


def test_attempt_limit_terminally_suppresses_work_without_completing_it(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo")
    executor = _Executor()
    policy = _policy(max_attempts=1)
    run_autonomous_research_cycle(
        memory=memory, ledger=memory, execution_controller=_controller(),
        executor=executor, revalidator=_Revalidator(), policy=policy, now=NOW, execution_id="pb08:first",
    )
    later = run_autonomous_research_cycle(
        memory=memory, ledger=memory, execution_controller=_controller(),
        executor=executor, revalidator=_Revalidator(), policy=policy, now=NOW + timedelta(days=1),
        execution_id="pb08:later",
    )
    assert later.selected_work_keys == ()
    assert later.exhausted_work_keys == (intents[0].work_key,)
    assert memory.pending_work_keys() == (intents[0].work_key,)
    assert len(executor.calls) == 1


def test_global_budget_stop_prevents_claim_and_provider_execution(tmp_path) -> None:
    memory, _ = _memory(tmp_path, "seo")
    executor = _Executor()
    cycle = run_autonomous_research_cycle(
        memory=memory, ledger=memory,
        execution_controller=_controller(no_progress=2, max_no_progress=2),
        executor=executor, revalidator=_Revalidator(), policy=_policy(), now=NOW, execution_id="pb08:stopped",
    )
    assert cycle.stop_reason is ExecutionStopReason.NO_PROGRESS
    assert executor.calls == []


def test_provider_failure_is_backed_off_and_lease_is_released(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo")
    with pytest.raises(RuntimeError, match="governed research batch execution failed"):
        run_autonomous_research_cycle(
            memory=memory, ledger=memory, execution_controller=_controller(),
            executor=_Executor(fail=True), revalidator=_Revalidator(), policy=_policy(), now=NOW,
            execution_id="pb08:failure",
        )
    state = memory.get_schedule(intents[0].work_key)
    assert state is not None
    assert state.last_outcome is ResearchScheduleOutcome.FAILED
    assert memory.claim(
        intents[0].work_key,
        now=NOW + timedelta(seconds=1),
        lease_for=timedelta(minutes=1),
    ) is not None


def test_revalidation_blocks_stale_work_before_lease_or_budget(tmp_path) -> None:
    memory, intents = _memory(tmp_path, "seo", "geo")
    executor = _Executor()
    controller = _controller()
    cycle = run_autonomous_research_cycle(
        memory=memory,
        ledger=memory,
        execution_controller=controller,
        executor=executor,
        revalidator=_Revalidator(blocked=frozenset({"seo", "geo"})),
        policy=_policy(),
        now=NOW,
        execution_id="pb08:stale",
    )
    assert cycle.selected_work_keys == ()
    assert executor.calls == []
    assert controller.state.requests == 0
    assert memory.pending_work_keys() == tuple(sorted(intent.work_key for intent in intents))
