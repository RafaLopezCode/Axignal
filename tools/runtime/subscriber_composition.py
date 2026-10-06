"""Durable subscriber runtime composition; no fixture or ambient authority."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

from application.admin_billing.subscriber_billing import PaymentState, SubscriptionLifecycle
from application.admin_billing.subscriber_checkout import (
    BillingProjection,
    CurrentPurchaseAuthorityReader,
    OfferCatalogueReader,
    PurchaseAuthorityReader,
    SubscriberCheckoutError,
)
from application.admin_billing.subscriber_checkout import (
    EntitlementSnapshot as BillingEntitlementSnapshot,
)
from application.economic_discovery.observation_memory import ObservationMemory
from application.economic_discovery.observation_reuse import ObservationReusePolicy
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.subscriber_identity.runtime import (
    Clock,
    OidcProviderConfig,
    OidcProviderId,
    PrincipalTenantMembershipReader,
    TrustedSubscriberContext,
)
from application.subscriber_portfolio.models import (
    AddOrganizationRequest,
    CapacityCheckoutRequest,
    CheckoutRequestResult,
    EntitlementSnapshot,
    PortfolioError,
    PurchaseScopeAuthorization,
)
from application.subscriber_portfolio.service import (
    CapacityCheckoutPort,
    EntitlementPort,
    PurchaseAuthorityPort,
)
from application.subscriber_projection.subscriber_runtime import (
    SubscriberEconomicExecutionPlan,
    SubscriberEconomicRuntime,
)
from domain.admin_billing.checkout_binding import ApprovedOfferCatalogue
from domain.evidence.epistemics import Currentness
from domain.identity import TenantId, XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from tools.runtime.subscriber_checkout import (
    StripeSubscriberRuntimeSettings,
    SubscriberCheckoutRuntime,
    WebhookAcceptanceResult,
    build_stripe_subscriber_checkout_runtime,
)
from tools.runtime.subscriber_configuration import SubscriberSettings
from tools.runtime.subscriber_economic import build_subscriber_economic_runtime
from tools.runtime.subscriber_http import (
    SubscriberHttpFacade,
    SubscriberOutputPort,
    SubscriberWorkflowPort,
)
from tools.runtime.subscriber_identity import (
    build_subscriber_identity_runtime,
)
from tools.runtime.subscriber_portfolio import (
    SubscriberPortfolioRuntime,
    build_subscriber_portfolio_runtime,
)


class SubscriberEconomicExecutionPlanReader(Protocol):
    """Return only an operator-authorized plan for this current private scope."""

    def plan_for(
        self, context: TrustedSubscriberContext, focus_id: XeedId
    ) -> SubscriberEconomicExecutionPlan | None: ...


@dataclass(slots=True)
class _BillingAuthorityAdapter(PurchaseAuthorityPort):
    identity_store: PrincipalTenantMembershipReader
    authority: PurchaseAuthorityReader

    def resolve(
        self, context: TrustedSubscriberContext, now: datetime
    ) -> PurchaseScopeAuthorization | None:
        principal = self.identity_store.get_principal(context.principal_id)
        if principal is None:
            return None
        receipt = self.authority.resolve(principal, context.tenant_id, now=now)
        if receipt is None:
            return None
        if (
            receipt.principal_id != context.principal_id
            or receipt.tenant_id != context.tenant_id
            or receipt.checked_at > now
        ):
            return None
        return PurchaseScopeAuthorization(
            str(receipt.principal_id),
            str(receipt.tenant_id),
            receipt.authority_ref,
            receipt.membership_ref,
            receipt.checked_at,
        )


@dataclass(slots=True)
class _ProjectionEntitlements(EntitlementPort):
    billing_store: SqliteSubscriberBillingStore
    clock: Clock
    environment_ref: str | None

    policy_version = "subscriber-billing-snapshot-v1"
    maximum_age = timedelta(minutes=5)

    def _read(self, tenant_id: TenantId) -> tuple[BillingProjection | None, Currentness]:
        projection = self.billing_store.get_billing_projection(tenant_id)
        if projection is None:
            return None, Currentness.UNKNOWN
        now = self.clock.now()
        if projection.tenant_id != tenant_id or self.environment_ref is None:
            return projection, Currentness.UNKNOWN
        if projection.environment_ref != self.environment_ref:
            return projection, Currentness.UNKNOWN
        if projection.provider_state_at is None or projection.provider_state_ref is None:
            return projection, Currentness.UNKNOWN
        if projection.provider_state_at > now:
            return projection, Currentness.UNKNOWN
        if now - projection.provider_state_at > self.maximum_age:
            return projection, Currentness.STALE
        binding = projection.binding
        if binding is not None and binding.reason.value == "STALE_EVIDENCE":
            return projection, Currentness.STALE
        if (
            projection.effective_capacity is not None
            and binding is not None
            and binding.status.value == "VERIFIED"
            and binding.reason.value == "EXACT_MATCH"
            and binding.effective_capacity == projection.effective_capacity
            and binding.provider_state_ref == projection.provider_state_ref
            and binding.provider_state_at == projection.provider_state_at
            and binding.provider_state_at is not None
            and projection.payment_state is PaymentState.VERIFIED
            and projection.lifecycle
            in (SubscriptionLifecycle.ELIGIBLE, SubscriptionLifecycle.CANCEL_AT_PERIOD_END)
            and projection.paid_through is not None
            and projection.paid_through > now
            and projection.provider_state_at is not None
            and projection.verified_invoice_ref is not None
            and binding.evidence_ref is not None
        ):
            return projection, Currentness.CURRENT
        if (
            projection.payment_state is PaymentState.FAILED
            or projection.lifecycle
            in (SubscriptionLifecycle.CANCELED, SubscriptionLifecycle.OVERDUE)
            or (projection.paid_through is not None and projection.paid_through <= now)
        ):
            return projection, Currentness.STALE
        return projection, Currentness.UNKNOWN

    def snapshot(self, tenant_id: TenantId) -> EntitlementSnapshot:
        projection, currentness = self._read(tenant_id)
        if projection is None:
            return EntitlementSnapshot(None, Currentness.UNKNOWN, None)
        capacity = projection.effective_capacity if currentness is Currentness.CURRENT else None
        return EntitlementSnapshot(capacity, currentness, projection.provider_state_at)

    def billing_snapshot(self, tenant_id: TenantId) -> BillingEntitlementSnapshot | None:
        projection, currentness = self._read(tenant_id)
        if projection is None:
            return None
        capacity = projection.effective_capacity if currentness is Currentness.CURRENT else None
        return BillingEntitlementSnapshot(
            tenant_id=tenant_id,
            effective_capacity=capacity,
            currentness=currentness.value,
            evidence_ref=(None if projection.binding is None else projection.binding.evidence_ref),
            paid_through=projection.paid_through,
        )


class _BillingSnapshotReader:
    """Narrow bridge for checkout's projection-backed entitlement contract."""

    def __init__(self, entitlements: _ProjectionEntitlements) -> None:
        self._entitlements = entitlements

    def snapshot(self, tenant_id: TenantId) -> BillingEntitlementSnapshot | None:
        return self._entitlements.billing_snapshot(tenant_id)


class _CheckoutPortAdapter(CapacityCheckoutPort):
    """Recheck Principal, membership, purchase owner and capacity at dispatch."""

    def __init__(
        self,
        *,
        runtime: SubscriberCheckoutRuntime,
        identity_store: PrincipalTenantMembershipReader,
        authority_reader: PurchaseAuthorityReader,
        entitlements: _ProjectionEntitlements,
        clock: Clock,
    ) -> None:
        self._runtime = runtime
        self._identity_store = identity_store
        self._authority_reader = authority_reader
        self._entitlements = entitlements
        self._clock = clock

    def request_checkout(self, request: CapacityCheckoutRequest) -> CheckoutRequestResult:
        principal = self._identity_store.get_principal(request.context.principal_id)
        if principal is None:
            return CheckoutRequestResult(None, False, "ACCESS_DENIED")
        now = self._clock.now()
        receipt = self._authority_reader.resolve(principal, request.context.tenant_id, now=now)
        if (
            receipt is None
            or receipt.principal_id != request.authorization.principal_id
            or receipt.tenant_id != request.authorization.tenant_id
            or receipt.authority_ref != request.authorization.authority_ref
            or receipt.membership_ref != request.authorization.membership_ref
            or receipt.checked_at > now
            or now - receipt.checked_at > timedelta(minutes=1)
        ):
            return CheckoutRequestResult(None, False, "PURCHASE_AUTHORITY_UNKNOWN")
        snapshot = self._entitlements.billing_snapshot(request.context.tenant_id)
        if (
            snapshot is None
            or snapshot.currentness != Currentness.CURRENT.value
            or snapshot.effective_capacity != request.current_capacity
            or snapshot.evidence_ref is None
            or snapshot.paid_through is None
            or snapshot.paid_through <= now
        ):
            return CheckoutRequestResult(None, False, "CAPACITY_UNKNOWN")
        result = self._runtime.request_capacity_increase(
            principal=principal,
            tenant_id=request.context.tenant_id,
            request_ref=request.idempotency_key,
            desired_organization_total=request.desired_capacity,
            now=now,
        )
        return CheckoutRequestResult(
            result.request_ref,
            result.status == "PENDING_PURCHASE",
            result.status,
        )


class _UnavailableCheckout(CapacityCheckoutPort):
    def request_checkout(self, request: CapacityCheckoutRequest) -> CheckoutRequestResult:
        del request
        return CheckoutRequestResult(None, False, "NOT_CONFIGURED")


class _BillingWebhookAdapter:
    def __init__(self, runtime: SubscriberCheckoutRuntime) -> None:
        self._runtime = runtime

    def handle_signed_webhook(
        self, raw_body: bytes, stripe_signature: str, received_at: datetime
    ) -> WebhookAcceptanceResult:
        return self._runtime.handle_signed_webhook(
            raw_body=raw_body,
            stripe_signature=stripe_signature,
            received_at=received_at,
        )


class _ObservationTrigger:
    """Synchronous plan execution; absence of a real plan stays NOT_READY."""

    def __init__(
        self,
        *,
        plans: SubscriberEconomicExecutionPlanReader | None,
    ) -> None:
        self._portfolio: SubscriberPortfolioRuntime | None = None
        self._economic: SubscriberEconomicRuntime | None = None
        self._plans = plans
        self.last_state_by_focus: dict[str, str] = {}

    def bind(
        self, portfolio: SubscriberPortfolioRuntime, economic: SubscriberEconomicRuntime
    ) -> None:
        self._portfolio = portfolio
        self._economic = economic

    def trigger(
        self,
        context: TrustedSubscriberContext,
        focus_id: XeedId,
        idempotency_key: str,
    ) -> str:
        del idempotency_key
        # Reauthorize before retrieving the private plan or canonical Organization.
        if self._portfolio is None or self._economic is None:
            return "NOT_READY"
        entry = self._portfolio.store.get_authorized(context, focus_id)
        if entry is None or self._plans is None:
            state = "NOT_READY"
        else:
            plan = self._plans.plan_for(context, focus_id)
            state = (
                "NOT_READY"
                if plan is None
                else self._economic.execute(context, focus_id, plan).state
            )
        self.last_state_by_focus[str(focus_id)] = state
        return state


class _SubscriberWorkflow(SubscriberWorkflowPort):
    def __init__(
        self,
        *,
        settings: SubscriberSettings,
        clock: Clock,
        identity_store: PrincipalTenantMembershipReader,
        portfolio: SubscriberPortfolioRuntime,
        entitlements: _ProjectionEntitlements,
        purchase_authority: _BillingAuthorityAdapter,
        checkout_available: bool,
        checkout_mutations_enabled: bool,
        checkout_runtime: SubscriberCheckoutRuntime | None,
        observation_trigger: _ObservationTrigger,
        catalogue_reader: OfferCatalogueReader | None,
        environment_ref: str,
    ) -> None:
        self._settings = settings
        self._clock = clock
        self._identity_store = identity_store
        self._portfolio = portfolio
        self._entitlements = entitlements
        self._purchase_authority = purchase_authority
        self._checkout = checkout_runtime
        self._checkout_available = checkout_available
        self._checkout_runtime = checkout_runtime
        self._trigger = observation_trigger
        self._catalogue_reader = catalogue_reader
        self._environment_ref = environment_ref
        self._checkout_mutations_enabled = checkout_available and checkout_mutations_enabled

    def _tax_ready(self) -> bool:
        if self._catalogue_reader is None or not self._checkout_available:
            return False
        catalogue = self._catalogue_reader.resolve(self._environment_ref)
        if not isinstance(catalogue, ApprovedOfferCatalogue):
            return False
        tax = catalogue.tax_configuration
        return (
            tax is not None
            and tax.is_current(self._environment_ref, self._clock.now())
            and self._checkout_mutations_enabled
            and catalogue.base_offer.terms.interval_unit == "month"
            and catalogue.base_offer.terms.interval_count == 1
            and catalogue.base_offer.terms.currency == "EUR"
            and catalogue.base_offer.terms.unit_amount_minor == 995
            and catalogue.base_offer.terms.tax_behavior == "exclusive"
            and catalogue.additional_xeed_offer.terms.interval_unit == "month"
            and catalogue.additional_xeed_offer.terms.interval_count == 1
            and catalogue.additional_xeed_offer.terms.currency == "EUR"
            and catalogue.additional_xeed_offer.terms.unit_amount_minor == 495
            and catalogue.additional_xeed_offer.terms.tax_behavior == "exclusive"
        )

    def portfolio(self, context: TrustedSubscriberContext) -> dict[str, object]:
        entries = self._portfolio.list(context)
        pending = self._portfolio.list_pending(context)
        snapshot = self._entitlements.snapshot(context.tenant_id)
        authority = self._purchase_authority.resolve(context, self._clock.now())
        organizations: list[dict[str, object]] = [
            {
                "focusId": str(entry.focus_id),
                "organizationId": str(entry.xeed.organization_id),
                "label": entry.xeed.label or "Organization",
                "state": entry.status.value,
            }
            for entry in entries
        ]
        organizations.extend(
            {
                "focusId": item.pending_id,
                "organizationId": None,
                "label": item.display_label or item.locator,
                "state": item.status.value,
            }
            for item in pending
        )
        return {
            "state": "success",
            "capacity": snapshot.capacity,
            "capacityCurrentness": snapshot.currentness.value,
            "canPurchase": None if authority is None else self._tax_ready(),
            "contractingEnabled": self._settings.contracting_enabled and self._tax_ready(),
            "organizations": organizations,
        }

    def command(
        self, context: TrustedSubscriberContext, command: dict[str, object]
    ) -> dict[str, object]:
        action = str(command["action"])
        request_ref = str(command["requestRef"])
        focus_id = XeedId(str(command["focusId"])) if "focusId" in command else None
        try:
            if action == "add":
                add_result = self._portfolio.add(
                    context,
                    AddOrganizationRequest(request_ref, str(command["locator"])),
                )
                response: dict[str, object] = {"state": add_result.status.value}
                if add_result.entry is not None:
                    response["focusId"] = str(add_result.entry.focus_id)
                    response["organizationId"] = str(add_result.entry.xeed.organization_id)
                    response["observationState"] = self._trigger.last_state_by_focus.get(
                        str(add_result.entry.focus_id), "NOT_READY"
                    )
                if add_result.checkout is not None:
                    response["reason"] = add_result.checkout.safe_status
                if add_result.identity_reason is not None:
                    response["reason"] = add_result.identity_reason
                return response
            if action in {"retry_pending", "cancel_pending"}:
                assert focus_id is not None
                if action == "retry_pending":
                    retry_result = self._portfolio.retry_pending(context, str(focus_id))
                    body: dict[str, object] = {"state": retry_result.status.value}
                    if retry_result.entry is not None:
                        body["focusId"] = str(retry_result.entry.focus_id)
                        body["organizationId"] = str(retry_result.entry.xeed.organization_id)
                        body["observationState"] = self._trigger.last_state_by_focus.get(
                            str(retry_result.entry.focus_id), "NOT_READY"
                        )
                    return body
                cancelled = self._portfolio.cancel_pending(context, str(focus_id), request_ref)
                return {"state": cancelled.status.value, "focusId": cancelled.pending_id}
            if action in {"pause", "resume", "remove"}:
                assert focus_id is not None
                lifecycle_result = getattr(self._portfolio, action)(context, focus_id, request_ref)
                return {
                    "state": lifecycle_result.entry.status.value,
                    "focusId": str(lifecycle_result.entry.focus_id),
                }
            if action == "replace":
                assert focus_id is not None
                replace_result = self._portfolio.replace(
                    context,
                    focus_id,
                    AddOrganizationRequest(request_ref, str(command["locator"])),
                    request_ref,
                )
                return {
                    "state": replace_result.entry.status.value,
                    "focusId": str(replace_result.entry.focus_id),
                    "organizationId": str(replace_result.entry.xeed.organization_id),
                    "observationState": self._trigger.last_state_by_focus.get(
                        str(replace_result.entry.focus_id), "NOT_READY"
                    ),
                }
            if action == "reobserve":
                assert focus_id is not None
                observation_result = self._portfolio.reobserve(context, focus_id, request_ref)
                return {
                    "state": observation_result.run_id,
                    "focusId": str(observation_result.focus_id),
                    "observationState": observation_result.run_id,
                }
            if action in {"purchase", "expand"}:
                if not self._settings.contracting_enabled or not self._tax_ready():
                    return {"state": "NOT_READY", "reason": "TAX_CONFIGURATION_UNKNOWN"}
                if self._checkout is None:
                    return {"state": "NOT_READY", "reason": "BILLING_RUNTIME_UNAVAILABLE"}
                principal = self._identity_store.get_principal(context.principal_id)
                if principal is None:
                    return {"state": "NOT_READY", "reason": "ACCESS_DENIED"}
                total_value = command["desiredOrganizationTotal"]
                if type(total_value) is not int:
                    return {"state": "rejected", "code": "INVALID_CAPACITY"}
                total = total_value
                now = self._clock.now()
                checkout_result = (
                    self._checkout.start_initial_checkout(
                        principal=principal,
                        tenant_id=context.tenant_id,
                        request_ref=request_ref,
                        desired_organization_total=total,
                        now=now,
                    )
                    if action == "purchase"
                    else self._checkout.request_capacity_increase(
                        principal=principal,
                        tenant_id=context.tenant_id,
                        request_ref=request_ref,
                        desired_organization_total=total,
                        now=now,
                    )
                )
                return {
                    "state": checkout_result.status,
                    "requestRef": checkout_result.request_ref,
                    "effectiveCapacity": checkout_result.effective_capacity,
                    "desiredCapacity": checkout_result.desired_capacity,
                    "checkoutUrl": getattr(checkout_result, "checkout_url", None),
                    "paymentUrl": getattr(checkout_result, "payment_url", None),
                    "reason": checkout_result.reason,
                }
            if action == "refresh_purchase":
                if self._checkout is None:
                    return {"state": "NOT_READY", "reason": "BILLING_RUNTIME_UNAVAILABLE"}
                principal = self._identity_store.get_principal(context.principal_id)
                if principal is None:
                    return {"state": "rejected", "code": "ACCESS_DENIED"}
                if self._purchase_authority.resolve(context, self._clock.now()) is None:
                    return {"state": "rejected", "code": "PURCHASE_AUTHORITY_REQUIRED"}
                outcomes = self._checkout.reconcile_pending(
                    principal=principal,
                    tenant_id=context.tenant_id,
                    now=self._clock.now(),
                )
                snapshot = self._entitlements.snapshot(context.tenant_id)
                return {
                    "state": (
                        "NOT_READY"
                        if not outcomes
                        else "UNKNOWN"
                        if "UNKNOWN" in outcomes
                        else "REFRESHED"
                    ),
                    "refreshOutcomes": outcomes,
                    "capacity": snapshot.capacity,
                    "capacityCurrentness": snapshot.currentness.value,
                }
        except PortfolioError as exc:
            return {"state": "rejected", "code": exc.failure.value}
        except SubscriberCheckoutError as exc:
            return {"state": "rejected", "code": exc.failure.value}
        return {"state": "rejected", "code": "NOT_READY"}


class _SubscriberOutputs(SubscriberOutputPort):
    def __init__(self, workflow: _SubscriberWorkflow, economic: SubscriberEconomicRuntime):
        self._workflow = workflow
        self._economic = economic

    def output(
        self, context: TrustedSubscriberContext, focus_id: XeedId, as_of: datetime
    ) -> dict[str, object]:
        return self._economic.read(context, focus_id, as_of).to_wire()


def _oidc_provider_configs(
    settings: SubscriberSettings,
) -> dict[OidcProviderId, OidcProviderConfig]:
    definitions = (
        (
            OidcProviderId.GOOGLE,
            "GOOGLE",
            "https://accounts.google.com",
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://www.googleapis.com/oauth2/v3/certs",
            "google",
        ),
        (
            OidcProviderId.OPENAI,
            "CHATGPT",
            "https://auth.openai.com",
            "https://auth.openai.com/api/accounts/authorize",
            "https://auth.openai.com/api/accounts/oauth/token",
            "https://auth.openai.com/.well-known/jwks.json",
            "openai",
        ),
    )
    result: dict[OidcProviderId, OidcProviderConfig] = {}
    for provider, prefix, issuer, authorization, token, jwks, callback_name in definitions:
        client_id = settings.values.get(f"AXIGNAL_{prefix}_CLIENT_ID", "")
        secret_file = settings.values.get(f"AXIGNAL_{prefix}_CLIENT_SECRET_FILE", "")
        registered = settings.values.get(f"AXIGNAL_{prefix}_REGISTERED", "false") == "true"
        redirect_uri = settings.values.get(
            f"AXIGNAL_{prefix}_REDIRECT_URI", f"{settings.origin}/api/auth/callback/{callback_name}"
        )
        secret_path = Path(secret_file) if secret_file else None
        secret_file_present = False
        if secret_path is not None:
            try:
                secret_file_present = secret_path.is_file() and secret_path.stat().st_size > 0
            except OSError:
                secret_file_present = False
        ready = bool(
            settings.provider_ready("openai" if provider is OidcProviderId.OPENAI else "google")
            and client_id
            and registered
            and secret_file_present
        )
        result[provider] = OidcProviderConfig(
            provider_id=provider,
            issuer=issuer,
            client_id=client_id or "unconfigured",
            redirect_uri=redirect_uri,
            enabled=ready,
            registered=registered and ready,
            authorization_endpoint=authorization,
            token_endpoint=token,
            jwks_uri=jwks,
            client_secret_path=secret_path,
            client_scope=client_id or None,
        )
    return result


def build_subscriber_facade(
    settings: SubscriberSettings,
    data_dir: str | Path,
    *,
    observation_memory: ObservationMemory,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
    code_sha: str,
    stripe_settings: StripeSubscriberRuntimeSettings | None = None,
    offer_catalogue_reader: OfferCatalogueReader | None = None,
    execution_plan_reader: SubscriberEconomicExecutionPlanReader | None = None,
    clock: Clock | None = None,
) -> SubscriberHttpFacade:
    """Compose real durable subscriber services from root-authorized inputs.

    No provider keys, catalogue, execution plan or governance authority are
    inferred from ambient process state. Missing optional production inputs
    remain unavailable/UNKNOWN and never load demonstration data.
    """
    from application.subscriber_identity.runtime import SystemClock

    effective_clock = clock or SystemClock()
    root = Path(data_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    billing_store = SqliteSubscriberBillingStore(root / "subscriber-billing.sqlite3")
    identity = build_subscriber_identity_runtime(
        root,
        _oidc_provider_configs(settings),
        effective_clock,
        billing_store,
    )
    purchase_reader = CurrentPurchaseAuthorityReader(identity.store, billing_store)
    purchase_adapter = _BillingAuthorityAdapter(identity.store, purchase_reader)
    environment_ref = stripe_settings.environment_ref if stripe_settings is not None else None
    entitlements = _ProjectionEntitlements(
        billing_store,
        effective_clock,
        environment_ref,
    )
    checkout: SubscriberCheckoutRuntime | None = None
    checkout_available = False
    checkout_mutations_enabled = False
    resolved_stripe_settings: StripeSubscriberRuntimeSettings | None = None
    if (
        stripe_settings is not None
        and offer_catalogue_reader is not None
        and stripe_settings.api_key
        and stripe_settings.webhook_signing_secret
    ):
        tax_catalogue = offer_catalogue_reader.resolve(stripe_settings.environment_ref)
        tax = None if tax_catalogue is None else tax_catalogue.tax_configuration
        tax_ready = bool(
            tax and tax.is_current(stripe_settings.environment_ref, effective_clock.now())
        )
        resolved_stripe_settings = replace(
            stripe_settings,
            database_path=root / "subscriber-billing.sqlite3",
            enabled=settings.enabled and stripe_settings.enabled,
            mutations_enabled=(
                stripe_settings.mutations_enabled and settings.contracting_enabled and tax_ready
            ),
        )
        checkout = build_stripe_subscriber_checkout_runtime(
            settings=resolved_stripe_settings,
            authority_reader=purchase_reader,
            entitlement_reader=_BillingSnapshotReader(entitlements),
            catalogue_reader=offer_catalogue_reader,
        )
        checkout_available = resolved_stripe_settings.enabled
        checkout_mutations_enabled = resolved_stripe_settings.mutations_enabled

    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    governance = SqliteIdentityGovernanceStore(root / "identity-governance.sqlite3")
    organizations = SqliteCanonicalOrganizationStore(
        root / "canonical-organizations.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(artifacts),
        governance=governance,
    )
    observation_trigger = _ObservationTrigger(plans=execution_plan_reader)
    portfolio = build_subscriber_portfolio_runtime(
        root,
        identity.store,
        entitlements,
        purchase_adapter,
        (
            _CheckoutPortAdapter(
                runtime=checkout,
                identity_store=identity.store,
                authority_reader=purchase_reader,
                entitlements=entitlements,
                clock=effective_clock,
            )
            if checkout is not None
            else _UnavailableCheckout()
        ),
        organizations,
        observation_trigger,
        effective_clock,
    )
    economic = build_subscriber_economic_runtime(
        database_path=root / "subscriber-economic-output.sqlite3",
        identity_store=identity.store,
        portfolio_store=portfolio.store,
        organizations=organizations,
        observation_memory=observation_memory,
        reuse_policy=reuse_policy,
        temporal_policy=temporal_policy,
        code_sha=code_sha,
    )
    observation_trigger.bind(portfolio, economic)
    workflow = _SubscriberWorkflow(
        settings=settings,
        clock=effective_clock,
        identity_store=identity.store,
        portfolio=portfolio,
        entitlements=entitlements,
        purchase_authority=purchase_adapter,
        checkout_available=checkout_available,
        checkout_mutations_enabled=checkout_mutations_enabled,
        checkout_runtime=checkout,
        observation_trigger=observation_trigger,
        catalogue_reader=offer_catalogue_reader,
        environment_ref=(
            stripe_settings.environment_ref if stripe_settings is not None else "UNCONFIGURED"
        ),
    )
    return SubscriberHttpFacade(
        settings=settings,
        identity=identity,
        workflow=workflow,
        outputs=_SubscriberOutputs(workflow, economic),
        billing_webhook=None if checkout is None else _BillingWebhookAdapter(checkout),
        available_providers=frozenset(
            provider.value.casefold()
            for provider, config in _oidc_provider_configs(settings).items()
            if config.enabled and config.registered
        ),
    )


__all__ = [
    "SubscriberEconomicExecutionPlanReader",
    "build_subscriber_facade",
]
