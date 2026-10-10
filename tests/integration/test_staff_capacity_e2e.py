"""Staff → grant → organization → subscriber sees it, over real Admin HTTP, with no checkout.

Issue #177: an authorized Admin adds organizations for internal research and for client
accounts without checkout or prior payment, through governed staff capacity. Nothing in
billing is created or edited, and another tenant never sees the work.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from application.subscriber_access.staff_capacity import StaffCapacityDestination
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from pipeline.admin_access import SqliteAdminAccessStore
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.integration import test_subscriber_composition as composition
from tests.integration.test_organization_admission_e2e import LOCATOR, _headers
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei
from tools.runtime import service as runtime_service
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import build_runtime, make_handler

WEB = Path(__file__).resolve().parents[2] / "apps" / "web"
ROUTE = "/internal/admin/staff-capacity"
SECOND = "Borealis Ingeniería SL https://www.borealis.example.com/"


def _registry(root: Path) -> ControlledRegistry:
    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    return ControlledRegistry(
        [
            entity(
                artifacts,
                legal_name="Solartec Energía SL",
                lei_value=lei("SOLARTEC0000000001"),
                websites=("https://www.solartec.example.com/",),
            ),
            entity(
                artifacts,
                legal_name="Borealis Ingeniería SL",
                lei_value=lei("BOREALIS000000001X"),
                websites=("https://www.borealis.example.com/",),
            ),
        ]
    )


class _Authenticator:
    def __init__(self, identities: dict[str, VerifiedAdminIdentity]) -> None:
        self._identities = identities

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identities.get(credential)


def _sessions(root: Path, now: datetime) -> tuple[str, str]:
    """A fresh STEP_UP founder session and a PRIMARY one, issued by the AO-01 service."""
    founder = AdminPrincipalId("founder")

    def identity(assurance: AdminAssurance) -> VerifiedAdminIdentity:
        return VerifiedAdminIdentity(founder, now, assurance, "test-admin-auth")

    service = AdminAccessService(
        SqliteAdminAccessStore(root / "admin-access.sqlite3"),
        _Authenticator(
            {
                "step-up": identity(AdminAssurance.STEP_UP),
                "primary": identity(AdminAssurance.PRIMARY),
            }
        ),
    )
    service.bootstrap_founder("step-up", occurred_at=now, reason="Test founder bootstrap")
    step_up = service.issue_session("step-up", authenticated_at=now).token
    primary = service.issue_session("primary", authenticated_at=now).token
    return step_up, primary


def _rows(path: Path) -> int:
    if not path.exists():
        return 0
    with sqlite3.connect(path) as db:
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return sum(int(db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]) for t in tables)


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    root = tmp_path / "runtime"
    root.mkdir()
    settings = composition._settings(root)
    settings = dataclasses.replace(
        settings,
        values={**settings.values, "AXIGNAL_STAFF_CAPACITY_ENABLED": "true"},
    )
    registry = _registry(root)
    monkeypatch.setattr(
        runtime_service,
        "build_subscriber_facade",
        functools.partial(runtime_service.build_subscriber_facade, identity_source=registry),
    )
    runtime = build_runtime(
        RuntimeConfig(
            environment="test",
            bind_host="127.0.0.1",
            port=0,
            code_sha="a" * 40,
            data_dir=root,
            web_root=WEB,
            admin_access_enabled=True,
            subscriber_settings=settings,
        )
    )
    assert runtime.subscriber is not None and runtime.subscriber.staff is not None
    runtime.subscriber.identity.auth._provider = composition._ControlledOidc()
    step_up, primary = _sessions(root, datetime.now(UTC))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def admin(
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        token: str | None = step_up,
        step_up_token: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        conn = HTTPConnection(*server.server_address)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        if step_up_token:
            headers["X-Axignal-Step-Up"] = "Bearer " + step_up_token
        conn.request(method, path, None if body is None else json.dumps(body), headers)
        response = conn.getresponse()
        status, result = response.status, json.loads(response.read())
        conn.close()
        return status, result

    try:
        yield {
            "root": root,
            "facade": runtime.subscriber,
            "admin": admin,
            "primary": primary,
            "step_up": step_up,
        }
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def _grant_body(tenant: str, key: str, capacity: int = 2) -> dict[str, object]:
    return {
        "tenantId": tenant,
        "destination": "CUSTOMER_ACCOUNT",
        "capacity": capacity,
        "reason": "Client account prepared by staff",
        "expiresAt": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "idempotencyKey": key,
    }


def test_staff_grant_and_add_reaches_the_subscriber_without_checkout(world: dict[str, Any]) -> None:
    facade, admin, root = world["facade"], world["admin"], world["root"]
    token, tenant = composition._signup(facade, "subject:client-a")
    other_token, other_tenant = composition._signup(facade, "subject:client-b")
    assert facade.handle("GET", "/subscriber/portfolio", _headers(token)).status == 200
    billing_before = _rows(root / "subscriber-billing.sqlite3")  # signup scope owners only

    body = _grant_body(str(tenant), "grant:a:1")
    status, preview = admin("POST", f"{ROUTE}/preview", body)
    assert status == 200 and preview["checkoutCreated"] is False
    status, granted = admin("POST", f"{ROUTE}/grant", body)
    assert status == 200, granted
    assert granted["entitlementSource"] == "STAFF_GRANT"
    assert granted["grant"]["provenance"] == "STAFF_GRANT_NOT_BILLING"
    replay = admin("POST", f"{ROUTE}/grant", body)  # a double submit is the same grant
    assert replay[1]["grant"]["grantRef"] == granted["grant"]["grantRef"]
    conflict = admin("POST", f"{ROUTE}/grant", {**body, "capacity": 9})
    assert conflict[0] == 409 and conflict[1]["reason"] == "IDEMPOTENCY_CONFLICT"

    add = {
        "tenantId": str(tenant),
        "locator": LOCATOR,
        "reason": "Add the client's own organization",
        "idempotencyKey": "staff-add:a:1",
    }
    status, added = admin("POST", f"{ROUTE}/organizations", add)
    assert status == 200 and added["status"] == "CREATED", added
    assert added["checkoutCreated"] is False
    again = admin("POST", f"{ROUTE}/organizations", add)[1]
    assert (again["status"], again["focusId"]) == ("ALREADY_PRESENT", added["focusId"])

    # The customer sees the organization in their own portfolio; the other tenant does not.
    read = facade.handle("GET", "/subscriber/portfolio", _headers(token))
    assert [o["focusId"] for o in read.body["organizations"]] == [added["focusId"]]
    other = facade.handle("GET", "/subscriber/portfolio", _headers(other_token))
    assert other.body["organizations"] == []
    output = facade.handle(
        "GET", f"/subscriber/organizations/{added['focusId']}/output", _headers(other_token)
    )
    assert output.status in {403, 404}

    status, state = admin("GET", f"{ROUTE}?tenantId={tenant}")
    assert status == 200 and state["activeStaffCapacity"] == 2
    actions = [row["action"] for row in state["audit"]]
    assert "CAPACITY_GRANTED" in actions and "ORGANIZATION_ADDED_BY_STAFF" in actions
    assert all(row["actor"] == "admin:founder" for row in state["audit"])

    # Payment separation: nothing in billing, no pilot grant, no checkout.
    assert _rows(root / "subscriber-billing.sqlite3") == billing_before
    with sqlite3.connect(root / "subscriber-billing.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM subscriber_billing_projection").fetchone()[0] == 0
    assert not (root / "subscriber-pilot.sqlite3").exists()
    assert other_tenant != tenant


def test_revocation_withdraws_capacity_and_a_full_portfolio_never_offers_checkout(
    world: dict[str, Any],
) -> None:
    facade, admin = world["facade"], world["admin"]
    token, tenant = composition._signup(facade, "subject:client-c")
    granted = admin("POST", f"{ROUTE}/grant", _grant_body(str(tenant), "grant:c:1", capacity=1))[1]
    first = admin(
        "POST",
        f"{ROUTE}/organizations",
        {
            "tenantId": str(tenant),
            "locator": LOCATOR,
            "reason": "First organization",
            "idempotencyKey": "c:1",
        },
    )[1]
    assert first["status"] == "CREATED"
    full = admin(
        "POST",
        f"{ROUTE}/organizations",
        {
            "tenantId": str(tenant),
            "locator": SECOND,
            "reason": "Second organization",
            "idempotencyKey": "c:2",
        },
    )[1]
    assert full["status"] == "CAPACITY_REQUIRED", full
    assert full["checkoutCreated"] is False

    status, revoked = admin(
        "POST",
        f"{ROUTE}/revoke",
        {"grantRef": granted["grant"]["grantRef"], "reason": "Engagement finished"},
    )
    assert status == 200 and revoked["grant"]["state"] == "REVOKED"
    assert revoked["entitlementSource"] == "UNKNOWN"
    after = admin(
        "POST",
        f"{ROUTE}/organizations",
        {
            "tenantId": str(tenant),
            "locator": LOCATOR,
            "reason": "After revocation",
            "idempotencyKey": "c:3",
        },
    )[1]
    assert after["status"] == "CAPACITY_UNKNOWN"
    assert facade.handle("GET", "/subscriber/portfolio", _headers(token)).status == 200


def test_admin_boundary_refuses_missing_session_missing_step_up_and_unknown_tenant(
    world: dict[str, Any],
) -> None:
    facade, admin, primary = world["facade"], world["admin"], world["primary"]
    _, tenant = composition._signup(facade, "subject:client-d")
    body = _grant_body(str(tenant), "grant:d:1")
    assert admin("POST", f"{ROUTE}/grant", body, token=None) == (
        401,
        {"reason": "ADMIN_SESSION_REQUIRED"},
    )
    assert admin("POST", f"{ROUTE}/grant", body, token=primary)[0] == 403
    assert admin("GET", f"{ROUTE}?tenantId={tenant}", token=primary)[0] == 200  # read only
    unknown = admin("POST", f"{ROUTE}/grant", _grant_body("tenant_does_not_exist", "grant:x:1"))
    assert unknown == (404, unknown[1]) and unknown[1]["reason"] == "TENANT_UNKNOWN"
    assert admin("POST", f"{ROUTE}/organizations", {
        "tenantId": "tenant_does_not_exist", "locator": LOCATOR,
        "reason": "No such tenant here", "idempotencyKey": "x:1",
    })[0] == 404  # fmt: skip
    assert admin("POST", f"{ROUTE}/unknown", body)[0] == 400
    assert admin("GET", f"{ROUTE}?tenantId={tenant}")[1]["grants"] == []


def test_staff_capacity_adds_to_verified_billing_without_editing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = composition._settings

    def with_staff(*args: Any, **kwargs: Any) -> Any:
        settings = original(*args, **kwargs)
        values = {**settings.values, "AXIGNAL_STAFF_CAPACITY_ENABLED": "true"}
        return dataclasses.replace(settings, values=values)

    monkeypatch.setattr(composition, "_settings", with_staff)
    facade = composition._build(tmp_path)
    _, tenant = composition._signup(facade, "subject:paying-client")
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    composition._commit_verified_projection(billing, tenant, now=datetime.now(UTC), capacity=1)
    before = billing.get_billing_projection(tenant)
    assert facade.staff.entitlement_source(tenant) == "BILLING"

    roles = frozenset({AdminRole.FOUNDER})
    founder = AdminAuthorizationGrant(
        AdminSessionId("session:founder"),
        AdminPrincipalId("founder"),
        roles,
        scopes_for_roles(roles),
        AdminAssurance.STEP_UP,
    )
    now = datetime.now(UTC)
    facade.staff.capacity.grant(
        founder,
        tenant_id=tenant,
        destination=StaffCapacityDestination.CUSTOMER_ACCOUNT,
        capacity=3,
        reason="Extra capacity for a paying client",
        expires_at=now + timedelta(days=30),
        idempotency_key="grant:paying:1",
        now=now,
    )
    assert facade.staff.entitlement_source(tenant) == "BILLING+STAFF_GRANT"
    assert billing.get_billing_projection(tenant) == before  # paid capacity untouched


def test_private_step_up_proof_requires_live_primary_same_actor_and_fresh_step_up(
    world: dict[str, Any],
) -> None:
    root = world["root"]
    admin = world["admin"]
    primary = world["primary"]
    step_up = world["step_up"]
    path = "/internal/admin/step-up/verify"

    good_status, good_body = admin("GET", path, token=primary, step_up_token=step_up)
    assert (good_status, good_body) == (200, {"authorized": True})
    assert admin("GET", path, token=primary)[0] == 401
    assert admin("GET", path, token=primary, step_up_token=primary)[0] == 403
    assert admin("GET", path, token=step_up, step_up_token=step_up)[0] == 403
    assert admin("GET", path, token="not-a-token", step_up_token=step_up)[0] == 401

    store = SqliteAdminAccessStore(root / "admin-access.sqlite3")
    now = datetime.now(UTC)
    other = AdminPrincipalId("another-operator")
    founder = AdminAccessService(
        store,
        _Authenticator(
            {"unused": VerifiedAdminIdentity(other, now, AdminAssurance.STEP_UP, "test")}
        ),
    )
    from domain.admin_access import PrivilegeChangeKind

    founder.change_role(
        step_up,
        target_principal_id=other,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now,
        reason="Additional operator for protected test",
    )
    issued_for_other = founder.issue_session("unused", authenticated_at=now).token
    assert admin("GET", path, token=primary, step_up_token=issued_for_other)[0] == 403
    assert admin("GET", path, token=primary, step_up_token=step_up)[0] == 200
