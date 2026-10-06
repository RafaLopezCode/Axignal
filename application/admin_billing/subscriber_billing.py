"""Provider-neutral subscriber billing state and current-capacity validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    BindingReason,
    BindingStatus,
    CurrentSubscriptionItems,
    NormalizedRecurringItem,
    SnapshotCurrentness,
)


class PaymentState(StrEnum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class SubscriptionLifecycle(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    CANCEL_AT_PERIOD_END = "CANCEL_AT_PERIOD_END"
    OVERDUE = "OVERDUE"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


class PurchaseState(StrEnum):
    PENDING_PURCHASE = "PENDING_PURCHASE"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SubscriptionCapacityValidation:
    status: BindingStatus
    reason: BindingReason
    evidence_ref: str | None
    evidence_fingerprint: str | None
    provider_state_ref: str | None
    provider_state_at: datetime | None
    effective_capacity: int | None

    def __post_init__(self) -> None:
        if type(self.status) is not BindingStatus or type(self.reason) is not BindingReason:
            raise ValueError("status and reason must use their declared enums")
        if self.status is BindingStatus.VERIFIED:
            if (
                self.evidence_ref is None
                or self.evidence_fingerprint is None
                or self.provider_state_ref is None
                or self.provider_state_at is None
                or type(self.effective_capacity) is not int
                or self.effective_capacity < 1
            ):
                raise ValueError("verified capacity needs complete evidence")
        elif self.effective_capacity is not None:
            raise ValueError("non-verified capacity cannot be positive")


def _terms_data(item: NormalizedRecurringItem) -> dict[str, object] | None:
    if item.terms is None:
        return None
    return {
        "interval_unit": item.terms.interval_unit,
        "interval_count": item.terms.interval_count,
        "currency": item.terms.currency,
        "unit_amount_minor": item.terms.unit_amount_minor,
        "tax_behavior": item.terms.tax_behavior,
    }


def _fingerprint(
    *,
    expected_capacity: int | None,
    catalogue: ApprovedOfferCatalogue | None,
    snapshot: CurrentSubscriptionItems | None,
) -> str | None:
    if snapshot is None:
        return None
    payload: dict[str, object] = {
        "expected_capacity": expected_capacity,
        "catalogue": None
        if catalogue is None
        else {
            "catalogue_ref": catalogue.catalogue_ref,
            "version": catalogue.version,
            "base_offer_ref": catalogue.base_offer.offer_ref,
            "base_terms": {
                "interval_unit": catalogue.base_offer.terms.interval_unit,
                "interval_count": catalogue.base_offer.terms.interval_count,
                "currency": catalogue.base_offer.terms.currency,
                "unit_amount_minor": catalogue.base_offer.terms.unit_amount_minor,
                "tax_behavior": catalogue.base_offer.terms.tax_behavior,
            },
            "additional_offer_ref": catalogue.additional_xeed_offer.offer_ref,
            "additional_terms": {
                "interval_unit": catalogue.additional_xeed_offer.terms.interval_unit,
                "interval_count": catalogue.additional_xeed_offer.terms.interval_count,
                "currency": catalogue.additional_xeed_offer.terms.currency,
                "unit_amount_minor": catalogue.additional_xeed_offer.terms.unit_amount_minor,
                "tax_behavior": catalogue.additional_xeed_offer.terms.tax_behavior,
            },
        },
        "customer_ref": snapshot.customer_ref,
        "subscription_ref": snapshot.subscription_ref,
        "environment_ref": snapshot.environment_ref,
        "provider_state_ref": snapshot.provider_state_ref,
        "provider_state_at": (
            snapshot.provider_state_at.isoformat() if snapshot.provider_state_at else None
        ),
        "currentness": snapshot.currentness.value,
        "enumeration_complete": snapshot.enumeration_complete,
        "has_more": snapshot.has_more,
        "items": [
            {
                "item_ref": item.item_ref,
                "offer_ref": item.offer_ref,
                "quantity": item.quantity,
                "recurring": item.recurring,
                "terms": _terms_data(item),
            }
            for item in snapshot.items
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _result(
    status: BindingStatus,
    reason: BindingReason,
    snapshot: CurrentSubscriptionItems | None,
    fingerprint: str | None,
    capacity: int | None = None,
) -> SubscriptionCapacityValidation:
    return SubscriptionCapacityValidation(
        status=status,
        reason=reason,
        evidence_ref=None if snapshot is None else snapshot.evidence_ref,
        evidence_fingerprint=fingerprint,
        provider_state_ref=None if snapshot is None else snapshot.provider_state_ref,
        provider_state_at=None if snapshot is None else snapshot.provider_state_at,
        effective_capacity=capacity,
    )


def validate_subscription_capacity(
    *,
    expected_capacity: int | None,
    authorized_at: datetime | None,
    catalogue: ApprovedOfferCatalogue | None,
    expected_customer_ref: str | None,
    expected_subscription_ref: str | None,
    expected_environment_ref: str | None,
    snapshot: CurrentSubscriptionItems | None,
    previous: SubscriptionCapacityValidation | None = None,
) -> SubscriptionCapacityValidation:
    """Validate one complete current item snapshot against a desired total.

    This validates recurring item binding only. It does not establish payment,
    identity/membership, lifecycle eligibility, effective entitlement, or
    provider event ordering outside the supplied snapshot.
    """
    fingerprint = _fingerprint(
        expected_capacity=expected_capacity,
        catalogue=catalogue,
        snapshot=snapshot,
    )

    def unknown(reason: BindingReason) -> SubscriptionCapacityValidation:
        return _result(BindingStatus.UNKNOWN, reason, snapshot, fingerprint)

    def mismatch(reason: BindingReason) -> SubscriptionCapacityValidation:
        return _result(BindingStatus.MISMATCH, reason, snapshot, fingerprint)

    if type(expected_capacity) is not int or expected_capacity < 1:
        return unknown(BindingReason.MISSING_INTENT)
    if authorized_at is None or authorized_at.tzinfo is None or authorized_at.utcoffset() is None:
        return unknown(BindingReason.PRE_AUTHORIZATION_EVIDENCE)
    if catalogue is None:
        return unknown(BindingReason.MISSING_CATALOGUE)
    if snapshot is None:
        return unknown(BindingReason.MISSING_SNAPSHOT)
    if not all((expected_customer_ref, expected_subscription_ref, expected_environment_ref)):
        return unknown(BindingReason.INCOMPLETE_CURRENTNESS)
    if snapshot.customer_ref != expected_customer_ref:
        return mismatch(BindingReason.CUSTOMER_REFERENCE_MISMATCH)
    if snapshot.subscription_ref != expected_subscription_ref:
        return mismatch(BindingReason.SUBSCRIPTION_REFERENCE_MISMATCH)
    if snapshot.environment_ref != expected_environment_ref:
        return mismatch(BindingReason.ENVIRONMENT_MISMATCH)
    if snapshot.currentness is SnapshotCurrentness.STALE:
        return unknown(BindingReason.STALE_EVIDENCE)
    if (
        snapshot.currentness is not SnapshotCurrentness.CURRENT
        or snapshot.provider_state_ref is None
        or snapshot.provider_state_at is None
    ):
        return unknown(BindingReason.INCOMPLETE_CURRENTNESS)
    if snapshot.provider_state_at < authorized_at:
        return unknown(BindingReason.PRE_AUTHORIZATION_EVIDENCE)
    if snapshot.provider_state_at > snapshot.retrieved_at:
        return unknown(BindingReason.FUTURE_EVIDENCE)
    if snapshot.enumeration_complete is not True or snapshot.has_more is not False:
        return unknown(BindingReason.INCOMPLETE_SNAPSHOT)

    allowed = {
        catalogue.base_offer.offer_ref: catalogue.base_offer,
        catalogue.additional_xeed_offer.offer_ref: catalogue.additional_xeed_offer,
    }
    by_offer: dict[str, NormalizedRecurringItem] = {}
    item_refs: set[str] = set()
    for item in snapshot.items:
        if item.item_ref in item_refs:
            return mismatch(BindingReason.DUPLICATE_ITEM_REFERENCE)
        item_refs.add(item.item_ref)
        if item.offer_ref is not None and item.offer_ref not in allowed:
            return mismatch(BindingReason.UNAPPROVED_OFFER_ITEM)
        if (
            item.offer_ref is None
            or item.quantity is None
            or item.recurring is None
            or item.terms is None
        ):
            return unknown(BindingReason.INCOMPLETE_SNAPSHOT)
        if item.recurring is not True:
            return mismatch(BindingReason.ITEM_TERMS_MISMATCH)
        if item.offer_ref in by_offer:
            return mismatch(BindingReason.DUPLICATE_OFFER_ITEM)
        by_offer[item.offer_ref] = item
        if item.terms != allowed[item.offer_ref].terms:
            return mismatch(BindingReason.ITEM_TERMS_MISMATCH)

    base = by_offer.get(catalogue.base_offer.offer_ref)
    additional = by_offer.get(catalogue.additional_xeed_offer.offer_ref)
    if base is None or base.quantity != 1:
        return mismatch(BindingReason.BASE_ITEM_MISMATCH)
    expected_additional = expected_capacity - 1
    if expected_additional == 0:
        if additional is not None:
            return mismatch(BindingReason.ADDITIONAL_ITEM_MISMATCH)
    elif additional is None or additional.quantity != expected_additional:
        return mismatch(BindingReason.ADDITIONAL_ITEM_MISMATCH)

    recomputed = _result(
        BindingStatus.VERIFIED,
        BindingReason.EXACT_MATCH,
        snapshot,
        fingerprint,
        capacity=expected_capacity,
    )
    if previous is not None:
        if previous.evidence_ref == snapshot.evidence_ref:
            if previous.evidence_fingerprint != fingerprint or previous != recomputed:
                return mismatch(BindingReason.CONFLICTING_REPLAY)
        elif previous.provider_state_at is not None:
            if snapshot.provider_state_at < previous.provider_state_at:
                return unknown(BindingReason.STALE_EVIDENCE)
            if snapshot.provider_state_at == previous.provider_state_at:
                return unknown(BindingReason.AMBIGUOUS_ORDER)
    return recomputed
