"""Staff-provisioned observation capacity (issue #177, Phase 3).

An authorized AXIGNAL operator may fund observation capacity for AXIGNAL's own use
(Customer Zero) or for a specific customer tenant without a self-service purchase. It
is a separately governed grant: it never creates or edits a payment, subscription,
invoice or Stripe object, and it is never presented as paid capacity. Every grant and
revocation is attributed, reasoned, bounded in time and capacity, idempotent and
recorded in an append-only audit trail.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.identity import TenantId

MAX_CAPACITY = 500
MAX_VALIDITY = timedelta(days=366)
MIN_REASON = 8
MAX_REASON = 500


class StaffCapacityDestination(StrEnum):
    """Who the capacity is for. Internal use is AXIGNAL's own Customer Zero tenant."""

    AXIGNAL_INTERNAL = "AXIGNAL_INTERNAL"
    CUSTOMER_ACCOUNT = "CUSTOMER_ACCOUNT"


class StaffCapacityFailure(StrEnum):
    SCOPE_REQUIRED = "SCOPE_REQUIRED"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"
    TENANT_UNKNOWN = "TENANT_UNKNOWN"
    INVALID_REQUEST = "INVALID_REQUEST"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    GRANT_NOT_FOUND = "GRANT_NOT_FOUND"


class StaffCapacityError(Exception):
    def __init__(self, failure: StaffCapacityFailure, detail: str = "") -> None:
        super().__init__(detail or failure.value)
        self.failure = failure


@dataclass(frozen=True, slots=True)
class StaffCapacityGrant:
    grant_ref: str
    tenant_id: TenantId
    destination: StaffCapacityDestination
    capacity: int
    reason: str
    granted_by: str
    granted_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    revoked_by: str | None = None
    revocation_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.grant_ref.startswith("staff_capacity_"):
            raise ValueError("staff capacity grant reference is required")
        if type(self.capacity) is not int or not 1 <= self.capacity <= MAX_CAPACITY:
            raise ValueError("staff capacity must be between 1 and 500")
        for value in (self.granted_at, self.expires_at, self.revoked_at):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("staff capacity times must be timezone-aware")
        if self.expires_at <= self.granted_at:
            raise ValueError("staff capacity must expire after it is granted")

    def active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.granted_at <= now < self.expires_at

    def to_wire(self, now: datetime) -> dict[str, object]:
        return {
            "grantRef": self.grant_ref,
            "tenantId": str(self.tenant_id),
            "destination": self.destination.value,
            "capacity": self.capacity,
            "reason": self.reason,
            "grantedBy": self.granted_by,
            "grantedAt": self.granted_at.isoformat(),
            "expiresAt": self.expires_at.isoformat(),
            "revokedAt": None if self.revoked_at is None else self.revoked_at.isoformat(),
            "revokedBy": self.revoked_by,
            "revocationReason": self.revocation_reason,
            "state": "ACTIVE" if self.active(now) else "REVOKED" if self.revoked_at else "EXPIRED",
            # Explicitly not billing: staff-funded capacity never claims a verified payment.
            "provenance": "STAFF_GRANT_NOT_BILLING",
        }


@dataclass(frozen=True, slots=True)
class StaffCapacityTotal:
    capacity: int
    confirmed_at: datetime | None
    grant_refs: tuple[str, ...]


class StaffCapacityStore(Protocol):
    def insert(
        self, grant: StaffCapacityGrant, *, idempotency_key: str, fingerprint: str
    ) -> StaffCapacityGrant: ...
    def by_idempotency(self, idempotency_key: str) -> tuple[StaffCapacityGrant, str] | None: ...
    def get(self, grant_ref: str) -> StaffCapacityGrant | None: ...
    def revoke(
        self, grant_ref: str, *, revoked_at: datetime, revoked_by: str, reason: str
    ) -> StaffCapacityGrant | None: ...
    def for_tenant(self, tenant_id: TenantId) -> tuple[StaffCapacityGrant, ...]: ...
    def all_grants(self, *, limit: int) -> tuple[StaffCapacityGrant, ...]: ...
    def record_audit(
        self,
        *,
        occurred_at: datetime,
        actor: str,
        action: str,
        tenant_id: TenantId,
        grant_ref: str | None,
        detail: dict[str, object],
    ) -> None: ...
    def audit(
        self, *, limit: int, tenant_id: TenantId | None = None
    ) -> tuple[dict[str, object], ...]: ...


class TenantDirectory(Protocol):
    """Only tenants that exist with an active member can receive capacity."""

    def tenant_exists(self, tenant_id: TenantId) -> bool: ...


class StaffCapacityReader(Protocol):
    def active_total(self, tenant_id: TenantId, *, now: datetime) -> StaffCapacityTotal: ...


def require_staff_write(grant: AdminAuthorizationGrant) -> str:
    """Defense in depth: the HTTP guard authorizes, the service re-checks the grant."""
    if AdminScope.CUSTOMERS_WRITE not in grant.scopes:
        raise StaffCapacityError(StaffCapacityFailure.SCOPE_REQUIRED)
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise StaffCapacityError(StaffCapacityFailure.STEP_UP_REQUIRED)
    return f"admin:{grant.principal_id}"


def _aware(now: datetime) -> datetime:
    if now.tzinfo is None or now.utcoffset() is None:
        raise StaffCapacityError(
            StaffCapacityFailure.INVALID_REQUEST, "time must be timezone-aware"
        )
    return now.astimezone(UTC)


def _reason(value: str) -> str:
    if not isinstance(value, str) or not MIN_REASON <= len(value.strip()) <= MAX_REASON:
        raise StaffCapacityError(
            StaffCapacityFailure.INVALID_REQUEST, "a reason of 8-500 characters is required"
        )
    return value.strip()


class StaffCapacityService(StaffCapacityReader):
    def __init__(
        self,
        store: StaffCapacityStore,
        tenants: TenantDirectory,
        *,
        internal_tenant: TenantId | None = None,
    ) -> None:
        self._store = store
        self._tenants = tenants
        self._internal = internal_tenant

    def preview(
        self,
        admin: AdminAuthorizationGrant,
        *,
        tenant_id: TenantId,
        destination: StaffCapacityDestination,
        capacity: int,
        expires_at: datetime,
        now: datetime,
    ) -> dict[str, object]:
        """What will happen, before anything is written."""
        require_staff_write(admin)
        now = _aware(now)
        self._validate(tenant_id, destination, capacity, expires_at, now)
        current = self.active_total(tenant_id, now=now)
        return {
            "tenantId": str(tenant_id),
            "destination": destination.value,
            "currentStaffCapacity": current.capacity,
            "staffCapacityAfter": current.capacity + capacity,
            "expiresAt": expires_at.astimezone(UTC).isoformat(),
            "billingChanged": False,
            "checkoutCreated": False,
            "provenance": "STAFF_GRANT_NOT_BILLING",
        }

    def _validate(
        self,
        tenant_id: TenantId,
        destination: StaffCapacityDestination,
        capacity: int,
        expires_at: datetime,
        now: datetime,
    ) -> None:
        if type(capacity) is not int or not 1 <= capacity <= MAX_CAPACITY:
            raise StaffCapacityError(StaffCapacityFailure.INVALID_REQUEST, "capacity must be 1-500")
        expires = _aware(expires_at)
        if expires <= now or expires - now > MAX_VALIDITY:
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST,
                "expiry must be in the future and within a year",
            )
        if not isinstance(destination, StaffCapacityDestination):
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST, "destination is required"
            )
        if not self._tenants.tenant_exists(tenant_id):
            raise StaffCapacityError(StaffCapacityFailure.TENANT_UNKNOWN)
        # The destination must agree with the tenant: no accidental internal grant to a customer.
        if destination is StaffCapacityDestination.AXIGNAL_INTERNAL and (
            self._internal is None or tenant_id != self._internal
        ):
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST,
                "internal capacity is only for the configured AXIGNAL tenant",
            )
        if (
            destination is StaffCapacityDestination.CUSTOMER_ACCOUNT
            and self._internal is not None
            and tenant_id == self._internal
        ):
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST,
                "the AXIGNAL tenant is internal, not a customer account",
            )

    def grant(
        self,
        admin: AdminAuthorizationGrant,
        *,
        tenant_id: TenantId,
        destination: StaffCapacityDestination,
        capacity: int,
        reason: str,
        expires_at: datetime,
        idempotency_key: str,
        now: datetime,
    ) -> StaffCapacityGrant:
        actor = require_staff_write(admin)
        now = _aware(now)
        reason = _reason(reason)
        if not isinstance(idempotency_key, str) or not 8 <= len(idempotency_key) <= 160:
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST, "idempotency key is required"
            )
        fingerprint = hashlib.sha256(
            json.dumps(
                [
                    str(tenant_id),
                    destination.value,
                    capacity,
                    reason,
                    _aware(expires_at).isoformat(),
                    actor,
                ],
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        prior = self._store.by_idempotency(idempotency_key)
        if prior is not None:
            existing, prior_fingerprint = prior
            if prior_fingerprint != fingerprint:
                raise StaffCapacityError(StaffCapacityFailure.IDEMPOTENCY_CONFLICT)
            return existing
        self._validate(tenant_id, destination, capacity, expires_at, now)
        grant = StaffCapacityGrant(
            grant_ref=f"staff_capacity_{secrets.token_hex(12)}",
            tenant_id=tenant_id,
            destination=destination,
            capacity=capacity,
            reason=reason,
            granted_by=actor,
            granted_at=now,
            expires_at=_aware(expires_at),
        )
        return self._store.insert(grant, idempotency_key=idempotency_key, fingerprint=fingerprint)

    def revoke(
        self, admin: AdminAuthorizationGrant, *, grant_ref: str, reason: str, now: datetime
    ) -> StaffCapacityGrant:
        actor = require_staff_write(admin)
        now = _aware(now)
        reason = _reason(reason)
        existing = self._store.get(grant_ref)
        if existing is None:
            raise StaffCapacityError(StaffCapacityFailure.GRANT_NOT_FOUND)
        if existing.revoked_at is not None:
            return existing  # revoking twice is idempotent and keeps the first record
        revoked = self._store.revoke(grant_ref, revoked_at=now, revoked_by=actor, reason=reason)
        if revoked is None:
            raise StaffCapacityError(StaffCapacityFailure.GRANT_NOT_FOUND)
        return revoked

    def active_total(self, tenant_id: TenantId, *, now: datetime) -> StaffCapacityTotal:
        active = [g for g in self._store.for_tenant(tenant_id) if g.active(now)]
        return StaffCapacityTotal(
            sum(g.capacity for g in active),
            min((g.granted_at for g in active), default=None),
            tuple(g.grant_ref for g in active),
        )

    def require_tenant(self, tenant_id: TenantId) -> None:
        """Staff acts only on a tenant that exists with an active member (no IDOR by guess)."""
        if not self._tenants.tenant_exists(tenant_id):
            raise StaffCapacityError(StaffCapacityFailure.TENANT_UNKNOWN)

    def for_tenant(self, tenant_id: TenantId) -> tuple[StaffCapacityGrant, ...]:
        return self._store.for_tenant(tenant_id)

    def audit(
        self, *, limit: int, tenant_id: TenantId | None = None
    ) -> tuple[dict[str, object], ...]:
        return self._store.audit(limit=limit, tenant_id=tenant_id)

    def record_audit(
        self,
        *,
        occurred_at: datetime,
        actor: str,
        action: str,
        tenant_id: TenantId,
        grant_ref: str | None,
        detail: dict[str, object],
    ) -> None:
        self._store.record_audit(
            occurred_at=occurred_at,
            actor=actor,
            action=action,
            tenant_id=tenant_id,
            grant_ref=grant_ref,
            detail=detail,
        )
