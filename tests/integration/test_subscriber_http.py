"""Real HTTP + durable identity tests with an explicitly controlled OIDC exchange."""

import json
from collections.abc import Iterator
from datetime import datetime
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from application.subscriber_identity.runtime import (
    OidcProviderConfig,
    OidcProviderId,
    OidcTransaction,
    PurchaseScopeProvisioningReceipt,
    SubscriberAuthenticationService,
    SystemClock,
    TrustedSubscriberContext,
    VerifiedExternalIdentity,
)
from application.xeed_access.reader import ReadFailure, XeedReadError
from domain.identity import PrincipalId, TenantId, XeedId
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler
from tools.runtime.subscriber_configuration import load_subscriber_settings
from tools.runtime.subscriber_http import SubscriberHttpFacade
from tools.runtime.subscriber_identity import SubscriberIdentityRuntime


class ControlledOidc:
    def authorization_url(
        self, config: OidcProviderConfig, *, state: str, nonce: str, code_challenge: str
    ) -> str:
        return (
            config.authorization_endpoint
            + "?"
            + urlencode({"state": state, "nonce": nonce, "code_challenge": code_challenge})
        )

    def exchange_and_verify(
        self, config: OidcProviderConfig, transaction: OidcTransaction, code: str
    ) -> VerifiedExternalIdentity:
        assert transaction.client_id == config.client_id
        return VerifiedExternalIdentity(config.issuer, code)


class ControlledPurchaseProvisioner:
    def ensure_initial_purchase_scope(
        self, principal_id: PrincipalId, initial_tenant_id: TenantId, registration_key: str
    ) -> PurchaseScopeProvisioningReceipt:
        return PurchaseScopeProvisioningReceipt(
            principal_id, initial_tenant_id, registration_key, True
        )


class ControlledWorkflow:
    def __init__(self) -> None:
        self.reads: list[TrustedSubscriberContext] = []
        self.commands: list[dict[str, object]] = []

    def portfolio(self, context: TrustedSubscriberContext) -> dict[str, object]:
        self.reads.append(context)
        return {
            "state": "success",
            "capacity": None,
            "capacityCurrentness": "UNKNOWN",
            "canPurchase": None,
            "contractingEnabled": False,
            "organizations": [],
        }

    def command(
        self, context: TrustedSubscriberContext, command: dict[str, object]
    ) -> dict[str, object]:
        self.reads.append(context)
        self.commands.append(command)
        return {"state": "IDENTITY_PENDING", "requestRef": command["requestRef"]}


class ControlledOutput:
    def __init__(self) -> None:
        self.reads = 0

    def output(
        self, context: TrustedSubscriberContext, focus_id: XeedId, as_of: datetime
    ) -> dict[str, object]:
        del context, focus_id, as_of
        self.reads += 1
        raise XeedReadError(ReadFailure.XEED_ACCESS_DENIED)


SubscriberServer = tuple[
    ThreadingHTTPServer, SqliteSubscriberIdentityStore, ControlledWorkflow, ControlledOutput
]


@pytest.fixture
def subscriber_server(tmp_path: Path) -> Iterator[SubscriberServer]:
    web = tmp_path / "web"
    web.mkdir()
    runtime = build_runtime(
        RuntimeConfig("development", "127.0.0.1", 8765, "test", tmp_path / "data", web)
    )
    store = SqliteSubscriberIdentityStore(tmp_path / "subscriber.sqlite3")
    config = OidcProviderConfig(
        OidcProviderId.GOOGLE,
        "https://accounts.google.com",
        "controlled-client",
        "https://axignal.com/api/auth/callback/google",
        True,
        True,
        "https://accounts.google.com/o/oauth2/v2/auth",
        "https://oauth2.googleapis.com/token",
        "https://www.googleapis.com/oauth2/v3/certs",
    )
    auth = SubscriberAuthenticationService(
        {OidcProviderId.GOOGLE: config},
        ControlledOidc(),
        store,
        store,
        store,
        ControlledPurchaseProvisioner(),
        SystemClock(),
    )
    workflow, output = ControlledWorkflow(), ControlledOutput()
    runtime.subscriber = SubscriberHttpFacade(
        settings=load_subscriber_settings(
            {
                "AXIGNAL_SUBSCRIBER_ENABLED": "true",
                "AXIGNAL_EXPERIENCE_ORIGIN": "https://axignal.com",
            }
        ),
        identity=SubscriberIdentityRuntime(auth, store),
        workflow=workflow,
        outputs=output,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, store, workflow, output
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def request(
    server: ThreadingHTTPServer,
    path: str,
    body: dict[str, object] | None = None,
    *,
    token: str | None = None,
    origin: str = "https://axignal.com",
) -> tuple[int, dict[str, object]]:
    connection = HTTPConnection(*server.server_address[:2], timeout=5)
    headers = {"Origin": origin, "Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    try:
        connection.request(
            "GET" if body is None else "POST",
            path,
            body=None if body is None else json.dumps(body),
            headers=headers,
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def sign_in(
    server: ThreadingHTTPServer, *, intent: str = "signup", code: str = "controlled-person"
) -> tuple[int, dict[str, object], dict[str, object]]:
    status, started = request(
        server, "/subscriber/auth/start", {"provider": "google", "intent": intent}
    )
    assert status == 200
    state = parse_qs(urlsplit(str(started["authorizationUrl"])).query)["state"][0]
    callback: dict[str, object] = {
        "provider": "google",
        "transactionToken": started["transactionToken"],
        "state": state,
        "code": code,
    }
    status, issued = request(server, "/subscriber/auth/callback", callback)
    return status, issued, callback


def test_real_http_session_hash_restart_replay_and_revocation(
    subscriber_server: SubscriberServer,
) -> None:
    server, store, workflow, _ = subscriber_server
    status, issued, callback = sign_in(server)
    assert status == 200
    token = str(issued["sessionToken"])
    assert token.encode() not in store.path.read_bytes()
    assert (
        SqliteSubscriberIdentityStore(store.path).resolve(
            SubscriberAuthenticationService._digest(token), SystemClock().now()
        )
        is not None
    )
    assert request(server, "/subscriber/auth/callback", callback)[0] == 401
    status, portfolio = request(server, "/subscriber/portfolio", token=token)
    assert status == 200 and portfolio["capacity"] is None
    assert request(server, "/subscriber/auth/logout", {}, token=token)[0] == 200
    count = len(workflow.reads)
    assert request(server, "/subscriber/portfolio", token=token)[0] == 401
    assert len(workflow.reads) == count


def test_http_cannot_select_tenant_or_promote_attention_to_truth(
    subscriber_server: SubscriberServer,
) -> None:
    server, _, workflow, _ = subscriber_server
    status, issued, _ = sign_in(server)
    assert status == 200
    token = str(issued["sessionToken"])
    command: dict[str, object] = {
        "action": "add",
        "requestRef": "request:one",
        "locator": "Some organization",
    }
    assert (
        request(
            server, "/subscriber/portfolio", {**command, "tenantId": "tenant:foreign"}, token=token
        )[0]
        == 400
    )
    assert (
        request(
            server, "/subscriber/portfolio", command, token=token, origin="https://evil.example"
        )[0]
        == 403
    )
    assert workflow.commands == []
    status, result = request(server, "/subscriber/portfolio", command, token=token)
    assert status == 200 and result["state"] == "IDENTITY_PENDING"
    assert "organizationId" not in result


def test_login_unknown_identity_and_private_output_denial(
    subscriber_server: SubscriberServer,
) -> None:
    server, _, _, output = subscriber_server
    assert sign_in(server, intent="login", code="unbound-person")[0] == 401
    _, issued, _ = sign_in(server)
    assert request(
        server, "/subscriber/organizations/foreign/output", token=str(issued["sessionToken"])
    ) == (403, {"state": "rejected", "code": "ACCESS_DENIED"})
    assert request(server, "/subscriber/organizations/foreign/output")[0] == 401
    assert output.reads == 1


@pytest.mark.parametrize("capacity", [1, 2, 100, True, 1.1])
def test_contracting_gate_never_grants_capacity(
    subscriber_server: SubscriberServer, capacity: object
) -> None:
    server, _, workflow, _ = subscriber_server
    _, issued, _ = sign_in(server)
    status, _ = request(
        server,
        "/subscriber/portfolio",
        {"action": "purchase", "requestRef": "purchase:one", "desiredOrganizationTotal": capacity},
        token=str(issued["sessionToken"]),
    )
    assert status == (400 if type(capacity) is not int else 409)
    assert workflow.commands == []
