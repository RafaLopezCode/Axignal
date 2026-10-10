"""SQLite Focus portfolio with authorization-before-read and serialized capacity."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import cast

from application.subscriber_identity.runtime import TrustedSubscriberContext
from application.subscriber_portfolio.models import (
    AddOrganizationRequest,
    AddStatus,
    FocusStatus,
    PendingAttentionEntry,
    PendingStatus,
    PortfolioEntry,
    PortfolioError,
    PortfolioFailure,
)
from domain.identity import OrganizationId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.xeed.model import Xeed


class SqliteSubscriberPortfolioStore:
    """Durable private Xeed lifecycle store sharing subscriber identity SQLite."""

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
                CREATE TABLE IF NOT EXISTS subscriber_focuses (
                    focus_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    organization_id TEXT NOT NULL,
                    label TEXT,
                    status TEXT NOT NULL CHECK(status IN ('ACTIVE','PAUSED','REMOVED')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_active_focus_organization
                ON subscriber_focuses(tenant_id, organization_id)
                WHERE status IN ('ACTIVE','PAUSED');
                CREATE INDEX IF NOT EXISTS idx_focus_tenant_status
                ON subscriber_focuses(tenant_id, status, created_at);
                CREATE TABLE IF NOT EXISTS subscriber_portfolio_pending (
                    pending_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    idempotency_key TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    locator TEXT NOT NULL,
                    display_label TEXT,
                    status TEXT NOT NULL CHECK(status IN (
                        'IDENTITY_PENDING','IDENTITY_REJECTED','CAPACITY_UNKNOWN',
                        'CAPACITY_PENDING','PURCHASE_AUTHORITY_REQUIRED','RESOLVED','CANCELLED'
                    )),
                    resolved_focus_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (tenant_id, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS subscriber_portfolio_commands (
                    tenant_id TEXT NOT NULL REFERENCES subscriber_tenants(tenant_id),
                    idempotency_key TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    focus_id TEXT,
                    previous_organization_id TEXT,
                    result_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, idempotency_key)
                );
                PRAGMA user_version = 1;
                """
            )
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(subscriber_portfolio_pending)")
            }
            if "identity_reason" not in columns:
                # Additive migration (spec 052): existing pending rows keep reason NULL.
                connection.execute(
                    "ALTER TABLE subscriber_portfolio_pending ADD COLUMN identity_reason TEXT"
                )

    @staticmethod
    def _entry(row: sqlite3.Row) -> PortfolioEntry:
        created_at = datetime.fromisoformat(str(row["created_at"]))
        updated_at = datetime.fromisoformat(str(row["updated_at"]))
        xeed = Xeed(
            XeedId(str(row["focus_id"])),
            TenantId(str(row["tenant_id"])),
            OrganizationId(str(row["organization_id"])),
            None if row["label"] is None else str(row["label"]),
        )
        return PortfolioEntry(xeed, FocusStatus(str(row["status"])), created_at, updated_at)

    @staticmethod
    def _pending_entry(row: sqlite3.Row) -> PendingAttentionEntry:
        return PendingAttentionEntry(
            pending_id=str(row["pending_id"]),
            tenant_id=TenantId(str(row["tenant_id"])),
            locator=str(row["locator"]),
            idempotency_key=str(row["idempotency_key"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            display_label=None if row["display_label"] is None else str(row["display_label"]),
            status=PendingStatus(str(row["status"])),
            identity_reason=(
                None if row["identity_reason"] is None else str(row["identity_reason"])
            ),
        )

    @staticmethod
    def _require_membership(
        connection: sqlite3.Connection,
        context: TrustedSubscriberContext,
    ) -> None:
        principal = connection.execute(
            "SELECT 1 FROM subscriber_principals WHERE principal_id = ?",
            (context.principal_id,),
        ).fetchone()
        membership = connection.execute(
            """SELECT 1 FROM subscriber_memberships
               WHERE principal_id = ? AND tenant_id = ? AND revoked_at IS NULL""",
            (context.principal_id, context.tenant_id),
        ).fetchone()
        if principal is None or membership is None:
            raise PortfolioError(PortfolioFailure.ACCESS_DENIED)

    @staticmethod
    def _fingerprint(value: object) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    def _existing_command(
        self,
        connection: sqlite3.Connection,
        tenant_id: TenantId,
        idempotency_key: str,
        operation: str,
        fingerprint: str,
    ) -> sqlite3.Row | None:
        row = cast(
            sqlite3.Row | None,
            connection.execute(
                """SELECT * FROM subscriber_portfolio_commands
               WHERE tenant_id = ? AND idempotency_key = ?""",
                (tenant_id, idempotency_key),
            ).fetchone(),
        )
        if row is not None and (
            str(row["operation"]) != operation or str(row["request_fingerprint"]) != fingerprint
        ):
            raise PortfolioError(PortfolioFailure.IDEMPOTENCY_CONFLICT)
        return row

    @staticmethod
    def _record_command(
        connection: sqlite3.Connection,
        tenant_id: TenantId,
        idempotency_key: str,
        operation: str,
        fingerprint: str,
        focus_id: XeedId | None,
        previous_organization_id: OrganizationId | None,
        result_status: str,
        now: datetime,
    ) -> None:
        connection.execute(
            """INSERT INTO subscriber_portfolio_commands(
                   tenant_id, idempotency_key, operation, request_fingerprint,
                   focus_id, previous_organization_id, result_status, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tenant_id,
                idempotency_key,
                operation,
                fingerprint,
                focus_id,
                previous_organization_id,
                result_status,
                now.isoformat(),
            ),
        )

    def _get_entry(
        self,
        connection: sqlite3.Connection,
        tenant_id: TenantId,
        focus_id: XeedId,
        *,
        include_removed: bool = False,
    ) -> sqlite3.Row | None:
        sql = "SELECT * FROM subscriber_focuses WHERE tenant_id = ? AND focus_id = ?"
        if not include_removed:
            sql += " AND status IN ('ACTIVE','PAUSED')"
        return cast(sqlite3.Row | None, connection.execute(sql, (tenant_id, focus_id)).fetchone())

    def list_authorized(self, context: TrustedSubscriberContext) -> tuple[PortfolioEntry, ...]:
        with self._connect() as connection:
            connection.execute("BEGIN")
            self._require_membership(connection, context)
            rows = connection.execute(
                """SELECT * FROM subscriber_focuses
                   WHERE tenant_id = ? AND status IN ('ACTIVE','PAUSED')
                   ORDER BY created_at, focus_id""",
                (context.tenant_id,),
            ).fetchall()
        return tuple(self._entry(row) for row in rows)

    def get_authorized(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
    ) -> PortfolioEntry | None:
        with self._connect() as connection:
            connection.execute("BEGIN")
            self._require_membership(connection, context)
            row = self._get_entry(connection, context.tenant_id, focus_id)
        return None if row is None else self._entry(row)

    def list_pending_authorized(
        self,
        context: TrustedSubscriberContext,
    ) -> tuple[PendingAttentionEntry, ...]:
        with self._connect() as connection:
            connection.execute("BEGIN")
            self._require_membership(connection, context)
            rows = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND status IN (
                     'IDENTITY_PENDING','IDENTITY_REJECTED','CAPACITY_UNKNOWN',
                     'CAPACITY_PENDING','PURCHASE_AUTHORITY_REQUIRED'
                   ) ORDER BY created_at, pending_id""",
                (context.tenant_id,),
            ).fetchall()
        return tuple(self._pending_entry(row) for row in rows)

    def get_pending_authorized(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
    ) -> PendingAttentionEntry | None:
        with self._connect() as connection:
            connection.execute("BEGIN")
            self._require_membership(connection, context)
            row = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND pending_id = ?
                     AND status IN (
                       'IDENTITY_PENDING','IDENTITY_REJECTED','CAPACITY_UNKNOWN',
                       'CAPACITY_PENDING','PURCHASE_AUTHORITY_REQUIRED'
                     )""",
                (context.tenant_id, pending_id),
            ).fetchone()
        return None if row is None else self._pending_entry(row)

    def get_xeed(self, focus_id: XeedId) -> Xeed | None:
        """Internal XeedReader hook; callers must use AuthorizedXeedReader."""

        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM subscriber_focuses
                   WHERE focus_id = ? AND status IN ('ACTIVE','PAUSED')""",
                (focus_id,),
            ).fetchone()
        return None if row is None else self._entry(row).xeed

    def record_pending(
        self,
        context: TrustedSubscriberContext,
        request: AddOrganizationRequest,
        now: datetime,
        reason: str | None = None,
        status: PendingStatus = PendingStatus.IDENTITY_PENDING,
    ) -> None:
        fingerprint = self._fingerprint(["PENDING", request.locator, request.display_label])
        reason = None if reason is None else reason[:160]
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            existing = self._existing_command(
                connection,
                context.tenant_id,
                request.idempotency_key,
                "PENDING",
                fingerprint,
            )
            if existing is not None:
                connection.execute(
                    """UPDATE subscriber_portfolio_pending
                       SET status = ?, identity_reason = ?, updated_at = ?
                       WHERE tenant_id = ? AND idempotency_key = ?
                         AND status NOT IN ('RESOLVED','CANCELLED')""",
                    (
                        status.value,
                        reason,
                        now.isoformat(),
                        context.tenant_id,
                        request.idempotency_key,
                    ),
                )
                return
            connection.execute(
                """INSERT INTO subscriber_portfolio_pending(
                       pending_id, tenant_id, idempotency_key, request_fingerprint,
                       locator, display_label, status, created_at, updated_at,
                       identity_reason
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    f"pending_{uuid.uuid4().hex}",
                    context.tenant_id,
                    request.idempotency_key,
                    fingerprint,
                    request.locator,
                    request.display_label,
                    status.value,
                    now.isoformat(),
                    now.isoformat(),
                    reason,
                ),
            )
            self._record_command(
                connection,
                context.tenant_id,
                request.idempotency_key,
                "PENDING",
                fingerprint,
                None,
                None,
                (
                    AddStatus.CAPACITY_UNKNOWN.value
                    if status is PendingStatus.CAPACITY_UNKNOWN
                    else AddStatus.IDENTITY_PENDING.value
                ),
                now,
            )

    def mark_pending_status(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
        status: PendingStatus,
        now: datetime,
    ) -> PendingAttentionEntry:
        if status in (PendingStatus.RESOLVED, PendingStatus.CANCELLED):
            raise ValueError("only retryable pending status can be set directly")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            row = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND pending_id = ?""",
                (context.tenant_id, pending_id),
            ).fetchone()
            if row is None or str(row["status"]) in ("RESOLVED", "CANCELLED"):
                raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
            connection.execute(
                """UPDATE subscriber_portfolio_pending SET status = ?, updated_at = ?
                   WHERE tenant_id = ? AND pending_id = ?""",
                (status.value, now.isoformat(), context.tenant_id, pending_id),
            )
            updated = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND pending_id = ?""",
                (context.tenant_id, pending_id),
            ).fetchone()
        if updated is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        return self._pending_entry(updated)

    def cancel_pending(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
        idempotency_key: str,
        now: datetime,
    ) -> PendingAttentionEntry:
        if not idempotency_key.strip() or len(idempotency_key) > 160:
            raise PortfolioError(PortfolioFailure.INVALID_COMMAND)
        fingerprint = self._fingerprint(["CANCEL_PENDING", pending_id])
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            prior = self._existing_command(
                connection,
                context.tenant_id,
                idempotency_key,
                "CANCEL_PENDING",
                fingerprint,
            )
            row = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND pending_id = ?""",
                (context.tenant_id, pending_id),
            ).fetchone()
            if row is None:
                raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
            current = PendingStatus(str(row["status"]))
            if prior is None:
                if current is PendingStatus.RESOLVED:
                    raise PortfolioError(PortfolioFailure.INVALID_TRANSITION)
                if current is not PendingStatus.CANCELLED:
                    connection.execute(
                        """UPDATE subscriber_portfolio_pending SET status = 'CANCELLED', updated_at = ?
                           WHERE tenant_id = ? AND pending_id = ?""",
                        (now.isoformat(), context.tenant_id, pending_id),
                    )
                    self._record_command(
                        connection,
                        context.tenant_id,
                        idempotency_key,
                        "CANCEL_PENDING",
                        fingerprint,
                        XeedId(pending_id),
                        None,
                        PendingStatus.CANCELLED.value,
                        now,
                    )
            updated = connection.execute(
                """SELECT * FROM subscriber_portfolio_pending
                   WHERE tenant_id = ? AND pending_id = ?""",
                (context.tenant_id, pending_id),
            ).fetchone()
        if updated is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        return self._pending_entry(updated)

    def add_if_capacity(
        self,
        context: TrustedSubscriberContext,
        organization: Organization,
        capacity: int,
        request: AddOrganizationRequest,
        now: datetime,
    ) -> tuple[PortfolioEntry | None, bool]:
        if not isinstance(organization, Organization) or capacity < 0:
            raise PortfolioError(PortfolioFailure.ORGANIZATION_INVALID)
        fingerprint = self._fingerprint(
            ["ADD", request.locator, request.display_label, organization.id]
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            prior = connection.execute(
                """SELECT * FROM subscriber_portfolio_commands
                   WHERE tenant_id = ? AND idempotency_key = ?""",
                (context.tenant_id, request.idempotency_key),
            ).fetchone()
            pending = None
            if prior is not None and str(prior["operation"]) == "PENDING":
                pending = connection.execute(
                    """SELECT * FROM subscriber_portfolio_pending
                       WHERE tenant_id = ? AND idempotency_key = ?""",
                    (context.tenant_id, request.idempotency_key),
                ).fetchone()
                if (
                    pending is None
                    or str(pending["locator"]) != request.locator
                    or pending["display_label"] != request.display_label
                    or str(pending["status"]) in ("RESOLVED", "CANCELLED")
                ):
                    raise PortfolioError(PortfolioFailure.IDEMPOTENCY_CONFLICT)
            elif prior is not None:
                self._existing_command(
                    connection,
                    context.tenant_id,
                    request.idempotency_key,
                    "ADD",
                    fingerprint,
                )
                if prior["focus_id"] is None:
                    return None, False
                row = self._get_entry(connection, context.tenant_id, XeedId(str(prior["focus_id"])))
                return (None, False) if row is None else (self._entry(row), False)
            existing = connection.execute(
                """SELECT * FROM subscriber_focuses WHERE tenant_id = ?
                   AND organization_id = ? AND status IN ('ACTIVE','PAUSED')""",
                (context.tenant_id, organization.id),
            ).fetchone()
            if existing is not None:
                entry = self._entry(existing)
                if pending is None:
                    self._record_command(
                        connection,
                        context.tenant_id,
                        request.idempotency_key,
                        "ADD",
                        fingerprint,
                        entry.focus_id,
                        None,
                        AddStatus.ALREADY_PRESENT.value,
                        now,
                    )
                else:
                    self._complete_pending_add(
                        connection,
                        context,
                        request,
                        fingerprint,
                        pending,
                        entry,
                        now,
                        AddStatus.ALREADY_PRESENT.value,
                    )
                return entry, False
            used = int(
                connection.execute(
                    """SELECT COUNT(*) FROM subscriber_focuses
                       WHERE tenant_id = ? AND status IN ('ACTIVE','PAUSED')""",
                    (context.tenant_id,),
                ).fetchone()[0]
            )
            if used >= capacity:
                return None, False
            focus_id = XeedId(f"focus_{uuid.uuid4().hex}")
            connection.execute(
                """INSERT INTO subscriber_focuses(
                       focus_id, tenant_id, organization_id, label, status, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, 'ACTIVE', ?, ?)""",
                (
                    focus_id,
                    context.tenant_id,
                    organization.id,
                    request.display_label,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            if pending is None:
                self._record_command(
                    connection,
                    context.tenant_id,
                    request.idempotency_key,
                    "ADD",
                    fingerprint,
                    focus_id,
                    None,
                    AddStatus.CREATED.value,
                    now,
                )
            else:
                resolved_row = self._get_entry(connection, context.tenant_id, focus_id)
                if resolved_row is None:
                    raise RuntimeError("new Focus was not persisted")
                self._complete_pending_add(
                    connection,
                    context,
                    request,
                    fingerprint,
                    pending,
                    self._entry(resolved_row),
                    now,
                    AddStatus.CREATED.value,
                )
            row = self._get_entry(connection, context.tenant_id, focus_id)
        if row is None:
            raise RuntimeError("new Focus was not persisted")
        return self._entry(row), True

    def staff_add_if_capacity(
        self,
        tenant_id: TenantId,
        actor: str,
        organization: Organization,
        capacity: int,
        request: AddOrganizationRequest,
        now: datetime,
    ) -> tuple[PortfolioEntry | None, bool]:
        """Staff adds a Focus for a tenant it does not belong to (issue #177).

        No subscriber membership is borrowed or created: the caller is an authorized
        Admin operator, recorded as a distinct STAFF_ADD operation whose fingerprint
        carries the actor. The tenant must exist with an active member, capacity is the
        tenant's own entitlement and a full portfolio returns no entry, never a checkout.
        """
        if (
            not isinstance(organization, Organization)
            or capacity < 0
            or not actor.startswith("admin:")
        ):
            raise PortfolioError(PortfolioFailure.ORGANIZATION_INVALID)
        fingerprint = self._fingerprint(
            ["STAFF_ADD", actor, request.locator, request.display_label, organization.id]
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            member = connection.execute(
                """SELECT 1 FROM subscriber_memberships
                   WHERE tenant_id = ? AND revoked_at IS NULL LIMIT 1""",
                (tenant_id,),
            ).fetchone()
            if member is None:
                raise PortfolioError(PortfolioFailure.ACCESS_DENIED)
            prior = self._existing_command(
                connection, tenant_id, request.idempotency_key, "STAFF_ADD", fingerprint
            )
            if prior is not None:
                if prior["focus_id"] is None:
                    return None, False
                row = self._get_entry(connection, tenant_id, XeedId(str(prior["focus_id"])))
                return (None, False) if row is None else (self._entry(row), False)
            existing = connection.execute(
                """SELECT * FROM subscriber_focuses WHERE tenant_id = ?
                   AND organization_id = ? AND status IN ('ACTIVE','PAUSED')""",
                (tenant_id, organization.id),
            ).fetchone()
            if existing is not None:
                entry = self._entry(existing)
                self._record_command(
                    connection,
                    tenant_id,
                    request.idempotency_key,
                    "STAFF_ADD",
                    fingerprint,
                    entry.focus_id,
                    None,
                    AddStatus.ALREADY_PRESENT.value,
                    now,
                )
                return entry, False
            used = int(
                connection.execute(
                    """SELECT COUNT(*) FROM subscriber_focuses
                       WHERE tenant_id = ? AND status IN ('ACTIVE','PAUSED')""",
                    (tenant_id,),
                ).fetchone()[0]
            )
            if used >= capacity:
                return None, False
            focus_id = XeedId(f"focus_{uuid.uuid4().hex}")
            connection.execute(
                """INSERT INTO subscriber_focuses(
                       focus_id, tenant_id, organization_id, label, status, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, 'ACTIVE', ?, ?)""",
                (
                    focus_id,
                    tenant_id,
                    organization.id,
                    request.display_label,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            self._record_command(
                connection,
                tenant_id,
                request.idempotency_key,
                "STAFF_ADD",
                fingerprint,
                focus_id,
                None,
                AddStatus.CREATED.value,
                now,
            )
            row = self._get_entry(connection, tenant_id, focus_id)
            if row is None:
                raise RuntimeError("new Focus was not persisted")
            return self._entry(row), True

    def resolve_waiting_for_capacity(
        self,
        context: TrustedSubscriberContext,
        locator: str,
        focus_id: XeedId,
        now: datetime,
    ) -> int:
        """Resolve this tenant's attention that waited for capacity on the same locator."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            cursor = connection.execute(
                """UPDATE subscriber_portfolio_pending
                   SET status = 'RESOLVED', resolved_focus_id = ?, updated_at = ?
                   WHERE tenant_id = ? AND locator = ?
                     AND status IN ('CAPACITY_UNKNOWN','CAPACITY_PENDING','PURCHASE_AUTHORITY_REQUIRED')""",
                (focus_id, now.isoformat(), context.tenant_id, locator),
            )
            return int(cursor.rowcount)

    @staticmethod
    def _complete_pending_add(
        connection: sqlite3.Connection,
        context: TrustedSubscriberContext,
        request: AddOrganizationRequest,
        fingerprint: str,
        pending: sqlite3.Row,
        entry: PortfolioEntry,
        now: datetime,
        result_status: str,
    ) -> None:
        connection.execute(
            """UPDATE subscriber_portfolio_pending
               SET status = 'RESOLVED', resolved_focus_id = ?, updated_at = ?
               WHERE tenant_id = ? AND idempotency_key = ?""",
            (entry.focus_id, now.isoformat(), context.tenant_id, request.idempotency_key),
        )
        connection.execute(
            """UPDATE subscriber_portfolio_commands
               SET operation = 'ADD', request_fingerprint = ?, focus_id = ?, result_status = ?
               WHERE tenant_id = ? AND idempotency_key = ? AND operation = 'PENDING'""",
            (
                fingerprint,
                entry.focus_id,
                result_status,
                context.tenant_id,
                request.idempotency_key,
            ),
        )

    def transition(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        operation: str,
        idempotency_key: str,
        now: datetime,
        capacity: int | None = None,
    ) -> PortfolioEntry:
        targets = {
            "PAUSE": FocusStatus.PAUSED,
            "RESUME": FocusStatus.ACTIVE,
            "REMOVE": FocusStatus.REMOVED,
        }
        target = targets.get(operation)
        if target is None or not idempotency_key.strip():
            raise PortfolioError(PortfolioFailure.INVALID_COMMAND)
        fingerprint = self._fingerprint([operation, focus_id])
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            prior = self._existing_command(
                connection, context.tenant_id, idempotency_key, operation, fingerprint
            )
            if prior is not None:
                row = self._get_entry(
                    connection,
                    context.tenant_id,
                    focus_id,
                    include_removed=operation == "REMOVE",
                )
                if row is None:
                    raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
                return self._entry(row)
            row = self._get_entry(
                connection,
                context.tenant_id,
                focus_id,
                include_removed=operation == "REMOVE",
            )
            if row is None:
                raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
            current = FocusStatus(str(row["status"]))
            allowed = {
                "PAUSE": current is FocusStatus.ACTIVE,
                "RESUME": current is FocusStatus.PAUSED,
                "REMOVE": current is not FocusStatus.REMOVED,
            }[operation]
            if not allowed:
                if current is target:
                    return self._entry(row)
                raise PortfolioError(PortfolioFailure.INVALID_TRANSITION)
            if operation == "RESUME":
                if capacity is None:
                    raise PortfolioError(PortfolioFailure.CAPACITY_EXCEEDED)
                used = int(
                    connection.execute(
                        """SELECT COUNT(*) FROM subscriber_focuses
                           WHERE tenant_id = ? AND status IN ('ACTIVE','PAUSED')""",
                        (context.tenant_id,),
                    ).fetchone()[0]
                )
                if used > capacity:
                    raise PortfolioError(PortfolioFailure.CAPACITY_EXCEEDED)
            connection.execute(
                """UPDATE subscriber_focuses SET status = ?, updated_at = ?
                   WHERE tenant_id = ? AND focus_id = ?""",
                (target.value, now.isoformat(), context.tenant_id, focus_id),
            )
            self._record_command(
                connection,
                context.tenant_id,
                idempotency_key,
                operation,
                fingerprint,
                focus_id,
                None,
                target.value,
                now,
            )
            updated = self._get_entry(
                connection,
                context.tenant_id,
                focus_id,
                include_removed=operation == "REMOVE",
            )
        if updated is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        return self._entry(updated)

    def replace_organization(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        organization_id: OrganizationId,
        idempotency_key: str,
        now: datetime,
    ) -> tuple[PortfolioEntry, OrganizationId, bool]:
        fingerprint = self._fingerprint(["REPLACE", focus_id, organization_id])
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._require_membership(connection, context)
            prior = self._existing_command(
                connection, context.tenant_id, idempotency_key, "REPLACE", fingerprint
            )
            if prior is not None:
                row = self._get_entry(connection, context.tenant_id, focus_id)
                if row is None:
                    raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
                return (
                    self._entry(row),
                    OrganizationId(str(prior["previous_organization_id"])),
                    True,
                )
            row = self._get_entry(connection, context.tenant_id, focus_id)
            if row is None:
                raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
            previous = OrganizationId(str(row["organization_id"]))
            if previous == organization_id:
                return self._entry(row), previous, False
            duplicate = connection.execute(
                """SELECT 1 FROM subscriber_focuses WHERE tenant_id = ?
                   AND organization_id = ? AND status IN ('ACTIVE','PAUSED')""",
                (context.tenant_id, organization_id),
            ).fetchone()
            if duplicate is not None:
                raise PortfolioError(PortfolioFailure.IDEMPOTENCY_CONFLICT)
            connection.execute(
                """UPDATE subscriber_focuses SET organization_id = ?, updated_at = ?
                   WHERE tenant_id = ? AND focus_id = ?""",
                (organization_id, now.isoformat(), context.tenant_id, focus_id),
            )
            self._record_command(
                connection,
                context.tenant_id,
                idempotency_key,
                "REPLACE",
                fingerprint,
                focus_id,
                previous,
                "REPLACED",
                now,
            )
            updated = self._get_entry(connection, context.tenant_id, focus_id)
        if updated is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        return self._entry(updated), previous, False


__all__ = ["SqliteSubscriberPortfolioStore"]
