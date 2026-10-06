from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from application.admin_billing.checkout_binding import validate_checkout_binding
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedRecurringOffer,
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

NOW = datetime(2026, 10, 6, 12, tzinfo=UTC)
BASE_OFFER_REF = "offer:base:fixture-v1"
ADDITIONAL_OFFER_REF = "offer:additional:fixture-v1"


def _terms(amount_minor: int) -> RecurringTerms:
    return RecurringTerms(
        interval_unit="month",
        interval_count=1,
        currency="EUR",
        unit_amount_minor=amount_minor,
    )


def _catalogue() -> ApprovedOfferCatalogue:
    # Synthetic amounts and opaque offer refs; these are not AXIGNAL prices.
    return ApprovedOfferCatalogue(
        catalogue_ref="catalogue:fixture",
        version="fixture-v1",
        base_offer=ApprovedRecurringOffer(BASE_OFFER_REF, _terms(1000)),
        additional_xeed_offer=ApprovedRecurringOffer(ADDITIONAL_OFFER_REF, _terms(250)),
    )


def _intent(capacity: int, *, environment: str = "environment:test") -> PurchaseIntent:
    return PurchaseIntent(
        intent_ref="intent:fixture-1",
        attempt_ref="attempt:fixture-1",
        catalogue_ref="catalogue:fixture",
        catalogue_version="fixture-v1",
        xeed_capacity=capacity,
        environment_ref=environment,
        authorized_at=NOW,
    )


def _binding(*, environment: str = "environment:test") -> CheckoutAttemptBinding:
    return CheckoutAttemptBinding(
        binding_ref="binding:fixture-1",
        intent_ref="intent:fixture-1",
        attempt_ref="attempt:fixture-1",
        checkout_session_ref="session:fixture-1",
        customer_ref="customer:fixture-1",
        subscription_ref="subscription:fixture-1",
        environment_ref=environment,
        established_at=NOW + timedelta(seconds=1),
    )


def _snapshot(
    capacity: int,
    *,
    evidence_ref: str = "evidence:fixture-1",
    retrieved_at: datetime = NOW + timedelta(seconds=3),
    currentness: SnapshotCurrentness = SnapshotCurrentness.CURRENT,
    enumeration_complete: bool | None = True,
    has_more: bool | None = False,
    metadata_intent_ref: str | None = "intent:fixture-1",
    items: tuple[NormalizedRecurringItem, ...] | None = None,
    session_ref: str = "session:fixture-1",
    customer_ref: str = "customer:fixture-1",
    subscription_ref: str = "subscription:fixture-1",
    environment_ref: str = "environment:test",
    provider_state_at: datetime | None = NOW + timedelta(seconds=2),
    provider_state_ref: str | None = "state:fixture-1",
) -> SubscriptionItemSnapshot:
    if items is None:
        values = [
            NormalizedRecurringItem(
                item_ref="item:base",
                offer_ref=BASE_OFFER_REF,
                quantity=1,
                recurring=True,
                terms=_terms(1000),
            )
        ]
        if capacity > 1:
            values.append(
                NormalizedRecurringItem(
                    item_ref="item:additional",
                    offer_ref=ADDITIONAL_OFFER_REF,
                    quantity=capacity - 1,
                    recurring=True,
                    terms=_terms(250),
                )
            )
        items = tuple(values)
    return SubscriptionItemSnapshot(
        evidence_ref=evidence_ref,
        checkout_session_ref=session_ref,
        customer_ref=customer_ref,
        subscription_ref=subscription_ref,
        environment_ref=environment_ref,
        provider_state_ref=provider_state_ref,
        provider_state_at=provider_state_at,
        retrieved_at=retrieved_at,
        currentness=currentness,
        enumeration_complete=enumeration_complete,
        has_more=has_more,
        metadata_intent_ref=metadata_intent_ref,
        items=items,
    )


@pytest.mark.parametrize(("capacity", "additional"), [(1, 0), (2, 1), (100, 99)])
def test_complete_item_set_verifies_only_derived_capacity(capacity: int, additional: int) -> None:
    result = validate_checkout_binding(
        intent=_intent(capacity),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(capacity),
    )

    assert result.status is BindingStatus.VERIFIED
    assert result.reason is BindingReason.EXACT_MATCH
    assert result.xeed_capacity == capacity
    assert result.base_quantity == 1
    assert result.additional_xeed_quantity == additional
    assert result.evidence_fingerprint is not None


@pytest.mark.parametrize(
    ("items", "reason"),
    [
        ((), BindingReason.BASE_ITEM_MISMATCH),
        (
            (
                NormalizedRecurringItem("item:base", BASE_OFFER_REF, 2, True, _terms(1000)),
                NormalizedRecurringItem(
                    "item:additional", ADDITIONAL_OFFER_REF, 1, True, _terms(250)
                ),
            ),
            BindingReason.BASE_ITEM_MISMATCH,
        ),
        (
            (
                NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1000)),
                NormalizedRecurringItem(
                    "item:additional", ADDITIONAL_OFFER_REF, 2, True, _terms(250)
                ),
            ),
            BindingReason.ADDITIONAL_ITEM_MISMATCH,
        ),
        (
            (
                NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1000)),
                NormalizedRecurringItem("item:extra", "offer:unapproved", 1, True, _terms(100)),
            ),
            BindingReason.UNAPPROVED_OFFER_ITEM,
        ),
        (
            (NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1001)),),
            BindingReason.ITEM_TERMS_MISMATCH,
        ),
    ],
)
def test_known_item_mismatches_never_return_positive_capacity(
    items: tuple[NormalizedRecurringItem, ...], reason: BindingReason
) -> None:
    result = validate_checkout_binding(
        intent=_intent(2),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(2, items=items),
    )

    assert result.status is BindingStatus.MISMATCH
    assert result.reason is reason
    assert result.xeed_capacity is None


@pytest.mark.parametrize(
    ("complete", "has_more", "currentness", "state_at", "reason"),
    [
        (
            False,
            False,
            SnapshotCurrentness.CURRENT,
            NOW + timedelta(seconds=2),
            BindingReason.INCOMPLETE_SNAPSHOT,
        ),
        (
            True,
            True,
            SnapshotCurrentness.CURRENT,
            NOW + timedelta(seconds=2),
            BindingReason.INCOMPLETE_SNAPSHOT,
        ),
        (
            True,
            None,
            SnapshotCurrentness.CURRENT,
            NOW + timedelta(seconds=2),
            BindingReason.INCOMPLETE_SNAPSHOT,
        ),
        (
            None,
            False,
            SnapshotCurrentness.CURRENT,
            NOW + timedelta(seconds=2),
            BindingReason.INCOMPLETE_SNAPSHOT,
        ),
        (
            True,
            False,
            SnapshotCurrentness.STALE,
            NOW + timedelta(seconds=2),
            BindingReason.STALE_EVIDENCE,
        ),
        (
            True,
            False,
            SnapshotCurrentness.UNKNOWN,
            NOW + timedelta(seconds=2),
            BindingReason.INCOMPLETE_CURRENTNESS,
        ),
        (True, False, SnapshotCurrentness.CURRENT, None, BindingReason.INCOMPLETE_CURRENTNESS),
    ],
)
def test_incomplete_or_noncurrent_snapshot_stays_unknown(
    complete: bool | None,
    has_more: bool | None,
    currentness: SnapshotCurrentness,
    state_at: datetime | None,
    reason: BindingReason,
) -> None:
    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(
            1,
            enumeration_complete=complete,
            has_more=has_more,
            currentness=currentness,
            provider_state_at=state_at,
        ),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is reason
    assert result.xeed_capacity is None


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ("session", BindingReason.SESSION_REFERENCE_MISMATCH),
        ("customer", BindingReason.CUSTOMER_REFERENCE_MISMATCH),
        ("subscription", BindingReason.SUBSCRIPTION_REFERENCE_MISMATCH),
        ("environment", BindingReason.ENVIRONMENT_MISMATCH),
        ("metadata", BindingReason.METADATA_INTENT_MISMATCH),
    ],
)
def test_binding_references_and_metadata_correlation_must_match(
    change: str, reason: BindingReason
) -> None:
    snapshot = _snapshot(1)
    if change == "session":
        snapshot = replace(snapshot, checkout_session_ref="session:other")
    elif change == "customer":
        snapshot = replace(snapshot, customer_ref="customer:other")
    elif change == "subscription":
        snapshot = replace(snapshot, subscription_ref="subscription:other")
    elif change == "environment":
        snapshot = replace(snapshot, environment_ref="environment:live")
    else:
        snapshot = replace(snapshot, metadata_intent_ref="intent:other")

    result = validate_checkout_binding(
        intent=_intent(1), catalogue=_catalogue(), binding=_binding(), snapshot=snapshot
    )

    assert result.status is BindingStatus.MISMATCH
    assert result.reason is reason
    assert result.xeed_capacity is None


def test_metadata_alone_cannot_verify_binding() -> None:
    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=None,
        snapshot=_snapshot(1),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.MISSING_ATTEMPT_BINDING
    assert result.xeed_capacity is None


def test_unknown_item_facts_remain_unknown() -> None:
    snapshot = _snapshot(
        1,
        items=(NormalizedRecurringItem("item:base", BASE_OFFER_REF, None, True, _terms(1000)),),
    )

    result = validate_checkout_binding(
        intent=_intent(1), catalogue=_catalogue(), binding=_binding(), snapshot=snapshot
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.INCOMPLETE_SNAPSHOT
    assert result.xeed_capacity is None


def test_exact_replay_recomputes_same_result_when_retrieved_again_later() -> None:
    first = validate_checkout_binding(
        intent=_intent(2), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(2)
    )
    later_snapshot = replace(_snapshot(2), retrieved_at=NOW + timedelta(minutes=1))

    replay = validate_checkout_binding(
        intent=_intent(2),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=later_snapshot,
        previous=first,
    )

    assert replay == first
    assert replay is not first


@pytest.mark.parametrize(
    "corrupt_previous",
    [
        lambda previous: replace(
            previous,
            xeed_capacity=100,
            additional_xeed_quantity=99,
        ),
        lambda previous: replace(previous, reason=BindingReason.FUTURE_EVIDENCE),
        lambda previous: replace(
            previous,
            status=BindingStatus.MISMATCH,
            reason=BindingReason.BASE_ITEM_MISMATCH,
            xeed_capacity=None,
            base_quantity=None,
            additional_xeed_quantity=None,
        ),
    ],
)
def test_replay_does_not_trust_corrupt_previous_result(
    corrupt_previous: Callable[[BindingValidationResult], BindingValidationResult],
) -> None:
    valid = validate_checkout_binding(
        intent=_intent(1), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(1)
    )
    corrupted = corrupt_previous(valid)

    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1),
        previous=corrupted,
    )

    assert result.status is BindingStatus.MISMATCH
    assert result.reason is BindingReason.CONFLICTING_REPLAY
    assert result.xeed_capacity is None


def test_missing_snapshot_cannot_reuse_previous_verified_capacity() -> None:
    previous = validate_checkout_binding(
        intent=_intent(1), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(1)
    )

    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=None,
        previous=previous,
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.MISSING_SNAPSHOT
    assert result.xeed_capacity is None


def test_same_evidence_reference_with_changed_items_is_conflicting_replay() -> None:
    first = validate_checkout_binding(
        intent=_intent(2), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(2)
    )
    changed = _snapshot(
        2,
        items=(NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1001)),),
    )

    conflict = validate_checkout_binding(
        intent=_intent(2),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=changed,
        previous=first,
    )

    assert conflict.status is BindingStatus.MISMATCH
    assert conflict.reason is BindingReason.CONFLICTING_REPLAY
    assert conflict.xeed_capacity is None


@pytest.mark.parametrize(
    ("provider_state_at", "evidence_ref", "reason"),
    [
        (NOW + timedelta(seconds=1), "evidence:older", BindingReason.STALE_EVIDENCE),
        (NOW + timedelta(seconds=2), "evidence:peer", BindingReason.AMBIGUOUS_ORDER),
    ],
)
def test_stale_or_ambiguous_prior_order_never_returns_capacity(
    provider_state_at: datetime, evidence_ref: str, reason: BindingReason
) -> None:
    prior = validate_checkout_binding(
        intent=_intent(2), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(2)
    )
    candidate = _snapshot(
        2,
        evidence_ref=evidence_ref,
        provider_state_at=provider_state_at,
        provider_state_ref=f"state:{evidence_ref}",
    )

    result = validate_checkout_binding(
        intent=_intent(2),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=candidate,
        previous=prior,
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is reason
    assert result.xeed_capacity is None


def test_catalogue_reference_mismatch_is_unknown() -> None:
    intent = replace(_intent(1), catalogue_version="not-the-catalogue")

    result = validate_checkout_binding(
        intent=intent,
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.INTENT_CATALOGUE_MISMATCH
    assert result.xeed_capacity is None


def test_future_provider_state_is_unknown() -> None:
    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1, provider_state_at=NOW + timedelta(minutes=1)),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.FUTURE_EVIDENCE
    assert result.xeed_capacity is None


def test_binding_established_before_intent_authorization_is_unknown() -> None:
    intent = replace(_intent(1), authorized_at=NOW + timedelta(seconds=2))

    result = validate_checkout_binding(
        intent=intent,
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.FUTURE_EVIDENCE
    assert result.xeed_capacity is None


def test_provider_state_before_intent_authorization_is_unknown() -> None:
    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1, provider_state_at=NOW - timedelta(seconds=1)),
    )

    assert result.status is BindingStatus.UNKNOWN
    assert result.reason is BindingReason.PRE_AUTHORIZATION_EVIDENCE
    assert result.xeed_capacity is None


def test_provider_state_after_authorization_but_before_local_binding_is_valid() -> None:
    result = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=_snapshot(1, provider_state_at=NOW + timedelta(milliseconds=500)),
    )

    assert result.status is BindingStatus.VERIFIED
    assert result.xeed_capacity == 1


@pytest.mark.parametrize(
    "make_invalid",
    [
        lambda: replace(_intent(1), xeed_capacity=True),
        lambda: replace(_intent(1), xeed_capacity=1.0),
        lambda: replace(_terms(100), interval_count=True),
        lambda: replace(_terms(100), interval_count=1.0),
        lambda: replace(_terms(100), unit_amount_minor=True),
        lambda: replace(_terms(100), unit_amount_minor=1.0),
        lambda: replace(
            NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1000)),
            quantity=True,
        ),
        lambda: replace(
            NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1000)),
            quantity=1.0,
        ),
        lambda: replace(
            NormalizedRecurringItem("item:base", BASE_OFFER_REF, 1, True, _terms(1000)),
            recurring=1,
        ),
        lambda: replace(_snapshot(1), enumeration_complete=1),
        lambda: replace(_snapshot(1), has_more=0),
        lambda: replace(_snapshot(1), currentness="CURRENT"),
    ],
)
def test_boolean_and_float_values_cannot_masquerade_as_normalized_facts(
    make_invalid: Callable[[], object],
) -> None:
    with pytest.raises(ValueError):
        make_invalid()


def test_replay_shortcut_does_not_hide_temporal_inconsistency() -> None:
    previous = validate_checkout_binding(
        intent=_intent(1), catalogue=_catalogue(), binding=_binding(), snapshot=_snapshot(1)
    )
    temporally_invalid = replace(_snapshot(1), retrieved_at=NOW + timedelta(seconds=1))

    replay = validate_checkout_binding(
        intent=_intent(1),
        catalogue=_catalogue(),
        binding=_binding(),
        snapshot=temporally_invalid,
        previous=previous,
    )

    assert replay.status is BindingStatus.UNKNOWN
    assert replay.reason is BindingReason.FUTURE_EVIDENCE
    assert replay.xeed_capacity is None
