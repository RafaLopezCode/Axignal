from datetime import UTC, datetime

import pytest

from application.admin_billing.subscriber_billing import PaymentState, SubscriptionLifecycle
from application.admin_billing.subscriber_checkout import AuthorizedPurchaseScope, BillingProjection
from application.admin_billing.subscriber_management import (
    BillingManagementError,
    SubscriberBillingManagement,
)
from domain.identity import PrincipalId, TenantId
from domain.tenancy.model import Principal
from pipeline.admin_billing.stripe_subscriber import (
    StripeSubscriberAdapter,
    StripeSubscriberConfig,
)

NOW = datetime(2026, 10, 13, tzinfo=UTC)
OWNER = Principal(PrincipalId("owner"))
TENANT = TenantId("tenant")
PROJECTION = BillingProjection(
    TENANT,
    "cus_one",
    "sub_one",
    "cs_one",
    "env",
    None,
    1,
    PaymentState.VERIFIED,
    SubscriptionLifecycle.ELIGIBLE,
    None,
    "state",
    NOW,
    NOW,
)


class Authority:
    enabled = True

    def resolve(self, principal, tenant, *, now):
        if not self.enabled or principal != OWNER or tenant != TENANT:
            return None
        return AuthorizedPurchaseScope(principal.id, tenant, "owner-grant", "membership", now)


class Store:
    def get_billing_projection(self, tenant):
        return PROJECTION


class Transport:
    def __init__(self):
        self.calls = []
        self.customer = "cus_one"
        self.url = "https://billing.stripe.com/p/session/controlled"
        self.mode = "at_period_end"
        self.subscription_update = False

    def request(self, method, path, *, parameters, idempotency_key=None):
        self.calls.append((method, path, dict(parameters), idempotency_key))
        if path == "/v1/account":
            return {"id": "acct_one"}
        if path == "/v1/subscriptions/sub_one":
            return {"id": "sub_one", "customer": self.customer, "livemode": False}
        if path == "/v1/billing_portal/configurations" and method == "GET":
            return {"data": [], "has_more": False}
        if path == "/v1/billing_portal/configurations":
            return {
                "id": "bpc_one",
                "livemode": False,
                "active": True,
                "features": {
                    "payment_method_update": {"enabled": True},
                    "invoice_history": {"enabled": True},
                    "subscription_cancel": {"enabled": True, "mode": self.mode},
                    "subscription_update": {"enabled": self.subscription_update},
                    "customer_update": {"enabled": False},
                },
            }
        if path == "/v1/billing_portal/sessions":
            return {"customer": self.customer, "url": self.url}
        raise AssertionError(path)


def setup():
    transport = Transport()
    config = StripeSubscriberConfig(
        "env",
        "acct_one",
        False,
        "2026-08-26.dahlia",
        "base",
        "addon",
        {"base": "price_one", "addon": "price_two"},
        "https://axignal.test/account",
        "https://axignal.test/account",
        "rk_controlled",
        False,
    )
    provider = StripeSubscriberAdapter(config=config, transport=transport)
    authority = Authority()
    service = SubscriberBillingManagement(
        authority, Store(), provider, "env", "https://axignal.test/account?billing=return", True
    )
    return service, transport, authority


@pytest.mark.parametrize("action", ["payment_method", "invoices", "cancel"])
def test_portal_uses_authorized_mapping_and_restricted_configuration(action):
    service, transport, _ = setup()
    result = service.open(OWNER, TENANT, {"action": action, "locale": "es"}, NOW)
    assert result["state"] == "success"
    sessions = [call for call in transport.calls if call[1] == "/v1/billing_portal/sessions"]
    assert len(sessions) == 1 and sessions[0][2]["customer"] == "cus_one"
    if action == "cancel":
        assert sessions[0][2]["flow_data[subscription_cancel][subscription]"] == "sub_one"
    assert not any(
        call[1] == "/v1/subscriptions/sub_one" and call[0] == "POST" for call in transport.calls
    )
    configured = next(
        call
        for call in transport.calls
        if call[:2] == ("POST", "/v1/billing_portal/configurations")
    )
    assert configured[2]["features[subscription_update][enabled]"] == "false"
    assert configured[2]["features[subscription_cancel][mode]"] == "at_period_end"


@pytest.mark.parametrize(
    "body",
    [
        {"action": "cancel", "locale": "es", "customer": "cus_other"},
        {"action": "delete", "locale": "es"},
        {"action": [], "locale": "es"},
    ],
)
def test_browser_cannot_supply_provider_identity_or_arbitrary_actions(body):
    service, transport, _ = setup()
    with pytest.raises(ValueError):
        service.open(OWNER, TENANT, body, NOW)
    assert not transport.calls


def test_owner_revocation_and_provider_mapping_fail_closed():
    service, transport, authority = setup()
    with pytest.raises(BillingManagementError):
        service.open(
            Principal(PrincipalId("other")), TENANT, {"action": "invoices", "locale": "en"}, NOW
        )
    assert not transport.calls
    authority.enabled = False
    with pytest.raises(BillingManagementError):
        service.open(OWNER, TENANT, {"action": "invoices", "locale": "en"}, NOW)
    assert not transport.calls
    authority.enabled = True
    transport.customer = "cus_other"
    with pytest.raises(BillingManagementError):
        service.open(OWNER, TENANT, {"action": "cancel", "locale": "en"}, NOW)
    assert not any(call[1] == "/v1/billing_portal/sessions" for call in transport.calls)


@pytest.mark.parametrize(
    "url",
    [
        "https://billing.stripe.com.attacker.test/path",
        "https://user:pass@billing.stripe.com/path",
        "http://billing.stripe.com/path",
    ],
)
def test_portal_redirect_never_leaks_session_to_unapproved_host(url):
    service, transport, _ = setup()
    transport.url = url
    with pytest.raises(BillingManagementError):
        service.open(OWNER, TENANT, {"action": "payment_method", "locale": "es"}, NOW)


@pytest.mark.parametrize("mode,update", [("immediately", False), ("at_period_end", True)])
def test_configuration_cannot_cancel_immediately_or_bypass_capacity_policy(mode, update):
    service, transport, _ = setup()
    transport.mode = mode
    transport.subscription_update = update
    with pytest.raises(BillingManagementError):
        service.open(OWNER, TENANT, {"action": "cancel", "locale": "es"}, NOW)
    assert not any(call[1] == "/v1/billing_portal/sessions" for call in transport.calls)
