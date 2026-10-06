"""PB-07 governed runtime for previously authorized adaptive research batches."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from application.economic_discovery.batch_research import (
    ClaimedResearchWork,
    claim_research_batch,
    complete_research_batch,
    release_research_batch,
)
from application.economic_discovery.continuous_observation import SharedObservationWorkMemory
from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    ExecutionBudgetReservation,
    GovernedExecutionController,
)


@dataclass(frozen=True, slots=True)
class ResearchBatchItemResult:
    """Provider-neutral outcome for one leased research objective."""

    work_key: str
    output_fingerprint: str
    objective_resolved: bool
    provider: str | None = None
    provider_version: str | None = None

    def __post_init__(self) -> None:
        if not self.work_key.strip() or not self.output_fingerprint.strip():
            raise ValueError("research batch result requires work and output identity")
        if (self.provider is None) != (self.provider_version is None):
            raise ValueError("research provider and version must coexist")


class ResearchBatchExecutionFailed(RuntimeError):
    """Execution failed after leases were acquired; exposes exact attempted work."""

    def __init__(self, claimed_work_keys: tuple[str, ...]) -> None:
        self.claimed_work_keys = claimed_work_keys
        super().__init__("governed research batch execution failed")


class ResearchBatchExecutor(Protocol):
    """Execute research and report resolution only after governed admission."""

    def execute_batch(
        self,
        claimed: tuple[ClaimedResearchWork, ...],
    ) -> tuple[ResearchBatchItemResult, ...]: ...


@dataclass(frozen=True, slots=True)
class ResearchBatchExecutionTrace:
    reservation_id: str | None
    claimed_work_keys: tuple[str, ...]
    completed_work_keys: tuple[str, ...]
    released_work_keys: tuple[str, ...]
    made_progress: bool
    elapsed_ms: int


def execute_governed_research_batch(
    *,
    memory: SharedObservationWorkMemory,
    execution_controller: GovernedExecutionController,
    executor: ResearchBatchExecutor,
    work_keys: tuple[str, ...],
    now: datetime,
    lease_for: timedelta,
    max_batch_size: int,
    execution_id: str,
) -> ResearchBatchExecutionTrace:
    """Claim, budget, execute and settle one non-recursive research batch."""

    if not execution_id.strip():
        raise ValueError("research batch execution identity is required")
    claimed = claim_research_batch(
        memory,
        work_keys=work_keys,
        now=now,
        lease_for=lease_for,
        max_batch_size=max_batch_size,
    )
    if not claimed:
        return ResearchBatchExecutionTrace(None, (), (), (), False, 0)

    claimed_keys = tuple(item.lease.work_key for item in claimed)
    reservation_id = f"reserve:{execution_id}:research-batch"
    try:
        execution_controller.reserve(
            ExecutionBudgetReservation(
                reservation_id=reservation_id,
                requests=len(claimed),
                loops=1,
            )
        )
    except Exception:
        release_research_batch(memory, claimed=claimed)
        raise

    started_ns = time.monotonic_ns()
    try:
        results = tuple(executor.execute_batch(claimed))
        elapsed_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        result_keys = tuple(result.work_key for result in results)
        if len(set(result_keys)) != len(result_keys) or set(result_keys) != set(claimed_keys):
            raise ValueError("research batch result population does not match claimed work")
        resolved_by_key = {result.work_key: result.objective_resolved for result in results}
        progressed = tuple(item for item in claimed if resolved_by_key[item.lease.work_key])
        deferred = tuple(item for item in claimed if not resolved_by_key[item.lease.work_key])
        completed = complete_research_batch(memory, claimed=progressed, completed_at=now)
        released = release_research_batch(memory, claimed=deferred)
        made_progress = bool(completed)
        execution_controller.reconcile(
            reservation_id,
            ExecutionBudgetDelta(
                elapsed_ms=elapsed_ms,
                requests=len(claimed),
                loops=1,
                made_progress=made_progress,
            ),
        )
        return ResearchBatchExecutionTrace(
            reservation_id,
            claimed_keys,
            completed,
            released,
            made_progress,
            elapsed_ms,
        )
    except Exception:
        elapsed_ms = max(0, (time.monotonic_ns() - started_ns) // 1_000_000)
        release_research_batch(memory, claimed=claimed)
        execution_controller.reconcile(
            reservation_id,
            ExecutionBudgetDelta(
                elapsed_ms=elapsed_ms,
                requests=len(claimed),
                loops=1,
                made_progress=False,
            ),
        )
        raise ResearchBatchExecutionFailed(claimed_keys) from None
