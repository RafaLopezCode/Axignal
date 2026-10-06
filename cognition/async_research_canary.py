"""PB-10 asynchronous governed bridge from durable research work to Batch API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from application.economic_discovery.batch_research import (
    ClaimedResearchWork,
    claim_research_batch,
    complete_research_batch,
    release_research_batch,
)
from application.economic_discovery.continuous_observation import (
    ObservationWorkLease,
    SharedObservationWorkMemory,
)
from cognition.providers.openai_batch import BatchState, DurableBatchTransport
from cognition.research_batch_adapter import ResearchResultAdmissionPort, build_research_job


@dataclass(frozen=True, slots=True)
class DurableCanaryClaim:
    work_key: str
    lease_token: str
    acquired_at: datetime
    expires_at: datetime
    job_id: str


@dataclass(frozen=True, slots=True)
class DurableCanaryExecution:
    execution_id: str
    subject_id: str
    provider_batch_id: str
    claims: tuple[DurableCanaryClaim, ...]
    submitted_at: datetime


class DurableCanaryExecutionStore(Protocol):
    def active_for_subject(self, subject_id: str) -> DurableCanaryExecution | None: ...
    def save(self, execution: DurableCanaryExecution) -> None: ...
    def settle(self, provider_batch_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class AsyncCanaryTick:
    action: str
    provider_batch_id: str | None = None
    completed_work_keys: tuple[str, ...] = ()
    released_work_keys: tuple[str, ...] = ()


class AsyncGovernedCanaryCoordinator:
    """Submit or collect one durable batch while preserving observation-work fencing."""

    def __init__(
        self,
        *,
        memory: SharedObservationWorkMemory,
        store: DurableCanaryExecutionStore,
        transport: DurableBatchTransport,
        admission: ResearchResultAdmissionPort,
        authorized_model: str,
        lease_for: timedelta = timedelta(hours=26),
        max_batch_size: int = 8,
    ) -> None:
        if lease_for <= timedelta(hours=24):
            raise ValueError("async canary lease must exceed provider completion window")
        if max_batch_size < 1:
            raise ValueError("async canary batch size must be positive")
        self._memory = memory
        self._store = store
        self._transport = transport
        self._admission = admission
        self._model = authorized_model
        self._lease_for = lease_for
        self._max_batch_size = max_batch_size

    def tick(
        self,
        *,
        subject_id: str,
        execution_id: str,
        work_keys: tuple[str, ...],
        now: datetime,
    ) -> AsyncCanaryTick:
        active = self._store.active_for_subject(subject_id)
        if active is not None:
            return self._collect(active=active, now=now)
        claimed = claim_research_batch(
            self._memory,
            work_keys=work_keys,
            now=now,
            lease_for=self._lease_for,
            max_batch_size=self._max_batch_size,
        )
        if not claimed:
            return AsyncCanaryTick("idle")
        jobs = tuple(build_research_job(item) for item in claimed)
        try:
            receipt = self._transport.submit(model=self._model, jobs=jobs)
        except Exception:
            release_research_batch(self._memory, claimed=claimed)
            raise
        execution = DurableCanaryExecution(
            execution_id=execution_id,
            subject_id=subject_id,
            provider_batch_id=receipt.batch_id,
            claims=tuple(
                DurableCanaryClaim(
                    work_key=item.lease.work_key,
                    lease_token=item.lease.lease_token,
                    acquired_at=item.lease.acquired_at,
                    expires_at=item.lease.expires_at,
                    job_id=job.id,
                )
                for item, job in zip(claimed, jobs, strict=True)
            ),
            submitted_at=now,
        )
        self._store.save(execution)
        return AsyncCanaryTick("submitted", receipt.batch_id)

    def _collect(self, *, active: DurableCanaryExecution, now: datetime) -> AsyncCanaryTick:
        poll = self._transport.poll(active.provider_batch_id)
        if poll.state in {BatchState.SUBMITTED, BatchState.PENDING}:
            return AsyncCanaryTick("pending", active.provider_batch_id)
        claimed = self._rehydrate(active)
        if poll.state is BatchState.FAILED:
            released = release_research_batch(self._memory, claimed=claimed)
            self._store.settle(active.provider_batch_id)
            return AsyncCanaryTick("failed", active.provider_batch_id, released_work_keys=released)

        expected = {item.job_id for item in active.claims}
        result_ids = tuple(result.job_id for result in poll.results)
        if len(result_ids) != len(set(result_ids)) or set(result_ids) != expected:
            raise ValueError("provider batch results do not match durable canary claims")
        by_job = {result.job_id: result for result in poll.results}
        resolved = tuple(
            item
            for item, claim in zip(claimed, active.claims, strict=True)
            if self._admission.admit(work=item, result=by_job[claim.job_id])
        )
        unresolved = tuple(item for item in claimed if item not in resolved)
        completed = complete_research_batch(self._memory, claimed=resolved, completed_at=now)
        released = release_research_batch(self._memory, claimed=unresolved)
        self._store.settle(active.provider_batch_id)
        return AsyncCanaryTick("completed", active.provider_batch_id, completed, released)

    def _rehydrate(self, active: DurableCanaryExecution) -> tuple[ClaimedResearchWork, ...]:
        items = []
        for claim in active.claims:
            work = self._memory.get(claim.work_key)
            if work is None:
                raise ValueError("durable canary work disappeared")
            items.append(
                ClaimedResearchWork(
                    work,
                    ObservationWorkLease(
                        claim.work_key,
                        claim.lease_token,
                        claim.acquired_at,
                        claim.expires_at,
                    ),
                )
            )
        return tuple(items)
