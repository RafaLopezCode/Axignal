"""Stripe adapter for subscriber Checkout, updates and complete current reads."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from application.admin_billing.subscriber_billing import (
    PaymentState,
    SubscriptionLifecycle,
)
from application.admin_billing.subscriber_checkout import (
    BillingProjection,
    CapacityUpdateResponse,
    CreatedCheckoutSession,
    ProviderCheckoutBinding,
    ProviderCurrentSubscription,
    PurchaseAttempt,
)
from domain.admin_billing.checkout_binding import (
    ApprovedOfferCatalogue,
    ApprovedTaxConfiguration,
    CheckoutAttemptBinding,
    CurrentSubscriptionItems,
    NormalizedRecurringItem,
    PurchaseIntent,
    RecurringTerms,
    SnapshotCurrentness,
    SubscriptionItemSnapshot,
)


class StripeSubscriberError(RuntimeError):
    """A provider failure safe to expose as a bounded category."""


class StripeSubscriberConflict(StripeSubscriberError):
    pass


class StripeTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        parameters: Mapping[str, str],
        idempotency_key: str | None = None,
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class StripeSubscriberConfig:
    environment_ref: str
    account_ref: str
    live_mode: bool
    api_version: str
    base_offer_ref: str
    additional_offer_ref: str
    price_refs: Mapping[str, str]
    success_url: str
    cancel_url: str
    api_key: str = field(repr=False)
    mutations_enabled: bool = False
    api_base: str = "https://api.stripe.com"

    def __post_init__(self) -> None:
        for name, value in (
            ("environment_ref", self.environment_ref),
            ("account_ref", self.account_ref),
            ("api_version", self.api_version),
            ("base_offer_ref", self.base_offer_ref),
            ("additional_offer_ref", self.additional_offer_ref),
            ("api_key", self.api_key),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.account_ref.startswith("acct_"):
            raise ValueError("direct Stripe account reference is invalid")
        parsed = urllib.parse.urlsplit(self.api_base)
        if parsed.scheme != "https" or parsed.hostname != "api.stripe.com":
            raise ValueError("Stripe API base must use the official HTTPS host")
        for url in (self.success_url, self.cancel_url):
            parsed_url = urllib.parse.urlsplit(url)
            if parsed_url.scheme != "https" or not parsed_url.hostname:
                raise ValueError("Checkout return URLs must be absolute HTTPS URLs")
        if not self.price_refs or any(
            not key or not value.startswith("price_") for key, value in self.price_refs.items()
        ):
            raise ValueError("configured offer references must map to Stripe Price IDs")
        if (
            self.base_offer_ref not in self.price_refs
            or self.additional_offer_ref not in self.price_refs
        ):
            raise ValueError("base and additional offers must both have configured Stripe Prices")


class UrllibStripeTransport:
    """Small no-redirect HTTPS form transport; secret values are never logged."""

    def __init__(self, config: StripeSubscriberConfig, *, timeout_seconds: float = 10.0) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        path: str,
        *,
        parameters: Mapping[str, str],
        idempotency_key: str | None = None,
    ) -> Mapping[str, object]:
        if not path.startswith("/v1/") or "://" in path or ".." in path:
            raise StripeSubscriberError("invalid Stripe API path")
        encoded = urllib.parse.urlencode(parameters)
        url = f"{self._config.api_base}{path}"
        body: bytes | None = None
        if method.upper() == "GET":
            if encoded:
                url = f"{url}?{encoded}"
        elif method.upper() == "POST":
            body = encoded.encode("ascii")
        else:
            raise StripeSubscriberError("unsupported Stripe API method")
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Stripe-Version": self._config.api_version,
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        opener = urllib.request.build_opener(_RejectRedirects())
        try:
            with opener.open(request, timeout=self._timeout_seconds) as response:
                response_body = response.read(8_388_609)
                if len(response_body) > 8_388_608:
                    raise StripeSubscriberError("Stripe response exceeds supported size")
                payload = json.loads(response_body)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            raise StripeSubscriberError("Stripe transport request failed") from None
        if not isinstance(payload, dict):
            raise StripeSubscriberError("Stripe API returned a malformed object")
        return payload


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class StripeSubscriberAdapter:
    """Implements provider-neutral subscriber billing port for one direct account."""

    def __init__(
        self,
        *,
        config: StripeSubscriberConfig,
        transport: StripeTransport,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._transport = transport
        self._clock = clock or (lambda: datetime.now(UTC))
        self._account_verified = False

    def _require_mutations(self) -> None:
        if not self._config.mutations_enabled:
            raise StripeSubscriberError("Stripe subscriber mutations are disabled")

    def _request(
        self,
        method: str,
        path: str,
        parameters: Mapping[str, str] | None = None,
        *,
        idempotency_key: str | None = None,
    ) -> Mapping[str, object]:
        self._verify_account()
        try:
            return self._transport.request(
                method,
                path,
                parameters={} if parameters is None else parameters,
                idempotency_key=idempotency_key,
            )
        except StripeSubscriberError:
            raise
        except Exception:
            raise StripeSubscriberError("Stripe provider dependency failed") from None

    def _verify_account(self) -> None:
        if self._account_verified:
            return
        try:
            account = self._transport.request("GET", "/v1/account", parameters={})
        except StripeSubscriberError:
            raise
        except Exception:
            raise StripeSubscriberError("Stripe account verification failed") from None
        if account.get("id") != self._config.account_ref:
            raise StripeSubscriberConflict("Stripe account does not match configured merchant")
        self._account_verified = True

    def verify_catalogue(self, catalogue: ApprovedOfferCatalogue) -> bool:
        for offer in (catalogue.base_offer, catalogue.additional_xeed_offer):
            price_ref = self._config.price_refs.get(offer.offer_ref)
            if price_ref is None:
                return False
            price = self._request("GET", f"/v1/prices/{price_ref}")
            recurring = price.get("recurring")
            if not isinstance(recurring, dict):
                return False
            if (
                price.get("id") != price_ref
                or price.get("active") is not True
                or price.get("livemode") is not self._config.live_mode
                or price.get("billing_scheme") != "per_unit"
                or price.get("type") != "recurring"
                or price.get("transform_quantity") is not None
                or price.get("tiers_mode") is not None
                or price.get("currency") != offer.terms.currency.casefold()
                or price.get("tax_behavior") != offer.terms.tax_behavior
                or type(price.get("unit_amount")) is not int
                or price.get("unit_amount") != offer.terms.unit_amount_minor
                or recurring.get("interval") != offer.terms.interval_unit
                or type(recurring.get("interval_count")) is not int
                or recurring.get("interval_count") != offer.terms.interval_count
            ):
                return False
        return True

    def create_initial_checkout(
        self,
        intent: PurchaseIntent,
        catalogue: ApprovedOfferCatalogue,
        *,
        idempotency_key: str,
    ) -> CreatedCheckoutSession:
        self._require_mutations()
        if intent.environment_ref != self._config.environment_ref:
            raise StripeSubscriberConflict("intent environment does not match Stripe configuration")
        if (
            intent.catalogue_ref != catalogue.catalogue_ref
            or intent.catalogue_version != catalogue.version
        ):
            raise StripeSubscriberConflict("intent offer catalogue does not match")
        if not self.verify_catalogue(catalogue):
            raise StripeSubscriberConflict(
                "configured Stripe prices do not match approved catalogue"
            )
        _require_tax_configuration(
            catalogue.tax_configuration, self._config.environment_ref, self._clock()
        )
        base_ref = self._config.price_refs[catalogue.base_offer.offer_ref]
        additional_ref = self._config.price_refs[catalogue.additional_xeed_offer.offer_ref]
        parameters: dict[str, str] = {
            "mode": "subscription",
            "success_url": self._config.success_url,
            "cancel_url": self._config.cancel_url,
            "client_reference_id": intent.intent_ref,
            "line_items[0][price]": base_ref,
            "line_items[0][quantity]": "1",
            "metadata[axignal_intent_ref]": intent.intent_ref,
            "metadata[axignal_attempt_ref]": intent.attempt_ref,
            "subscription_data[metadata][axignal_intent_ref]": intent.intent_ref,
            "automatic_tax[enabled]": "true",
        }
        if intent.xeed_capacity > 1:
            parameters["line_items[1][price]"] = additional_ref
            parameters["line_items[1][quantity]"] = str(intent.xeed_capacity - 1)
        session = self._request(
            "POST",
            "/v1/checkout/sessions",
            parameters,
            idempotency_key=idempotency_key,
        )
        if session.get("livemode") is not self._config.live_mode:
            raise StripeSubscriberConflict("Checkout Session mode does not match configuration")
        automatic_tax = session.get("automatic_tax")
        if not isinstance(automatic_tax, dict) or automatic_tax.get("enabled") is not True:
            raise StripeSubscriberConflict("Checkout Session automatic tax is not enabled")
        session_ref = _required_text(session, "id")
        customer_ref = _optional_text(session.get("customer"))
        subscription_ref = _optional_text(session.get("subscription"))
        redirect_url = _required_text(session, "url")
        return CreatedCheckoutSession(session_ref, customer_ref, subscription_ref, redirect_url)

    def read_current_subscription(
        self,
        projection: BillingProjection,
    ) -> ProviderCurrentSubscription:
        subscription = self._request("GET", f"/v1/subscriptions/{projection.subscription_ref}")
        self._assert_subscription_identity(subscription, projection)
        _require_automatic_tax(subscription)
        items = self._all_subscription_items(projection.subscription_ref)
        normalized = tuple(self._normalize_item(item) for item in items)
        state_updated = subscription.get("updated")
        if type(state_updated) is not int:
            raise StripeSubscriberError("Stripe subscription currentness is unknown")
        retrieved_at = self._clock()
        state_at = datetime.fromtimestamp(state_updated, UTC)
        payment_state, payment_ref, payment_at = self._read_latest_invoice_evidence(
            subscription, projection
        )
        if payment_at is not None:
            state_at = max(state_at, payment_at)
        snapshot = CurrentSubscriptionItems(
            evidence_ref=f"stripe:subscription:{projection.subscription_ref}:{state_at.timestamp()}:{payment_ref or 'unknown'}",
            customer_ref=projection.customer_ref,
            subscription_ref=projection.subscription_ref,
            environment_ref=self._config.environment_ref,
            provider_state_ref=f"updated:{state_updated};payment:{payment_ref or 'unknown'}",
            provider_state_at=state_at,
            retrieved_at=retrieved_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=normalized,
        )
        lifecycle = self._lifecycle(subscription)
        paid_through = _paid_through(subscription, items)
        additional_item_ref = self._additional_item_ref(normalized)
        return ProviderCurrentSubscription(
            snapshot=snapshot,
            payment_state=payment_state,
            lifecycle=lifecycle,
            paid_through=paid_through,
            additional_item_ref=additional_item_ref,
            invoice_ref=_optional_text(subscription.get("latest_invoice")),
        )

    def read_checkout_binding(self, attempt: PurchaseAttempt) -> ProviderCheckoutBinding:
        """Read a completed session, all session lines, subscription, and invoice."""
        if attempt.checkout_session_ref is None:
            raise StripeSubscriberError("checkout attempt has no durable session reference")
        session = self._request("GET", f"/v1/checkout/sessions/{attempt.checkout_session_ref}")
        session_ref = _required_text(session, "id")
        customer_ref = _optional_text(session.get("customer"))
        subscription_ref = _optional_text(session.get("subscription"))
        if (
            session_ref != attempt.checkout_session_ref
            or session.get("livemode") is not self._config.live_mode
            or session.get("mode") != "subscription"
            or session.get("status") != "complete"
            or customer_ref is None
            or subscription_ref is None
        ):
            raise StripeSubscriberConflict("Checkout Session is not complete for this attempt")
        if session.get("client_reference_id") != attempt.intent_ref:
            raise StripeSubscriberConflict("Checkout Session intent correlation does not match")
        metadata = session.get("metadata")
        metadata_intent = metadata.get("axignal_intent_ref") if isinstance(metadata, dict) else None
        metadata_attempt = (
            metadata.get("axignal_attempt_ref") if isinstance(metadata, dict) else None
        )
        if metadata_intent != attempt.intent_ref or metadata_attempt != attempt.attempt_ref:
            raise StripeSubscriberConflict("Checkout Session attempt correlation does not match")
        session_items = self._all_checkout_session_items(session_ref)
        subscription = self._request("GET", f"/v1/subscriptions/{subscription_ref}")
        projection = BillingProjection(
            tenant_id=attempt.tenant_id,
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            checkout_session_ref=session_ref,
            environment_ref=self._config.environment_ref,
            additional_item_ref=None,
            effective_capacity=None,
            payment_state=PaymentState.UNKNOWN,
            lifecycle=SubscriptionLifecycle.UNKNOWN,
            binding=None,
            provider_state_ref=None,
            provider_state_at=None,
            paid_through=None,
        )
        self._assert_subscription_identity(subscription, projection)
        _require_automatic_tax(subscription)
        sub_items = self._all_subscription_items(subscription_ref)
        normalized = tuple(self._normalize_item(item) for item in sub_items)
        state_updated = subscription.get("updated")
        if type(state_updated) is not int:
            raise StripeSubscriberError("Stripe subscription currentness is unknown")
        retrieved_at = self._clock()
        state_at = datetime.fromtimestamp(state_updated, UTC)
        payment, payment_ref, payment_at = self._read_latest_invoice_evidence(
            subscription, projection
        )
        if payment_at is not None:
            state_at = max(state_at, payment_at)
        current_snapshot = CurrentSubscriptionItems(
            evidence_ref=f"stripe:subscription:{subscription_ref}:{state_at.timestamp()}:{payment_ref or 'unknown'}",
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            environment_ref=self._config.environment_ref,
            provider_state_ref=f"updated:{state_updated};payment:{payment_ref or 'unknown'}",
            provider_state_at=state_at,
            retrieved_at=retrieved_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            items=normalized,
        )
        session_updated = session.get("created")
        if type(session_updated) is not int:
            raise StripeSubscriberError("Checkout Session creation time is unknown")
        binding = CheckoutAttemptBinding(
            binding_ref=f"stripe:checkout-binding:{attempt.attempt_ref}",
            intent_ref=attempt.intent_ref,
            attempt_ref=attempt.attempt_ref,
            checkout_session_ref=session_ref,
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            environment_ref=self._config.environment_ref,
            established_at=datetime.fromtimestamp(session_updated, UTC),
        )
        session_snapshot = SubscriptionItemSnapshot(
            evidence_ref=f"stripe:checkout-lines:{session_ref}:{session_updated}",
            checkout_session_ref=session_ref,
            customer_ref=customer_ref,
            subscription_ref=subscription_ref,
            environment_ref=self._config.environment_ref,
            provider_state_ref=f"checkout-created:{session_updated}",
            provider_state_at=datetime.fromtimestamp(session_updated, UTC),
            retrieved_at=retrieved_at,
            currentness=SnapshotCurrentness.CURRENT,
            enumeration_complete=True,
            has_more=False,
            metadata_intent_ref=metadata_intent if isinstance(metadata_intent, str) else None,
            items=tuple(self._normalize_item(item) for item in session_items),
        )
        invoice_ref = _optional_text(subscription.get("latest_invoice"))
        return ProviderCheckoutBinding(
            binding=binding,
            session_snapshot=session_snapshot,
            current_snapshot=current_snapshot,
            payment_state=payment,
            lifecycle=self._lifecycle(subscription),
            paid_through=_paid_through(subscription, sub_items),
            invoice_ref=invoice_ref,
        )

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
    ) -> CapacityUpdateResponse:
        self._require_mutations()
        if proration_behavior != "always_invoice" or payment_behavior != "pending_if_incomplete":
            raise StripeSubscriberConflict("unsupported subscription update payment policy")
        if desired_total <= 1 or type(desired_total) is not int:
            raise StripeSubscriberConflict(
                "capacity increase must request at least two Organizations"
            )
        if projection.environment_ref != self._config.environment_ref:
            raise StripeSubscriberConflict("subscription environment does not match configuration")
        _require_tax_configuration(
            catalogue.tax_configuration, self._config.environment_ref, self._clock()
        )
        if not self.verify_catalogue(catalogue):
            raise StripeSubscriberConflict(
                "configured Stripe prices do not match approved catalogue"
            )
        current = self._request("GET", f"/v1/subscriptions/{projection.subscription_ref}")
        self._assert_subscription_identity(current, projection)
        _require_automatic_tax(current)
        if additional_item_ref is None:
            additional_price_ref = self._additional_price_ref()
            params = {
                "subscription": projection.subscription_ref,
                "price": additional_price_ref,
                "quantity": str(desired_total - 1),
                "proration_behavior": proration_behavior,
                "payment_behavior": payment_behavior,
            }
            updated = self._request(
                "POST",
                "/v1/subscription_items",
                params,
                idempotency_key=idempotency_key,
            )
            item_ref = _required_text(updated, "id")
            subscription = self._request("GET", f"/v1/subscriptions/{projection.subscription_ref}")
            invoice_ref = _optional_text(subscription.get("latest_invoice"))
        else:
            params = {
                "items[0][id]": additional_item_ref,
                "items[0][quantity]": str(desired_total - 1),
                "proration_behavior": proration_behavior,
                "payment_behavior": payment_behavior,
            }
            subscription = self._request(
                "POST",
                f"/v1/subscriptions/{projection.subscription_ref}",
                params,
                idempotency_key=idempotency_key,
            )
            item_ref = additional_item_ref
            invoice_ref = _optional_text(subscription.get("latest_invoice"))
        self._assert_subscription_identity(subscription, projection)
        pending_update = isinstance(subscription.get("pending_update"), dict)
        hosted_url: str | None = None
        if invoice_ref is not None:
            invoice = self._request("GET", f"/v1/invoices/{invoice_ref}")
            if (
                invoice.get("id") != invoice_ref
                or invoice.get("customer") != projection.customer_ref
                or invoice.get("livemode") is not self._config.live_mode
                or _invoice_subscription_ref(invoice) != projection.subscription_ref
                or not _automatic_tax_enabled(invoice)
            ):
                raise StripeSubscriberConflict("proration invoice does not match subscription")
            hosted_url = _optional_text(invoice.get("hosted_invoice_url"))
        return CapacityUpdateResponse(
            subscription_ref=projection.subscription_ref,
            customer_ref=projection.customer_ref,
            additional_item_ref=item_ref,
            invoice_ref=invoice_ref,
            hosted_invoice_url=hosted_url,
            pending_update=pending_update,
        )

    def _all_subscription_items(self, subscription_ref: str) -> list[Mapping[str, object]]:
        result: list[Mapping[str, object]] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        seen_ids: set[str] = set()
        for _ in range(100):
            params = {"subscription": subscription_ref, "limit": "100"}
            if cursor is not None:
                params["starting_after"] = cursor
            page = self._request("GET", "/v1/subscription_items", params)
            data = page.get("data")
            has_more = page.get("has_more")
            if not isinstance(data, list) or type(has_more) is not bool:
                raise StripeSubscriberError("subscription item page is incomplete")
            for item in data:
                if not isinstance(item, dict):
                    raise StripeSubscriberError("subscription item shape is invalid")
                item_id = _required_text(item, "id")
                if item_id in seen_ids:
                    raise StripeSubscriberConflict("duplicate subscription item across pages")
                seen_ids.add(item_id)
                result.append(item)
            if has_more is False:
                return result
            if not data:
                raise StripeSubscriberError("pagination claims more items but page is empty")
            cursor = _required_text(data[-1], "id")
            if cursor in seen_cursors:
                raise StripeSubscriberConflict("subscription item pagination cursor repeated")
            seen_cursors.add(cursor)
        raise StripeSubscriberError("subscription item pagination exceeded page limit")

    def _all_checkout_session_items(self, session_ref: str) -> list[Mapping[str, object]]:
        result: list[Mapping[str, object]] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        seen_ids: set[str] = set()
        for _ in range(100):
            params = {"limit": "100"}
            if cursor is not None:
                params["starting_after"] = cursor
            page = self._request("GET", f"/v1/checkout/sessions/{session_ref}/line_items", params)
            data, has_more = page.get("data"), page.get("has_more")
            if not isinstance(data, list) or type(has_more) is not bool:
                raise StripeSubscriberError("Checkout line-item page is incomplete")
            for item in data:
                if not isinstance(item, dict):
                    raise StripeSubscriberError("Checkout line-item shape is invalid")
                item_id = _required_text(item, "id")
                if item_id in seen_ids:
                    raise StripeSubscriberConflict("duplicate Checkout line item across pages")
                seen_ids.add(item_id)
                result.append(item)
            if has_more is False:
                return result
            if not data:
                raise StripeSubscriberError("Checkout pagination claims more items but is empty")
            cursor = _required_text(data[-1], "id")
            if cursor in seen_cursors:
                raise StripeSubscriberConflict("Checkout pagination cursor repeated")
            seen_cursors.add(cursor)
        raise StripeSubscriberError("Checkout line-item pagination exceeded page limit")

    def _normalize_item(self, item: Mapping[str, object]) -> NormalizedRecurringItem:
        price = item.get("price")
        if not isinstance(price, dict):
            return NormalizedRecurringItem(
                item_ref=_required_text(item, "id"),
                offer_ref=None,
                quantity=_int_or_none(item.get("quantity")),
                recurring=None,
                terms=None,
            )
        price_ref = _optional_text(price.get("id"))
        offer_ref = self._offer_ref_for_price(price_ref)
        recurring_raw = price.get("recurring")
        recurring = isinstance(recurring_raw, dict)
        terms: RecurringTerms | None = None
        if recurring and isinstance(recurring_raw, dict):
            interval = recurring_raw.get("interval")
            interval_count = recurring_raw.get("interval_count")
            amount = price.get("unit_amount")
            currency = price.get("currency")
            tax_behavior = price.get("tax_behavior")
            if (
                isinstance(interval, str)
                and type(interval_count) is int
                and isinstance(currency, str)
                and tax_behavior in {"exclusive", "inclusive"}
                and type(amount) is int
            ):
                terms = RecurringTerms(interval, interval_count, currency, amount, tax_behavior)
        return NormalizedRecurringItem(
            item_ref=_required_text(item, "id"),
            offer_ref=offer_ref,
            quantity=_int_or_none(item.get("quantity")),
            recurring=recurring,
            terms=terms,
        )

    def _offer_ref_for_price(self, price_ref: str | None) -> str | None:
        if price_ref is None:
            return None
        return next(
            (ref for ref, configured in self._config.price_refs.items() if configured == price_ref),
            None,
        )

    def _additional_price_ref(self) -> str:
        price_ref = self._config.price_refs.get(self._config.additional_offer_ref)
        if price_ref is None:
            raise StripeSubscriberError("additional recurring price is not configured")
        return price_ref

    def _additional_item_ref(self, items: tuple[NormalizedRecurringItem, ...]) -> str | None:
        additional_price = self._additional_price_ref()
        refs = [
            item.item_ref
            for item in items
            if item.offer_ref == self._config.additional_offer_ref
            and self._config.price_refs.get(item.offer_ref) == additional_price
        ]
        if len(refs) > 1:
            raise StripeSubscriberConflict("subscription has duplicate additional price items")
        return refs[0] if refs else None

    def _assert_subscription_identity(
        self, subscription: Mapping[str, object], projection: BillingProjection
    ) -> None:
        if (
            subscription.get("id") != projection.subscription_ref
            or subscription.get("customer") != projection.customer_ref
            or subscription.get("livemode") is not self._config.live_mode
        ):
            raise StripeSubscriberConflict(
                "provider subscription identity does not match billing scope"
            )

    def _read_latest_invoice(
        self, subscription: Mapping[str, object], projection: BillingProjection
    ) -> PaymentState:
        return self._read_latest_invoice_evidence(subscription, projection)[0]

    def _read_latest_invoice_evidence(
        self, subscription: Mapping[str, object], projection: BillingProjection
    ) -> tuple[PaymentState, str | None, datetime | None]:
        invoice_ref = _optional_text(subscription.get("latest_invoice"))
        if invoice_ref is None:
            return PaymentState.UNKNOWN, None, None
        invoice = self._request("GET", f"/v1/invoices/{invoice_ref}")
        if (
            invoice.get("id") != invoice_ref
            or invoice.get("customer") != projection.customer_ref
            or invoice.get("livemode") is not self._config.live_mode
            or _invoice_subscription_ref(invoice) != projection.subscription_ref
        ):
            raise StripeSubscriberConflict("latest invoice does not match subscription")
        if not _automatic_tax_enabled(invoice):
            return PaymentState.UNKNOWN, f"invoice:{invoice_ref}:automatic-tax-unknown", None
        status = invoice.get("status")
        invoice_updated = invoice.get("status_transitions")
        paid_at = invoice_updated.get("paid_at") if isinstance(invoice_updated, dict) else None
        if status == "paid":
            payment_intent_ref = _optional_text(invoice.get("payment_intent"))
            if payment_intent_ref is None:
                return PaymentState.UNKNOWN, f"invoice:{invoice_ref}:missing-payment-intent", None
            intent = self._request("GET", f"/v1/payment_intents/{payment_intent_ref}")
            if (
                intent.get("id") != payment_intent_ref
                or intent.get("livemode") is not self._config.live_mode
                or intent.get("status") != "succeeded"
            ):
                return (
                    PaymentState.UNKNOWN,
                    f"payment-intent:{payment_intent_ref}:not-succeeded",
                    None,
                )
            charge_ref = _optional_text(intent.get("latest_charge"))
            if charge_ref is None:
                return (
                    PaymentState.UNKNOWN,
                    f"payment-intent:{payment_intent_ref}:missing-charge",
                    None,
                )
            charge = self._request("GET", f"/v1/charges/{charge_ref}")
            if (
                charge.get("id") != charge_ref
                or charge.get("livemode") is not self._config.live_mode
                or charge.get("payment_intent") != payment_intent_ref
            ):
                raise StripeSubscriberConflict("charge does not match paid invoice")
            amount_refunded = charge.get("amount_refunded")
            if (
                type(amount_refunded) is not int
                or amount_refunded > 0
                or charge.get("refunded") is True
            ):
                return PaymentState.UNKNOWN, f"charge:{charge_ref}:refunded-or-unknown", None
            if charge.get("disputed") is True or self._has_dispute(charge_ref):
                return PaymentState.UNKNOWN, f"charge:{charge_ref}:disputed-or-unknown", None
            payment_at = datetime.fromtimestamp(paid_at, UTC) if type(paid_at) is int else None
            intent_created = intent.get("created")
            intent_at = (
                datetime.fromtimestamp(intent_created, UTC) if type(intent_created) is int else None
            )
            state_at = max(
                (value for value in (payment_at, intent_at) if value is not None), default=None
            )
            return (
                PaymentState.VERIFIED,
                f"invoice:{invoice_ref}:pi:{payment_intent_ref}:charge:{charge_ref}",
                state_at,
            )
        if status in {"open", "uncollectible", "void"}:
            updated_at = invoice.get("updated")
            at = datetime.fromtimestamp(updated_at, UTC) if type(updated_at) is int else None
            return PaymentState.FAILED, f"invoice:{invoice_ref}:{status}", at
        return PaymentState.UNKNOWN, f"invoice:{invoice_ref}:unknown-status", None

    def _has_dispute(self, charge_ref: str) -> bool:
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(100):
            params = {"charge": charge_ref, "limit": "100"}
            if cursor is not None:
                params["starting_after"] = cursor
            page = self._request("GET", "/v1/disputes", params)
            data, has_more = page.get("data"), page.get("has_more")
            if not isinstance(data, list) or type(has_more) is not bool:
                raise StripeSubscriberError("dispute enumeration is incomplete")
            if data:
                return True
            if has_more is False:
                return False
            if not data:
                raise StripeSubscriberError("dispute pagination is incomplete")
            dispute_ref = _required_text(data[-1], "id")
            if dispute_ref in seen:
                raise StripeSubscriberConflict("dispute pagination cursor repeated")
            seen.add(dispute_ref)
            cursor = dispute_ref
        raise StripeSubscriberError("dispute pagination exceeded page limit")

    @staticmethod
    def _lifecycle(subscription: Mapping[str, object]) -> SubscriptionLifecycle:
        status = subscription.get("status")
        if subscription.get("cancel_at_period_end") is True:
            return SubscriptionLifecycle.CANCEL_AT_PERIOD_END
        if status == "active":
            return SubscriptionLifecycle.ELIGIBLE
        if status in {"past_due", "unpaid", "incomplete_expired"}:
            return SubscriptionLifecycle.OVERDUE
        if status == "canceled":
            return SubscriptionLifecycle.CANCELED
        return SubscriptionLifecycle.UNKNOWN


def _required_text(value: Mapping[str, object], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise StripeSubscriberError(f"Stripe response is missing {key}")
    return result


def _automatic_tax_enabled(value: Mapping[str, object]) -> bool:
    automatic_tax = value.get("automatic_tax")
    return isinstance(automatic_tax, dict) and automatic_tax.get("enabled") is True


def _require_automatic_tax(value: Mapping[str, object]) -> None:
    if not _automatic_tax_enabled(value):
        raise StripeSubscriberConflict("Stripe automatic tax is not enabled")


def _require_tax_configuration(
    configuration: ApprovedTaxConfiguration | None,
    environment_ref: str,
    now: datetime,
) -> None:
    if configuration is None or not configuration.is_current(environment_ref, now):
        raise StripeSubscriberConflict("approved tax configuration is not current")


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    if isinstance(value, dict):
        result = value.get("id")
        if isinstance(result, str) and result.strip():
            return result
    return None


def _int_or_none(value: object) -> int | None:
    return value if type(value) is int else None


def _invoice_subscription_ref(invoice: Mapping[str, object]) -> str | None:
    legacy = _optional_text(invoice.get("subscription"))
    if legacy is not None:
        return legacy
    parent = invoice.get("parent")
    if isinstance(parent, dict):
        details = parent.get("subscription_details")
        if isinstance(details, dict):
            return _optional_text(details.get("subscription"))
    return None


def _paid_through(
    subscription: Mapping[str, object], items: list[Mapping[str, object]]
) -> datetime | None:
    raw = subscription.get("current_period_end")
    if type(raw) is int:
        return datetime.fromtimestamp(raw, UTC)
    periods: list[int] = []
    for item in items:
        period = item.get("current_period_end")
        if type(period) is int:
            periods.append(period)
    if periods:
        return datetime.fromtimestamp(max(periods), UTC)
    return None
