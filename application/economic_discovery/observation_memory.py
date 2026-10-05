"""Governed Observation Memory and deterministic state reconstruction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.brain_contracts import ObservationRecord, StateChange
from domain.evidence.epistemics import Currentness


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("observation-memory identity and values must be non-empty")


class ObservationFieldState(StrEnum):
    """Explicit temporal meaning of one observed field contribution."""

    VALUE = "VALUE"
    MEASURED_ABSENCE = "MEASURED_ABSENCE"
    WITHDRAWN = "WITHDRAWN"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ObservedField:
    """One normalized state contribution carried by an observation."""

    name: str
    value: str
    state: ObservationFieldState = ObservationFieldState.VALUE
    competing_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.name, self.value)
        if self.state is ObservationFieldState.CONFLICTING:
            if len(set(self.competing_values)) < 2 or any(
                not value.strip() for value in self.competing_values
            ):
                raise ValueError("CONFLICTING field requires at least two competing values")
        elif self.competing_values:
            raise ValueError("only CONFLICTING fields can carry competing values")


class ObservationRightsStatus(StrEnum):
    PERMITTED = "PERMITTED"
    PROHIBITED = "PROHIBITED"
    UNKNOWN = "UNKNOWN"


class ObservationAccessStatus(StrEnum):
    ACCESSIBLE = "ACCESSIBLE"
    INACCESSIBLE = "INACCESSIBLE"


class ObservationReuseScope(StrEnum):
    GLOBAL_PUBLIC = "GLOBAL_PUBLIC"
    TENANT_PRIVATE = "TENANT_PRIVATE"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True, slots=True)
class ObservationReuseAuthority:
    rights_status: ObservationRightsStatus = ObservationRightsStatus.UNKNOWN
    access_status: ObservationAccessStatus = ObservationAccessStatus.ACCESSIBLE
    scope: ObservationReuseScope = ObservationReuseScope.RESTRICTED
    scope_owner_id: str | None = None
    provenance_ref: str | None = None
    currentness: Currentness = Currentness.UNKNOWN
    applicable_subject_ids: tuple[str, ...] = ()
    applicable_purposes: tuple[str, ...] = ()
    authority_id: str | None = None
    authority_version: str | None = None
    reuse_reason: str | None = None
    retention_policy_ref: str | None = None
    robots_policy_ref: str | None = None
    rate_policy_ref: str | None = None

    def __post_init__(self) -> None:
        if self.scope is ObservationReuseScope.TENANT_PRIVATE:
            if self.scope_owner_id is None or not self.scope_owner_id.strip():
                raise ValueError("private observation reuse scope requires owner")
        elif self.scope_owner_id is not None:
            raise ValueError("non-private observation reuse scope cannot carry owner")
        if self.provenance_ref is not None and not self.provenance_ref.strip():
            raise ValueError("observation reuse provenance ref cannot be empty")
        if (self.authority_id is None) != (self.authority_version is None):
            raise ValueError("observation reuse authority id/version must coexist")
        for value in (
            self.authority_id,
            self.authority_version,
            self.reuse_reason,
            self.retention_policy_ref,
            self.robots_policy_ref,
            self.rate_policy_ref,
        ):
            if value is not None and not value.strip():
                raise ValueError("observation reuse authority metadata cannot be empty")
        if any(not value.strip() for value in self.applicable_subject_ids):
            raise ValueError("observation applicability subjects must be non-empty")
        if any(not value.strip() for value in self.applicable_purposes):
            raise ValueError("observation applicability purposes must be non-empty")


@dataclass(frozen=True, slots=True)
class ObservationAccessMetadata:
    """Authorization-only observation metadata; excludes raw content/artifacts."""

    record: ObservationRecord
    reuse_authority: ObservationReuseAuthority


@dataclass(frozen=True, slots=True)
class GovernedObservation:
    """Observation plus reconstructible raw material and normalized state contributions."""

    record: ObservationRecord
    raw_content: str | None = None
    raw_artifact_ref: str | None = None
    fields: tuple[ObservedField, ...] = ()
    reuse_authority: ObservationReuseAuthority = ObservationReuseAuthority()

    def __post_init__(self) -> None:
        if self.raw_content is None and self.raw_artifact_ref is None:
            raise ValueError(
                "observation memory requires raw content or an immutable artifact reference"
            )
        if self.raw_content is not None and not self.raw_content:
            raise ValueError("raw observation content cannot be empty")
        if self.raw_artifact_ref is not None:
            _required(self.raw_artifact_ref)
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("an observation cannot contribute the same state field twice")


@dataclass(frozen=True, slots=True)
class StateField:
    """Current selected value for one state field, retaining exact provenance."""

    name: str
    value: str
    observation_id: str
    source_ref: str
    observed_at: datetime
    state: ObservationFieldState = ObservationFieldState.VALUE
    competing_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(self.name, self.value, self.observation_id, self.source_ref)
        if self.observed_at.tzinfo is None:
            raise ValueError("state field time must be timezone-aware")
        if self.state is ObservationFieldState.CONFLICTING and len(set(self.competing_values)) < 2:
            raise ValueError("CONFLICTING state requires competing values")


@dataclass(frozen=True, slots=True)
class ObservationState:
    """Deterministic state reconstructed from append-only observation history."""

    subject_id: str
    fields: tuple[StateField, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        _required(self.subject_id, self.fingerprint)
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            raise ValueError("compiled observation state requires unique field names")

    @property
    def available_fields(self) -> frozenset[str]:
        return frozenset(field.name for field in self.fields)

    def get(self, name: str) -> StateField | None:
        return next((field for field in self.fields if field.name == name), None)


def observation_reuse_authority_payload(
    authority: ObservationReuseAuthority,
) -> dict[str, object]:
    return {
        "rights_status": authority.rights_status.value,
        "access_status": authority.access_status.value,
        "scope": authority.scope.value,
        "scope_owner_id": authority.scope_owner_id,
        "provenance_ref": authority.provenance_ref,
        "currentness": authority.currentness.value,
        "applicable_subject_ids": list(authority.applicable_subject_ids),
        "applicable_purposes": list(authority.applicable_purposes),
        "authority_id": authority.authority_id,
        "authority_version": authority.authority_version,
        "reuse_reason": authority.reuse_reason,
        "retention_policy_ref": authority.retention_policy_ref,
        "robots_policy_ref": authority.robots_policy_ref,
        "rate_policy_ref": authority.rate_policy_ref,
    }


def observation_reuse_authority_from_payload(
    payload: dict[str, object],
) -> ObservationReuseAuthority:
    subjects = payload.get("applicable_subject_ids", [])
    purposes = payload.get("applicable_purposes", [])
    if not isinstance(subjects, list) or not isinstance(purposes, list):
        raise ValueError("observation reuse applicability payload must be arrays")
    return ObservationReuseAuthority(
        rights_status=ObservationRightsStatus(str(payload["rights_status"])),
        access_status=ObservationAccessStatus(str(payload["access_status"])),
        scope=ObservationReuseScope(str(payload["scope"])),
        scope_owner_id=(
            None if payload.get("scope_owner_id") is None else str(payload["scope_owner_id"])
        ),
        provenance_ref=(
            None if payload.get("provenance_ref") is None else str(payload["provenance_ref"])
        ),
        currentness=Currentness(str(payload["currentness"])),
        applicable_subject_ids=tuple(str(item) for item in subjects),
        applicable_purposes=tuple(str(item) for item in purposes),
        authority_id=(
            None if payload.get("authority_id") is None else str(payload["authority_id"])
        ),
        authority_version=(
            None if payload.get("authority_version") is None else str(payload["authority_version"])
        ),
        reuse_reason=(
            None if payload.get("reuse_reason") is None else str(payload["reuse_reason"])
        ),
        retention_policy_ref=(
            None
            if payload.get("retention_policy_ref") is None
            else str(payload["retention_policy_ref"])
        ),
        robots_policy_ref=(
            None if payload.get("robots_policy_ref") is None else str(payload["robots_policy_ref"])
        ),
        rate_policy_ref=(
            None if payload.get("rate_policy_ref") is None else str(payload["rate_policy_ref"])
        ),
    )


class ObservationMemoryConflict(ValueError):
    """Raised when an existing observation id is reused with different content."""


class ObservationMemory(Protocol):
    """Persistence port. Storage retains observations; it never admits truth."""

    def append(self, observation: GovernedObservation) -> bool:
        """Persist once. Return False only for an exact idempotent replay."""

    def for_subject(self, subject_id: str) -> tuple[GovernedObservation, ...]:
        """Return the complete governed history for one subject."""


class TemporalFieldChangeKind(StrEnum):
    INITIALIZED = "INITIALIZED"
    VALUE_CHANGED = "VALUE_CHANGED"
    REFRESHED = "REFRESHED"
    MEASURED_ABSENCE = "MEASURED_ABSENCE"
    WITHDRAWN = "WITHDRAWN"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TemporalFieldChange:
    field_name: str
    kind: TemporalFieldChangeKind
    previous: StateField | None
    current: StateField

    def __post_init__(self) -> None:
        _required(self.field_name)


@dataclass(frozen=True, slots=True)
class ObservationMutation:
    inserted: bool
    previous_state: ObservationState
    current_state: ObservationState
    change: StateChange | None
    typed_changes: tuple[TemporalFieldChange, ...] = ()


def _state_fingerprint(subject_id: str, fields: tuple[StateField, ...]) -> str:
    payload = {
        "subject_id": subject_id,
        "fields": [
            {
                "name": field.name,
                "value": field.value,
                "observation_id": field.observation_id,
                "source_ref": field.source_ref,
                "observed_at": field.observed_at.astimezone(UTC).isoformat(),
                "state": field.state.value,
                "competing_values": list(field.competing_values),
            }
            for field in fields
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compile_observation_state(
    subject_id: str,
    observations: tuple[GovernedObservation, ...],
    *,
    as_of: datetime | None = None,
) -> ObservationState:
    """Select the latest contribution per field without discarding history."""

    _required(subject_id)
    if as_of is not None and (as_of.tzinfo is None or as_of.utcoffset() is None):
        raise ValueError("as_of must be timezone-aware")
    cutoff = None if as_of is None else as_of.astimezone(UTC)
    latest: dict[str, StateField] = {}
    for observation in sorted(
        observations,
        key=lambda item: (
            item.record.observed_at.astimezone(UTC),
            item.record.observation_id,
        ),
    ):
        if observation.record.subject_id != subject_id:
            raise ValueError("state compilation cannot mix observation subjects")
        observed_at = observation.record.observed_at
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("observation time must be timezone-aware")
        if cutoff is not None and observed_at.astimezone(UTC) > cutoff:
            continue
        for field in observation.fields:
            latest[field.name] = StateField(
                name=field.name,
                value=field.value,
                observation_id=observation.record.observation_id,
                source_ref=observation.record.source_ref,
                observed_at=observed_at,
                state=field.state,
                competing_values=tuple(sorted(field.competing_values)),
            )

    selected = tuple(latest[name] for name in sorted(latest))
    return ObservationState(
        subject_id=subject_id,
        fields=selected,
        fingerprint=_state_fingerprint(subject_id, selected),
    )


def _typed_field_change(
    previous: StateField | None,
    current: StateField,
) -> TemporalFieldChange:
    if previous is None:
        kind = TemporalFieldChangeKind.INITIALIZED
    elif current.state is ObservationFieldState.MEASURED_ABSENCE:
        kind = TemporalFieldChangeKind.MEASURED_ABSENCE
    elif current.state is ObservationFieldState.WITHDRAWN:
        kind = TemporalFieldChangeKind.WITHDRAWN
    elif current.state is ObservationFieldState.CONFLICTING:
        kind = TemporalFieldChangeKind.CONFLICTING
    elif current.state is ObservationFieldState.UNKNOWN:
        kind = TemporalFieldChangeKind.UNKNOWN
    elif previous.value != current.value or previous.state is not current.state:
        kind = TemporalFieldChangeKind.VALUE_CHANGED
    else:
        kind = TemporalFieldChangeKind.REFRESHED
    return TemporalFieldChange(
        field_name=current.name,
        kind=kind,
        previous=previous,
        current=current,
    )


def ingest_observation(
    memory: ObservationMemory,
    observation: GovernedObservation,
) -> ObservationMutation:
    """Persist one observation and describe its deterministic state mutation."""

    subject_id = observation.record.subject_id
    previous = compile_observation_state(subject_id, memory.for_subject(subject_id))
    inserted = memory.append(observation)
    current = compile_observation_state(subject_id, memory.for_subject(subject_id))

    if not inserted or previous.fingerprint == current.fingerprint:
        return ObservationMutation(inserted, previous, current, None, ())

    previous_by_name = {field.name: field for field in previous.fields}
    current_by_name = {field.name: field for field in current.fields}
    changed = frozenset(
        name
        for name in previous_by_name.keys() | current_by_name.keys()
        if previous_by_name.get(name) != current_by_name.get(name)
    )
    if not changed:
        return ObservationMutation(inserted, previous, current, None, ())

    typed_changes = tuple(
        _typed_field_change(previous_by_name.get(name), current_by_name[name])
        for name in sorted(changed)
        if name in current_by_name
    )
    return ObservationMutation(
        inserted=True,
        previous_state=previous,
        current_state=current,
        change=StateChange(
            subject_id=subject_id,
            changed_fields=changed,
            previous_fingerprint=previous.fingerprint,
            current_fingerprint=current.fingerprint,
        ),
        typed_changes=typed_changes,
    )
