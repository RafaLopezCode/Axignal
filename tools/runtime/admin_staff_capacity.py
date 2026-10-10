"""Admin HTTP for staff-provisioned capacity and staff-operated organizations (issue #177).

Every write is ``admin:customers:write`` at SENSITIVE risk (fresh step-up session), re-checked
by the service, attributed to the Admin principal and audited. Nothing here touches billing:
no checkout, payment, subscription, invoice or Stripe object is created or edited.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from application.subscriber_access.staff_capacity import (
    StaffCapacityDestination,
    StaffCapacityError,
    StaffCapacityFailure,
    StaffCapacityService,
    require_staff_write,
)
from application.subscriber_portfolio.models import AddOrganizationRequest
from domain.admin_access import AdminRiskClass, AdminScope
from domain.identity import TenantId
from tools.runtime.admin_access import AdminHttpAccessGuard

ROUTE = "/internal/admin/staff-capacity"


@dataclass(frozen=True, slots=True)
class StaffOperations:
    capacity: StaffCapacityService
    add_for_tenant: Callable[[TenantId, str, AddOrganizationRequest], object]
    entitlement_source: Callable[[TenantId], str]
    audit: Callable[..., tuple[dict[str, object], ...]]
    record_audit: Callable[..., None]


def _text(payload: dict[str, object], key: str, *, limit: int = 2048) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise StaffCapacityError(StaffCapacityFailure.INVALID_REQUEST, f"{key} is required")
    return value.strip()


def _tenant(value: str) -> TenantId:
    if not 3 <= len(value) <= 160 or not all(c.isalnum() or c in ":_-." for c in value):
        raise StaffCapacityError(StaffCapacityFailure.INVALID_REQUEST, "tenantId is invalid")
    return TenantId(value)


def _when(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise StaffCapacityError(
            StaffCapacityFailure.INVALID_REQUEST, "expiresAt must be ISO-8601"
        ) from error
    if parsed.tzinfo is None:
        raise StaffCapacityError(StaffCapacityFailure.INVALID_REQUEST, "expiresAt needs a timezone")
    return parsed.astimezone(UTC)


def staff_capacity_request(
    guard: AdminHttpAccessGuard,
    staff: StaffOperations,
    *,
    authorization: str | None,
    action: str,
    query: dict[str, str],
    payload: dict[str, object] | None,
    now: datetime,
) -> dict[str, object]:
    write = payload is not None
    grant = guard.authorize_header(
        authorization,
        required_scope=AdminScope.CUSTOMERS_WRITE if write else AdminScope.CUSTOMERS_READ,
        risk=AdminRiskClass.SENSITIVE if write else AdminRiskClass.READ,
        now=now,
    )
    if not write:
        tenant = _tenant(query.get("tenantId", ""))
        total = staff.capacity.active_total(tenant, now=now)
        return {
            "tenantId": str(tenant),
            "entitlementSource": staff.entitlement_source(tenant),
            "activeStaffCapacity": total.capacity,
            "grants": [g.to_wire(now) for g in staff.capacity.for_tenant(tenant)],
            "audit": list(staff.audit(limit=50, tenant_id=tenant)),
        }
    assert payload is not None
    if action in {"preview", "grant"}:
        tenant = _tenant(_text(payload, "tenantId", limit=160))
        destination = StaffCapacityDestination(_text(payload, "destination", limit=40))
        capacity = payload.get("capacity")
        if type(capacity) is not int:
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST, "capacity must be an integer"
            )
        expires = _when(_text(payload, "expiresAt", limit=64))
        if action == "preview":
            return staff.capacity.preview(
                grant,
                tenant_id=tenant,
                destination=destination,
                capacity=capacity,
                expires_at=expires,
                now=now,
            )
        created = staff.capacity.grant(
            grant,
            tenant_id=tenant,
            destination=destination,
            capacity=capacity,
            reason=_text(payload, "reason", limit=500),
            expires_at=expires,
            idempotency_key=_text(payload, "idempotencyKey", limit=160),
            now=now,
        )
        return {
            "grant": created.to_wire(now),
            "entitlementSource": staff.entitlement_source(tenant),
        }
    if action == "revoke":
        revoked = staff.capacity.revoke(
            grant,
            grant_ref=_text(payload, "grantRef", limit=80),
            reason=_text(payload, "reason", limit=500),
            now=now,
        )
        return {
            "grant": revoked.to_wire(now),
            "entitlementSource": staff.entitlement_source(revoked.tenant_id),
        }
    if action == "organizations":
        actor = require_staff_write(grant)
        tenant = _tenant(_text(payload, "tenantId", limit=160))
        staff.capacity.require_tenant(tenant)
        reason = _text(payload, "reason", limit=500)
        if len(reason) < 8:
            raise StaffCapacityError(
                StaffCapacityFailure.INVALID_REQUEST, "a reason of 8-500 characters is required"
            )
        request = AddOrganizationRequest(
            locator=_text(payload, "locator"),
            idempotency_key=_text(payload, "idempotencyKey", limit=160),
            display_label=None,
        )
        result = staff.add_for_tenant(tenant, actor, request)
        status = getattr(result, "status", None)
        entry = getattr(result, "entry", None)
        outcome = {
            "status": None if status is None else str(getattr(status, "value", status)),
            "focusId": None if entry is None else str(entry.focus_id),
            "identityReason": getattr(result, "identity_reason", None),
            "checkoutCreated": False,
        }
        staff.record_audit(
            occurred_at=now,
            actor=actor,
            action="ORGANIZATION_ADDED_BY_STAFF",
            tenant_id=tenant,
            grant_ref=None,
            detail={"locator": request.locator, "reason": reason, **outcome},
        )
        return outcome
    raise StaffCapacityError(StaffCapacityFailure.INVALID_REQUEST, "unknown staff capacity action")
