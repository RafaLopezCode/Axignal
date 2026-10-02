"""AO-15 Admin acquisition projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.admin_acquisition.marketing_service import (
    MarketingEventStore,
    summarize_marketing,
)
from application.admin_acquisition.service import AcquisitionStore, _require_scope, _snapshot
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_acquisition import (
    BriefReviewState,
    MarketingEventKind,
    NewsletterConsentState,
)


class AcquisitionProjectionStore(AcquisitionStore, MarketingEventStore, Protocol):
    pass


@dataclass(frozen=True, slots=True)
class BriefRequestView:
    request_id: str
    company_name: str
    company_domain: str
    review_state: str
    coverage_state: str
    consent_state: str
    delivery_eligible: bool
    observed_source: str
    observed_campaign: str
    attribution_event_id: str | None
    requested_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AdminAcquisitionProjection:
    privacy_class: str
    generated_at: datetime
    request_count: int
    accepted_count: int
    consented_count: int
    delivery_eligible_count: int
    marketing_event_count: int
    anonymous_session_count: int
    attributed_request_count: int
    source_counts: tuple[tuple[str, int], ...]
    campaign_counts: tuple[tuple[str, int], ...]
    attribution_model: str
    requests: tuple[BriefRequestView, ...]
    pii_visible: bool
    coverage_notes: tuple[str, ...]


def project_admin_acquisition(
    *,
    store: AcquisitionProjectionStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> AdminAcquisitionProjection:
    _require_scope(grant, AdminScope.ACQUISITION_READ)
    request_ids = sorted({str(event.request_id) for event in store.all_events()})
    snapshots = tuple(_snapshot(store, request_id) for request_id in request_ids)
    marketing_events = store.marketing_events()
    marketing = summarize_marketing(marketing_events)
    request_attribution: dict[str, tuple[str, str, str | None]] = {}
    for link in marketing_events:
        if link.kind is not MarketingEventKind.WEEKLY_BRIEF_REQUESTED or link.request_id is None:
            continue
        candidates = tuple(
            event
            for event in marketing_events
            if event.session_ref == link.session_ref
            and event.occurred_at <= link.occurred_at
            and event.kind is not MarketingEventKind.WEEKLY_BRIEF_REQUESTED
            and (event.utm_source is not None or event.utm_campaign is not None)
        )
        observed = candidates[-1] if candidates else None
        request_attribution[link.request_id] = (
            observed.utm_source if observed and observed.utm_source else "UNATTRIBUTED",
            observed.utm_campaign if observed and observed.utm_campaign else "UNATTRIBUTED",
            str(observed.event_id) if observed else None,
        )
    return AdminAcquisitionProjection(
        privacy_class="PRIVATE_AXIGNAL_ACQUISITION",
        generated_at=generated_at,
        request_count=len(snapshots),
        accepted_count=sum(item.review_state is BriefReviewState.ACCEPTED for item in snapshots),
        consented_count=sum(
            item.consent_state is NewsletterConsentState.GRANTED for item in snapshots
        ),
        delivery_eligible_count=sum(item.delivery_eligible for item in snapshots),
        marketing_event_count=marketing.event_count,
        anonymous_session_count=marketing.anonymous_session_count,
        attributed_request_count=marketing.linked_request_count,
        source_counts=marketing.source_counts,
        campaign_counts=marketing.campaign_counts,
        attribution_model=marketing.model_version.value,
        requests=tuple(
            BriefRequestView(
                request_id=str(item.request_id),
                company_name=item.company_name,
                company_domain=item.company_domain,
                review_state=item.review_state.value,
                coverage_state=item.coverage_state.value,
                consent_state=item.consent_state.value,
                delivery_eligible=item.delivery_eligible,
                observed_source=request_attribution.get(
                    str(item.request_id), ("UNATTRIBUTED", "UNATTRIBUTED", None)
                )[0],
                observed_campaign=request_attribution.get(
                    str(item.request_id), ("UNATTRIBUTED", "UNATTRIBUTED", None)
                )[1],
                attribution_event_id=request_attribution.get(
                    str(item.request_id), ("UNATTRIBUTED", "UNATTRIBUTED", None)
                )[2],
                requested_at=item.requested_at,
                updated_at=item.updated_at,
            )
            for item in snapshots
        ),
        pii_visible=False,
        coverage_notes=(
            "Request, coverage acceptance, newsletter consent and paid conversion are separate states.",
            "Marketing attribution records observed touches; it does not claim causal influence.",
            "Anonymous session references are operational telemetry, not person identities or CRM contacts.",
            "Professional email and free-text purpose are excluded from this projection.",
            "An accepted request never creates a free Xeed or AXENT entitlement.",
        ),
    )
