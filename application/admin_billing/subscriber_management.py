"""Bounded billing self service from current membership and purchase ownership."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit

from application.admin_billing.subscriber_checkout import (
    BillingProjection,
    PurchaseAuthorityReader,
    SubscriberPurchaseStore,
)
from domain.identity import TenantId
from domain.tenancy.model import Principal


class BillingManagementError(ValueError):
    pass


class BillingManagementProvider(Protocol):
    def portal(
        self, projection: BillingProjection, *, action: str, locale: str, return_url: str
    ) -> str: ...


@dataclass
class SubscriberBillingManagement:
    authority: PurchaseAuthorityReader
    store: SubscriberPurchaseStore
    provider: BillingManagementProvider
    environment: str
    return_url: str
    enabled: bool

    def _projection(
        self, principal: Principal, tenant: TenantId, now: datetime
    ) -> BillingProjection | None:
        scope = self.authority.resolve(principal, tenant, now=now)
        if (
            scope is None
            or scope.principal_id != principal.id
            or scope.tenant_id != tenant
            or scope.checked_at != now
        ):
            raise BillingManagementError("BILLING_ACCESS_DENIED")
        projection = self.store.get_billing_projection(tenant)
        if projection is not None and projection.environment_ref != self.environment:
            raise BillingManagementError("BILLING_ENVIRONMENT_MISMATCH")
        return projection

    def status(self, principal: Principal, tenant: TenantId, now: datetime) -> dict[str, object]:
        if not self.enabled:
            return {"state": "NOT_CONFIGURED", "canManage": False}
        try:
            projection = self._projection(principal, tenant, now)
        except BillingManagementError:
            return {"state": "ACCESS_DENIED", "canManage": False}
        return {
            "state": "AVAILABLE" if projection is not None else "NO_SUBSCRIPTION",
            "canManage": projection is not None,
        }

    def open(
        self, principal: Principal, tenant: TenantId, payload: dict[str, object], now: datetime
    ) -> dict[str, object]:
        if not isinstance(payload.get("action"), str) or not isinstance(payload.get("locale"), str):
            raise ValueError("invalid billing management request")
        if (
            set(payload) != {"action", "locale"}
            or payload["action"] not in {"payment_method", "invoices", "cancel"}
            or payload["locale"] not in {"es", "en", "de", "pt", "fr", "it"}
        ):
            raise ValueError("invalid billing management request")
        if not self.enabled:
            raise BillingManagementError("BILLING_NOT_CONFIGURED")
        projection = self._projection(principal, tenant, now)
        if projection is None:
            raise BillingManagementError("NO_SUBSCRIPTION")
        try:
            url = self.provider.portal(
                projection,
                action=str(payload["action"]),
                locale=str(payload["locale"]),
                return_url=self.return_url,
            )
        except Exception:
            raise BillingManagementError("BILLING_PROVIDER_UNAVAILABLE") from None
        # Reauthorize after provider IO; a revoked owner never receives the session URL.
        latest = self._projection(principal, tenant, now)
        if (
            latest is None
            or latest.customer_ref != projection.customer_ref
            or latest.subscription_ref != projection.subscription_ref
        ):
            raise BillingManagementError("BILLING_CHANGED")
        try:
            parsed = urlsplit(url)
            port = parsed.port
        except ValueError:
            raise BillingManagementError("BILLING_REDIRECT_REJECTED") from None
        if (
            parsed.scheme != "https"
            or parsed.hostname != "billing.stripe.com"
            or parsed.username
            or parsed.password
            or port
            or parsed.fragment
            or len(url) > 2048
        ):
            raise BillingManagementError("BILLING_REDIRECT_REJECTED")
        return {"state": "success", "url": url}
