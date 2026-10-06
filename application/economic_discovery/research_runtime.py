"""PB-09 operational control plane for the governed autonomous research scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.research_scheduler import AutonomousResearchCycle


class ResearchRuntimeMode(StrEnum):
    DISABLED = "DISABLED"
    CANARY = "CANARY"
    ENABLED = "ENABLED"


class ResearchRuntimeStatus(StrEnum):
    DISABLED = "DISABLED"
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    THROTTLED = "THROTTLED"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class ResearchRuntimePolicy:
    policy_id: str
    version: str
    mode: ResearchRuntimeMode
    wake_interval: timedelta
    max_global_inflight: int
    max_subject_inflight: int
    inflight_lease_for: timedelta
    canary_subject_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("runtime policy identity is required")
        if self.wake_interval <= timedelta(0):
            raise ValueError("runtime wake interval must be positive")
        if self.max_global_inflight < 1 or self.max_subject_inflight < 1:
            raise ValueError("runtime concurrency limits must be positive")
        if self.max_subject_inflight > self.max_global_inflight:
            raise ValueError("subject concurrency cannot exceed global concurrency")
        if self.inflight_lease_for <= timedelta(0):
            raise ValueError("runtime inflight lease must be positive")
        if self.mode is ResearchRuntimeMode.CANARY and not self.canary_subject_ids:
            raise ValueError("canary runtime requires explicit subject allowlist")
        if any(not value.strip() for value in self.canary_subject_ids):
            raise ValueError("canary subject ids cannot be blank")


@dataclass(frozen=True, slots=True)
class ResearchRuntimeSnapshot:
    mode: ResearchRuntimeMode
    status: ResearchRuntimeStatus
    kill_switch: bool
    global_inflight: int
    last_started_at: datetime | None
    last_finished_at: datetime | None
    next_wake_at: datetime | None
    last_error_type: str | None
    cycles_started: int
    cycles_completed: int

    def __post_init__(self) -> None:
        for value in (self.last_started_at, self.last_finished_at, self.next_wake_at):
            if value is not None and value.tzinfo is None:
                raise ValueError("runtime snapshot times must be timezone-aware")
        if min(self.global_inflight, self.cycles_started, self.cycles_completed) < 0:
            raise ValueError("runtime counters cannot be negative")
        if self.cycles_completed > self.cycles_started:
            raise ValueError("completed cycles cannot exceed started cycles")


class ResearchRuntimeStore(Protocol):
    def snapshot(self) -> ResearchRuntimeSnapshot: ...
    def set_kill_switch(self, enabled: bool) -> None: ...
    def try_acquire(self, *, subject_id: str, now: datetime, policy: ResearchRuntimePolicy) -> bool: ...
    def finish(
        self,
        *,
        subject_id: str,
        now: datetime,
        policy: ResearchRuntimePolicy,
        error_type: str | None,
    ) -> None: ...


class ResearchCycleRunner(Protocol):
    def run(self, *, now: datetime, execution_id: str) -> AutonomousResearchCycle: ...


@dataclass(frozen=True, slots=True)
class ResearchRuntimeTick:
    ran: bool
    reason: str
    cycle: AutonomousResearchCycle | None
    snapshot: ResearchRuntimeSnapshot


def run_research_runtime_tick(
    *,
    store: ResearchRuntimeStore,
    runner: ResearchCycleRunner,
    policy: ResearchRuntimePolicy,
    subject_id: str,
    now: datetime,
    execution_id: str,
) -> ResearchRuntimeTick:
    """Execute at most one scheduler cycle behind operational gates."""

    if now.tzinfo is None:
        raise ValueError("runtime tick time must be timezone-aware")
    if not subject_id.strip() or not execution_id.strip():
        raise ValueError("runtime tick identity is required")
    before = store.snapshot()
    if before.kill_switch or policy.mode is ResearchRuntimeMode.DISABLED:
        return ResearchRuntimeTick(False, "disabled", None, before)
    if policy.mode is ResearchRuntimeMode.CANARY and subject_id not in policy.canary_subject_ids:
        return ResearchRuntimeTick(False, "outside-canary", None, before)
    if before.next_wake_at is not None and now < before.next_wake_at:
        return ResearchRuntimeTick(False, "not-due", None, before)
    if not store.try_acquire(subject_id=subject_id, now=now, policy=policy):
        return ResearchRuntimeTick(False, "concurrency-limit", None, store.snapshot())

    try:
        cycle = runner.run(now=now, execution_id=execution_id)
    except Exception as exc:
        store.finish(
            subject_id=subject_id,
            now=now,
            policy=policy,
            error_type=type(exc).__name__,
        )
        raise
    store.finish(subject_id=subject_id, now=now, policy=policy, error_type=None)
    return ResearchRuntimeTick(True, "executed", cycle, store.snapshot())
