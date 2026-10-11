"""Route-independent composition boundary for subscriber checkout."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from application.admin_billing.subscriber_checkout import (
    CapacityChangeResult,
    CapacityIncreaseCommand,
    CheckoutStartResult,
    EntitlementSnapshotReader,
    InitialCheckoutCommand,
    OfferCatalogueReader,
    PurchaseAuthorityReader,
    PurchaseFailure,
    PurchaseStatusResult,
    SubscriberBillingProvider,
    SubscriberCheckoutError,
    SubscriberCheckoutService,
    SubscriberPurchaseStore,
    SubscriberReconciler,
)
from domain.identity import TenantId
from domain.tenancy.model import Principal


@dataclass(frozen=True, slots=True)
class SubscriberCheckoutRuntimeConfig:
    enabled: bool
    environment_ref: str
    checkout_hosts: frozenset[str]
    invoice_hosts: frozenset[str]

    def __post_init__(self) -> None:
        if not self.environment_ref.strip():
            raise ValueError("environment_ref is required")
        if any(not _valid_host(host) for host in self.checkout_hosts | self.invoice_hosts):
            raise ValueError("redirect host allowlist must contain plain hostnames")


@dataclass(frozen=True, slots=True)
class WebhookAcceptanceResult:
    accepted: bool
    disposition: str
    event_ref: str | None


class SubscriberBillingWebhook(Protocol):
    def handle_signed_webhook(
        self, raw_body: bytes, stripe_signature: str, received_at: datetime
    ) -> WebhookReceiptLike: ...


class WebhookReceiptLike(Protocol):
    @property
    def accepted(self) -> bool: ...

    @property
    def disposition(self) -> str: ...

    @property
    def event_ref(self) -> str | None: ...


class SubscriberRetryWorker(Protocol):
    def run_due(self, *, now: datetime, limit: int = 20) -> tuple[str, ...]: ...


class SubscriberCheckoutRuntime:
    """Expose typed use cases to root-owned routes without registering routes."""

    def __init__(
        self,
        *,
        service: SubscriberCheckoutService,
        webhook: SubscriberBillingWebhook | None,
        config: SubscriberCheckoutRuntimeConfig,
        retry_worker: SubscriberRetryWorker | None = None,
    ) -> None:
        if service is None:
            raise ValueError("subscriber checkout service is required")
        self._service = service
        self._webhook = webhook
        self._config = config
        self._retry_worker = retry_worker

    def start_initial_checkout(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        request_ref: str,
        desired_organization_total: int,
        now: datetime,
    ) -> CheckoutStartResult:
        self._require_enabled()
        result = self._service.start_initial_checkout(
            principal=principal,
            tenant_id=tenant_id,
            command=InitialCheckoutCommand(
                request_ref=request_ref,
                desired_total=desired_organization_total,
            ),
            now=now,
        )
        return CheckoutStartResult(
            status=result.status,
            request_ref=result.request_ref,
            intent_ref=result.intent_ref,
            desired_capacity=result.desired_capacity,
            effective_capacity=result.effective_capacity,
            checkout_url=_validated_redirect(result.checkout_url, self._config.checkout_hosts),
            payment_url=_validated_redirect(result.payment_url, self._config.invoice_hosts),
            reason=result.reason,
        )

    def request_capacity_increase(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        request_ref: str,
        desired_organization_total: int,
        now: datetime,
    ) -> CapacityChangeResult:
        self._require_enabled()
        result = self._service.request_capacity_increase(
            principal=principal,
            tenant_id=tenant_id,
            command=CapacityIncreaseCommand(
                request_ref=request_ref,
                desired_total=desired_organization_total,
            ),
            now=now,
        )
        return CapacityChangeResult(
            status=result.status,
            request_ref=result.request_ref,
            intent_ref=result.intent_ref,
            desired_capacity=result.desired_capacity,
            effective_capacity=result.effective_capacity,
            pending_update=result.pending_update,
            payment_url=_validated_redirect(result.payment_url, self._config.invoice_hosts),
            reason=result.reason,
        )

    def get_purchase_status(
        self,
        *,
        principal: Principal,
        tenant_id: TenantId,
        request_ref: str,
        now: datetime,
    ) -> PurchaseStatusResult:
        self._require_enabled()
        return self._service.get_purchase_status(
            principal=principal,
            tenant_id=tenant_id,
            request_ref=request_ref,
            now=now,
        )

    def reconcile_pending(
        self, *, principal: Principal, tenant_id: TenantId, now: datetime
    ) -> tuple[str, ...]:
        self._require_enabled()
        return self._service.reconcile_pending(principal=principal, tenant_id=tenant_id, now=now)

    def reverify_current_projection(self, *, tenant_id: TenantId, now: datetime) -> str:
        self._require_enabled()
        return self._service.reverify_current_projection(tenant_id=tenant_id, now=now)

    def handle_signed_webhook(
        self, *, raw_body: bytes, stripe_signature: str, received_at: datetime
    ) -> WebhookAcceptanceResult:
        self._require_enabled()
        if self._webhook is None:
            raise SubscriberCheckoutError(PurchaseFailure.PROVIDER_UNAVAILABLE)
        receipt = self._webhook.handle_signed_webhook(raw_body, stripe_signature, received_at)
        return WebhookAcceptanceResult(
            accepted=receipt.accepted,
            disposition=receipt.disposition,
            event_ref=receipt.event_ref,
        )

    def run_reconciliation_retries(self, *, now: datetime, limit: int = 20) -> tuple[str, ...]:
        self._require_enabled()
        if self._retry_worker is None:
            return ()
        return self._retry_worker.run_due(now=now, limit=limit)

    def _require_enabled(self) -> None:
        if not self._config.enabled:
            raise RuntimeError("subscriber billing runtime is disabled")


def build_subscriber_checkout_runtime(
    *,
    config: SubscriberCheckoutRuntimeConfig,
    authority_reader: PurchaseAuthorityReader,
    entitlement_reader: EntitlementSnapshotReader,
    catalogue_reader: OfferCatalogueReader,
    store: SubscriberPurchaseStore,
    provider: SubscriberBillingProvider,
    webhook: SubscriberBillingWebhook | None,
    reconciler: SubscriberReconciler | None = None,
    retry_worker: SubscriberRetryWorker | None = None,
) -> SubscriberCheckoutRuntime:
    """Construct the boundary from root-owned identity/provider composition."""
    service = SubscriberCheckoutService(
        authority_reader=authority_reader,
        entitlement_reader=entitlement_reader,
        catalogue_reader=catalogue_reader,
        store=store,
        provider=provider,
        environment_ref=config.environment_ref,
        reconciler=reconciler,
    )
    return SubscriberCheckoutRuntime(
        service=service, webhook=webhook, config=config, retry_worker=retry_worker
    )


@dataclass(frozen=True, slots=True)
class StripeSubscriberRuntimeSettings:
    environment_ref: str
    account_ref: str
    live_mode: bool
    api_version: str
    base_offer_ref: str
    additional_offer_ref: str
    price_refs: dict[str, str]
    success_url: str
    cancel_url: str
    checkout_hosts: frozenset[str]
    invoice_hosts: frozenset[str]
    database_path: Path
    enabled: bool
    mutations_enabled: bool = False
    api_key: str | None = field(default=None, repr=False)
    webhook_signing_secret: str | None = field(default=None, repr=False)


def build_stripe_subscriber_checkout_runtime(
    *,
    settings: StripeSubscriberRuntimeSettings,
    authority_reader: PurchaseAuthorityReader,
    entitlement_reader: EntitlementSnapshotReader,
    catalogue_reader: OfferCatalogueReader,
) -> SubscriberCheckoutRuntime:
    """Compose real Stripe HTTP, durable store, reconciler and signed webhook.

    Credentials are explicit runtime inputs. There are no implicit environment
    defaults, no live call occurs during construction, and write enablement is
    an explicit server setting with a fail-closed default.
    """
    if not settings.api_key or not settings.webhook_signing_secret:
        raise RuntimeError("Stripe subscriber runtime is NOT_CONFIGURED")
    from application.admin_billing.subscriber_reconciliation import (
        SubscriberPurchaseReconciler,
    )
    from pipeline.admin_billing.reconciliation_worker import SubscriberReconciliationWorker
    from pipeline.admin_billing.stripe_subscriber import (
        StripeSubscriberAdapter,
        StripeSubscriberConfig,
        UrllibStripeTransport,
    )
    from pipeline.admin_billing.stripe_webhook import StripeWebhookVerifier
    from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore

    provider_config = StripeSubscriberConfig(
        environment_ref=settings.environment_ref,
        account_ref=settings.account_ref,
        live_mode=settings.live_mode,
        api_version=settings.api_version,
        base_offer_ref=settings.base_offer_ref,
        additional_offer_ref=settings.additional_offer_ref,
        price_refs=settings.price_refs,
        success_url=settings.success_url,
        cancel_url=settings.cancel_url,
        api_key=settings.api_key,
        mutations_enabled=settings.mutations_enabled,
    )
    transport = UrllibStripeTransport(provider_config)
    provider = StripeSubscriberAdapter(config=provider_config, transport=transport)
    store = SqliteSubscriberBillingStore(settings.database_path)
    reconciler = SubscriberPurchaseReconciler(
        store=store,
        provider=provider,
        catalogue_reader=catalogue_reader,
        environment_ref=settings.environment_ref,
    )
    webhook = StripeWebhookVerifier(
        signing_secret=settings.webhook_signing_secret,
        account_ref=settings.account_ref,
        environment_ref=settings.environment_ref,
        live_mode=settings.live_mode,
        store=store,
        reconciler=reconciler,
    )
    retry_worker = SubscriberReconciliationWorker(store=store, reconciler=reconciler)
    return build_subscriber_checkout_runtime(
        config=SubscriberCheckoutRuntimeConfig(
            enabled=settings.enabled,
            environment_ref=settings.environment_ref,
            checkout_hosts=settings.checkout_hosts,
            invoice_hosts=settings.invoice_hosts,
        ),
        authority_reader=authority_reader,
        entitlement_reader=entitlement_reader,
        catalogue_reader=catalogue_reader,
        store=store,
        provider=provider,
        webhook=webhook,
        reconciler=reconciler,
        retry_worker=retry_worker,
    )


def _valid_host(host: str) -> bool:
    return (
        isinstance(host, str)
        and bool(host)
        and host == host.casefold()
        and "://" not in host
        and "/" not in host
        and ":" not in host
        and "@" not in host
    )


def _validated_redirect(value: str | None, allowed_hosts: frozenset[str]) -> str | None:
    if value is None:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() not in allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.fragment
    ):
        return None
    return value
