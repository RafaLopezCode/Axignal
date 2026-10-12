"""Pilot test accounts listed by the operator get pilot access at a verified sign-in.

The address is the one Google verified, compared at sign-in and never stored; the grant
keeps the invite-backed shape, is audited, shown with its origin and can be revoked.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.subscriber_access.pilot import PilotAccessService
from application.subscriber_identity.runtime import SubscriberAuthenticationService
from application.subscriber_identity.service import VerifiedExternalIdentity
from domain.identity import PrincipalId, TenantId
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from pipeline.subscriber_identity.sqlite_store import SqliteSubscriberIdentityStore
from tests.subscriber_identity.test_runtime import (
    FakeProvider,
    FakeProvisioner,
    MutableClock,
    _callback,
    _config,
)

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)
LISTED = ("ana@example.com", "luis@example.com")


def _pilot(tmp_path: Path) -> tuple[PilotAccessService, SqlitePilotAccessStore]:
    store = SqlitePilotAccessStore(tmp_path / "subscriber-pilot.sqlite3")
    return PilotAccessService(store), store


def test_a_listed_verified_address_gets_one_audited_grant_with_its_origin(tmp_path: Path) -> None:
    pilot, store = _pilot(tmp_path)
    principal, tenant = PrincipalId("principal-1"), TenantId("tenant-1")

    grant = pilot.grant_listed_account(
        principal_id=principal, tenant_id=tenant, verified_email=" Luis@Example.com ",
        listed=LISTED, now=NOW,
    )  # fmt: skip

    assert grant is not None and grant.capacity == 1
    assert grant.expires_at == NOW + timedelta(days=60)
    assert pilot.active_grant(tenant, now=NOW) == grant
    inventory = store.inventory(now=NOW)
    (record,) = inventory["grants"]  # type: ignore[misc]
    assert (record["origin"], record["account"], record["state"]) == (
        "LISTED_ACCOUNT",
        "B",
        "ACTIVE",
    )
    assert inventory["invites"] == []  # the internal invite is not a usable invitation
    assert [a["action"] for a in inventory["audit"]] == ["GRANTED_LISTED_ACCOUNT"]  # type: ignore[index,union-attr]
    # Signing in again does not renew or duplicate the grant.
    again = pilot.grant_listed_account(
        principal_id=principal, tenant_id=tenant, verified_email="luis@example.com",
        listed=LISTED, now=NOW + timedelta(days=1),
    )  # fmt: skip
    assert again is None and len(store.inventory(now=NOW)["grants"]) == 1  # type: ignore[arg-type]


def test_unlisted_or_unverified_addresses_get_nothing(tmp_path: Path) -> None:
    pilot, store = _pilot(tmp_path)
    for email in ("otra@example.com", None, ""):
        assert (
            pilot.grant_listed_account(
                principal_id=PrincipalId("p"),
                tenant_id=TenantId("t"),
                verified_email=email,
                listed=LISTED,
                now=NOW,
            )
            is None
        )
    assert store.inventory(now=NOW)["grants"] == []


def test_a_revoked_listed_grant_stays_revoked_at_the_next_sign_in(tmp_path: Path) -> None:
    pilot, store = _pilot(tmp_path)
    grant = pilot.grant_listed_account(
        principal_id=PrincipalId("p"), tenant_id=TenantId("t"), verified_email=LISTED[0],
        listed=LISTED, now=NOW,
    )  # fmt: skip
    assert grant is not None and store.revoke_grant(grant.grant_ref, revoked_at=NOW)
    assert (
        pilot.grant_listed_account(
            principal_id=PrincipalId("p"),
            tenant_id=TenantId("t"),
            verified_email=LISTED[0],
            listed=LISTED,
            now=NOW + timedelta(hours=1),
        )
        is None
    )
    assert pilot.active_grant(TenantId("t"), now=NOW + timedelta(hours=1)) is None


def _auth(tmp_path: Path, identity: VerifiedExternalIdentity, hook):  # type: ignore[no-untyped-def]
    store = SqliteSubscriberIdentityStore(tmp_path / "identity.sqlite3")
    provider = FakeProvider(identity)
    service = SubscriberAuthenticationService(
        {_config().provider_id: _config()}, provider, store, store, store, FakeProvisioner(),
        MutableClock(NOW), on_verified_email=hook,
    )  # fmt: skip
    return service, provider


def test_sign_in_passes_only_a_provider_verified_email_and_never_fails_on_the_hook(
    tmp_path: Path,
) -> None:
    seen: list[str] = []

    def hook(principal: PrincipalId, tenant: TenantId, email: str, now: datetime) -> None:
        seen.append(email)
        raise RuntimeError("pilot store unavailable")

    verified = VerifiedExternalIdentity(
        "https://accounts.google.com", "subject-1", verified_email="ana@example.com"
    )
    service, provider = _auth(tmp_path, verified, hook)
    issued, _, _ = _callback(service, provider)
    assert issued.session_token and seen == ["ana@example.com"]
    # The address is not part of the identity binding.
    assert verified == VerifiedExternalIdentity("https://accounts.google.com", "subject-1")


def test_without_a_verified_email_the_hook_is_not_called(tmp_path: Path) -> None:
    seen: list[str] = []
    service, provider = _auth(
        tmp_path,
        VerifiedExternalIdentity("https://accounts.google.com", "subject-1"),
        lambda p, t, email, now: seen.append(email),
    )
    _callback(service, provider)
    assert seen == []
