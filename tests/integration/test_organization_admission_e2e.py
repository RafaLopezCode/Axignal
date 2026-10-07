"""Spec 052 end to end through the real subscriber composition.

verified Principal → Tenant → PilotGrant(capacity 1) → POST add locator → independent
registry admission → canonical Organization → private Focus → restart → subscriber read.
And the negative paths: unresolved, ambiguous, replay, two Tenants, unauthorized.
The registry is a controlled offline source behind the production port; admission goes
through EvidenceAdmission and the one canonical store exactly as in production.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.organization_admission.service import organization_id_for
from application.subscriber_access.pilot import PilotAccessService
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from tests.integration.test_subscriber_composition import (
    _build,
    _commit_verified_projection,
    _signup,
)
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei

ORIGIN = "https://axignal.com"
SOLAR = lei("SOLARTEC0000000001")
ACME_ONE = lei("ACMEONE00000000001")
ACME_TWO = lei("ACMETWO00000000002")
# One line, as the web form sends it: the HTTP edge refuses control characters.
LOCATOR = "Solartec Energía SL https://www.solartec.example.com/"


def _registry(tmp_path: Path) -> ControlledRegistry:
    # Same content-addressed store the composition verifies identity artifacts against.
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    return ControlledRegistry(
        [
            entity(
                artifacts,
                legal_name="Solartec Energía SL",
                lei_value=SOLAR,
                websites=("https://www.solartec.example.com/",),
            ),
            entity(artifacts, legal_name="Acme SL", lei_value=ACME_ONE),
            entity(artifacts, legal_name="ACME SL", lei_value=ACME_TWO),
        ]
    )


def _facade(tmp_path: Path, registry: ControlledRegistry) -> Any:
    return _build(tmp_path, pilot=True, identity_source=registry)


def _headers(token: str | None = None) -> dict[str, str]:
    headers = {"Origin": ORIGIN}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _pilot(facade: Any, tmp_path: Path, subject: str) -> tuple[str, str]:
    token, tenant = _signup(facade, subject)
    invite = PilotAccessService(SqlitePilotAccessStore(tmp_path / "subscriber-pilot.sqlite3"))
    redeemed = facade.handle(
        "POST",
        "/subscriber/pilot/redeem",
        _headers(token),
        {"inviteToken": invite.issue_invite(
            issued_by="founder", reason="design partner", now=datetime.now(UTC)
        ).invite_token},
    )  # fmt: skip
    assert redeemed.body["state"] == "PILOT_ACTIVE"
    return token, str(tenant)


def _add(facade: Any, token: str, ref: str, locator: str = LOCATOR) -> Any:
    return facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token),
        {"action": "add", "requestRef": ref, "locator": locator},
    )


def _portfolio(facade: Any, token: str) -> list[dict[str, Any]]:
    read = facade.handle("GET", "/subscriber/portfolio", _headers(token))
    assert read.status == 200, read.body
    return list(read.body["organizations"])


def _count(tmp_path: Path, database: str, table: str) -> int:
    with sqlite3.connect(tmp_path / database) as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _organizations(tmp_path: Path) -> int:
    return _count(tmp_path, "canonical-organizations.sqlite3", "canonical_legal_identities")


def _focuses(tmp_path: Path) -> int:
    return _count(tmp_path, "subscriber-runtime.sqlite3", "subscriber_focuses")


def test_single_tenant_pilot_admits_one_organization_and_survives_restart(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    facade = _facade(tmp_path, registry)
    token, _ = _pilot(facade, tmp_path, "subject:pilot-a")
    assert _organizations(tmp_path) == 0  # nothing canonical before attention resolves

    added = _add(facade, token, "add:solar")
    assert added.status == 200 and added.body["state"] == "CREATED", added.body
    organization_id = str(organization_id_for("LEI", "GLEIF", SOLAR))
    assert added.body["organizationId"] == organization_id
    focus = str(added.body["focusId"])
    assert "observationState" in added.body  # handed to the existing observation runtime
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)

    # Restart: a new process over the same data resolves the same identity and Focus.
    restarted = _facade(tmp_path, registry)
    calls = registry.calls
    (entry,) = _portfolio(restarted, token)
    assert (entry["focusId"], entry["organizationId"], entry["state"]) == (
        focus,
        organization_id,
        "ACTIVE",
    )
    output = restarted.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(token))
    assert output.status == 200, output.body
    assert output.body["projection"]["organization"]["name"] == "Solartec Energía SL"
    again = _add(restarted, token, "add:solar:again", "https://solartec.example.com")
    assert (again.body["state"], again.body["focusId"]) == ("ALREADY_PRESENT", focus)
    assert registry.calls == calls  # known identity: no source call, no new admission
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)


def test_unresolved_identity_is_pending_with_zero_canonical_state_until_the_source_attests(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path)
    facade = _facade(tmp_path, registry)
    token, _ = _pilot(facade, tmp_path, "subject:pilot-pending")
    pending = _add(
        facade, token, "add:unknown", "Nueva Fotovoltaica SL https://nuevafv.example.com/"
    )
    assert pending.status == 200
    assert (pending.body["state"], pending.body["reason"]) == (
        "IDENTITY_PENDING",
        "NOT_FOUND_IN_IDENTITY_SOURCE",
    )
    (item,) = _portfolio(facade, token)
    assert (item["state"], item["organizationId"], item["reason"]) == (
        "IDENTITY_PENDING",
        None,
        "NOT_FOUND_IN_IDENTITY_SOURCE",
    )
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (0, 0)
    output = facade.handle(
        "GET", f"/subscriber/organizations/{item['focusId']}/output", _headers(token)
    )
    assert output.status in (403, 404)  # a pending request is not an observable Xeed

    # The registry later attests the entity; retrying the same request resolves it.
    registry.records.append(
        entity(
            ContentAddressedArtifactStore(tmp_path / "artifacts"),
            legal_name="Nueva Fotovoltaica SL",
            lei_value=lei("NUEVAFV00000000001"),
            websites=("https://nuevafv.example.com/",),
        )
    )
    retried = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token),
        {"action": "retry_pending", "requestRef": "retry:unknown", "focusId": item["focusId"]},
    )
    assert retried.body["state"] == "CREATED", retried.body
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)


def test_source_unavailable_and_ambiguous_names_never_create_state(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    facade = _facade(tmp_path, registry)
    token, _ = _pilot(facade, tmp_path, "subject:pilot-ambiguous")
    ambiguous = _add(facade, token, "add:acme", "Acme SL")
    assert (ambiguous.body["state"], ambiguous.body["reason"]) == (
        "IDENTITY_PENDING",
        "AMBIGUOUS:SOURCE_RETURNED_SEVERAL_IDENTITIES",
    )
    registry.available = False
    unavailable = _add(facade, token, "add:offline", "Offline Example SL")
    assert unavailable.body["reason"] == "IDENTITY_SOURCE_UNAVAILABLE"
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (0, 0)


def test_replayed_request_creates_one_organization_and_one_focus(tmp_path: Path) -> None:
    facade = _facade(tmp_path, _registry(tmp_path))
    token, _ = _pilot(facade, tmp_path, "subject:pilot-replay")
    first = _add(facade, token, "add:replay")
    replay = _add(facade, token, "add:replay")
    assert first.body["state"] == "CREATED"
    assert replay.body["focusId"] == first.body["focusId"]
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)


def test_two_tenants_share_one_canonical_organization_with_isolated_foci(tmp_path: Path) -> None:
    facade = _facade(tmp_path, _registry(tmp_path))
    token_a, tenant_a = _pilot(facade, tmp_path, "subject:tenant-a")
    token_b, tenant_b = _signup(facade, "subject:tenant-b")
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(billing, tenant_b, now=datetime.now(UTC))
    added_a = _add(facade, token_a, "add:a")
    added_b = _add(facade, token_b, "add:b", f"LEI {SOLAR}")
    assert added_a.body["state"] == added_b.body["state"] == "CREATED"
    assert added_a.body["organizationId"] == added_b.body["organizationId"]
    assert added_a.body["focusId"] != added_b.body["focusId"]
    assert tenant_a != str(tenant_b)
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 2)
    # Each Tenant sees only its Focus; the other's Focus id opens nothing.
    assert [item["focusId"] for item in _portfolio(facade, token_a)] == [added_a.body["focusId"]]
    for token, foreign in ((token_a, added_b.body["focusId"]), (token_b, added_a.body["focusId"])):
        read = facade.handle("GET", f"/subscriber/organizations/{foreign}/output", _headers(token))
        assert read.status in (403, 404) and "projection" not in read.body
    # Removing a private Focus never deletes the shared canonical Organization.
    removed = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token_a),
        {"action": "remove", "requestRef": "remove:a", "focusId": added_a.body["focusId"]},
    )
    assert removed.body["state"] == "REMOVED"
    assert _organizations(tmp_path) == 1
    still = facade.handle(
        "GET", f"/subscriber/organizations/{added_b.body['focusId']}/output", _headers(token_b)
    )
    assert still.status == 200


def test_unauthorized_and_forged_requests_fail_before_any_identity_work(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    facade = _facade(tmp_path, registry)
    # No session, forged session, and a Tenant without entitlement.
    assert _add(facade, None, "add:anon").status == 401  # type: ignore[arg-type]
    assert _add(facade, "forged-session-token-" + "x" * 30, "add:forged").status == 401
    unentitled, _ = _signup(facade, "subject:no-entitlement")
    refused = _add(facade, unentitled, "add:no-entitlement")
    assert refused.body["state"] == "CAPACITY_UNKNOWN"
    assert registry.calls == 0  # nothing reached the identity source

    token, _ = _pilot(facade, tmp_path, "subject:pilot-adversary")
    first = _add(facade, token, "add:solar")
    organization_id = str(first.body["organizationId"])
    # An internal Organization or Focus id is never accepted as a locator.
    for ref, locator in (
        ("add:org-id", organization_id),
        ("add:focus-id", str(first.body["focusId"])),
    ):
        forged = _add(facade, token, ref, locator)
        assert (forged.body["state"], forged.body["reason"]) == (
            "IDENTITY_REJECTED",
            "INTERNAL_IDENTIFIER_NOT_ACCEPTED",
        )
    # Exhausted pilot capacity (exactly 1): a second Organization gets no Focus.
    # The identity itself is global registry truth and may be admitted; the Tenant still
    # gets no private Focus beyond its entitlement.
    second = _add(facade, token, "add:second", f"LEI {ACME_ONE}")
    assert second.body["state"] in ("ACCESS_DENIED", "CHECKOUT_REQUIRED"), second.body
    assert "focusId" not in second.body
    assert _focuses(tmp_path) == 1
    # A forged Focus id and another Tenant's id are both just "not found / denied".
    for focus in ("focus_" + "0" * 32, "../" + str(first.body["focusId"])):
        read = facade.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(token))
        assert read.status in (400, 403, 404)
    # After sign-out the session can no longer add or read.
    signed_out = facade.handle("POST", "/subscriber/auth/logout", _headers(token), {})
    assert signed_out.status == 200
    assert _add(facade, token, "add:after-logout").status == 401
