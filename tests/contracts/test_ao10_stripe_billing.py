from __future__ import annotations

import hashlib
import hmac
import json
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.admin_billing import AdminBillingService
from application.admin_customer_accounts import (
    AdminCustomerAccountService,
    EntitledXeedReader,
    ServiceXeedAccessError,
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
from domain.admin_billing import (
    BillingAuthorityGrant,
    BillingPaymentState,
    BillingProvider,
    quantities_for_xeed_capacity,
)
from domain.admin_customer_accounts import AccountUserRole, PaymentVerificationState
from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
)
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.tenancy import Principal, PrincipalTenantMembership, Tenant
from domain.xeed import Xeed
from pipeline.admin_billing import SqliteAdminBillingStore
from pipeline.admin_billing.stripe import (
    StripeEventNormalizer,
    StripeWebhookError,
    StripeWebhookVerifier,
    checkout_mapping_from_verified_event,
)
from pipeline.admin_customer_accounts import SqliteAdminCustomerAccountStore
from tests.support.xeed_authority import InMemoryXeedAuthority
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler

NOW = datetime(2026, 10, 2, 10, 0, tzinfo=UTC)
SECRET = b"fixture-webhook-signing-secret"
BASE_PRICE = "price_axignal_base_monthly"
ADDITIONAL_PRICE = "price_axignal_additional_xeed"


def _grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("session:founder"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _register_stripe_integration(runtime, *, at: datetime) -> None:
    runtime.admin_integration_store.append_definition(
        operation_id="ao10-register-stripe-integration",
        occurred_at=at,
        definition=IntegrationDefinition(
            integration_id="stripe-billing",
            provider="Stripe",
            purpose="AXIGNAL first-party billing and payment lifecycle",
            owner="AXIGNAL Operations",
            environment=IntegrationEnvironment.DEVELOPMENT,
            enabled=True,
            credential=CredentialLifecycle(
                reference="secret://stripe/development/webhook-signing-secret",
                state=CredentialState.CONFIGURED,
                last_rotated_at=at,
            ),
            scopes=("webhooks.verify", "subscriptions.read", "invoices.read"),
            direction=IntegrationDirection.BIDIRECTIONAL,
            authority_boundary=(
                "Stripe owns payment/subscription facts; AXIGNAL owns account and Xeed entitlement."
            ),
            webhook_capable=True,
            webhook_endpoint="https://axignal.com/internal/webhooks/stripe",
            rate_limit_posture="Provider quota observed; inbound verification fails closed.",
            health_freshness_seconds=900,
        ),
    )


def _stores(tmp_path: Path):
    accounts = SqliteAdminCustomerAccountStore(tmp_path / "accounts.sqlite3")
    billing = SqliteAdminBillingStore(tmp_path / "billing.sqlite3")
    return accounts, billing


def _signup(
    accounts: SqliteAdminCustomerAccountStore,
    *,
    at: datetime = NOW,
) -> AdminCustomerAccountService:
    service = AdminCustomerAccountService(accounts)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="AXIGNAL Customer",
        now=at,
        reason="signup",
    )
    service.add_user(
        grant=_grant(),
        account_id="account:1",
        user_id="user:owner",
        principal_id="principal:1",
        role=AccountUserRole.OWNER,
        now=at + timedelta(seconds=1),
        reason="owner",
    )
    return service


def _payload(
    event_id: str,
    event_type: str,
    created: datetime,
    obj: dict[str, object],
    *,
    livemode: bool = False,
) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "created": int(created.timestamp()),
            "livemode": livemode,
            "data": {"object": obj},
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _signature(payload: bytes, created: datetime) -> str:
    timestamp = int(created.timestamp())
    digest = hmac.new(
        SECRET,
        str(timestamp).encode("ascii") + b"." + payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def _verify(payload: bytes, at: datetime):
    return StripeWebhookVerifier(SECRET).verify(
        payload=payload,
        signature_header=_signature(payload, at),
        received_at=at,
    )


def _authority(event_id: str, at: datetime) -> BillingAuthorityGrant:
    return BillingAuthorityGrant(
        provider=BillingProvider.STRIPE,
        integration_id="stripe-billing",
        provider_event_id=event_id,
        verified_at=at,
    )


def _checkout_object(capacity: int = 1) -> dict[str, object]:
    return {
        "id": "cs_test_fixture",
        "mode": "subscription",
        "customer": "cus_fixture",
        "subscription": "sub_fixture",
        "metadata": {
            "axignal_account_id": "account:1",
            "axignal_xeed_capacity": str(capacity),
        },
    }


def _subscription_object(*, capacity: int, status: str = "active") -> dict[str, object]:
    return {
        "id": "sub_fixture",
        "status": status,
        "items": {
            "data": [
                {"price": {"id": BASE_PRICE}, "quantity": 1},
                {
                    "price": {"id": ADDITIONAL_PRICE},
                    "quantity": max(0, capacity - 1),
                },
            ]
        },
    }


def _invoice_object(*, paid: bool, amount_minor: int = 995) -> dict[str, object]:
    return {
        "id": "in_fixture",
        "subscription": "sub_fixture",
        "amount_paid": amount_minor if paid else 0,
        "amount_due": amount_minor,
        "currency": "eur",
    }


def _bootstrap_checkout(tmp_path: Path, *, capacity: int = 1):
    accounts, billing = _stores(tmp_path)
    account_service = _signup(accounts)
    billing_service = AdminBillingService(billing, account_service)
    at = NOW + timedelta(seconds=10)
    raw = _payload("evt_checkout", "checkout.session.completed", at, _checkout_object(capacity))
    verified = _verify(raw, at)
    mapping, mapped_capacity = checkout_mapping_from_verified_event(
        verified,
        base_price_ref=BASE_PRICE,
        additional_xeed_price_ref=ADDITIONAL_PRICE,
        recorded_at=at,
    )
    result = billing_service.register_verified_checkout(
        authority=_authority(verified.event_id, at),
        mapping=mapping,
        xeed_capacity=mapped_capacity,
        now=at,
    )
    return accounts, billing, account_service, billing_service, result


def test_stripe_signature_verification_is_fail_closed() -> None:
    at = NOW + timedelta(seconds=10)
    raw = _payload("evt_1", "invoice.paid", at, _invoice_object(paid=True))
    verified = _verify(raw, at)
    assert verified.event_id == "evt_1"

    with pytest.raises(StripeWebhookError, match="signature mismatch"):
        StripeWebhookVerifier(SECRET).verify(
            payload=raw + b" ",
            signature_header=_signature(raw, at),
            received_at=at,
        )

    with pytest.raises(StripeWebhookError, match="outside tolerance"):
        StripeWebhookVerifier(SECRET).verify(
            payload=raw,
            signature_header=_signature(raw, at),
            received_at=at + timedelta(minutes=10),
        )


def test_checkout_maps_stripe_without_claiming_payment_or_access(tmp_path: Path) -> None:
    accounts, billing, _, _, result = _bootstrap_checkout(tmp_path, capacity=2)

    assert result.mapping_created is True
    mapping = billing.mapping_for_account("account:1")
    assert mapping is not None
    assert str(mapping.external_customer_id) == "cus_fixture"
    assert str(mapping.external_subscription_id) == "sub_fixture"

    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    assert snapshot.xeed_capacity == 2
    assert snapshot.payment_verification is PaymentVerificationState.EXTERNAL_PENDING

    with pytest.raises(ValueError, match="verified billing"):
        AdminCustomerAccountService(accounts).entitle_xeed(
            grant=_grant(),
            account_id="account:1",
            xeed_id="xeed:1",
            now=NOW + timedelta(seconds=11),
            reason="must not grant before invoice.paid",
        )


def test_subscription_quantity_and_invoice_paid_drive_billing_state(tmp_path: Path) -> None:
    accounts, billing, account_service, billing_service, _ = _bootstrap_checkout(
        tmp_path, capacity=1
    )
    normalizer = StripeEventNormalizer(billing)

    sub_at = NOW + timedelta(seconds=20)
    sub_raw = _payload(
        "evt_sub_update",
        "customer.subscription.updated",
        sub_at,
        _subscription_object(capacity=3),
    )
    sub_verified = _verify(sub_raw, sub_at)
    sub_event = normalizer.normalize(sub_verified, recorded_at=sub_at)
    billing_service.ingest_verified_event(
        authority=_authority(sub_verified.event_id, sub_at),
        event=sub_event,
        now=sub_at,
    )

    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    assert snapshot.xeed_capacity == 3
    assert snapshot.payment_verification is PaymentVerificationState.EXTERNAL_PENDING

    paid_at = NOW + timedelta(seconds=30)
    paid_raw = _payload(
        "evt_invoice_paid",
        "invoice.paid",
        paid_at,
        _invoice_object(paid=True, amount_minor=1985),
    )
    paid_verified = _verify(paid_raw, paid_at)
    paid_event = normalizer.normalize(paid_verified, recorded_at=paid_at)
    result = billing_service.ingest_verified_event(
        authority=_authority(paid_verified.event_id, paid_at),
        event=paid_event,
        now=paid_at,
    )

    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    assert snapshot.payment_verification is PaymentVerificationState.VERIFIED
    assert result.billing_snapshot.payment_state is BillingPaymentState.PAID
    assert result.billing_snapshot.xeed_capacity == 3

    account_service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:1",
        now=paid_at + timedelta(seconds=1),
        reason="first paid Xeed",
    )
    assert accounts.snapshot_for_tenant("tenant:1").entitled_xeed_ids == {"xeed:1"}

    quantities = quantities_for_xeed_capacity(3)
    assert quantities.base_quantity == 1
    assert quantities.additional_xeed_quantity == 2


def test_duplicate_webhook_is_replay_safe(tmp_path: Path) -> None:
    accounts, billing, _, billing_service, _ = _bootstrap_checkout(tmp_path)
    normalizer = StripeEventNormalizer(billing)
    paid_at = NOW + timedelta(seconds=20)
    raw = _payload("evt_paid_once", "invoice.paid", paid_at, _invoice_object(paid=True))
    verified = _verify(raw, paid_at)
    event = normalizer.normalize(verified, recorded_at=paid_at)

    first = billing_service.ingest_verified_event(
        authority=_authority(verified.event_id, paid_at),
        event=event,
        now=paid_at,
    )
    replay_event = normalizer.normalize(
        verified,
        recorded_at=paid_at + timedelta(seconds=15),
    )
    second = billing_service.ingest_verified_event(
        authority=_authority(verified.event_id, paid_at + timedelta(seconds=15)),
        event=replay_event,
        now=paid_at + timedelta(seconds=15),
    )

    assert first.replayed is False
    assert second.replayed is True
    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    billing_events = [event for event in accounts.all_events() if "billing:" in str(event.event_id)]
    assert len([event for event in billing_events if "evt_paid_once" in str(event.event_id)]) == 1


def test_out_of_order_old_failure_cannot_override_newer_paid_fact(tmp_path: Path) -> None:
    accounts, billing, _, billing_service, _ = _bootstrap_checkout(tmp_path)
    normalizer = StripeEventNormalizer(billing)

    paid_created = NOW + timedelta(seconds=40)
    paid = _verify(
        _payload("evt_paid_newer", "invoice.paid", paid_created, _invoice_object(paid=True)),
        paid_created,
    )
    billing_service.ingest_verified_event(
        authority=_authority(paid.event_id, paid_created),
        event=normalizer.normalize(paid, recorded_at=paid_created),
        now=paid_created,
    )

    failed_created = NOW + timedelta(seconds=30)
    failed_raw = _payload(
        "evt_failed_older",
        "invoice.payment_failed",
        failed_created,
        _invoice_object(paid=False),
    )
    failed = _verify(failed_raw, failed_created)
    billing_service.ingest_verified_event(
        authority=_authority(failed.event_id, paid_created + timedelta(seconds=20)),
        event=normalizer.normalize(
            failed,
            recorded_at=paid_created + timedelta(seconds=20),
        ),
        now=paid_created + timedelta(seconds=20),
    )

    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    assert snapshot.payment_verification is PaymentVerificationState.VERIFIED
    assert billing.snapshot("account:1").payment_state is BillingPaymentState.PAID


def test_newer_failed_payment_revokes_service_access(tmp_path: Path) -> None:
    accounts, billing, account_service, billing_service, _ = _bootstrap_checkout(tmp_path)
    normalizer = StripeEventNormalizer(billing)

    paid_at = NOW + timedelta(seconds=20)
    paid = _verify(
        _payload("evt_paid", "invoice.paid", paid_at, _invoice_object(paid=True)),
        paid_at,
    )
    billing_service.ingest_verified_event(
        authority=_authority(paid.event_id, paid_at),
        event=normalizer.normalize(paid, recorded_at=paid_at),
        now=paid_at,
    )
    account_service.entitle_xeed(
        grant=_grant(),
        account_id="account:1",
        xeed_id="xeed:1",
        now=paid_at + timedelta(seconds=1),
        reason="paid entitlement",
    )

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
    reader = EntitledXeedReader(
        AuthorizedXeedReader(authority, authority, authority),
        accounts,
    )
    context = TrustedRequestContext(principal_id=principal_id, tenant_id=tenant_id)
    assert reader.read(context, XeedId("xeed:1")).xeed.id == "xeed:1"

    failed_at = NOW + timedelta(seconds=40)
    failed = _verify(
        _payload(
            "evt_failed",
            "invoice.payment_failed",
            failed_at,
            _invoice_object(paid=False),
        ),
        failed_at,
    )
    billing_service.ingest_verified_event(
        authority=_authority(failed.event_id, failed_at),
        event=normalizer.normalize(failed, recorded_at=failed_at),
        now=failed_at,
    )

    with pytest.raises(ServiceXeedAccessError, match="billing is not verified"):
        reader.read(context, XeedId("xeed:1"))


def test_refund_and_cancellation_are_fail_closed(tmp_path: Path) -> None:
    accounts, billing, _, billing_service, _ = _bootstrap_checkout(tmp_path)
    normalizer = StripeEventNormalizer(billing)

    refund_at = NOW + timedelta(seconds=30)
    refund_obj = {
        "id": "ch_fixture",
        "amount_refunded": 995,
        "currency": "eur",
        "metadata": {
            "axignal_account_id": "account:1",
            "axignal_subscription_id": "sub_fixture",
        },
    }
    refund = _verify(
        _payload("evt_refund", "charge.refunded", refund_at, refund_obj),
        refund_at,
    )
    billing_service.ingest_verified_event(
        authority=_authority(refund.event_id, refund_at),
        event=normalizer.normalize(refund, recorded_at=refund_at),
        now=refund_at,
    )
    snapshot = accounts.snapshot_for_tenant("tenant:1")
    assert snapshot is not None
    assert snapshot.payment_verification is PaymentVerificationState.FAILED
    assert billing.snapshot("account:1").payment_state is BillingPaymentState.REFUNDED

    cancelled_at = NOW + timedelta(seconds=40)
    cancelled = _verify(
        _payload(
            "evt_cancel",
            "customer.subscription.deleted",
            cancelled_at,
            _subscription_object(capacity=1, status="canceled"),
        ),
        cancelled_at,
    )
    billing_service.ingest_verified_event(
        authority=_authority(cancelled.event_id, cancelled_at),
        event=normalizer.normalize(cancelled, recorded_at=cancelled_at),
        now=cancelled_at,
    )
    assert billing.snapshot("account:1").subscription_state.value == "CANCELLED"
    assert (
        accounts.snapshot_for_tenant("tenant:1").payment_verification
        is PaymentVerificationState.FAILED
    )


def test_xignals_are_not_billing_quantity() -> None:
    source = (
        Path("domain/admin_billing/model.py").read_text(encoding="utf-8")
        + Path("application/admin_billing/service.py").read_text(encoding="utf-8")
        + Path("pipeline/admin_billing/stripe.py").read_text(encoding="utf-8")
    )
    assert "xignal_quantity" not in source.lower()
    assert quantities_for_xeed_capacity(100).additional_xeed_quantity == 99


def test_runtime_stripe_webhook_http_flow_is_signed_and_replay_safe(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    config = RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="a" * 40,
        data_dir=tmp_path / "runtime",
        web_root=root / "apps" / "web",
        stripe_account_id="acct_fixture_axignal",
        stripe_base_price_ref=BASE_PRICE,
        stripe_additional_xeed_price_ref=ADDITIONAL_PRICE,
        stripe_webhook_signing_secret=SECRET.decode("utf-8"),
    )
    runtime = build_runtime(config)
    _register_stripe_integration(
        runtime,
        at=datetime.now(UTC) - timedelta(seconds=6),
    )
    _signup(
        runtime.admin_customer_account_store,
        at=datetime.now(UTC) - timedelta(seconds=5),
    )
    assert runtime.stripe_webhook is not None
    assert runtime.health_payload()["provider_ingress"] == "stripe-webhook-gated"

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    url = f"http://{host}:{port}/internal/webhooks/stripe"

    def post(raw: bytes, created: datetime) -> dict[str, object]:
        request = urllib.request.Request(
            url,
            data=raw,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": _signature(raw, created),
            },
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 200
            parsed = json.loads(response.read().decode("utf-8"))
        assert isinstance(parsed, dict)
        return parsed

    try:
        checkout_at = datetime.now(UTC) - timedelta(seconds=1)
        checkout_raw = _payload(
            "evt_http_checkout",
            "checkout.session.completed",
            checkout_at,
            _checkout_object(capacity=2),
        )
        checkout_response = post(checkout_raw, checkout_at)
        assert checkout_response["status"] == "accepted"
        assert checkout_response["replayed"] is False

        pending = runtime.admin_customer_account_store.snapshot_for_tenant("tenant:1")
        assert pending is not None
        assert pending.payment_verification is PaymentVerificationState.EXTERNAL_PENDING

        paid_at = datetime.now(UTC) - timedelta(seconds=1)
        paid_raw = _payload(
            "evt_http_paid",
            "invoice.paid",
            paid_at,
            _invoice_object(paid=True, amount_minor=1490),
        )
        first = post(paid_raw, paid_at)
        replay = post(paid_raw, paid_at)
        assert first["replayed"] is False
        assert replay["replayed"] is True

        verified = runtime.admin_customer_account_store.snapshot_for_tenant("tenant:1")
        assert verified is not None
        assert verified.payment_verification is PaymentVerificationState.VERIFIED
        assert verified.xeed_capacity == 2

        unsigned = urllib.request.Request(
            url,
            data=paid_raw,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(unsigned, timeout=5)
        assert exc.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_runtime_stripe_direct_checkout_composition(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    config = RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="a" * 40,
        data_dir=tmp_path / "runtime-direct",
        web_root=root / "apps" / "web",
        stripe_account_id="acct_fixture_axignal",
        stripe_base_price_ref=BASE_PRICE,
        stripe_additional_xeed_price_ref=ADDITIONAL_PRICE,
        stripe_webhook_signing_secret=SECRET.decode("utf-8"),
    )
    runtime = build_runtime(config)
    _register_stripe_integration(
        runtime,
        at=datetime.now(UTC) - timedelta(seconds=6),
    )
    _signup(
        runtime.admin_customer_account_store,
        at=datetime.now(UTC) - timedelta(seconds=5),
    )
    assert runtime.stripe_webhook is not None
    at = datetime.now(UTC) - timedelta(seconds=1)
    raw = _payload(
        "evt_direct_checkout",
        "checkout.session.completed",
        at,
        _checkout_object(capacity=2),
    )
    result = runtime.stripe_webhook.handle(
        payload=raw,
        signature_header=_signature(raw, at),
        received_at=datetime.now(UTC),
    )
    assert result.account_id == "account:1"


def test_runtime_stripe_ingress_requires_ao18_registry_authority(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    config = RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="b" * 40,
        data_dir=tmp_path / "runtime-ungoverned",
        web_root=root / "apps" / "web",
        stripe_account_id="acct_fixture_axignal",
        stripe_base_price_ref=BASE_PRICE,
        stripe_additional_xeed_price_ref=ADDITIONAL_PRICE,
        stripe_webhook_signing_secret=SECRET.decode("utf-8"),
    )
    runtime = build_runtime(config)
    _signup(
        runtime.admin_customer_account_store,
        at=datetime.now(UTC) - timedelta(seconds=5),
    )
    assert runtime.stripe_webhook is not None
    at = datetime.now(UTC) - timedelta(seconds=1)
    raw = _payload(
        "evt_ungoverned",
        "checkout.session.completed",
        at,
        _checkout_object(),
    )
    with pytest.raises(StripeWebhookError, match="not governed"):
        runtime.stripe_webhook.handle(
            payload=raw,
            signature_header=_signature(raw, at),
            received_at=datetime.now(UTC),
        )


def test_stripe_runtime_config_is_all_or_nothing_and_secret_safe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("AXIGNAL_DATA_DIR", str(tmp_path / "config-data"))
    monkeypatch.setenv("AXIGNAL_WEB_ROOT", str(root / "apps" / "web"))
    monkeypatch.setenv("AXIGNAL_STRIPE_ACCOUNT_ID", "acct_fixture_axignal")
    with pytest.raises(ValueError, match="requires account, both price refs and signing secret"):
        RuntimeConfig.from_env()

    monkeypatch.setenv("AXIGNAL_STRIPE_BASE_PRICE_REF", BASE_PRICE)
    monkeypatch.setenv("AXIGNAL_STRIPE_ADDITIONAL_XEED_PRICE_REF", ADDITIONAL_PRICE)
    monkeypatch.setenv("AXIGNAL_STRIPE_WEBHOOK_SIGNING_SECRET", SECRET.decode("utf-8"))
    config = RuntimeConfig.from_env()
    assert config.stripe_account_id == "acct_fixture_axignal"
    assert SECRET.decode("utf-8") not in repr(config)
