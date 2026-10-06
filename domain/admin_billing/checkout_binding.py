"""Provider-neutral evidence contracts for recurring Checkout binding validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


def _text(value: str, name: str, maximum: int = 300) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be non-empty bounded text")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


class BindingStatus(StrEnum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


class BindingReason(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    MISSING_INTENT = "MISSING_INTENT"
    MISSING_CATALOGUE = "MISSING_CATALOGUE"
    MISSING_SNAPSHOT = "MISSING_SNAPSHOT"
    MISSING_ATTEMPT_BINDING = "MISSING_ATTEMPT_BINDING"
    INCOMPLETE_SNAPSHOT = "INCOMPLETE_SNAPSHOT"
    INCOMPLETE_CURRENTNESS = "INCOMPLETE_CURRENTNESS"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    AMBIGUOUS_ORDER = "AMBIGUOUS_ORDER"
    FUTURE_EVIDENCE = "FUTURE_EVIDENCE"
    PRE_AUTHORIZATION_EVIDENCE = "PRE_AUTHORIZATION_EVIDENCE"
    INTENT_CATALOGUE_MISMATCH = "INTENT_CATALOGUE_MISMATCH"
    ATTEMPT_REFERENCE_MISMATCH = "ATTEMPT_REFERENCE_MISMATCH"
    SESSION_REFERENCE_MISMATCH = "SESSION_REFERENCE_MISMATCH"
    CUSTOMER_REFERENCE_MISMATCH = "CUSTOMER_REFERENCE_MISMATCH"
    SUBSCRIPTION_REFERENCE_MISMATCH = "SUBSCRIPTION_REFERENCE_MISMATCH"
    ENVIRONMENT_MISMATCH = "ENVIRONMENT_MISMATCH"
    METADATA_INTENT_MISMATCH = "METADATA_INTENT_MISMATCH"
    DUPLICATE_ITEM_REFERENCE = "DUPLICATE_ITEM_REFERENCE"
    DUPLICATE_OFFER_ITEM = "DUPLICATE_OFFER_ITEM"
    UNAPPROVED_OFFER_ITEM = "UNAPPROVED_OFFER_ITEM"
    ITEM_TERMS_MISMATCH = "ITEM_TERMS_MISMATCH"
    BASE_ITEM_MISMATCH = "BASE_ITEM_MISMATCH"
    ADDITIONAL_ITEM_MISMATCH = "ADDITIONAL_ITEM_MISMATCH"
    CAPACITY_MISMATCH = "CAPACITY_MISMATCH"
    CONFLICTING_REPLAY = "CONFLICTING_REPLAY"
    PRIOR_INTENT_MISMATCH = "PRIOR_INTENT_MISMATCH"


class SnapshotCurrentness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RecurringTerms:
    interval_unit: str
    interval_count: int
    currency: str
    unit_amount_minor: int
    tax_behavior: str = "exclusive"

    def __post_init__(self) -> None:
        _text(self.interval_unit, "interval_unit", 40)
        object.__setattr__(self, "interval_unit", self.interval_unit.casefold())
        if type(self.interval_count) is not int or self.interval_count < 1:
            raise ValueError("interval_count must be positive")
        if (
            not isinstance(self.currency, str)
            or len(self.currency) != 3
            or not self.currency.isascii()
            or not self.currency.isalpha()
        ):
            raise ValueError("currency must be a three-letter ASCII code")
        object.__setattr__(self, "currency", self.currency.upper())
        if self.tax_behavior not in {"exclusive", "inclusive"}:
            raise ValueError("tax_behavior must be an explicit inclusive or exclusive policy")
        if type(self.unit_amount_minor) is not int or self.unit_amount_minor < 0:
            raise ValueError("unit_amount_minor cannot be negative")

    @property
    def normalized_currency(self) -> str:
        return self.currency


@dataclass(frozen=True, slots=True)
class ApprovedRecurringOffer:
    offer_ref: str
    terms: RecurringTerms

    def __post_init__(self) -> None:
        _text(self.offer_ref, "offer_ref")


@dataclass(frozen=True, slots=True)
class ApprovedTaxConfiguration:
    """Root-reviewed evidence that automatic tax has a current active registration."""

    configuration_ref: str
    environment_ref: str
    active_registration_refs: tuple[str, ...]
    automatic_tax_enabled: bool
    verified_at: datetime
    valid_until: datetime | None = None

    def __post_init__(self) -> None:
        _text(self.configuration_ref, "tax configuration reference")
        _text(self.environment_ref, "tax environment reference")
        if (
            not isinstance(self.active_registration_refs, tuple)
            or not self.active_registration_refs
            or any(
                not isinstance(ref, str) or not ref.strip() for ref in self.active_registration_refs
            )
        ):
            raise ValueError("tax configuration requires confirmed active registration references")
        if type(self.automatic_tax_enabled) is not bool:
            raise ValueError("automatic tax enablement must be explicit")
        _aware(self.verified_at, "tax configuration verification time")
        if self.valid_until is not None:
            _aware(self.valid_until, "tax configuration validity end")

    def is_current(self, environment_ref: str, now: datetime) -> bool:
        return (
            self.environment_ref == environment_ref
            and self.automatic_tax_enabled is True
            and self.verified_at <= now
            and (self.valid_until is None or now < self.valid_until)
        )


@dataclass(frozen=True, slots=True)
class ApprovedOfferCatalogue:
    catalogue_ref: str
    version: str
    base_offer: ApprovedRecurringOffer
    additional_xeed_offer: ApprovedRecurringOffer
    tax_configuration: ApprovedTaxConfiguration | None = None

    def __post_init__(self) -> None:
        _text(self.catalogue_ref, "catalogue_ref")
        _text(self.version, "version", 100)
        if self.base_offer.offer_ref == self.additional_xeed_offer.offer_ref:
            raise ValueError("base and additional-Xeed offer references must differ")


@dataclass(frozen=True, slots=True)
class PurchaseIntent:
    """AXIGNAL-authorized offer/capacity intent; contains no payer or Tenant identity."""

    intent_ref: str
    attempt_ref: str
    catalogue_ref: str
    catalogue_version: str
    xeed_capacity: int
    environment_ref: str
    authorized_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.intent_ref, "intent_ref"),
            (self.attempt_ref, "attempt_ref"),
            (self.catalogue_ref, "catalogue_ref"),
            (self.catalogue_version, "catalogue_version"),
            (self.environment_ref, "environment_ref"),
        ):
            _text(value, name)
        if type(self.xeed_capacity) is not int or self.xeed_capacity < 1:
            raise ValueError("xeed_capacity must be positive")
        _aware(self.authorized_at, "authorized_at")


@dataclass(frozen=True, slots=True)
class CheckoutAttemptBinding:
    """Opaque server-owned binding recorded for one authorized Checkout attempt."""

    binding_ref: str
    intent_ref: str
    attempt_ref: str
    checkout_session_ref: str
    customer_ref: str
    subscription_ref: str
    environment_ref: str
    established_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.binding_ref, "binding_ref"),
            (self.intent_ref, "intent_ref"),
            (self.attempt_ref, "attempt_ref"),
            (self.checkout_session_ref, "checkout_session_ref"),
            (self.customer_ref, "customer_ref"),
            (self.subscription_ref, "subscription_ref"),
            (self.environment_ref, "environment_ref"),
        ):
            _text(value, name)
        _aware(self.established_at, "established_at")


@dataclass(frozen=True, slots=True)
class NormalizedRecurringItem:
    item_ref: str
    offer_ref: str | None
    quantity: int | None
    recurring: bool | None
    terms: RecurringTerms | None

    def __post_init__(self) -> None:
        _text(self.item_ref, "item_ref")
        if self.offer_ref is not None:
            _text(self.offer_ref, "offer_ref")
        if self.quantity is not None and (type(self.quantity) is not int or self.quantity < 1):
            raise ValueError("known subscription item quantity must be positive")
        if self.recurring is not None and type(self.recurring) is not bool:
            raise ValueError("recurring must be bool or None")


@dataclass(frozen=True, slots=True)
class SubscriptionItemSnapshot:
    """Normalized provider facts. Completeness/currentness are explicit evidence."""

    evidence_ref: str
    checkout_session_ref: str
    customer_ref: str
    subscription_ref: str
    environment_ref: str
    provider_state_ref: str | None
    provider_state_at: datetime | None
    retrieved_at: datetime
    currentness: SnapshotCurrentness
    enumeration_complete: bool | None
    has_more: bool | None
    metadata_intent_ref: str | None
    items: tuple[NormalizedRecurringItem, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.evidence_ref, "evidence_ref"),
            (self.checkout_session_ref, "checkout_session_ref"),
            (self.customer_ref, "customer_ref"),
            (self.subscription_ref, "subscription_ref"),
            (self.environment_ref, "environment_ref"),
        ):
            _text(value, name)
        if self.provider_state_ref is not None:
            _text(self.provider_state_ref, "provider_state_ref")
        if self.metadata_intent_ref is not None:
            _text(self.metadata_intent_ref, "metadata_intent_ref")
        _aware(self.retrieved_at, "retrieved_at")
        if self.provider_state_at is not None:
            _aware(self.provider_state_at, "provider_state_at")
        if type(self.currentness) is not SnapshotCurrentness:
            raise ValueError("currentness must use SnapshotCurrentness")
        if self.enumeration_complete is not None and type(self.enumeration_complete) is not bool:
            raise ValueError("enumeration_complete must be bool or None")
        if self.has_more is not None and type(self.has_more) is not bool:
            raise ValueError("has_more must be bool or None")
        if not isinstance(self.items, tuple):
            raise ValueError("items must be an immutable tuple")


@dataclass(frozen=True, slots=True)
class BindingValidationResult:
    status: BindingStatus
    reason: BindingReason
    intent_ref: str | None
    evidence_ref: str | None
    evidence_fingerprint: str | None
    provider_state_at: datetime | None
    xeed_capacity: int | None
    base_quantity: int | None
    additional_xeed_quantity: int | None

    def __post_init__(self) -> None:
        if type(self.status) is not BindingStatus or type(self.reason) is not BindingReason:
            raise ValueError("status and reason must use their declared enums")
        if self.status is BindingStatus.VERIFIED:
            if (
                self.intent_ref is None
                or self.evidence_ref is None
                or self.evidence_fingerprint is None
                or self.provider_state_at is None
                or self.xeed_capacity is None
                or type(self.xeed_capacity) is not int
                or self.xeed_capacity < 1
                or type(self.base_quantity) is not int
                or type(self.additional_xeed_quantity) is not int
                or self.base_quantity != 1
                or self.additional_xeed_quantity != self.xeed_capacity - 1
            ):
                raise ValueError("verified binding requires complete positive binding facts")
        elif any(
            value is not None
            for value in (self.xeed_capacity, self.base_quantity, self.additional_xeed_quantity)
        ):
            raise ValueError("non-verified binding cannot carry a positive capacity")


@dataclass(frozen=True, slots=True)
class CurrentSubscriptionItems:
    """Provider-neutral complete/current subscription facts for later capacity changes.

    This is intentionally separate from `SubscriptionItemSnapshot`, which is
    bound to an initial Checkout Session. A subscription quantity update has no
    new Checkout Session to bind; it must be validated against the existing
    durable subscription/customer/environment association instead.
    """

    evidence_ref: str
    customer_ref: str
    subscription_ref: str
    environment_ref: str
    provider_state_ref: str | None
    provider_state_at: datetime | None
    retrieved_at: datetime
    currentness: SnapshotCurrentness
    enumeration_complete: bool | None
    has_more: bool | None
    items: tuple[NormalizedRecurringItem, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.evidence_ref, "evidence_ref"),
            (self.customer_ref, "customer_ref"),
            (self.subscription_ref, "subscription_ref"),
            (self.environment_ref, "environment_ref"),
        ):
            _text(value, name)
        if self.provider_state_ref is not None:
            _text(self.provider_state_ref, "provider_state_ref")
        _aware(self.retrieved_at, "retrieved_at")
        if self.provider_state_at is not None:
            _aware(self.provider_state_at, "provider_state_at")
        if type(self.currentness) is not SnapshotCurrentness:
            raise ValueError("currentness must use SnapshotCurrentness")
        if self.enumeration_complete is not None and type(self.enumeration_complete) is not bool:
            raise ValueError("enumeration_complete must be bool or None")
        if self.has_more is not None and type(self.has_more) is not bool:
            raise ValueError("has_more must be bool or None")
        if not isinstance(self.items, tuple):
            raise ValueError("items must be an immutable tuple")
