"""Durable staff-provisioned capacity grants with an append-only audit trail."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from application.subscriber_access.staff_capacity import (
    StaffCapacityDestination,
    StaffCapacityError,
    StaffCapacityFailure,
    StaffCapacityGrant,
)
from domain.identity import TenantId


def _grant(row: sqlite3.Row) -> StaffCapacityGrant:
    return StaffCapacityGrant(
        grant_ref=str(row["grant_ref"]),
        tenant_id=TenantId(str(row["tenant_id"])),
        destination=StaffCapacityDestination(str(row["destination"])),
        capacity=int(row["capacity"]),
        reason=str(row["reason"]),
        granted_by=str(row["granted_by"]),
        granted_at=datetime.fromisoformat(str(row["granted_at"])),
        expires_at=datetime.fromisoformat(str(row["expires_at"])),
        revoked_at=None
        if row["revoked_at"] is None
        else datetime.fromisoformat(str(row["revoked_at"])),
        revoked_by=None if row["revoked_by"] is None else str(row["revoked_by"]),
        revocation_reason=None
        if row["revocation_reason"] is None
        else str(row["revocation_reason"]),
    )


class SqliteStaffCapacityStore:
    def __init__(self, database_path: str | Path, *, read_only: bool = False) -> None:
        self.path = Path(database_path)
        self._read_only = read_only
        if read_only:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS staff_capacity_grants (
                    grant_ref TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    capacity INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 500),
                    reason TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    revoked_by TEXT,
                    revocation_reason TEXT,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    request_fingerprint TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_staff_capacity_tenant ON staff_capacity_grants(tenant_id);
                CREATE TABLE IF NOT EXISTS staff_capacity_audit (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    grant_ref TEXT,
                    detail TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS staff_capacity_audit_append_only_update
                    BEFORE UPDATE ON staff_capacity_audit
                    BEGIN SELECT RAISE(ABORT, 'staff capacity audit is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS staff_capacity_audit_append_only_delete
                    BEFORE DELETE ON staff_capacity_audit
                    BEGIN SELECT RAISE(ABORT, 'staff capacity audit is append-only'); END;
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(
            f"{self.path.resolve().as_uri()}?mode=ro" if self._read_only else self.path,
            uri=self._read_only,
            timeout=10,
        )
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 10000")
        return db

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
        with self._connect() as db:
            db.execute(
                """INSERT INTO staff_capacity_audit(occurred_at, actor, action, tenant_id, grant_ref, detail)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    occurred_at.isoformat(),
                    actor,
                    action,
                    str(tenant_id),
                    grant_ref,
                    json.dumps(detail, sort_keys=True, separators=(",", ":")),
                ),
            )

    def insert(
        self, grant: StaffCapacityGrant, *, idempotency_key: str, fingerprint: str
    ) -> StaffCapacityGrant:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if prior is not None:
                if str(prior["request_fingerprint"]) != fingerprint:
                    raise StaffCapacityError(StaffCapacityFailure.IDEMPOTENCY_CONFLICT)
                return _grant(prior)
            db.execute(
                """INSERT INTO staff_capacity_grants(grant_ref, tenant_id, destination, capacity, reason,
                       granted_by, granted_at, expires_at, idempotency_key, request_fingerprint)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    grant.grant_ref,
                    str(grant.tenant_id),
                    grant.destination.value,
                    grant.capacity,
                    grant.reason,
                    grant.granted_by,
                    grant.granted_at.isoformat(),
                    grant.expires_at.isoformat(),
                    idempotency_key,
                    fingerprint,
                ),
            )
            db.execute(
                """INSERT INTO staff_capacity_audit(occurred_at, actor, action, tenant_id, grant_ref, detail)
                   VALUES (?, ?, 'CAPACITY_GRANTED', ?, ?, ?)""",
                (
                    grant.granted_at.isoformat(),
                    grant.granted_by,
                    str(grant.tenant_id),
                    grant.grant_ref,
                    json.dumps(
                        {
                            "capacity": grant.capacity,
                            "destination": grant.destination.value,
                            "expiresAt": grant.expires_at.isoformat(),
                            "reason": grant.reason,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
        return grant

    def by_idempotency(self, idempotency_key: str) -> tuple[StaffCapacityGrant, str] | None:
        if self._read_only and not self.path.is_file():
            return None
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
        return None if row is None else (_grant(row), str(row["request_fingerprint"]))

    def get(self, grant_ref: str) -> StaffCapacityGrant | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE grant_ref = ?", (grant_ref,)
            ).fetchone()
        return None if row is None else _grant(row)

    def revoke(
        self, grant_ref: str, *, revoked_at: datetime, revoked_by: str, reason: str
    ) -> StaffCapacityGrant | None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE grant_ref = ?", (grant_ref,)
            ).fetchone()
            if row is None:
                return None
            if row["revoked_at"] is None:
                db.execute(
                    """UPDATE staff_capacity_grants SET revoked_at = ?, revoked_by = ?, revocation_reason = ?
                       WHERE grant_ref = ? AND revoked_at IS NULL""",
                    (revoked_at.isoformat(), revoked_by, reason, grant_ref),
                )
                db.execute(
                    """INSERT INTO staff_capacity_audit(occurred_at, actor, action, tenant_id, grant_ref, detail)
                       VALUES (?, ?, 'CAPACITY_REVOKED', ?, ?, ?)""",
                    (
                        revoked_at.isoformat(),
                        revoked_by,
                        str(row["tenant_id"]),
                        grant_ref,
                        json.dumps({"reason": reason}, sort_keys=True, separators=(",", ":")),
                    ),
                )
            row = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE grant_ref = ?", (grant_ref,)
            ).fetchone()
        return _grant(row)

    def for_tenant(self, tenant_id: TenantId) -> tuple[StaffCapacityGrant, ...]:
        if self._read_only and not self.path.is_file():
            return ()
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM staff_capacity_grants WHERE tenant_id = ? ORDER BY granted_at DESC",
                (str(tenant_id),),
            ).fetchall()
        return tuple(_grant(row) for row in rows)

    def all_grants(self, *, limit: int) -> tuple[StaffCapacityGrant, ...]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM staff_capacity_grants ORDER BY granted_at DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
        return tuple(_grant(row) for row in rows)

    def audit(
        self, *, limit: int, tenant_id: TenantId | None = None
    ) -> tuple[dict[str, object], ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT * FROM staff_capacity_audit WHERE (? IS NULL OR tenant_id = ?)
                   ORDER BY sequence DESC LIMIT ?""",
                (
                    None if tenant_id is None else str(tenant_id),
                    None if tenant_id is None else str(tenant_id),
                    max(1, min(limit, 500)),
                ),
            ).fetchall()
        return tuple(
            {
                "occurredAt": r["occurred_at"],
                "actor": r["actor"],
                "action": r["action"],
                "tenantId": r["tenant_id"],
                "grantRef": r["grant_ref"],
                "detail": json.loads(r["detail"]),
            }
            for r in rows
        )


class SqliteTenantDirectory:
    """A tenant exists for staff purposes only with at least one active member."""

    def __init__(self, portfolio_database: str | Path) -> None:
        self.path = Path(portfolio_database)

    def tenant_exists(self, tenant_id: TenantId) -> bool:
        if not self.path.is_file():
            return False
        db = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro", uri=True, timeout=10)
        try:
            row = db.execute(
                "SELECT 1 FROM subscriber_memberships WHERE tenant_id = ? AND revoked_at IS NULL LIMIT 1",
                (str(tenant_id),),
            ).fetchone()
        finally:
            db.close()
        return row is not None
