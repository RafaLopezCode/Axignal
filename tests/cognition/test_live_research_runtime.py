from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.economic_discovery.async_research_runtime import LiveResearchBudgetPolicy
from application.economic_discovery.continuous_observation import SharedObservationIntent
from application.economic_discovery.research_scheduler import (
    AutonomousResearchPolicy,
    ResearchScheduleOutcome,
)
from cognition.async_research_canary import (
    AsyncCanaryTick,
    DurableCanaryClaim,
    DurableCanaryExecution,
)
from cognition.live_research_runtime import (
    CanaryResearchRevalidator,
    GovernedAsyncResearchRunner,
)
from pipeline.continuous_observation.live_budget_store import SqliteLiveResearchBudgetStore
from pipeline.continuous_observation.sqlite_store import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 6, 10, 0, tzinfo=UTC)


class _ExecutionStore:
    def __init__(self):
        self.active = None

    def active_for_subject(self, subject_id):
        if self.active is not None and self.active.subject_id == subject_id:
            return self.active
        return None

    def save(self, execution):
        self.active = execution

    def settle(self, provider_batch_id):
        assert self.active is not None
        assert self.active.provider_batch_id == provider_batch_id
        self.active = None


class _Coordinator:
    def __init__(self, execution_store):
        self.store = execution_store
        self.next_action = "submitted"

    def tick(self, *, subject_id, execution_id, work_keys, now):
        if self.store.active is None:
            assert self.next_action == "submitted"
            claims = tuple(
                DurableCanaryClaim(
                    work_key=key,
                    lease_token=f"lease:{index}",
                    acquired_at=now,
                    expires_at=now + timedelta(hours=26),
                    job_id=f"research:{key}",
                )
                for index, key in enumerate(work_keys)
            )
            self.store.active = DurableCanaryExecution(
                execution_id=execution_id,
                subject_id=subject_id,
                provider_batch_id="batch:1",
                claims=claims,
                submitted_at=now,
            )
            return AsyncCanaryTick("submitted", "batch:1")
        active = self.store.active
        if self.next_action == "pending":
            return AsyncCanaryTick("pending", active.provider_batch_id)
        key = active.claims[0].work_key
        self.store.active = None
        if self.next_action == "completed":
            return AsyncCanaryTick(
                "completed",
                active.provider_batch_id,
                completed_work_keys=(key,),
            )
        return AsyncCanaryTick(
            "failed",
            active.provider_batch_id,
            released_work_keys=(key,),
        )


def _scheduler_policy() -> AutonomousResearchPolicy:
    return AutonomousResearchPolicy(
        policy_id="pb11-scheduler",
        version="1",
        max_batch_size=1,
        max_attempts_per_work=3,
        base_backoff=timedelta(minutes=5),
        max_backoff=timedelta(hours=1),
        lease_for=timedelta(hours=26),
    )


def _budget_policy() -> LiveResearchBudgetPolicy:
    return LiveResearchBudgetPolicy(
        policy_id="pb11-budget",
        version="1",
        currency="USD",
        max_cost_upper_bound_microunits=300,
        per_batch_cost_upper_bound_microunits=100,
        max_batches=3,
        max_jobs=3,
    )


def _runner(tmp_path):
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intent = SharedObservationIntent(
        subject_id="org:canary",
        state_fingerprint="state:1",
        dimension_id="public_identity",
        missing_requirements=("public identity evidence",),
        research_policy_id="pb11-live-canary",
        research_policy_version="1",
        research_context_fingerprint="ctx:1",
    )
    memory.enqueue(intent, "prime:canary")
    execution_store = _ExecutionStore()
    coordinator = _Coordinator(execution_store)
    runner = GovernedAsyncResearchRunner(
        memory=memory,
        ledger=memory,
        execution_store=execution_store,
        coordinator=coordinator,  # type: ignore[arg-type]
        revalidator=CanaryResearchRevalidator(
            allowed_subject_ids=frozenset({"org:canary"}),
            research_policy_id="pb11-live-canary",
            research_policy_version="1",
        ),
        scheduler_policy=_scheduler_policy(),
        budget_store=SqliteLiveResearchBudgetStore(tmp_path / "budget.sqlite3"),
        budget_policy=_budget_policy(),
    )
    return runner, memory, intent, coordinator


def test_submit_does_not_consume_scheduler_attempt_until_terminal_result(tmp_path) -> None:
    runner, memory, intent, coordinator = _runner(tmp_path)
    submitted = runner.run(
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:1",
        allow_submit=True,
    )
    assert submitted.action == "submitted"
    assert memory.get_schedule(intent.work_key) is None

    coordinator.next_action = "completed"
    completed = runner.run(
        subject_id="org:canary",
        now=NOW + timedelta(minutes=1),
        execution_id="pb11:poll",
        allow_submit=False,
    )
    assert completed.action == "completed"
    state = memory.get_schedule(intent.work_key)
    assert state is not None
    assert state.last_outcome is ResearchScheduleOutcome.RESOLVED
    assert state.attempt_count == 1


def test_failed_provider_batch_records_backoff_only_after_terminal_failure(tmp_path) -> None:
    runner, memory, intent, coordinator = _runner(tmp_path)
    runner.run(
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:1",
        allow_submit=True,
    )
    coordinator.next_action = "failed"
    failed = runner.run(
        subject_id="org:canary",
        now=NOW + timedelta(minutes=2),
        execution_id="pb11:poll",
        allow_submit=False,
    )
    assert failed.action == "failed"
    state = memory.get_schedule(intent.work_key)
    assert state is not None
    assert state.last_outcome is ResearchScheduleOutcome.FAILED
    assert state.next_eligible_at == NOW + timedelta(minutes=7)


def test_runner_never_selects_work_for_another_canary_subject(tmp_path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    other = SharedObservationIntent(
        subject_id="org:other",
        state_fingerprint="state:other",
        dimension_id="seo",
        missing_requirements=("seo evidence",),
        research_policy_id="pb11-live-canary",
        research_policy_version="1",
        research_context_fingerprint="ctx:other",
    )
    memory.enqueue(other, "prime:other")
    execution_store = _ExecutionStore()
    coordinator = _Coordinator(execution_store)
    budget = SqliteLiveResearchBudgetStore(tmp_path / "budget.sqlite3")
    runner = GovernedAsyncResearchRunner(
        memory=memory,
        ledger=memory,
        execution_store=execution_store,
        coordinator=coordinator,  # type: ignore[arg-type]
        revalidator=CanaryResearchRevalidator(
            allowed_subject_ids=frozenset({"org:canary", "org:other"}),
            research_policy_id="pb11-live-canary",
            research_policy_version="1",
        ),
        scheduler_policy=_scheduler_policy(),
        budget_store=budget,
        budget_policy=_budget_policy(),
    )
    result = runner.run(
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:subject-scope",
        allow_submit=True,
    )
    assert result.action == "idle"
    assert execution_store.active is None
    assert budget.snapshot(currency="USD").committed_batches == 0


def test_revalidator_blocks_wrong_policy_before_budget_or_submit(tmp_path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    intent = SharedObservationIntent(
        subject_id="org:canary",
        state_fingerprint="state:1",
        dimension_id="seo",
        missing_requirements=("seo evidence",),
        research_policy_id="wrong-policy",
        research_policy_version="1",
        research_context_fingerprint="ctx:1",
    )
    memory.enqueue(intent, "prime:canary")
    execution_store = _ExecutionStore()
    coordinator = _Coordinator(execution_store)
    budget = SqliteLiveResearchBudgetStore(tmp_path / "budget.sqlite3")
    runner = GovernedAsyncResearchRunner(
        memory=memory,
        ledger=memory,
        execution_store=execution_store,
        coordinator=coordinator,  # type: ignore[arg-type]
        revalidator=CanaryResearchRevalidator(
            allowed_subject_ids=frozenset({"org:canary"}),
            research_policy_id="pb11-live-canary",
            research_policy_version="1",
        ),
        scheduler_policy=_scheduler_policy(),
        budget_store=budget,
        budget_policy=_budget_policy(),
    )
    result = runner.run(
        subject_id="org:canary",
        now=NOW,
        execution_id="pb11:blocked",
        allow_submit=True,
    )
    assert result.action == "idle"
    assert execution_store.active is None
    assert budget.snapshot(currency="USD").committed_batches == 0
