"""PB-11 live async research runner composed from existing governed parts."""

from __future__ import annotations

from datetime import datetime

from application.economic_discovery.async_research_runtime import (
    AsyncResearchRuntimeCycle,
    LiveResearchBudgetPolicy,
    LiveResearchBudgetStore,
)
from application.economic_discovery.continuous_observation import (
    ObservationWorkState,
    SharedObservationWork,
    SharedObservationWorkMemory,
)
from application.economic_discovery.research_scheduler import (
    AutonomousResearchPolicy,
    ResearchScheduleLedger,
    ResearchScheduleOutcome,
    ResearchWorkRevalidator,
    record_research_schedule_outcome,
    select_research_work_keys,
)
from cognition.async_research_canary import (
    AsyncGovernedCanaryCoordinator,
    DurableCanaryExecutionStore,
)


class CanaryResearchRevalidator:
    """Narrow fail-closed revalidation for explicit live-canary subjects/policies."""

    def __init__(
        self,
        *,
        allowed_subject_ids: frozenset[str],
        research_policy_id: str,
        research_policy_version: str,
    ) -> None:
        if not allowed_subject_ids or any(not item.strip() for item in allowed_subject_ids):
            raise ValueError("canary revalidator requires explicit subjects")
        if not research_policy_id.strip() or not research_policy_version.strip():
            raise ValueError("canary revalidator requires policy identity")
        self._subjects = allowed_subject_ids
        self._policy_id = research_policy_id
        self._policy_version = research_policy_version

    def may_run(self, work: SharedObservationWork, *, now: datetime) -> bool:
        del now
        intent = work.intent
        return (
            work.state is ObservationWorkState.PENDING
            and intent.subject_id in self._subjects
            and intent.research_policy_id == self._policy_id
            and intent.research_policy_version == self._policy_version
        )


class GovernedAsyncResearchRunner:
    """Apply scheduler + persistent budget around the PB-10 durable coordinator."""

    def __init__(
        self,
        *,
        memory: SharedObservationWorkMemory,
        ledger: ResearchScheduleLedger,
        execution_store: DurableCanaryExecutionStore,
        coordinator: AsyncGovernedCanaryCoordinator,
        revalidator: ResearchWorkRevalidator,
        scheduler_policy: AutonomousResearchPolicy,
        budget_store: LiveResearchBudgetStore,
        budget_policy: LiveResearchBudgetPolicy,
    ) -> None:
        self._memory = memory
        self._ledger = ledger
        self._execution_store = execution_store
        self._coordinator = coordinator
        self._revalidator = revalidator
        self._scheduler_policy = scheduler_policy
        self._budget_store = budget_store
        self._budget_policy = budget_policy

    def has_active(self, subject_id: str) -> bool:
        return self._execution_store.active_for_subject(subject_id) is not None

    def run(
        self,
        *,
        subject_id: str,
        now: datetime,
        execution_id: str,
        allow_submit: bool,
    ) -> AsyncResearchRuntimeCycle:
        active = self._execution_store.active_for_subject(subject_id)
        if active is not None:
            # Crash-safe: a reservation made just before provider submission is
            # finalized as soon as the durable provider batch is visible.
            self._budget_store.commit(active.execution_id)
            tick = self._coordinator.tick(
                subject_id=subject_id,
                execution_id=execution_id,
                work_keys=(),
                now=now,
            )
            selected = tuple(item.work_key for item in active.claims)
            if tick.action == "completed":
                completed = set(tick.completed_work_keys)
                released = set(tick.released_work_keys)
                for work_key in selected:
                    if work_key in completed:
                        outcome = ResearchScheduleOutcome.RESOLVED
                    elif work_key in released:
                        outcome = ResearchScheduleOutcome.NO_PROGRESS
                    else:
                        continue
                    record_research_schedule_outcome(
                        self._ledger,
                        work_key=work_key,
                        outcome=outcome,
                        now=now,
                        policy=self._scheduler_policy,
                    )
            elif tick.action == "failed":
                for work_key in tick.released_work_keys:
                    record_research_schedule_outcome(
                        self._ledger,
                        work_key=work_key,
                        outcome=ResearchScheduleOutcome.FAILED,
                        now=now,
                        policy=self._scheduler_policy,
                    )
            return AsyncResearchRuntimeCycle(
                action=tick.action,
                selected_work_keys=selected,
                completed_work_keys=tick.completed_work_keys,
                released_work_keys=tick.released_work_keys,
                provider_batch_id=tick.provider_batch_id,
            )

        if not allow_submit:
            return AsyncResearchRuntimeCycle(action="submit-blocked")

        selected, exhausted = select_research_work_keys(
            memory=self._memory,
            ledger=self._ledger,
            policy=self._scheduler_policy,
            revalidator=self._revalidator,
            now=now,
        )
        selected = tuple(
            work_key
            for work_key in selected
            if (work := self._memory.get(work_key)) is not None
            and work.intent.subject_id == subject_id
        )
        exhausted = tuple(
            work_key
            for work_key in exhausted
            if (work := self._memory.get(work_key)) is not None
            and work.intent.subject_id == subject_id
        )
        if not selected:
            return AsyncResearchRuntimeCycle(
                action="idle",
                exhausted_work_keys=exhausted,
            )

        reserved = self._budget_store.try_reserve(
            execution_id=execution_id,
            job_count=len(selected),
            now=now,
            policy=self._budget_policy,
        )
        if not reserved:
            return AsyncResearchRuntimeCycle(
                action="budget-stopped",
                selected_work_keys=selected,
                exhausted_work_keys=exhausted,
                budget_blocked=True,
            )

        try:
            tick = self._coordinator.tick(
                subject_id=subject_id,
                execution_id=execution_id,
                work_keys=selected,
                now=now,
            )
        except Exception:
            self._budget_store.release(execution_id)
            raise

        if tick.action == "submitted":
            self._budget_store.commit(execution_id)
        else:
            self._budget_store.release(execution_id)

        return AsyncResearchRuntimeCycle(
            action=tick.action,
            selected_work_keys=selected,
            completed_work_keys=tick.completed_work_keys,
            released_work_keys=tick.released_work_keys,
            exhausted_work_keys=exhausted,
            provider_batch_id=tick.provider_batch_id,
        )
