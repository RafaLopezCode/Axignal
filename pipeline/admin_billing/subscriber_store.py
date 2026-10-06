"""Durable SQLite store isolated from AO-10 Admin billing records."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionCapacityValidation,
    SubscriptionLifecycle,
)
from application.admin_billing.subscriber_checkout import (
    AttemptKind,
    AttemptStatus,
    BillingProjection,
    PurchaseAttempt,
)
from application.subscriber_identity.runtime import PurchaseScopeProvisioningReceipt
from domain.admin_billing.checkout_binding import BindingReason, BindingStatus
from domain.identity import PrincipalId, TenantId


class SubscriberStoreConflict(ValueError):
    """An idempotent request conflicts with previously durable state."""


class SqliteSubscriberBillingStore:
    """SQLite persistence for subscriber attempts, projections and inbox metadata.

    Raw webhook bodies, signatures, secret values, payment credentials and
    provider URLs are never stored by this class.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS subscriber_purchase_attempts (
                    intent_ref TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    request_ref TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    desired_total INTEGER NOT NULL,
                    subscription_ref TEXT,
                    checkout_session_ref TEXT,
                    request_fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(tenant_id, request_ref)
                );
                CREATE INDEX IF NOT EXISTS idx_subscriber_attempt_subscription
                    ON subscriber_purchase_attempts(tenant_id, subscription_ref, status);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_one_open_initial_purchase
                    ON subscriber_purchase_attempts(tenant_id)
                    WHERE kind = 'INITIAL'
                    AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE');
                CREATE UNIQUE INDEX IF NOT EXISTS idx_one_open_capacity_change
                    ON subscriber_purchase_attempts(tenant_id, subscription_ref)
                    WHERE kind = 'CAPACITY_CHANGE'
                    AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE');
                CREATE TABLE IF NOT EXISTS subscriber_billing_projection (
                    tenant_id TEXT PRIMARY KEY,
                    provider_state_at TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subscriber_purchase_scope_owners (
                    tenant_id TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL,
                    registration_key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subscriber_webhook_inbox (
                    event_ref TEXT PRIMARY KEY,
                    payload_fingerprint TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    provider_created_at TEXT NOT NULL,
                    received_at TEXT NOT NULL,
                    environment_ref TEXT NOT NULL,
                    account_ref TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    safe_refs_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subscriber_retry_dlq (
                    operation_ref TEXT PRIMARY KEY,
                    next_attempt_at TEXT,
                    attempt_count INTEGER NOT NULL,
                    disposition TEXT NOT NULL,
                    failure_code TEXT NOT NULL,
                    safe_refs_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS subscriber_webhook_conflicts (
                    event_ref TEXT NOT NULL,
                    prior_fingerprint TEXT NOT NULL,
                    conflicting_fingerprint TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    PRIMARY KEY(event_ref, conflicting_fingerprint)
                );
                """
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(subscriber_purchase_attempts)")
            }
            if "checkout_session_ref" not in columns:
                connection.execute(
                    "ALTER TABLE subscriber_purchase_attempts ADD COLUMN checkout_session_ref TEXT"
                )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriber_attempt_session
                   ON subscriber_purchase_attempts(checkout_session_ref)
                   WHERE checkout_session_ref IS NOT NULL"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @staticmethod
    def _attempt_fingerprint(attempt: PurchaseAttempt) -> str:
        payload = {
            "tenant_id": str(attempt.tenant_id),
            "principal_id": str(attempt.principal_id),
            "request_ref": attempt.request_ref,
            "kind": attempt.kind.value,
            "desired_total": attempt.desired_total,
            "catalogue_ref": attempt.catalogue_ref,
            "catalogue_version": attempt.catalogue_version,
            "environment_ref": attempt.environment_ref,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _attempt_data(attempt: PurchaseAttempt) -> dict[str, object]:
        payload = asdict(attempt)
        payload["tenant_id"] = str(attempt.tenant_id)
        payload["principal_id"] = str(attempt.principal_id)
        payload["kind"] = attempt.kind.value
        payload["status"] = attempt.status.value
        payload["authorized_at"] = attempt.authorized_at.isoformat()
        return payload

    @staticmethod
    def _attempt_payload(attempt: PurchaseAttempt) -> str:
        return json.dumps(
            SqliteSubscriberBillingStore._attempt_data(attempt),
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _attempt_from_row(row: sqlite3.Row) -> PurchaseAttempt:
        payload = json.loads(str(row["payload_json"]))
        payload["tenant_id"] = TenantId(payload["tenant_id"])
        payload["principal_id"] = PrincipalId(payload["principal_id"])
        payload["kind"] = AttemptKind(payload["kind"])
        payload["status"] = AttemptStatus(payload["status"])
        payload["authorized_at"] = datetime.fromisoformat(payload["authorized_at"])
        return PurchaseAttempt(**payload)

    def get_attempt(self, tenant_id: TenantId, request_ref: str) -> PurchaseAttempt | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE tenant_id = ? AND request_ref = ?",
                (str(tenant_id), request_ref),
            ).fetchone()
        return None if row is None else self._attempt_from_row(row)

    def get_attempt_by_intent(self, intent_ref: str) -> PurchaseAttempt | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE intent_ref = ?",
                (intent_ref,),
            ).fetchone()
        return None if row is None else self._attempt_from_row(row)

    def ensure_initial_purchase_scope(
        self,
        principal_id: PrincipalId,
        initial_tenant_id: TenantId,
        registration_key: str,
    ) -> PurchaseScopeProvisioningReceipt:
        if not registration_key.strip() or len(registration_key) > 300:
            raise ValueError("registration key must be bounded non-empty text")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                "SELECT principal_id, registration_key FROM subscriber_purchase_scope_owners WHERE tenant_id = ?",
                (str(initial_tenant_id),),
            ).fetchone()
            if prior is not None:
                if (
                    str(prior["principal_id"]) != str(principal_id)
                    or str(prior["registration_key"]) != registration_key
                ):
                    raise SubscriberStoreConflict("Tenant purchase owner is already provisioned")
                return PurchaseScopeProvisioningReceipt(
                    principal_id, initial_tenant_id, registration_key, True
                )
            collision = connection.execute(
                "SELECT tenant_id, principal_id FROM subscriber_purchase_scope_owners WHERE registration_key = ?",
                (registration_key,),
            ).fetchone()
            if collision is not None:
                if str(collision["tenant_id"]) == str(initial_tenant_id) and str(
                    collision["principal_id"]
                ) == str(principal_id):
                    return PurchaseScopeProvisioningReceipt(
                        principal_id, initial_tenant_id, registration_key, True
                    )
                raise SubscriberStoreConflict("registration key is already bound to another scope")
            connection.execute(
                "INSERT INTO subscriber_purchase_scope_owners(tenant_id, principal_id, registration_key, created_at) VALUES (?, ?, ?, ?)",
                (
                    str(initial_tenant_id),
                    str(principal_id),
                    registration_key,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return PurchaseScopeProvisioningReceipt(
            principal_id, initial_tenant_id, registration_key, True
        )

    def is_purchase_owner(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT principal_id FROM subscriber_purchase_scope_owners WHERE tenant_id = ?",
                (str(tenant_id),),
            ).fetchone()
        return None if row is None else str(row["principal_id"]) == str(principal_id)

    def get_attempt_by_session(self, checkout_session_ref: str) -> PurchaseAttempt | None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE checkout_session_ref = ? LIMIT 2",
                (checkout_session_ref,),
            ).fetchall()
        if len(rows) > 1:
            raise SubscriberStoreConflict("Checkout Session is bound to multiple attempts")
        return None if not rows else self._attempt_from_row(rows[0])

    def get_pending_attempt_by_subscription(self, subscription_ref: str) -> PurchaseAttempt | None:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM subscriber_purchase_attempts
                   WHERE subscription_ref = ?
                     AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                   LIMIT 2""",
                (subscription_ref,),
            ).fetchall()
        if len(rows) > 1:
            raise SubscriberStoreConflict("subscription has multiple pending purchase attempts")
        return None if not rows else self._attempt_from_row(rows[0])

    def get_pending_capacity_change(
        self, tenant_id: TenantId, subscription_ref: str
    ) -> PurchaseAttempt | None:
        with self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM subscriber_purchase_attempts
                   WHERE tenant_id = ? AND subscription_ref = ? AND kind = 'CAPACITY_CHANGE'
                     AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                   ORDER BY rowid LIMIT 1""",
                (str(tenant_id), subscription_ref),
            ).fetchone()
        return None if row is None else self._attempt_from_row(row)

    def list_pending_attempts(
        self, tenant_id: TenantId, *, limit: int = 20
    ) -> tuple[PurchaseAttempt, ...]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("pending attempt page size must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM subscriber_purchase_attempts
                   WHERE tenant_id = ? AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                   ORDER BY rowid LIMIT ?""",
                (str(tenant_id), limit),
            ).fetchall()
        return tuple(self._attempt_from_row(row) for row in rows)

    def list_all_pending_attempts(self, *, limit: int = 20) -> tuple[PurchaseAttempt, ...]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("pending attempt page size must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM subscriber_purchase_attempts
                   WHERE status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                   ORDER BY rowid LIMIT ?""",
                (limit,),
            ).fetchall()
        return tuple(self._attempt_from_row(row) for row in rows)

    def prepare_attempt(self, attempt: PurchaseAttempt) -> PurchaseAttempt:
        fingerprint = self._attempt_fingerprint(attempt)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE tenant_id = ? AND request_ref = ?",
                (str(attempt.tenant_id), attempt.request_ref),
            ).fetchone()
            if prior is not None:
                if str(prior["request_fingerprint"]) != fingerprint:
                    raise SubscriberStoreConflict(
                        "request reference already has different purchase intent"
                    )
                return self._attempt_from_row(prior)
            if attempt.kind is AttemptKind.CAPACITY_CHANGE:
                pending = connection.execute(
                    """SELECT * FROM subscriber_purchase_attempts
                       WHERE tenant_id = ? AND subscription_ref = ? AND kind = 'CAPACITY_CHANGE'
                         AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                       ORDER BY rowid LIMIT 1""",
                    (str(attempt.tenant_id), attempt.subscription_ref),
                ).fetchone()
                if pending is not None:
                    existing = self._attempt_from_row(pending)
                    if existing.desired_total == attempt.desired_total:
                        return existing
                    raise SubscriberStoreConflict("a different capacity change is already pending")
            elif attempt.kind is AttemptKind.INITIAL:
                pending = connection.execute(
                    """SELECT * FROM subscriber_purchase_attempts
                       WHERE tenant_id = ? AND kind = 'INITIAL'
                         AND status IN ('PREPARED', 'PROVIDER_PENDING', 'PENDING_PURCHASE')
                       ORDER BY rowid LIMIT 1""",
                    (str(attempt.tenant_id),),
                ).fetchone()
                if pending is not None:
                    existing = self._attempt_from_row(pending)
                    if existing.desired_total == attempt.desired_total:
                        return existing
                    raise SubscriberStoreConflict("a different initial purchase is already pending")
            try:
                connection.execute(
                    """INSERT INTO subscriber_purchase_attempts(
                       intent_ref, tenant_id, principal_id, request_ref, kind, status,
                       desired_total, subscription_ref, checkout_session_ref, request_fingerprint, payload_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        attempt.intent_ref,
                        str(attempt.tenant_id),
                        str(attempt.principal_id),
                        attempt.request_ref,
                        attempt.kind.value,
                        attempt.status.value,
                        attempt.desired_total,
                        attempt.subscription_ref,
                        attempt.checkout_session_ref,
                        fingerprint,
                        self._attempt_payload(attempt),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise SubscriberStoreConflict("concurrent subscriber purchase conflict") from exc
        return attempt

    def _record_attempt(self, attempt: PurchaseAttempt) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE intent_ref = ?",
                (attempt.intent_ref,),
            ).fetchone()
            if row is None:
                raise SubscriberStoreConflict("purchase intent was not durably prepared")
            prior = self._attempt_from_row(row)
            if (
                prior.tenant_id != attempt.tenant_id
                or prior.request_ref != attempt.request_ref
                or prior.kind is not attempt.kind
                or prior.desired_total != attempt.desired_total
                or prior.idempotency_key != attempt.idempotency_key
            ):
                raise SubscriberStoreConflict(
                    "provider result conflicts with immutable purchase intent"
                )
            connection.execute(
                """UPDATE subscriber_purchase_attempts
                   SET status = ?, subscription_ref = ?, checkout_session_ref = ?, payload_json = ?
                   WHERE intent_ref = ?""",
                (
                    attempt.status.value,
                    attempt.subscription_ref,
                    attempt.checkout_session_ref,
                    self._attempt_payload(attempt),
                    attempt.intent_ref,
                ),
            )

    def record_initial_session(self, attempt: PurchaseAttempt) -> None:
        if attempt.kind is not AttemptKind.INITIAL or not attempt.checkout_session_ref:
            raise ValueError("initial session result requires initial Checkout references")
        self._record_attempt(attempt)

    def record_capacity_update(self, attempt: PurchaseAttempt) -> None:
        if attempt.kind is not AttemptKind.CAPACITY_CHANGE or not attempt.subscription_ref:
            raise ValueError("capacity update result requires existing subscription reference")
        self._record_attempt(attempt)

    def record_reconciled_purchase(
        self, attempt: PurchaseAttempt, projection: BillingProjection
    ) -> None:
        if attempt.status is not AttemptStatus.COMPLETE:
            raise ValueError("reconciled purchase must be complete")
        if attempt.tenant_id != projection.tenant_id:
            raise SubscriberStoreConflict("attempt and billing projection scope differ")
        serialized_projection = self._projection_payload(projection)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM subscriber_purchase_attempts WHERE intent_ref = ?",
                (attempt.intent_ref,),
            ).fetchone()
            if row is None:
                raise SubscriberStoreConflict("purchase intent was not durably prepared")
            prior = self._attempt_from_row(row)
            if prior.tenant_id != attempt.tenant_id or prior.request_ref != attempt.request_ref:
                raise SubscriberStoreConflict("reconciled purchase scope changed")
            if prior.status is AttemptStatus.COMPLETE:
                return
            if prior.status not in (
                AttemptStatus.PREPARED,
                AttemptStatus.PROVIDER_PENDING,
                AttemptStatus.PENDING_PURCHASE,
            ):
                raise SubscriberStoreConflict("purchase attempt is no longer reconcilable")
            existing = connection.execute(
                "SELECT provider_state_at, payload_json FROM subscriber_billing_projection WHERE tenant_id = ?",
                (str(projection.tenant_id),),
            ).fetchone()
            if existing is not None and existing["provider_state_at"] is not None:
                previous_at = datetime.fromisoformat(str(existing["provider_state_at"]))
                if (
                    projection.provider_state_at is None
                    or projection.provider_state_at < previous_at
                ):
                    raise SubscriberStoreConflict(
                        "stale billing projection cannot replace newer state"
                    )
                if (
                    projection.provider_state_at == previous_at
                    and str(existing["payload_json"]) != serialized_projection
                ):
                    prior_payload = json.loads(str(existing["payload_json"]))
                    prior_binding = prior_payload.get("binding")
                    fail_closed_unknown = (
                        projection.provider_state_ref == "provider-refresh:unknown"
                        and projection.effective_capacity is None
                        and projection.payment_state is PaymentState.UNKNOWN
                        and projection.binding is not None
                        and projection.binding.status is BindingStatus.VERIFIED
                        and isinstance(prior_binding, dict)
                        and prior_binding.get("status") == BindingStatus.VERIFIED.value
                        and projection.binding.evidence_fingerprint
                        == prior_binding.get("evidence_fingerprint")
                        and projection.verified_invoice_ref
                        == prior_payload.get("verified_invoice_ref")
                        and projection.customer_ref == prior_payload.get("customer_ref")
                        and projection.subscription_ref == prior_payload.get("subscription_ref")
                        and projection.environment_ref == prior_payload.get("environment_ref")
                    )
                    recovery = (
                        prior_payload.get("provider_state_ref") == "provider-refresh:unknown"
                        and prior_payload.get("effective_capacity") is None
                        and prior_payload.get("payment_state") == PaymentState.UNKNOWN.value
                        and isinstance(prior_binding, dict)
                        and prior_binding.get("status") == BindingStatus.VERIFIED.value
                        and projection.effective_capacity == prior_binding.get("effective_capacity")
                        and projection.payment_state is PaymentState.VERIFIED
                        and projection.verified_invoice_ref is not None
                        and projection.binding is not None
                        and projection.binding.status is BindingStatus.VERIFIED
                        and projection.verified_invoice_ref
                        == prior_payload.get("verified_invoice_ref")
                        and projection.customer_ref == prior_payload.get("customer_ref")
                        and projection.subscription_ref == prior_payload.get("subscription_ref")
                        and projection.environment_ref == prior_payload.get("environment_ref")
                    )
                    if not fail_closed_unknown and not recovery:
                        raise SubscriberStoreConflict(
                            "equal provider state time requires reconciliation"
                        )
            connection.execute(
                """INSERT INTO subscriber_billing_projection(tenant_id, provider_state_at, payload_json)
                   VALUES (?, ?, ?) ON CONFLICT(tenant_id) DO UPDATE SET
                   provider_state_at=excluded.provider_state_at, payload_json=excluded.payload_json""",
                (
                    str(projection.tenant_id),
                    None
                    if projection.provider_state_at is None
                    else projection.provider_state_at.isoformat(),
                    serialized_projection,
                ),
            )
            connection.execute(
                """UPDATE subscriber_purchase_attempts
                   SET status = ?, subscription_ref = ?, checkout_session_ref = ?, payload_json = ?
                   WHERE intent_ref = ?""",
                (
                    attempt.status.value,
                    attempt.subscription_ref,
                    attempt.checkout_session_ref,
                    self._attempt_payload(attempt),
                    attempt.intent_ref,
                ),
            )

    def get_billing_projection(self, tenant_id: TenantId) -> BillingProjection | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM subscriber_billing_projection WHERE tenant_id = ?",
                (str(tenant_id),),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(str(row["payload_json"]))
        binding_data = payload.pop("binding")
        binding = None
        if binding_data is not None:
            binding_data["status"] = BindingStatus(binding_data["status"])
            binding_data["reason"] = BindingReason(binding_data["reason"])
            if binding_data["provider_state_at"] is not None:
                binding_data["provider_state_at"] = datetime.fromisoformat(
                    binding_data["provider_state_at"]
                )
            binding = SubscriptionCapacityValidation(**binding_data)
        payload["tenant_id"] = TenantId(payload["tenant_id"])
        payload["payment_state"] = PaymentState(payload["payment_state"])
        payload["lifecycle"] = SubscriptionLifecycle(payload["lifecycle"])
        for name in ("provider_state_at", "paid_through"):
            if payload[name] is not None:
                payload[name] = datetime.fromisoformat(payload[name])
        return BillingProjection(binding=binding, **payload)

    def commit_billing_projection(self, projection: BillingProjection) -> None:
        serialized = self._projection_payload(projection)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                "SELECT provider_state_at, payload_json FROM subscriber_billing_projection WHERE tenant_id = ?",
                (str(projection.tenant_id),),
            ).fetchone()
            if prior is not None and prior["provider_state_at"] is not None:
                prior_at = datetime.fromisoformat(str(prior["provider_state_at"]))
                if projection.provider_state_at is None or projection.provider_state_at < prior_at:
                    raise SubscriberStoreConflict(
                        "stale billing projection cannot replace newer state"
                    )
                if projection.provider_state_at == prior_at:
                    if str(prior["payload_json"]) == serialized:
                        return
                    prior_payload = json.loads(str(prior["payload_json"]))
                    prior_binding = prior_payload.get("binding")
                    fail_closed_unknown = (
                        projection.provider_state_ref == "provider-refresh:unknown"
                        and projection.effective_capacity is None
                        and projection.payment_state is PaymentState.UNKNOWN
                        and projection.binding is not None
                        and projection.binding.status is BindingStatus.VERIFIED
                        and isinstance(prior_binding, dict)
                        and prior_binding.get("status") == BindingStatus.VERIFIED.value
                        and projection.binding.evidence_fingerprint
                        == prior_binding.get("evidence_fingerprint")
                        and projection.verified_invoice_ref
                        == prior_payload.get("verified_invoice_ref")
                        and projection.customer_ref == prior_payload.get("customer_ref")
                        and projection.subscription_ref == prior_payload.get("subscription_ref")
                        and projection.environment_ref == prior_payload.get("environment_ref")
                    )
                    recovery = (
                        prior_payload.get("provider_state_ref") == "provider-refresh:unknown"
                        and prior_payload.get("effective_capacity") is None
                        and prior_payload.get("payment_state") == PaymentState.UNKNOWN.value
                        and isinstance(prior_binding, dict)
                        and prior_binding.get("status") == BindingStatus.VERIFIED.value
                        and projection.effective_capacity == prior_binding.get("effective_capacity")
                        and projection.payment_state is PaymentState.VERIFIED
                        and projection.verified_invoice_ref is not None
                        and projection.binding is not None
                        and projection.binding.status is BindingStatus.VERIFIED
                        and projection.verified_invoice_ref
                        == prior_payload.get("verified_invoice_ref")
                        and projection.customer_ref == prior_payload.get("customer_ref")
                        and projection.subscription_ref == prior_payload.get("subscription_ref")
                        and projection.environment_ref == prior_payload.get("environment_ref")
                    )
                    if (
                        not fail_closed_unknown
                        and not recovery
                        and (
                            projection.effective_capacity is not None
                            or projection.payment_state is PaymentState.VERIFIED
                        )
                    ):
                        raise SubscriberStoreConflict(
                            "equal provider state time cannot raise billing capacity"
                        )
            connection.execute(
                """INSERT INTO subscriber_billing_projection(tenant_id, provider_state_at, payload_json)
                   VALUES (?, ?, ?)
                   ON CONFLICT(tenant_id) DO UPDATE SET
                     provider_state_at=excluded.provider_state_at,
                     payload_json=excluded.payload_json""",
                (
                    str(projection.tenant_id),
                    None
                    if projection.provider_state_at is None
                    else projection.provider_state_at.isoformat(),
                    serialized,
                ),
            )

    def mark_projection_unknown(self, tenant_id: TenantId) -> None:
        projection = self.get_billing_projection(tenant_id)
        if projection is None:
            return
        unknown = BillingProjection(
            tenant_id=projection.tenant_id,
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            checkout_session_ref=projection.checkout_session_ref,
            environment_ref=projection.environment_ref,
            additional_item_ref=projection.additional_item_ref,
            effective_capacity=None,
            payment_state=PaymentState.UNKNOWN,
            lifecycle=SubscriptionLifecycle.UNKNOWN,
            binding=projection.binding,
            provider_state_ref="provider-refresh:unknown",
            provider_state_at=projection.provider_state_at,
            paid_through=projection.paid_through,
            verified_invoice_ref=projection.verified_invoice_ref,
        )
        self.commit_billing_projection(unknown)

    @staticmethod
    def _projection_payload(projection: BillingProjection) -> str:
        payload = asdict(projection)
        payload["tenant_id"] = str(projection.tenant_id)
        payload["payment_state"] = projection.payment_state.value
        payload["lifecycle"] = projection.lifecycle.value
        for name in ("provider_state_at", "paid_through"):
            value = getattr(projection, name)
            payload[name] = None if value is None else value.isoformat()
        if projection.binding is not None:
            payload["binding"] = asdict(projection.binding)
            payload["binding"]["status"] = projection.binding.status.value
            payload["binding"]["reason"] = projection.binding.reason.value
            if projection.binding.provider_state_at is not None:
                payload["binding"]["provider_state_at"] = (
                    projection.binding.provider_state_at.isoformat()
                )
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def accept_webhook(
        self,
        *,
        event_ref: str,
        payload_fingerprint: str,
        event_type: str,
        provider_created_at: datetime,
        received_at: datetime,
        environment_ref: str,
        account_ref: str,
        safe_refs: dict[str, str],
    ) -> str:
        """Durably accept event metadata; return STORED, EXACT_REPLAY or CONFLICT."""
        refs_json = json.dumps(safe_refs, sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prior = connection.execute(
                "SELECT payload_fingerprint FROM subscriber_webhook_inbox WHERE event_ref = ?",
                (event_ref,),
            ).fetchone()
            if prior is not None:
                if prior["payload_fingerprint"] == payload_fingerprint:
                    return "EXACT_REPLAY"
                connection.execute(
                    """INSERT OR IGNORE INTO subscriber_webhook_conflicts(
                       event_ref, prior_fingerprint, conflicting_fingerprint, observed_at
                       ) VALUES (?, ?, ?, ?)""",
                    (
                        event_ref,
                        str(prior["payload_fingerprint"]),
                        payload_fingerprint,
                        received_at.isoformat(),
                    ),
                )
                return "QUARANTINED_CONFLICT"
            connection.execute(
                """INSERT INTO subscriber_webhook_inbox(
                    event_ref, payload_fingerprint, event_type, provider_created_at,
                    received_at, environment_ref, account_ref, disposition, safe_refs_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'RECEIVED', ?)""",
                (
                    event_ref,
                    payload_fingerprint,
                    event_type,
                    provider_created_at.isoformat(),
                    received_at.isoformat(),
                    environment_ref,
                    account_ref,
                    refs_json,
                ),
            )
        return "STORED"

    def enqueue_retry(
        self,
        *,
        operation_ref: str,
        next_attempt_at: datetime | None,
        attempt_count: int,
        disposition: str,
        failure_code: str,
        safe_refs: dict[str, str],
    ) -> None:
        if attempt_count < 0:
            raise ValueError("attempt_count cannot be negative")
        refs_json = json.dumps(safe_refs, sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO subscriber_retry_dlq(
                   operation_ref, next_attempt_at, attempt_count, disposition,
                   failure_code, safe_refs_json) VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(operation_ref) DO UPDATE SET
                     next_attempt_at=excluded.next_attempt_at,
                     attempt_count=excluded.attempt_count,
                     disposition=excluded.disposition,
                     failure_code=excluded.failure_code,
                     safe_refs_json=excluded.safe_refs_json""",
                (
                    operation_ref,
                    None if next_attempt_at is None else next_attempt_at.isoformat(),
                    attempt_count,
                    disposition,
                    failure_code,
                    refs_json,
                ),
            )

    def retry_attempt_count(self, operation_ref: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT attempt_count FROM subscriber_retry_dlq WHERE operation_ref = ?",
                (operation_ref,),
            ).fetchone()
        return 0 if row is None else int(row["attempt_count"])

    def pending_retries(self, now: datetime, *, limit: int = 20) -> tuple[dict[str, object], ...]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("retry page size must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT operation_ref, attempt_count, failure_code, safe_refs_json
                   FROM subscriber_retry_dlq
                   WHERE disposition = 'RETRY'
                     AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                   ORDER BY COALESCE(next_attempt_at, '') LIMIT ?""",
                (now.isoformat(), limit),
            ).fetchall()
        return tuple(
            {
                "operation_ref": str(row["operation_ref"]),
                "attempt_count": int(row["attempt_count"]),
                "failure_code": str(row["failure_code"]),
                "safe_refs": json.loads(str(row["safe_refs_json"])),
            }
            for row in rows
        )
