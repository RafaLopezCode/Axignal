"""Provider-authenticated Stripe webhook runtime for AO-10."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.admin_api_operations import WebhookOperationsService
from application.admin_billing import AdminBillingService
from application.admin_customer_accounts import AdminCustomerAccountService
from application.admin_financial_documents import AdminFinancialDocumentService
from domain.admin_billing import BillingAuthorityGrant, BillingProvider
from domain.admin_integrations import (
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
)
from pipeline.admin_api_operations import SqliteApiOperationsStore
from pipeline.admin_billing import SqliteAdminBillingStore
from pipeline.admin_billing.stripe import (
    StripeEventNormalizer,
    StripeWebhookDependencyError,
    StripeWebhookError,
    StripeWebhookVerifier,
    VerifiedStripeEvent,
    checkout_mapping_from_verified_event,
)
from pipeline.admin_customer_accounts import SqliteAdminCustomerAccountStore
from pipeline.admin_financial_documents import SqliteFinancialDocumentStore


class IntegrationRegistryReader(Protocol):
    def all_definitions(self) -> tuple[IntegrationDefinition, ...]: ...


@dataclass(frozen=True, slots=True)
class StripeWebhookResult:
    event_id: str
    event_type: str
    replayed: bool
    account_id: str


class StripeWebhookRuntime:
    def __init__(
        self,
        *,
        stripe_account_id: str,
        base_price_ref: str,
        additional_xeed_price_ref: str,
        signing_secret: str,
        billing_store: SqliteAdminBillingStore,
        account_store: SqliteAdminCustomerAccountStore,
        integration_store: IntegrationRegistryReader,
        runtime_environment: IntegrationEnvironment,
        require_livemode: bool,
        operations_store: SqliteApiOperationsStore | None = None,
        financial_store: SqliteFinancialDocumentStore | None = None,
    ) -> None:
        if not stripe_account_id.startswith("acct_"):
            raise ValueError("Stripe account id is invalid")
        if not base_price_ref or not additional_xeed_price_ref:
            raise ValueError("Stripe price refs are required")
        self._stripe_account_id = stripe_account_id
        self._base_price_ref = base_price_ref
        self._additional_xeed_price_ref = additional_xeed_price_ref
        self._integration_store = integration_store
        self._runtime_environment = runtime_environment
        self._require_livemode = require_livemode
        self._verifier = StripeWebhookVerifier(signing_secret.encode("utf-8"))
        self._billing_store = billing_store
        self._billing = AdminBillingService(
            billing_store,
            AdminCustomerAccountService(account_store),
        )
        self._normalizer = StripeEventNormalizer(billing_store)
        self._financial_documents = (
            None if financial_store is None else AdminFinancialDocumentService(financial_store)
        )
        self._operations = (
            None if operations_store is None else WebhookOperationsService(operations_store)
        )

    def _require_governed_integration(self) -> IntegrationDefinition:
        matches = tuple(
            definition
            for definition in self._integration_store.all_definitions()
            if definition.integration_id == "stripe-billing"
        )
        if len(matches) != 1:
            raise StripeWebhookError("Stripe integration is not governed by AO-18")
        definition = matches[0]
        if definition.provider.casefold() != "stripe":
            raise StripeWebhookError("Stripe integration provider mismatch")
        if not definition.enabled:
            raise StripeWebhookError("Stripe integration is disabled")
        if definition.environment is not self._runtime_environment:
            raise StripeWebhookError("Stripe integration environment mismatch")
        if definition.direction not in {
            IntegrationDirection.INBOUND,
            IntegrationDirection.BIDIRECTIONAL,
        }:
            raise StripeWebhookError("Stripe integration does not allow inbound events")
        if not definition.webhook_capable:
            raise StripeWebhookError("Stripe integration is not webhook-capable")
        if definition.credential.state not in {
            CredentialState.CONFIGURED,
            CredentialState.ROTATION_DUE,
        }:
            raise StripeWebhookError("Stripe integration credential metadata is not usable")
        if definition.credential.reference is None:
            raise StripeWebhookError("Stripe integration credential reference is missing")
        return definition

    def _process_verified(
        self,
        *,
        verified: VerifiedStripeEvent,
        received_at: datetime,
    ) -> StripeWebhookResult:
        authority = BillingAuthorityGrant(
            provider=BillingProvider.STRIPE,
            integration_id="stripe-billing",
            provider_event_id=verified.event_id,
            verified_at=received_at,
        )
        if verified.event_type == "checkout.session.completed":
            mapping, capacity = checkout_mapping_from_verified_event(
                verified,
                base_price_ref=self._base_price_ref,
                additional_xeed_price_ref=self._additional_xeed_price_ref,
                recorded_at=received_at,
            )
            checkout_result = self._billing.register_verified_checkout(
                authority=authority,
                mapping=mapping,
                xeed_capacity=capacity,
                now=received_at,
            )
            return StripeWebhookResult(
                event_id=verified.event_id,
                event_type=verified.event_type,
                replayed=not checkout_result.mapping_created,
                account_id=checkout_result.account_id,
            )

        event = self._normalizer.normalize(verified, recorded_at=received_at)
        ingest_result = self._billing.ingest_verified_event(
            authority=authority,
            event=event,
            now=received_at,
        )
        if self._financial_documents is not None:
            self._financial_documents.ingest_billing_event(event)
        return StripeWebhookResult(
            event_id=verified.event_id,
            event_type=verified.event_type,
            replayed=ingest_result.replayed,
            account_id=ingest_result.account_id,
        )

    def handle(
        self,
        *,
        payload: bytes,
        signature_header: str,
        received_at: datetime,
    ) -> StripeWebhookResult:
        self._require_governed_integration()
        verified = self._verifier.verify(
            payload=payload,
            signature_header=signature_header,
            received_at=received_at,
        )
        account = verified.payload.get("account")
        if account is not None and account != self._stripe_account_id:
            raise StripeWebhookError("Stripe event account does not match AXIGNAL merchant")
        livemode = verified.payload.get("livemode")
        if self._require_livemode and livemode is not True:
            raise StripeWebhookError("production Stripe webhook requires livemode event")
        if not self._require_livemode and livemode is True:
            raise StripeWebhookError("non-production Stripe webhook rejects livemode event")

        if self._operations is None:
            return self._process_verified(verified=verified, received_at=received_at)

        envelope, result, _replayed = self._operations.receive_and_process(
            integration_id="stripe-billing",
            provider_event_id=verified.event_id,
            event_type=verified.event_type,
            payload=payload,
            schema_version="stripe-event-v1",
            received_at=received_at,
            processor=lambda: self._process_verified(
                verified=verified,
                received_at=received_at,
            ),
            transient_exceptions=(StripeWebhookDependencyError, LookupError),
        )
        if result is not None:
            return result
        if envelope.disposition.value == "SUCCEEDED":
            # Signature was verified above. Re-running the existing AO-10 handler
            # is safe because provider event identity is idempotent at billing/account stores.
            replay_result = self._process_verified(verified=verified, received_at=received_at)
            return StripeWebhookResult(
                event_id=replay_result.event_id,
                event_type=replay_result.event_type,
                replayed=True,
                account_id=replay_result.account_id,
            )
        if envelope.disposition.value == "DEAD_LETTER":
            raise StripeWebhookDependencyError("Stripe webhook exhausted AO-19 retry budget")
        raise StripeWebhookError("Stripe webhook is not processable")
