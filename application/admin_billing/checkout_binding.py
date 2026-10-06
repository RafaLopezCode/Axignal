"""Pure validation of a purchase intent against complete normalized item evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    BindingReason,
    BindingStatus,
    BindingValidationResult,
    CheckoutAttemptBinding,
    NormalizedRecurringItem,
    PurchaseIntent,
    RecurringTerms,
    SnapshotCurrentness,
    SubscriptionItemSnapshot,
)


@dataclass(frozen=True, slots=True)
class _EvaluatedInput:
    fingerprint: str
    intent_ref: str | None
    evidence_ref: str | None
    provider_state_at: datetime | None
    retrieved_at: datetime | None


def _terms_data(terms: RecurringTerms | None) -> dict[str, object] | None:
    if terms is None:
        return None
    return {
        "interval_unit": terms.interval_unit.casefold(),
        "interval_count": terms.interval_count,
        "currency": terms.normalized_currency,
        "unit_amount_minor": terms.unit_amount_minor,
        "tax_behavior": terms.tax_behavior,
    }


def _item_data(item: NormalizedRecurringItem) -> dict[str, object]:
    return {
        "item_ref": item.item_ref,
        "offer_ref": item.offer_ref,
        "quantity": item.quantity,
        "recurring": item.recurring,
        "terms": _terms_data(item.terms),
    }


def _fingerprint(
    intent: PurchaseIntent | None,
    catalogue: ApprovedOfferCatalogue | None,
    binding: CheckoutAttemptBinding | None,
    snapshot: SubscriptionItemSnapshot,
) -> str:
    # Retrieval time is deliberately excluded: retrying the same provider state
    # does not create a content conflict merely because it was read later.
    data: dict[str, object] = {
        "intent": None
        if intent is None
        else {
            "intent_ref": intent.intent_ref,
            "attempt_ref": intent.attempt_ref,
            "catalogue_ref": intent.catalogue_ref,
            "catalogue_version": intent.catalogue_version,
            "xeed_capacity": intent.xeed_capacity,
            "environment_ref": intent.environment_ref,
            "authorized_at": intent.authorized_at.isoformat(),
        },
        "catalogue": None
        if catalogue is None
        else {
            "catalogue_ref": catalogue.catalogue_ref,
            "version": catalogue.version,
            "base_offer": {
                "offer_ref": catalogue.base_offer.offer_ref,
                "terms": _terms_data(catalogue.base_offer.terms),
            },
            "additional_xeed_offer": {
                "offer_ref": catalogue.additional_xeed_offer.offer_ref,
                "terms": _terms_data(catalogue.additional_xeed_offer.terms),
            },
        },
        "binding": None
        if binding is None
        else {
            "binding_ref": binding.binding_ref,
            "intent_ref": binding.intent_ref,
            "attempt_ref": binding.attempt_ref,
            "checkout_session_ref": binding.checkout_session_ref,
            "customer_ref": binding.customer_ref,
            "subscription_ref": binding.subscription_ref,
            "environment_ref": binding.environment_ref,
            "established_at": binding.established_at.isoformat(),
        },
        "snapshot": {
            "evidence_ref": snapshot.evidence_ref,
            "checkout_session_ref": snapshot.checkout_session_ref,
            "customer_ref": snapshot.customer_ref,
            "subscription_ref": snapshot.subscription_ref,
            "environment_ref": snapshot.environment_ref,
            "provider_state_ref": snapshot.provider_state_ref,
            "provider_state_at": snapshot.provider_state_at.isoformat()
            if snapshot.provider_state_at
            else None,
            "currentness": snapshot.currentness.value,
            "enumeration_complete": snapshot.enumeration_complete,
            "has_more": snapshot.has_more,
            "metadata_intent_ref": snapshot.metadata_intent_ref,
            "items": sorted(
                (_item_data(item) for item in snapshot.items), key=lambda x: str(x["item_ref"])
            ),
        },
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _evaluated(
    intent: PurchaseIntent | None,
    snapshot: SubscriptionItemSnapshot | None,
    catalogue: ApprovedOfferCatalogue | None,
    binding: CheckoutAttemptBinding | None,
) -> _EvaluatedInput | None:
    if snapshot is None:
        return None
    return _EvaluatedInput(
        fingerprint=_fingerprint(intent, catalogue, binding, snapshot),
        intent_ref=intent.intent_ref if intent else None,
        evidence_ref=snapshot.evidence_ref,
        provider_state_at=snapshot.provider_state_at,
        retrieved_at=snapshot.retrieved_at,
    )


def _result(
    status: BindingStatus,
    reason: BindingReason,
    values: _EvaluatedInput | None,
    *,
    capacity: int | None = None,
) -> BindingValidationResult:
    return BindingValidationResult(
        status=status,
        reason=reason,
        intent_ref=values.intent_ref if values else None,
        evidence_ref=values.evidence_ref if values else None,
        evidence_fingerprint=values.fingerprint if values else None,
        provider_state_at=values.provider_state_at if values else None,
        xeed_capacity=capacity,
        base_quantity=1 if capacity is not None else None,
        additional_xeed_quantity=capacity - 1 if capacity is not None else None,
    )


def _unknown(reason: BindingReason, values: _EvaluatedInput | None) -> BindingValidationResult:
    return _result(BindingStatus.UNKNOWN, reason, values)


def _mismatch(reason: BindingReason, values: _EvaluatedInput) -> BindingValidationResult:
    return _result(BindingStatus.MISMATCH, reason, values)


def _validate_checkout_binding_inputs(
    *,
    intent: PurchaseIntent | None,
    catalogue: ApprovedOfferCatalogue | None,
    binding: CheckoutAttemptBinding | None,
    snapshot: SubscriptionItemSnapshot | None,
) -> BindingValidationResult:
    """Recompute binding facts solely from the supplied normalized inputs."""
    values = _evaluated(intent, snapshot, catalogue, binding)

    if intent is not None and snapshot is not None and binding is not None:
        if intent.authorized_at > binding.established_at:
            return _unknown(BindingReason.FUTURE_EVIDENCE, values)
        if binding.established_at > snapshot.retrieved_at:
            return _unknown(BindingReason.FUTURE_EVIDENCE, values)
        if snapshot.provider_state_at is not None:
            if snapshot.provider_state_at < intent.authorized_at:
                return _unknown(BindingReason.PRE_AUTHORIZATION_EVIDENCE, values)
            if snapshot.provider_state_at > snapshot.retrieved_at:
                return _unknown(BindingReason.FUTURE_EVIDENCE, values)

    if intent is None:
        return _unknown(BindingReason.MISSING_INTENT, values)
    if catalogue is None:
        return _unknown(BindingReason.MISSING_CATALOGUE, values)
    if snapshot is None:
        return _unknown(BindingReason.MISSING_SNAPSHOT, values)
    if binding is None:
        return _unknown(BindingReason.MISSING_ATTEMPT_BINDING, values)
    assert values is not None
    if (
        intent.catalogue_ref != catalogue.catalogue_ref
        or intent.catalogue_version != catalogue.version
    ):
        return _unknown(BindingReason.INTENT_CATALOGUE_MISMATCH, values)
    if binding.intent_ref != intent.intent_ref or binding.attempt_ref != intent.attempt_ref:
        return _mismatch(BindingReason.ATTEMPT_REFERENCE_MISMATCH, values)
    if (
        binding.environment_ref != intent.environment_ref
        or snapshot.environment_ref != intent.environment_ref
    ):
        return _mismatch(BindingReason.ENVIRONMENT_MISMATCH, values)
    if snapshot.checkout_session_ref != binding.checkout_session_ref:
        return _mismatch(BindingReason.SESSION_REFERENCE_MISMATCH, values)
    if snapshot.customer_ref != binding.customer_ref:
        return _mismatch(BindingReason.CUSTOMER_REFERENCE_MISMATCH, values)
    if snapshot.subscription_ref != binding.subscription_ref:
        return _mismatch(BindingReason.SUBSCRIPTION_REFERENCE_MISMATCH, values)
    if (
        snapshot.metadata_intent_ref is not None
        and snapshot.metadata_intent_ref != intent.intent_ref
    ):
        return _mismatch(BindingReason.METADATA_INTENT_MISMATCH, values)

    if snapshot.currentness is SnapshotCurrentness.STALE:
        return _unknown(BindingReason.STALE_EVIDENCE, values)
    if (
        snapshot.currentness is SnapshotCurrentness.UNKNOWN
        or snapshot.provider_state_at is None
        or snapshot.provider_state_ref is None
    ):
        return _unknown(BindingReason.INCOMPLETE_CURRENTNESS, values)
    if intent.authorized_at > binding.established_at:
        return _unknown(BindingReason.FUTURE_EVIDENCE, values)
    if binding.established_at > snapshot.retrieved_at:
        return _unknown(BindingReason.FUTURE_EVIDENCE, values)
    if snapshot.currentness is not SnapshotCurrentness.CURRENT:
        return _unknown(BindingReason.INCOMPLETE_CURRENTNESS, values)
    if snapshot.enumeration_complete is not True or snapshot.has_more is not False:
        return _unknown(BindingReason.INCOMPLETE_SNAPSHOT, values)

    allowed = {
        catalogue.base_offer.offer_ref: (catalogue.base_offer, "base"),
        catalogue.additional_xeed_offer.offer_ref: (catalogue.additional_xeed_offer, "additional"),
    }
    by_offer: dict[str, NormalizedRecurringItem] = {}
    item_refs: set[str] = set()
    for item in snapshot.items:
        if item.item_ref in item_refs:
            return _mismatch(BindingReason.DUPLICATE_ITEM_REFERENCE, values)
        item_refs.add(item.item_ref)
        if item.offer_ref is not None and item.offer_ref not in allowed:
            return _mismatch(BindingReason.UNAPPROVED_OFFER_ITEM, values)
        if (
            item.offer_ref is None
            or item.quantity is None
            or item.recurring is None
            or item.terms is None
        ):
            return _unknown(BindingReason.INCOMPLETE_SNAPSHOT, values)
        if item.recurring is False:
            return _mismatch(BindingReason.ITEM_TERMS_MISMATCH, values)
        if item.offer_ref in by_offer:
            return _mismatch(BindingReason.DUPLICATE_OFFER_ITEM, values)
        by_offer[item.offer_ref] = item
        approved, _ = allowed[item.offer_ref]
        if item.terms != approved.terms:
            return _mismatch(BindingReason.ITEM_TERMS_MISMATCH, values)

    base = by_offer.get(catalogue.base_offer.offer_ref)
    additional = by_offer.get(catalogue.additional_xeed_offer.offer_ref)
    if base is None or base.quantity is None:
        return _mismatch(BindingReason.BASE_ITEM_MISMATCH, values)
    if base.quantity != 1:
        return _mismatch(BindingReason.BASE_ITEM_MISMATCH, values)
    expected_additional = max(0, intent.xeed_capacity - 1)
    additional_quantity = 0
    if expected_additional == 0:
        if additional is not None:
            return _mismatch(BindingReason.ADDITIONAL_ITEM_MISMATCH, values)
    else:
        if additional is None:
            return _mismatch(BindingReason.ADDITIONAL_ITEM_MISMATCH, values)
        if additional.quantity is None:
            return _unknown(BindingReason.INCOMPLETE_SNAPSHOT, values)
        if additional.quantity != expected_additional:
            return _mismatch(BindingReason.ADDITIONAL_ITEM_MISMATCH, values)
        additional_quantity = additional.quantity

    derived_capacity = base.quantity + additional_quantity
    if derived_capacity != intent.xeed_capacity:
        return _mismatch(BindingReason.CAPACITY_MISMATCH, values)
    return _result(
        BindingStatus.VERIFIED, BindingReason.EXACT_MATCH, values, capacity=derived_capacity
    )


def validate_checkout_binding(
    *,
    intent: PurchaseIntent | None,
    catalogue: ApprovedOfferCatalogue | None,
    binding: CheckoutAttemptBinding | None,
    snapshot: SubscriptionItemSnapshot | None,
    previous: BindingValidationResult | None = None,
) -> BindingValidationResult:
    """Recompute item binding; a stored result never supplies capacity authority."""
    values = _evaluated(intent, snapshot, catalogue, binding)
    recomputed = _validate_checkout_binding_inputs(
        intent=intent,
        catalogue=catalogue,
        binding=binding,
        snapshot=snapshot,
    )

    if previous is None:
        return recomputed
    if previous.intent_ref != (intent.intent_ref if intent else None):
        return _mismatch(BindingReason.PRIOR_INTENT_MISMATCH, values) if values else recomputed
    if snapshot is None:
        return recomputed
    assert values is not None
    if previous.evidence_ref == snapshot.evidence_ref:
        if previous.evidence_fingerprint != values.fingerprint:
            return _mismatch(BindingReason.CONFLICTING_REPLAY, values)
        if recomputed.status is BindingStatus.VERIFIED and previous != recomputed:
            return _mismatch(BindingReason.CONFLICTING_REPLAY, values)
        return recomputed
    if previous.provider_state_at is not None and snapshot.provider_state_at is not None:
        if snapshot.provider_state_at < previous.provider_state_at:
            return _unknown(BindingReason.STALE_EVIDENCE, values)
        if snapshot.provider_state_at == previous.provider_state_at:
            return _unknown(BindingReason.AMBIGUOUS_ORDER, values)
    return recomputed
