"""AO-19 private API/webhook operations domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,199}$")
_SECRET_LIKE = re.compile(
    r"(?i)(sk_(?:live|test)_[A-Za-z0-9]+|bearer\s+\S+|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:api[_ -]?key|password|token)\s*[:=]\s*\S+)"
)


class ApiExposure(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    ADMIN = "ADMIN"


class ApiDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class WebhookDisposition(StrEnum):
    RECEIVED = "RECEIVED"
    SUCCEEDED = "SUCCEEDED"
    RETRY_PENDING = "RETRY_PENDING"
    DEAD_LETTER = "DEAD_LETTER"
    REJECTED = "REJECTED"


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _safe(value: str, name: str, maximum: int = 300) -> None:
    if not value or len(value) > maximum or _SECRET_LIKE.search(value):
        raise ValueError(f"{name} must be bounded non-secret text")


@dataclass(frozen=True, slots=True)
class ApiEndpointDefinition:
    endpoint_id: str
    method: str
    path_template: str
    exposure: ApiExposure
    direction: ApiDirection
    schema_version: str
    authority_boundary: str
    integration_id: str | None = None

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.endpoint_id):
            raise ValueError("endpoint_id must be a stable bounded identifier")
        if self.method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("unsupported endpoint method")
        if not self.path_template.startswith("/") or len(self.path_template) > 240:
            raise ValueError("path_template must be a bounded absolute path")
        _safe(self.schema_version, "schema_version", 80)
        _safe(self.authority_boundary, "authority_boundary", 500)
        if self.integration_id is not None:
            _safe(self.integration_id, "integration_id", 80)


@dataclass(frozen=True, slots=True)
class ApiOperationObservation:
    observation_id: str
    endpoint_id: str
    occurred_at: datetime
    latency_ms: int | None
    status_code: int | None
    error_category: str | None = None
    quota_remaining: int | None = None
    rate_limited: bool | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.observation_id, "observation_id"),
            (self.endpoint_id, "endpoint_id"),
        ):
            _safe(value, name, 200)
        _aware(self.occurred_at, "occurred_at")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be an HTTP status")
        if self.error_category is not None:
            _safe(self.error_category, "error_category", 80)
        if self.quota_remaining is not None and self.quota_remaining < 0:
            raise ValueError("quota_remaining cannot be negative")


@dataclass(frozen=True, slots=True)
class WebhookEnvelope:
    inbox_id: str
    integration_id: str
    provider_event_id: str
    event_type: str
    received_at: datetime
    payload_fingerprint: str
    payload_size: int
    schema_version: str
    disposition: WebhookDisposition
    attempt_count: int
    max_attempts: int
    last_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    failure_category: str | None = None
    result_ref: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.inbox_id, "inbox_id"),
            (self.integration_id, "integration_id"),
            (self.provider_event_id, "provider_event_id"),
            (self.event_type, "event_type"),
            (self.payload_fingerprint, "payload_fingerprint"),
            (self.schema_version, "schema_version"),
        ):
            _safe(value, name, 300)
        _aware(self.received_at, "received_at")
        if self.payload_size < 0 or self.payload_size > 1_048_576:
            raise ValueError("payload_size outside governed bounds")
        if self.max_attempts < 1 or self.max_attempts > 10:
            raise ValueError("max_attempts must be between 1 and 10")
        if self.attempt_count < 0 or self.attempt_count > self.max_attempts:
            raise ValueError("attempt_count outside governed bounds")
        if self.last_attempt_at is not None:
            _aware(self.last_attempt_at, "last_attempt_at")
        if self.next_retry_at is not None:
            _aware(self.next_retry_at, "next_retry_at")
        if self.failure_category is not None:
            _safe(self.failure_category, "failure_category", 80)
        if self.result_ref is not None:
            _safe(self.result_ref, "result_ref", 200)
