"""Governed source registry for acquisition and observation reuse authority.

The registry is metadata authority, not truth authority. It decides whether a
registered instrument may acquire a bounded source for one purpose and emits the
exact reuse/currentness metadata that must follow the resulting observation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from application.economic_discovery.observation_memory import (
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
    SourceTargetRule,
)
from domain.evidence.epistemics import Currentness


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("source registry identity and metadata must be non-empty")


class RobotsRequirement(StrEnum):
    NOT_REQUIRED_SINGLE_DOCUMENT = "NOT_REQUIRED_SINGLE_DOCUMENT"
    REQUIRED = "REQUIRED"


class RobotsDecision(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PERMITTED = "PERMITTED"
    PROHIBITED = "PROHIBITED"
    UNKNOWN = "UNKNOWN"


class SourceRegistryReason(StrEnum):
    SOURCE_NOT_REGISTERED = "SOURCE_NOT_REGISTERED"
    SOURCE_TYPE_MISMATCH = "SOURCE_TYPE_MISMATCH"
    PURPOSE_NOT_ALLOWED = "PURPOSE_NOT_ALLOWED"
    RIGHTS_PROHIBITED = "RIGHTS_PROHIBITED"
    RIGHTS_UNKNOWN = "RIGHTS_UNKNOWN"
    SOURCE_INACCESSIBLE = "SOURCE_INACCESSIBLE"
    ROBOTS_PROHIBITED = "ROBOTS_PROHIBITED"
    ROBOTS_UNKNOWN = "ROBOTS_UNKNOWN"
    INSTRUMENT_NOT_AUTHORIZED = "INSTRUMENT_NOT_AUTHORIZED"


@dataclass(frozen=True, slots=True)
class SourceRatePolicy:
    policy_id: str
    version: str
    max_requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        _required(self.policy_id, self.version)
        if self.max_requests < 1 or self.window_seconds < 1:
            raise ValueError("source rate policy limits must be positive")

    @property
    def ref(self) -> str:
        return f"{self.policy_id}@{self.version}"


@dataclass(frozen=True, slots=True)
class SourceRetentionPolicy:
    policy_id: str
    version: str
    raw_retention_days: int
    metadata_retention_days: int

    def __post_init__(self) -> None:
        _required(self.policy_id, self.version)
        if self.raw_retention_days < 0 or self.metadata_retention_days < 1:
            raise ValueError("source retention policy durations are invalid")
        if self.metadata_retention_days < self.raw_retention_days:
            raise ValueError("metadata retention cannot be shorter than raw retention")

    @property
    def ref(self) -> str:
        return f"{self.policy_id}@{self.version}"


@dataclass(frozen=True, slots=True)
class SourceRegistryEntry:
    source_id: str
    version: str
    source_type: str
    instrument_ref: str
    decision_basis: str
    targets: tuple[SourceTargetRule, ...]
    allowed_purposes: tuple[ReusePurpose, ...]
    rights_status: ObservationRightsStatus
    access_status: ObservationAccessStatus
    reuse_scope: ObservationReuseScope
    reuse_reason: str
    temporal_policy: TemporalCurrentnessPolicy
    retention_policy: SourceRetentionPolicy
    rate_policy: SourceRatePolicy
    robots_requirement: RobotsRequirement
    robots_decision: RobotsDecision
    robots_policy_ref: str
    scope_owner_id: str | None = None
    currentness: Currentness = Currentness.CURRENT
    max_response_bytes: int = 2_000_000
    timeout_ms: int = 5_000
    max_redirects: int = 3

    def __post_init__(self) -> None:
        _required(
            self.source_id,
            self.version,
            self.source_type,
            self.instrument_ref,
            self.decision_basis,
            self.reuse_reason,
            self.robots_policy_ref,
        )
        if not self.targets:
            raise ValueError("source registry entry requires bounded targets")
        if not self.allowed_purposes:
            raise ValueError("source registry entry requires at least one purpose")
        if len(set(self.allowed_purposes)) != len(self.allowed_purposes):
            raise ValueError("source registry purposes must be unique")
        if self.reuse_scope is ObservationReuseScope.TENANT_PRIVATE:
            if self.scope_owner_id is None or not self.scope_owner_id.strip():
                raise ValueError("tenant-private source registry entry requires scope owner")
        elif self.scope_owner_id is not None:
            raise ValueError("non-private source registry entry cannot carry scope owner")
        if self.robots_requirement is RobotsRequirement.NOT_REQUIRED_SINGLE_DOCUMENT:
            if self.robots_decision is not RobotsDecision.NOT_APPLICABLE:
                raise ValueError(
                    "single-document robots exemption must be explicitly NOT_APPLICABLE"
                )
        elif self.robots_decision is RobotsDecision.NOT_APPLICABLE:
            raise ValueError("required robots evaluation cannot be NOT_APPLICABLE")
        if self.max_response_bytes < 1 or self.max_response_bytes > 20_000_000:
            raise ValueError("source registry response budget must be between 1 byte and 20 MB")
        if self.timeout_ms < 100 or self.timeout_ms > 30_000:
            raise ValueError("source registry timeout must be between 100 ms and 30 s")
        if self.max_redirects < 0 or self.max_redirects > 10:
            raise ValueError("source registry redirect budget must be between 0 and 10")

    @property
    def fingerprint(self) -> str:
        payload = {
            "source_id": self.source_id,
            "version": self.version,
            "source_type": self.source_type,
            "instrument_ref": self.instrument_ref,
            "decision_basis": self.decision_basis,
            "targets": [
                {
                    "host": target.host.rstrip(".").lower(),
                    "path_prefix": target.path_prefix,
                    "schemes": list(target.schemes),
                }
                for target in self.targets
            ],
            "allowed_purposes": [item.value for item in self.allowed_purposes],
            "rights_status": self.rights_status.value,
            "access_status": self.access_status.value,
            "reuse_scope": self.reuse_scope.value,
            "scope_owner_id": self.scope_owner_id,
            "reuse_reason": self.reuse_reason,
            "temporal_policy": {
                "policy_id": self.temporal_policy.policy_id,
                "version": self.temporal_policy.version,
                "stale_after_seconds": int(self.temporal_policy.stale_after.total_seconds()),
                "historical_after_seconds": int(
                    self.temporal_policy.historical_after.total_seconds()
                ),
            },
            "retention_policy_ref": self.retention_policy.ref,
            "rate_policy_ref": self.rate_policy.ref,
            "robots_requirement": self.robots_requirement.value,
            "robots_decision": self.robots_decision.value,
            "robots_policy_ref": self.robots_policy_ref,
            "currentness": self.currentness.value,
            "max_response_bytes": self.max_response_bytes,
            "timeout_ms": self.timeout_ms,
            "max_redirects": self.max_redirects,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceRegistryAuthorization:
    source_id: str
    source_version: str
    source_fingerprint: str
    purpose: ReusePurpose
    request: SourceRequest
    dispatch_policy: SourceDispatchPolicy
    reuse_authority: ObservationReuseAuthority
    temporal_policy: TemporalCurrentnessPolicy
    retention_policy: SourceRetentionPolicy
    rate_policy: SourceRatePolicy


class SourceRegistryRejected(ValueError):
    def __init__(self, source_id: str, reason: SourceRegistryReason) -> None:
        self.source_id = source_id
        self.reason = reason
        super().__init__(f"{source_id}:{reason.value}")


class StaticSourceRegistry:
    """Immutable registry suitable for deterministic runtime composition."""

    def __init__(self, entries: tuple[SourceRegistryEntry, ...]) -> None:
        if not entries:
            raise ValueError("source registry requires at least one entry")
        ids = [entry.source_id for entry in entries]
        if len(ids) != len(set(ids)):
            raise ValueError("source registry source ids must be unique")
        self._entries = {entry.source_id: entry for entry in entries}

    def get(self, source_id: str) -> SourceRegistryEntry | None:
        return self._entries.get(source_id)

    def authorize(
        self,
        *,
        source_id: str,
        request_id: str,
        subject_id: str,
        observation_slot: str,
        target_uri: str,
        source_type: str,
        purpose: ReusePurpose,
        instrument_ref: str,
    ) -> SourceRegistryAuthorization:
        entry = self.get(source_id)
        if entry is None:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.SOURCE_NOT_REGISTERED)
        if source_type != entry.source_type:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.SOURCE_TYPE_MISMATCH)
        if purpose not in entry.allowed_purposes:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.PURPOSE_NOT_ALLOWED)
        if entry.rights_status is ObservationRightsStatus.PROHIBITED:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.RIGHTS_PROHIBITED)
        if entry.rights_status is ObservationRightsStatus.UNKNOWN:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.RIGHTS_UNKNOWN)
        if entry.access_status is ObservationAccessStatus.INACCESSIBLE:
            raise SourceRegistryRejected(source_id, SourceRegistryReason.SOURCE_INACCESSIBLE)
        if entry.robots_requirement is RobotsRequirement.REQUIRED:
            if entry.robots_decision is RobotsDecision.PROHIBITED:
                raise SourceRegistryRejected(source_id, SourceRegistryReason.ROBOTS_PROHIBITED)
            if entry.robots_decision is not RobotsDecision.PERMITTED:
                raise SourceRegistryRejected(source_id, SourceRegistryReason.ROBOTS_UNKNOWN)
        if instrument_ref != entry.instrument_ref:
            raise SourceRegistryRejected(
                source_id,
                SourceRegistryReason.INSTRUMENT_NOT_AUTHORIZED,
            )

        policy = SourceDispatchPolicy(
            policy_id=f"source-registry:{entry.source_id}",
            policy_version=entry.version,
            disposition=DispatchDisposition.ALLOW,
            decision_basis=entry.decision_basis,
            targets=entry.targets,
            max_response_bytes=entry.max_response_bytes,
            timeout_ms=entry.timeout_ms,
            max_redirects=entry.max_redirects,
        )
        request = SourceRequest(
            request_id=request_id,
            subject_id=subject_id,
            observation_slot=observation_slot,
            target_uri=target_uri,
            source_type=source_type,
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            policy_version=policy.policy_version,
        )
        provenance_ref = f"source-registry:{entry.source_id}@{entry.version}:{entry.fingerprint}"
        authority = ObservationReuseAuthority(
            rights_status=entry.rights_status,
            access_status=entry.access_status,
            scope=entry.reuse_scope,
            scope_owner_id=entry.scope_owner_id,
            provenance_ref=provenance_ref,
            currentness=entry.currentness,
            applicable_subject_ids=(subject_id,),
            applicable_purposes=(purpose.value,),
            authority_id=entry.source_id,
            authority_version=entry.version,
            reuse_reason=entry.reuse_reason,
            retention_policy_ref=entry.retention_policy.ref,
            content_retention_days=entry.retention_policy.raw_retention_days,
            robots_policy_ref=entry.robots_policy_ref,
            rate_policy_ref=entry.rate_policy.ref,
        )
        return SourceRegistryAuthorization(
            source_id=entry.source_id,
            source_version=entry.version,
            source_fingerprint=entry.fingerprint,
            purpose=purpose,
            request=request,
            dispatch_policy=policy,
            reuse_authority=authority,
            temporal_policy=entry.temporal_policy,
            retention_policy=entry.retention_policy,
            rate_policy=entry.rate_policy,
        )
