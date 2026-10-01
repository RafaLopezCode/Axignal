"""SQLite adapter for Admin sessions, revocations and append-only privilege history."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from application.admin_access import AdminPrivilegeConflict
from domain.admin_access import (
    AdminAssurance,
    AdminPrincipalId,
    AdminPrivilegeEvent,
    AdminPrivilegeEventId,
    AdminRole,
    AdminSession,
    AdminSessionId,
    AdminSessionRevocation,
    PrivilegeChangeKind,
)


class SqliteAdminAccessStore:
    """Durable Admin security state; raw bearer credentials are never persisted."""

    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    session_id TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL,
                    token_digest TEXT NOT NULL UNIQUE,
                    issued_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    assurance TEXT NOT NULL,
                    auth_source TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_admin_sessions_principal
                ON admin_sessions(principal_id, issued_at, session_id);

                CREATE TABLE IF NOT EXISTS admin_session_revocations (
                    session_id TEXT PRIMARY KEY,
                    revoked_at TEXT NOT NULL,
                    actor_principal_id TEXT NOT NULL,
                    reason TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS admin_privilege_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    target_principal_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    actor_principal_id TEXT NOT NULL,
                    actor_session_id TEXT,
                    reason TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_admin_privilege_target
                ON admin_privilege_events(target_principal_id, sequence);
                """
            )

    @staticmethod
    def _session(row: sqlite3.Row) -> AdminSession:
        return AdminSession(
            session_id=AdminSessionId(str(row["session_id"])),
            principal_id=AdminPrincipalId(str(row["principal_id"])),
            token_digest=str(row["token_digest"]),
            issued_at=datetime.fromisoformat(str(row["issued_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
            assurance=AdminAssurance(str(row["assurance"])),
            auth_source=str(row["auth_source"]),
        )

    @staticmethod
    def _privilege(row: sqlite3.Row) -> AdminPrivilegeEvent:
        actor_session = row["actor_session_id"]
        return AdminPrivilegeEvent(
            event_id=AdminPrivilegeEventId(str(row["event_id"])),
            target_principal_id=AdminPrincipalId(str(row["target_principal_id"])),
            role=AdminRole(str(row["role"])),
            kind=PrivilegeChangeKind(str(row["kind"])),
            occurred_at=datetime.fromisoformat(str(row["occurred_at"])),
            actor_principal_id=AdminPrincipalId(str(row["actor_principal_id"])),
            actor_session_id=(
                None if actor_session is None else AdminSessionId(str(actor_session))
            ),
            reason=str(row["reason"]),
        )

    def has_privilege_history(self) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT 1 FROM admin_privilege_events LIMIT 1").fetchone()
        return row is not None

    def append_privilege_event(self, event: AdminPrivilegeEvent) -> bool:
        if not isinstance(event, AdminPrivilegeEvent):
            raise TypeError("admin access store accepts AdminPrivilegeEvent only")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM admin_privilege_events WHERE event_id = ?",
                (event.event_id,),
            ).fetchone()
            if row is not None:
                if self._privilege(row) == event:
                    return False
                raise AdminPrivilegeConflict(
                    "Admin privilege event id already exists with different content"
                )
            connection.execute(
                """
                INSERT INTO admin_privilege_events (
                    event_id, target_principal_id, role, kind, occurred_at,
                    actor_principal_id, actor_session_id, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.target_principal_id,
                    event.role.value,
                    event.kind.value,
                    event.occurred_at.isoformat(),
                    event.actor_principal_id,
                    event.actor_session_id,
                    event.reason,
                ),
            )
        return True

    def privilege_events(self) -> tuple[AdminPrivilegeEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM admin_privilege_events
                ORDER BY sequence
                """
            ).fetchall()
        return tuple(self._privilege(row) for row in rows)

    def roles_for_principal(self, principal_id: AdminPrincipalId) -> frozenset[AdminRole]:
        active: set[AdminRole] = set()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM admin_privilege_events
                WHERE target_principal_id = ?
                ORDER BY sequence
                """,
                (principal_id,),
            ).fetchall()
        for row in rows:
            event = self._privilege(row)
            if event.kind in {
                PrivilegeChangeKind.BOOTSTRAP_FOUNDER,
                PrivilegeChangeKind.GRANT_ROLE,
            }:
                active.add(event.role)
            elif event.kind is PrivilegeChangeKind.REVOKE_ROLE:
                active.discard(event.role)
        return frozenset(active)

    def append_session(self, session: AdminSession) -> bool:
        if not isinstance(session, AdminSession):
            raise TypeError("admin access store accepts AdminSession only")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM admin_sessions WHERE session_id = ?",
                (session.session_id,),
            ).fetchone()
            if row is not None:
                if self._session(row) == session:
                    return False
                raise AdminPrivilegeConflict(
                    "Admin session id already exists with different content"
                )
            digest_row = connection.execute(
                "SELECT session_id FROM admin_sessions WHERE token_digest = ?",
                (session.token_digest,),
            ).fetchone()
            if digest_row is not None:
                raise AdminPrivilegeConflict("Admin session credential digest already exists")
            connection.execute(
                """
                INSERT INTO admin_sessions (
                    session_id, principal_id, token_digest, issued_at,
                    expires_at, assurance, auth_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.principal_id,
                    session.token_digest,
                    session.issued_at.isoformat(),
                    session.expires_at.isoformat(),
                    session.assurance.value,
                    session.auth_source,
                ),
            )
        return True

    def get_session_by_digest(self, token_digest: str) -> AdminSession | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_sessions WHERE token_digest = ?",
                (token_digest,),
            ).fetchone()
        return None if row is None else self._session(row)

    def get_session(self, session_id: AdminSessionId) -> AdminSession | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return None if row is None else self._session(row)

    def append_revocation(self, revocation: AdminSessionRevocation) -> bool:
        if not isinstance(revocation, AdminSessionRevocation):
            raise TypeError("admin access store accepts AdminSessionRevocation only")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM admin_session_revocations WHERE session_id = ?",
                (revocation.session_id,),
            ).fetchone()
            if row is not None:
                existing = AdminSessionRevocation(
                    session_id=AdminSessionId(str(row["session_id"])),
                    revoked_at=datetime.fromisoformat(str(row["revoked_at"])),
                    actor_principal_id=AdminPrincipalId(str(row["actor_principal_id"])),
                    reason=str(row["reason"]),
                )
                if existing == revocation:
                    return False
                raise AdminPrivilegeConflict("Admin session already revoked with different content")
            connection.execute(
                """
                INSERT INTO admin_session_revocations (
                    session_id, revoked_at, actor_principal_id, reason
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    revocation.session_id,
                    revocation.revoked_at.isoformat(),
                    revocation.actor_principal_id,
                    revocation.reason,
                ),
            )
        return True

    def is_revoked(self, session_id: AdminSessionId) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM admin_session_revocations WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row is not None
