"""SQLite persistence for private design-partner pilot access."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.subscriber_access.pilot import PilotGrant, PilotOperationError
from domain.identity import PrincipalId, TenantId


class SqlitePilotAccessStore:
    def __init__(self, database_path: str | Path, *, read_only: bool = False) -> None:
        self.path = Path(database_path)
        self._read_only = read_only
        if read_only:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"{self.path.resolve().as_uri()}?mode=ro" if self._read_only else self.path,
            uri=self._read_only,
            timeout=10,
        )
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

            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(subscriber_pilot_invites)")
            }
            if "revoked_at" not in columns:
                connection.execute(
                    "ALTER TABLE subscriber_pilot_invites ADD COLUMN revoked_at TEXT"
                )
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS subscriber_pilot_commands (
                    actor TEXT NOT NULL, command_key TEXT NOT NULL,
                    fingerprint TEXT NOT NULL, reference TEXT NOT NULL,
                    PRIMARY KEY (actor, command_key)
                );
                CREATE TABLE IF NOT EXISTS subscriber_pilot_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL, actor TEXT NOT NULL,
                    reference TEXT NOT NULL, occurred_at TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    tenant_id TEXT, principal_id TEXT
                );
            """)

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        *,
        action: str,
        actor: str,
        reference: str,
        now: datetime,
        reason: str,
        tenant: str | None = None,
        principal: str | None = None,
    ) -> None:
        connection.execute(
            """INSERT INTO subscriber_pilot_audit
            (action, actor, reference, occurred_at, reason, tenant_id, principal_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (action, actor, reference, now.astimezone(UTC).isoformat(), reason, tenant, principal),
        )

    @staticmethod
    def _receipt(
        connection: sqlite3.Connection, actor: str, key: str, fingerprint: str
    ) -> str | None:
        row = connection.execute(
            "SELECT fingerprint, reference FROM subscriber_pilot_commands WHERE actor=? AND command_key=?",
            (actor, key),
        ).fetchone()
        if row is None:
            return None
        if row["fingerprint"] != fingerprint:
            raise PilotOperationError("IDEMPOTENCY_CONFLICT")
        return str(row["reference"])

    @staticmethod
    def _remember(
        connection: sqlite3.Connection, actor: str, key: str, fingerprint: str, reference: str
    ) -> None:
        connection.execute(
            "INSERT INTO subscriber_pilot_commands VALUES (?, ?, ?, ?)",
            (actor, key, fingerprint, reference),
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
        idempotency_key: str | None = None,
        fingerprint: str | None = None,
    ) -> None:
        if created_at.tzinfo is None or expires_at.tzinfo is None or expires_at <= created_at:
            raise ValueError("invalid pilot invite interval")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if idempotency_key is not None:
                if fingerprint is None:
                    raise ValueError("fingerprint required")
                prior = self._receipt(connection, issued_by, idempotency_key, fingerprint)
                if prior is not None:
                    raise PilotOperationError("INVITE_ALREADY_ISSUED", prior)
                count = connection.execute(
                    """SELECT COUNT(*) FROM subscriber_pilot_audit
                    WHERE action='ISSUED' AND actor=? AND occurred_at>?""",
                    (issued_by, (created_at.astimezone(UTC) - timedelta(hours=1)).isoformat()),
                ).fetchone()[0]
                if count >= 20:
                    raise PilotOperationError("RATE_LIMITED")
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

            self._audit(
                connection,
                action="ISSUED",
                actor=issued_by,
                reference=invite_ref,
                now=created_at,
                reason=reason,
            )
            if idempotency_key is not None and fingerprint is not None:
                self._remember(connection, issued_by, idempotency_key, fingerprint, invite_ref)

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
                   WHERE token_digest = ? AND expires_at > ? AND revoked_at IS NULL""",
                (token_digest, redeemed_at.isoformat()),
            ).fetchone()
            if invite is None:
                return None
            if invite["redeemed_at"] is not None:
                return None
            existing = connection.execute(
                """SELECT 1 FROM subscriber_pilot_grants
                   WHERE principal_id = ? AND tenant_id = ?""",
                (principal_id, tenant_id),
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
            self._audit(
                connection,
                action="REDEEMED",
                actor=str(principal_id),
                reference=str(invite["invite_ref"]),
                now=redeemed_at,
                reason="Authenticated one-use redemption",
                tenant=str(tenant_id),
                principal=str(principal_id),
            )
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

    def active_grants(self, *, now: datetime) -> tuple[PilotGrant, ...]:
        """Operator listing of live grants (references and tenants only)."""
        if now.tzinfo is None:
            raise ValueError("pilot grant read time must be timezone-aware")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM subscriber_pilot_grants
                   WHERE revoked_at IS NULL AND expires_at > ? ORDER BY granted_at""",
                (now.isoformat(),),
            ).fetchall()
        return tuple(self._grant(row) for row in rows)

    def revoke_grant(self, grant_ref: str, *, revoked_at: datetime) -> bool:
        if revoked_at.tzinfo is None:
            raise ValueError("pilot revocation time must be timezone-aware")
        with self._connect() as connection:
            changed = connection.execute(
                """UPDATE subscriber_pilot_grants SET revoked_at = ?
                   WHERE grant_ref = ? AND revoked_at IS NULL""",
                (revoked_at.isoformat(), grant_ref),
            ).rowcount
            if changed == 1:
                self._audit(
                    connection,
                    action="GRANT_REVOKED",
                    actor="operator-cli",
                    reference=grant_ref,
                    now=revoked_at,
                    reason="Contingency revocation",
                )
        return changed == 1

    def inventory(self, *, now: datetime) -> dict[str, object]:
        if now.tzinfo is None:
            raise ValueError("aware time required")
        with self._connect() as connection:
            invites = connection.execute("""
                SELECT invite_ref, issued_by, reason, created_at, expires_at,
                    redeemed_at, redeemed_principal_id, redeemed_tenant_id, revoked_at
                FROM subscriber_pilot_invites ORDER BY created_at DESC LIMIT 500
            """).fetchall()
            grants = connection.execute("""
                SELECT grant_ref, invite_ref, principal_id, tenant_id, capacity,
                    granted_at, expires_at, revoked_at
                FROM subscriber_pilot_grants ORDER BY granted_at DESC LIMIT 500
            """).fetchall()
            audit = connection.execute("""
                SELECT sequence, action, actor, reference, occurred_at, reason,
                    tenant_id, principal_id FROM subscriber_pilot_audit
                ORDER BY sequence DESC LIMIT 100
            """).fetchall()

        def state(row: sqlite3.Row, redeemed: bool = False) -> str:
            if redeemed and row["redeemed_at"] is not None:
                return "REDEEMED"
            if row["revoked_at"] is not None:
                return "REVOKED"
            if datetime.fromisoformat(row["expires_at"]) <= now:
                return "EXPIRED"
            return "PENDING" if redeemed else "ACTIVE"

        return {
            "asOf": now.isoformat(),
            "invites": [{**dict(row), "state": state(row, True), "capacity": 1} for row in invites],
            "grants": [{**dict(row), "state": state(row)} for row in grants],
            "audit": [dict(row) for row in audit],
            "limit": 500,
        }

    def revoke_admin(
        self,
        *,
        kind: str,
        reference: str,
        actor: str,
        reason: str,
        idempotency_key: str,
        now: datetime,
    ) -> None:
        if now.tzinfo is None:
            raise ValueError("aware time required")
        fingerprint = hashlib.sha256(json.dumps([kind, reference, reason]).encode()).hexdigest()
        table, column = (
            ("subscriber_pilot_invites", "invite_ref")
            if kind == "invite"
            else ("subscriber_pilot_grants", "grant_ref")
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if self._receipt(connection, actor, idempotency_key, fingerprint) is not None:
                return
            row = connection.execute(
                f"SELECT * FROM {table} WHERE {column}=?", (reference,)
            ).fetchone()
            if row is None:
                raise PilotOperationError("REFERENCE_NOT_FOUND")
            if row["revoked_at"] is not None or (
                kind == "invite" and row["redeemed_at"] is not None
            ):
                raise PilotOperationError("STATE_CONFLICT")
            if datetime.fromisoformat(row["expires_at"]) <= now:
                raise PilotOperationError("STATE_CONFLICT")
            connection.execute(
                f"UPDATE {table} SET revoked_at=? WHERE {column}=?",
                (now.astimezone(UTC).isoformat(), reference),
            )
            self._audit(
                connection,
                action="INVITE_REVOKED" if kind == "invite" else "GRANT_REVOKED",
                actor=actor,
                reference=reference,
                now=now,
                reason=reason,
                tenant=None if kind == "invite" else row["tenant_id"],
                principal=None if kind == "invite" else row["principal_id"],
            )
            self._remember(connection, actor, idempotency_key, fingerprint, reference)
