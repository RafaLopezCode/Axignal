"""AO-15 Admin acquisition projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from application.admin_acquisition.service import AcquisitionStore, _require_scope, _snapshot
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_acquisition import BriefReviewState, NewsletterConsentState


@dataclass(frozen=True, slots=True)
class BriefRequestView:
    request_id: str
    company_name: str
    company_domain: str
    review_state: str
    coverage_state: str
    consent_state: str
    delivery_eligible: bool
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
    requests: tuple[BriefRequestView, ...]
    pii_visible: bool
    coverage_notes: tuple[str, ...]


def project_admin_acquisition(
    *,
    store: AcquisitionStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> AdminAcquisitionProjection:
    _require_scope(grant, AdminScope.ACQUISITION_READ)
    request_ids = sorted({str(event.request_id) for event in store.all_events()})
    snapshots = tuple(_snapshot(store, request_id) for request_id in request_ids)
    return AdminAcquisitionProjection(
        privacy_class="PRIVATE_AXIGNAL_ACQUISITION",
        generated_at=generated_at,
        request_count=len(snapshots),
        accepted_count=sum(item.review_state is BriefReviewState.ACCEPTED for item in snapshots),
        consented_count=sum(
            item.consent_state is NewsletterConsentState.GRANTED for item in snapshots
        ),
        delivery_eligible_count=sum(item.delivery_eligible for item in snapshots),
        requests=tuple(
            BriefRequestView(
                request_id=str(item.request_id),
                company_name=item.company_name,
                company_domain=item.company_domain,
                review_state=item.review_state.value,
                coverage_state=item.coverage_state.value,
                consent_state=item.consent_state.value,
                delivery_eligible=item.delivery_eligible,
                requested_at=item.requested_at,
                updated_at=item.updated_at,
            )
            for item in snapshots
        ),
        pii_visible=False,
        coverage_notes=(
            "Request, coverage acceptance, newsletter consent and paid conversion are separate states.",
            "Professional email and free-text purpose are excluded from this projection.",
            "An accepted request never creates a free Xeed or AXENT entitlement.",
        ),
    )
