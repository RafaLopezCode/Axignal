"""Subscriber checkout orchestration behind root-owned purchase authority."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from application.admin_billing.subscriber_billing import (
    PaymentState,
    PurchaseState,
    SubscriptionCapacityValidation,
    SubscriptionLifecycle,
    validate_subscription_capacity,
)
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedTaxConfiguration,
    CheckoutAttemptBinding,
    CurrentSubscriptionItems,
    PurchaseIntent,
    SubscriptionItemSnapshot,
)
from domain.identity import PrincipalId, TenantId
from domain.tenancy.model import Principal


class PurchaseFailure(StrEnum):
    INVALID_AUTHORITY = "INVALID_AUTHORITY"
    MEMBERSHIP_REVOKED = "MEMBERSHIP_REVOKED"
    PURCHASE_OWNER_UNKNOWN = "PURCHASE_OWNER_UNKNOWN"
    CATALOGUE_UNKNOWN = "CATALOGUE_UNKNOWN"
    TAX_CONFIGURATION_UNKNOWN = "TAX_CONFIGURATION_UNKNOWN"
    INITIAL_SUBSCRIPTION_EXISTS = "INITIAL_SUBSCRIPTION_EXISTS"
    BILLING_STATE_UNKNOWN = "BILLING_STATE_UNKNOWN"
    PAYMENT_NOT_CURRENT = "PAYMENT_NOT_CURRENT"
    UPDATE_ALREADY_PENDING = "UPDATE_ALREADY_PENDING"
    DESIRED_CAPACITY_NOT_HIGHER = "DESIRED_CAPACITY_NOT_HIGHER"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"


class SubscriberCheckoutError(RuntimeError):
    def __init__(self, failure: PurchaseFailure) -> None:
        self.failure = failure
        super().__init__(failure.value)


@dataclass(frozen=True, slots=True)
class AuthorizedPurchaseScope:
    """Result issued only by the injected identity/purchase-owner reader.

    The value contains no Stripe identity and cannot be made authoritative by
    strings from a client. The resolver must re-read current membership and
    bootstrap purchase ownership for every command.
    """

    principal_id: PrincipalId
    tenant_id: TenantId
    authority_ref: str
    membership_ref: str
    checked_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.principal_id, str) or not self.principal_id.strip():
            raise ValueError("purchase scope requires Principal identity")
        if not isinstance(self.tenant_id, str) or not self.tenant_id.strip():
            raise ValueError("purchase scope requires Tenant identity")
        if (
            not isinstance(self.authority_ref, str)
            or not self.authority_ref.strip()
            or not isinstance(self.membership_ref, str)
            or not self.membership_ref.strip()
        ):
            raise ValueError("purchase scope requires authority and membership evidence")
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("purchase authorization time must be timezone-aware")


class PurchaseAuthorityReader(Protocol):
    def resolve(
        self, principal: Principal, tenant_id: TenantId, *, now: datetime
    ) -> AuthorizedPurchaseScope | None: ...


class PurchaseScopeStore(Protocol):
    def is_purchase_owner(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool | None: ...


class PurchaseMembershipReader(Protocol):
    def get_principal(self, principal_id: PrincipalId) -> Principal | None: ...

    def has_membership(self, principal_id: PrincipalId, tenant_id: TenantId) -> bool: ...


class CurrentPurchaseAuthorityReader:
    """Resolve purchase authority from separate current membership and owner facts."""

    def __init__(self, memberships: PurchaseMembershipReader, owners: PurchaseScopeStore) -> None:
        self._memberships = memberships
        self._owners = owners

    def resolve(
        self, principal: Principal, tenant_id: TenantId, *, now: datetime
    ) -> AuthorizedPurchaseScope | None:
        persisted = self._memberships.get_principal(principal.id)
        if persisted is None or persisted.id != principal.id:
            return None
        if not self._memberships.has_membership(principal.id, tenant_id):
            return None
        if self._owners.is_purchase_owner(principal.id, tenant_id) is not True:
            return None
        identity = hashlib.sha256(f"{principal.id}:{tenant_id}".encode()).hexdigest()
        return AuthorizedPurchaseScope(
            principal_id=principal.id,
            tenant_id=tenant_id,
            authority_ref=f"purchase-owner-check:{identity}",
            membership_ref=f"membership-check:{identity}",
            checked_at=now,
        )


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    """Read-only Tenant entitlement snapshot; missing capacity stays None."""

    tenant_id: TenantId
    effective_capacity: int | None
    currentness: str
    evidence_ref: str | None
    paid_through: datetime | None

    def __post_init__(self) -> None:
        if self.effective_capacity is not None and (
            type(self.effective_capacity) is not int or self.effective_capacity < 0
        ):
            raise ValueError("known effective capacity must be a non-negative integer")
        if self.paid_through is not None and (
            self.paid_through.tzinfo is None or self.paid_through.utcoffset() is None
        ):
            raise ValueError("paid_through must be timezone-aware")


class EntitlementSnapshotReader(Protocol):
    def snapshot(self, tenant_id: TenantId) -> EntitlementSnapshot | None: ...


@dataclass(frozen=True, slots=True)
class InitialCheckoutCommand:
    request_ref: str
    desired_total: int

    def __post_init__(self) -> None:
        if not self.request_ref.strip() or len(self.request_ref) > 160:
            raise ValueError("request_ref must be bounded non-empty text")
        if type(self.desired_total) is not int or self.desired_total < 1:
            raise ValueError("desired_total must be a positive integer")


@dataclass(frozen=True, slots=True)
class CapacityIncreaseCommand:
    request_ref: str
    desired_total: int

    def __post_init__(self) -> None:
        if not self.request_ref.strip() or len(self.request_ref) > 160:
            raise ValueError("request_ref must be bounded non-empty text")
        if type(self.desired_total) is not int or self.desired_total < 1:
            raise ValueError("desired_total must be a positive integer")


class AttemptKind(StrEnum):
    INITIAL = "INITIAL"
    CAPACITY_CHANGE = "CAPACITY_CHANGE"


class AttemptStatus(StrEnum):
    PREPARED = "PREPARED"
    PROVIDER_PENDING = "PROVIDER_PENDING"
    PENDING_PURCHASE = "PENDING_PURCHASE"
    COMPLETE = "COMPLETE"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class BillingProjection:
    tenant_id: TenantId
    customer_ref: str
    subscription_ref: str
    checkout_session_ref: str
    environment_ref: str
    additional_item_ref: str | None
    effective_capacity: int | None
    payment_state: PaymentState
    lifecycle: SubscriptionLifecycle
    binding: SubscriptionCapacityValidation | None
    provider_state_ref: str | None
    provider_state_at: datetime | None
    paid_through: datetime | None
    verified_invoice_ref: str | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                self.customer_ref,
                self.subscription_ref,
                self.checkout_session_ref,
                self.environment_ref,
            )
        ):
            raise ValueError("billing projection requires provider references")
        if self.effective_capacity is not None and (
            type(self.effective_capacity) is not int or self.effective_capacity < 1
        ):
            raise ValueError("effective capacity must be a positive integer or UNKNOWN")
        for value in (self.provider_state_at, self.paid_through):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise ValueError("billing projection times must be timezone-aware")


@dataclass(frozen=True, slots=True)
class PurchaseAttempt:
    tenant_id: TenantId
    principal_id: PrincipalId
    authority_ref: str
    membership_ref: str
    request_ref: str
    intent_ref: str
    attempt_ref: str
    idempotency_key: str
    kind: AttemptKind
    desired_total: int
    previous_effective_capacity: int | None
    catalogue_ref: str
    catalogue_version: str
    environment_ref: str
    authorized_at: datetime
    status: AttemptStatus
    checkout_session_ref: str | None = None
    customer_ref: str | None = None
    subscription_ref: str | None = None
    additional_item_ref: str | None = None
    invoice_ref: str | None = None
    checkout_url: str | None = None
    payment_url: str | None = None

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                self.authority_ref,
                self.membership_ref,
                self.request_ref,
                self.intent_ref,
                self.attempt_ref,
                self.idempotency_key,
                self.catalogue_ref,
                self.catalogue_version,
                self.environment_ref,
            )
        ):
            raise ValueError("purchase attempt requires stable references")
        if len(self.request_ref) > 160 or len(self.idempotency_key) > 255:
            raise ValueError("purchase references exceed supported bounds")
        if type(self.desired_total) is not int or self.desired_total < 1:
            raise ValueError("desired capacity must be a positive integer")
        if self.previous_effective_capacity is not None and (
            type(self.previous_effective_capacity) is not int
            or self.previous_effective_capacity < 1
        ):
            raise ValueError("previous capacity must be positive or unknown")
        if self.authorized_at.tzinfo is None or self.authorized_at.utcoffset() is None:
            raise ValueError("purchase authorization time must be timezone-aware")
        if type(self.kind) is not AttemptKind or type(self.status) is not AttemptStatus:
            raise ValueError("purchase attempt state must use declared enums")


@dataclass(frozen=True, slots=True)
class CheckoutStartResult:
    status: PurchaseState
    request_ref: str
    intent_ref: str
    desired_capacity: int
    effective_capacity: int | None
    checkout_url: str | None
    payment_url: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class CapacityChangeResult:
    status: PurchaseState
    request_ref: str
    intent_ref: str
    desired_capacity: int
    effective_capacity: int | None
    pending_update: bool
    payment_url: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class PurchaseStatusResult:
    request_ref: str
    identity_scope: str
    binding: str
    payment: str
    subscription_lifecycle: str
    effective_capacity: int | None
    desired_capacity: int
    purchase: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreatedCheckoutSession:
    session_ref: str
    customer_ref: str | None
    subscription_ref: str | None
    redirect_url: str


@dataclass(frozen=True, slots=True)
class CapacityUpdateResponse:
    subscription_ref: str
    customer_ref: str
    additional_item_ref: str
    invoice_ref: str | None
    hosted_invoice_url: str | None
    pending_update: bool


class OfferCatalogueReader(Protocol):
    def resolve(self, environment_ref: str) -> ApprovedOfferCatalogue | None: ...


class SubscriberPurchaseStore(Protocol):
    def get_attempt(self, tenant_id: TenantId, request_ref: str) -> PurchaseAttempt | None: ...

    def get_billing_projection(self, tenant_id: TenantId) -> BillingProjection | None: ...

    def prepare_attempt(self, attempt: PurchaseAttempt) -> PurchaseAttempt: ...

    def record_initial_session(self, attempt: PurchaseAttempt) -> None: ...

    def record_capacity_update(self, attempt: PurchaseAttempt) -> None: ...

    def commit_billing_projection(self, projection: BillingProjection) -> None: ...

    def list_pending_attempts(
        self, tenant_id: TenantId, *, limit: int = 20
    ) -> tuple[PurchaseAttempt, ...]: ...

    def get_pending_capacity_change(
        self, tenant_id: TenantId, subscription_ref: str
    ) -> PurchaseAttempt | None: ...


class SubscriberBillingProvider(Protocol):
    def create_initial_checkout(
        self,
        intent: PurchaseIntent,
        catalogue: ApprovedOfferCatalogue,
        *,
        idempotency_key: str,
    ) -> CreatedCheckoutSession: ...

    def read_current_subscription(
        self, projection: BillingProjection
    ) -> ProviderCurrentSubscription: ...

    def read_checkout_binding(self, attempt: PurchaseAttempt) -> ProviderCheckoutBinding: ...

    def update_capacity(
        self,
        projection: BillingProjection,
        *,
        catalogue: ApprovedOfferCatalogue,
        desired_total: int,
        additional_item_ref: str | None,
        idempotency_key: str,
        proration_behavior: str,
        payment_behavior: str,
    ) -> CapacityUpdateResponse: ...


class SubscriberReconciler(Protocol):
    def reconcile_attempt(
        self, tenant_id: TenantId, request_ref: str, *, now: datetime
    ) -> StrEnum: ...

    def refresh_current_projection(self, tenant_id: TenantId, *, now: datetime) -> StrEnum: ...


@dataclass(frozen=True, slots=True)
class ProviderCurrentSubscription:
    snapshot: CurrentSubscriptionItems
    payment_state: PaymentState
    lifecycle: SubscriptionLifecycle
    paid_through: datetime | None
    additional_item_ref: str | None
    invoice_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderCheckoutBinding:
    binding: CheckoutAttemptBinding
    session_snapshot: SubscriptionItemSnapshot
    current_snapshot: CurrentSubscriptionItems
    payment_state: PaymentState
    lifecycle: SubscriptionLifecycle
    paid_through: datetime | None
    invoice_ref: str | None


class SubscriberReconciliationStore(SubscriberPurchaseStore, Protocol):
    def get_attempt_by_session(self, checkout_session_ref: str) -> PurchaseAttempt | None: ...

    def get_pending_attempt_by_subscription(
        self, subscription_ref: str
    ) -> PurchaseAttempt | None: ...

    def record_reconciled_purchase(
        self, attempt: PurchaseAttempt, projection: BillingProjection
    ) -> None: ...

    def list_pending_attempts(
        self, tenant_id: TenantId, *, limit: int = 20
    ) -> tuple[PurchaseAttempt, ...]: ...

    def list_all_pending_attempts(self, *, limit: int = 20) -> tuple[PurchaseAttempt, ...]: ...


class SubscriberCheckoutService:
    def __init__(
        self,
        *,
        authority_reader: PurchaseAuthorityReader,
        entitlement_reader: EntitlementSnapshotReader,
        catalogue_reader: OfferCatalogueReader,
        store: SubscriberPurchaseStore,
        provider: SubscriberBillingProvider,
        environment_ref: str,
        reconciler: SubscriberReconciler | None = None,
    ) -> None:
        if not environment_ref.strip():
            raise ValueError("provider environment is required")
        self._authority_reader = authority_reader
        self._entitlement_reader = entitlement_reader
        self._catalogue_reader = catalogue_reader
        self._store = store
        self._provider = provider
        self._environment_ref = environment_ref
        self._reconciler = reconciler

    def reconcile_pending(
        self, *, principal: Principal, tenant_id: TenantId, now: datetime
    ) -> tuple[str, ...]:
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
            or authority.checked_at > now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        if self._reconciler is None:
            return ()
        pending = self._store.list_pending_attempts(tenant_id, limit=20)
        outcomes: list[str] = []
        completed_pending = False
        for attempt in pending:
            retry_ref = f"reconcile:{attempt.intent_ref}"
            try:
                outcome = self._reconciler.reconcile_attempt(
                    tenant_id, attempt.request_ref, now=now
                )
            except Exception as exc:
                count = self._store.retry_attempt_count(retry_ref) + 1  # type: ignore[attr-defined]
                dead = count >= 8
                delay = min(60 * (2 ** min(count, 10)), 21_600)
                self._store.enqueue_retry(  # type: ignore[attr-defined]
                    operation_ref=retry_ref,
                    next_attempt_at=None if dead else now + timedelta(seconds=delay),
                    attempt_count=count,
                    disposition="DLQ" if dead else "RETRY",
                    failure_code=type(exc).__name__[:80],
                    safe_refs={"tenant_ref": str(tenant_id), "intent_ref": attempt.intent_ref},
                )
                outcomes.append("UNKNOWN")
                continue
            outcomes.append(outcome.value)
            if outcome.value == "COMPLETE":
                completed_pending = True
                self._store.enqueue_retry(  # type: ignore[attr-defined]
                    operation_ref=retry_ref,
                    next_attempt_at=None,
                    attempt_count=self._store.retry_attempt_count(retry_ref),  # type: ignore[attr-defined]
                    disposition="COMPLETE",
                    failure_code="NONE",
                    safe_refs={"tenant_ref": str(tenant_id), "intent_ref": attempt.intent_ref},
                )
        # Pending purchase reconciliation validates and persists the exact
        # current item snapshot for its immutable desired-capacity intent. A
        # subsequent general refresh must not first bind that same provider
        # evidence to the previously effective capacity. That would turn a
        # valid paid expansion into a conflicting replay. The completed
        # reconciliation itself is the authoritative refresh in this case.
        if not completed_pending:
            try:
                refresh = self._reconciler.refresh_current_projection(tenant_id, now=now)
                outcomes.append(refresh.value)
            except Exception:
                self._store.mark_projection_unknown(tenant_id)  # type: ignore[attr-defined]
                outcomes.append("UNKNOWN")
        return tuple(outcomes)

    def get_purchase_status(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        request_ref: str,
        now: datetime,
    ) -> PurchaseStatusResult:
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
        ):
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        if authority.checked_at > now:
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        attempt = self._store.get_attempt(tenant_id, request_ref)
        if attempt is None:
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        projection = self._store.get_billing_projection(tenant_id)
        effective_capacity = None if projection is None else projection.effective_capacity
        evidence_refs: list[str] = [authority.authority_ref, authority.membership_ref]
        binding = "UNKNOWN"
        payment = "UNKNOWN"
        lifecycle = "UNKNOWN"
        if projection is not None:
            payment = projection.payment_state.value
            lifecycle = projection.lifecycle.value
            if projection.binding is not None:
                binding = projection.binding.status.value
                if projection.binding.evidence_ref is not None:
                    evidence_refs.append(projection.binding.evidence_ref)
        return PurchaseStatusResult(
            request_ref=attempt.request_ref,
            identity_scope="VERIFIED",
            binding=binding,
            payment=payment,
            subscription_lifecycle=lifecycle,
            effective_capacity=effective_capacity,
            desired_capacity=attempt.desired_total,
            purchase=(
                PurchaseState.COMPLETE.value
                if attempt.status is AttemptStatus.COMPLETE
                else PurchaseState.PENDING_PURCHASE.value
                if attempt.status
                in (
                    AttemptStatus.PREPARED,
                    AttemptStatus.PROVIDER_PENDING,
                    AttemptStatus.PENDING_PURCHASE,
                )
                else PurchaseState.REJECTED.value
                if attempt.status is AttemptStatus.REJECTED
                else PurchaseState.UNKNOWN.value
            ),
            evidence_refs=tuple(evidence_refs),
        )

    def start_initial_checkout(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        command: InitialCheckoutCommand,
        now: datetime,
    ) -> CheckoutStartResult:
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
        ):
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        if authority.checked_at > now:
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        existing = self._store.get_attempt(tenant_id, command.request_ref)
        if existing is not None:
            if (
                existing.kind is AttemptKind.INITIAL
                and existing.status is AttemptStatus.PREPARED
                and existing.checkout_session_ref is None
            ):
                return self._submit_prepared_initial(
                    existing, principal=principal, tenant_id=tenant_id, now=now
                )
            return self._initial_result(existing)
        projection = self._store.get_billing_projection(tenant_id)
        if projection is not None:
            raise SubscriberCheckoutError(PurchaseFailure.INITIAL_SUBSCRIPTION_EXISTS)
        entitlement = self._entitlement_reader.snapshot(tenant_id)
        if entitlement is not None and entitlement.effective_capacity is None:
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        if (
            entitlement is not None
            and entitlement.effective_capacity is not None
            and entitlement.effective_capacity > 0
        ):
            raise SubscriberCheckoutError(PurchaseFailure.INITIAL_SUBSCRIPTION_EXISTS)
        catalogue = self._catalogue_reader.resolve(self._environment_ref)
        if catalogue is None:
            raise SubscriberCheckoutError(PurchaseFailure.CATALOGUE_UNKNOWN)
        _require_tax_configuration(catalogue.tax_configuration, self._environment_ref, now)
        attempt = self._store.prepare_attempt(
            PurchaseAttempt(
                tenant_id=tenant_id,
                principal_id=principal.id,
                authority_ref=authority.authority_ref,
                membership_ref=authority.membership_ref,
                request_ref=command.request_ref,
                intent_ref=f"intent:{uuid4().hex}",
                attempt_ref=f"attempt:{uuid4().hex}",
                idempotency_key=_idempotency_key("checkout", tenant_id, command.request_ref),
                kind=AttemptKind.INITIAL,
                desired_total=command.desired_total,
                previous_effective_capacity=None,
                catalogue_ref=catalogue.catalogue_ref,
                catalogue_version=catalogue.version,
                environment_ref=self._environment_ref,
                authorized_at=now,
                status=AttemptStatus.PREPARED,
            )
        )
        intent = PurchaseIntent(
            intent_ref=attempt.intent_ref,
            attempt_ref=attempt.attempt_ref,
            catalogue_ref=attempt.catalogue_ref,
            catalogue_version=attempt.catalogue_version,
            xeed_capacity=attempt.desired_total,
            environment_ref=attempt.environment_ref,
            authorized_at=attempt.authorized_at,
        )
        latest_authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            latest_authority is None
            or latest_authority.principal_id != principal.id
            or latest_authority.tenant_id != tenant_id
            or latest_authority.checked_at > now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.MEMBERSHIP_REVOKED)
        created = self._provider.create_initial_checkout(
            intent, catalogue, idempotency_key=attempt.idempotency_key
        )
        completed_attempt = replace(
            attempt,
            status=AttemptStatus.PENDING_PURCHASE,
            checkout_session_ref=created.session_ref,
            customer_ref=created.customer_ref,
            subscription_ref=created.subscription_ref,
            checkout_url=created.redirect_url,
        )
        self._store.record_initial_session(completed_attempt)
        return self._initial_result(completed_attempt)

    def request_capacity_increase(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        command: CapacityIncreaseCommand,
        now: datetime,
    ) -> CapacityChangeResult:
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
        ):
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        if authority.checked_at > now:
            raise SubscriberCheckoutError(PurchaseFailure.INVALID_AUTHORITY)
        existing = self._store.get_attempt(tenant_id, command.request_ref)
        if existing is not None:
            if (
                existing.kind is AttemptKind.CAPACITY_CHANGE
                and existing.status is AttemptStatus.PREPARED
            ):
                return self._submit_prepared_capacity_change(
                    existing, principal=principal, tenant_id=tenant_id, now=now
                )
            return self._capacity_result(existing)
        projection = self._store.get_billing_projection(tenant_id)
        if projection is not None:
            pending = self._store.get_pending_capacity_change(
                tenant_id, projection.subscription_ref
            )
            if pending is not None:
                if pending.desired_total == command.desired_total:
                    return self._capacity_result(pending)
                raise SubscriberCheckoutError(PurchaseFailure.UPDATE_ALREADY_PENDING)
        snapshot = self._entitlement_reader.snapshot(tenant_id)
        if (
            projection is None
            or snapshot is None
            or snapshot.tenant_id != tenant_id
            or snapshot.effective_capacity is None
            or projection.effective_capacity is None
            or snapshot.effective_capacity != projection.effective_capacity
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        if projection.payment_state is not PaymentState.VERIFIED:
            raise SubscriberCheckoutError(PurchaseFailure.PAYMENT_NOT_CURRENT)
        if projection.lifecycle is not SubscriptionLifecycle.ELIGIBLE:
            raise SubscriberCheckoutError(PurchaseFailure.PAYMENT_NOT_CURRENT)
        if (
            snapshot.currentness != "CURRENT"
            or snapshot.evidence_ref is None
            or snapshot.paid_through is None
            or snapshot.paid_through <= now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        if command.desired_total <= projection.effective_capacity:
            raise SubscriberCheckoutError(PurchaseFailure.DESIRED_CAPACITY_NOT_HIGHER)
        catalogue = self._catalogue_reader.resolve(self._environment_ref)
        if catalogue is None:
            raise SubscriberCheckoutError(PurchaseFailure.CATALOGUE_UNKNOWN)
        _require_tax_configuration(catalogue.tax_configuration, self._environment_ref, now)
        provider_current = self._provider.read_current_subscription(projection)
        validation = validate_subscription_capacity(
            expected_capacity=projection.effective_capacity,
            authorized_at=projection.provider_state_at or now,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=provider_current.snapshot,
            previous=projection.binding,
        )
        if (
            validation.status.value != "VERIFIED"
            or provider_current.payment_state is not PaymentState.VERIFIED
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        if provider_current.lifecycle is not SubscriptionLifecycle.ELIGIBLE:
            raise SubscriberCheckoutError(PurchaseFailure.PAYMENT_NOT_CURRENT)
        if provider_current.paid_through is None or provider_current.paid_through <= now:
            raise SubscriberCheckoutError(PurchaseFailure.PAYMENT_NOT_CURRENT)
        attempt = self._store.prepare_attempt(
            PurchaseAttempt(
                tenant_id=tenant_id,
                principal_id=principal.id,
                authority_ref=authority.authority_ref,
                membership_ref=authority.membership_ref,
                request_ref=command.request_ref,
                intent_ref=f"capacity:{uuid4().hex}",
                attempt_ref=f"capacity-attempt:{uuid4().hex}",
                idempotency_key=_idempotency_key(
                    "capacity", tenant_id, projection.subscription_ref, command.request_ref
                ),
                kind=AttemptKind.CAPACITY_CHANGE,
                desired_total=command.desired_total,
                previous_effective_capacity=projection.effective_capacity,
                catalogue_ref=catalogue.catalogue_ref,
                catalogue_version=catalogue.version,
                environment_ref=self._environment_ref,
                authorized_at=now,
                status=AttemptStatus.PREPARED,
                customer_ref=projection.customer_ref,
                subscription_ref=projection.subscription_ref,
                additional_item_ref=provider_current.additional_item_ref,
            )
        )
        latest_authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            latest_authority is None
            or latest_authority.principal_id != principal.id
            or latest_authority.tenant_id != tenant_id
            or latest_authority.checked_at > now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.MEMBERSHIP_REVOKED)
        latest_provider = self._provider.read_current_subscription(projection)
        latest_validation = validate_subscription_capacity(
            expected_capacity=projection.effective_capacity,
            authorized_at=projection.provider_state_at or now,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=latest_provider.snapshot,
            previous=validation,
        )
        if (
            latest_validation.status.value != "VERIFIED"
            or latest_validation.evidence_fingerprint != validation.evidence_fingerprint
            or latest_provider.payment_state is not PaymentState.VERIFIED
            or latest_provider.lifecycle is not SubscriptionLifecycle.ELIGIBLE
            or latest_provider.paid_through is None
            or latest_provider.paid_through <= now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        response = self._provider.update_capacity(
            projection,
            catalogue=catalogue,
            desired_total=attempt.desired_total,
            additional_item_ref=latest_provider.additional_item_ref,
            idempotency_key=attempt.idempotency_key,
            proration_behavior="always_invoice",
            payment_behavior="pending_if_incomplete",
        )
        pending_attempt = replace(
            attempt,
            status=AttemptStatus.PENDING_PURCHASE,
            customer_ref=response.customer_ref,
            subscription_ref=response.subscription_ref,
            additional_item_ref=response.additional_item_ref,
            invoice_ref=response.invoice_ref,
            payment_url=response.hosted_invoice_url,
        )
        self._store.record_capacity_update(pending_attempt)
        return self._capacity_result(pending_attempt)

    @staticmethod
    def _initial_result(attempt: PurchaseAttempt) -> CheckoutStartResult:
        return CheckoutStartResult(
            status=PurchaseState.PENDING_PURCHASE,
            request_ref=attempt.request_ref,
            intent_ref=attempt.intent_ref,
            desired_capacity=attempt.desired_total,
            effective_capacity=attempt.previous_effective_capacity,
            checkout_url=attempt.checkout_url,
            payment_url=attempt.payment_url,
            reason="AWAITING_CHECKOUT_AND_PAYMENT_RECONCILIATION",
        )

    @staticmethod
    def _capacity_result(attempt: PurchaseAttempt) -> CapacityChangeResult:
        return CapacityChangeResult(
            status=PurchaseState.PENDING_PURCHASE,
            request_ref=attempt.request_ref,
            intent_ref=attempt.intent_ref,
            desired_capacity=attempt.desired_total,
            effective_capacity=attempt.previous_effective_capacity,
            pending_update=attempt.status is AttemptStatus.PENDING_PURCHASE,
            payment_url=attempt.payment_url,
            reason="AWAITING_INVOICE_PAYMENT_AND_CURRENT_BINDING",
        )

    def _submit_prepared_initial(
        self,
        attempt: PurchaseAttempt,
        *,
        principal: Principal,
        tenant_id: TenantId,
        now: datetime,
    ) -> CheckoutStartResult:
        catalogue = self._catalogue_reader.resolve(attempt.environment_ref)
        if catalogue is None or (
            catalogue.catalogue_ref != attempt.catalogue_ref
            or catalogue.version != attempt.catalogue_version
        ):
            raise SubscriberCheckoutError(PurchaseFailure.CATALOGUE_UNKNOWN)
        _require_tax_configuration(catalogue.tax_configuration, self._environment_ref, now)
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
            or authority.checked_at > now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.MEMBERSHIP_REVOKED)
        created = self._provider.create_initial_checkout(
            PurchaseIntent(
                intent_ref=attempt.intent_ref,
                attempt_ref=attempt.attempt_ref,
                catalogue_ref=attempt.catalogue_ref,
                catalogue_version=attempt.catalogue_version,
                xeed_capacity=attempt.desired_total,
                environment_ref=attempt.environment_ref,
                authorized_at=attempt.authorized_at,
            ),
            catalogue,
            idempotency_key=attempt.idempotency_key,
        )
        persisted = replace(
            attempt,
            status=AttemptStatus.PENDING_PURCHASE,
            checkout_session_ref=created.session_ref,
            customer_ref=created.customer_ref,
            subscription_ref=created.subscription_ref,
            checkout_url=created.redirect_url,
        )
        self._store.record_initial_session(persisted)
        return self._initial_result(persisted)

    def _submit_prepared_capacity_change(
        self,
        attempt: PurchaseAttempt,
        *,
        principal: Principal,
        tenant_id: TenantId,
        now: datetime,
    ) -> CapacityChangeResult:
        projection = self._store.get_billing_projection(tenant_id)
        authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            authority is None
            or authority.principal_id != principal.id
            or authority.tenant_id != tenant_id
        ):
            raise SubscriberCheckoutError(PurchaseFailure.MEMBERSHIP_REVOKED)
        if projection is None or projection.subscription_ref != attempt.subscription_ref:
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        catalogue = self._catalogue_reader.resolve(attempt.environment_ref)
        if catalogue is None or (
            catalogue.catalogue_ref != attempt.catalogue_ref
            or catalogue.version != attempt.catalogue_version
        ):
            raise SubscriberCheckoutError(PurchaseFailure.CATALOGUE_UNKNOWN)
        _require_tax_configuration(catalogue.tax_configuration, self._environment_ref, now)
        current = self._provider.read_current_subscription(projection)
        validation = validate_subscription_capacity(
            expected_capacity=attempt.previous_effective_capacity,
            authorized_at=projection.provider_state_at or attempt.authorized_at,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=current.snapshot,
            previous=projection.binding,
        )
        if (
            validation.status.value != "VERIFIED"
            or current.payment_state is not PaymentState.VERIFIED
            or current.lifecycle is not SubscriptionLifecycle.ELIGIBLE
            or current.paid_through is None
            or current.paid_through <= now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        latest_authority = self._authority_reader.resolve(principal, tenant_id, now=now)
        if (
            latest_authority is None
            or latest_authority.principal_id != principal.id
            or latest_authority.tenant_id != tenant_id
            or latest_authority.checked_at > now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.MEMBERSHIP_REVOKED)
        latest = self._provider.read_current_subscription(projection)
        latest_validation = validate_subscription_capacity(
            expected_capacity=attempt.previous_effective_capacity,
            authorized_at=projection.provider_state_at or attempt.authorized_at,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=latest.snapshot,
            previous=validation,
        )
        if (
            latest_validation.status.value != "VERIFIED"
            or latest_validation.evidence_fingerprint != validation.evidence_fingerprint
            or latest.payment_state is not PaymentState.VERIFIED
            or latest.lifecycle is not SubscriptionLifecycle.ELIGIBLE
            or latest.paid_through is None
            or latest.paid_through <= now
        ):
            raise SubscriberCheckoutError(PurchaseFailure.BILLING_STATE_UNKNOWN)
        response = self._provider.update_capacity(
            projection,
            catalogue=catalogue,
            desired_total=attempt.desired_total,
            additional_item_ref=latest.additional_item_ref,
            idempotency_key=attempt.idempotency_key,
            proration_behavior="always_invoice",
            payment_behavior="pending_if_incomplete",
        )
        persisted = replace(
            attempt,
            status=AttemptStatus.PENDING_PURCHASE,
            customer_ref=response.customer_ref,
            subscription_ref=response.subscription_ref,
            additional_item_ref=response.additional_item_ref,
            invoice_ref=response.invoice_ref,
            payment_url=response.hosted_invoice_url,
        )
        self._store.record_capacity_update(persisted)
        return self._capacity_result(persisted)


def _idempotency_key(*parts: object) -> str:
    canonical = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"axignal:subscriber:{digest}"


def _require_tax_configuration(
    tax_configuration: ApprovedTaxConfiguration | None,
    environment_ref: str,
    now: datetime,
) -> None:
    if tax_configuration is None or not tax_configuration.is_current(environment_ref, now):
        raise SubscriberCheckoutError(PurchaseFailure.TAX_CONFIGURATION_UNKNOWN)
