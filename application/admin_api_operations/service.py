"""AO-19 API/webhook operations console and bounded replay service."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol, TypeVar

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_api_operations import (
    ApiDirection,
    ApiEndpointDefinition,
    ApiExposure,
    ApiOperationObservation,
    WebhookDisposition,
    WebhookEnvelope,
)

T = TypeVar("T")


class ApiOperationsStore(Protocol):
    def append_observation(self, observation: ApiOperationObservation) -> bool: ...
    def observations(self) -> tuple[ApiOperationObservation, ...]: ...
    def put_webhook(self, envelope: WebhookEnvelope) -> bool: ...
    def webhook(self, integration_id: str, provider_event_id: str) -> WebhookEnvelope | None: ...
    def webhooks(self) -> tuple[WebhookEnvelope, ...]: ...


class WebhookReplayConflict(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EndpointOperationsView:
    endpoint: ApiEndpointDefinition
    request_count: int
    error_count: int
    error_rate: float | None
    average_latency_ms: int | None
    last_status_code: int | None
    last_observed_at: datetime | None
    quota_remaining: int | None
    rate_limited: bool | None


@dataclass(frozen=True, slots=True)
class ApiOperationsProjection:
    privacy_class: str
    generated_at: datetime
    endpoints: tuple[EndpointOperationsView, ...]
    webhook_received_count: int
    webhook_success_count: int
    webhook_retry_pending_count: int
    webhook_dead_letter_count: int
    webhook_rejected_count: int
    dead_letters: tuple[WebhookEnvelope, ...]
    coverage_notes: tuple[str, ...]


def canonical_api_inventory() -> tuple[ApiEndpointDefinition, ...]:
    return (
        ApiEndpointDefinition(
            "public.healthz",
            "GET",
            "/healthz",
            ApiExposure.PUBLIC,
            ApiDirection.INBOUND,
            "runtime-health-v1",
            "Operational health only; never AXIGLAND truth.",
        ),
        ApiEndpointDefinition(
            "public.runtimez",
            "GET",
            "/runtimez",
            ApiExposure.PUBLIC,
            ApiDirection.INBOUND,
            "runtime-detail-v1",
            "Runtime capability metadata only.",
        ),
        ApiEndpointDefinition(
            "public.acquisition.events",
            "POST",
            "/api/acquisition/events",
            ApiExposure.PUBLIC,
            ApiDirection.INBOUND,
            "observed-touch-v1",
            "AO-12 first-party marketing observation.",
        ),
        ApiEndpointDefinition(
            "public.weekly-brief.requests",
            "POST",
            "/api/weekly-brief/requests",
            ApiExposure.PUBLIC,
            ApiDirection.INBOUND,
            "brief-request-v1",
            "AO-15 request/consent boundary.",
        ),
        ApiEndpointDefinition(
            "internal.stripe.webhook",
            "POST",
            "/internal/webhooks/stripe",
            ApiExposure.INTERNAL,
            ApiDirection.INBOUND,
            "stripe-event-v1",
            "Stripe owns payment/subscription facts; AXIGNAL owns service entitlement.",
            "stripe-billing",
        ),
        ApiEndpointDefinition(
            "admin.shell",
            "GET",
            "/admin/{domain}",
            ApiExposure.ADMIN,
            ApiDirection.INBOUND,
            "admin-shell-v1",
            "Private Admin projection protected by AO-01 scopes.",
        ),
    )


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.INTEGRATIONS_READ not in grant.scopes:
        raise PermissionError("API operations console requires admin:integrations:read")


def _require_operate(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.INTEGRATIONS_MANAGE not in grant.scopes:
        raise PermissionError("webhook replay requires admin:integrations:manage")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("webhook replay requires STEP_UP assurance")


def _fingerprint(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def project_api_operations(
    *, store: ApiOperationsStore, grant: AdminAuthorizationGrant, generated_at: datetime
) -> ApiOperationsProjection:
    _require_read(grant)
    observations = store.observations()
    views: list[EndpointOperationsView] = []
    for endpoint in canonical_api_inventory():
        items = sorted(
            (item for item in observations if item.endpoint_id == endpoint.endpoint_id),
            key=lambda item: item.occurred_at,
        )
        errors = [
            item
            for item in items
            if item.error_category is not None
            or (item.status_code is not None and item.status_code >= 400)
        ]
        latencies = [item.latency_ms for item in items if item.latency_ms is not None]
        latest = items[-1] if items else None
        views.append(
            EndpointOperationsView(
                endpoint=endpoint,
                request_count=len(items),
                error_count=len(errors),
                error_rate=(None if not items else len(errors) / len(items)),
                average_latency_ms=(None if not latencies else sum(latencies) // len(latencies)),
                last_status_code=None if latest is None else latest.status_code,
                last_observed_at=None if latest is None else latest.occurred_at,
                quota_remaining=None if latest is None else latest.quota_remaining,
                rate_limited=None if latest is None else latest.rate_limited,
            )
        )
    webhooks = store.webhooks()
    return ApiOperationsProjection(
        privacy_class="PRIVATE_AXIGNAL_API_OPERATIONS",
        generated_at=generated_at,
        endpoints=tuple(views),
        webhook_received_count=len(webhooks),
        webhook_success_count=sum(x.disposition is WebhookDisposition.SUCCEEDED for x in webhooks),
        webhook_retry_pending_count=sum(
            x.disposition is WebhookDisposition.RETRY_PENDING for x in webhooks
        ),
        webhook_dead_letter_count=sum(
            x.disposition is WebhookDisposition.DEAD_LETTER for x in webhooks
        ),
        webhook_rejected_count=sum(x.disposition is WebhookDisposition.REJECTED for x in webhooks),
        dead_letters=tuple(x for x in webhooks if x.disposition is WebhookDisposition.DEAD_LETTER),
        coverage_notes=(
            "Payload bodies, authorization headers and credential bytes are never projected.",
            "Replay is bounded and provider-event identity plus payload fingerprint prevent duplicate effects.",
            "This console exposes predefined governed operations only; it is not an arbitrary request console.",
            "Missing latency, quota or rate-limit evidence remains UNKNOWN rather than zero.",
        ),
    )


class WebhookOperationsService:
    def __init__(self, store: ApiOperationsStore, *, max_attempts: int = 3) -> None:
        if not 1 <= max_attempts <= 10:
            raise ValueError("max_attempts must be between 1 and 10")
        self._store = store
        self._max_attempts = max_attempts

    def receive_and_process(
        self,
        *,
        integration_id: str,
        provider_event_id: str,
        event_type: str,
        payload: bytes,
        schema_version: str,
        received_at: datetime,
        processor: Callable[[], T],
        transient_exceptions: tuple[type[BaseException], ...] = (),
    ) -> tuple[WebhookEnvelope, T | None, bool]:
        fingerprint = _fingerprint(payload)
        existing = self._store.webhook(integration_id, provider_event_id)
        if existing is not None:
            if existing.payload_fingerprint != fingerprint:
                raise WebhookReplayConflict("provider event id reused with different payload")
            if existing.disposition is WebhookDisposition.SUCCEEDED:
                return existing, None, True
            if existing.disposition in {
                WebhookDisposition.REJECTED,
                WebhookDisposition.DEAD_LETTER,
            }:
                return existing, None, True
        envelope = existing or WebhookEnvelope(
            inbox_id=f"webhook:{integration_id}:{provider_event_id}",
            integration_id=integration_id,
            provider_event_id=provider_event_id,
            event_type=event_type,
            received_at=received_at,
            payload_fingerprint=fingerprint,
            payload_size=len(payload),
            schema_version=schema_version,
            disposition=WebhookDisposition.RECEIVED,
            attempt_count=0,
            max_attempts=self._max_attempts,
        )
        attempt = envelope.attempt_count + 1
        try:
            result = processor()
        except transient_exceptions as exc:
            exhausted = attempt >= envelope.max_attempts
            updated = replace(
                envelope,
                disposition=(
                    WebhookDisposition.DEAD_LETTER
                    if exhausted
                    else WebhookDisposition.RETRY_PENDING
                ),
                attempt_count=attempt,
                last_attempt_at=received_at,
                next_retry_at=(None if exhausted else received_at + timedelta(minutes=2**attempt)),
                failure_category=type(exc).__name__.upper()[:80],
            )
            self._store.put_webhook(updated)
            raise
        except Exception as exc:
            updated = replace(
                envelope,
                disposition=WebhookDisposition.REJECTED,
                attempt_count=attempt,
                last_attempt_at=received_at,
                next_retry_at=None,
                failure_category=type(exc).__name__.upper()[:80],
            )
            self._store.put_webhook(updated)
            raise
        updated = replace(
            envelope,
            disposition=WebhookDisposition.SUCCEEDED,
            attempt_count=attempt,
            last_attempt_at=received_at,
            next_retry_at=None,
            failure_category=None,
            result_ref=f"processed:{integration_id}:{provider_event_id}",
        )
        self._store.put_webhook(updated)
        return updated, result, False
