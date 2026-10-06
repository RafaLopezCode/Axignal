from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.admin_billing.subscriber_billing import PaymentState, SubscriptionLifecycle
from application.admin_billing.subscriber_checkout import (
    AttemptKind,
    AttemptStatus,
    BillingProjection,
    PurchaseAttempt,
)
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedRecurringOffer,
    ApprovedTaxConfiguration,
    RecurringTerms,
)
from domain.identity import PrincipalId, TenantId
from pipeline.admin_billing.stripe_subscriber import (
    StripeSubscriberAdapter,
    StripeSubscriberConfig,
    StripeSubscriberConflict,
    StripeSubscriberError,
)


class _PagedTransport:
    def __init__(
        self,
        *,
        malformed_session_page: bool = False,
        refunded: bool = False,
        disputed: bool = False,
        tax_enabled: bool = True,
    ) -> None:
        self.malformed_session_page = malformed_session_page
        self.refunded = refunded
        self.disputed = disputed
        self.tax_enabled = tax_enabled
        self.calls: list[str] = []
        self.requests: list[tuple[str, str, dict[str, str], str | None]] = []
        self.price_base = {
            "id": "price_base",
            "active": True,
            "livemode": True,
            "billing_scheme": "per_unit",
            "type": "recurring",
            "transform_quantity": None,
            "tiers_mode": None,
            "tax_behavior": "exclusive",
            "recurring": {"interval": "month", "interval_count": 1},
            "currency": "eur",
            "unit_amount": 995,
        }
        self.price_addon = {
            "id": "price_addon",
            "active": True,
            "livemode": True,
            "billing_scheme": "per_unit",
            "type": "recurring",
            "transform_quantity": None,
            "tiers_mode": None,
            "tax_behavior": "exclusive",
            "recurring": {"interval": "month", "interval_count": 1},
            "currency": "eur",
            "unit_amount": 495,
        }

    def request(self, method, path, *, parameters, idempotency_key=None):
        self.requests.append((method, path, dict(parameters), idempotency_key))
        self.calls.append(
            path
            + ("?after=" + parameters["starting_after"] if "starting_after" in parameters else "")
        )
        if path == "/v1/account":
            return {"id": "acct_fixture"}
        if path == "/v1/prices/price_base":
            return self.price_base
        if path == "/v1/prices/price_addon":
            return self.price_addon
        if path == "/v1/checkout/sessions/cs_fixture":
            return {
                "id": "cs_fixture",
                "livemode": True,
                "mode": "subscription",
                "status": "complete",
                "client_reference_id": "intent_fixture",
                "customer": "cus_fixture",
                "subscription": "sub_fixture",
                "automatic_tax": {"enabled": self.tax_enabled},
                "created": 1791244800,
                "metadata": {
                    "axignal_intent_ref": "intent_fixture",
                    "axignal_attempt_ref": "attempt_fixture",
                },
            }
        if path == "/v1/checkout/sessions/cs_fixture/line_items":
            if self.malformed_session_page:
                return {"data": [{"id": "si_base", "price": self.price_base, "quantity": 1}]}
            if parameters.get("starting_after") == "li_base":
                return {"data": [self._line("li_addon", self.price_addon, 99)], "has_more": False}
            return {
                "data": [self._line("li_base", self.price_base, 1)],
                "has_more": True,
            }
        if path == "/v1/subscriptions/sub_fixture":
            return {
                "id": "sub_fixture",
                "customer": "cus_fixture",
                "livemode": True,
                "status": "active",
                "cancel_at_period_end": False,
                "updated": 1791244800,
                "current_period_end": 1793836800,
                "latest_invoice": "in_fixture",
                "automatic_tax": {"enabled": self.tax_enabled},
            }
        if path == "/v1/subscription_items":
            if method == "POST":
                return {"id": "si_addon"}
            if parameters.get("starting_after") == "si_base":
                return {"data": [self._item("si_addon", self.price_addon, 99)], "has_more": False}
            return {
                "data": [self._item("si_base", self.price_base, 1)],
                "has_more": True,
            }
        if path == "/v1/invoices/in_fixture":
            return {
                "id": "in_fixture",
                "customer": "cus_fixture",
                "subscription": "sub_fixture",
                "livemode": True,
                "status": "paid",
                "automatic_tax": {"enabled": self.tax_enabled},
                "payment_intent": "pi_fixture",
                "status_transitions": {"paid_at": 1791244800},
            }
        if path == "/v1/payment_intents/pi_fixture":
            return {
                "id": "pi_fixture",
                "livemode": True,
                "status": "succeeded",
                "latest_charge": "ch_fixture",
                "created": 1791244800,
            }
        if path == "/v1/charges/ch_fixture":
            return {
                "id": "ch_fixture",
                "livemode": True,
                "payment_intent": "pi_fixture",
                "amount_refunded": 1000 if self.refunded else 0,
                "refunded": self.refunded,
                "disputed": self.disputed,
            }
        if path == "/v1/disputes":
            return {
                "data": [{"id": "dp_fixture"}] if self.disputed else [],
                "has_more": False,
            }
        raise AssertionError(f"unexpected Stripe fixture request: {method} {path}")

    @staticmethod
    def _line(item_ref, price, quantity):
        return {"id": item_ref, "price": price, "quantity": quantity}

    @staticmethod
    def _item(item_ref, price, quantity):
        return {"id": item_ref, "price": price, "quantity": quantity}


def _setup(
    malformed_session_page: bool = False,
    *,
    refunded: bool = False,
    disputed: bool = False,
    tax_enabled: bool = True,
    mutations_enabled: bool = False,
):
    now = datetime(2026, 10, 6, tzinfo=UTC)
    transport = _PagedTransport(
        malformed_session_page=malformed_session_page,
        refunded=refunded,
        disputed=disputed,
        tax_enabled=tax_enabled,
    )
    config = StripeSubscriberConfig(
        environment_ref="stripe-live-fixture",
        account_ref="acct_fixture",
        live_mode=True,
        api_version="2025-06-30.basil",
        base_offer_ref="offer_base",
        additional_offer_ref="offer_addon",
        price_refs={"offer_base": "price_base", "offer_addon": "price_addon"},
        success_url="https://axignal.com/billing/return",
        cancel_url="https://axignal.com/billing/cancel",
        api_key="sk_fixture",
        mutations_enabled=mutations_enabled,
    )
    adapter = StripeSubscriberAdapter(config=config, transport=transport, clock=lambda: now)
    attempt = PurchaseAttempt(
        tenant_id=TenantId("tenant_fixture"),
        principal_id=PrincipalId("principal_fixture"),
        authority_ref="authority_fixture",
        membership_ref="membership_fixture",
        request_ref="request_fixture",
        intent_ref="intent_fixture",
        attempt_ref="attempt_fixture",
        idempotency_key="idem_fixture",
        kind=AttemptKind.INITIAL,
        desired_total=100,
        previous_effective_capacity=None,
        catalogue_ref="catalogue_fixture",
        catalogue_version="v1",
        environment_ref="stripe-live-fixture",
        authorized_at=now,
        status=AttemptStatus.PENDING_PURCHASE,
        checkout_session_ref="cs_fixture",
    )
    catalogue = ApprovedOfferCatalogue(
        "catalogue_fixture",
        "v1",
        ApprovedRecurringOffer("offer_base", RecurringTerms("month", 1, "EUR", 995)),
        ApprovedRecurringOffer("offer_addon", RecurringTerms("month", 1, "EUR", 495)),
        ApprovedTaxConfiguration(
            "tax-fixture-config",
            "stripe-live-fixture",
            ("tax-registration-fixture",),
            True,
            now,
            datetime(2026, 10, 7, tzinfo=UTC),
        ),
    )
    return adapter, attempt, catalogue, transport


def test_reads_all_pages_and_verifies_complete_paid_capacity_100_binding():
    adapter, attempt, _catalogue, transport = _setup()

    facts = adapter.read_checkout_binding(attempt)

    assert facts.payment_state.value == "VERIFIED"
    assert facts.lifecycle.value == "ELIGIBLE"
    assert len(facts.session_snapshot.items) == 2
    assert len(facts.current_snapshot.items) == 2
    assert facts.current_snapshot.items[1].quantity == 99
    assert facts.binding.subscription_ref == "sub_fixture"
    assert "/v1/checkout/sessions/cs_fixture/line_items?after=li_base" in transport.calls
    assert "/v1/subscription_items?after=si_base" in transport.calls


def test_incomplete_checkout_pagination_fails_closed():
    adapter, attempt, _catalogue, _transport = _setup(malformed_session_page=True)

    with pytest.raises(StripeSubscriberError, match="page is incomplete"):
        adapter.read_checkout_binding(attempt)


@pytest.mark.parametrize("risk", ["refunded", "disputed"])
def test_paid_invoice_with_refund_or_dispute_is_not_verified(risk):
    adapter, attempt, _catalogue, _transport = _setup(**{risk: True})

    facts = adapter.read_checkout_binding(attempt)

    assert facts.payment_state.value == "UNKNOWN"


def test_current_stripe_tax_disabled_fails_closed():
    adapter, attempt, _catalogue, _transport = _setup(tax_enabled=False)

    with pytest.raises(StripeSubscriberConflict, match="automatic tax"):
        adapter.read_checkout_binding(attempt)


def test_live_price_tax_behavior_must_match_approved_exclusive_terms():
    adapter, _attempt, catalogue, transport = _setup()
    transport.price_addon["tax_behavior"] = "inclusive"

    assert adapter.verify_catalogue(catalogue) is False


def test_capacity_update_uses_absolute_quantity_pending_payment_and_idempotency():
    adapter, _attempt, catalogue, transport = _setup(mutations_enabled=True)
    projection = BillingProjection(
        tenant_id=TenantId("tenant_fixture"),
        customer_ref="cus_fixture",
        subscription_ref="sub_fixture",
        checkout_session_ref="cs_fixture",
        environment_ref="stripe-live-fixture",
        additional_item_ref=None,
        effective_capacity=1,
        payment_state=PaymentState.VERIFIED,
        lifecycle=SubscriptionLifecycle.ELIGIBLE,
        binding=None,
        provider_state_ref="provider-state-fixture",
        provider_state_at=datetime(2026, 10, 6, tzinfo=UTC),
        paid_through=datetime(2026, 11, 5, tzinfo=UTC),
        verified_invoice_ref="in_fixture",
    )

    response = adapter.update_capacity(
        projection,
        catalogue=catalogue,
        desired_total=100,
        additional_item_ref=None,
        idempotency_key="capacity-attempt-fixture",
        proration_behavior="always_invoice",
        payment_behavior="pending_if_incomplete",
    )

    mutation = next(
        request
        for request in transport.requests
        if request[0:2] == ("POST", "/v1/subscription_items")
    )
    assert mutation[2]["quantity"] == "99"
    assert mutation[2]["proration_behavior"] == "always_invoice"
    assert mutation[2]["payment_behavior"] == "pending_if_incomplete"
    assert mutation[3] == "capacity-attempt-fixture"
    assert response.subscription_ref == "sub_fixture"
    assert response.pending_update is False
