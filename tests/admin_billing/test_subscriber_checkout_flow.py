from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionLifecycle,
)
from application.admin_billing.subscriber_checkout import (
    AuthorizedPurchaseScope,
    CapacityIncreaseCommand,
    CapacityUpdateResponse,
    CreatedCheckoutSession,
    EntitlementSnapshot,
    InitialCheckoutCommand,
    ProviderCurrentSubscription,
    PurchaseFailure,
    SubscriberCheckoutError,
    SubscriberCheckoutService,
)
from application.admin_billing.subscriber_checkout import (
    ProviderCheckoutBinding as _CheckoutFacts,
)
from application.admin_billing.subscriber_reconciliation import (
    ReconciliationDisposition,
    SubscriberPurchaseReconciler,
)
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedRecurringOffer,
    ApprovedTaxConfiguration,
    CheckoutAttemptBinding,
    CurrentSubscriptionItems,
    NormalizedRecurringItem,
    PurchaseIntent,
    RecurringTerms,
    SnapshotCurrentness,
    SubscriptionItemSnapshot,
)
from domain.identity import PrincipalId, TenantId
from domain.tenancy.model import Principal
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore

NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)
CATALOGUE = ApprovedOfferCatalogue(
    "catalogue_fixture",
    "v1",
    ApprovedRecurringOffer("base", RecurringTerms("month", 1, "EUR", 995)),
    ApprovedRecurringOffer("addon", RecurringTerms("month", 1, "EUR", 495)),
    ApprovedTaxConfiguration(
        "tax-fixture-config",
        "stripe-live-fixture",
        ("tax-registration-fixture",),
        True,
        NOW,
        NOW + timedelta(days=1),
    ),
)


class _Authority:
    def resolve(self, principal, tenant_id, *, now):
        return AuthorizedPurchaseScope(
            principal.id,
            tenant_id,
            "owner-check",
            "membership-check",
            now,
        )


class _Entitlement:
    def __init__(self, provider):
        self.provider = provider

    def snapshot(self, tenant_id):
        if self.provider.entitled_capacity is None:
            return None
        return EntitlementSnapshot(
            tenant_id,
            self.provider.entitled_capacity,
            "CURRENT",
            "entitlement:evidence",
            NOW + timedelta(days=30),
        )


class _Catalogue:
    def resolve(self, environment_ref):
        return CATALOGUE


class _Provider:
    def __init__(
        self, payment_state: PaymentState = PaymentState.VERIFIED, *, fail_create_once=False
    ):
        self.payment_state = payment_state
        self.created_intent: PurchaseIntent | None = None
        self.fail_create_once = fail_create_once
        self.checkout_create_keys: list[str] = []
        self.capacity: int | None = None
        self.entitled_capacity: int | None = None
        self.current_state_at = NOW + timedelta(seconds=3)
        self.current_lifecycle = SubscriptionLifecycle.ELIGIBLE
        self.current_paid_through = NOW + timedelta(days=30)
        self.current_invoice_ref: str | None = "in_fixture"
        self.capacity_updates: list[tuple[int, str | None, str, str]] = []

    def create_initial_checkout(self, intent, catalogue, *, idempotency_key):
        self.checkout_create_keys.append(idempotency_key)
        if self.fail_create_once:
            self.fail_create_once = False
            raise RuntimeError("fixture provider timeout")
        self.created_intent = intent
        return CreatedCheckoutSession("cs_fixture", None, None, "https://checkout.stripe.com/c/pay")

    def read_checkout_binding(self, attempt):
        self.capacity = attempt.desired_total
        items = [NormalizedRecurringItem("si_base", "base", 1, True, CATALOGUE.base_offer.terms)]
        if attempt.desired_total > 1:
            items.append(
                NormalizedRecurringItem(
                    "si_addon",
                    "addon",
                    attempt.desired_total - 1,
                    True,
                    CATALOGUE.additional_xeed_offer.terms,
                )
            )
        item_tuple = tuple(items)
        state_at = attempt.authorized_at + timedelta(seconds=1)
        snapshot = SubscriptionItemSnapshot(
            evidence_ref="evidence:checkout",
            checkout_session_ref="cs_fixture",
            customer_ref="cus_fixture",
            subscription_ref="sub_fixture",
            environment_ref="stripe-live-fixture",
            provider_state_ref="checkout-created:fixture",
            provider_state_at=state_at,
            retrieved_at=state_at + timedelta(seconds=1),
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            metadata_intent_ref=attempt.intent_ref,
            items=item_tuple,
        )
        current = CurrentSubscriptionItems(
            evidence_ref="evidence:subscription",
            customer_ref="cus_fixture",
            subscription_ref="sub_fixture",
            environment_ref="stripe-live-fixture",
            provider_state_ref="subscription-updated:fixture",
            provider_state_at=state_at,
            retrieved_at=state_at + timedelta(seconds=1),
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=item_tuple,
        )
        return _CheckoutFacts(
            CheckoutAttemptBinding(
                "binding:fixture",
                attempt.intent_ref,
                attempt.attempt_ref,
                "cs_fixture",
                "cus_fixture",
                "sub_fixture",
                "stripe-live-fixture",
                attempt.authorized_at,
            ),
            snapshot,
            current,
            self.payment_state,
            SubscriptionLifecycle.ELIGIBLE,
            NOW + timedelta(days=30),
            "in_fixture",
        )

    def read_current_subscription(self, projection):
        capacity = self.capacity or projection.effective_capacity or 1
        items = [NormalizedRecurringItem("si_base", "base", 1, True, CATALOGUE.base_offer.terms)]
        if capacity > 1:
            items.append(
                NormalizedRecurringItem(
                    "si_addon", "addon", capacity - 1, True, CATALOGUE.additional_xeed_offer.terms
                )
            )
        state_at = self.current_state_at
        snapshot = CurrentSubscriptionItems(
            evidence_ref=f"evidence:subscription:{capacity}:{state_at.isoformat()}",
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            environment_ref=projection.environment_ref,
            provider_state_ref=f"subscription:{capacity}:{state_at.isoformat()}",
            provider_state_at=state_at,
            retrieved_at=max(NOW + timedelta(seconds=6), state_at + timedelta(seconds=1)),
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=tuple(items),
        )
        return ProviderCurrentSubscription(
            snapshot=snapshot,
            payment_state=self.payment_state,
            lifecycle=self.current_lifecycle,
            paid_through=self.current_paid_through,
            additional_item_ref=None if capacity == 1 else "si_addon",
            invoice_ref=self.current_invoice_ref,
        )

    def update_capacity(self, *args, **kwargs):
        self.capacity_updates.append(
            (
                kwargs["desired_total"],
                kwargs["additional_item_ref"],
                kwargs["proration_behavior"],
                kwargs["payment_behavior"],
            )
        )
        self.capacity = kwargs["desired_total"]
        self.current_state_at = NOW + timedelta(seconds=8)
        self.current_invoice_ref = "in_proration_fixture"
        return CapacityUpdateResponse(
            "sub_fixture",
            "cus_fixture",
            "si_addon",
            "in_proration_fixture",
            "https://invoice.stripe.com/i/fixture",
            True,
        )


@pytest.mark.parametrize("desired_total", [1, 2, 100])
def test_initial_checkout_reconciles_only_paid_exact_capacity(tmp_path, desired_total):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / f"subscriber-{desired_total}.sqlite3")
    provider = _Provider()
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
    )
    started = service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand(f"request-{desired_total}", desired_total),
        now=NOW,
    )
    assert started.status.value == "PENDING_PURCHASE"
    assert started.effective_capacity is None
    assert provider.created_intent is not None
    assert provider.created_intent.xeed_capacity == desired_total

    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=_Catalogue(),
        environment_ref="stripe-live-fixture",
    )
    outcome = reconciler.reconcile_session("cs_fixture", now=NOW + timedelta(seconds=2))

    assert outcome is ReconciliationDisposition.COMPLETE
    projection = store.get_billing_projection(tenant_id)
    assert projection is not None
    assert projection.effective_capacity == desired_total
    provider.entitled_capacity = desired_total
    assert store.get_attempt(tenant_id, f"request-{desired_total}").status.value == "COMPLETE"


def test_checkout_completed_without_paid_invoice_keeps_capacity_unknown(tmp_path):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber-unpaid.sqlite3")
    provider = _Provider(payment_state=PaymentState.UNKNOWN)
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
    )
    service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand("request-unpaid", 2),
        now=NOW,
    )
    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=_Catalogue(),
        environment_ref="stripe-live-fixture",
    )

    assert (
        reconciler.reconcile_session("cs_fixture", now=NOW + timedelta(seconds=2))
        is ReconciliationDisposition.PENDING_PURCHASE
    )
    assert store.get_billing_projection(tenant_id) is None


def test_checkout_fails_closed_without_confirmed_tax_registration(tmp_path):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / "tax-unknown.sqlite3")
    provider = _Provider()

    class MissingTaxCatalogue:
        def resolve(self, environment_ref):
            return ApprovedOfferCatalogue(
                CATALOGUE.catalogue_ref,
                CATALOGUE.version,
                CATALOGUE.base_offer,
                CATALOGUE.additional_xeed_offer,
                None,
            )

    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=MissingTaxCatalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
    )

    with pytest.raises(SubscriberCheckoutError) as error:
        service.start_initial_checkout(
            principal=principal,
            tenant_id=tenant_id,
            command=InitialCheckoutCommand("tax-unknown", 1),
            now=NOW,
        )

    assert error.value.failure is PurchaseFailure.TAX_CONFIGURATION_UNKNOWN
    assert store.list_pending_attempts(tenant_id) == ()
    assert provider.checkout_create_keys == []


def test_prepared_checkout_recovers_with_same_provider_idempotency_key(tmp_path):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / "prepared-retry.sqlite3")
    provider = _Provider(fail_create_once=True)
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
    )

    with pytest.raises(RuntimeError, match="fixture provider timeout"):
        service.start_initial_checkout(
            principal=principal,
            tenant_id=tenant_id,
            command=InitialCheckoutCommand("prepared-retry", 2),
            now=NOW,
        )
    prepared = store.get_attempt(tenant_id, "prepared-retry")
    assert prepared.status.value == "PREPARED"
    retry_result = service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand("prepared-retry", 2),
        now=NOW + timedelta(seconds=1),
    )

    assert retry_result.status.value == "PENDING_PURCHASE"
    assert provider.checkout_create_keys == [prepared.idempotency_key, prepared.idempotency_key]
    assert store.get_attempt(tenant_id, "prepared-retry").checkout_session_ref == "cs_fixture"


@pytest.mark.parametrize("desired_total", [2, 100])
def test_capacity_expansion_updates_same_subscription_once_and_waits_for_reconciliation(
    tmp_path, desired_total
):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / f"capacity-{desired_total}.sqlite3")
    provider = _Provider()
    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=_Catalogue(),
        environment_ref="stripe-live-fixture",
    )
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
        reconciler=reconciler,
    )
    service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand("initial", 1),
        now=NOW,
    )
    assert (
        reconciler.reconcile_session("cs_fixture", now=NOW + timedelta(seconds=2))
        is ReconciliationDisposition.COMPLETE
    )
    provider.entitled_capacity = 1

    requested = service.request_capacity_increase(
        principal=principal,
        tenant_id=tenant_id,
        command=CapacityIncreaseCommand("expand", desired_total),
        now=NOW + timedelta(seconds=7),
    )
    duplicate = service.request_capacity_increase(
        principal=principal,
        tenant_id=tenant_id,
        command=CapacityIncreaseCommand("expand", desired_total),
        now=NOW + timedelta(seconds=7),
    )
    second_click = service.request_capacity_increase(
        principal=principal,
        tenant_id=tenant_id,
        command=CapacityIncreaseCommand("expand-second-click", desired_total),
        now=NOW + timedelta(seconds=7),
    )

    assert requested.status.value == "PENDING_PURCHASE"
    assert requested.effective_capacity == 1
    assert duplicate.intent_ref == requested.intent_ref
    assert second_click.intent_ref == requested.intent_ref
    assert provider.created_intent is not None and provider.created_intent.xeed_capacity == 1
    assert provider.capacity_updates == [
        (desired_total, None, "always_invoice", "pending_if_incomplete")
    ]
    assert store.get_billing_projection(tenant_id).effective_capacity == 1

    result = service.reconcile_pending(
        principal=principal,
        tenant_id=tenant_id,
        now=NOW + timedelta(seconds=9),
    )

    assert result == (ReconciliationDisposition.COMPLETE.value,)
    assert store.get_billing_projection(tenant_id).effective_capacity == desired_total
    provider.entitled_capacity = desired_total


@pytest.mark.parametrize("current_invoice_ref", ["unrelated_paid_invoice", None])
def test_capacity_expansion_requires_exact_paid_attempt_invoice(tmp_path, current_invoice_ref):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(
        tmp_path / f"invoice-mismatch-{current_invoice_ref}.sqlite3"
    )
    provider = _Provider()
    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=_Catalogue(),
        environment_ref="stripe-live-fixture",
    )
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
        reconciler=reconciler,
    )
    service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand("initial", 1),
        now=NOW,
    )
    assert (
        reconciler.reconcile_session("cs_fixture", now=NOW + timedelta(seconds=2))
        is ReconciliationDisposition.COMPLETE
    )
    provider.entitled_capacity = 1
    service.request_capacity_increase(
        principal=principal,
        tenant_id=tenant_id,
        command=CapacityIncreaseCommand("expand", 2),
        now=NOW + timedelta(seconds=7),
    )
    attempt = store.get_attempt(tenant_id, "expand")
    assert attempt is not None
    assert attempt.invoice_ref == "in_proration_fixture"

    provider.current_invoice_ref = current_invoice_ref
    result = reconciler.reconcile_attempt(tenant_id, "expand", now=NOW + timedelta(seconds=9))

    assert result is ReconciliationDisposition.UNKNOWN
    attempt = store.get_attempt(tenant_id, "expand")
    projection = store.get_billing_projection(tenant_id)
    assert attempt is not None and attempt.status.value == "PENDING_PURCHASE"
    assert projection is not None and projection.effective_capacity == 1

    outcomes = service.reconcile_pending(
        principal=principal,
        tenant_id=tenant_id,
        now=NOW + timedelta(seconds=10),
    )

    assert "COMPLETE" not in outcomes
    attempt = store.get_attempt(tenant_id, "expand")
    projection = store.get_billing_projection(tenant_id)
    assert attempt is not None and attempt.status.value == "PENDING_PURCHASE"
    assert projection is not None and projection.effective_capacity != 2


def test_refresh_recovers_transient_unknown_and_respects_paid_through_lifecycle(tmp_path):
    tenant_id = TenantId("tenant_fixture")
    principal = Principal(PrincipalId("principal_fixture"))
    store = SqliteSubscriberBillingStore(tmp_path / "refresh-lifecycle.sqlite3")
    provider = _Provider()
    service = SubscriberCheckoutService(
        authority_reader=_Authority(),
        entitlement_reader=_Entitlement(provider),
        catalogue_reader=_Catalogue(),
        store=store,
        provider=provider,
        environment_ref="stripe-live-fixture",
    )
    service.start_initial_checkout(
        principal=principal,
        tenant_id=tenant_id,
        command=InitialCheckoutCommand("initial", 1),
        now=NOW,
    )
    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=_Catalogue(),
        environment_ref="stripe-live-fixture",
    )
    assert (
        reconciler.reconcile_session("cs_fixture", now=NOW + timedelta(seconds=2))
        is ReconciliationDisposition.COMPLETE
    )
    assert (
        reconciler.refresh_current_projection(tenant_id, now=NOW + timedelta(seconds=4))
        is ReconciliationDisposition.COMPLETE
    )
    store.mark_projection_unknown(tenant_id)
    unknown = store.get_billing_projection(tenant_id)
    assert unknown.effective_capacity is None
    assert unknown.binding.effective_capacity == 1
    assert (
        reconciler.refresh_current_projection(tenant_id, now=NOW + timedelta(seconds=5))
        is ReconciliationDisposition.COMPLETE
    )
    assert store.get_billing_projection(tenant_id).effective_capacity == 1

    provider.current_lifecycle = SubscriptionLifecycle.CANCEL_AT_PERIOD_END
    provider.current_paid_through = NOW + timedelta(days=2)
    provider.current_state_at = NOW + timedelta(seconds=6)
    assert (
        reconciler.refresh_current_projection(tenant_id, now=NOW + timedelta(days=1))
        is ReconciliationDisposition.COMPLETE
    )
    assert store.get_billing_projection(tenant_id).effective_capacity == 1

    provider.current_lifecycle = SubscriptionLifecycle.CANCELED
    provider.current_paid_through = NOW + timedelta(days=2)
    provider.current_state_at = NOW + timedelta(seconds=7)
    assert (
        reconciler.refresh_current_projection(tenant_id, now=NOW + timedelta(days=3))
        is ReconciliationDisposition.UNKNOWN
    )
    assert store.get_billing_projection(tenant_id).effective_capacity is None
