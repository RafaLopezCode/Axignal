"""Durable shared observation-work contracts for EB-07.

This is not a generic scheduler. It persists explicit research work already
authorized by Prime/ResearchValue and deduplicates identical governed intents.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.prime import PrimeControlPlan, PrimeRoute


class ObservationWorkState(StrEnum):
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True)
class SharedObservationIntent:
    subject_id: str
    state_fingerprint: str
    dimension_id: str
    missing_requirements: tuple[str, ...]
    research_policy_id: str
    research_policy_version: str
    research_context_fingerprint: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.subject_id,
                self.state_fingerprint,
                self.dimension_id,
                self.research_policy_id,
                self.research_policy_version,
                self.research_context_fingerprint,
            )
        ):
            raise ValueError("shared observation intent identity is required")
        if not self.missing_requirements or any(
            not value.strip() for value in self.missing_requirements
        ):
            raise ValueError("shared observation intent requires explicit missing information")
        if len(set(self.missing_requirements)) != len(self.missing_requirements):
            raise ValueError("shared observation missing requirements must be unique")
        object.__setattr__(self, "missing_requirements", tuple(sorted(self.missing_requirements)))

    @property
    def work_key(self) -> str:
        payload = {
            "subject_id": self.subject_id,
            "state_fingerprint": self.state_fingerprint,
            "dimension_id": self.dimension_id,
            "missing_requirements": sorted(self.missing_requirements),
            "research_policy_id": self.research_policy_id,
            "research_policy_version": self.research_policy_version,
            "research_context_fingerprint": self.research_context_fingerprint,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "observe-work:" + hashlib.sha256(encoded.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SharedObservationWork:
    intent: SharedObservationIntent
    state: ObservationWorkState
    requester_refs: tuple[str, ...]
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.requester_refs or any(not item.strip() for item in self.requester_refs):
            raise ValueError("shared observation work requires requester provenance")
        if self.state is ObservationWorkState.COMPLETE:
            if self.completed_at is None or self.completed_at.tzinfo is None:
                raise ValueError("completed observation work requires timezone-aware completion")
        elif self.completed_at is not None:
            raise ValueError("pending observation work cannot carry completion time")


@dataclass(frozen=True, slots=True)
class ObservationWorkLease:
    work_key: str
    lease_token: str
    acquired_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.work_key.strip() or not self.lease_token.strip():
            raise ValueError("observation work lease identity is required")
        if self.acquired_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("observation work lease time must be timezone-aware")
        if self.expires_at <= self.acquired_at:
            raise ValueError("observation work lease must expire after acquisition")


class SharedObservationWorkMemory(Protocol):
    def enqueue(self, intent: SharedObservationIntent, requester_ref: str) -> bool:
        """Return True only when a new shared work row is created."""

    def get(self, work_key: str) -> SharedObservationWork | None: ...

    def pending_work_keys(self) -> tuple[str, ...]:
        """Return pending work in deterministic durable order."""

    def claim(
        self,
        work_key: str,
        *,
        now: datetime,
        lease_for: timedelta,
    ) -> ObservationWorkLease | None: ...

    def complete(
        self,
        work_key: str,
        lease_token: str,
        *,
        completed_at: datetime,
    ) -> bool:
        """Complete only if the caller still owns the live lease."""

    def release(self, work_key: str, lease_token: str) -> bool: ...


def intents_from_prime_plan(plan: PrimeControlPlan) -> tuple[SharedObservationIntent, ...]:
    """Convert only ResearchValue-authorized adaptive work into durable intents."""

    intents: list[SharedObservationIntent] = []
    for item in plan.items:
        if item.route is not PrimeRoute.ADAPTIVE_RESEARCH:
            continue
        if any(
            value is None
            for value in (
                item.research_policy_id,
                item.research_policy_version,
                item.research_context_fingerprint,
            )
        ):
            raise ValueError("adaptive research work lacks governed research provenance")
        intents.append(
            SharedObservationIntent(
                subject_id=plan.subject_id,
                state_fingerprint=plan.state_fingerprint,
                dimension_id=item.dimension_id,
                missing_requirements=item.missing_requirements,
                research_policy_id=str(item.research_policy_id),
                research_policy_version=str(item.research_policy_version),
                research_context_fingerprint=str(item.research_context_fingerprint),
            )
        )
    return tuple(intents)


def schedule_prime_research(
    memory: SharedObservationWorkMemory,
    *,
    plan: PrimeControlPlan,
    requester_ref: str,
) -> tuple[SharedObservationIntent, ...]:
    """Persist authorized research once while retaining every attention requester."""

    if not requester_ref.strip():
        raise ValueError("shared observation requester ref is required")
    intents = intents_from_prime_plan(plan)
    for intent in intents:
        memory.enqueue(intent, requester_ref)
    return intents
