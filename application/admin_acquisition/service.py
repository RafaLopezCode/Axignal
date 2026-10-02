"""AO-15 application services for weekly brief requests and consent."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_acquisition import (
    BriefRequestEvent,
    BriefRequestEventId,
    BriefRequestEventKind,
    BriefRequestId,
    BriefRequestSnapshot,
    BriefReviewState,
    CoverageState,
    NewsletterConsentState,
)


class AcquisitionStore(Protocol):
    def append_event(self, event: BriefRequestEvent) -> bool: ...
    def events_for_request(self, request_id: str) -> tuple[BriefRequestEvent, ...]: ...
    def all_events(self) -> tuple[BriefRequestEvent, ...]: ...


def _payload(**values: str | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, value) for key, value in values.items() if value is not None))


def _payload_dict(event: BriefRequestEvent) -> dict[str, str]:
    return dict(event.payload)


def _require_scope(grant: AdminAuthorizationGrant, scope: AdminScope) -> None:
    if scope not in grant.scopes:
        raise PermissionError(f"acquisition operation requires {scope.value}")


def _require_write_scope(grant: AdminAuthorizationGrant) -> None:
    _require_scope(grant, AdminScope.ACQUISITION_WRITE)
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("acquisition mutation requires STEP_UP assurance")


def reduce_brief_request(events: tuple[BriefRequestEvent, ...]) -> BriefRequestSnapshot:
    if not events or events[0].kind is not BriefRequestEventKind.REQUEST_SUBMITTED:
        raise ValueError("brief request history must start with REQUEST_SUBMITTED")
    first = events[0]
    data = _payload_dict(first)
    snapshot = BriefRequestSnapshot(
        request_id=first.request_id,
        company_name=data["company_name"],
        company_domain=data["company_domain"],
        professional_email=data["professional_email"],
        purpose=data["purpose"],
        request_notice_version=data["request_notice_version"],
        requested_at=first.occurred_at,
        updated_at=first.occurred_at,
        review_state=BriefReviewState.REQUESTED,
        coverage_state=CoverageState.UNKNOWN,
        consent_state=NewsletterConsentState.NOT_GRANTED,
    )
    for event in events[1:]:
        if event.request_id != snapshot.request_id:
            raise ValueError("brief request history contains another request")
        if event.occurred_at < snapshot.updated_at:
            raise ValueError("brief request events must be monotonic")
        data = _payload_dict(event)
        if event.kind is BriefRequestEventKind.CLARIFICATION_REQUIRED:
            snapshot = replace(
                snapshot,
                review_state=BriefReviewState.CLARIFICATION_REQUIRED,
                review_reason=data["reason"],
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.COVERAGE_ACCEPTED:
            snapshot = replace(
                snapshot,
                review_state=BriefReviewState.ACCEPTED,
                coverage_state=CoverageState.SUFFICIENT,
                subject_reference=data.get("subject_reference"),
                review_reason=data["reason"],
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.COVERAGE_DECLINED:
            snapshot = replace(
                snapshot,
                review_state=BriefReviewState.DECLINED,
                coverage_state=CoverageState.INSUFFICIENT,
                review_reason=data["reason"],
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.CONSENT_GRANTED:
            snapshot = replace(
                snapshot,
                consent_state=NewsletterConsentState.GRANTED,
                newsletter_notice_version=data["newsletter_notice_version"],
                consented_at=event.occurred_at,
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.CONSENT_WITHDRAWN:
            snapshot = replace(
                snapshot,
                consent_state=NewsletterConsentState.WITHDRAWN,
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.SUPPRESSED:
            snapshot = replace(
                snapshot,
                consent_state=NewsletterConsentState.SUPPRESSED,
                review_reason=data["reason"],
                updated_at=event.occurred_at,
            )
        elif event.kind is BriefRequestEventKind.WITHDRAWN:
            snapshot = replace(
                snapshot,
                review_state=BriefReviewState.WITHDRAWN,
                updated_at=event.occurred_at,
            )
    return snapshot


def _snapshot(store: AcquisitionStore, request_id: str) -> BriefRequestSnapshot:
    events = store.events_for_request(request_id)
    if not events:
        raise LookupError(request_id)
    return reduce_brief_request(events)


def _append(
    store: AcquisitionStore,
    *,
    event_id: str,
    request_id: str,
    kind: BriefRequestEventKind,
    occurred_at: datetime,
    actor: str,
    payload: tuple[tuple[str, str], ...] = (),
) -> bool:
    current = store.events_for_request(request_id)
    if current and occurred_at < current[-1].occurred_at:
        raise ValueError("brief request mutation cannot move backward in time")
    return store.append_event(
        BriefRequestEvent(
            event_id=BriefRequestEventId(event_id),
            request_id=BriefRequestId(request_id),
            kind=kind,
            occurred_at=occurred_at,
            actor=actor,
            payload=payload,
        )
    )
