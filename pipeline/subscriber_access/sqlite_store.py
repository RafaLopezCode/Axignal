"""SQLite persistence for private design-partner pilot access."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from application.subscriber_access.pilot import PilotGrant
from domain.identity import PrincipalId, TenantId


class SqlitePilotAccessStore:
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS subscriber_pilot_invites (
                    invite_ref TEXT PRIMARY KEY,
                    token_digest TEXT NOT NULL UNIQUE,
                    issued_by TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    redeemed_at TEXT,
                    redeemed_principal_id TEXT,
                    redeemed_tenant_id TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_pilot_invite_expiry
                ON subscriber_pilot_invites(expires_at, redeemed_at);
                CREATE TABLE IF NOT EXISTS subscriber_pilot_grants (
                    grant_ref TEXT PRIMARY KEY,
                    invite_ref TEXT NOT NULL UNIQUE REFERENCES subscriber_pilot_invites(invite_ref),
                    principal_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    capacity INTEGER NOT NULL CHECK (capacity = 1),
                    granted_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    UNIQUE (principal_id, tenant_id)
                );
                CREATE INDEX IF NOT EXISTS idx_pilot_grant_tenant
                ON subscriber_pilot_grants(tenant_id, expires_at, revoked_at);
                """
            )

    @staticmethod
    def _grant(row: sqlite3.Row) -> PilotGrant:
        return PilotGrant(
            grant_ref=str(row["grant_ref"]),
            principal_id=PrincipalId(str(row["principal_id"])),
            tenant_id=TenantId(str(row["tenant_id"])),
            capacity=int(row["capacity"]),
            granted_at=datetime.fromisoformat(str(row["granted_at"])),
            expires_at=datetime.fromisoformat(str(row["expires_at"])),
        )

    def create_invite(
        self,
        *,
        invite_ref: str,
        token_digest: str,
        issued_by: str,
        reason: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> None:
        if created_at.tzinfo is None or expires_at.tzinfo is None or expires_at <= created_at:
            raise ValueError("invalid pilot invite interval")
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO subscriber_pilot_invites(invite_ref, token_digest, issued_by, reason, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    invite_ref,
                    token_digest,
                    issued_by,
                    reason,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )

    def redeem_invite(
        self,
        *,
        token_digest: str,
        principal_id: PrincipalId,
        tenant_id: TenantId,
        redeemed_at: datetime,
        grant_expires_at: datetime,
    ) -> PilotGrant | None:
        if redeemed_at.tzinfo is None or grant_expires_at.tzinfo is None:
            raise ValueError("pilot redemption times must be timezone-aware")
        if grant_expires_at <= redeemed_at:
            raise ValueError("pilot grant expiry must follow redemption")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            invite = connection.execute(
                """SELECT * FROM subscriber_pilot_invites
                   WHERE token_digest = ? AND expires_at > ?""",
                (token_digest, redeemed_at.isoformat()),
            ).fetchone()
            if invite is None:
                return None
            if invite["redeemed_at"] is not None:
                if str(invite["redeemed_principal_id"]) != str(principal_id) or str(
                    invite["redeemed_tenant_id"]
                ) != str(tenant_id):
                    return None
                existing = connection.execute(
                    """SELECT * FROM subscriber_pilot_grants
                       WHERE invite_ref = ? AND revoked_at IS NULL AND expires_at > ?""",
                    (str(invite["invite_ref"]), redeemed_at.isoformat()),
                ).fetchone()
                return None if existing is None else self._grant(existing)
            existing = connection.execute(
                """SELECT 1 FROM subscriber_pilot_grants
                   WHERE principal_id = ? AND tenant_id = ? AND revoked_at IS NULL AND expires_at > ?""",
                (principal_id, tenant_id, redeemed_at.isoformat()),
            ).fetchone()
            if existing is not None:
                return None
            changed = connection.execute(
                """UPDATE subscriber_pilot_invites
                   SET redeemed_at = ?, redeemed_principal_id = ?, redeemed_tenant_id = ?
                   WHERE invite_ref = ? AND redeemed_at IS NULL""",
                (redeemed_at.isoformat(), principal_id, tenant_id, str(invite["invite_ref"])),
            ).rowcount
            if changed != 1:
                return None
            grant_ref = f"pilot_grant_{uuid.uuid4().hex}"
            connection.execute(
                """INSERT INTO subscriber_pilot_grants(grant_ref, invite_ref, principal_id, tenant_id, capacity, granted_at, expires_at)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (
                    grant_ref,
                    str(invite["invite_ref"]),
                    principal_id,
                    tenant_id,
                    redeemed_at.isoformat(),
                    grant_expires_at.isoformat(),
                ),
            )
            row = connection.execute(
                "SELECT * FROM subscriber_pilot_grants WHERE grant_ref = ?", (grant_ref,)
            ).fetchone()
            assert row is not None
            return self._grant(row)

    def active_grant(self, tenant_id: TenantId, *, now: datetime) -> PilotGrant | None:
        if now.tzinfo is None:
            raise ValueError("pilot grant read time must be timezone-aware")
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM subscriber_pilot_grants
                   WHERE tenant_id = ? AND revoked_at IS NULL AND expires_at > ?
                   ORDER BY granted_at DESC LIMIT 1""",
                (tenant_id, now.isoformat()),
            ).fetchone()
        return None if row is None else self._grant(row)

    def revoke_grant(self, grant_ref: str, *, revoked_at: datetime) -> bool:
        if revoked_at.tzinfo is None:
            raise ValueError("pilot revocation time must be timezone-aware")
        with self._connect() as connection:
            changed = connection.execute(
                """UPDATE subscriber_pilot_grants SET revoked_at = ?
                   WHERE grant_ref = ? AND revoked_at IS NULL""",
                (revoked_at.isoformat(), grant_ref),
            ).rowcount
        return changed == 1
