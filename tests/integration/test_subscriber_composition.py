"""Integration checks for durable subscriber composition and authority seams."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from urllib.parse import parse_qs, urlsplit

from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionCapacityValidation,
    SubscriptionLifecycle,
)
from application.admin_billing.subscriber_checkout import (
    AttemptKind,
    AttemptStatus,
    BillingProjection,
    PurchaseAttempt,
)
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_identity.runtime import (
    OidcProviderConfig,
    OidcProviderId,
    OidcTransaction,
    SystemClock,
    VerifiedExternalIdentity,
)
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedRecurringOffer,
    ApprovedTaxConfiguration,
    BindingReason,
    BindingStatus,
    RecurringTerms,
)
from domain.evidence.admission import EvidenceAdmission
from domain.identity import PrincipalId, TenantId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from tests.contracts.test_admitted_organization_store import admitted_identity
from tools.runtime.subscriber_checkout import StripeSubscriberRuntimeSettings
from tools.runtime.subscriber_composition import (
    _oidc_provider_configs,
    _SubscriberWorkflow,
    build_subscriber_facade,
)
from tools.runtime.subscriber_configuration import SubscriberSettings, load_subscriber_settings
from tools.runtime.subscriber_http import SubscriberHttpFacade
from tools.runtime.subscriber_provisioning import ConfiguredOfferCatalogueReader


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


def _settings(tmp_path: Path, *, contracting: bool = False) -> SubscriberSettings:
    secret_path = tmp_path / "controlled-oidc-client-secret"
    secret_path.write_text("test-only", encoding="utf-8")
    return load_subscriber_settings(
        {
            "AXIGNAL_SUBSCRIBER_ENABLED": "true",
            "AXIGNAL_EXPERIENCE_ORIGIN": "https://axignal.com",
            "AXIGNAL_GOOGLE_CLIENT_ID": "controlled-google-client",
            "AXIGNAL_GOOGLE_CLIENT_SECRET_FILE": str(secret_path),
            "AXIGNAL_GOOGLE_REDIRECT_URI": "https://axignal.com/api/auth/callback/google",
            "AXIGNAL_GOOGLE_REGISTERED": "true",
            "AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED": "true" if contracting else "false",
            "AXIGNAL_LEGAL_OPERATOR_NAME": "Axignal SLU",
            "AXIGNAL_LEGAL_TAX_ID": "test-tax-id",
            "AXIGNAL_LEGAL_ADDRESS": "Test address",
            "AXIGNAL_LEGAL_CONTACT": "legal@example.test",
            "AXIGNAL_LEGAL_TERMS_VERSION": "test-terms-v1",
        }
    )


def _build(
    tmp_path: Path,
    *,
    environment_ref: str | None = "test",
    offer_catalogue_reader: ConfiguredOfferCatalogueReader | None = None,
    contracting: bool = False,
    checkout_configured: bool = False,
) -> SubscriberHttpFacade:
    settings = _settings(tmp_path, contracting=contracting)
    facade = build_subscriber_facade(
        settings,
        tmp_path,
        observation_memory=SqliteObservationMemory(tmp_path / "observation-memory.sqlite3"),
        reuse_policy=ObservationReusePolicy("subscriber-read", "051-v1"),
        temporal_policy=TemporalCurrentnessPolicy(
            "subscriber-currentness", "051-v1", timedelta(days=7), timedelta(days=30)
        ),
        code_sha="test-code-sha",
        stripe_settings=(
            None
            if environment_ref is None
            else StripeSubscriberRuntimeSettings(
                environment_ref=environment_ref,
                account_ref="acct_test",
                live_mode=False,
                api_version="2026-10-01",
                base_offer_ref="base-offer",
                additional_offer_ref="additional-offer",
                price_refs={
                    "base-offer": "price_test_base",
                    "additional-offer": "price_test_additional",
                },
                success_url="https://axignal.com/account?purchase=complete",
                cancel_url="https://axignal.com/account?purchase=cancelled",
                checkout_hosts=frozenset({"axignal.com"}),
                invoice_hosts=frozenset({"axignal.com"}),
                database_path=tmp_path / "ignored-by-composition.sqlite3",
                enabled=checkout_configured,
                mutations_enabled=checkout_configured,
                api_key="sk_test_composition_only" if checkout_configured else None,
                webhook_signing_secret=("whsec_composition_only" if checkout_configured else None),
            )
        ),
        offer_catalogue_reader=offer_catalogue_reader,
        clock=SystemClock(),
    )
    facade.identity.auth._provider = _ControlledOidc()
    return facade


def _signup(facade: SubscriberHttpFacade, subject: str) -> tuple[str, TenantId]:
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
    context = facade.identity.authenticate(token)
    return token, context.tenant_id


def _register_canonical_organization(tmp_path: Path) -> None:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    governance = SqliteIdentityGovernanceStore(tmp_path / "identity-governance.sqlite3")
    store = SqliteCanonicalOrganizationStore(
        tmp_path / "canonical-organizations.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        governance=governance,
    )
    request = admitted_identity(artifacts, "org:registry:shared", "Shared Registry Example SLU")
    assert store.register(request, EvidenceAdmission.admit_claim(request))


def _commit_verified_projection(
    store: SqliteSubscriberBillingStore,
    tenant_id: TenantId,
    *,
    now: datetime,
    environment_ref: str = "test",
    capacity: int = 1,
    binding_capacity: int | None = None,
) -> None:
    state_ref = f"provider-state:{tenant_id}:{now.isoformat()}"
    binding = SubscriptionCapacityValidation(
        BindingStatus.VERIFIED,
        BindingReason.EXACT_MATCH,
        "evidence:paid-invoice",
        "fingerprint:paid-invoice",
        state_ref,
        now,
        capacity if binding_capacity is None else binding_capacity,
    )
    projection = BillingProjection(
        tenant_id=tenant_id,
        customer_ref=f"customer:{tenant_id}",
        subscription_ref=f"subscription:{tenant_id}",
        checkout_session_ref=f"session:{tenant_id}",
        environment_ref=environment_ref,
        additional_item_ref=None,
        effective_capacity=capacity,
        payment_state=PaymentState.VERIFIED,
        lifecycle=SubscriptionLifecycle.ELIGIBLE,
        binding=binding,
        provider_state_ref=state_ref,
        provider_state_at=now,
        paid_through=now + timedelta(days=30),
        verified_invoice_ref=f"invoice:{tenant_id}",
    )
    attempt = PurchaseAttempt(
        tenant_id=tenant_id,
        principal_id=PrincipalId("principal:test"),
        authority_ref="authority:test",
        membership_ref="membership:test",
        request_ref=f"seed:{tenant_id}",
        intent_ref=f"intent:{tenant_id}",
        attempt_ref=f"attempt:{tenant_id}",
        idempotency_key=f"idempotency:{tenant_id}",
        kind=AttemptKind.INITIAL,
        desired_total=capacity,
        previous_effective_capacity=None,
        catalogue_ref="catalogue:test",
        catalogue_version="v1",
        environment_ref=environment_ref,
        authorized_at=now,
        status=AttemptStatus.PENDING_PURCHASE,
        checkout_session_ref=projection.checkout_session_ref,
        customer_ref=projection.customer_ref,
        subscription_ref=projection.subscription_ref,
    )
    store.prepare_attempt(attempt)
    complete = replace(
        attempt,
        status=AttemptStatus.COMPLETE,
        invoice_ref=projection.verified_invoice_ref,
    )
    store.record_reconciled_purchase(complete, projection)


def test_composed_signup_bootstraps_purchase_scope_and_unknown_capacity_survives_restart(
    tmp_path: Path,
) -> None:
    _register_canonical_organization(tmp_path)
    facade = _build(tmp_path, environment_ref=None)
    token, tenant_id = _signup(facade, "subject:one")

    assert facade.identity.store.has_membership(
        facade.identity.authenticate(token).principal_id, tenant_id
    )
    assert SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3").is_purchase_owner(
        facade.identity.authenticate(token).principal_id, tenant_id
    )
    response = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
        {
            "action": "add",
            "requestRef": "add:unknown",
            "locator": "Shared Registry Example SLU",
        },
    )
    assert response.status == 200
    assert response.body["state"] == "CAPACITY_UNKNOWN"
    assert "organizationId" not in response.body

    restarted = _build(tmp_path, environment_ref=None)
    restarted.identity.auth._provider = _ControlledOidc()
    portfolio = restarted.handle(
        "GET",
        "/subscriber/portfolio",
        {"Authorization": f"Bearer {token}"},
    )
    assert portfolio.status == 200
    assert portfolio.body["capacity"] is None
    assert portfolio.body["capacityCurrentness"] == "UNKNOWN"


def test_composed_portfolios_are_private_and_output_stays_honest_without_plan(
    tmp_path: Path,
) -> None:
    _register_canonical_organization(tmp_path)
    facade = _build(tmp_path)
    token_a, tenant_a = _signup(facade, "subject:a")
    token_b, tenant_b = _signup(facade, "subject:b")
    billing_store = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    now = datetime.now(UTC)
    _commit_verified_projection(billing_store, tenant_a, now=now)
    _commit_verified_projection(billing_store, tenant_b, now=now)

    def add(token: str, request_ref: str) -> dict[str, object]:
        response = facade.handle(
            "POST",
            "/subscriber/portfolio",
            {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
            {
                "action": "add",
                "requestRef": request_ref,
                "locator": "Shared Registry Example SLU",
            },
        )
        assert response.status == 200
        return response.body

    added_a = add(token_a, "add:a")
    added_b = add(token_b, "add:b")
    assert added_a["state"] == added_b["state"] == "CREATED"
    assert added_a["organizationId"] == added_b["organizationId"] == "org:registry:shared"
    assert added_a["focusId"] != added_b["focusId"]
    assert added_a["observationState"] == added_b["observationState"] == "NOT_READY"

    read_a = facade.handle("GET", "/subscriber/portfolio", {"Authorization": f"Bearer {token_a}"})
    read_b = facade.handle("GET", "/subscriber/portfolio", {"Authorization": f"Bearer {token_b}"})
    organizations_a = cast(list[dict[str, object]], read_a.body["organizations"])
    organizations_b = cast(list[dict[str, object]], read_b.body["organizations"])
    assert [item["focusId"] for item in organizations_a] == [added_a["focusId"]]
    assert [item["focusId"] for item in organizations_b] == [added_b["focusId"]]
    foreign_output = facade.handle(
        "GET",
        f"/subscriber/organizations/{added_a['focusId']}/output",
        {"Authorization": f"Bearer {token_b}"},
    )
    assert foreign_output.status == 403

    output = facade.handle(
        "GET",
        f"/subscriber/organizations/{added_a['focusId']}/output",
        {"Authorization": f"Bearer {token_a}"},
    )
    assert output.status == 200
    assert output.body["state"] == "INSUFFICIENT_EVIDENCE"
    assert "economicOutput" not in output.body and "signals" not in output.body

    reobserved = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token_a}"},
        {
            "action": "reobserve",
            "requestRef": "reobserve:a",
            "focusId": str(added_a["focusId"]),
        },
    )
    assert reobserved.status == 200
    assert reobserved.body["state"] == "NOT_READY"
    assert reobserved.body["observationState"] == "NOT_READY"
    assert reobserved.body["focusId"] == added_a["focusId"]

    restarted = _build(tmp_path)
    portfolio_after_restart = restarted.handle(
        "GET", "/subscriber/portfolio", {"Authorization": f"Bearer {token_a}"}
    )
    persisted = cast(list[dict[str, object]], portfolio_after_restart.body["organizations"])
    assert [item["focusId"] for item in persisted] == [added_a["focusId"]]


def test_billing_snapshot_freshness_fails_closed_for_old_future_or_mismatched_evidence(
    tmp_path: Path,
) -> None:
    facade = _build(tmp_path)
    token, tenant_id = _signup(facade, "subject:freshness")
    store = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    now = datetime.now(UTC)
    _commit_verified_projection(
        store,
        tenant_id,
        now=now - timedelta(minutes=5, seconds=1),
    )
    stale = facade.workflow.portfolio(facade.identity.authenticate(token))
    assert stale["capacity"] is None
    assert stale["capacityCurrentness"] == "STALE"

    future_tenant = TenantId("tenant:future")
    _commit_verified_projection(store, future_tenant, now=now + timedelta(seconds=1))
    workflow = cast(_SubscriberWorkflow, facade.workflow)
    future = workflow._entitlements.snapshot(future_tenant)
    assert future.capacity is None
    assert future.currentness.value == "UNKNOWN"

    mismatch_tenant = TenantId("tenant:mismatched-binding")
    _commit_verified_projection(
        store,
        mismatch_tenant,
        now=now,
        binding_capacity=2,
    )
    mismatch = workflow._entitlements.snapshot(mismatch_tenant)
    assert mismatch.capacity is None
    assert mismatch.currentness.value == "UNKNOWN"


def test_oidc_endpoint_configuration_uses_issuer_specific_official_routes(tmp_path: Path) -> None:
    configs = _oidc_provider_configs(_settings(tmp_path))
    assert configs[OidcProviderId.OPENAI].authorization_endpoint == (
        "https://auth.openai.com/api/accounts/authorize"
    )
    assert configs[OidcProviderId.OPENAI].token_endpoint == (
        "https://auth.openai.com/api/accounts/oauth/token"
    )
    assert configs[OidcProviderId.GOOGLE].authorization_endpoint == (
        "https://accounts.google.com/o/oauth2/v2/auth"
    )


def test_tax_ready_accepts_only_exact_approved_offer_and_current_tax_contract(
    tmp_path: Path,
) -> None:
    now = datetime.now(UTC)
    tax = ApprovedTaxConfiguration(
        configuration_ref="tax:approved",
        environment_ref="test",
        active_registration_refs=("registration:verified",),
        automatic_tax_enabled=True,
        verified_at=now - timedelta(minutes=1),
        valid_until=now + timedelta(days=1),
    )

    def reader(
        base_amount: int,
        addon_amount: int,
        tax_configuration: ApprovedTaxConfiguration | None = tax,
    ) -> ConfiguredOfferCatalogueReader:
        return ConfiguredOfferCatalogueReader(
            ApprovedOfferCatalogue(
                catalogue_ref="catalogue:approved",
                version="v1",
                base_offer=ApprovedRecurringOffer(
                    "base-offer",
                    RecurringTerms("month", 1, "EUR", base_amount, tax_behavior="exclusive"),
                ),
                additional_xeed_offer=ApprovedRecurringOffer(
                    "additional-offer",
                    RecurringTerms("month", 1, "EUR", addon_amount, tax_behavior="exclusive"),
                ),
                tax_configuration=tax_configuration,
            ),
            "test",
        )

    def workflow(
        root: Path,
        catalogue_reader: ConfiguredOfferCatalogueReader,
    ) -> _SubscriberWorkflow:
        root.mkdir()
        facade = _build(
            root,
            offer_catalogue_reader=catalogue_reader,
            contracting=True,
            checkout_configured=True,
        )
        return cast(_SubscriberWorkflow, facade.workflow)

    approved = workflow(tmp_path / "approved", reader(995, 495))
    assert approved._tax_ready() is True

    wrong_prices = workflow(tmp_path / "wrong-prices", reader(99_500, 49_500))
    assert wrong_prices._tax_ready() is False

    missing_tax = workflow(tmp_path / "missing-tax", reader(995, 495, None))
    assert missing_tax._tax_ready() is False

    wrong_interval_reader = ConfiguredOfferCatalogueReader(
        ApprovedOfferCatalogue(
            catalogue_ref="catalogue:wrong-interval",
            version="v1",
            base_offer=ApprovedRecurringOffer(
                "base-offer", RecurringTerms("year", 1, "EUR", 995, tax_behavior="exclusive")
            ),
            additional_xeed_offer=ApprovedRecurringOffer(
                "additional-offer",
                RecurringTerms("month", 1, "EUR", 495, tax_behavior="exclusive"),
            ),
            tax_configuration=tax,
        ),
        "test",
    )
    wrong_interval = workflow(tmp_path / "wrong-interval", wrong_interval_reader)
    assert wrong_interval._tax_ready() is False
