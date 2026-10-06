"""Membership-first private Organization Focus portfolio policy."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Protocol

from application.subscriber_identity.runtime import (
    Clock,
    PrincipalTenantMembershipReader,
    TrustedSubscriberContext,
)
from application.subscriber_portfolio.models import (
    AddOrganizationRequest,
    AddResult,
    AddStatus,
    CapacityCheckoutRequest,
    CheckoutRequestResult,
    EntitlementSnapshot,
    FocusStatus,
    ObservationRunResult,
    OrganizationIdentityPending,
    OrganizationIdentityRejected,
    OrganizationResolution,
    PendingAttentionEntry,
    PendingStatus,
    PortfolioCommandResult,
    PortfolioEntry,
    PortfolioError,
    PortfolioFailure,
    PurchaseScopeAuthorization,
    ReplaceResult,
)
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.xeed.model import Xeed


class EntitlementPort(Protocol):
    def snapshot(self, tenant_id: TenantId) -> EntitlementSnapshot | None: ...


class PurchaseAuthorityPort(Protocol):
    def resolve(
        self,
        context: TrustedSubscriberContext,
        now: datetime,
    ) -> PurchaseScopeAuthorization | None: ...


class CapacityCheckoutPort(Protocol):
    def request_checkout(self, request: CapacityCheckoutRequest) -> CheckoutRequestResult: ...


class OrganizationResolutionPort(Protocol):
    def resolve(self, locator: str) -> OrganizationResolution: ...


class ObservationTriggerPort(Protocol):
    def trigger(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> str: ...


class SubscriberPortfolioStore(Protocol):
    def list_authorized(self, context: TrustedSubscriberContext) -> tuple[PortfolioEntry, ...]: ...

    def get_authorized(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
    ) -> PortfolioEntry | None: ...

    def get_xeed(self, focus_id: XeedId) -> Xeed | None: ...

    def record_pending(
        self,
        context: TrustedSubscriberContext,
        request: AddOrganizationRequest,
        now: datetime,
    ) -> None: ...

    def list_pending_authorized(
        self,
        context: TrustedSubscriberContext,
    ) -> tuple[PendingAttentionEntry, ...]: ...

    def get_pending_authorized(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
    ) -> PendingAttentionEntry | None: ...

    def cancel_pending(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
        idempotency_key: str,
        now: datetime,
    ) -> PendingAttentionEntry: ...

    def mark_pending_status(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
        status: PendingStatus,
        now: datetime,
    ) -> PendingAttentionEntry: ...

    def add_if_capacity(
        self,
        context: TrustedSubscriberContext,
        organization: Organization,
        capacity: int,
        request: AddOrganizationRequest,
        now: datetime,
    ) -> tuple[PortfolioEntry | None, bool]: ...

    def transition(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        operation: str,
        idempotency_key: str,
        now: datetime,
        capacity: int | None = None,
    ) -> PortfolioEntry: ...

    def replace_organization(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        organization_id: OrganizationId,
        idempotency_key: str,
        now: datetime,
    ) -> tuple[PortfolioEntry, OrganizationId, bool]: ...


class SubscriberPortfolioService:
    """Private portfolio service; locators never become canonical identities."""

    def __init__(
        self,
        portfolio: SubscriberPortfolioStore,
        memberships: PrincipalTenantMembershipReader,
        entitlement: EntitlementPort,
        purchase_authority: PurchaseAuthorityPort,
        checkout: CapacityCheckoutPort,
        organization_resolution: OrganizationResolutionPort,
        observation_trigger: ObservationTriggerPort,
        clock: Clock,
    ) -> None:
        self._portfolio = portfolio
        self._memberships = memberships
        self._entitlement = entitlement
        self._purchase_authority = purchase_authority
        self._checkout = checkout
        self._organizations = organization_resolution
        self._observation = observation_trigger
        self._clock = clock

    def _authorize(self, context: TrustedSubscriberContext) -> None:
        principal = self._memberships.get_principal(context.principal_id)
        if principal is None or not self._memberships.has_membership(
            context.principal_id, context.tenant_id
        ):
            raise PortfolioError(PortfolioFailure.ACCESS_DENIED)

    def list(self, context: TrustedSubscriberContext) -> tuple[PortfolioEntry, ...]:
        self._authorize(context)
        return self._portfolio.list_authorized(context)

    def list_pending(self, context: TrustedSubscriberContext) -> tuple[PendingAttentionEntry, ...]:
        self._authorize(context)
        return self._portfolio.list_pending_authorized(context)

    def cancel_pending(
        self,
        context: TrustedSubscriberContext,
        pending_id: str,
        idempotency_key: str,
    ) -> PendingAttentionEntry:
        self._authorize(context)
        return self._portfolio.cancel_pending(
            context,
            pending_id,
            idempotency_key,
            self._clock.now(),
        )

    def retry_pending(self, context: TrustedSubscriberContext, pending_id: str) -> AddResult:
        self._authorize(context)
        pending = self._portfolio.get_pending_authorized(context, pending_id)
        if pending is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        result = self.add(
            context,
            AddOrganizationRequest(
                pending.idempotency_key,
                pending.locator,
                pending.display_label,
            ),
        )
        status_map = {
            AddStatus.IDENTITY_REJECTED: PendingStatus.IDENTITY_REJECTED,
            AddStatus.CAPACITY_UNKNOWN: PendingStatus.CAPACITY_UNKNOWN,
            AddStatus.CHECKOUT_REQUIRED: PendingStatus.CAPACITY_PENDING,
            AddStatus.ACCESS_DENIED: PendingStatus.PURCHASE_AUTHORITY_REQUIRED,
        }
        pending_status = status_map.get(result.status)
        if pending_status is not None:
            self._portfolio.mark_pending_status(
                context,
                pending_id,
                pending_status,
                self._clock.now(),
            )
        return result

    def add(self, context: TrustedSubscriberContext, request: AddOrganizationRequest) -> AddResult:
        self._authorize(context)
        now = self._clock.now()
        snapshot = self._entitlement.snapshot(context.tenant_id)
        if (
            snapshot is None
            or snapshot.capacity is None
            or snapshot.currentness is not Currentness.CURRENT
            or snapshot.confirmed_at is None
            or snapshot.confirmed_at > now
        ):
            return AddResult(AddStatus.CAPACITY_UNKNOWN)

        resolved = self._organizations.resolve(request.locator)
        if isinstance(resolved, OrganizationIdentityPending):
            self._portfolio.record_pending(context, request, now)
            return AddResult(AddStatus.IDENTITY_PENDING, identity_reason=resolved.reason_code)
        if isinstance(resolved, OrganizationIdentityRejected):
            return AddResult(AddStatus.IDENTITY_REJECTED, identity_reason=resolved.reason_code)
        if not isinstance(resolved, Organization):
            raise PortfolioError(PortfolioFailure.ORGANIZATION_INVALID)

        entry, created = self._portfolio.add_if_capacity(
            context,
            resolved,
            snapshot.capacity,
            request,
            now,
        )
        if entry is None:
            current_entries = self._portfolio.list_authorized(context)
            current_used = sum(
                value.status in (FocusStatus.ACTIVE, FocusStatus.PAUSED)
                for value in current_entries
            )
            return self._request_capacity(
                context,
                request,
                self._clock.now(),
                max(1, current_used + 1 - snapshot.capacity),
                snapshot.capacity,
            )
        if created:
            self._observation.trigger(context, entry.focus_id, request.idempotency_key)
            return AddResult(AddStatus.CREATED, entry)
        return AddResult(AddStatus.ALREADY_PRESENT, entry)

    def _request_capacity(
        self,
        context: TrustedSubscriberContext,
        request: AddOrganizationRequest,
        now: datetime,
        additional_count: int,
        current_capacity: int,
    ) -> AddResult:
        self._authorize(context)
        authorization = self._purchase_authority.resolve(context, now)
        if (
            authorization is None
            or authorization.principal_id != context.principal_id
            or authorization.tenant_id != context.tenant_id
            or authorization.checked_at > now
            or now - authorization.checked_at > timedelta(seconds=60)
            or not authorization.authority_ref.strip()
            or not authorization.membership_ref.strip()
        ):
            return AddResult(AddStatus.ACCESS_DENIED)
        checkout = self._checkout.request_checkout(
            CapacityCheckoutRequest(
                context,
                authorization,
                current_capacity,
                additional_count,
                request.idempotency_key,
            )
        )
        return AddResult(AddStatus.CHECKOUT_REQUIRED, checkout=checkout)

    def pause(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> PortfolioCommandResult:
        self._authorize(context)
        entry = self._portfolio.transition(
            context, focus_id, "PAUSE", idempotency_key, self._clock.now()
        )
        return PortfolioCommandResult(entry)

    def resume(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> PortfolioCommandResult:
        self._authorize(context)
        snapshot = self._entitlement.snapshot(context.tenant_id)
        if (
            snapshot is None
            or snapshot.capacity is None
            or snapshot.currentness is not Currentness.CURRENT
            or snapshot.confirmed_at is None
            or snapshot.confirmed_at > self._clock.now()
        ):
            raise PortfolioError(PortfolioFailure.CAPACITY_UNKNOWN)
        entry = self._portfolio.transition(
            context, focus_id, "RESUME", idempotency_key, self._clock.now(), snapshot.capacity
        )
        return PortfolioCommandResult(entry)

    def remove(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> PortfolioCommandResult:
        self._authorize(context)
        entry = self._portfolio.transition(
            context, focus_id, "REMOVE", idempotency_key, self._clock.now()
        )
        return PortfolioCommandResult(entry)

    def replace(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        target: AddOrganizationRequest,
        idempotency_key: str,
    ) -> ReplaceResult:
        self._authorize(context)
        resolved = self._organizations.resolve(target.locator)
        if isinstance(resolved, OrganizationIdentityPending):
            raise PortfolioError(PortfolioFailure.IDENTITY_PENDING)
        if isinstance(resolved, OrganizationIdentityRejected):
            raise PortfolioError(PortfolioFailure.IDENTITY_REJECTED)
        if not isinstance(resolved, Organization):
            raise PortfolioError(PortfolioFailure.ORGANIZATION_INVALID)
        entry, previous_organization_id, replayed = self._portfolio.replace_organization(
            context,
            focus_id,
            resolved.id,
            idempotency_key,
            self._clock.now(),
        )
        if not replayed:
            self._observation.trigger(context, focus_id, idempotency_key)
        return ReplaceResult(entry, previous_organization_id, replayed)

    def reobserve(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> ObservationRunResult:
        self._authorize(context)
        entry = self._portfolio.get_authorized(context, focus_id)
        if entry is None:
            raise PortfolioError(PortfolioFailure.FOCUS_NOT_FOUND)
        if entry.status is not FocusStatus.ACTIVE:
            raise PortfolioError(PortfolioFailure.INVALID_TRANSITION)
        run_id = self._observation.trigger(context, focus_id, idempotency_key)
        return ObservationRunResult(focus_id, run_id, True, "ACCEPTED")


__all__ = [
    "CapacityCheckoutPort",
    "EntitlementPort",
    "ObservationTriggerPort",
    "OrganizationResolutionPort",
    "PurchaseAuthorityPort",
    "SubscriberPortfolioService",
    "SubscriberPortfolioStore",
]
