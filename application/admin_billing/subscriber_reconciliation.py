"""Fail-closed reconciliation from provider facts to subscriber billing projection."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from enum import StrEnum

from application.admin_billing.checkout_binding import validate_checkout_binding
from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionCapacityValidation,
    SubscriptionLifecycle,
    validate_subscription_capacity,
)
from application.admin_billing.subscriber_checkout import (
    AttemptKind,
    AttemptStatus,
    BillingProjection,
    OfferCatalogueReader,
    ProviderCheckoutBinding,
    PurchaseAttempt,
    SubscriberBillingProvider,
    SubscriberReconciliationStore,
)
from domain.admin_billing.checkout_binding import (
    BindingReason,
    BindingStatus,
    PurchaseIntent,
)
from domain.admin_billing.checkout_binding import (
    BindingStatus as CheckoutBindingStatus,
)
from domain.identity import TenantId


class ReconciliationDisposition(StrEnum):
    COMPLETE = "COMPLETE"
    PENDING_PURCHASE = "PENDING_PURCHASE"
    UNKNOWN = "UNKNOWN"
    MISMATCH = "MISMATCH"


class SubscriberPurchaseReconciler:
    """Re-read session, invoice and full subscription before projecting billing.

    This records billing facts only. It does not issue Tenant entitlements;
    portfolio authorization must consume the separately governed projection.
    """

    def __init__(
        self,
        *,
        store: SubscriberReconciliationStore,
        provider: SubscriberBillingProvider,
        catalogue_reader: OfferCatalogueReader,
        environment_ref: str,
    ) -> None:
        if not environment_ref.strip():
            raise ValueError("provider environment is required")
        self._store = store
        self._provider = provider
        self._catalogue_reader = catalogue_reader
        self._environment_ref = environment_ref

    def reconcile_session(
        self, checkout_session_ref: str, *, now: datetime
    ) -> ReconciliationDisposition:
        attempt = self._store.get_attempt_by_session(checkout_session_ref)
        if attempt is None:
            return ReconciliationDisposition.UNKNOWN
        if attempt.kind is not AttemptKind.INITIAL:
            return ReconciliationDisposition.UNKNOWN
        return self._reconcile(attempt, now=now)

    def reconcile_attempt(
        self, tenant_id: TenantId, request_ref: str, *, now: datetime
    ) -> ReconciliationDisposition:
        attempt = self._store.get_attempt(tenant_id, request_ref)
        if attempt is None:
            return ReconciliationDisposition.UNKNOWN
        return self._reconcile(attempt, now=now)

    def reconcile_subscription(
        self, subscription_ref: str, *, now: datetime
    ) -> ReconciliationDisposition:
        """Treat provider event refs only as a bounded hint to re-read attempts."""
        complete = False
        for attempt in self._store.list_all_pending_attempts(limit=100):
            if (
                attempt.subscription_ref is not None
                and attempt.subscription_ref != subscription_ref
            ):
                continue
            result = self._reconcile(attempt, now=now)
            if result is ReconciliationDisposition.COMPLETE:
                complete = True
        if complete:
            return ReconciliationDisposition.COMPLETE
        return ReconciliationDisposition.UNKNOWN

    def refresh_current_projection(
        self, tenant_id: TenantId, *, now: datetime
    ) -> ReconciliationDisposition:
        projection = self._store.get_billing_projection(tenant_id)
        if projection is None:
            return ReconciliationDisposition.UNKNOWN
        catalogue = self._catalogue_reader.resolve(self._environment_ref)
        if catalogue is None:
            return ReconciliationDisposition.UNKNOWN
        current = self._provider.read_current_subscription(projection)
        expected_capacity = projection.effective_capacity
        if (
            expected_capacity is None
            and projection.binding is not None
            and projection.binding.status is BindingStatus.VERIFIED
        ):
            expected_capacity = projection.binding.effective_capacity
        validation = validate_subscription_capacity(
            expected_capacity=expected_capacity,
            authorized_at=projection.provider_state_at,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=current.snapshot,
            previous=projection.binding,
        )
        items_verified = validation.status is BindingStatus.VERIFIED
        paid_period_current = current.paid_through is not None and current.paid_through > now
        verified_lifecycle = current.lifecycle is SubscriptionLifecycle.ELIGIBLE or (
            current.lifecycle is SubscriptionLifecycle.CANCEL_AT_PERIOD_END and paid_period_current
        )
        capacity = (
            validation.effective_capacity
            if items_verified
            and current.payment_state is PaymentState.VERIFIED
            and verified_lifecycle
            and paid_period_current
            else None
        )
        payment_state = current.payment_state
        paid_through = current.paid_through

        # A pending invoice for an increase cannot revoke the already-paid
        # lower capacity while its exact old line-items and paid-through remain
        # current. Refund/dispute handling for a paid attempt is not covered by
        # this exception because the purchase attempt is no longer pending.
        pending = self._store.get_pending_capacity_change(tenant_id, projection.subscription_ref)
        if (
            capacity is None
            and pending is not None
            and pending.invoice_ref is not None
            and pending.invoice_ref == current.invoice_ref
            and projection.payment_state is PaymentState.VERIFIED
            and projection.effective_capacity is not None
            and projection.paid_through is not None
            and projection.paid_through > now
            and items_verified
            and validation.effective_capacity == projection.effective_capacity
            and current.lifecycle is SubscriptionLifecycle.ELIGIBLE
        ):
            capacity = projection.effective_capacity
            payment_state = projection.payment_state
            paid_through = projection.paid_through

        updated = BillingProjection(
            tenant_id=tenant_id,
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            checkout_session_ref=projection.checkout_session_ref,
            environment_ref=projection.environment_ref,
            additional_item_ref=current.additional_item_ref,
            effective_capacity=capacity,
            payment_state=payment_state,
            lifecycle=current.lifecycle,
            binding=validation,
            provider_state_ref=current.snapshot.provider_state_ref,
            provider_state_at=current.snapshot.provider_state_at,
            paid_through=paid_through,
            verified_invoice_ref=(
                projection.verified_invoice_ref
                if payment_state is not PaymentState.VERIFIED
                else current.invoice_ref or projection.verified_invoice_ref
            ),
        )
        self._store.commit_billing_projection(updated)
        return (
            ReconciliationDisposition.COMPLETE
            if capacity is not None
            else ReconciliationDisposition.UNKNOWN
        )

    def _reconcile(self, attempt: PurchaseAttempt, *, now: datetime) -> ReconciliationDisposition:
        if attempt.environment_ref != self._environment_ref:
            return ReconciliationDisposition.MISMATCH
        catalogue = self._catalogue_reader.resolve(self._environment_ref)
        if catalogue is None or (
            catalogue.catalogue_ref != attempt.catalogue_ref
            or catalogue.version != attempt.catalogue_version
        ):
            return ReconciliationDisposition.UNKNOWN
        if attempt.kind is AttemptKind.INITIAL:
            facts = self._provider.read_checkout_binding(attempt)
            checkout_validation = validate_checkout_binding(
                intent=PurchaseIntent(
                    intent_ref=attempt.intent_ref,
                    attempt_ref=attempt.attempt_ref,
                    catalogue_ref=attempt.catalogue_ref,
                    catalogue_version=attempt.catalogue_version,
                    xeed_capacity=attempt.desired_total,
                    environment_ref=attempt.environment_ref,
                    authorized_at=attempt.authorized_at,
                ),
                catalogue=catalogue,
                binding=facts.binding,
                snapshot=facts.session_snapshot,
            )
            if checkout_validation.status is not CheckoutBindingStatus.VERIFIED:
                return (
                    ReconciliationDisposition.MISMATCH
                    if checkout_validation.status is CheckoutBindingStatus.MISMATCH
                    else ReconciliationDisposition.UNKNOWN
                )
            capacity_validation = validate_subscription_capacity(
                expected_capacity=attempt.desired_total,
                authorized_at=attempt.authorized_at,
                catalogue=catalogue,
                expected_customer_ref=facts.binding.customer_ref,
                expected_subscription_ref=facts.binding.subscription_ref,
                expected_environment_ref=attempt.environment_ref,
                snapshot=facts.current_snapshot,
            )
            if capacity_validation.status is not BindingStatus.VERIFIED:
                return (
                    ReconciliationDisposition.MISMATCH
                    if capacity_validation.status is BindingStatus.MISMATCH
                    else ReconciliationDisposition.UNKNOWN
                )
            if facts.payment_state is not PaymentState.VERIFIED:
                return ReconciliationDisposition.PENDING_PURCHASE
            if facts.lifecycle not in (
                SubscriptionLifecycle.ELIGIBLE,
                SubscriptionLifecycle.CANCEL_AT_PERIOD_END,
            ):
                return ReconciliationDisposition.PENDING_PURCHASE
            return self._commit(
                attempt,
                facts,
                checkout_validation.xeed_capacity,
                now=now,
                capacity_binding=capacity_validation,
            )

        projection = self._store.get_billing_projection(attempt.tenant_id)
        if projection is None or projection.subscription_ref != attempt.subscription_ref:
            return ReconciliationDisposition.UNKNOWN
        current = self._provider.read_current_subscription(projection)
        validation = validate_subscription_capacity(
            expected_capacity=attempt.desired_total,
            authorized_at=attempt.authorized_at,
            catalogue=catalogue,
            expected_customer_ref=projection.customer_ref,
            expected_subscription_ref=projection.subscription_ref,
            expected_environment_ref=self._environment_ref,
            snapshot=current.snapshot,
            previous=projection.binding,
        )
        if validation.status is not BindingStatus.VERIFIED:
            return (
                ReconciliationDisposition.MISMATCH
                if validation.status is BindingStatus.MISMATCH
                else ReconciliationDisposition.UNKNOWN
            )
        if (
            not attempt.invoice_ref
            or not current.invoice_ref
            or current.invoice_ref != attempt.invoice_ref
        ):
            return ReconciliationDisposition.UNKNOWN
        if current.payment_state is not PaymentState.VERIFIED:
            return ReconciliationDisposition.PENDING_PURCHASE
        if (
            current.lifecycle is not SubscriptionLifecycle.ELIGIBLE
            or current.paid_through is None
            or current.paid_through <= now
        ):
            return ReconciliationDisposition.PENDING_PURCHASE
        projection = BillingProjection(
            tenant_id=attempt.tenant_id,
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            checkout_session_ref=projection.checkout_session_ref,
            environment_ref=projection.environment_ref,
            additional_item_ref=current.additional_item_ref,
            effective_capacity=validation.effective_capacity,
            payment_state=current.payment_state,
            lifecycle=current.lifecycle,
            binding=validation,
            provider_state_ref=current.snapshot.provider_state_ref,
            provider_state_at=current.snapshot.provider_state_at,
            paid_through=current.paid_through,
            verified_invoice_ref=current.invoice_ref,
        )
        completed = replace(attempt, status=AttemptStatus.COMPLETE)
        self._store.record_reconciled_purchase(completed, projection)
        return ReconciliationDisposition.COMPLETE

    def _commit(
        self,
        attempt: PurchaseAttempt,
        facts: ProviderCheckoutBinding,
        capacity: int | None,
        *,
        now: datetime,
        capacity_binding: SubscriptionCapacityValidation | None = None,
    ) -> ReconciliationDisposition:
        if capacity is None or facts.payment_state is not PaymentState.VERIFIED:
            return ReconciliationDisposition.PENDING_PURCHASE
        if facts.paid_through is None or facts.paid_through <= now:
            return ReconciliationDisposition.PENDING_PURCHASE
        if facts.binding is not None:
            customer_ref = facts.binding.customer_ref
            subscription_ref = facts.binding.subscription_ref
            session_ref = facts.binding.checkout_session_ref
        else:
            customer_ref = attempt.customer_ref or ""
            subscription_ref = attempt.subscription_ref or ""
            session_ref = attempt.checkout_session_ref or "capacity-update"
        if not customer_ref or not subscription_ref:
            return ReconciliationDisposition.UNKNOWN
        validation = capacity_binding
        if validation is None:
            snapshot = facts.current_snapshot
            validation = SubscriptionCapacityValidation(
                status=BindingStatus.VERIFIED,
                reason=BindingReason.EXACT_MATCH,
                evidence_ref=snapshot.evidence_ref,
                evidence_fingerprint=f"{snapshot.evidence_ref}:{capacity}",
                provider_state_ref=snapshot.provider_state_ref,
                provider_state_at=snapshot.provider_state_at,
                effective_capacity=capacity,
            )
        projection = BillingProjection(
            tenant_id=attempt.tenant_id,
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            checkout_session_ref=session_ref,
            environment_ref=attempt.environment_ref,
            additional_item_ref=attempt.additional_item_ref,
            effective_capacity=capacity,
            payment_state=facts.payment_state,
            lifecycle=facts.lifecycle,
            binding=validation,
            provider_state_ref=validation.provider_state_ref,
            provider_state_at=validation.provider_state_at,
            paid_through=facts.paid_through,
            verified_invoice_ref=facts.invoice_ref,
        )
        completed = replace(
            attempt,
            status=AttemptStatus.COMPLETE,
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            checkout_session_ref=session_ref,
            additional_item_ref=attempt.additional_item_ref,
            invoice_ref=facts.invoice_ref or attempt.invoice_ref,
        )
        self._store.record_reconciled_purchase(completed, projection)
        return ReconciliationDisposition.COMPLETE
