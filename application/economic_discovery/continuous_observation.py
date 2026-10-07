"""Durable shared observation-work contracts for EB-07.

This is not a generic scheduler. It persists explicit research work already
authorized by Prime/ResearchValue and deduplicates identical governed intents.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
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


_PRIVATE_REF = ("focus_", "tenant:", "principal:", "pending_", "mcpgrant_", "membership:")


def opaque_requester_ref(scope: str, *private_parts: str) -> str:
    """Requester provenance for shared work without exposing private identifiers.

    Shared work is global; who asked for it is private. The ref lets a requester find
    its own row again (same inputs, same ref) while revealing no Tenant or Focus id.
    """
    if not scope.strip() or not private_parts or any(not part.strip() for part in private_parts):
        raise ValueError("opaque requester ref requires a scope and private parts")
    digest = hashlib.sha256("|".join(private_parts).encode("utf-8")).hexdigest()[:32]
    return f"{scope}:{digest}"


def require_shareable_requester_ref(requester_ref: str) -> str:
    """Refuse raw subscriber identifiers in the shared-work requester ledger."""
    if not requester_ref.strip():
        raise ValueError("shared observation requester ref is required")
    if requester_ref.lower().startswith(_PRIVATE_REF):
        raise ValueError("shared work requester ref must not carry a private identifier")
    return requester_ref


@dataclass(frozen=True, slots=True)
class PrimeResearchAuthority:
    subject_id: str
    state_fingerprint: str
    authorized_work_keys: frozenset[str]
    observation_watermark_at: datetime
    observation_watermark_id: str
    valid_until: datetime
    temporal_policy_id: str
    temporal_policy_version: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.subject_id,
                self.state_fingerprint,
                self.observation_watermark_id,
                self.temporal_policy_id,
                self.temporal_policy_version,
            )
        ):
            raise ValueError("Prime research authority identity is required")
        if self.observation_watermark_at.tzinfo is None or self.valid_until.tzinfo is None:
            raise ValueError("Prime research authority times must be timezone-aware")
        if self.valid_until <= self.observation_watermark_at:
            raise ValueError("Prime research authority must expire after its observation watermark")
        if any(not key.strip() for key in self.authorized_work_keys):
            raise ValueError("Prime research authority work keys cannot be blank")


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
    def replace_prime_authority(self, authority: PrimeResearchAuthority) -> None:
        """Replace the current Prime research authority snapshot for one subject."""

    def prime_authority(self, subject_id: str) -> PrimeResearchAuthority | None:
        """Return the latest Prime research authority snapshot for one subject."""

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
    observation_watermark_at: datetime,
    observation_watermark_id: str,
    valid_until: datetime,
    temporal_policy_id: str,
    temporal_policy_version: str,
) -> tuple[SharedObservationIntent, ...]:
    """Persist authorized research and replace the subject's temporal Prime authority."""

    if not requester_ref.strip():
        raise ValueError("shared observation requester ref is required")
    intents = intents_from_prime_plan(plan)
    memory.replace_prime_authority(
        PrimeResearchAuthority(
            subject_id=plan.subject_id,
            state_fingerprint=plan.state_fingerprint,
            authorized_work_keys=frozenset(intent.work_key for intent in intents),
            observation_watermark_at=observation_watermark_at,
            observation_watermark_id=observation_watermark_id,
            valid_until=valid_until,
            temporal_policy_id=temporal_policy_id,
            temporal_policy_version=temporal_policy_version,
        )
    )
    for intent in intents:
        memory.enqueue(intent, requester_ref)
    return intents


def refresh_prime_research_authority(
    memory: SharedObservationWorkMemory,
    *,
    subject_id: str,
    prior_observation_ids: frozenset[str],
    observation_watermark_at: datetime,
    observation_watermark_id: str,
    valid_until: datetime,
    temporal_policy_id: str,
    temporal_policy_version: str,
) -> bool:
    """Advance a temporal refresh into the existing authority without new work.

    A refresh re-confirms identical content, so the already-authorized work stays
    the same work: no new keys are minted and nothing is re-enqueued. Only the
    observation watermark and expiry move forward, which keeps that work runnable
    under revalidation. The authority must have been advanced from the very state
    being refreshed (lineage via its watermark); any mismatch leaves it untouched.
    """

    current = memory.prime_authority(subject_id)
    if (
        current is None
        or current.observation_watermark_id not in prior_observation_ids
        or current.temporal_policy_id != temporal_policy_id
        or current.temporal_policy_version != temporal_policy_version
        or (observation_watermark_at, observation_watermark_id)
        <= (current.observation_watermark_at, current.observation_watermark_id)
    ):
        return False
    memory.replace_prime_authority(
        replace(
            current,
            observation_watermark_at=observation_watermark_at,
            observation_watermark_id=observation_watermark_id,
            valid_until=valid_until,
        )
    )
    return True
