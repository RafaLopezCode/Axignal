# Subscriber Checkout Runtime Contract v1

**Status:** Implemented billing interface; root review/runtime integration remains separate. No HTTP paths defined here.
**Runtime composition:** `tools/runtime/subscriber_checkout.py`
**Use cases:** `application/admin_billing/subscriber_checkout.py` and `subscriber_billing.py`

## Authority input

The route authenticates the request and calls the existing membership authority
before invoking billing. Billing receives the authenticated `Principal`, the
authorized `TenantId`, and `now`. `CurrentPurchaseAuthorityReader` re-reads the
stored principal, current membership and purchase-owner receipt; absent owner
receipt (`None`) blocks mutation. Identity's `ensure_initial_purchase_scope`
stores only the initial REGISTER authority, idempotently; LOGIN does not call it.

```python
start_initial_checkout(*, principal: Principal, tenant_id: TenantId,
                       command: InitialCheckoutCommand, now: datetime)
request_capacity_increase(*, principal: Principal, tenant_id: TenantId,
                          command: CapacityIncreaseCommand, now: datetime)
```

Missing principal, current membership, purchase-owner receipt, or a future
authority-check time blocks the command. Tenant is the capacity-consumption
scope; it is not separately asserted to be a legal payer. Membership and
purchase ownership remain separate facts. Authority is checked again before
provider mutation.

## Approved offer and tax evidence

`ApprovedOfferCatalogue` carries the base/add-on recurring terms and an optional
`ApprovedTaxConfiguration`. Both Stripe Prices must read back active, LIVE,
EUR, monthly licensed/per-unit, exact approved amounts, and
`tax_behavior=exclusive`. Checkout and capacity updates fail with
`TAX_CONFIGURATION_UNKNOWN` unless the injected catalogue contains current
explicit `automatic_tax_enabled=True` evidence, matching the environment and
including at least one confirmed active registration reference. Stripe
TaxSettings status `active` or exclusive Price behavior alone does not satisfy
this evidence. Checkout sends `automatic_tax[enabled]=true`; Session,
Subscription and Invoice reads require the setting to remain enabled. The
approved catalogue is EUR 9.95 monthly for the base and EUR 4.95 monthly per
additional Organization, excluding applicable taxes; it does not authorize a
universal tax rate or assert where AXIGNAL is legally required to collect.
Current root LIVE readback has no active registration, so this bridge presently
blocks checkout and updates. See [approved catalogue evidence](../../../docs/audits/production-readiness-2026-10-06/APPROVED_LIVE_CATALOGUE.md).

## Composition constructor

```python
SubscriberCheckoutRuntime(
    *,
    service: SubscriberCheckoutService,
    webhook: SubscriberBillingWebhook | None,
    config: SubscriberCheckoutRuntimeConfig,
    retry_worker=None,
)
```

`config` requires explicit provider environment, configured allowed redirect
hosts, and a feature-enable flag. Real provider composition is
`build_stripe_subscriber_checkout_runtime(settings, authority_reader,
entitlement_reader, catalogue_reader)`. `StripeSubscriberRuntimeSettings`
requires explicit account/environment/API version, offer and price references,
server success/cancel URLs, redirect allowlists, SQLite path, `enabled`, and
credentials. Missing API key or webhook secret raises `NOT_CONFIGURED` before
any call. `mutations_enabled` defaults false and must be explicitly enabled by
root server configuration. Construction does not contact Stripe. Unit tests use
injected transports and fixtures. This module creates no HTTP routes or deploy
configuration.

## Methods

```python
start_initial_checkout(*, principal, tenant_id, command, now) -> CheckoutStartResult

request_capacity_increase(*, principal, tenant_id, command, now) -> CapacityChangeResult

get_purchase_status(*, principal, tenant_id, request_ref, now) -> PurchaseStatusResult

handle_signed_webhook(
    raw_body: bytes,
    stripe_signature: str,
    received_at: datetime,
) -> WebhookAcceptanceResult

reconcile_pending(*, principal, tenant_id, now) -> tuple[str, ...]
run_reconciliation_retries(*, now, limit=20) -> tuple[str, ...]
```

Webhook receives exact unmodified request bytes for Stripe signature
verification. It validates timestamp tolerance, configured account scope and
livemode before inbox replay lookup, commits bounded refs/fingerprint before
dispatch, and does not use body metadata as identity or capacity authority.
It re-fetches session, subscription, invoice and full item pages through the
provider adapter. `COMPLETE` requires a verified Checkout binding, matching
complete current subscription items and a paid associated latest invoice; a
checkout return URL never grants access. HTTP status mapping is root-owned.

The provider port `update_capacity(projection, *, catalogue, desired_total,
additional_item_ref, idempotency_key, proration_behavior,
payment_behavior)` revalidates current catalogue/registration evidence and the
existing subscription's automatic-tax state immediately before mutation. It
sets absolute additional-item quantity to `desired_total - 1` on the existing
subscription (never creates a second base subscription), with `always_invoice`
and `pending_if_incomplete`. Capacity remains the previously verified amount
until reconciliation verifies the changed complete item set and associated
payment. Prepared attempts retry the same request idempotency key.

## Request and response payload shapes

Initial request (authenticated route derives authority; public body has no
Principal, Tenant, Stripe IDs, prices, or URLs):

```json
{
  "requestRef": "client-generated stable UUID",
  "desiredOrganizationTotal": 2
}
```

`CheckoutStartResult`:

```json
{
  "status": "PENDING_PURCHASE",
  "requestRef": "stable request id",
  "purchaseIntentRef": "opaque server-owned id",
  "effectiveCapacity": null,
  "desiredCapacity": 2,
  "checkoutUrl": "validated HTTPS URL on configured Stripe Checkout host or null",
  "paymentUrl": null,
  "reason": "AWAITING_CHECKOUT_AND_PAYMENT_RECONCILIATION"
}
```

Capacity increase request:

```json
{
  "requestRef": "stable client-generated UUID",
  "desiredOrganizationTotal": 3
}
```

`CapacityChangeResult`:

```json
{
  "status": "PENDING_PURCHASE",
  "requestRef": "stable request id",
  "capacityChangeIntentRef": "opaque server-owned id",
  "effectiveCapacity": 2,
  "desiredCapacity": 3,
  "pendingUpdate": true,
  "paymentUrl": "validated HTTPS Stripe hosted invoice URL or null",
  "reason": "AWAITING_INVOICE_PAYMENT_AND_CURRENT_BINDING"
}
```

Exact replay of the same pending request returns the same intent and provider
references. It does not create another Checkout Session, subscription update or
invoice. A different target while a change is pending returns the same
effective capacity with a conflict/pending reason and no provider mutation.

Status payload has separate states and never collapses UNKNOWN to false:

```json
{
  "requestRef": "stable request id",
  "identityScope": "VERIFIED | UNKNOWN | REVOKED",
  "binding": "VERIFIED | MISMATCH | UNKNOWN",
  "payment": "VERIFIED | FAILED | UNKNOWN",
  "subscriptionLifecycle": "ELIGIBLE | INELIGIBLE | UNKNOWN",
  "effectiveCapacity": 2,
  "desiredCapacity": 3,
  "purchase": "PENDING_PURCHASE | COMPLETE | REJECTED | UNKNOWN",
  "evidenceRefs": ["opaque references"]
}
```

`handle_signed_webhook` returns bounded acceptance only:

```json
{
  "accepted": true,
  "disposition": "STORED | EXACT_REPLAY | QUARANTINED_CONFLICT",
  "eventRef": "opaque provider event reference"
}
```

It never returns an entitlement or marks capacity effective. The subsequent
bounded worker/reconciliation path owns the billing projection transition; the
independent portfolio entitlement evaluator owns access.

## Redirect safety

The `checkoutUrl` and `paymentUrl` are server-derived. Parse and require HTTPS,
no embedded username/password, no custom port, no fragment, and an exact
hostname match against configured environment-specific provider hosts. For
invoice payment, require the retrieved invoice's `hosted_invoice_url` to be
non-null and on the configured Stripe invoice host. For initial checkout,
validate the Session URL against configured Stripe Checkout hosts. On any
failure, return pending with a null URL and safe reason; do not echo arbitrary
provider or request input into a `Location` header.

## Errors and HTTP responsibilities

This contract exposes typed outcomes, not HTTP codes. Root routes map:

- unauthenticated to root auth behavior;
- revoked/non-member to root authorization behavior;
- catalogue/provider not configured or UNKNOWN to unavailable/pending without
  provider mutation;
- idempotency conflict or existing different pending target to conflict with
  effective capacity unchanged;
- accepted webhook metadata only after signature verification and durable store.

Do not expose payment details, raw Stripe event, customer email, account secret,
webhook signature or provider object payload in route responses/logs.
