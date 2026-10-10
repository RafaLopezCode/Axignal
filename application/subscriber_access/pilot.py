"""Private design-partner pilot access policy."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from application.subscriber_access.staff_capacity import require_staff_write
from application.subscriber_identity.runtime import TrustedSubscriberContext
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.identity import PrincipalId, TenantId


@dataclass(frozen=True, slots=True)
class PilotGrant:
    grant_ref: str
    principal_id: PrincipalId
    tenant_id: TenantId
    capacity: int
    granted_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.grant_ref.strip():
            raise ValueError("pilot grant reference is required")
        if type(self.capacity) is not int or self.capacity != 1:
            raise ValueError("design-partner pilot capacity is exactly one")
        if self.granted_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("pilot grant times must be timezone-aware")
        if self.expires_at <= self.granted_at:
            raise ValueError("pilot grant expiry must follow grant time")


@dataclass(frozen=True, slots=True)
class IssuedPilotInvite:
    invite_ref: str
    invite_token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PilotRedemption:
    accepted: bool
    state: str
    grant: PilotGrant | None = None


class PilotOperationError(ValueError):
    """Safe operational failure; never contains a token or digest."""

    def __init__(self, code: str, reference: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.reference = reference


class PilotAccessStore(Protocol):
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
    ) -> None: ...
    def redeem_invite(
        self,
        *,
        token_digest: str,
        principal_id: PrincipalId,
        tenant_id: TenantId,
        redeemed_at: datetime,
        grant_expires_at: datetime,
    ) -> PilotGrant | None: ...
    def active_grant(self, tenant_id: TenantId, *, now: datetime) -> PilotGrant | None: ...
    def revoke_grant(self, grant_ref: str, *, revoked_at: datetime) -> bool: ...
    def inventory(self, *, now: datetime) -> dict[str, object]: ...
    def revoke_admin(
        self,
        *,
        kind: str,
        reference: str,
        actor: str,
        reason: str,
        idempotency_key: str,
        now: datetime,
    ) -> None: ...


class PilotAccessService:
    """Issue and redeem one-use private pilot invitations."""

    def __init__(
        self, store: PilotAccessStore, *, grant_ttl: timedelta = timedelta(days=60)
    ) -> None:
        if grant_ttl <= timedelta(0):
            raise ValueError("pilot grant TTL must be positive")
        self._store = store
        self._grant_ttl = grant_ttl

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue_invite(
        self,
        *,
        issued_by: str,
        reason: str,
        now: datetime,
        invite_ttl: timedelta = timedelta(days=7),
        idempotency_key: str | None = None,
        fingerprint: str | None = None,
    ) -> IssuedPilotInvite:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("pilot invite time must be timezone-aware")
        if not timedelta(hours=1) <= invite_ttl <= timedelta(days=30):
            raise ValueError("pilot invite TTL must be 1 hour to 30 days")
        if not issued_by.strip() or not reason.strip():
            raise ValueError("pilot invite requires operator and reason")
        token = secrets.token_urlsafe(32)
        invite_ref = f"pilot_invite_{secrets.token_hex(16)}"
        expires_at = now + invite_ttl
        self._store.create_invite(
            invite_ref=invite_ref,
            token_digest=self._digest(token),
            issued_by=issued_by.strip(),
            reason=reason.strip(),
            created_at=now,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
        )
        return IssuedPilotInvite(invite_ref, token, expires_at)

    def redeem(
        self, context: TrustedSubscriberContext, invite_token: str, *, now: datetime
    ) -> PilotRedemption:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("pilot redemption time must be timezone-aware")
        if not isinstance(invite_token, str) or not 20 <= len(invite_token) <= 256:
            return PilotRedemption(False, "PILOT_INVITE_INVALID")
        grant = self._store.redeem_invite(
            token_digest=self._digest(invite_token),
            principal_id=context.principal_id,
            tenant_id=context.tenant_id,
            redeemed_at=now,
            grant_expires_at=now + self._grant_ttl,
        )
        if grant is None:
            return PilotRedemption(False, "PILOT_INVITE_INVALID")
        return PilotRedemption(True, "PILOT_ACTIVE", grant)

    def active_grant(self, tenant_id: TenantId, *, now: datetime) -> PilotGrant | None:
        return self._store.active_grant(tenant_id, now=now)

    @staticmethod
    def _command_text(value: str, *, minimum: int = 8, maximum: int = 500) -> str:
        if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
            raise PilotOperationError("INVALID_REQUEST")
        if any(ord(c) < 32 for c in value):
            raise PilotOperationError("INVALID_REQUEST")
        return value.strip()

    def issue_admin(
        self,
        grant: AdminAuthorizationGrant,
        *,
        reason: str,
        invite_hours: int,
        idempotency_key: str,
        now: datetime,
    ) -> IssuedPilotInvite:
        actor = require_staff_write(grant)
        reason = self._command_text(reason)
        key = self._command_text(idempotency_key, maximum=160)
        if type(invite_hours) is not int or not 1 <= invite_hours <= 720:
            raise PilotOperationError("INVALID_REQUEST")
        fingerprint = self._digest(f"{reason}\x00{invite_hours}")
        return self.issue_invite(
            issued_by=actor,
            reason=reason,
            now=now,
            invite_ttl=timedelta(hours=invite_hours),
            idempotency_key=key,
            fingerprint=fingerprint,
        )

    def inventory(self, grant: AdminAuthorizationGrant, *, now: datetime) -> dict[str, object]:
        if AdminScope.CUSTOMERS_READ not in grant.scopes:
            raise PilotOperationError("ADMIN_SCOPE_REQUIRED")
        return self._store.inventory(now=now)

    def revoke_admin(
        self,
        grant: AdminAuthorizationGrant,
        *,
        kind: str,
        reference: str,
        reason: str,
        idempotency_key: str,
        now: datetime,
    ) -> None:
        actor = require_staff_write(grant)
        if kind not in {"invite", "grant"}:
            raise PilotOperationError("INVALID_REQUEST")
        self._store.revoke_admin(
            kind=kind,
            reference=self._command_text(reference, maximum=80),
            actor=actor,
            reason=self._command_text(reason),
            idempotency_key=self._command_text(idempotency_key, maximum=160),
            now=now,
        )
