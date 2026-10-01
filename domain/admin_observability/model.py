"""Canonical semantic types for the Admin observability projection substrate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

AdminRecordId = NewType("AdminRecordId", str)
AdminProjectionId = NewType("AdminProjectionId", str)
AdminProjectionSnapshotId = NewType("AdminProjectionSnapshotId", str)


class AdminObservabilityError(ValueError):
    """Raised when an Admin observability record violates semantic contracts."""


class AdminRecordClass(StrEnum):
    """Observation classes stay distinct; they are not interchangeable telemetry."""

    OPERATIONAL_EVENT = "OPERATIONAL_EVENT"
    ECONOMIC_OBSERVATION = "ECONOMIC_OBSERVATION"
    EPISTEMIC_TRANSITION = "EPISTEMIC_TRANSITION"
    PROVIDER_USAGE_OBSERVATION = "PROVIDER_USAGE_OBSERVATION"
    ADMIN_METRIC_OBSERVATION = "ADMIN_METRIC_OBSERVATION"
    GOVERNANCE_EVENT = "GOVERNANCE_EVENT"
    SECURITY_EVENT = "SECURITY_EVENT"
    LOG_RECORD = "LOG_RECORD"
    TRACE_RECORD = "TRACE_RECORD"


class DataCompleteness(StrEnum):
    KNOWN = "KNOWN"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AdminPrivacyClass(StrEnum):
    """Privacy classification for metadata carried by Admin observability."""

    AGENT_SAFE = "AGENT_SAFE"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise AdminObservabilityError(f"{field_name} is required")


def _require_aware(value: datetime | None, field_name: str) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise AdminObservabilityError(f"{field_name} must be timezone-aware")


def _clean_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    cleaned = tuple(value.strip() for value in values)
    if any(not value for value in cleaned):
        raise AdminObservabilityError(f"{field_name} cannot contain blank references")
    if len(cleaned) != len(set(cleaned)):
        raise AdminObservabilityError(f"{field_name} cannot contain duplicate references")
    return cleaned


@dataclass(frozen=True, slots=True)
class AdminEventEnvelope:
    """Metadata-first record emitted by an owning domain for Admin projection.

    The envelope references source records. It does not copy raw private payloads,
    model prompts/responses, credentials, canonical evidence bodies or hidden
    reasoning.
    """

    record_id: AdminRecordId
    record_type: str
    record_class: AdminRecordClass
    schema_version: int
    producer: str
    owning_domain: str
    recorded_at: datetime
    outcome_state: str
    completeness: DataCompleteness
    privacy_class: AdminPrivacyClass
    occurred_at: datetime | None = None
    observed_at: datetime | None = None
    effective_at: datetime | None = None
    subject_refs: tuple[str, ...] = ()
    correlation_refs: tuple[str, ...] = ()
    causation_ref: str | None = None
    policy_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    unknown_reason: str | None = None
    supersedes_record_id: AdminRecordId | None = None

    def __post_init__(self) -> None:
        _require_text(self.record_id, "record_id")
        _require_text(self.record_type, "record_type")
        _require_text(self.producer, "producer")
        _require_text(self.owning_domain, "owning_domain")
        _require_text(self.outcome_state, "outcome_state")
        if self.schema_version < 1:
            raise AdminObservabilityError("schema_version must be >= 1")
        _require_aware(self.recorded_at, "recorded_at")
        _require_aware(self.occurred_at, "occurred_at")
        _require_aware(self.observed_at, "observed_at")
        _require_aware(self.effective_at, "effective_at")
        object.__setattr__(self, "subject_refs", _clean_refs(self.subject_refs, "subject_refs"))
        object.__setattr__(
            self,
            "correlation_refs",
            _clean_refs(self.correlation_refs, "correlation_refs"),
        )
        object.__setattr__(self, "policy_refs", _clean_refs(self.policy_refs, "policy_refs"))
        object.__setattr__(
            self,
            "provenance_refs",
            _clean_refs(self.provenance_refs, "provenance_refs"),
        )
        if self.causation_ref is not None:
            _require_text(self.causation_ref, "causation_ref")
        if self.supersedes_record_id is not None:
            _require_text(self.supersedes_record_id, "supersedes_record_id")
            if self.supersedes_record_id == self.record_id:
                raise AdminObservabilityError("a record cannot supersede itself")
        if self.completeness in {DataCompleteness.UNKNOWN, DataCompleteness.UNAVAILABLE}:
            if self.unknown_reason is None or not self.unknown_reason.strip():
                raise AdminObservabilityError("UNKNOWN/UNAVAILABLE records require unknown_reason")
        elif self.unknown_reason is not None and not self.unknown_reason.strip():
            raise AdminObservabilityError("unknown_reason cannot be blank")

    @property
    def fingerprint(self) -> str:
        payload = {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "record_class": self.record_class.value,
            "schema_version": self.schema_version,
            "producer": self.producer,
            "owning_domain": self.owning_domain,
            "recorded_at": self.recorded_at.isoformat(),
            "outcome_state": self.outcome_state,
            "completeness": self.completeness.value,
            "privacy_class": self.privacy_class.value,
            "occurred_at": None if self.occurred_at is None else self.occurred_at.isoformat(),
            "observed_at": None if self.observed_at is None else self.observed_at.isoformat(),
            "effective_at": None if self.effective_at is None else self.effective_at.isoformat(),
            "subject_refs": list(self.subject_refs),
            "correlation_refs": list(self.correlation_refs),
            "causation_ref": self.causation_ref,
            "policy_refs": list(self.policy_refs),
            "provenance_refs": list(self.provenance_refs),
            "unknown_reason": self.unknown_reason,
            "supersedes_record_id": self.supersedes_record_id,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ProjectionDatum:
    key: str
    value: str

    def __post_init__(self) -> None:
        _require_text(self.key, "projection datum key")
        if not isinstance(self.value, str):
            raise AdminObservabilityError("projection datum value must be text")


@dataclass(frozen=True, slots=True)
class AdminProjectionSnapshot:
    """Versioned temporal Admin read model; never an owning-domain record."""

    snapshot_id: AdminProjectionSnapshotId
    projection_id: AdminProjectionId
    schema_version: int
    scope: str
    as_of: datetime
    generated_at: datetime
    completeness: DataCompleteness
    source_record_ids: tuple[AdminRecordId, ...]
    data: tuple[ProjectionDatum, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        _require_text(self.snapshot_id, "snapshot_id")
        _require_text(self.projection_id, "projection_id")
        _require_text(self.scope, "scope")
        _require_text(self.fingerprint, "fingerprint")
        if self.schema_version < 1:
            raise AdminObservabilityError("projection schema_version must be >= 1")
        _require_aware(self.as_of, "as_of")
        _require_aware(self.generated_at, "generated_at")
        if self.generated_at < self.as_of:
            raise AdminObservabilityError("projection cannot be generated before as_of")
        _clean_refs(tuple(self.source_record_ids), "source_record_ids")
        keys = tuple(item.key for item in self.data)
        if len(keys) != len(set(keys)):
            raise AdminObservabilityError("projection data keys must be unique")
