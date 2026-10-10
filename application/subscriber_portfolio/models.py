"""Private subscriber portfolio values; Organization truth remains global."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from application.subscriber_identity.runtime import TrustedSubscriberContext
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.xeed.model import Xeed


class FocusStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REMOVED = "REMOVED"


class AddStatus(StrEnum):
    CREATED = "CREATED"
    ALREADY_PRESENT = "ALREADY_PRESENT"
    IDENTITY_PENDING = "IDENTITY_PENDING"
    IDENTITY_REJECTED = "IDENTITY_REJECTED"
    CHECKOUT_REQUIRED = "CHECKOUT_REQUIRED"
    CAPACITY_UNKNOWN = "CAPACITY_UNKNOWN"
    ACCESS_DENIED = "ACCESS_DENIED"
    # Staff-operated add only: the tenant's capacity is full; staff grants capacity, never sells it.
    CAPACITY_REQUIRED = "CAPACITY_REQUIRED"


class PendingStatus(StrEnum):
    IDENTITY_PENDING = "IDENTITY_PENDING"
    IDENTITY_REJECTED = "IDENTITY_REJECTED"
    CAPACITY_UNKNOWN = "CAPACITY_UNKNOWN"
    CAPACITY_PENDING = "CAPACITY_PENDING"
    PURCHASE_AUTHORITY_REQUIRED = "PURCHASE_AUTHORITY_REQUIRED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class PortfolioFailure(StrEnum):
    ACCESS_DENIED = "ACCESS_DENIED"
    INVALID_COMMAND = "INVALID_COMMAND"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    FOCUS_NOT_FOUND = "FOCUS_NOT_FOUND"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    CAPACITY_UNKNOWN = "CAPACITY_UNKNOWN"
    ORGANIZATION_INVALID = "ORGANIZATION_INVALID"
    IDENTITY_PENDING = "IDENTITY_PENDING"
    IDENTITY_REJECTED = "IDENTITY_REJECTED"
    CHECKOUT_NOT_AUTHORIZED = "CHECKOUT_NOT_AUTHORIZED"


class PortfolioError(Exception):
    def __init__(self, failure: PortfolioFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True, slots=True)
class AddOrganizationRequest:
    idempotency_key: str
    locator: str
    display_label: str | None = None

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip() or len(self.idempotency_key) > 160:
            raise ValueError("idempotency key must be bounded non-empty text")
        if not self.locator.strip() or len(self.locator) > 2048:
            raise ValueError("Organization locator must be bounded non-empty text")
        if self.display_label is not None and (
            not self.display_label.strip() or len(self.display_label) > 240
        ):
            raise ValueError("display label must be bounded non-empty text")


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    capacity: int | None
    currentness: Currentness
    confirmed_at: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(self.currentness, Currentness):
            raise ValueError("entitlement currentness must use Currentness")
        if self.capacity is not None and (type(self.capacity) is not int or self.capacity < 0):
            raise ValueError("confirmed capacity must be a non-negative integer")
        if self.confirmed_at is not None and (
            self.confirmed_at.tzinfo is None or self.confirmed_at.utcoffset() is None
        ):
            raise ValueError("entitlement confirmation time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class PurchaseScopeAuthorization:
    principal_id: str
    tenant_id: str
    authority_ref: str
    membership_ref: str
    checked_at: datetime

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.principal_id,
                self.tenant_id,
                self.authority_ref,
                self.membership_ref,
            )
        ):
            raise ValueError("purchase scope authorization requires identity references")
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("purchase scope authorization time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class CheckoutRequestResult:
    request_ref: str | None
    accepted: bool
    safe_status: str


@dataclass(frozen=True, slots=True)
class OrganizationIdentityPending:
    reason_code: str


@dataclass(frozen=True, slots=True)
class OrganizationIdentityRejected:
    reason_code: str


OrganizationResolution = Organization | OrganizationIdentityPending | OrganizationIdentityRejected


@dataclass(frozen=True, slots=True)
class PortfolioEntry:
    xeed: Xeed
    status: FocusStatus
    created_at: datetime
    updated_at: datetime

    @property
    def focus_id(self) -> XeedId:
        return self.xeed.id


@dataclass(frozen=True, slots=True)
class PendingAttentionEntry:
    pending_id: str
    tenant_id: TenantId
    locator: str
    idempotency_key: str = field(repr=False)
    created_at: datetime
    updated_at: datetime
    display_label: str | None = None
    status: PendingStatus = PendingStatus.IDENTITY_PENDING
    organization_id: None = None
    #: Why identity is still unresolved (UNKNOWN, AMBIGUOUS, CONFLICT…); never input text.
    identity_reason: str | None = None

    @property
    def focus_id(self) -> str:
        return self.pending_id

    @property
    def state(self) -> str:
        return self.status.value


@dataclass(frozen=True, slots=True)
class AddResult:
    status: AddStatus
    entry: PortfolioEntry | None = None
    checkout: CheckoutRequestResult | None = None
    identity_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PortfolioCommandResult:
    entry: PortfolioEntry
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class ReplaceResult:
    entry: PortfolioEntry
    previous_organization_id: OrganizationId
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class ObservationRunResult:
    focus_id: XeedId
    run_id: str
    accepted: bool
    status: str


@dataclass(frozen=True, slots=True)
class CapacityCheckoutRequest:
    context: TrustedSubscriberContext
    authorization: PurchaseScopeAuthorization
    current_capacity: int
    additional_count: int
    idempotency_key: str

    def __post_init__(self) -> None:
        if (
            self.authorization.principal_id != self.context.principal_id
            or self.authorization.tenant_id != self.context.tenant_id
        ):
            raise ValueError("checkout authority must match trusted subscriber context")
        if type(self.current_capacity) is not int or self.current_capacity < 0:
            raise ValueError("current capacity must be a known non-negative integer")
        if type(self.additional_count) is not int or self.additional_count <= 0:
            raise ValueError("capacity checkout addition must be positive")
        if not self.idempotency_key.strip() or len(self.idempotency_key) > 160:
            raise ValueError("checkout idempotency key must be bounded non-empty text")

    @property
    def tenant_id(self) -> TenantId:
        return self.context.tenant_id

    @property
    def desired_capacity(self) -> int:
        return self.current_capacity + self.additional_count
