"""Composition of staff-provisioned capacity; one builder for every runtime reader."""

from __future__ import annotations

from pathlib import Path

from application.subscriber_access.staff_capacity import StaffCapacityService
from domain.identity import TenantId
from pipeline.subscriber_access.staff_capacity_store import (
    SqliteStaffCapacityStore,
    SqliteTenantDirectory,
)

STAFF_CAPACITY_DATABASE = "subscriber-staff-capacity.sqlite3"


def build_staff_capacity(
    root: Path, *, enabled: bool, internal_tenant: str | None, read_only: bool = False
) -> StaffCapacityService | None:
    """None when disabled; read-only readers never create the database."""
    if not enabled:
        return None
    path = root / STAFF_CAPACITY_DATABASE
    if read_only and not path.is_file():
        return None
    return StaffCapacityService(
        SqliteStaffCapacityStore(path, read_only=read_only),
        SqliteTenantDirectory(root / "subscriber-runtime.sqlite3"),
        internal_tenant=None if internal_tenant is None else TenantId(internal_tenant),
    )
