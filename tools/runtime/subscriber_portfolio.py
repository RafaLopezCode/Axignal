"""Composition façade for private subscriber Organization portfolios."""

from __future__ import annotations

from pathlib import Path

from application.subscriber_identity.runtime import Clock, PrincipalTenantMembershipReader
from application.subscriber_portfolio.models import (
    AddOrganizationRequest,
    AddResult,
    ObservationRunResult,
    PendingAttentionEntry,
    PortfolioCommandResult,
    PortfolioEntry,
    ReplaceResult,
)
from application.subscriber_portfolio.service import (
    CapacityCheckoutPort,
    EntitlementPort,
    ObservationTriggerPort,
    OrganizationResolutionPort,
    PurchaseAuthorityPort,
    SubscriberPortfolioService,
    SubscriberPortfolioStore,
)
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId
from pipeline.subscriber_portfolio.sqlite_store import SqliteSubscriberPortfolioStore


class SubscriberPortfolioRuntime:
    """Stable API facade; root HTTP owns auth and transport status mapping."""

    def __init__(self, service: SubscriberPortfolioService, store: SubscriberPortfolioStore):
        self._service = service
        self.store = store

    def list(self, context: TrustedRequestContext) -> tuple[PortfolioEntry, ...]:
        return self._service.list(context)

    def list_pending(self, context: TrustedRequestContext) -> tuple[PendingAttentionEntry, ...]:
        return self._service.list_pending(context)

    def cancel_pending(
        self,
        context: TrustedRequestContext,
        pending_id: str,
        idempotency_key: str,
    ) -> PendingAttentionEntry:
        return self._service.cancel_pending(context, pending_id, idempotency_key)

    def retry_pending(self, context: TrustedRequestContext, pending_id: str) -> AddResult:
        return self._service.retry_pending(context, pending_id)

    def add(self, context: TrustedRequestContext, request: AddOrganizationRequest) -> AddResult:
        return self._service.add(context, request)

    def pause(
        self, context: TrustedRequestContext, focus_id: XeedId, idempotency_key: str
    ) -> PortfolioCommandResult:
        return self._service.pause(context, focus_id, idempotency_key)

    def resume(
        self, context: TrustedRequestContext, focus_id: XeedId, idempotency_key: str
    ) -> PortfolioCommandResult:
        return self._service.resume(context, focus_id, idempotency_key)

    def remove(
        self, context: TrustedRequestContext, focus_id: XeedId, idempotency_key: str
    ) -> PortfolioCommandResult:
        return self._service.remove(context, focus_id, idempotency_key)

    def replace(
        self,
        context: TrustedRequestContext,
        focus_id: XeedId,
        target: AddOrganizationRequest,
        idempotency_key: str,
    ) -> ReplaceResult:
        return self._service.replace(context, focus_id, target, idempotency_key)

    def reobserve(
        self, context: TrustedRequestContext, focus_id: XeedId, idempotency_key: str
    ) -> ObservationRunResult:
        return self._service.reobserve(context, focus_id, idempotency_key)


def build_subscriber_portfolio_runtime(
    data_dir: str | Path,
    identity_store: PrincipalTenantMembershipReader,
    entitlement: EntitlementPort,
    purchase_authority: PurchaseAuthorityPort,
    checkout: CapacityCheckoutPort,
    organization_resolution: OrganizationResolutionPort,
    observation_trigger: ObservationTriggerPort,
    clock: Clock,
) -> SubscriberPortfolioRuntime:
    """Build portfolio storage beside identity storage under AXIGNAL_DATA_DIR."""

    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    store = SqliteSubscriberPortfolioStore(root / "subscriber-runtime.sqlite3")
    service = SubscriberPortfolioService(
        portfolio=store,
        memberships=identity_store,
        entitlement=entitlement,
        purchase_authority=purchase_authority,
        checkout=checkout,
        organization_resolution=organization_resolution,
        observation_trigger=observation_trigger,
        clock=clock,
    )
    return SubscriberPortfolioRuntime(service, store)


__all__ = [
    "SubscriberPortfolioRuntime",
    "build_subscriber_portfolio_runtime",
]
