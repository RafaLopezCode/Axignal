"""Replay-safe private billing persistence for AO-10."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_billing import (
    BillingEvent,
    BillingEventId,
    BillingEventKind,
    BillingMapping,
    BillingPaymentState,
    BillingProvider,
    BillingSnapshot,
    BillingSubscriptionState,
    ExternalCustomerId,
    ExternalSubscriptionId,
)


class BillingStoreConflict(ValueError):
    pass


class SqliteAdminBillingStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_billing_mappings (
                    account_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    external_customer_id TEXT NOT NULL UNIQUE,
                    external_subscription_id TEXT NOT NULL UNIQUE,
                    base_price_ref TEXT NOT NULL,
                    additional_xeed_price_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admin_billing_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    provider_event_type TEXT NOT NULL,
                    provider_created_at TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    external_object_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_admin_billing_events_account
                    ON admin_billing_events(account_id, provider_created_at, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def register_mapping(self, mapping: BillingMapping) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_billing_mappings WHERE account_id = ?",
                (mapping.account_id,),
            ).fetchone()
            expected = (
                mapping.provider.value,
                str(mapping.external_customer_id),
                str(mapping.external_subscription_id),
                mapping.base_price_ref,
                mapping.additional_xeed_price_ref,
                mapping.created_at.isoformat(),
            )
            if row is not None:
                actual = tuple(
                    str(row[key])
                    for key in (
                        "provider",
                        "external_customer_id",
                        "external_subscription_id",
                        "base_price_ref",
                        "additional_xeed_price_ref",
                        "created_at",
                    )
                )
                if actual == expected:
                    return False
                raise BillingStoreConflict("account billing mapping already differs")
            try:
                connection.execute(
                    """
                    INSERT INTO admin_billing_mappings(
                        account_id, provider, external_customer_id,
                        external_subscription_id, base_price_ref,
                        additional_xeed_price_ref, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (mapping.account_id, *expected),
                )
            except sqlite3.IntegrityError as exc:
                raise BillingStoreConflict("external billing identity already mapped") from exc
        return True

    def mapping_for_account(self, account_id: str) -> BillingMapping | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_billing_mappings WHERE account_id = ?",
                (account_id,),
            ).fetchone()
        return None if row is None else self._mapping(row)

    def mapping_for_subscription(self, subscription_id: str) -> BillingMapping | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_billing_mappings WHERE external_subscription_id = ?",
                (subscription_id,),
            ).fetchone()
        return None if row is None else self._mapping(row)

    @staticmethod
    def _mapping(row: sqlite3.Row) -> BillingMapping:
        return BillingMapping(
            account_id=str(row["account_id"]),
            provider=BillingProvider(str(row["provider"])),
            external_customer_id=ExternalCustomerId(str(row["external_customer_id"])),
            external_subscription_id=ExternalSubscriptionId(str(row["external_subscription_id"])),
            base_price_ref=str(row["base_price_ref"]),
            additional_xeed_price_ref=str(row["additional_xeed_price_ref"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
        )

    @staticmethod
    def _event_payload(event: BillingEvent) -> str:
        return json.dumps(
            {
                "subscription_state": (
                    None if event.subscription_state is None else event.subscription_state.value
                ),
                "payment_state": (
                    None if event.payment_state is None else event.payment_state.value
                ),
                "xeed_capacity": event.xeed_capacity,
                "amount_minor": event.amount_minor,
                "currency": event.currency,
                "source_ref": event.source_ref,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_event(self, event: BillingEvent) -> bool:
        payload = self._event_payload(event)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT * FROM admin_billing_events WHERE event_id = ?",
                (str(event.event_id),),
            ).fetchone()
            expected = (
                event.provider.value,
                event.provider_event_type,
                event.provider_created_at.isoformat(),
                event.external_object_id,
                event.account_id,
                event.kind.value,
                payload,
            )
            if existing is not None:
                actual = tuple(
                    str(existing[key])
                    for key in (
                        "provider",
                        "provider_event_type",
                        "provider_created_at",
                        "external_object_id",
                        "account_id",
                        "kind",
                        "payload_json",
                    )
                )
                if actual == expected:
                    return False
                raise BillingStoreConflict("billing event id reused with different content")
            connection.execute(
                """
                INSERT INTO admin_billing_events(
                    event_id, provider, provider_event_type, provider_created_at,
                    recorded_at, external_object_id, account_id, kind, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id),
                    event.provider.value,
                    event.provider_event_type,
                    event.provider_created_at.isoformat(),
                    event.recorded_at.isoformat(),
                    event.external_object_id,
                    event.account_id,
                    event.kind.value,
                    payload,
                ),
            )
        return True

    @staticmethod
    def _event(row: sqlite3.Row) -> BillingEvent:
        payload = json.loads(str(row["payload_json"]))
        return BillingEvent(
            event_id=BillingEventId(str(row["event_id"])),
            provider=BillingProvider(str(row["provider"])),
            provider_event_type=str(row["provider_event_type"]),
            provider_created_at=datetime.fromisoformat(str(row["provider_created_at"])),
            recorded_at=datetime.fromisoformat(str(row["recorded_at"])),
            external_object_id=str(row["external_object_id"]),
            account_id=str(row["account_id"]),
            kind=BillingEventKind(str(row["kind"])),
            subscription_state=(
                None
                if payload["subscription_state"] is None
                else BillingSubscriptionState(str(payload["subscription_state"]))
            ),
            payment_state=(
                None
                if payload["payment_state"] is None
                else BillingPaymentState(str(payload["payment_state"]))
            ),
            xeed_capacity=(
                None if payload["xeed_capacity"] is None else int(payload["xeed_capacity"])
            ),
            amount_minor=(
                None if payload["amount_minor"] is None else int(payload["amount_minor"])
            ),
            currency=None if payload["currency"] is None else str(payload["currency"]),
            source_ref=None if payload["source_ref"] is None else str(payload["source_ref"]),
        )

    def events_for_account(self, account_id: str) -> tuple[BillingEvent, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM admin_billing_events
                WHERE account_id = ?
                ORDER BY provider_created_at, sequence
                """,
                (account_id,),
            ).fetchall()
        return tuple(self._event(row) for row in rows)

    def event_by_id(self, event_id: str) -> BillingEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM admin_billing_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return None if row is None else self._event(row)

    def latest_payment_event(self, account_id: str) -> BillingEvent | None:
        events = tuple(
            event
            for event in self.events_for_account(account_id)
            if event.payment_state is not None
        )
        return None if not events else events[-1]

    def latest_capacity_event(self, account_id: str) -> BillingEvent | None:
        events = tuple(
            event
            for event in self.events_for_account(account_id)
            if event.xeed_capacity is not None
        )
        return None if not events else events[-1]

    def latest_subscription_event(self, account_id: str) -> BillingEvent | None:
        events = tuple(
            event
            for event in self.events_for_account(account_id)
            if event.subscription_state is not None
        )
        return None if not events else events[-1]

    def snapshot(self, account_id: str) -> BillingSnapshot | None:
        mapping = self.mapping_for_account(account_id)
        if mapping is None:
            return None
        events = self.events_for_account(account_id)
        subscription_state = BillingSubscriptionState.PENDING
        payment_state = BillingPaymentState.UNKNOWN
        capacity = 1
        amount_minor: int | None = None
        currency: str | None = None
        source_event_id: BillingEventId | None = None
        provider_created_at: datetime | None = None
        for event in events:
            if event.subscription_state is not None:
                subscription_state = event.subscription_state
            if event.payment_state is not None:
                payment_state = event.payment_state
            if event.xeed_capacity is not None:
                capacity = event.xeed_capacity
            if event.amount_minor is not None:
                amount_minor = event.amount_minor
                currency = event.currency
            source_event_id = event.event_id
            provider_created_at = event.provider_created_at
        return BillingSnapshot(
            account_id=account_id,
            mapping=mapping,
            subscription_state=subscription_state,
            payment_state=payment_state,
            xeed_capacity=capacity,
            amount_minor=amount_minor,
            currency=currency,
            source_event_id=source_event_id,
            provider_created_at=provider_created_at,
        )
