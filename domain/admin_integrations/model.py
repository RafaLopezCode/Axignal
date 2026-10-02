"""AO-18 private integration metadata; credential bytes are intentionally absent."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit


class IntegrationEnvironment(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class IntegrationDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class CredentialState(StrEnum):
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    CONFIGURED = "CONFIGURED"
    ROTATION_DUE = "ROTATION_DUE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class IntegrationHealthState(StrEnum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILING = "FAILING"
    UNAVAILABLE = "UNAVAILABLE"
    STALE = "STALE"


_IDENTITY = re.compile(r"^[a-z][a-z0-9._-]{1,79}$")
_SECRET_REFERENCE = re.compile(r"^secret://[A-Za-z0-9][A-Za-z0-9._/-]{0,190}$")
_SECRET_LIKE = re.compile(
    r"(?i)(sk_(?:live|test)_[A-Za-z0-9]+|bearer\s+\S+|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_ -]?key|password|token)\s*[:=]\s*\S+)"
)
_SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$")
_FAILURE_CATEGORY = re.compile(r"^[A-Z][A-Z0-9_]{1,79}$")
_SCOPE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{0,159}$")


def _required(value: str, field: str, maximum: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{field} is required and must be at most {maximum} characters")
    if _SECRET_LIKE.search(value):
        raise ValueError(f"{field} must not contain credential-like material")


def _aware(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class CredentialLifecycle:
    """Secret-free locator and lifecycle metadata, never credential material."""

    reference: str | None
    state: CredentialState
    last_rotated_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.reference is not None and not _SECRET_REFERENCE.fullmatch(self.reference):
            raise ValueError("credential reference must be a non-secret secret:// locator")
        for field, value in (
            ("last_rotated_at", self.last_rotated_at),
            ("expires_at", self.expires_at),
            ("revoked_at", self.revoked_at),
        ):
            if value is not None:
                _aware(value, field)
        if self.state in {CredentialState.CONFIGURED, CredentialState.ROTATION_DUE} and (
            self.reference is None
        ):
            raise ValueError("configured credential metadata requires a reference")
        if self.state is CredentialState.REVOKED and self.revoked_at is None:
            raise ValueError("revoked credential metadata requires revoked_at")


@dataclass(frozen=True, slots=True)
class IntegrationDefinition:
    integration_id: str
    provider: str
    purpose: str
    owner: str
    environment: IntegrationEnvironment
    enabled: bool
    credential: CredentialLifecycle
    scopes: tuple[str, ...]
    direction: IntegrationDirection
    authority_boundary: str
    webhook_capable: bool
    webhook_endpoint: str | None
    rate_limit_posture: str | None
    health_freshness_seconds: int
    version: int = 1

    def __post_init__(self) -> None:
        if not _IDENTITY.fullmatch(self.integration_id):
            raise ValueError("integration_id must be a stable lowercase identifier")
        for field, value in (
            ("provider", self.provider),
            ("purpose", self.purpose),
            ("owner", self.owner),
            ("authority_boundary", self.authority_boundary),
        ):
            _required(value, field)
        if self.webhook_endpoint is not None:
            _required(self.webhook_endpoint, "webhook_endpoint", 1000)
            if not self.webhook_capable:
                raise ValueError("webhook endpoint requires webhook capability")
            endpoint = urlsplit(self.webhook_endpoint)
            if (
                endpoint.scheme != "https"
                or not endpoint.hostname
                or endpoint.username is not None
                or endpoint.password is not None
                or endpoint.query
                or endpoint.fragment
            ):
                raise ValueError(
                    "webhook endpoint must be HTTPS and contain no userinfo, query, or fragment"
                )
        if self.version < 1:
            raise ValueError("integration version must be positive")
        if (
            isinstance(self.health_freshness_seconds, bool)
            or not isinstance(self.health_freshness_seconds, int)
            or self.health_freshness_seconds < 1
        ):
            raise ValueError("health_freshness_seconds must be a positive integer")
        if any(not isinstance(scope, str) or not _SCOPE.fullmatch(scope) for scope in self.scopes):
            raise ValueError("scope names must use bounded identifiers")
        if len(set(self.scopes)) != len(self.scopes):
            raise ValueError("scope names must be unique")
        if self.rate_limit_posture is not None:
            _required(self.rate_limit_posture, "rate_limit_posture")


@dataclass(frozen=True, slots=True)
class IntegrationHealth:
    integration_id: str
    state: IntegrationHealthState
    observed_at: datetime
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_category: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        if not _IDENTITY.fullmatch(self.integration_id):
            raise ValueError("integration_id must be a stable lowercase identifier")
        for field, value in (
            ("observed_at", self.observed_at),
            ("last_success_at", self.last_success_at),
            ("last_failure_at", self.last_failure_at),
        ):
            if value is not None:
                _aware(value, field)
        for metadata_field, metadata_value in (
            ("failure_category", self.failure_category),
            ("source_ref", self.source_ref),
        ):
            if metadata_value is not None:
                _required(metadata_value, metadata_field)
        if self.failure_category is not None and not _FAILURE_CATEGORY.fullmatch(
            self.failure_category
        ):
            raise ValueError("failure_category must use a bounded category identifier")
        if self.source_ref is not None and not _SAFE_REFERENCE.fullmatch(self.source_ref):
            raise ValueError("source_ref must use a bounded opaque reference")
        if self.state is IntegrationHealthState.FAILING and self.last_failure_at is None:
            raise ValueError("failing health requires an observed last failure")
        if self.state is IntegrationHealthState.STALE:
            raise ValueError("STALE is derived from observation time, not recorded as health")


def definition_fingerprint(definition: IntegrationDefinition) -> str:
    """Stable replay identity over metadata; no credential value can be included."""
    payload = {
        "integration_id": definition.integration_id,
        "provider": definition.provider,
        "purpose": definition.purpose,
        "owner": definition.owner,
        "environment": definition.environment.value,
        "enabled": definition.enabled,
        "credential_reference": definition.credential.reference,
        "credential_state": definition.credential.state.value,
        "last_rotated_at": (
            None
            if definition.credential.last_rotated_at is None
            else definition.credential.last_rotated_at.isoformat()
        ),
        "expires_at": (
            None
            if definition.credential.expires_at is None
            else definition.credential.expires_at.isoformat()
        ),
        "revoked_at": (
            None
            if definition.credential.revoked_at is None
            else definition.credential.revoked_at.isoformat()
        ),
        "scopes": list(definition.scopes),
        "direction": definition.direction.value,
        "authority_boundary": definition.authority_boundary,
        "webhook_capable": definition.webhook_capable,
        "webhook_endpoint": definition.webhook_endpoint,
        "rate_limit_posture": definition.rate_limit_posture,
        "health_freshness_seconds": definition.health_freshness_seconds,
        "version": definition.version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
