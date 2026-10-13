"""Actual HTTP, composed session/membership, durable preferences and billing ownership.

Only external identity exchange and financial provider IO are controlled; no live accounts.
"""

import base64
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from io import BytesIO
from random import Random
from threading import Thread

from PIL import Image

from application.admin_billing.subscriber_checkout import CurrentPurchaseAuthorityReader
from application.admin_billing.subscriber_management import SubscriberBillingManagement
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from tests.integration.test_subscriber_composition import _build, _commit_verified_projection
from tests.integration.test_subscriber_http import request, sign_in
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler


class ControlledPortal:
    def __init__(self):
        self.calls = []
        self.failure = False

    def portal(self, projection, *, action, locale, return_url):
        self.calls.append(
            (projection.tenant_id, projection.customer_ref, action, locale, return_url)
        )
        if self.failure:
            raise OSError("controlled unavailable provider")
        return "https://billing.stripe.com/p/session/controlled-e2e"


@contextmanager
def account_http(tmp_path):
    facade = _build(tmp_path)
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    provider = ControlledPortal()
    facade.management = SubscriberBillingManagement(
        CurrentPurchaseAuthorityReader(facade.identity.store, billing),
        billing,
        provider,
        "test",
        "https://axignal.com/account?billing=return",
        True,
    )
    runtime = build_runtime(
        RuntimeConfig("development", "127.0.0.1", 8765, "test", tmp_path / "http-data", tmp_path)
    )
    runtime.subscriber = facade
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, facade, billing, provider
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_complete_profile_and_billing_journey_over_actual_http(tmp_path):
    with account_http(tmp_path) as (server, facade, billing, provider):
        status, issued, _ = sign_in(server, code="account-owner")
        assert status == 200
        token = str(issued["sessionToken"])
        _, other, _ = sign_in(server, code="another-account")
        other_token = str(other["sessionToken"])
        context = facade.identity.authenticate(token)
        assert request(server, "/subscriber/profile")[0] == 401
        for index, locale in enumerate(["es", "en", "de", "pt", "fr", "it"]):
            status, saved = request(
                server,
                "/subscriber/profile",
                {"action": "locale", "locale": locale, "version": index},
                token=token,
            )
            assert status == 200 and saved["locale"] == locale
        assert request(server, "/subscriber/profile", token=other_token)[1]["locale"] is None
        # Incompressible bounded raster exercises the dedicated upload HTTP size limit (>8 KiB).
        pixels = Random(7).randbytes(128 * 128 * 3)
        image = Image.frombytes("RGB", (128, 128), pixels)
        out = BytesIO()
        image.save(out, format="PNG")
        encoded = base64.b64encode(out.getvalue()).decode()
        assert len(encoded) > 8192
        status, avatar = request(
            server,
            "/subscriber/profile",
            {"action": "avatar", "image": encoded, "version": 6},
            token=token,
        )
        assert status == 200 and avatar["avatar"].startswith("data:image/png;base64,")
        assert (
            _build(tmp_path)
            .handle("GET", "/subscriber/profile", {"Authorization": "Bearer " + token})
            .body
            == avatar
        )
        assert (
            request(
                server,
                "/subscriber/profile",
                {"action": "remove_avatar", "version": 6},
                token=token,
            )[0]
            == 409
        )
        assert (
            request(
                server,
                "/subscriber/profile",
                {"action": "remove_avatar", "version": 7},
                token=token,
                origin="https://other.test",
            )[0]
            == 403
        )
        status, removed = request(
            server, "/subscriber/profile", {"action": "remove_avatar", "version": 7}, token=token
        )
        assert status == 200 and removed["avatar"] is None and removed["locale"] == "it"
        status, automatic = request(
            server,
            "/subscriber/profile",
            {"action": "locale", "locale": None, "version": 8},
            token=token,
        )
        assert status == 200 and automatic["locale"] is None
        assert (
            request(server, "/subscriber/billing/management", token=token)[1]["state"]
            == "NO_SUBSCRIPTION"
        )
        _commit_verified_projection(billing, context.tenant_id, now=datetime.now(UTC))
        assert (
            request(server, "/subscriber/billing/management", token=token)[1]["canManage"] is True
        )
        for action in ["payment_method", "invoices", "cancel"]:
            status, portal = request(
                server,
                "/subscriber/billing/management",
                {"action": action, "locale": "es"},
                token=token,
            )
            assert status == 200 and portal["url"].startswith("https://billing.stripe.com/")
            assert provider.calls[-1] == (
                context.tenant_id,
                "customer:" + str(context.tenant_id),
                action,
                "es",
                "https://axignal.com/account?billing=return",
            )
        before = len(provider.calls)
        assert (
            request(
                server,
                "/subscriber/billing/management",
                {"action": "cancel", "locale": "es", "customer": "stolen"},
                token=token,
            )[0]
            == 400
        )
        assert (
            request(
                server,
                "/subscriber/billing/management",
                {"action": "cancel", "locale": "es"},
                token=other_token,
            )[0]
            == 503
        )
        assert len(provider.calls) == before
        provider.failure = True
        assert (
            request(
                server,
                "/subscriber/billing/management",
                {"action": "invoices", "locale": "es"},
                token=token,
            )[0]
            == 503
        )
        provider.failure = False
        assert (
            request(
                server,
                "/subscriber/billing/management",
                {"action": "invoices", "locale": "es"},
                token=token,
            )[0]
            == 200
        )
        # Opening the portal is no cancellation receipt and changes no entitlement.
        assert billing.get_billing_projection(context.tenant_id).lifecycle.value == "ELIGIBLE"
        facade.identity.store.remove_membership(context.principal_id, context.tenant_id)
        assert request(server, "/subscriber/profile", token=token)[0] == 401
        assert (
            request(
                server,
                "/subscriber/billing/management",
                {"action": "cancel", "locale": "es"},
                token=token,
            )[0]
            == 401
        )
        assert request(server, "/subscriber/profile", token=other_token)[0] == 200
