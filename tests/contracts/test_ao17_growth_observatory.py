from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_acquisition import AdminAnalyticsService, project_growth_observatory
from application.admin_acquisition.marketing_service import PublicMarketingEventService
from application.admin_acquisition.public_service import PublicBriefRequestService
from application.admin_acquisition.review_service import AdminBriefReviewService
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_acquisition import (
    AnalyticsEvent,
    AnalyticsEventId,
    AnalyticsEventKind,
    MarketingEventKind,
    TrafficClassification,
)
from domain.admin_billing import (
    BillingEvent,
    BillingEventId,
    BillingEventKind,
    BillingMapping,
    BillingPaymentState,
    BillingProvider,
    BillingSubscriptionState,
    ExternalCustomerId,
    ExternalSubscriptionId,
)
from domain.admin_weekly_brief import (
    WeeklyBriefCorrection,
    WeeklyBriefDelivery,
    WeeklyBriefIssue,
    WeeklyBriefIssueKind,
)
from pipeline.admin_acquisition import AcquisitionStoreConflict, SqliteAdminAcquisitionStore
from pipeline.admin_billing import SqliteAdminBillingStore
from pipeline.admin_weekly_brief import SqliteWeeklyBriefStore

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _eligible_request(store: SqliteAdminAcquisitionStore) -> None:
    PublicBriefRequestService(store).submit(
        request_id="brief:1",
        company_name="Acme Industrial",
        company_domain="acme.example",
        professional_email="private@acme.example",
        purpose="Receive evidence-backed observation updates.",
        request_notice_version="brief-request-v1",
        newsletter_consent=True,
        newsletter_notice_version="newsletter-v1",
        now=NOW,
    )
    AdminBriefReviewService(store).accept(
        grant=_grant(),
        request_id="brief:1",
        subject_reference="organization:acme",
        reason="Resolvable subject with sufficient public coverage.",
        now=NOW + timedelta(minutes=1),
    )


def _issue(issue_id: str, created_at: datetime) -> WeeklyBriefIssue:
    return WeeklyBriefIssue(
        issue_id=issue_id,
        request_id="brief:1",
        subject_reference="organization:acme",
        issue_version="v1",
        composition_policy_id="weekly-brief-composition",
        composition_policy_version="v1",
        created_at=created_at,
        kind=WeeklyBriefIssueKind.NO_MATERIAL_CHANGE,
        items=(),
        evidence_fingerprint="sha256:empty",
    )


def _billing(store: SqliteAdminBillingStore) -> None:
    store.register_mapping(
        BillingMapping(
            account_id="account:1",
            provider=BillingProvider.STRIPE,
            external_customer_id=ExternalCustomerId("cus_1"),
            external_subscription_id=ExternalSubscriptionId("sub_1"),
            base_price_ref="price_base",
            additional_xeed_price_ref="price_extra",
            created_at=NOW + timedelta(hours=1),
        )
    )
    store.append_event(
        BillingEvent(
            event_id=BillingEventId("billing:capacity"),
            provider=BillingProvider.STRIPE,
            provider_event_type="customer.subscription.updated",
            provider_created_at=NOW + timedelta(days=1),
            recorded_at=NOW + timedelta(days=1, seconds=1),
            external_object_id="sub_1",
            account_id="account:1",
            kind=BillingEventKind.SUBSCRIPTION_SYNCED,
            subscription_state=BillingSubscriptionState.ACTIVE,
            xeed_capacity=3,
        )
    )
    store.append_event(
        BillingEvent(
            event_id=BillingEventId("billing:paid"),
            provider=BillingProvider.STRIPE,
            provider_event_type="invoice.paid",
            provider_created_at=NOW + timedelta(days=2),
            recorded_at=NOW + timedelta(days=2, seconds=1),
            external_object_id="in_1",
            account_id="account:1",
            kind=BillingEventKind.INVOICE_PAID,
            payment_state=BillingPaymentState.PAID,
            amount_minor=1990,
            currency="eur",
        )
    )


def test_ao14_events_are_versioned_classified_and_replay_safe(tmp_path: Path) -> None:
    store = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    service = AdminAnalyticsService(store)
    event = AnalyticsEvent(
        event_id=AnalyticsEventId("analytics:return:1"),
        kind=AnalyticsEventKind.RETURN_VISIT,
        occurred_at=NOW,
        classification=TrafficClassification.HUMAN,
        session_ref="session:opaque:1",
    )
    assert service.record(event) is True
    assert service.record(event) is False
    assert store.analytics_events() == (event,)
    assert store.analytics_events()[0].definition_version == "AO14_V1"

    with pytest.raises(AcquisitionStoreConflict):
        service.record(
            AnalyticsEvent(
                event_id=AnalyticsEventId("analytics:return:1"),
                kind=AnalyticsEventKind.RETURN_VISIT,
                occurred_at=NOW,
                classification=TrafficClassification.BOT,
                session_ref="session:opaque:1",
            )
        )


def test_ao17_projects_funnel_conversion_attach_engagement_and_economics(tmp_path: Path) -> None:
    acquisition = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    weekly = SqliteWeeklyBriefStore(tmp_path / "weekly.sqlite3")
    billing = SqliteAdminBillingStore(tmp_path / "billing.sqlite3")
    _eligible_request(acquisition)
    _billing(billing)

    weekly.put_issue(_issue("issue:1", NOW + timedelta(hours=2)))
    weekly.put_issue(_issue("issue:2", NOW + timedelta(days=7)))
    weekly.put_delivery(
        WeeklyBriefDelivery(
            delivery_id="delivery:1",
            issue_id="issue:1",
            delivered_at=NOW + timedelta(hours=3),
            integration_id="email-provider",
            provider_message_ref="message:1",
        )
    )
    weekly.put_correction(
        WeeklyBriefCorrection(
            correction_id="correction:1",
            issue_id="issue:1",
            occurred_at=NOW + timedelta(hours=4),
            actor_principal_id="admin:founder",
            reason="source correction",
            note="Corrected delivery note without rewriting history.",
        )
    )

    marketing = PublicMarketingEventService(acquisition)
    marketing.ingest(
        event_id="marketing:landing:1",
        session_ref="session:opaque:1",
        kind=MarketingEventKind.LANDING_VIEWED,
        occurred_at=NOW,
        received_at=NOW,
        surface="landing",
        locale="es",
        path="/",
    )
    marketing.ingest(
        event_id="marketing:cta:1",
        session_ref="session:opaque:1",
        kind=MarketingEventKind.CTA_ACTIVATED,
        occurred_at=NOW + timedelta(seconds=10),
        received_at=NOW + timedelta(seconds=10),
        surface="landing",
        locale="es",
        path="/",
        cta="signup",
    )

    analytics = AdminAnalyticsService(acquisition)
    analytics.record_event(
        event_id="analytics:signup:1",
        kind=AnalyticsEventKind.SIGNUP_COMPLETED,
        occurred_at=NOW + timedelta(hours=1),
        classification=TrafficClassification.HUMAN,
        session_ref="session:opaque:1",
        account_id="account:1",
    )
    analytics.record_event(
        event_id="analytics:first-xeed:1",
        kind=AnalyticsEventKind.FIRST_XEED_CREATED,
        occurred_at=NOW + timedelta(hours=2),
        classification=TrafficClassification.HUMAN,
        account_id="account:1",
        xeed_id="xeed:1",
    )
    analytics.record_event(
        event_id="analytics:today:1",
        kind=AnalyticsEventKind.TODAY_VIEWED,
        occurred_at=NOW + timedelta(hours=3),
        classification=TrafficClassification.HUMAN,
        account_id="account:1",
        xeed_id="xeed:1",
    )
    analytics.record_event(
        event_id="analytics:return:1",
        kind=AnalyticsEventKind.RETURN_VISIT,
        occurred_at=NOW + timedelta(days=1),
        classification=TrafficClassification.HUMAN,
        account_id="account:1",
    )
    events = (
        (
            "analytics:read:1",
            AnalyticsEventKind.BRIEF_ENGAGED,
            "issue:1",
            TrafficClassification.HUMAN,
        ),
        (
            "analytics:read:2",
            AnalyticsEventKind.BRIEF_ENGAGED,
            "issue:2",
            TrafficClassification.HUMAN,
        ),
        ("analytics:bot:1", AnalyticsEventKind.BRIEF_ENGAGED, "issue:1", TrafficClassification.BOT),
    )
    for event_id, kind, issue_id, classification in events:
        analytics.record_event(
            event_id=event_id,
            kind=kind,
            occurred_at=NOW + timedelta(days=8),
            classification=classification,
            request_id="brief:1",
            issue_id=issue_id,
        )
    analytics.record_event(
        event_id="analytics:evidence:1",
        kind=AnalyticsEventKind.EVIDENCE_CLICKED,
        occurred_at=NOW + timedelta(days=8, minutes=1),
        classification=TrafficClassification.HUMAN,
        request_id="brief:1",
        issue_id="issue:2",
        evidence_ref="source:public:1",
    )
    analytics.record_event(
        event_id="analytics:conversion:1",
        kind=AnalyticsEventKind.REQUEST_ACCOUNT_LINKED,
        occurred_at=NOW + timedelta(days=2),
        classification=TrafficClassification.HUMAN,
        request_id="brief:1",
        account_id="account:1",
    )
    analytics.record_event(
        event_id="analytics:advisory:inquiry",
        kind=AnalyticsEventKind.ADVISORY_INQUIRY,
        occurred_at=NOW + timedelta(days=3),
        classification=TrafficClassification.HUMAN,
        account_id="account:1",
        advisory_ref="advisory:1",
    )
    analytics.record_event(
        event_id="analytics:advisory:close",
        kind=AnalyticsEventKind.ADVISORY_CLOSED,
        occurred_at=NOW + timedelta(days=4),
        classification=TrafficClassification.HUMAN,
        account_id="account:1",
        advisory_ref="advisory:1",
    )
    analytics.record_event(
        event_id="analytics:complaint:1",
        kind=AnalyticsEventKind.COMPLAINT_RECORDED,
        occurred_at=NOW + timedelta(days=5),
        classification=TrafficClassification.HUMAN,
        request_id="brief:1",
    )
    analytics.record_event(
        event_id="analytics:cost:1",
        kind=AnalyticsEventKind.DELIVERY_COST_RECORDED,
        occurred_at=NOW + timedelta(days=5),
        classification=TrafficClassification.INTERNAL,
        request_id="brief:1",
        issue_id="issue:1",
        amount_minor=40,
        currency="eur",
    )
    PublicBriefRequestService(acquisition).withdraw_consent(
        request_id="brief:1",
        now=NOW + timedelta(days=9),
    )

    projection = project_growth_observatory(
        acquisition_store=acquisition,
        weekly_store=weekly,
        billing_store=billing,
        grant=_grant(),
        generated_at=NOW + timedelta(days=10),
    )

    assert projection.landing_view_count == 1
    assert projection.cta_activation_count == 1
    assert projection.signup_count == 1
    assert projection.first_xeed_count == 1
    assert projection.today_view_count == 1
    assert projection.return_visit_count == 1
    assert projection.request_count == 1
    assert projection.accepted_count == 1
    assert projection.consented_count == 0
    assert projection.delivery_count == 1
    assert projection.human_engagement_count == 3
    assert projection.bot_engagement_count == 1
    assert projection.ambiguous_engagement_count == 0
    assert projection.evidence_click_count == 1
    assert projection.recurring_reader_count == 1
    assert projection.paid_conversion_count == 1
    assert projection.additional_xeed_attach_count == 1
    assert projection.advisory_inquiry_count == 1
    assert projection.advisory_close_count == 1
    assert projection.unsubscribe_count == 1
    assert projection.complaint_count == 1
    assert projection.correction_count == 1
    assert projection.conversions[0].time_to_conversion_seconds == 172800
    assert projection.conversions[0].xeed_capacity == 3
    assert projection.economics[0].currency == "EUR"
    assert projection.economics[0].paid_revenue_minor == 1990
    assert projection.economics[0].delivery_cost_minor == 40
    assert projection.economics[0].gross_contribution_minor == 1950
    assert "private@acme.example" not in repr(projection)
    assert any("never AXIGLAND product truth" in note for note in projection.coverage_notes)


def test_growth_observatory_requires_acquisition_and_revenue_scope(tmp_path: Path) -> None:
    acquisition = SqliteAdminAcquisitionStore(tmp_path / "acquisition.sqlite3")
    weekly = SqliteWeeklyBriefStore(tmp_path / "weekly.sqlite3")
    billing = SqliteAdminBillingStore(tmp_path / "billing.sqlite3")
    with pytest.raises(PermissionError, match="growth observatory requires"):
        project_growth_observatory(
            acquisition_store=acquisition,
            weekly_store=weekly,
            billing_store=billing,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )
