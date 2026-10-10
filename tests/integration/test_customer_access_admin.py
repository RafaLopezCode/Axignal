"""Real Admin HTTP + durable subscriber services; OIDC is a controlled provider."""

from __future__ import annotations

import dataclasses
import functools
import json
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.subscriber_access.pilot import PilotAccessService
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from tests.first_observation.harness import World, registered_rights
from tests.first_observation.harness import runtime as observation_runtime
from tests.integration import test_subscriber_composition as composition
from tests.integration.test_organization_admission_e2e import LOCATOR, _headers
from tests.integration.test_staff_capacity_e2e import world as staff_world
from tools.runtime import service as runtime_service
from tools.runtime.first_observation import FirstObservationOverrides

ROUTE = "/internal/admin/customer-access"


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    sources = World()
    monkeypatch.setattr(
        runtime_service,
        "build_subscriber_facade",
        functools.partial(
            runtime_service.build_subscriber_facade,
            first_observation_overrides=FirstObservationOverrides(
                enabled=True,
                worker="manual",
                fetcher=sources.sites,
                source_ports={"ted-search-v3": sources.ted},
                feeds={"ted-search-v3": sources.ted},
                rights=registered_rights(),
                cascade_factory=lambda: None,
            ),
        ),
    )
    settings = composition._settings

    def pilot_settings(root: Path) -> Any:
        original = settings(root)
        return dataclasses.replace(
            original, values={**original.values, "AXIGNAL_SUBSCRIBER_PILOT_ENABLED": "true"}
        )

    monkeypatch.setattr(composition, "_settings", pilot_settings)
    yield from staff_world.__wrapped__(tmp_path, monkeypatch)


def issue(key: str = "invite:customer:1") -> dict[str, object]:
    return {
        "reason": "Private design partner validation",
        "inviteHours": 168,
        "idempotencyKey": key,
    }


def test_admin_issue_onboarding_redeem_activation_and_revocation(world: dict[str, Any]) -> None:
    facade, admin, root = world["facade"], world["admin"], world["root"]
    assert facade.pilot_admin is not None
    assert admin("POST", ROUTE + "/issue", issue(), token=world["primary"])[0] == 403
    assert admin("GET", ROUTE, token=None)[0] == 401
    status, invite = admin("POST", ROUTE + "/issue", issue())
    assert status == 200, invite
    token = invite["inviteToken"]
    assert token.encode() not in (root / "subscriber-pilot.sqlite3").read_bytes()
    repeated = admin("POST", ROUTE + "/issue", issue())
    assert repeated[0] == 409 and repeated[1]["reason"] == "INVITE_ALREADY_ISSUED"
    assert "inviteToken" not in repeated[1]
    assert (
        admin("POST", ROUTE + "/issue", {**issue(), "inviteHours": 24})[1]["reason"]
        == "IDEMPOTENCY_CONFLICT"
    )

    subscriber, tenant = composition._signup(facade, "subject:design-partner")
    other, _ = composition._signup(facade, "subject:another-tenant")
    attention = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(subscriber),
        {"action": "add", "requestRef": "attention:before-pilot", "locator": LOCATOR},
    )
    assert attention.body["state"] == "CAPACITY_UNKNOWN"
    pending = facade.handle("GET", "/subscriber/portfolio", _headers(subscriber)).body[
        "organizations"
    ][0]["focusId"]
    assert (
        facade.handle(
            "POST", "/subscriber/pilot/redeem", _headers(subscriber), {"inviteToken": token}
        ).body["state"]
        == "PILOT_ACTIVE"
    )
    duplicate = facade.handle(
        "POST", "/subscriber/pilot/redeem", _headers(subscriber), {"inviteToken": token}
    )
    assert duplicate.body["state"] == "PILOT_INVITE_INVALID"
    stolen = facade.handle(
        "POST", "/subscriber/pilot/redeem", _headers(other), {"inviteToken": token}
    )
    assert stolen.body["state"] == "PILOT_INVITE_INVALID"
    activated = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(subscriber),
        {"action": "retry_pending", "requestRef": "activate:pilot:1", "focusId": pending},
    )
    assert activated.body["state"] == "CREATED", activated.body
    client = facade.handle("GET", "/subscriber/portfolio", _headers(subscriber))
    assert client.body["capacity"] == 1
    assert len(client.body["organizations"]) == 1
    assert observation_runtime(facade).drain() == 1
    observed = facade.handle("GET", "/subscriber/portfolio", _headers(subscriber))
    assert observed.body["organizations"][0]["observation"]["firstProofReady"] is True

    assert (
        facade.handle("GET", "/subscriber/portfolio", _headers(other)).body["organizations"] == []
    )
    status, view = admin("GET", ROUTE, token=world["primary"])
    assert status == 200, view
    assert token not in json.dumps(view) and "token_digest" not in json.dumps(view)
    assert view["pilot"]["invites"][0]["state"] == "REDEEMED"
    assert view["pilot"]["invites"][0]["redeemed_tenant_id"] == str(tenant)
    grant = view["pilot"]["grants"][0]
    revoke = {
        "reference": grant["grant_ref"],
        "reason": "Design partner test completed",
        "idempotencyKey": "revoke:grant:1",
    }
    assert admin("POST", ROUTE + "/revoke-grant", revoke)[0] == 200
    assert admin("POST", ROUTE + "/revoke-grant", revoke)[0] == 200
    assert (
        facade.handle("GET", "/subscriber/portfolio", _headers(subscriber)).body["capacity"] is None
    )
    assert (
        len(
            facade.handle("GET", "/subscriber/portfolio", _headers(subscriber)).body[
                "organizations"
            ]
        )
        == 1
    )
    with sqlite3.connect(root / "subscriber-pilot.sqlite3") as db:
        assert [r[0] for r in db.execute("SELECT action FROM subscriber_pilot_audit")] == [
            "ISSUED",
            "REDEEMED",
            "GRANT_REVOKED",
        ]


def test_revoke_unused_expiry_limits_and_no_secret_listing(world: dict[str, Any]) -> None:
    admin, facade = world["admin"], world["facade"]
    _, invite = admin("POST", ROUTE + "/issue", issue())
    revoke = {
        "reference": invite["inviteRef"],
        "reason": "Invitation no longer required",
        "idempotencyKey": "revoke:invite:1",
    }
    assert admin("POST", ROUTE + "/revoke-invite", revoke)[0] == 200
    subscriber, _ = composition._signup(facade, "subject:revoked")
    assert (
        facade.handle(
            "POST",
            "/subscriber/pilot/redeem",
            _headers(subscriber),
            {"inviteToken": invite["inviteToken"]},
        ).body["state"]
        == "PILOT_INVITE_INVALID"
    )
    assert admin("GET", ROUTE)[1]["pilot"]["invites"][0]["state"] == "REVOKED"
    for hours in (0, 721, True):
        assert (
            admin(
                "POST", ROUTE + "/issue", {**issue(str(hours) + ":invalid"), "inviteHours": hours}
            )[0]
            == 400
        )
    assert admin("POST", ROUTE + "/issue", {**issue(), "tenantId": "foreign"})[0] == 400
    assert (
        admin(
            "POST",
            ROUTE + "/revoke-invite",
            {**revoke, "reference": "nonexistent", "idempotencyKey": "revoke:missing"},
        )[0]
        == 404
    )


def test_creation_rate_limit_is_durable_and_replays_do_not_consume_quota(
    world: dict[str, Any],
) -> None:
    admin = world["admin"]
    for number in range(20):
        assert admin("POST", ROUTE + "/issue", issue(f"invite:quota:{number}"))[0] == 200
    assert admin("POST", ROUTE + "/issue", issue("invite:quota:20"))[0] == 429
    assert admin("POST", ROUTE + "/issue", issue("invite:quota:0"))[0] == 409
    assert len(admin("GET", ROUTE)[1]["pilot"]["invites"]) == 20


def test_atomic_audit_failure_rolls_back_issuance(
    world: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SqlitePilotAccessStore(world["root"] / "subscriber-pilot.sqlite3")

    def fail(*args: Any, **kwargs: Any) -> None:
        raise sqlite3.OperationalError("controlled audit failure")

    monkeypatch.setattr(store, "_audit", fail)
    with pytest.raises(sqlite3.OperationalError):
        PilotAccessService(store).issue_invite(
            issued_by="staff", reason="atomic check", now=datetime.now(UTC)
        )
    assert store.inventory(now=datetime.now(UTC))["invites"] == []


def test_expired_sessions_and_membership_removal_fail_closed(world: dict[str, Any]) -> None:
    admin, facade, root = world["admin"], world["facade"], world["root"]
    subscriber, tenant = composition._signup(facade, "subject:membership")
    principal = facade.identity.authenticate(subscriber).principal_id
    facade.identity.store.remove_membership(principal, tenant)
    assert admin("GET", ROUTE)[1]["customers"] == []
    with sqlite3.connect(root / "admin-access.sqlite3") as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "admin_sessions" in tables
        db.execute(
            "UPDATE admin_sessions SET issued_at=?, expires_at=?",
            (
                (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
                (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            ),
        )
    assert admin("GET", ROUTE)[0] == 401
    assert admin("POST", ROUTE + "/issue", issue())[0] == 401


def test_expired_step_up_and_subscriber_credentials_cannot_write(world: dict[str, Any]) -> None:
    admin, facade, root = world["admin"], world["facade"], world["root"]
    subscriber, _ = composition._signup(facade, "subject:not-staff")
    assert admin("GET", ROUTE, token=subscriber)[0] == 401
    assert admin("POST", ROUTE + "/issue", issue(), token=subscriber)[0] == 401
    with sqlite3.connect(root / "admin-access.sqlite3") as db:
        db.execute(
            "UPDATE admin_sessions SET issued_at=? WHERE assurance='STEP_UP'",
            ((datetime.now(UTC) - timedelta(minutes=20)).isoformat(),),
        )
    assert admin("GET", ROUTE)[0] == 200
    assert admin("POST", ROUTE + "/issue", issue())[0] == 403
    assert admin("GET", ROUTE)[1]["pilot"]["invites"] == []
