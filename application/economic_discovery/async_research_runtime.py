"""Governed asynchronous live-research runtime contracts for PB-11."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from application.economic_discovery.research_runtime import (
    ResearchRuntimeMode,
    ResearchRuntimePolicy,
    ResearchRuntimeSnapshot,
    ResearchRuntimeStore,
)


@dataclass(frozen=True, slots=True)
class LiveResearchBudgetPolicy:
    policy_id: str
    version: str
    currency: str
    max_cost_upper_bound_microunits: int
    per_batch_cost_upper_bound_microunits: int
    max_batches: int
    max_jobs: int
    reservation_lease_for: timedelta = timedelta(minutes=30)

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("live research budget identity is required")
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("live research budget currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        limits = (
            self.max_cost_upper_bound_microunits,
            self.per_batch_cost_upper_bound_microunits,
            self.max_batches,
            self.max_jobs,
        )
        if any(value < 1 for value in limits):
            raise ValueError("live research budget limits must be positive")
        if self.per_batch_cost_upper_bound_microunits > self.max_cost_upper_bound_microunits:
            raise ValueError("per-batch cost ceiling cannot exceed total cost ceiling")
        if self.reservation_lease_for <= timedelta(0):
            raise ValueError("live research budget reservation lease must be positive")


@dataclass(frozen=True, slots=True)
class LiveResearchBudgetSnapshot:
    currency: str
    committed_cost_upper_bound_microunits: int
    reserved_cost_upper_bound_microunits: int
    committed_batches: int
    reserved_batches: int
    committed_jobs: int
    reserved_jobs: int

    @property
    def total_cost_upper_bound_microunits(self) -> int:
        return (
            self.committed_cost_upper_bound_microunits + self.reserved_cost_upper_bound_microunits
        )


class LiveResearchBudgetStore(Protocol):
    def snapshot(self, *, currency: str) -> LiveResearchBudgetSnapshot: ...

    def try_reserve(
        self,
        *,
        execution_id: str,
        job_count: int,
        now: datetime,
        policy: LiveResearchBudgetPolicy,
    ) -> bool: ...

    def commit(self, execution_id: str) -> None: ...

    def release(self, execution_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class AsyncResearchRuntimeCycle:
    action: str
    selected_work_keys: tuple[str, ...] = ()
    completed_work_keys: tuple[str, ...] = ()
    released_work_keys: tuple[str, ...] = ()
    exhausted_work_keys: tuple[str, ...] = ()
    provider_batch_id: str | None = None
    budget_blocked: bool = False

    @property
    def keeps_runtime_lease(self) -> bool:
        return self.action in {"submitted", "pending"}


class AsyncResearchCycleRunner(Protocol):
    def has_active(self, subject_id: str) -> bool: ...

    def run(
        self,
        *,
        subject_id: str,
        now: datetime,
        execution_id: str,
        allow_submit: bool,
    ) -> AsyncResearchRuntimeCycle: ...


@dataclass(frozen=True, slots=True)
class AsyncResearchRuntimeTick:
    ran: bool
    reason: str
    cycle: AsyncResearchRuntimeCycle | None
    snapshot: ResearchRuntimeSnapshot


def run_async_research_runtime_tick(
    *,
    store: ResearchRuntimeStore,
    runner: AsyncResearchCycleRunner,
    policy: ResearchRuntimePolicy,
    subject_id: str,
    now: datetime,
    execution_id: str,
) -> AsyncResearchRuntimeTick:
    """Run one async tick while retaining runtime capacity across provider batches."""

    if now.tzinfo is None:
        raise ValueError("async runtime tick time must be timezone-aware")
    if not subject_id.strip() or not execution_id.strip():
        raise ValueError("async runtime tick identity is required")

    active = runner.has_active(subject_id)
    before = store.snapshot()

    # Existing external work must remain collectable even after the kill switch is raised.
    if active:
        # Poll/collection failures are retryable operational uncertainty. Keep the
        # capacity lease while the external batch remains active.
        cycle = runner.run(
            subject_id=subject_id,
            now=now,
            execution_id=execution_id,
            allow_submit=False,
        )
        if not cycle.keeps_runtime_lease:
            store.finish(
                subject_id=subject_id,
                now=now,
                policy=policy,
                error_type=None if cycle.action != "failed" else "ProviderBatchFailed",
            )
        return AsyncResearchRuntimeTick(True, cycle.action, cycle, store.snapshot())

    if before.kill_switch or policy.mode is ResearchRuntimeMode.DISABLED:
        return AsyncResearchRuntimeTick(False, "disabled", None, before)
    if policy.mode is ResearchRuntimeMode.CANARY and subject_id not in policy.canary_subject_ids:
        return AsyncResearchRuntimeTick(False, "outside-canary", None, before)
    if before.next_wake_at is not None and now < before.next_wake_at:
        return AsyncResearchRuntimeTick(False, "not-due", None, before)
    if not store.try_acquire(subject_id=subject_id, now=now, policy=policy):
        return AsyncResearchRuntimeTick(False, "concurrency-limit", None, store.snapshot())

    try:
        cycle = runner.run(
            subject_id=subject_id,
            now=now,
            execution_id=execution_id,
            allow_submit=True,
        )
    except Exception as exc:
        store.finish(
            subject_id=subject_id,
            now=now,
            policy=policy,
            error_type=type(exc).__name__,
        )
        raise

    if not cycle.keeps_runtime_lease:
        store.finish(
            subject_id=subject_id,
            now=now,
            policy=policy,
            error_type=None,
        )
    return AsyncResearchRuntimeTick(True, cycle.action, cycle, store.snapshot())
