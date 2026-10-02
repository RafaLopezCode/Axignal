"""AO-09 AXIGNAL customer account, subscription and entitlement domain.

This domain owns AXIGNAL service-account state only. It is intentionally
separate from AXIGLAND Organization identity and from Stripe/payment authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

AccountId = NewType("AccountId", str)
AccountUserId = NewType("AccountUserId", str)
SubscriptionId = NewType("SubscriptionId", str)
AccountEventId = NewType("AccountEventId", str)


class AccountStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class SubscriptionStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class AccountUserRole(StrEnum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class PlanCode(StrEnum):
    SELF_SERVICE_V1 = "SELF_SERVICE_V1"


class PaymentVerificationState(StrEnum):
    EXTERNAL_PENDING = "EXTERNAL_PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class FunnelStage(StrEnum):
    SIGNUP = "SIGNUP"
    XEED_PLANTED = "XEED_PLANTED"
    GERMINATION_COMPLETE = "GERMINATION_COMPLETE"
    FIRST_MAP_VIEWED = "FIRST_MAP_VIEWED"
    FIRST_INXIGHT_VIEWED = "FIRST_INXIGHT_VIEWED"
    EVIDENCE_INSPECTED = "EVIDENCE_INSPECTED"
    ACTIVATED = "ACTIVATED"
    PAID = "PAID"
    RETAINED = "RETAINED"
    EXPANDED = "EXPANDED"


class AccountEventKind(StrEnum):
    ACCOUNT_SIGNED_UP = "ACCOUNT_SIGNED_UP"
    USER_ADDED = "USER_ADDED"
    USER_REMOVED = "USER_REMOVED"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED"
    BILLING_SUBSCRIPTION_LINKED = "BILLING_SUBSCRIPTION_LINKED"
    PLAN_CHANGED = "PLAN_CHANGED"
    BILLING_PAYMENT_VERIFIED = "BILLING_PAYMENT_VERIFIED"
    BILLING_PAYMENT_FAILED = "BILLING_PAYMENT_FAILED"
    BILLING_CAPACITY_SYNCED = "BILLING_CAPACITY_SYNCED"
    XEED_ENTITLED = "XEED_ENTITLED"
    XEED_REVOKED = "XEED_REVOKED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"
    ACCOUNT_REACTIVATED = "ACCOUNT_REACTIVATED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    FUNNEL_STAGE_RECORDED = "FUNNEL_STAGE_RECORDED"
    SUPPORT_REFERENCE_ADDED = "SUPPORT_REFERENCE_ADDED"
    CLAIM_REVIEW_REFERENCE_ADDED = "CLAIM_REVIEW_REFERENCE_ADDED"


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class PlanDefinition:
    code: PlanCode
    included_xeeds: int
    additional_xeed_unit_eur: str
    base_monthly_eur: str
    pricing_hypothesis: bool
    version: str

    def __post_init__(self) -> None:
        if self.included_xeeds < 1:
            raise ValueError("plan must include at least one Xeed")
        for value, name in (
            (self.additional_xeed_unit_eur, "additional Xeed unit"),
            (self.base_monthly_eur, "base monthly"),
            (self.version, "plan version"),
        ):
            _text(value, name)


SELF_SERVICE_V1 = PlanDefinition(
    code=PlanCode.SELF_SERVICE_V1,
    included_xeeds=1,
    additional_xeed_unit_eur="4.95",
    base_monthly_eur="9.95",
    pricing_hypothesis=True,
    version="MASTER-27-v1",
)


@dataclass(frozen=True, slots=True)
class AccountUser:
    user_id: AccountUserId
    principal_id: str
    role: AccountUserRole
    added_at: datetime

    def __post_init__(self) -> None:
        _text(self.user_id, "account user id")
        _text(self.principal_id, "principal id")
        _aware(self.added_at, "added_at")


@dataclass(frozen=True, slots=True)
class AccountEvent:
    event_id: AccountEventId
    account_id: AccountId
    kind: AccountEventKind
    occurred_at: datetime
    actor: str
    reason: str
    payload: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        _text(self.event_id, "account event id")
        _text(self.account_id, "account id")
        _text(self.actor, "actor")
        _text(self.reason, "reason")
        _aware(self.occurred_at, "occurred_at")
        keys = [key for key, _ in self.payload]
        if len(keys) != len(set(keys)):
            raise ValueError("account event payload keys must be unique")
        for key, value in self.payload:
            _text(key, "payload key")
            _text(value, f"payload value for {key}")

    def value(self, key: str) -> str | None:
        for candidate, value in self.payload:
            if candidate == key:
                return value
        return None


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    account_id: AccountId
    tenant_id: str
    display_name: str
    signup_at: datetime
    status: AccountStatus
    plan_code: PlanCode
    plan_version: str
    subscription_id: SubscriptionId | None
    subscription_status: SubscriptionStatus
    xeed_capacity: int
    entitled_xeed_ids: frozenset[str]
    users: tuple[AccountUser, ...]
    funnel_stages: tuple[tuple[FunnelStage, datetime], ...]
    support_refs: tuple[str, ...]
    claim_review_refs: tuple[str, ...]
    cancellation_reason: str | None
    payment_verification: PaymentVerificationState
    event_count: int
    last_event_at: datetime

    def __post_init__(self) -> None:
        _text(self.account_id, "account id")
        _text(self.tenant_id, "tenant id")
        _text(self.display_name, "display name")
        _text(self.plan_version, "plan version")
        _aware(self.signup_at, "signup_at")
        _aware(self.last_event_at, "last_event_at")
        if self.xeed_capacity < 1:
            raise ValueError("Xeed capacity must be positive")
        if len(self.entitled_xeed_ids) > self.xeed_capacity:
            raise ValueError("entitled Xeeds cannot exceed capacity")
        if self.subscription_status is SubscriptionStatus.ACTIVE and self.subscription_id is None:
            raise ValueError("active subscription requires subscription id")
        if (
            self.status is AccountStatus.CANCELLED
            and self.subscription_status is not SubscriptionStatus.CANCELLED
        ):
            raise ValueError("cancelled account requires cancelled subscription")


@dataclass(frozen=True, slots=True)
class AccountCohort:
    cohort_key: str
    account_count: int
    active_account_count: int
    cancelled_account_count: int

    def __post_init__(self) -> None:
        _text(self.cohort_key, "cohort key")
        if min(self.account_count, self.active_account_count, self.cancelled_account_count) < 0:
            raise ValueError("cohort counts cannot be negative")
