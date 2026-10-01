import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.admin_access import AdminAccessService, VerifiedAdminIdentity
from domain.admin_access import (
    AdminAssurance,
    AdminPrincipalId,
    AdminRole,
    PrivilegeChangeKind,
)
from pipeline.admin_access import SqliteAdminAccessStore


class FakeAdminAuthenticator:
    def __init__(self, identities: dict[str, VerifiedAdminIdentity]) -> None:
        self._identities = identities

    def verify(self, credential: str, *, now: datetime) -> VerifiedAdminIdentity | None:
        del now
        return self._identities.get(credential)


def test_sqlite_store_persists_only_credential_digest_and_append_only_audit(
    tmp_path: Path,
) -> None:
    database = tmp_path / "admin-access.sqlite3"
    store = SqliteAdminAccessStore(database)
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    support = AdminPrincipalId("admin:support")
    service = AdminAccessService(
        store,
        FakeAdminAuthenticator(
            {
                "founder-auth": VerifiedAdminIdentity(
                    principal_id=founder,
                    authenticated_at=now,
                    assurance=AdminAssurance.STEP_UP,
                    auth_source="verified-admin-provider",
                )
            }
        ),
    )

    bootstrap = service.bootstrap_founder(
        "founder-auth",
        occurred_at=now,
        reason="initial founder bootstrap",
    )
    credential = service.issue_session(
        "founder-auth",
        authenticated_at=now,
    )
    grant = service.change_role(
        credential.token,
        target_principal_id=support,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="support assignment",
    )

    raw = database.read_bytes()
    assert credential.token.encode("utf-8") not in raw
    assert b"sha256:" in raw

    with sqlite3.connect(database) as connection:
        stored = connection.execute(
            "SELECT token_digest FROM admin_sessions WHERE session_id = ?",
            (credential.session_id,),
        ).fetchone()
        assert stored is not None
        assert str(stored[0]).startswith("sha256:")
        assert str(stored[0]) != credential.token

        history = connection.execute(
            """
            SELECT event_id, kind
            FROM admin_privilege_events
            ORDER BY occurred_at, event_id
            """
        ).fetchall()
    assert history == [
        (bootstrap.event_id, PrivilegeChangeKind.BOOTSTRAP_FOUNDER.value),
        (grant.event_id, PrivilegeChangeKind.GRANT_ROLE.value),
    ]

    reopened = SqliteAdminAccessStore(database)
    assert reopened.roles_for_principal(founder) == frozenset({AdminRole.FOUNDER})
    assert reopened.roles_for_principal(support) == frozenset({AdminRole.SUPPORT})


def test_privilege_replay_uses_append_sequence_when_timestamps_match(tmp_path: Path) -> None:
    database = tmp_path / "admin-access-sequence.sqlite3"
    store = SqliteAdminAccessStore(database)
    now = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    founder = AdminPrincipalId("admin:founder")
    support = AdminPrincipalId("admin:support")
    service = AdminAccessService(
        store,
        FakeAdminAuthenticator(
            {
                "founder-auth": VerifiedAdminIdentity(
                    principal_id=founder,
                    authenticated_at=now,
                    assurance=AdminAssurance.STEP_UP,
                    auth_source="verified-admin-provider",
                )
            }
        ),
    )
    bootstrap = service.bootstrap_founder(
        "founder-auth",
        occurred_at=now,
        reason="initial founder bootstrap",
    )
    credential = service.issue_session("founder-auth", authenticated_at=now)
    grant = service.change_role(
        credential.token,
        target_principal_id=support,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.GRANT_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="temporary support role",
    )
    revoke = service.change_role(
        credential.token,
        target_principal_id=support,
        role=AdminRole.SUPPORT,
        kind=PrivilegeChangeKind.REVOKE_ROLE,
        occurred_at=now + timedelta(minutes=1),
        reason="same timestamp revoke follows grant",
    )

    assert store.privilege_events() == (bootstrap, grant, revoke)
    assert store.roles_for_principal(support) == frozenset()
