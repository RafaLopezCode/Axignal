"""Bounded claiming of durable research work for provider batch execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from application.economic_discovery.continuous_observation import (
    ObservationWorkLease,
    SharedObservationWork,
    SharedObservationWorkMemory,
)


@dataclass(frozen=True, slots=True)
class ClaimedResearchWork:
    """Durable work paired with the lease fencing its execution."""

    work: SharedObservationWork
    lease: ObservationWorkLease


def claim_research_batch(
    memory: SharedObservationWorkMemory,
    *,
    work_keys: tuple[str, ...],
    now: datetime,
    lease_for: timedelta,
    max_batch_size: int,
) -> tuple[ClaimedResearchWork, ...]:
    """Claim bounded, already-authorized work without creating successor work."""

    if now.tzinfo is None:
        raise ValueError("research batch claim time must be timezone-aware")
    if lease_for <= timedelta(0):
        raise ValueError("research batch lease duration must be positive")
    if max_batch_size < 1:
        raise ValueError("research batch size must be positive")
    if any(not key.strip() for key in work_keys):
        raise ValueError("research batch work keys cannot be blank")
    if len(set(work_keys)) != len(work_keys):
        raise ValueError("research batch work keys must be unique")

    claimed: list[ClaimedResearchWork] = []
    for work_key in work_keys:
        if len(claimed) >= max_batch_size:
            break
        work = memory.get(work_key)
        if work is None:
            continue
        lease = memory.claim(work_key, now=now, lease_for=lease_for)
        if lease is not None:
            claimed.append(ClaimedResearchWork(work=work, lease=lease))
    return tuple(claimed)


def complete_research_batch(
    memory: SharedObservationWorkMemory,
    *,
    claimed: tuple[ClaimedResearchWork, ...],
    completed_at: datetime,
    on_subject_changed: Callable[[str, datetime], object] | None = None,
) -> tuple[str, ...]:
    """Complete only work whose lease is still owned by this batch.

    ``on_subject_changed`` runs once per subject whose work this batch really completed
    (TASK-050 T022): dependents re-evaluate their declared dependencies. A fenced-out
    completion (stale lease, late or duplicate result) never triggers it.
    """

    if completed_at.tzinfo is None:
        raise ValueError("research batch completion time must be timezone-aware")
    completed: list[str] = []
    for item in claimed:
        if memory.complete(
            item.lease.work_key,
            item.lease.lease_token,
            completed_at=completed_at,
        ):
            completed.append(item.lease.work_key)
    if on_subject_changed is not None:
        subjects = {
            item.work.intent.subject_id for item in claimed if item.lease.work_key in completed
        }
        for subject_id in sorted(subjects):
            on_subject_changed(subject_id, completed_at)
    return tuple(completed)


def release_research_batch(
    memory: SharedObservationWorkMemory,
    *,
    claimed: tuple[ClaimedResearchWork, ...],
) -> tuple[str, ...]:
    """Release owned leases; never enqueue retries or successor work."""

    released: list[str] = []
    for item in claimed:
        if memory.release(item.lease.work_key, item.lease.lease_token):
            released.append(item.lease.work_key)
    return tuple(released)
