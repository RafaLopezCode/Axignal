"""AO-10 billing orchestration: Stripe-owned facts -> AXIGNAL-owned service state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.admin_customer_accounts import AdminCustomerAccountService
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_billing import (
    BillingAuthorityGrant,
    BillingEvent,
    BillingEventKind,
    BillingMapping,
    BillingPaymentState,
    BillingProvider,
    BillingSnapshot,
    BillingSubscriptionState,
    quantities_for_xeed_capacity,
)


class BillingStore(Protocol):
    def register_mapping(self, mapping: BillingMapping) -> bool: ...
    def mapping_for_account(self, account_id: str) -> BillingMapping | None: ...
    def mapping_for_subscription(self, subscription_id: str) -> BillingMapping | None: ...
    def append_event(self, event: BillingEvent) -> bool: ...
    def event_by_id(self, event_id: str) -> BillingEvent | None: ...
    def events_for_account(self, account_id: str) -> tuple[BillingEvent, ...]: ...
    def latest_payment_event(self, account_id: str) -> BillingEvent | None: ...
    def latest_capacity_event(self, account_id: str) -> BillingEvent | None: ...
    def latest_subscription_event(self, account_id: str) -> BillingEvent | None: ...
    def snapshot(self, account_id: str) -> BillingSnapshot | None: ...


def _require_billing_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.BILLING_WRITE not in grant.scopes:
        raise PermissionError("billing operation requires admin:billing:write")


@dataclass(frozen=True, slots=True)
class BillingIngestResult:
    replayed: bool
    account_id: str
    billing_snapshot: BillingSnapshot


@dataclass(frozen=True, slots=True)
class BillingCheckoutResult:
    mapping_created: bool
    account_id: str
    external_subscription_id: str


class AdminBillingService:
    def __init__(
        self,
        store: BillingStore,
        accounts: AdminCustomerAccountService,
    ) -> None:
        self._store = store
        self._accounts = accounts

    def register_mapping(
        self,
        *,
        grant: AdminAuthorizationGrant,
        mapping: BillingMapping,
    ) -> bool:
        _require_billing_write(grant)
        return self._store.register_mapping(mapping)

    def register_verified_checkout(
        self,
        *,
        authority: BillingAuthorityGrant,
        mapping: BillingMapping,
        xeed_capacity: int,
        now: datetime,
    ) -> BillingCheckoutResult:
        if authority.provider is not mapping.provider:
            raise PermissionError("billing authority/provider mismatch")
        created = self._store.register_mapping(mapping)
        self._accounts.link_billing_subscription(
            authority=authority,
            account_id=mapping.account_id,
            subscription_id=str(mapping.external_subscription_id),
            xeed_capacity=xeed_capacity,
            now=now,
            reason="verified Stripe Checkout subscription mapping",
        )
        return BillingCheckoutResult(
            mapping_created=created,
            account_id=mapping.account_id,
            external_subscription_id=str(mapping.external_subscription_id),
        )

    def ingest_verified_event(
        self,
        *,
        authority: BillingAuthorityGrant,
        event: BillingEvent,
        now: datetime,
    ) -> BillingIngestResult:
        if authority.provider is not event.provider:
            raise PermissionError("billing authority/provider mismatch")
        if authority.provider_event_id != str(event.event_id):
            raise PermissionError("billing authority/event mismatch")
        if event.provider is not BillingProvider.STRIPE:
            raise ValueError("AO-10 currently accepts only Stripe billing facts")
        mapping = self._store.mapping_for_account(event.account_id)
        if mapping is None:
            raise LookupError("billing event account has no Stripe mapping")
        if (
            event.kind is not BillingEventKind.MAPPING_REGISTERED
            and event.external_object_id != str(mapping.external_subscription_id)
            and event.kind
            in {
                BillingEventKind.SUBSCRIPTION_SYNCED,
                BillingEventKind.SUBSCRIPTION_CANCELLED,
            }
        ):
            raise ValueError("Stripe subscription event does not match account mapping")

        inserted = self._store.append_event(event)
        if inserted and self._is_current_effect(event):
            self._apply_account_effect(authority=authority, event=event, now=now)
        snapshot = self._store.snapshot(event.account_id)
        if snapshot is None:
            raise RuntimeError("billing snapshot missing after verified event")
        return BillingIngestResult(
            replayed=not inserted,
            account_id=event.account_id,
            billing_snapshot=snapshot,
        )

    def _is_current_effect(self, event: BillingEvent) -> bool:
        checks: list[bool] = []
        if event.payment_state is not None:
            latest = self._store.latest_payment_event(event.account_id)
            checks.append(latest is not None and latest.event_id == event.event_id)
        if event.xeed_capacity is not None:
            latest = self._store.latest_capacity_event(event.account_id)
            checks.append(latest is not None and latest.event_id == event.event_id)
        if event.subscription_state is not None:
            latest = self._store.latest_subscription_event(event.account_id)
            checks.append(latest is not None and latest.event_id == event.event_id)
        return all(checks) if checks else True

    def _apply_account_effect(
        self,
        *,
        authority: BillingAuthorityGrant,
        event: BillingEvent,
        now: datetime,
    ) -> None:
        provider_event_id = str(event.event_id)

        if event.xeed_capacity is not None:
            quantities_for_xeed_capacity(event.xeed_capacity)
            self._accounts.sync_billing_capacity(
                authority=authority,
                account_id=event.account_id,
                provider_event_id=provider_event_id,
                xeed_capacity=event.xeed_capacity,
                now=now,
                reason="verified Stripe subscription quantity",
            )

        if event.payment_state is BillingPaymentState.PAID:
            self._accounts.apply_billing_payment(
                authority=authority,
                account_id=event.account_id,
                provider_event_id=provider_event_id,
                verified=True,
                now=now,
                reason="verified Stripe payment",
            )
        elif event.payment_state in {
            BillingPaymentState.FAILED,
            BillingPaymentState.REFUNDED,
        }:
            self._accounts.apply_billing_payment(
                authority=authority,
                account_id=event.account_id,
                provider_event_id=provider_event_id,
                verified=False,
                now=now,
                reason=f"verified Stripe payment state {event.payment_state.value}",
            )

        if event.subscription_state in {
            BillingSubscriptionState.PAST_DUE,
            BillingSubscriptionState.CANCELLED,
        }:
            self._accounts.apply_billing_payment(
                authority=authority,
                account_id=event.account_id,
                provider_event_id=provider_event_id + ":subscription",
                verified=False,
                now=now,
                reason=f"verified Stripe subscription state {event.subscription_state.value}",
            )
