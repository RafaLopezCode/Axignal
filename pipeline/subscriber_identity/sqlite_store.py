"""SQLite persistence for subscriber OIDC, bootstrap and first-party sessions."""

from __future__ import annotations

import hmac
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from application.subscriber_identity.runtime import (
    ActiveSubscriberSession,
    AuthIntent,
    OidcProviderId,
    OidcTransaction,
    RegisteredSubscriber,
    VerifiedExternalIdentity,
)
from domain.identity import PrincipalId, TenantId
from domain.tenancy.model import Principal


class SqliteSubscriberIdentityStore:
    """Single-host durable identity store; never persists raw bearer cookies."""

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
                CREATE TABLE IF NOT EXISTS subscriber_principals (
                    principal_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS subscriber_tenants (
                    tenant_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS subscriber_memberships (
                    principal_id TEXT NOT NULL REFERENCES subscriber_principals(principal_id),
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    created_at TEXT NOT NULL,
                    revoked_at TEXT,
                    PRIMARY KEY (principal_id, tenant_id)
                );
                CREATE TABLE IF NOT EXISTS subscriber_identity_bindings (
                    issuer TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    client_scope TEXT NOT NULL,
                    principal_id TEXT NOT NULL REFERENCES subscriber_principals(principal_id),
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    created_at TEXT NOT NULL,
                    UNIQUE (issuer, subject, client_scope)
                );
                CREATE INDEX IF NOT EXISTS idx_subscriber_binding_principal
                ON subscriber_identity_bindings(principal_id);
                CREATE TABLE IF NOT EXISTS subscriber_oidc_transactions (
                    transaction_token_digest TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    redirect_uri TEXT NOT NULL,
                    state_digest TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    pkce_verifier TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_subscriber_oidc_expiry
                ON subscriber_oidc_transactions(expires_at, consumed_at);
                CREATE TABLE IF NOT EXISTS subscriber_sessions (
                    token_digest TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL REFERENCES subscriber_principals(principal_id),
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    issued_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY (principal_id, tenant_id)
                        REFERENCES subscriber_memberships(principal_id, tenant_id)
                );
                CREATE INDEX IF NOT EXISTS idx_subscriber_session_expiry
                ON subscriber_sessions(expires_at, revoked_at);
                PRAGMA user_version = 1;
                """
            )

    @staticmethod
    def _scope(identity: VerifiedExternalIdentity) -> str:
        return identity.client_id or ""

    @staticmethod
    def _subscriber(row: sqlite3.Row) -> RegisteredSubscriber:
        return RegisteredSubscriber(
            PrincipalId(str(row["principal_id"])),
            TenantId(str(row["tenant_id"])),
        )

    def find(self, identity: VerifiedExternalIdentity) -> RegisteredSubscriber | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT principal_id, tenant_id FROM subscriber_identity_bindings
                   WHERE issuer = ? AND subject = ? AND client_scope = ?""",
                (identity.issuer, identity.subject, self._scope(identity)),
            ).fetchone()
        return None if row is None else self._subscriber(row)

    def find_principal_ids(
        self,
        identity: VerifiedExternalIdentity,
    ) -> tuple[PrincipalId, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT principal_id FROM subscriber_identity_bindings
                   WHERE issuer = ? AND subject = ? AND client_scope = ?""",
                (identity.issuer, identity.subject, self._scope(identity)),
            ).fetchall()
        return tuple(PrincipalId(str(row["principal_id"])) for row in rows)

    def register(
        self,
        identity: VerifiedExternalIdentity,
        now: datetime,
    ) -> RegisteredSubscriber:
        if now.tzinfo is None:
            raise ValueError("registration time must be timezone-aware")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """SELECT principal_id, tenant_id FROM subscriber_identity_bindings
                   WHERE issuer = ? AND subject = ? AND client_scope = ?""",
                (identity.issuer, identity.subject, self._scope(identity)),
            ).fetchone()
            if existing is not None:
                return self._subscriber(existing)
            principal_id = PrincipalId(f"principal_{uuid.uuid4().hex}")
            tenant_id = TenantId(f"tenant_{uuid.uuid4().hex}")
            connection.execute(
                "INSERT INTO subscriber_principals(principal_id) VALUES (?)", (principal_id,)
            )
            connection.execute("INSERT INTO subscriber_tenants(tenant_id) VALUES (?)", (tenant_id,))
            connection.execute(
                """INSERT INTO subscriber_memberships(principal_id, tenant_id, created_at)
                   VALUES (?, ?, ?)""",
                (principal_id, tenant_id, now.isoformat()),
            )
            connection.execute(
                """INSERT INTO subscriber_identity_bindings(
                       issuer, subject, client_scope, principal_id, tenant_id, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    identity.issuer,
                    identity.subject,
                    self._scope(identity),
                    principal_id,
                    tenant_id,
                    now.isoformat(),
                ),
            )
        return RegisteredSubscriber(principal_id, tenant_id)

    def get_principal(self, principal_id: PrincipalId) -> Principal | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT principal_id FROM subscriber_principals WHERE principal_id = ?",
                (principal_id,),
            ).fetchone()
        return None if row is None else Principal(PrincipalId(str(row["principal_id"])))

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT 1 FROM subscriber_memberships
                   WHERE principal_id = ? AND tenant_id = ? AND revoked_at IS NULL""",
                (principal_id, tenant_id),
            ).fetchone()
        return row is not None

    def create(
        self,
        provider_id: OidcProviderId,
        transaction_token_digest: str,
        transaction: OidcTransaction,
    ) -> None:
        if provider_id is not transaction.provider_id:
            raise ValueError("transaction provider mismatch")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM subscriber_oidc_transactions WHERE expires_at <= ?",
                (transaction.created_at.isoformat(),),
            )
            connection.execute(
                """INSERT INTO subscriber_oidc_transactions(
                       transaction_token_digest, provider_id, client_id, redirect_uri,
                       state_digest, nonce, pkce_verifier, intent, created_at, expires_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    transaction_token_digest,
                    transaction.provider_id.value,
                    transaction.client_id,
                    transaction.redirect_uri,
                    transaction.state_digest,
                    transaction.nonce,
                    transaction.pkce_verifier,
                    transaction.intent.value,
                    transaction.created_at.isoformat(),
                    transaction.expires_at.isoformat(),
                ),
            )

    def consume_once(
        self,
        provider_id: OidcProviderId,
        client_id: str,
        transaction_token_digest: str,
        state_digest: str,
        now: datetime,
    ) -> OidcTransaction | None:
        if now.tzinfo is None:
            raise ValueError("transaction validation time must be timezone-aware")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT * FROM subscriber_oidc_transactions
                   WHERE transaction_token_digest = ? AND provider_id = ? AND client_id = ?
                     AND consumed_at IS NULL AND expires_at > ?""",
                (transaction_token_digest, provider_id.value, client_id, now.isoformat()),
            ).fetchone()
            if row is None or not hmac.compare_digest(str(row["state_digest"]), state_digest):
                return None
            changed = connection.execute(
                """UPDATE subscriber_oidc_transactions SET consumed_at = ?
                   WHERE transaction_token_digest = ? AND consumed_at IS NULL""",
                (now.isoformat(), transaction_token_digest),
            ).rowcount
            if changed != 1:
                return None
            return OidcTransaction(
                provider_id=provider_id,
                client_id=str(row["client_id"]),
                redirect_uri=str(row["redirect_uri"]),
                state_digest=str(row["state_digest"]),
                nonce=str(row["nonce"]),
                pkce_verifier=str(row["pkce_verifier"]),
                intent=AuthIntent(str(row["intent"])),
                created_at=datetime.fromisoformat(str(row["created_at"])),
                expires_at=datetime.fromisoformat(str(row["expires_at"])),
            )

    def issue(
        self,
        subscriber: RegisteredSubscriber,
        token_digest: str,
        now: datetime,
        expires_at: datetime,
    ) -> None:
        if now.tzinfo is None or expires_at.tzinfo is None or expires_at <= now:
            raise ValueError("session interval is invalid")
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO subscriber_sessions(
                       token_digest, principal_id, tenant_id, issued_at, expires_at
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    token_digest,
                    subscriber.principal_id,
                    subscriber.tenant_id,
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )

    def resolve(self, token_digest: str, now: datetime) -> ActiveSubscriberSession | None:
        if now.tzinfo is None:
            raise ValueError("session validation time must be timezone-aware")
        with self._connect() as connection:
            row = connection.execute(
                """SELECT principal_id, tenant_id, expires_at FROM subscriber_sessions
                   WHERE token_digest = ? AND revoked_at IS NULL AND expires_at > ?""",
                (token_digest, now.isoformat()),
            ).fetchone()
        if row is None:
            return None
        return ActiveSubscriberSession(
            PrincipalId(str(row["principal_id"])),
            TenantId(str(row["tenant_id"])),
            datetime.fromisoformat(str(row["expires_at"])),
        )

    def revoke(self, token_digest: str, now: datetime) -> bool:
        if now.tzinfo is None:
            raise ValueError("session revocation time must be timezone-aware")
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE subscriber_sessions SET revoked_at = ?
                   WHERE token_digest = ? AND revoked_at IS NULL""",
                (now.isoformat(), token_digest),
            )
        return cursor.rowcount == 1

    def remove_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool:
        """Governed internal test/admin hook; external subscriber API cannot call it."""

        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE subscriber_memberships SET revoked_at = CURRENT_TIMESTAMP
                   WHERE principal_id = ? AND tenant_id = ? AND revoked_at IS NULL""",
                (principal_id, tenant_id),
            )
        return cursor.rowcount == 1


__all__ = ["SqliteSubscriberIdentityStore"]
