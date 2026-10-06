"""PB-08 autonomous, bounded scheduler for already-authorized research work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.batch_research_runtime import (
    ResearchBatchExecutionFailed,
    ResearchBatchExecutionTrace,
    ResearchBatchExecutor,
    execute_governed_research_batch,
)
from application.economic_discovery.continuous_observation import (
    SharedObservationWork,
    SharedObservationWorkMemory,
)
from application.economic_discovery.execution_budget import (
    ExecutionStopReason,
    GovernedExecutionController,
)


class ResearchScheduleOutcome(StrEnum):
    RESOLVED = "RESOLVED"
    NO_PROGRESS = "NO_PROGRESS"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ResearchScheduleState:
    work_key: str
    attempt_count: int
    no_progress_count: int
    next_eligible_at: datetime
    last_outcome: ResearchScheduleOutcome
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.work_key.strip():
            raise ValueError("scheduler state requires work identity")
        if self.attempt_count < 1 or self.no_progress_count < 0:
            raise ValueError("scheduler counters are invalid")
        if self.no_progress_count > self.attempt_count:
            raise ValueError("no-progress count cannot exceed attempts")
        if self.next_eligible_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("scheduler state times must be timezone-aware")


class ResearchWorkRevalidator(Protocol):
    """Revalidate durable authorization/currentness immediately before dispatch."""

    def may_run(self, work: SharedObservationWork, *, now: datetime) -> bool: ...


class ResearchScheduleLedger(Protocol):
    def get_schedule(self, work_key: str) -> ResearchScheduleState | None: ...

    def record_schedule(self, state: ResearchScheduleState) -> None: ...


@dataclass(frozen=True, slots=True)
class AutonomousResearchPolicy:
    policy_id: str
    version: str
    max_batch_size: int
    max_attempts_per_work: int
    base_backoff: timedelta
    max_backoff: timedelta
    lease_for: timedelta

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("scheduler policy identity is required")
        if self.max_batch_size < 1 or self.max_attempts_per_work < 1:
            raise ValueError("scheduler limits must be positive")
        if self.base_backoff <= timedelta(0) or self.max_backoff < self.base_backoff:
            raise ValueError("scheduler backoff bounds are invalid")
        if self.lease_for <= timedelta(0):
            raise ValueError("scheduler lease duration must be positive")


@dataclass(frozen=True, slots=True)
class AutonomousResearchCycle:
    selected_work_keys: tuple[str, ...]
    execution: ResearchBatchExecutionTrace | None
    stop_reason: ExecutionStopReason | None
    exhausted_work_keys: tuple[str, ...] = ()


def _backoff(policy: AutonomousResearchPolicy, no_progress_count: int) -> timedelta:
    multiplier = 2 ** max(0, no_progress_count - 1)
    candidate = policy.base_backoff * multiplier
    return candidate if candidate <= policy.max_backoff else policy.max_backoff


def select_research_work_keys(
    *,
    memory: SharedObservationWorkMemory,
    ledger: ResearchScheduleLedger,
    policy: AutonomousResearchPolicy,
    revalidator: ResearchWorkRevalidator,
    now: datetime,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Select durable work without claiming or dispatching it."""

    eligible: list[str] = []
    exhausted: list[str] = []
    for work_key in memory.pending_work_keys():
        work = memory.get(work_key)
        if work is None or not revalidator.may_run(work, now=now):
            continue
        state = ledger.get_schedule(work_key)
        if state is None:
            eligible.append(work_key)
        elif state.attempt_count >= policy.max_attempts_per_work:
            exhausted.append(work_key)
        elif state.next_eligible_at <= now:
            eligible.append(work_key)
    return tuple(eligible[: policy.max_batch_size]), tuple(exhausted)


def record_research_schedule_outcome(
    ledger: ResearchScheduleLedger,
    *,
    work_key: str,
    outcome: ResearchScheduleOutcome,
    now: datetime,
    policy: AutonomousResearchPolicy,
) -> None:
    """Persist one terminal scheduler outcome for durable research work."""
    prior = ledger.get_schedule(work_key)
    attempts = 1 if prior is None else prior.attempt_count + 1
    no_progress = (
        0
        if outcome is ResearchScheduleOutcome.RESOLVED
        else (1 if prior is None else prior.no_progress_count + 1)
    )
    next_eligible = (
        now if outcome is ResearchScheduleOutcome.RESOLVED else now + _backoff(policy, no_progress)
    )
    ledger.record_schedule(
        ResearchScheduleState(
            work_key=work_key,
            attempt_count=attempts,
            no_progress_count=no_progress,
            next_eligible_at=next_eligible,
            last_outcome=outcome,
            updated_at=now,
        )
    )


def run_autonomous_research_cycle(
    *,
    memory: SharedObservationWorkMemory,
    ledger: ResearchScheduleLedger,
    execution_controller: GovernedExecutionController,
    executor: ResearchBatchExecutor,
    revalidator: ResearchWorkRevalidator,
    policy: AutonomousResearchPolicy,
    now: datetime,
    execution_id: str,
) -> AutonomousResearchCycle:
    """Run at most one governed batch; never recursively schedule another cycle."""

    if now.tzinfo is None:
        raise ValueError("scheduler cycle time must be timezone-aware")
    if not execution_id.strip():
        raise ValueError("scheduler execution identity is required")

    budget = execution_controller.authorize_next()
    if not budget.may_continue:
        return AutonomousResearchCycle((), None, budget.stop_reason)

    selected, exhausted = select_research_work_keys(
        memory=memory,
        ledger=ledger,
        policy=policy,
        revalidator=revalidator,
        now=now,
    )
    if not selected:
        return AutonomousResearchCycle((), None, None, exhausted)

    try:
        trace = execute_governed_research_batch(
            memory=memory,
            execution_controller=execution_controller,
            executor=executor,
            work_keys=selected,
            now=now,
            lease_for=policy.lease_for,
            max_batch_size=policy.max_batch_size,
            execution_id=execution_id,
        )
    except ResearchBatchExecutionFailed as exc:
        for work_key in exc.claimed_work_keys:
            record_research_schedule_outcome(
                ledger,
                work_key=work_key,
                outcome=ResearchScheduleOutcome.FAILED,
                now=now,
                policy=policy,
            )
        raise

    completed = set(trace.completed_work_keys)
    claimed = set(trace.claimed_work_keys)
    for work_key in selected:
        if work_key not in claimed:
            continue
        record_research_schedule_outcome(
            ledger,
            work_key=work_key,
            outcome=(
                ResearchScheduleOutcome.RESOLVED
                if work_key in completed
                else ResearchScheduleOutcome.NO_PROGRESS
            ),
            now=now,
            policy=policy,
        )
    return AutonomousResearchCycle(selected, trace, None, exhausted)
