"""Deterministic temporal currentness and reobservation core for FR-25."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from application.economic_discovery.brain_contracts import (
    StateChange,
    TypingDimensionContract,
    affected_dimensions,
)
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationMemory,
    ObservationMutation,
    ingest_observation,
)
from domain.evidence.epistemics import Currentness


class ReobservationDisposition(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"


class ReobservationReason(StrEnum):
    CURRENT_ENOUGH = "CURRENT_ENOUGH"
    STALE = "STALE"
    HISTORICAL = "HISTORICAL"
    CURRENTNESS_UNKNOWN = "CURRENTNESS_UNKNOWN"


@dataclass(frozen=True, slots=True)
class TemporalCurrentnessPolicy:
    policy_id: str
    version: str
    stale_after: timedelta
    historical_after: timedelta

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("temporal currentness policy identity is required")
        if self.stale_after <= timedelta(0):
            raise ValueError("stale_after must be positive")
        if self.historical_after <= self.stale_after:
            raise ValueError("historical_after must be greater than stale_after")


@dataclass(frozen=True, slots=True)
class TemporalCurrentnessDecision:
    observation_id: str
    previous: Currentness
    current: Currentness
    as_of: datetime
    policy_id: str
    policy_version: str

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("temporal currentness decision requires observation id")
        if self.as_of.tzinfo is None:
            raise ValueError("temporal currentness decision time must be timezone-aware")

    @property
    def changed(self) -> bool:
        return self.previous is not self.current


@dataclass(frozen=True, slots=True)
class ReobservationRequirement:
    observation_id: str
    disposition: ReobservationDisposition
    reason: ReobservationReason
    effective_currentness: Currentness
    policy_id: str
    policy_version: str


@dataclass(frozen=True, slots=True)
class TemporalDependencyChange:
    subject_id: str
    observation_id: str
    previous: Currentness
    current: Currentness
    changed_dependency_fields: frozenset[str]

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.observation_id.strip():
            raise ValueError("temporal dependency change identity is required")
        if self.previous is self.current:
            raise ValueError("temporal dependency change requires an actual transition")
        if not self.changed_dependency_fields:
            raise ValueError("temporal dependency change requires dependency fields")


@dataclass(frozen=True, slots=True)
class ReobservationResult:
    predecessor_observation_id: str
    observation_id: str
    mutation: ObservationMutation


@dataclass(frozen=True, slots=True)
class SubjectReobservationPlan:
    subject_id: str
    as_of: datetime
    requirements: tuple[ReobservationRequirement, ...]

    @property
    def required_observation_ids(self) -> tuple[str, ...]:
        return tuple(
            item.observation_id
            for item in self.requirements
            if item.disposition is ReobservationDisposition.REQUIRED
        )


def evaluate_effective_currentness(
    *,
    observation_id: str,
    observed_at: datetime,
    previous: Currentness,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> TemporalCurrentnessDecision:
    if not observation_id.strip():
        raise ValueError("currentness evaluation requires observation id")
    if observed_at.tzinfo is None or as_of.tzinfo is None:
        raise ValueError("currentness evaluation times must be timezone-aware")
    if as_of < observed_at:
        raise ValueError("currentness cannot be evaluated before observation time")

    age = as_of - observed_at
    if previous is Currentness.UNKNOWN:
        current = Currentness.UNKNOWN
    elif previous is Currentness.HISTORICAL or age >= policy.historical_after:
        current = Currentness.HISTORICAL
    elif previous is Currentness.STALE or age >= policy.stale_after:
        current = Currentness.STALE
    else:
        current = Currentness.CURRENT

    return TemporalCurrentnessDecision(
        observation_id=observation_id,
        previous=previous,
        current=current,
        as_of=as_of,
        policy_id=policy.policy_id,
        policy_version=policy.version,
    )


def evaluate_currentness(
    observation: GovernedObservation,
    *,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> TemporalCurrentnessDecision:
    if as_of < observation.record.observed_at:
        raise ValueError("currentness cannot be evaluated before observation time")
    return evaluate_effective_currentness(
        observation_id=observation.record.observation_id,
        observed_at=observation.record.observed_at,
        previous=observation.reuse_authority.currentness,
        as_of=as_of,
        policy=policy,
    )


def reobservation_requirement(
    observation: GovernedObservation,
    *,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> ReobservationRequirement:
    decision = evaluate_currentness(observation, as_of=as_of, policy=policy)

    if decision.current is Currentness.CURRENT:
        disposition = ReobservationDisposition.NOT_REQUIRED
        reason = ReobservationReason.CURRENT_ENOUGH
    elif decision.current is Currentness.STALE:
        disposition = ReobservationDisposition.REQUIRED
        reason = ReobservationReason.STALE
    elif decision.current is Currentness.HISTORICAL:
        disposition = ReobservationDisposition.REQUIRED
        reason = ReobservationReason.HISTORICAL
    else:
        disposition = ReobservationDisposition.REQUIRED
        reason = ReobservationReason.CURRENTNESS_UNKNOWN

    return ReobservationRequirement(
        observation_id=observation.record.observation_id,
        disposition=disposition,
        reason=reason,
        effective_currentness=decision.current,
        policy_id=policy.policy_id,
        policy_version=policy.version,
    )


def temporal_dependency_change(
    observation: GovernedObservation,
    *,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> TemporalDependencyChange | None:
    decision = evaluate_currentness(observation, as_of=as_of, policy=policy)
    if not decision.changed:
        return None
    return TemporalDependencyChange(
        subject_id=observation.record.subject_id,
        observation_id=observation.record.observation_id,
        previous=decision.previous,
        current=decision.current,
        changed_dependency_fields=frozenset({"source.currentness"}),
    )


def affected_temporal_dimensions(
    change: TemporalDependencyChange,
    contracts: tuple[TypingDimensionContract, ...],
) -> tuple[str, ...]:
    synthetic = StateChange(
        subject_id=change.subject_id,
        changed_fields=change.changed_dependency_fields,
        previous_fingerprint=f"currentness:{change.previous.value}",
        current_fingerprint=f"currentness:{change.current.value}",
    )
    return affected_dimensions(synthetic, contracts)


def plan_subject_reobservations(
    memory: ObservationMemory,
    *,
    subject_id: str,
    as_of: datetime,
    policy: TemporalCurrentnessPolicy,
) -> SubjectReobservationPlan:
    """Plan against only the latest observation per source for one canonical subject."""

    if not subject_id.strip():
        raise ValueError("reobservation plan requires subject id")
    latest_by_source: dict[str, GovernedObservation] = {}
    for observation in memory.for_subject(subject_id):
        current = latest_by_source.get(observation.record.source_ref)
        if current is None or (
            observation.record.observed_at,
            observation.record.observation_id,
        ) > (
            current.record.observed_at,
            current.record.observation_id,
        ):
            latest_by_source[observation.record.source_ref] = observation

    requirements = tuple(
        reobservation_requirement(
            observation,
            as_of=as_of,
            policy=policy,
        )
        for observation in sorted(
            latest_by_source.values(),
            key=lambda item: (item.record.source_ref, item.record.observation_id),
        )
    )
    return SubjectReobservationPlan(
        subject_id=subject_id,
        as_of=as_of,
        requirements=requirements,
    )


def append_reobservation(
    memory: ObservationMemory,
    *,
    predecessor: GovernedObservation,
    observation: GovernedObservation,
) -> ReobservationResult:
    """Append a reobservation; never mutate/replace the predecessor."""

    if predecessor.record.subject_id != observation.record.subject_id:
        raise ValueError("reobservation must preserve canonical subject")
    if predecessor.record.source_ref != observation.record.source_ref:
        raise ValueError("reobservation must preserve source identity")
    if predecessor.record.observation_id == observation.record.observation_id:
        raise ValueError("reobservation requires a new observation id")
    if observation.record.observed_at <= predecessor.record.observed_at:
        raise ValueError("reobservation must occur after predecessor")

    existing_ids = {
        item.record.observation_id for item in memory.for_subject(predecessor.record.subject_id)
    }
    if predecessor.record.observation_id not in existing_ids:
        raise ValueError("reobservation predecessor must already exist in Observation Memory")

    mutation = ingest_observation(memory, observation)
    if not mutation.inserted:
        raise ValueError("reobservation must append a new Observation Memory record")

    return ReobservationResult(
        predecessor_observation_id=predecessor.record.observation_id,
        observation_id=observation.record.observation_id,
        mutation=mutation,
    )
