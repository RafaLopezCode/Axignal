"""Full subscriber journey over real composition/stores and a controlled billing provider."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionLifecycle,
    validate_subscription_capacity,
)
from application.admin_billing.subscriber_checkout import (
    BillingProjection,
    CapacityUpdateResponse,
    CreatedCheckoutSession,
    ProviderCheckoutBinding,
    ProviderCurrentSubscription,
    PurchaseAttempt,
)
from application.admin_billing.subscriber_reconciliation import SubscriberPurchaseReconciler
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_identity.runtime import (
    OidcProviderConfig,
    OidcTransaction,
    VerifiedExternalIdentity,
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
from domain.evidence.admission import EvidenceAdmission
from domain.identity import TenantId
from pipeline.admin_billing.reconciliation_worker import SubscriberReconciliationWorker
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from tests.contracts.test_admitted_organization_store import admitted_identity
from tools.runtime import subscriber_composition
from tools.runtime.subscriber_checkout import (
    SubscriberCheckoutRuntimeConfig,
    build_subscriber_checkout_runtime,
)
from tools.runtime.subscriber_composition import build_subscriber_facade
from tools.runtime.subscriber_configuration import load_subscriber_settings

NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)
ENVIRONMENT = "controlled-live-journey"
CATALOGUE = ApprovedOfferCatalogue(
    "catalogue:axignal-live",
    "approved-v1",
    ApprovedRecurringOffer("offer:base", RecurringTerms("month", 1, "EUR", 995)),
    ApprovedRecurringOffer("offer:additional", RecurringTerms("month", 1, "EUR", 495)),
    ApprovedTaxConfiguration(
        "tax-fixture:explicit-active-registration",
        ENVIRONMENT,
        ("tax-registration:controlled-fixture",),
        True,
        NOW - timedelta(days=1),
        NOW + timedelta(days=30),
    ),
)


class _Clock:
    def __init__(self) -> None:
        self.value = NOW

    def now(self) -> datetime:
        return self.value

    def advance(self, *, seconds: int = 1) -> datetime:
        self.value += timedelta(seconds=seconds)
        return self.value


class _ControlledOidc:
    def authorization_url(
        self,
        config: OidcProviderConfig,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        del nonce, code_challenge
        return f"{config.authorization_endpoint}?state={state}"

    def exchange_and_verify(
        self, config: OidcProviderConfig, transaction: OidcTransaction, code: str
    ) -> VerifiedExternalIdentity:
        assert transaction.client_id == config.client_id
        return VerifiedExternalIdentity(config.issuer, code, config.client_id)


class _CatalogueReader:
    def resolve(self, environment_ref: str) -> ApprovedOfferCatalogue | None:
        return CATALOGUE if environment_ref == ENVIRONMENT else None


@dataclass
class _AttemptFacts:
    attempt_ref: str
    intent_ref: str
    session_ref: str
    capacity: int


class _ControlledBillingProvider:
    """Provider boundary fixture; real services still validate every returned fact."""

    def __init__(self, clock: _Clock) -> None:
        self.clock = clock
        self.paid = False
        self.current_capacity: int | None = None
        self.pending_capacity: int | None = None
        self.invoice_ref = "invoice:initial"
        self._facts: dict[str, _AttemptFacts] = {}
        self.checkout_creates: list[tuple[str, int]] = []
        self.capacity_updates: list[tuple[int, int, str, str, str, str]] = []
        self.state_at = NOW

    def create_initial_checkout(
        self,
        intent: PurchaseIntent,
        catalogue: ApprovedOfferCatalogue,
        *,
        idempotency_key: str,
    ) -> CreatedCheckoutSession:
        assert catalogue.catalogue_ref == CATALOGUE.catalogue_ref
        self.checkout_creates.append((idempotency_key, intent.xeed_capacity))
        self.current_capacity = intent.xeed_capacity
        self.pending_capacity = None
        self.paid = False
        self.invoice_ref = "invoice:initial"
        self.state_at = self.clock.advance()
        session_ref = "checkout:initial"
        self._facts[intent.attempt_ref] = _AttemptFacts(
            intent.attempt_ref, intent.intent_ref, session_ref, intent.xeed_capacity
        )
        return CreatedCheckoutSession(
            session_ref,
            "customer:subscriber",
            "subscription:subscriber",
            "https://checkout.stripe.com/c/pay/controlled",
        )

    def read_checkout_binding(self, attempt: PurchaseAttempt) -> ProviderCheckoutBinding:
        facts = self._facts[attempt.attempt_ref]
        observed_at = self.clock.now()
        items = _items(facts.capacity)
        binding = CheckoutAttemptBinding(
            binding_ref=f"provider-binding:{attempt.attempt_ref}",
            intent_ref=attempt.intent_ref,
            attempt_ref=attempt.attempt_ref,
            checkout_session_ref=facts.session_ref,
            customer_ref="customer:subscriber",
            subscription_ref="subscription:subscriber",
            environment_ref=ENVIRONMENT,
            established_at=attempt.authorized_at,
        )
        session_snapshot = SubscriptionItemSnapshot(
            evidence_ref=f"checkout-lines:{facts.session_ref}",
            checkout_session_ref=facts.session_ref,
            customer_ref="customer:subscriber",
            subscription_ref="subscription:subscriber",
            environment_ref=ENVIRONMENT,
            provider_state_ref=f"checkout-created:{facts.session_ref}",
            provider_state_at=attempt.authorized_at,
            retrieved_at=observed_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            metadata_intent_ref=attempt.intent_ref,
            items=items,
        )
        current_snapshot = CurrentSubscriptionItems(
            evidence_ref=f"subscription-items:subscription:subscriber:{self.state_at.isoformat()}",
            customer_ref="customer:subscriber",
            subscription_ref="subscription:subscriber",
            environment_ref=ENVIRONMENT,
            provider_state_ref=f"subscription-state:{self.state_at.isoformat()}",
            provider_state_at=self.state_at,
            retrieved_at=observed_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=items,
        )
        return ProviderCheckoutBinding(
            binding=binding,
            session_snapshot=session_snapshot,
            current_snapshot=current_snapshot,
            payment_state=PaymentState.VERIFIED if self.paid else PaymentState.UNKNOWN,
            lifecycle=SubscriptionLifecycle.ELIGIBLE,
            paid_through=self.clock.now() + timedelta(days=30) if self.paid else None,
            invoice_ref=self.invoice_ref,
        )

    def read_current_subscription(
        self, projection: BillingProjection
    ) -> ProviderCurrentSubscription:
        visible_capacity = self.current_capacity or projection.effective_capacity or 1
        if self.pending_capacity is not None and not self.paid:
            visible_capacity = projection.effective_capacity or visible_capacity
        observed_at = self.clock.now()
        snapshot = CurrentSubscriptionItems(
            evidence_ref=f"subscription-items:subscription:subscriber:{self.state_at.isoformat()}",
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            environment_ref=ENVIRONMENT,
            provider_state_ref=f"subscription-state:{self.state_at.isoformat()}",
            provider_state_at=self.state_at,
            retrieved_at=observed_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=_items(visible_capacity),
        )
        payment_state = (
            PaymentState.UNKNOWN
            if self.pending_capacity is not None and not self.paid
            else PaymentState.VERIFIED
            if self.paid
            else PaymentState.UNKNOWN
        )
        return ProviderCurrentSubscription(
            snapshot=snapshot,
            payment_state=payment_state,
            lifecycle=SubscriptionLifecycle.ELIGIBLE,
            paid_through=self.clock.now() + timedelta(days=30) if self.paid else None,
            additional_item_ref=None if visible_capacity == 1 else "subscription-item:addon",
            invoice_ref=self.invoice_ref,
        )

    def update_capacity(
        self,
        projection: BillingProjection,
        *,
        catalogue: ApprovedOfferCatalogue,
        desired_total: int,
        additional_item_ref: str | None,
        idempotency_key: str,
        proration_behavior: str,
        payment_behavior: str,
    ) -> CapacityUpdateResponse:
        assert catalogue.catalogue_ref == CATALOGUE.catalogue_ref
        assert projection.subscription_ref == "subscription:subscriber"
        assert proration_behavior == "always_invoice"
        assert payment_behavior == "pending_if_incomplete"
        quantity = desired_total - 1
        self.capacity_updates.append(
            (
                desired_total,
                quantity,
                additional_item_ref or "new",
                idempotency_key,
                proration_behavior,
                payment_behavior,
            )
        )
        self.pending_capacity = desired_total
        self.paid = False
        self.invoice_ref = f"invoice:capacity:{desired_total}"
        self.state_at = self.clock.advance()
        return CapacityUpdateResponse(
            "subscription:subscriber",
            "customer:subscriber",
            "subscription-item:addon",
            self.invoice_ref,
            "https://invoice.stripe.com/i/controlled",
            True,
        )

    def mark_paid(self) -> None:
        if self.pending_capacity is not None:
            self.current_capacity = self.pending_capacity
            self.pending_capacity = None
        self.paid = True
        self.state_at = self.clock.advance()


def _items(capacity: int) -> tuple[NormalizedRecurringItem, ...]:
    items = [
        NormalizedRecurringItem(
            "subscription-item:base", "offer:base", 1, True, CATALOGUE.base_offer.terms
        )
    ]
    if capacity > 1:
        items.append(
            NormalizedRecurringItem(
                "subscription-item:addon",
                "offer:additional",
                capacity - 1,
                True,
                CATALOGUE.additional_xeed_offer.terms,
            )
        )
    return tuple(items)


def _settings(tmp_path: Path):
    secret_file = tmp_path / "controlled-google-secret"
    secret_file.write_text("controlled-only", encoding="utf-8")
    return load_subscriber_settings(
        {
            "AXIGNAL_SUBSCRIBER_ENABLED": "true",
            "AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED": "true",
            "AXIGNAL_EXPERIENCE_ORIGIN": "https://axignal.com",
            "AXIGNAL_LEGAL_OPERATOR_NAME": "Fixture AXIGNAL SLU",
            "AXIGNAL_LEGAL_OPERATOR_KIND": "SLU",
            "AXIGNAL_LEGAL_TAX_ID": "FIXTURE-NOT-A-REAL-TAX-ID",
            "AXIGNAL_LEGAL_ADDRESS": "Fixture-only address",
            "AXIGNAL_LEGAL_CONTACT": "billing-fixture@example.invalid",
            "AXIGNAL_LEGAL_TERMS_VERSION": "fixture-v1",
            "AXIGNAL_GOOGLE_CLIENT_ID": "controlled-google-client",
            "AXIGNAL_GOOGLE_CLIENT_SECRET_FILE": str(secret_file),
            "AXIGNAL_GOOGLE_REDIRECT_URI": "https://axignal.com/api/auth/callback/google",
            "AXIGNAL_GOOGLE_REGISTERED": "true",
        }
    )


def _register_canonical_organization(data_dir: Path) -> None:
    artifacts = ContentAddressedArtifactStore(data_dir / "artifacts")
    governance = SqliteIdentityGovernanceStore(data_dir / "identity-governance.sqlite3")
    store = SqliteCanonicalOrganizationStore(
        data_dir / "canonical-organizations.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        governance=governance,
    )
    admitted = admitted_identity(artifacts, "org:registry:journey", "Journey Example SLU")
    assert store.register(admitted, EvidenceAdmission.admit_claim(admitted))


def _signup(facade, subject: str) -> tuple[str, TenantId]:
    started = facade.handle(
        "POST",
        "/subscriber/auth/start",
        {"Origin": "https://axignal.com"},
        {"provider": "google", "intent": "signup"},
    )
    assert started.status == 200
    state = parse_qs(urlsplit(str(started.body["authorizationUrl"])).query)["state"][0]
    callback = facade.handle(
        "POST",
        "/subscriber/auth/callback",
        {"Origin": "https://axignal.com"},
        {
            "provider": "google",
            "transactionToken": started.body["transactionToken"],
            "state": state,
            "code": subject,
        },
    )
    assert callback.status == 200
    token = str(callback.body["sessionToken"])
    return token, facade.identity.authenticate(token).tenant_id


@pytest.fixture
def paid_journey(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _register_canonical_organization(data_dir)
    clock = _Clock()
    provider = _ControlledBillingProvider(clock)
    catalogue_reader = _CatalogueReader()
    stores: list[SqliteSubscriberBillingStore] = []

    def build_facade():
        settings = _settings(tmp_path)
        stripe_settings = subscriber_composition.StripeSubscriberRuntimeSettings(
            environment_ref=ENVIRONMENT,
            account_ref="acct_fixture_only",
            live_mode=True,
            api_version="2026-10-06.fixture",
            base_offer_ref="offer:base",
            additional_offer_ref="offer:additional",
            price_refs={"offer:base": "price:base", "offer:additional": "price:addon"},
            success_url="https://axignal.com/account?purchase=complete",
            cancel_url="https://axignal.com/account?purchase=cancelled",
            checkout_hosts=frozenset({"checkout.stripe.com"}),
            invoice_hosts=frozenset({"invoice.stripe.com"}),
            database_path=data_dir / "unused.sqlite3",
            enabled=True,
            mutations_enabled=True,
            api_key="fixture-key-never-sent",
            webhook_signing_secret="fixture-webhook-never-sent",
        )

        def controlled_runtime_factory(
            *, settings, authority_reader, entitlement_reader, catalogue_reader
        ):
            store = SqliteSubscriberBillingStore(settings.database_path)
            stores.append(store)
            reconciler = SubscriberPurchaseReconciler(
                store=store,
                provider=provider,
                catalogue_reader=catalogue_reader,
                environment_ref=settings.environment_ref,
            )
            retry_worker = SubscriberReconciliationWorker(store=store, reconciler=reconciler)
            return build_subscriber_checkout_runtime(
                config=SubscriberCheckoutRuntimeConfig(
                    enabled=settings.enabled,
                    environment_ref=settings.environment_ref,
                    checkout_hosts=settings.checkout_hosts,
                    invoice_hosts=settings.invoice_hosts,
                ),
                authority_reader=authority_reader,
                entitlement_reader=entitlement_reader,
                catalogue_reader=catalogue_reader,
                store=store,
                provider=provider,
                webhook=None,
                reconciler=reconciler,
                retry_worker=retry_worker,
            )

        monkeypatch.setattr(
            subscriber_composition,
            "build_stripe_subscriber_checkout_runtime",
            controlled_runtime_factory,
        )
        facade = build_subscriber_facade(
            settings,
            data_dir,
            observation_memory=SqliteObservationMemory(data_dir / "observation-memory.sqlite3"),
            reuse_policy=ObservationReusePolicy("integration-read", "v1"),
            temporal_policy=TemporalCurrentnessPolicy(
                "integration-currentness", "v1", timedelta(days=7), timedelta(days=30)
            ),
            code_sha="controlled-integration-code",
            stripe_settings=stripe_settings,
            offer_catalogue_reader=catalogue_reader,
            clock=clock,
        )
        facade.identity.auth._provider = _ControlledOidc()
        return facade

    return data_dir, clock, provider, catalogue_reader, build_facade, stores


def test_registered_subscriber_paid_capacity_focus_output_and_expansion_journey(paid_journey):
    _data_dir, _clock, provider, _catalogue, build_facade, stores = paid_journey
    facade = build_facade()
    token_a, tenant_a = _signup(facade, "subject:subscriber-a")

    headers = {"Origin": "https://axignal.com", "Authorization": f"Bearer {token_a}"}
    free = facade.handle(
        "GET", "/subscriber/portfolio", {"Authorization": headers["Authorization"]}
    )
    assert free.status == 200
    assert free.body["capacity"] is None
    assert free.body["organizations"] == []
    assert free.body["contractingEnabled"] is True
    assert free.body["canPurchase"] is True

    no_capacity_add = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "add", "requestRef": "add:before-payment", "locator": "Journey Example SLU"},
    )
    assert no_capacity_add.status == 200
    assert no_capacity_add.body["state"] == "CAPACITY_UNKNOWN"
    assert "focusId" not in no_capacity_add.body
    assert facade.workflow._portfolio.list(facade.identity.authenticate(token_a)) == ()

    purchase = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "purchase", "requestRef": "purchase:base", "desiredOrganizationTotal": 1},
    )
    assert purchase.status == 200
    assert purchase.body["state"] == "PENDING_PURCHASE"
    assert purchase.body["effectiveCapacity"] is None
    assert purchase.body["checkoutUrl"] == "https://checkout.stripe.com/c/pay/controlled"
    assert len(provider.checkout_creates) == 1
    assert provider.checkout_creates[0][1] == 1

    pending = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "refresh_purchase", "requestRef": "refresh:unpaid"},
    )
    assert pending.status == 200
    assert pending.body["capacity"] is None
    assert pending.body["capacityCurrentness"] == "UNKNOWN"

    provider.mark_paid()
    activated = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "refresh_purchase", "requestRef": "refresh:paid-base"},
    )
    assert activated.status == 200
    assert activated.body["capacity"] == 1
    assert activated.body["capacityCurrentness"] == "CURRENT"

    created = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "add", "requestRef": "add:after-payment", "locator": "Journey Example SLU"},
    )
    assert created.status == 200
    assert created.body["state"] == "CREATED"
    assert created.body["organizationId"] == "org:registry:journey"
    focus_a = str(created.body["focusId"])
    output = facade.handle(
        "GET",
        f"/subscriber/organizations/{focus_a}/output",
        {"Authorization": headers["Authorization"]},
    )
    assert output.status == 200
    assert output.body["state"] == "INSUFFICIENT_EVIDENCE"
    assert "economicOutput" not in output.body and "signals" not in output.body

    def expand(request_ref: str, desired: int):
        return facade.handle(
            "POST",
            "/subscriber/portfolio",
            headers,
            {
                "action": "expand",
                "requestRef": request_ref,
                "desiredOrganizationTotal": desired,
            },
        )

    projection = stores[0].get_billing_projection(tenant_a)
    assert projection is not None
    observed_current = provider.read_current_subscription(projection)
    observed_validation = validate_subscription_capacity(
        expected_capacity=projection.effective_capacity,
        authorized_at=projection.provider_state_at,
        catalogue=CATALOGUE,
        expected_customer_ref=projection.customer_ref,
        expected_subscription_ref=projection.subscription_ref,
        expected_environment_ref=ENVIRONMENT,
        snapshot=observed_current.snapshot,
        previous=projection.binding,
    )
    assert observed_validation.status.value == "VERIFIED", (
        observed_validation,
        projection,
        observed_current,
    )
    first_update = expand("expand:two", 2)
    duplicate = expand("expand:two", 2)
    second_click = expand("expand:two-second-click", 2)
    assert first_update.status == duplicate.status == second_click.status == 200
    assert first_update.body["state"] == "PENDING_PURCHASE", (
        first_update.body,
        facade.workflow._entitlements.snapshot(tenant_a),
        stores[0].get_billing_projection(tenant_a),
    )
    assert first_update.body["effectiveCapacity"] == 1
    assert duplicate.body["requestRef"] == first_update.body["requestRef"]
    assert second_click.body["requestRef"] == first_update.body["requestRef"]
    assert first_update.body["paymentUrl"] == "https://invoice.stripe.com/i/controlled"
    assert [(update[1], update[4], update[5]) for update in provider.capacity_updates] == [
        (1, "always_invoice", "pending_if_incomplete")
    ]
    assert facade.workflow._entitlements.snapshot(tenant_a).capacity == 1

    still_pending = facade.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "refresh_purchase", "requestRef": "refresh:expand-unpaid"},
    )
    assert still_pending.body["capacity"] == 1
    restarted = build_facade()
    pending_after_restart = restarted.handle(
        "GET", "/subscriber/portfolio", {"Authorization": headers["Authorization"]}
    )
    assert pending_after_restart.status == 200
    assert pending_after_restart.body["capacity"] == 1
    replay_after_restart = restarted.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {
            "action": "expand",
            "requestRef": "expand:two",
            "desiredOrganizationTotal": 2,
        },
    )
    assert replay_after_restart.body["state"] == "PENDING_PURCHASE"
    assert replay_after_restart.body["paymentUrl"] == first_update.body["paymentUrl"]
    assert len(provider.capacity_updates) == 1
    provider.mark_paid()
    paid_two = restarted.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "refresh_purchase", "requestRef": "refresh:expand-two"},
    )
    assert paid_two.body["capacity"] == 2, paid_two.body

    expand_100 = restarted.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {
            "action": "expand",
            "requestRef": "expand:one-hundred",
            "desiredOrganizationTotal": 100,
        },
    )
    assert expand_100.body["state"] == "PENDING_PURCHASE"
    assert expand_100.body["effectiveCapacity"] == 2
    assert provider.capacity_updates[-1][1] == 99
    assert facade.workflow._entitlements.snapshot(tenant_a).capacity == 2
    provider.mark_paid()
    paid_100 = restarted.handle(
        "POST",
        "/subscriber/portfolio",
        headers,
        {"action": "refresh_purchase", "requestRef": "refresh:expand-100"},
    )
    assert paid_100.body["capacity"] == 100
    assert len(provider.checkout_creates) == 1
    assert [update[1] for update in provider.capacity_updates] == [1, 99]

    persisted = restarted.handle(
        "GET", "/subscriber/portfolio", {"Authorization": headers["Authorization"]}
    )
    assert persisted.status == 200
    assert persisted.body["capacity"] == 100
    assert len(persisted.body["organizations"]) == 1
    assert persisted.body["organizations"][0]["focusId"] == focus_a

    token_b, tenant_b = _signup(restarted, "subject:subscriber-b")
    other_headers = {"Origin": "https://axignal.com", "Authorization": f"Bearer {token_b}"}
    free_b = restarted.handle(
        "GET", "/subscriber/portfolio", {"Authorization": other_headers["Authorization"]}
    )
    assert free_b.status == 200 and free_b.body["capacity"] is None
    assert free_b.body["organizations"] == []
    cross_tenant = restarted.handle(
        "GET",
        f"/subscriber/organizations/{focus_a}/output",
        {"Authorization": other_headers["Authorization"]},
    )
    assert cross_tenant.status == 403
    assert tenant_b != tenant_a
