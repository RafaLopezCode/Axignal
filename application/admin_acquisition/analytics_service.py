"""AO-14 product analytics ingestion and AO-17 growth observatory projection."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.admin_acquisition.service import AcquisitionStore, reduce_brief_request
from application.admin_billing.service import BillingStore
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_acquisition import (
    AnalyticsEvent,
    AnalyticsEventId,
    AnalyticsEventKind,
    BriefRequestEventKind,
    BriefReviewState,
    MarketingEventKind,
    NewsletterConsentState,
    TrafficClassification,
)
from domain.admin_billing import BillingEventKind, BillingPaymentState


class AnalyticsStore(Protocol):
    def append_analytics_event(self, event: AnalyticsEvent) -> bool: ...
    def analytics_events(self) -> tuple[AnalyticsEvent, ...]: ...


class GrowthAcquisitionStore(AcquisitionStore, AnalyticsStore, Protocol):
    def marketing_events(self) -> tuple[object, ...]: ...


class GrowthWeeklyBriefStore(Protocol):
    def all_issues(self) -> tuple[object, ...]: ...
    def all_deliveries(self) -> tuple[object, ...]: ...
    def all_corrections(self) -> tuple[object, ...]: ...


@dataclass(frozen=True, slots=True)
class ConversionView:
    request_id: str
    account_id: str
    requested_at: datetime
    paid_at: datetime
    time_to_conversion_seconds: int
    xeed_capacity: int
    additional_xeed_attached: bool


@dataclass(frozen=True, slots=True)
class CohortEconomics:
    currency: str
    paid_revenue_minor: int
    delivery_cost_minor: int
    gross_contribution_minor: int


@dataclass(frozen=True, slots=True)
class GrowthObservatoryProjection:
    privacy_class: str
    generated_at: datetime
    analytics_definition_version: str
    landing_view_count: int
    cta_activation_count: int
    signup_count: int
    first_xeed_count: int
    today_view_count: int
    return_visit_count: int
    request_count: int
    accepted_count: int
    consented_count: int
    delivery_count: int
    human_engagement_count: int
    bot_engagement_count: int
    ambiguous_engagement_count: int
    internal_engagement_count: int
    evidence_click_count: int
    recurring_reader_count: int
    paid_conversion_count: int
    additional_xeed_attach_count: int
    advisory_inquiry_count: int
    advisory_close_count: int
    unsubscribe_count: int
    complaint_count: int
    correction_count: int
    conversions: tuple[ConversionView, ...]
    economics: tuple[CohortEconomics, ...]
    classification_counts: tuple[tuple[str, int], ...]
    coverage_notes: tuple[str, ...]


def _require_growth_read(grant: AdminAuthorizationGrant) -> None:
    required = {AdminScope.ACQUISITION_READ, AdminScope.REVENUE_READ}
    missing = required - grant.scopes
    if missing:
        raise PermissionError(
            "growth observatory requires " + ", ".join(sorted(scope.value for scope in missing))
        )


class AdminAnalyticsService:
    def __init__(self, store: AnalyticsStore) -> None:
        self._store = store

    def record(self, event: AnalyticsEvent) -> bool:
        return self._store.append_analytics_event(event)

    def record_event(
        self,
        *,
        event_id: str,
        kind: AnalyticsEventKind,
        occurred_at: datetime,
        classification: TrafficClassification,
        session_ref: str | None = None,
        request_id: str | None = None,
        issue_id: str | None = None,
        account_id: str | None = None,
        xeed_id: str | None = None,
        evidence_ref: str | None = None,
        advisory_ref: str | None = None,
        amount_minor: int | None = None,
        currency: str | None = None,
    ) -> bool:
        return self.record(
            AnalyticsEvent(
                event_id=AnalyticsEventId(event_id),
                kind=kind,
                occurred_at=occurred_at,
                classification=classification,
                session_ref=session_ref,
                request_id=request_id,
                issue_id=issue_id,
                account_id=account_id,
                xeed_id=xeed_id,
                evidence_ref=evidence_ref,
                advisory_ref=advisory_ref,
                amount_minor=amount_minor,
                currency=currency,
            )
        )


def project_growth_observatory(
    *,
    acquisition_store: GrowthAcquisitionStore,
    weekly_store: GrowthWeeklyBriefStore,
    billing_store: BillingStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> GrowthObservatoryProjection:
    _require_growth_read(grant)
    request_ids = sorted({str(event.request_id) for event in acquisition_store.all_events()})
    snapshots = tuple(
        reduce_brief_request(acquisition_store.events_for_request(request_id))
        for request_id in request_ids
    )
    request_by_id = {str(snapshot.request_id): snapshot for snapshot in snapshots}
    analytics = acquisition_store.analytics_events()
    marketing = acquisition_store.marketing_events()

    classifications = Counter(event.classification.value for event in analytics)
    engagements = tuple(
        event
        for event in analytics
        if event.kind in {AnalyticsEventKind.BRIEF_ENGAGED, AnalyticsEventKind.EVIDENCE_CLICKED}
    )
    human_engagement = tuple(
        event for event in engagements if event.classification is TrafficClassification.HUMAN
    )

    readership: dict[str, set[str]] = defaultdict(set)
    for event in analytics:
        if (
            event.kind is AnalyticsEventKind.BRIEF_ENGAGED
            and event.classification is TrafficClassification.HUMAN
            and event.issue_id
        ):
            identity = event.request_id or event.account_id or event.session_ref
            if identity:
                readership[identity].add(event.issue_id)

    links: dict[str, str] = {}
    for event in analytics:
        if event.kind is not AnalyticsEventKind.REQUEST_ACCOUNT_LINKED:
            continue
        assert event.request_id is not None and event.account_id is not None
        previous = links.get(event.request_id)
        if previous is not None and previous != event.account_id:
            raise ValueError("one acquisition request cannot map to multiple paid accounts")
        links[event.request_id] = event.account_id

    conversions: list[ConversionView] = []
    revenue_by_currency: Counter[str] = Counter()
    seen_revenue_events: set[str] = set()
    for request_id, account_id in sorted(links.items()):
        request = request_by_id.get(request_id)
        if request is None:
            continue
        billing_events = billing_store.events_for_account(account_id)
        paid_events = sorted(
            (
                event
                for event in billing_events
                if event.kind is BillingEventKind.INVOICE_PAID
                and event.payment_state is BillingPaymentState.PAID
                and event.provider_created_at >= request.requested_at
            ),
            key=lambda event: event.provider_created_at,
        )
        if not paid_events:
            continue
        first_paid = paid_events[0]
        capacity_events = [event for event in billing_events if event.xeed_capacity is not None]
        xeed_capacity = (
            max(capacity_events, key=lambda event: event.provider_created_at).xeed_capacity
            if capacity_events
            else 1
        )
        assert xeed_capacity is not None
        conversions.append(
            ConversionView(
                request_id=request_id,
                account_id=account_id,
                requested_at=request.requested_at,
                paid_at=first_paid.provider_created_at,
                time_to_conversion_seconds=int(
                    (first_paid.provider_created_at - request.requested_at).total_seconds()
                ),
                xeed_capacity=xeed_capacity,
                additional_xeed_attached=xeed_capacity > 1,
            )
        )
        for billing_event in paid_events:
            event_id = str(billing_event.event_id)
            if (
                event_id in seen_revenue_events
                or billing_event.amount_minor is None
                or billing_event.currency is None
            ):
                continue
            revenue_by_currency[billing_event.currency] += billing_event.amount_minor
            seen_revenue_events.add(event_id)

    cost_by_currency: Counter[str] = Counter()
    for event in analytics:
        if event.kind is AnalyticsEventKind.DELIVERY_COST_RECORDED:
            assert event.amount_minor is not None and event.currency is not None
            cost_by_currency[event.currency] += event.amount_minor

    currencies = sorted(set(revenue_by_currency) | set(cost_by_currency))
    economics = tuple(
        CohortEconomics(
            currency=currency,
            paid_revenue_minor=revenue_by_currency[currency],
            delivery_cost_minor=cost_by_currency[currency],
            gross_contribution_minor=revenue_by_currency[currency] - cost_by_currency[currency],
        )
        for currency in currencies
    )

    advisory_inquiries = {
        event.advisory_ref
        for event in analytics
        if event.kind is AnalyticsEventKind.ADVISORY_INQUIRY and event.advisory_ref
    }
    advisory_closes = {
        event.advisory_ref
        for event in analytics
        if event.kind is AnalyticsEventKind.ADVISORY_CLOSED and event.advisory_ref
    }

    return GrowthObservatoryProjection(
        privacy_class="PRIVATE_AXIGNAL_GROWTH_OBSERVATORY",
        generated_at=generated_at,
        analytics_definition_version="AO14_V1",
        landing_view_count=sum(
            getattr(event, "kind", None) is MarketingEventKind.LANDING_VIEWED for event in marketing
        ),
        cta_activation_count=sum(
            getattr(event, "kind", None) is MarketingEventKind.CTA_ACTIVATED for event in marketing
        ),
        signup_count=sum(event.kind is AnalyticsEventKind.SIGNUP_COMPLETED for event in analytics),
        first_xeed_count=sum(
            event.kind is AnalyticsEventKind.FIRST_XEED_CREATED for event in analytics
        ),
        today_view_count=sum(event.kind is AnalyticsEventKind.TODAY_VIEWED for event in analytics),
        return_visit_count=sum(
            event.kind is AnalyticsEventKind.RETURN_VISIT for event in analytics
        ),
        request_count=len(snapshots),
        accepted_count=sum(
            snapshot.review_state is BriefReviewState.ACCEPTED for snapshot in snapshots
        ),
        consented_count=sum(
            snapshot.consent_state is NewsletterConsentState.GRANTED for snapshot in snapshots
        ),
        delivery_count=len(weekly_store.all_deliveries()),
        human_engagement_count=sum(
            event.classification is TrafficClassification.HUMAN for event in engagements
        ),
        bot_engagement_count=sum(
            event.classification is TrafficClassification.BOT for event in engagements
        ),
        ambiguous_engagement_count=sum(
            event.classification is TrafficClassification.AMBIGUOUS for event in engagements
        ),
        internal_engagement_count=sum(
            event.classification is TrafficClassification.INTERNAL for event in engagements
        ),
        evidence_click_count=sum(
            event.kind is AnalyticsEventKind.EVIDENCE_CLICKED for event in human_engagement
        ),
        recurring_reader_count=sum(len(issue_ids) >= 2 for issue_ids in readership.values()),
        paid_conversion_count=len(conversions),
        additional_xeed_attach_count=sum(item.additional_xeed_attached for item in conversions),
        advisory_inquiry_count=len(advisory_inquiries),
        advisory_close_count=len(advisory_inquiries & advisory_closes),
        unsubscribe_count=sum(
            event.kind is BriefRequestEventKind.CONSENT_WITHDRAWN
            for event in acquisition_store.all_events()
        ),
        complaint_count=sum(
            event.kind is AnalyticsEventKind.COMPLAINT_RECORDED for event in analytics
        ),
        correction_count=len(weekly_store.all_corrections()),
        conversions=tuple(conversions),
        economics=economics,
        classification_counts=tuple(sorted(classifications.items())),
        coverage_notes=(
            "Conversion is reported as observed commercial behavior, never AXIGLAND product truth.",
            "Landing, product and paid sequence is an observed correlation trace, not causal influence.",
            "Bot, ambiguous and internal traffic remain separate from human engagement.",
            "Subscriber content and professional-email values are excluded from analytics events.",
            "Gross contribution is a private commercial projection over observed paid revenue and delivery cost.",
        ),
    )
