"""AO-09 event-sourced AXIGNAL customer account operations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise
from typing import Protocol

from application.xeed_access import AuthorizedXeed, AuthorizedXeedReader, TrustedRequestContext
from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_customer_accounts import (
    SELF_SERVICE_V1,
    AccountCohort,
    AccountEvent,
    AccountEventId,
    AccountEventKind,
    AccountId,
    AccountSnapshot,
    AccountStatus,
    AccountUser,
    AccountUserId,
    AccountUserRole,
    FunnelStage,
    PaymentVerificationState,
    PlanCode,
    SubscriptionId,
    SubscriptionStatus,
)
from domain.identity import XeedId


class AccountEventStore(Protocol):
    def append(self, event: AccountEvent) -> bool: ...
    def for_account(self, account_id: AccountId) -> tuple[AccountEvent, ...]: ...
    def all_events(self) -> tuple[AccountEvent, ...]: ...


def _required(event: AccountEvent, key: str) -> str:
    value = event.value(key)
    if value is None:
        raise ValueError(f"{event.kind.value} missing payload {key}")
    return value


def _int_value(event: AccountEvent, key: str) -> int:
    raw = _required(event, key)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{event.kind.value} invalid integer {key}") from exc


def replay_account(events: tuple[AccountEvent, ...]) -> AccountSnapshot:
    if not events:
        raise LookupError("account has no events")
    ordered = events
    if any(current.occurred_at < previous.occurred_at for previous, current in pairwise(ordered)):
        raise ValueError("account events must replay in append/temporal order")
    first = ordered[0]
    if first.kind is not AccountEventKind.ACCOUNT_SIGNED_UP:
        raise ValueError("first account event must be ACCOUNT_SIGNED_UP")

    account_id = first.account_id
    if any(event.account_id != account_id for event in ordered):
        raise ValueError("cannot replay events from multiple accounts")

    tenant_id = _required(first, "tenant_id")
    display_name = _required(first, "display_name")
    plan_code = PlanCode(_required(first, "plan_code"))
    plan_version = _required(first, "plan_version")
    status = AccountStatus.PENDING
    subscription_id: SubscriptionId | None = None
    subscription_status = SubscriptionStatus.PENDING
    xeed_capacity = _int_value(first, "xeed_capacity")
    entitled_xeeds: set[str] = set()
    users: dict[str, AccountUser] = {}
    funnel: dict[FunnelStage, datetime] = {FunnelStage.SIGNUP: first.occurred_at}
    support_refs: list[str] = []
    claim_review_refs: list[str] = []
    cancellation_reason: str | None = None
    payment_verification = PaymentVerificationState.EXTERNAL_PENDING

    for event in ordered[1:]:
        if event.kind is AccountEventKind.USER_ADDED:
            user_id = _required(event, "user_id")
            users[user_id] = AccountUser(
                user_id=AccountUserId(user_id),
                principal_id=_required(event, "principal_id"),
                role=AccountUserRole(_required(event, "role")),
                added_at=event.occurred_at,
            )
        elif event.kind is AccountEventKind.USER_REMOVED:
            users.pop(_required(event, "user_id"), None)
        elif event.kind is AccountEventKind.SUBSCRIPTION_ACTIVATED:
            subscription_id = SubscriptionId(_required(event, "subscription_id"))
            subscription_status = SubscriptionStatus.ACTIVE
            status = AccountStatus.ACTIVE
            xeed_capacity = _int_value(event, "xeed_capacity")
            payment_verification = PaymentVerificationState(
                _required(event, "payment_verification")
            )
        elif event.kind is AccountEventKind.PLAN_CHANGED:
            plan_code = PlanCode(_required(event, "plan_code"))
            plan_version = _required(event, "plan_version")
            new_capacity = _int_value(event, "xeed_capacity")
            if new_capacity < len(entitled_xeeds):
                raise ValueError("plan change cannot reduce capacity below active entitlements")
            xeed_capacity = new_capacity
        elif event.kind is AccountEventKind.XEED_ENTITLED:
            if (
                status is not AccountStatus.ACTIVE
                or subscription_status is not SubscriptionStatus.ACTIVE
            ):
                raise ValueError("Xeed entitlement requires active account and subscription")
            xeed_id = _required(event, "xeed_id")
            if xeed_id not in entitled_xeeds and len(entitled_xeeds) >= xeed_capacity:
                raise ValueError("Xeed entitlement exceeds account capacity")
            entitled_xeeds.add(xeed_id)
            funnel.setdefault(FunnelStage.XEED_PLANTED, event.occurred_at)
        elif event.kind is AccountEventKind.XEED_REVOKED:
            entitled_xeeds.discard(_required(event, "xeed_id"))
        elif event.kind is AccountEventKind.ACCOUNT_SUSPENDED:
            status = AccountStatus.SUSPENDED
            if subscription_status is SubscriptionStatus.ACTIVE:
                subscription_status = SubscriptionStatus.SUSPENDED
        elif event.kind is AccountEventKind.ACCOUNT_REACTIVATED:
            if subscription_id is None:
                raise ValueError("cannot reactivate account without subscription")
            status = AccountStatus.ACTIVE
            subscription_status = SubscriptionStatus.ACTIVE
        elif event.kind is AccountEventKind.SUBSCRIPTION_CANCELLED:
            status = AccountStatus.CANCELLED
            subscription_status = SubscriptionStatus.CANCELLED
            cancellation_reason = _required(event, "cancellation_reason")
            entitled_xeeds.clear()
        elif event.kind is AccountEventKind.FUNNEL_STAGE_RECORDED:
            stage = FunnelStage(_required(event, "stage"))
            funnel.setdefault(stage, event.occurred_at)
        elif event.kind is AccountEventKind.SUPPORT_REFERENCE_ADDED:
            reference = _required(event, "reference")
            if reference not in support_refs:
                support_refs.append(reference)
        elif event.kind is AccountEventKind.CLAIM_REVIEW_REFERENCE_ADDED:
            reference = _required(event, "reference")
            if reference not in claim_review_refs:
                claim_review_refs.append(reference)

    return AccountSnapshot(
        account_id=account_id,
        tenant_id=tenant_id,
        display_name=display_name,
        signup_at=first.occurred_at,
        status=status,
        plan_code=plan_code,
        plan_version=plan_version,
        subscription_id=subscription_id,
        subscription_status=subscription_status,
        xeed_capacity=xeed_capacity,
        entitled_xeed_ids=frozenset(entitled_xeeds),
        users=tuple(sorted(users.values(), key=lambda item: str(item.user_id))),
        funnel_stages=tuple(sorted(funnel.items(), key=lambda item: item[1])),
        support_refs=tuple(support_refs),
        claim_review_refs=tuple(claim_review_refs),
        cancellation_reason=cancellation_reason,
        payment_verification=payment_verification,
        event_count=len(ordered),
        last_event_at=ordered[-1].occurred_at,
    )


def _require_scope(grant: AdminAuthorizationGrant, scope: AdminScope) -> None:
    if scope not in grant.scopes:
        raise PermissionError(f"account operation requires {scope.value}")


def _payload(**values: object) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in values.items()))


class AdminCustomerAccountService:
    def __init__(self, store: AccountEventStore) -> None:
        self._store = store

    def _snapshot(self, account_id: str) -> AccountSnapshot:
        return replay_account(self._store.for_account(AccountId(account_id)))

    def _append(
        self,
        *,
        account_id: str,
        event_id: str,
        kind: AccountEventKind,
        grant: AdminAuthorizationGrant,
        now: datetime,
        reason: str,
        payload: tuple[tuple[str, str], ...],
    ) -> AccountEvent:
        event = AccountEvent(
            event_id=AccountEventId(event_id),
            account_id=AccountId(account_id),
            kind=kind,
            occurred_at=now,
            actor=str(grant.principal_id),
            reason=reason,
            payload=payload,
        )
        self._store.append(event)
        return event

    def signup(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        tenant_id: str,
        display_name: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        if self._store.for_account(AccountId(account_id)):
            raise ValueError("account already exists")
        if any(
            replay_account(events).tenant_id == tenant_id
            for events in _group_events(self._store.all_events()).values()
        ):
            raise ValueError("tenant already linked to an AXIGNAL account")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:signup",
            kind=AccountEventKind.ACCOUNT_SIGNED_UP,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(
                tenant_id=tenant_id,
                display_name=display_name,
                plan_code=PlanCode.SELF_SERVICE_V1.value,
                plan_version=SELF_SERVICE_V1.version,
                xeed_capacity=SELF_SERVICE_V1.included_xeeds,
            ),
        )
        return self._snapshot(account_id)

    def add_user(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        user_id: str,
        principal_id: str,
        role: AccountUserRole,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if any(user.user_id == user_id for user in snapshot.users):
            raise ValueError("account user already exists")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:user:add:{user_id}",
            kind=AccountEventKind.USER_ADDED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(user_id=user_id, principal_id=principal_id, role=role.value),
        )
        return self._snapshot(account_id)

    def activate_subscription(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        subscription_id: str,
        xeed_capacity: int,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if snapshot.status is AccountStatus.CANCELLED:
            raise ValueError("cancelled account cannot activate subscription")
        if snapshot.subscription_status is SubscriptionStatus.ACTIVE:
            raise ValueError("subscription already active")
        if xeed_capacity < 1:
            raise ValueError("Xeed capacity must be positive")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:subscription:activate:{subscription_id}",
            kind=AccountEventKind.SUBSCRIPTION_ACTIVATED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(
                subscription_id=subscription_id,
                xeed_capacity=xeed_capacity,
                payment_verification=PaymentVerificationState.EXTERNAL_PENDING.value,
            ),
        )
        return self._snapshot(account_id)

    def change_plan_capacity(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        xeed_capacity: int,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if snapshot.status is not AccountStatus.ACTIVE:
            raise ValueError("plan change requires active account")
        if xeed_capacity < len(snapshot.entitled_xeed_ids) or xeed_capacity < 1:
            raise ValueError("new Xeed capacity cannot invalidate active entitlements")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:plan:{xeed_capacity}:{now.isoformat()}",
            kind=AccountEventKind.PLAN_CHANGED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(
                plan_code=PlanCode.SELF_SERVICE_V1.value,
                plan_version=SELF_SERVICE_V1.version,
                xeed_capacity=xeed_capacity,
            ),
        )
        return self._snapshot(account_id)

    def entitle_xeed(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        xeed_id: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if (
            snapshot.status is not AccountStatus.ACTIVE
            or snapshot.subscription_status is not SubscriptionStatus.ACTIVE
        ):
            raise ValueError("Xeed entitlement requires active account/subscription")
        if xeed_id in snapshot.entitled_xeed_ids:
            return snapshot
        if len(snapshot.entitled_xeed_ids) >= snapshot.xeed_capacity:
            raise ValueError("Xeed capacity exhausted")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:xeed:entitle:{xeed_id}",
            kind=AccountEventKind.XEED_ENTITLED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(xeed_id=xeed_id),
        )
        return self._snapshot(account_id)

    def revoke_xeed(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        xeed_id: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        self._snapshot(account_id)
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:xeed:revoke:{xeed_id}:{now.isoformat()}",
            kind=AccountEventKind.XEED_REVOKED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(xeed_id=xeed_id),
        )
        return self._snapshot(account_id)

    def suspend(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if snapshot.status is not AccountStatus.ACTIVE:
            raise ValueError("only active accounts can be suspended")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:suspend:{now.isoformat()}",
            kind=AccountEventKind.ACCOUNT_SUSPENDED,
            grant=grant,
            now=now,
            reason=reason,
            payload=(),
        )
        return self._snapshot(account_id)

    def reactivate(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if snapshot.status is not AccountStatus.SUSPENDED:
            raise ValueError("only suspended accounts can be reactivated")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:reactivate:{now.isoformat()}",
            kind=AccountEventKind.ACCOUNT_REACTIVATED,
            grant=grant,
            now=now,
            reason=reason,
            payload=(),
        )
        return self._snapshot(account_id)

    def cancel(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        now: datetime,
        reason: str,
        cancellation_reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if snapshot.status is AccountStatus.CANCELLED:
            return snapshot
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:cancel:{now.isoformat()}",
            kind=AccountEventKind.SUBSCRIPTION_CANCELLED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(cancellation_reason=cancellation_reason),
        )
        return self._snapshot(account_id)

    def record_funnel_stage(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        stage: FunnelStage,
        definition_version: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        snapshot = self._snapshot(account_id)
        if any(existing is stage for existing, _ in snapshot.funnel_stages):
            return snapshot
        if stage is FunnelStage.PAID:
            raise ValueError("PAID stage is owned by AO-10 billing integration")
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:funnel:{stage.value}:{definition_version}",
            kind=AccountEventKind.FUNNEL_STAGE_RECORDED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(stage=stage.value, definition_version=definition_version),
        )
        return self._snapshot(account_id)

    def add_support_reference(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        reference: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.SUPPORT_WRITE)
        self._snapshot(account_id)
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:support:{reference}",
            kind=AccountEventKind.SUPPORT_REFERENCE_ADDED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(reference=reference),
        )
        return self._snapshot(account_id)

    def add_claim_review_reference(
        self,
        *,
        grant: AdminAuthorizationGrant,
        account_id: str,
        reference: str,
        now: datetime,
        reason: str,
    ) -> AccountSnapshot:
        _require_scope(grant, AdminScope.SUPPORT_WRITE)
        self._snapshot(account_id)
        self._append(
            account_id=account_id,
            event_id=f"account:{account_id}:claim-review:{reference}",
            kind=AccountEventKind.CLAIM_REVIEW_REFERENCE_ADDED,
            grant=grant,
            now=now,
            reason=reason,
            payload=_payload(reference=reference),
        )
        return self._snapshot(account_id)


def _group_events(events: tuple[AccountEvent, ...]) -> dict[AccountId, tuple[AccountEvent, ...]]:
    grouped: dict[AccountId, list[AccountEvent]] = defaultdict(list)
    for event in events:
        grouped[event.account_id].append(event)
    return {key: tuple(value) for key, value in grouped.items()}


@dataclass(frozen=True, slots=True)
class Customer360:
    account_id: str
    tenant_id: str
    display_name: str
    signup_at: datetime
    account_status: str
    subscription_status: str
    plan_code: str
    plan_version: str
    payment_state: str
    xeed_capacity: int
    active_xeed_count: int
    entitled_xeed_ids: tuple[str, ...]
    user_count: int
    funnel_stages: tuple[str, ...]
    support_refs: tuple[str, ...]
    claim_review_refs: tuple[str, ...]
    cancellation_reason: str | None
    mrr_eur: str | None
    pricing_hypothesis_monthly_eur: str
    event_count: int


@dataclass(frozen=True, slots=True)
class CustomerOperationsProjection:
    generated_at: datetime
    privacy_class: str
    account_count: int
    active_account_count: int
    suspended_account_count: int
    cancelled_account_count: int
    total_entitled_xeeds: int
    customers: tuple[Customer360, ...]
    cohorts: tuple[AccountCohort, ...]
    funnel_counts: tuple[tuple[str, int], ...]
    mrr_eur: str | None
    payment_authority: str
    coverage_notes: tuple[str, ...]


def _hypothesis_price(capacity: int) -> str:
    from decimal import Decimal

    base = Decimal(SELF_SERVICE_V1.base_monthly_eur)
    additional = Decimal(SELF_SERVICE_V1.additional_xeed_unit_eur)
    return str(base + additional * Decimal(max(0, capacity - SELF_SERVICE_V1.included_xeeds)))


def project_customer_operations(
    *,
    store: AccountEventStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> CustomerOperationsProjection:
    _require_scope(grant, AdminScope.CUSTOMERS_READ)
    snapshots = tuple(
        replay_account(events)
        for _, events in sorted(
            _group_events(store.all_events()).items(), key=lambda item: str(item[0])
        )
    )
    customers = tuple(
        Customer360(
            account_id=str(item.account_id),
            tenant_id=item.tenant_id,
            display_name=item.display_name,
            signup_at=item.signup_at,
            account_status=item.status.value,
            subscription_status=item.subscription_status.value,
            plan_code=item.plan_code.value,
            plan_version=item.plan_version,
            payment_state=item.payment_verification.value,
            xeed_capacity=item.xeed_capacity,
            active_xeed_count=len(item.entitled_xeed_ids),
            entitled_xeed_ids=tuple(sorted(item.entitled_xeed_ids)),
            user_count=len(item.users),
            funnel_stages=tuple(stage.value for stage, _ in item.funnel_stages),
            support_refs=item.support_refs,
            claim_review_refs=item.claim_review_refs,
            cancellation_reason=item.cancellation_reason,
            mrr_eur=None,
            pricing_hypothesis_monthly_eur=_hypothesis_price(item.xeed_capacity),
            event_count=item.event_count,
        )
        for item in snapshots
    )

    cohort_buckets: dict[str, list[AccountSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        cohort_buckets[snapshot.signup_at.strftime("%Y-%m")].append(snapshot)
    cohorts = tuple(
        AccountCohort(
            cohort_key=key,
            account_count=len(items),
            active_account_count=sum(item.status is AccountStatus.ACTIVE for item in items),
            cancelled_account_count=sum(item.status is AccountStatus.CANCELLED for item in items),
        )
        for key, items in sorted(cohort_buckets.items())
    )
    funnel_counts = tuple(
        (
            stage.value,
            sum(any(current is stage for current, _ in item.funnel_stages) for item in snapshots),
        )
        for stage in FunnelStage
    )

    return CustomerOperationsProjection(
        generated_at=generated_at,
        privacy_class="PRIVATE_FIRST_PARTY_SERVICE",
        account_count=len(snapshots),
        active_account_count=sum(item.status is AccountStatus.ACTIVE for item in snapshots),
        suspended_account_count=sum(item.status is AccountStatus.SUSPENDED for item in snapshots),
        cancelled_account_count=sum(item.status is AccountStatus.CANCELLED for item in snapshots),
        total_entitled_xeeds=sum(len(item.entitled_xeed_ids) for item in snapshots),
        customers=customers,
        cohorts=cohorts,
        funnel_counts=funnel_counts,
        mrr_eur=None,
        payment_authority="AO10_PENDING",
        coverage_notes=(
            "CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE.",
            "Subscription buys observation entitlement, never influence over AXIGLAND conclusions.",
            "MRR/payment state remain UNKNOWN until AO-10 billing evidence is integrated.",
            "Pricing displayed here is the current MASTER hypothesis, not measured revenue.",
            "Xeed entitlement is private service authority and does not own or duplicate the observed Organization.",
        ),
    )


class AccountByTenantReader(Protocol):
    def snapshot_for_tenant(self, tenant_id: str) -> AccountSnapshot | None: ...


class ServiceXeedAccessError(PermissionError):
    pass


class EntitledXeedReader:
    """Second server-side gate after identity/tenant/Xeed ownership authorization."""

    def __init__(self, base: AuthorizedXeedReader, accounts: AccountByTenantReader) -> None:
        self._base = base
        self._accounts = accounts

    def read(self, context: TrustedRequestContext | None, xeed_id: XeedId) -> AuthorizedXeed:
        authorized = self._base.read(context, xeed_id)
        if context is None:
            raise ServiceXeedAccessError("missing service account context")
        account = self._accounts.snapshot_for_tenant(str(context.tenant_id))
        if account is None:
            raise ServiceXeedAccessError("tenant has no AXIGNAL service account")
        if account.status is not AccountStatus.ACTIVE:
            raise ServiceXeedAccessError("AXIGNAL account is not active")
        if account.subscription_status is not SubscriptionStatus.ACTIVE:
            raise ServiceXeedAccessError("AXIGNAL subscription is not active")
        if str(xeed_id) not in account.entitled_xeed_ids:
            raise ServiceXeedAccessError("Xeed is not entitled for this account")
        return authorized
