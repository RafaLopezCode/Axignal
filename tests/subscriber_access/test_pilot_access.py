"""Private design-partner pilot authority tests."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.subscriber_access.pilot import PilotAccessService
from application.subscriber_identity.runtime import TrustedSubscriberContext
from domain.identity import PrincipalId, TenantId
from pipeline.subscriber_access.sqlite_store import SqlitePilotAccessStore

NOW = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)


def _context(name: str) -> TrustedSubscriberContext:
    return TrustedSubscriberContext(PrincipalId(f"principal:{name}"), TenantId(f"tenant:{name}"))


def test_invite_secret_is_hashed_single_scope_and_replay_safe(tmp_path: Path) -> None:
    store = SqlitePilotAccessStore(tmp_path / "pilot.sqlite3")
    service = PilotAccessService(store)
    invite = service.issue_invite(issued_by="founder", reason="design partner validation", now=NOW)
    raw = (tmp_path / "pilot.sqlite3").read_bytes()
    assert invite.invite_token.encode() not in raw

    context = _context("one")
    redeemed = service.redeem(context, invite.invite_token, now=NOW + timedelta(minutes=1))
    assert redeemed.accepted is True
    assert redeemed.grant is not None
    assert redeemed.grant.capacity == 1
    assert redeemed.grant.principal_id == context.principal_id
    assert redeemed.grant.tenant_id == context.tenant_id

    replay = service.redeem(context, invite.invite_token, now=NOW + timedelta(minutes=2))
    assert replay.accepted is False
    assert replay.grant is None
    assert service.active_grant(context.tenant_id, now=NOW + timedelta(minutes=2)) == redeemed.grant

    stolen = service.redeem(_context("two"), invite.invite_token, now=NOW + timedelta(minutes=3))
    assert stolen.accepted is False
    assert stolen.grant is None


def test_expired_invite_and_revoked_grant_fail_closed(tmp_path: Path) -> None:
    store = SqlitePilotAccessStore(tmp_path / "pilot.sqlite3")
    service = PilotAccessService(store, grant_ttl=timedelta(days=2))
    invite = service.issue_invite(
        issued_by="founder",
        reason="short invite",
        now=NOW,
        invite_ttl=timedelta(hours=1),
    )
    assert (
        service.redeem(_context("late"), invite.invite_token, now=NOW + timedelta(hours=2)).accepted
        is False
    )

    live = service.issue_invite(issued_by="founder", reason="live", now=NOW)
    context = _context("live")
    redeemed = service.redeem(context, live.invite_token, now=NOW + timedelta(minutes=1))
    assert redeemed.grant is not None
    assert service.active_grant(context.tenant_id, now=NOW + timedelta(hours=1)) is not None
    assert store.revoke_grant(redeemed.grant.grant_ref, revoked_at=NOW + timedelta(hours=2)) is True
    assert service.active_grant(context.tenant_id, now=NOW + timedelta(hours=3)) is None
