"""AO-10 private billing facts and Stripe-normalized contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

BillingEventId = NewType("BillingEventId", str)
ExternalCustomerId = NewType("ExternalCustomerId", str)
ExternalSubscriptionId = NewType("ExternalSubscriptionId", str)


class BillingProvider(StrEnum):
    STRIPE = "STRIPE"


class BillingSubscriptionState(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"


class BillingPaymentState(StrEnum):
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class BillingEventKind(StrEnum):
    MAPPING_REGISTERED = "MAPPING_REGISTERED"
    SUBSCRIPTION_SYNCED = "SUBSCRIPTION_SYNCED"
    INVOICE_PAID = "INVOICE_PAID"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    REFUND_RECORDED = "REFUND_RECORDED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"


@dataclass(frozen=True, slots=True)
class BillingAuthorityGrant:
    provider: BillingProvider
    integration_id: str
    provider_event_id: str
    verified_at: datetime

    def __post_init__(self) -> None:
        _text(self.integration_id, "integration_id")
        _text(self.provider_event_id, "provider_event_id")
        _aware(self.verified_at, "verified_at")


def _text(value: str, name: str, maximum: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} is required and must be at most {maximum} characters")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class BillingQuantities:
    xeed_capacity: int
    base_quantity: int
    additional_xeed_quantity: int

    def __post_init__(self) -> None:
        if self.xeed_capacity < 1:
            raise ValueError("Xeed capacity must be positive")
        if self.base_quantity != 1:
            raise ValueError("self-service billing requires exactly one base quantity")
        if self.additional_xeed_quantity != max(0, self.xeed_capacity - 1):
            raise ValueError("additional Xeed quantity must derive only from Xeed capacity")


def quantities_for_xeed_capacity(xeed_capacity: int) -> BillingQuantities:
    return BillingQuantities(
        xeed_capacity=xeed_capacity,
        base_quantity=1,
        additional_xeed_quantity=max(0, xeed_capacity - 1),
    )


@dataclass(frozen=True, slots=True)
class BillingMapping:
    account_id: str
    provider: BillingProvider
    external_customer_id: ExternalCustomerId
    external_subscription_id: ExternalSubscriptionId
    base_price_ref: str
    additional_xeed_price_ref: str
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.account_id, "account_id"),
            (self.external_customer_id, "external_customer_id"),
            (self.external_subscription_id, "external_subscription_id"),
            (self.base_price_ref, "base_price_ref"),
            (self.additional_xeed_price_ref, "additional_xeed_price_ref"),
        ):
            _text(str(value), name)
        _aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class BillingEvent:
    event_id: BillingEventId
    provider: BillingProvider
    provider_event_type: str
    provider_created_at: datetime
    recorded_at: datetime
    external_object_id: str
    account_id: str
    kind: BillingEventKind
    subscription_state: BillingSubscriptionState | None = None
    payment_state: BillingPaymentState | None = None
    xeed_capacity: int | None = None
    amount_minor: int | None = None
    currency: str | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.event_id, "event_id"),
            (self.provider_event_type, "provider_event_type"),
            (self.external_object_id, "external_object_id"),
            (self.account_id, "account_id"),
        ):
            _text(str(value), name)
        _aware(self.provider_created_at, "provider_created_at")
        _aware(self.recorded_at, "recorded_at")
        if self.recorded_at < self.provider_created_at:
            raise ValueError("billing record cannot be recorded before provider event")
        if self.xeed_capacity is not None and self.xeed_capacity < 1:
            raise ValueError("billing Xeed capacity must be positive")
        if self.amount_minor is not None and self.amount_minor < 0:
            raise ValueError("billing amount cannot be negative")
        if self.currency is not None:
            if len(self.currency) != 3 or not self.currency.isalpha():
                raise ValueError("currency must be a three-letter code")
            object.__setattr__(self, "currency", self.currency.upper())
        if self.source_ref is not None:
            _text(self.source_ref, "source_ref", 200)


@dataclass(frozen=True, slots=True)
class BillingSnapshot:
    account_id: str
    mapping: BillingMapping
    subscription_state: BillingSubscriptionState
    payment_state: BillingPaymentState
    xeed_capacity: int
    amount_minor: int | None
    currency: str | None
    source_event_id: BillingEventId | None
    provider_created_at: datetime | None

    def __post_init__(self) -> None:
        _text(self.account_id, "account_id")
        if self.mapping.account_id != self.account_id:
            raise ValueError("billing snapshot mapping/account mismatch")
        if self.xeed_capacity < 1:
            raise ValueError("billing snapshot Xeed capacity must be positive")
