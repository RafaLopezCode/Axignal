"""Staff-provisioned capacity is governed, audited, expiring and never billing (issue #177)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.subscriber_access.staff_capacity import (
    StaffCapacityDestination,
    StaffCapacityError,
    StaffCapacityFailure,
    StaffCapacityService,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.identity import TenantId
from pipeline.subscriber_access.staff_capacity_store import SqliteStaffCapacityStore

NOW = datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
CUSTOMER = TenantId("tenant_customer_a")
OTHER = TenantId("tenant_customer_b")
INTERNAL = TenantId("tenant_axignal_internal")
CUSTOMER_GRANT = StaffCapacityDestination.CUSTOMER_ACCOUNT


class _Tenants:
    def __init__(self, *known: TenantId) -> None:
        self.known = set(known)

    def tenant_exists(self, tenant_id: TenantId) -> bool:
        return tenant_id in self.known


def _admin(
    role: AdminRole = AdminRole.FOUNDER, assurance: AdminAssurance = AdminAssurance.STEP_UP
) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"principal-{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=assurance,
    )


def _service(tmp_path: Path) -> StaffCapacityService:
    return StaffCapacityService(
        SqliteStaffCapacityStore(tmp_path / "staff.sqlite3"),
        _Tenants(CUSTOMER, OTHER, INTERNAL),
        internal_tenant=INTERNAL,
    )


def _grant(service: StaffCapacityService, **overrides: object):  # type: ignore[no-untyped-def]
    values: dict[str, object] = {
        "tenant_id": CUSTOMER,
        "destination": CUSTOMER_GRANT,
        "capacity": 3,
        "reason": "Client onboarding without checkout",
        "expires_at": NOW + timedelta(days=30),
        "idempotency_key": "grant:customer-a:1",
        "now": NOW,
    }
    values.update(overrides)
    admin = values.pop("admin", _admin())
    return service.grant(admin, **values)  # type: ignore[arg-type]


def test_grant_requires_write_scope_and_fresh_step_up(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(StaffCapacityError) as missing_scope:
        _grant(service, admin=_admin(AdminRole.SUPPORT))
    assert missing_scope.value.failure is StaffCapacityFailure.SCOPE_REQUIRED
    with pytest.raises(StaffCapacityError) as no_step_up:
        _grant(service, admin=_admin(assurance=AdminAssurance.PRIMARY))
    assert no_step_up.value.failure is StaffCapacityFailure.STEP_UP_REQUIRED
    assert service.for_tenant(CUSTOMER) == ()
    assert service.audit(limit=10) == ()


def test_preview_writes_nothing_and_declares_no_billing(tmp_path: Path) -> None:
    service = _service(tmp_path)
    preview = service.preview(
        _admin(),
        tenant_id=CUSTOMER,
        destination=CUSTOMER_GRANT,
        capacity=2,
        expires_at=NOW + timedelta(days=7),
        now=NOW,
    )
    assert preview["staffCapacityAfter"] == 2
    assert (preview["billingChanged"], preview["checkoutCreated"]) == (False, False)
    assert preview["provenance"] == "STAFF_GRANT_NOT_BILLING"
    assert service.for_tenant(CUSTOMER) == () and service.audit(limit=10) == ()


@pytest.mark.parametrize(
    ("overrides", "failure"),
    [
        ({"tenant_id": TenantId("tenant_unknown")}, StaffCapacityFailure.TENANT_UNKNOWN),
        ({"capacity": 0}, StaffCapacityFailure.INVALID_REQUEST),
        ({"capacity": 501}, StaffCapacityFailure.INVALID_REQUEST),
        ({"expires_at": NOW}, StaffCapacityFailure.INVALID_REQUEST),
        ({"expires_at": NOW + timedelta(days=400)}, StaffCapacityFailure.INVALID_REQUEST),
        ({"reason": "short"}, StaffCapacityFailure.INVALID_REQUEST),
        (
            {"destination": StaffCapacityDestination.AXIGNAL_INTERNAL},
            StaffCapacityFailure.INVALID_REQUEST,
        ),
        ({"tenant_id": INTERNAL}, StaffCapacityFailure.INVALID_REQUEST),
    ],
)
def test_invalid_grants_are_refused_without_state(
    tmp_path: Path, overrides: dict[str, object], failure: StaffCapacityFailure
) -> None:
    service = _service(tmp_path)
    with pytest.raises(StaffCapacityError) as refused:
        _grant(service, **overrides)
    assert refused.value.failure is failure
    assert service.audit(limit=10) == ()


def test_internal_capacity_only_for_the_configured_axignal_tenant(tmp_path: Path) -> None:
    service = _service(tmp_path)
    granted = _grant(
        service,
        tenant_id=INTERNAL,
        destination=StaffCapacityDestination.AXIGNAL_INTERNAL,
        idempotency_key="grant:internal:1",
    )
    assert service.active_total(INTERNAL, now=NOW).capacity == 3
    assert service.active_total(CUSTOMER, now=NOW).capacity == 0
    assert granted.to_wire(NOW)["destination"] == "AXIGNAL_INTERNAL"


def test_grant_is_idempotent_and_conflicting_reuse_is_refused(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = _grant(service)
    replay = _grant(service, now=NOW + timedelta(minutes=1))
    assert replay.grant_ref == first.grant_ref
    assert service.active_total(CUSTOMER, now=NOW).capacity == 3
    with pytest.raises(StaffCapacityError) as conflict:
        _grant(service, capacity=50)
    assert conflict.value.failure is StaffCapacityFailure.IDEMPOTENCY_CONFLICT
    assert len(service.audit(limit=10)) == 1


def test_capacity_is_tenant_isolated_and_additive(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _grant(service)
    _grant(service, capacity=2, idempotency_key="grant:customer-a:2")
    _grant(service, tenant_id=OTHER, capacity=1, idempotency_key="grant:customer-b:1")
    assert service.active_total(CUSTOMER, now=NOW).capacity == 5
    assert service.active_total(OTHER, now=NOW).capacity == 1
    assert {g.tenant_id for g in service.for_tenant(OTHER)} == {OTHER}
    assert all(row["tenantId"] == str(OTHER) for row in service.audit(limit=10, tenant_id=OTHER))


def test_expiry_and_revocation_withdraw_capacity_and_are_audited(tmp_path: Path) -> None:
    service = _service(tmp_path)
    short = _grant(service, expires_at=NOW + timedelta(days=1))
    assert service.active_total(CUSTOMER, now=NOW + timedelta(days=2)).capacity == 0
    assert short.to_wire(NOW + timedelta(days=2))["state"] == "EXPIRED"

    long = _grant(service, idempotency_key="grant:customer-a:2")
    with pytest.raises(StaffCapacityError):
        service.revoke(
            _admin(AdminRole.SUPPORT), grant_ref=long.grant_ref, reason="x" * 10, now=NOW
        )
    revoked = service.revoke(
        _admin(), grant_ref=long.grant_ref, reason="Client offboarded", now=NOW
    )
    assert revoked.revoked_at == NOW and revoked.revoked_by == "admin:principal-founder"
    again = service.revoke(
        _admin(), grant_ref=long.grant_ref, reason="Second attempt", now=NOW + timedelta(hours=1)
    )
    assert again.revoked_at == NOW and again.revocation_reason == "Client offboarded"
    assert service.active_total(CUSTOMER, now=NOW).capacity == 3  # only the unexpired, unrevoked
    with pytest.raises(StaffCapacityError) as missing:
        service.revoke(
            _admin(), grant_ref="staff_capacity_missing", reason="No such grant", now=NOW
        )
    assert missing.value.failure is StaffCapacityFailure.GRANT_NOT_FOUND
    actions = [row["action"] for row in service.audit(limit=10)]
    assert actions == ["CAPACITY_REVOKED", "CAPACITY_GRANTED", "CAPACITY_GRANTED"]
    assert all(str(row["actor"]).startswith("admin:") for row in service.audit(limit=10))


def test_audit_trail_is_append_only(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _grant(service)
    with sqlite3.connect(tmp_path / "staff.sqlite3") as db:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("UPDATE staff_capacity_audit SET actor = 'someone-else'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute("DELETE FROM staff_capacity_audit")


def test_grant_wire_never_claims_billing(tmp_path: Path) -> None:
    wire = _grant(_service(tmp_path)).to_wire(NOW)
    assert wire["provenance"] == "STAFF_GRANT_NOT_BILLING"
    assert not {"invoice", "subscription", "checkout", "payment"} & {k.lower() for k in wire}
