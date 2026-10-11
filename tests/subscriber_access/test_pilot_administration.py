"""Pilot administration authority, migration and atomic one-use contracts."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.subscriber_access.pilot import PilotAccessService, PilotOperationError
from application.subscriber_access.staff_capacity import StaffCapacityError
from domain.admin_access import AdminAssurance, AdminRole
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore
from tests.subscriber_access.test_pilot_access import _context
from tests.subscriber_access.test_staff_capacity import _admin

NOW = datetime(2026, 10, 11, tzinfo=UTC)


def test_staff_authority_and_fixed_capacity(tmp_path: Path) -> None:
    service = PilotAccessService(SqlitePilotAccessStore(tmp_path / "pilot.sqlite3"))
    for grant in (_admin(AdminRole.SUPPORT), _admin(assurance=AdminAssurance.PRIMARY)):
        with pytest.raises(StaffCapacityError):
            service.issue_admin(
                grant,
                reason="Private validation",
                invite_hours=24,
                idempotency_key="authority:1",
                now=NOW,
            )
    with pytest.raises(PilotOperationError):
        service.inventory(_admin(AdminRole.AGENT_SAFE_READER), now=NOW)
    assert service.inventory(_admin(), now=NOW)["invites"] == []


def test_concurrent_redemption_mints_one_grant_only(tmp_path: Path) -> None:
    store = SqlitePilotAccessStore(tmp_path / "pilot.sqlite3")
    service = PilotAccessService(store)
    invite = service.issue_invite(issued_by="operator", reason="Concurrency validation", now=NOW)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(
                lambda n: service.redeem(
                    _context(str(n)), invite.invite_token, now=NOW + timedelta(minutes=1)
                ),
                range(8),
            )
        )
    assert sum(r.accepted for r in results) == 1
    view = store.inventory(now=NOW + timedelta(minutes=2))
    assert len(view["grants"]) == 1
    assert invite.invite_token not in json.dumps(view)
    assert "token_digest" not in json.dumps(view)


def test_expired_invite_and_grant_status_are_derived(tmp_path: Path) -> None:
    store = SqlitePilotAccessStore(tmp_path / "pilot.sqlite3")
    service = PilotAccessService(store, grant_ttl=timedelta(hours=2))
    invite = service.issue_invite(
        issued_by="operator", reason="Expire validation", now=NOW, invite_ttl=timedelta(hours=1)
    )
    assert (
        service.redeem(
            _context("expired"), invite.invite_token, now=NOW + timedelta(hours=1)
        ).accepted
        is False
    )
    assert store.inventory(now=NOW + timedelta(hours=1))["invites"][0]["state"] == "EXPIRED"
    other = service.issue_invite(issued_by="operator", reason="Grant validation", now=NOW)
    assert service.redeem(_context("grant"), other.invite_token, now=NOW).accepted
    assert store.inventory(now=NOW + timedelta(hours=3))["grants"][0]["state"] == "EXPIRED"


def test_revoke_is_idempotent_but_redeemed_invite_cannot_be_revoked(tmp_path: Path) -> None:
    store = SqlitePilotAccessStore(tmp_path / "pilot.sqlite3")
    service = PilotAccessService(store)
    invite = service.issue_admin(
        _admin(),
        reason="Revoke validation",
        invite_hours=24,
        idempotency_key="issue:validation",
        now=NOW,
    )
    service.revoke_admin(
        _admin(),
        kind="invite",
        reference=invite.invite_ref,
        reason="No longer needed",
        idempotency_key="revoke:validation",
        now=NOW,
    )
    service.revoke_admin(
        _admin(),
        kind="invite",
        reference=invite.invite_ref,
        reason="No longer needed",
        idempotency_key="revoke:validation",
        now=NOW,
    )
    assert service.redeem(_context("blocked"), invite.invite_token, now=NOW).accepted is False
    assert len(store.inventory(now=NOW)["audit"]) == 2
    with pytest.raises(PilotOperationError, match="IDEMPOTENCY_CONFLICT"):
        service.revoke_admin(
            _admin(),
            kind="invite",
            reference=invite.invite_ref,
            reason="Different reason",
            idempotency_key="revoke:validation",
            now=NOW,
        )
    redeemed = service.issue_invite(issued_by="staff", reason="Redeemed invitation", now=NOW)
    assert service.redeem(_context("accepted"), redeemed.invite_token, now=NOW).accepted
    with pytest.raises(PilotOperationError, match="STATE_CONFLICT"):
        service.revoke_admin(
            _admin(),
            kind="invite",
            reference=redeemed.invite_ref,
            reason="No longer needed",
            idempotency_key="revoke:redeemed",
            now=NOW,
        )


def test_additive_migration_preserves_legacy_invites_and_grants(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "legacy.sqlite3"
    service = PilotAccessService(SqlitePilotAccessStore(path))
    issued = service.issue_invite(issued_by="legacy", reason="Existing pilot", now=NOW)
    assert service.redeem(_context("existing"), issued.invite_token, now=NOW).accepted
    pending = service.issue_invite(issued_by="legacy", reason="Existing invite", now=NOW)
    with sqlite3.connect(path) as db:
        db.execute("ALTER TABLE subscriber_pilot_invites DROP COLUMN revoked_at")
        db.execute("DROP TABLE subscriber_pilot_commands")
        db.execute("DROP TABLE subscriber_pilot_audit")
    migrated = SqlitePilotAccessStore(path)
    view = migrated.inventory(now=NOW)
    assert len(view["invites"]) == 2 and len(view["grants"]) == 1
    assert view["grants"][0]["state"] == "ACTIVE"
    assert view["audit"] == []  # Do not fabricate a historical audit.
    assert (
        PilotAccessService(migrated).redeem(_context("new"), pending.invite_token, now=NOW).accepted
    )
    assert len(migrated.inventory(now=NOW)["audit"]) == 1
