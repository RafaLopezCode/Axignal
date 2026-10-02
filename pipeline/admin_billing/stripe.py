"""Minimal Stripe boundary for AO-10: signature verification and event normalization.

No Stripe SDK or secret storage lives here. Secret bytes are supplied by the
AO-18 credential boundary at runtime.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from domain.admin_billing import (
    BillingEvent,
    BillingEventId,
    BillingEventKind,
    BillingMapping,
    BillingPaymentState,
    BillingProvider,
    BillingSubscriptionState,
    ExternalCustomerId,
    ExternalSubscriptionId,
)


class StripeWebhookError(ValueError):
    pass


class StripeWebhookDependencyError(StripeWebhookError):
    pass


class StripeMappingReader(Protocol):
    def mapping_for_subscription(self, subscription_id: str) -> BillingMapping | None: ...


@dataclass(frozen=True, slots=True)
class VerifiedStripeEvent:
    event_id: str
    event_type: str
    created_at: datetime
    payload: dict[str, Any]


class StripeWebhookVerifier:
    def __init__(self, signing_secret: bytes, *, tolerance_seconds: int = 300) -> None:
        if not signing_secret:
            raise ValueError("Stripe signing secret bytes are required")
        if tolerance_seconds < 1:
            raise ValueError("Stripe signature tolerance must be positive")
        self._secret = signing_secret
        self._tolerance_seconds = tolerance_seconds

    def verify(
        self,
        *,
        payload: bytes,
        signature_header: str,
        received_at: datetime,
    ) -> VerifiedStripeEvent:
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise StripeWebhookError("received_at must be timezone-aware")
        timestamp, signatures = self._parse_signature(signature_header)
        drift = abs(int(received_at.timestamp()) - timestamp)
        if drift > self._tolerance_seconds:
            raise StripeWebhookError("Stripe webhook timestamp outside tolerance")
        signed = str(timestamp).encode("ascii") + b"." + payload
        expected = hmac.new(self._secret, signed, hashlib.sha256).hexdigest()
        if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
            raise StripeWebhookError("Stripe webhook signature mismatch")
        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StripeWebhookError("Stripe webhook payload is not valid JSON") from exc
        if not isinstance(data, dict):
            raise StripeWebhookError("Stripe webhook payload must be an object")
        event_id = data.get("id")
        event_type = data.get("type")
        created = data.get("created")
        if not isinstance(event_id, str) or not event_id:
            raise StripeWebhookError("Stripe event id is required")
        if not isinstance(event_type, str) or not event_type:
            raise StripeWebhookError("Stripe event type is required")
        if not isinstance(created, int):
            raise StripeWebhookError("Stripe event created timestamp is required")
        return VerifiedStripeEvent(
            event_id=event_id,
            event_type=event_type,
            created_at=datetime.fromtimestamp(created, tz=UTC),
            payload=data,
        )

    @staticmethod
    def _parse_signature(header: str) -> tuple[int, tuple[str, ...]]:
        timestamp: int | None = None
        signatures: list[str] = []
        for item in header.split(","):
            key, separator, value = item.strip().partition("=")
            if not separator:
                continue
            if key == "t":
                try:
                    timestamp = int(value)
                except ValueError as exc:
                    raise StripeWebhookError("invalid Stripe signature timestamp") from exc
            elif key == "v1" and value:
                signatures.append(value)
        if timestamp is None or not signatures:
            raise StripeWebhookError("Stripe signature requires t and v1")
        return timestamp, tuple(signatures)


def _object_data(event: VerifiedStripeEvent) -> dict[str, Any]:
    data = event.payload.get("data")
    if not isinstance(data, dict):
        raise StripeWebhookError("Stripe event data is required")
    obj = data.get("object")
    if not isinstance(obj, dict):
        raise StripeWebhookError("Stripe event object is required")
    return obj


def _subscription_id_from_invoice(obj: dict[str, Any]) -> str:
    subscription = obj.get("subscription")
    if isinstance(subscription, str) and subscription:
        return subscription
    parent = obj.get("parent")
    if isinstance(parent, dict):
        details = parent.get("subscription_details")
        if isinstance(details, dict):
            candidate = details.get("subscription")
            if isinstance(candidate, str) and candidate:
                return candidate
    raise StripeWebhookError("Stripe invoice lacks subscription reference")


def _price_id(item: dict[str, Any]) -> str | None:
    price = item.get("price")
    if isinstance(price, dict):
        candidate = price.get("id")
        if isinstance(candidate, str) and candidate:
            return candidate
    pricing = item.get("pricing")
    if isinstance(pricing, dict):
        price_details = pricing.get("price_details")
        if isinstance(price_details, dict):
            candidate = price_details.get("price")
            if isinstance(candidate, str) and candidate:
                return candidate
    return None


def _subscription_capacity(obj: dict[str, Any], *, base_price_ref: str, additional_ref: str) -> int:
    items = obj.get("items")
    if not isinstance(items, dict):
        raise StripeWebhookError("Stripe subscription items are required")
    data = items.get("data")
    if not isinstance(data, list):
        raise StripeWebhookError("Stripe subscription items.data must be a list")
    base_quantity: int | None = None
    additional_quantity = 0
    for raw in data:
        if not isinstance(raw, dict):
            continue
        price_id = _price_id(raw)
        quantity = raw.get("quantity", 1)
        if not isinstance(quantity, int) or quantity < 0:
            raise StripeWebhookError("Stripe subscription quantity must be a non-negative integer")
        if price_id == base_price_ref:
            base_quantity = quantity
        elif price_id == additional_ref:
            additional_quantity = quantity
    if base_quantity != 1:
        raise StripeWebhookError("Stripe subscription must contain exactly one AXIGNAL base item")
    return 1 + additional_quantity


def _subscription_state(status: object) -> BillingSubscriptionState:
    if status in {"active", "trialing"}:
        return BillingSubscriptionState.ACTIVE
    if status in {"past_due", "unpaid", "incomplete", "incomplete_expired", "paused"}:
        return BillingSubscriptionState.PAST_DUE
    if status == "canceled":
        return BillingSubscriptionState.CANCELLED
    return BillingSubscriptionState.PENDING


class StripeEventNormalizer:
    def __init__(self, mappings: StripeMappingReader) -> None:
        self._mappings = mappings

    def normalize(
        self,
        event: VerifiedStripeEvent,
        *,
        recorded_at: datetime,
    ) -> BillingEvent:
        if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
            raise StripeWebhookError("recorded_at must be timezone-aware")
        obj = _object_data(event)

        if event.event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            subscription_id = obj.get("id")
            if not isinstance(subscription_id, str) or not subscription_id:
                raise StripeWebhookError("Stripe subscription id is required")
            mapping = self._mappings.mapping_for_subscription(subscription_id)
            if mapping is None:
                raise StripeWebhookDependencyError(
                    "Stripe subscription is not mapped to an AXIGNAL account"
                )
            state = (
                BillingSubscriptionState.CANCELLED
                if event.event_type == "customer.subscription.deleted"
                else _subscription_state(obj.get("status"))
            )
            capacity = _subscription_capacity(
                obj,
                base_price_ref=mapping.base_price_ref,
                additional_ref=mapping.additional_xeed_price_ref,
            )
            return BillingEvent(
                event_id=BillingEventId(event.event_id),
                provider=BillingProvider.STRIPE,
                provider_event_type=event.event_type,
                provider_created_at=event.created_at,
                recorded_at=recorded_at,
                external_object_id=subscription_id,
                account_id=mapping.account_id,
                kind=(
                    BillingEventKind.SUBSCRIPTION_CANCELLED
                    if state is BillingSubscriptionState.CANCELLED
                    else BillingEventKind.SUBSCRIPTION_SYNCED
                ),
                subscription_state=state,
                xeed_capacity=capacity,
                source_ref=f"stripe:event:{event.event_id}",
            )

        if event.event_type in {"invoice.paid", "invoice.payment_failed"}:
            subscription_id = _subscription_id_from_invoice(obj)
            mapping = self._mappings.mapping_for_subscription(subscription_id)
            if mapping is None:
                raise StripeWebhookDependencyError("Stripe invoice subscription is not mapped")
            amount = obj.get("amount_paid" if event.event_type == "invoice.paid" else "amount_due")
            if amount is not None and not isinstance(amount, int):
                raise StripeWebhookError("Stripe invoice amount must be integer minor units")
            currency = obj.get("currency")
            if currency is not None and not isinstance(currency, str):
                raise StripeWebhookError("Stripe invoice currency must be text")
            return BillingEvent(
                event_id=BillingEventId(event.event_id),
                provider=BillingProvider.STRIPE,
                provider_event_type=event.event_type,
                provider_created_at=event.created_at,
                recorded_at=recorded_at,
                external_object_id=str(obj.get("id") or subscription_id),
                account_id=mapping.account_id,
                kind=(
                    BillingEventKind.INVOICE_PAID
                    if event.event_type == "invoice.paid"
                    else BillingEventKind.PAYMENT_FAILED
                ),
                payment_state=(
                    BillingPaymentState.PAID
                    if event.event_type == "invoice.paid"
                    else BillingPaymentState.FAILED
                ),
                amount_minor=amount,
                currency=currency,
                source_ref=f"stripe:event:{event.event_id}",
            )

        if event.event_type == "charge.refunded":
            metadata = obj.get("metadata")
            if not isinstance(metadata, dict):
                raise StripeWebhookError("Stripe refunded charge lacks mapping metadata")
            account_id = metadata.get("axignal_account_id")
            subscription_id = metadata.get("axignal_subscription_id")
            if not isinstance(account_id, str) or not isinstance(subscription_id, str):
                raise StripeWebhookError("Stripe refunded charge lacks AXIGNAL mapping metadata")
            mapping = self._mappings.mapping_for_subscription(subscription_id)
            if mapping is None or mapping.account_id != account_id:
                raise StripeWebhookError("Stripe refund mapping does not match AXIGNAL account")
            amount = obj.get("amount_refunded")
            currency = obj.get("currency")
            if not isinstance(amount, int) or not isinstance(currency, str):
                raise StripeWebhookError("Stripe refund amount/currency are required")
            return BillingEvent(
                event_id=BillingEventId(event.event_id),
                provider=BillingProvider.STRIPE,
                provider_event_type=event.event_type,
                provider_created_at=event.created_at,
                recorded_at=recorded_at,
                external_object_id=str(obj.get("id") or subscription_id),
                account_id=account_id,
                kind=BillingEventKind.REFUND_RECORDED,
                payment_state=BillingPaymentState.REFUNDED,
                amount_minor=amount,
                currency=currency,
                source_ref=f"stripe:event:{event.event_id}",
            )

        raise StripeWebhookError(f"unsupported Stripe event type: {event.event_type}")


def checkout_mapping_from_verified_event(
    event: VerifiedStripeEvent,
    *,
    base_price_ref: str,
    additional_xeed_price_ref: str,
    recorded_at: datetime,
) -> tuple[BillingMapping, int]:
    if event.event_type != "checkout.session.completed":
        raise StripeWebhookError("expected checkout.session.completed")
    obj = _object_data(event)
    mode = obj.get("mode")
    if mode != "subscription":
        raise StripeWebhookError("AXIGNAL checkout must be subscription mode")
    customer_id = obj.get("customer")
    subscription_id = obj.get("subscription")
    metadata = obj.get("metadata")
    if not isinstance(customer_id, str) or not customer_id:
        raise StripeWebhookError("Stripe checkout customer id is required")
    if not isinstance(subscription_id, str) or not subscription_id:
        raise StripeWebhookError("Stripe checkout subscription id is required")
    if not isinstance(metadata, dict):
        raise StripeWebhookError("Stripe checkout metadata is required")
    account_id = metadata.get("axignal_account_id")
    capacity_raw = metadata.get("axignal_xeed_capacity")
    if not isinstance(account_id, str) or not account_id:
        raise StripeWebhookError("Stripe checkout lacks AXIGNAL account mapping")
    try:
        capacity = int(str(capacity_raw))
    except (TypeError, ValueError) as exc:
        raise StripeWebhookError("Stripe checkout Xeed capacity is invalid") from exc
    if capacity < 1:
        raise StripeWebhookError("Stripe checkout Xeed capacity must be positive")
    return (
        BillingMapping(
            account_id=account_id,
            provider=BillingProvider.STRIPE,
            external_customer_id=ExternalCustomerId(customer_id),
            external_subscription_id=ExternalSubscriptionId(subscription_id),
            base_price_ref=base_price_ref,
            additional_xeed_price_ref=additional_xeed_price_ref,
            created_at=event.created_at,
        ),
        capacity,
    )
