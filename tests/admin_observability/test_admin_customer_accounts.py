from datetime import UTC, datetime, timedelta

import pytest

from application.admin_customer_accounts import (
    AdminCustomerAccountService,
    EntitledXeedReader,
    ServiceXeedAccessError,
    project_customer_operations,
    replay_account,
)
from application.xeed_access import AuthorizedXeedReader, TrustedRequestContext
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_billing import BillingAuthorityGrant, BillingProvider
from domain.admin_customer_accounts import (
    AccountStatus,
    AccountUserRole,
    FunnelStage,
    PaymentVerificationState,
    SubscriptionStatus,
)
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.tenancy import Principal, PrincipalTenantMembership, Tenant
from domain.xeed import Xeed
from pipeline.admin_customer_accounts import SqliteAdminCustomerAccountStore
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 10, 2, 5, 30, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _account(store: SqliteAdminCustomerAccountStore) -> AdminCustomerAccountService:
    return AdminCustomerAccountService(store)


def _active_account(
    store: SqliteAdminCustomerAccountStore,
    *,
    capacity: int = 1,
) -> AdminCustomerAccountService:
    service = _account(store)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )
    service.add_user(
        grant=_grant(),
        account_id="account:1",
        user_id="user:owner",
        principal_id="principal:1",
        role=AccountUserRole.OWNER,
        now=NOW + timedelta(seconds=1),
        reason="owner membership",
    )
    service.activate_subscription(
        grant=_grant(),
        account_id="account:1",
        subscription_id="subscription:1",
        xeed_capacity=capacity,
        now=NOW + timedelta(seconds=2),
        reason="service activation before AO-10 payment verification",
    )
    service.apply_billing_payment(
        authority=BillingAuthorityGrant(
            provider=BillingProvider.STRIPE,
            integration_id="stripe-billing",
            provider_event_id="evt_active_account_paid",
            verified_at=NOW + timedelta(seconds=3),
        ),
        account_id="account:1",
        provider_event_id="evt_active_account_paid",
        verified=True,
        now=NOW + timedelta(seconds=3),
        reason="verified billing fixture",
    )
    return service


def test_signup_is_private_service_state_and_payment_remains_unverified(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _account(store)
    snapshot = service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )

    assert snapshot.status is AccountStatus.PENDING
    assert snapshot.subscription_status is SubscriptionStatus.PENDING
    assert snapshot.payment_verification is PaymentVerificationState.EXTERNAL_PENDING
    assert snapshot.entitled_xeed_ids == frozenset()
    assert snapshot.funnel_stages[0][0] is FunnelStage.SIGNUP

    projection = project_customer_operations(
        store=store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.account_count == 1
    assert projection.mrr_eur is None
    assert projection.payment_authority == "STRIPE_VERIFIED_EVENTS"
    assert projection.customers[0].mrr_eur is None
    assert projection.customers[0].pricing_hypothesis_monthly_eur == "9.95"


def test_xeed_capacity_is_enforced_and_plan_expansion_is_explicit(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _active_account(store)
    first = service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:1",
        now=NOW + timedelta(seconds=3),
        reason="first Xeed",
    )
    assert first.entitled_xeed_ids == {"xeed:1"}

    with pytest.raises(ValueError, match="capacity exhausted"):
        service.entitle_xeed(
            grant=_grant(),
            account_id="account:1",
            xeed_id="xeed:2",
            now=NOW + timedelta(seconds=4),
            reason="would exceed plan",
        )

    expanded = service.change_plan_capacity(
        grant=_grant(),
        account_id="account:1",
        xeed_capacity=2,
        now=NOW + timedelta(seconds=5),
        reason="explicit additional Xeed entitlement",
    )
    assert expanded.xeed_capacity == 2
    second = service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:2",
        now=NOW + timedelta(seconds=6),
        reason="second Xeed after expansion",
    )
    assert second.entitled_xeed_ids == {"xeed:1", "xeed:2"}
    projection = project_customer_operations(store=store, grant=_grant(), generated_at=NOW)
    assert projection.customers[0].pricing_hypothesis_monthly_eur == "14.90"


def _xeed_authority() -> tuple[InMemoryXeedAuthority, TrustedRequestContext]:
    authority = InMemoryXeedAuthority()
    principal_id = PrincipalId("principal:1")
    tenant_id = TenantId("tenant:1")
    authority.add_principal(Principal(principal_id))
    authority.add_tenant(Tenant(tenant_id))
    authority.add_membership(PrincipalTenantMembership(principal_id, tenant_id))
    authority.add_xeed(
        Xeed(
            id=XeedId("xeed:1"),
            tenant_id=tenant_id,
            organization_id=OrganizationId("organization:1"),
        )
    )
    return authority, TrustedRequestContext(principal_id=principal_id, tenant_id=tenant_id)


def test_entitlement_is_a_second_server_side_gate_after_tenancy(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _active_account(store)
    authority, context = _xeed_authority()
    reader = EntitledXeedReader(
        AuthorizedXeedReader(authority, authority, authority),
        store,
    )

    with pytest.raises(ServiceXeedAccessError, match="not entitled"):
        reader.read(context, XeedId("xeed:1"))

    service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:1",
        now=NOW + timedelta(seconds=3),
        reason="authorize service Xeed",
    )
    assert reader.read(context, XeedId("xeed:1")).xeed.id == "xeed:1"


def test_suspension_and_cancellation_fail_closed_for_xeed_service_access(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _active_account(store)
    service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:1",
        now=NOW + timedelta(seconds=3),
        reason="authorize service Xeed",
    )
    authority, context = _xeed_authority()
    reader = EntitledXeedReader(
        AuthorizedXeedReader(authority, authority, authority),
        store,
    )
    assert reader.read(context, XeedId("xeed:1")).xeed.id == "xeed:1"

    service.suspend(
        grant=_grant(),
        account_id="account:1",
        now=NOW + timedelta(seconds=4),
        reason="support suspension",
    )
    with pytest.raises(ServiceXeedAccessError, match="not active"):
        reader.read(context, XeedId("xeed:1"))

    service.reactivate(
        grant=_grant(),
        account_id="account:1",
        now=NOW + timedelta(seconds=5),
        reason="suspension resolved",
    )
    assert reader.read(context, XeedId("xeed:1")).xeed.id == "xeed:1"

    cancelled = service.cancel(
        grant=_grant(),
        account_id="account:1",
        now=NOW + timedelta(seconds=6),
        reason="customer cancellation",
        cancellation_reason="CUSTOMER_REQUEST",
    )
    assert cancelled.entitled_xeed_ids == frozenset()
    with pytest.raises(ServiceXeedAccessError, match="not active"):
        reader.read(context, XeedId("xeed:1"))


def test_manual_account_operations_cannot_claim_paid_stage(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _account(store)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )
    service.activate_subscription(
        grant=_grant(),
        account_id="account:1",
        subscription_id="subscription:1",
        xeed_capacity=1,
        now=NOW + timedelta(seconds=1),
        reason="pending billing verification",
    )
    with pytest.raises(ValueError, match="AO-10"):
        service.record_funnel_stage(
            grant=_grant(),
            account_id="account:1",
            stage=FunnelStage.PAID,
            definition_version="activation-v1",
            now=NOW + timedelta(seconds=2),
            reason="must be billing-owned",
        )

    snapshot = service.record_funnel_stage(
        grant=_grant(),
        account_id="account:1",
        stage=FunnelStage.FIRST_MAP_VIEWED,
        definition_version="behavior-v1",
        now=NOW + timedelta(seconds=3),
        reason="first map observed",
    )
    assert FunnelStage.FIRST_MAP_VIEWED in {stage for stage, _ in snapshot.funnel_stages}
    assert FunnelStage.PAID not in {stage for stage, _ in snapshot.funnel_stages}


def test_support_and_claim_review_references_are_replayable(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _active_account(store)
    service.add_support_reference(
        grant=_grant(AdminRole.SUPPORT),
        account_id="account:1",
        reference="support:case:17",
        now=NOW + timedelta(seconds=3),
        reason="customer support case",
    )
    snapshot = service.add_claim_review_reference(
        grant=_grant(AdminRole.SUPPORT),
        account_id="account:1",
        reference="claim-review:9",
        now=NOW + timedelta(seconds=4),
        reason="subscriber correction request",
    )
    assert snapshot.support_refs == ("support:case:17",)
    assert snapshot.claim_review_refs == ("claim-review:9",)

    replayed = replay_account(store.for_account(snapshot.account_id))
    assert replayed == snapshot


def test_sqlite_event_id_is_idempotent_but_conflicting_reuse_fails(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _account(store)
    snapshot = service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )
    event = store.for_account(snapshot.account_id)[0]
    assert store.append(event) is False

    from dataclasses import replace

    with pytest.raises(ValueError, match="different immutable content"):
        store.append(replace(event, reason="different"))


def test_business_role_can_operate_customer_account_but_support_cannot_activate(tmp_path) -> None:
    store = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    service = _account(store)
    service.signup(
        grant=_grant(AdminRole.BUSINESS),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )
    with pytest.raises(PermissionError, match="admin:customers:write"):
        service.activate_subscription(
            grant=_grant(AdminRole.SUPPORT),
            account_id="account:1",
            subscription_id="subscription:1",
            xeed_capacity=1,
            now=NOW + timedelta(seconds=1),
            reason="support must not activate subscriptions",
        )
