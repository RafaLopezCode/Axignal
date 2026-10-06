# Phase B Architecture Proposal â€” Subscriber Checkout and Billing E2E

**Status:** Awaiting root architecture approval; design only, no runtime changes authorized yet
**Date:** 2026-10-06
**Feature:** `047-subscriber-billing-bridge`
**Scope owner:** subscriber billing; runtime HTTP routes remain coordinated by root

## Decision boundary

The human has explicitly selected Stripe LIVE as the development path. This
proposal therefore does not require a sandbox or claim one is available. Root
owns any Stripe writes. This phase may prepare and verify catalogue/configuration
and create a LIVE Checkout Session only after the design and concrete request
are reviewed; it must not complete a real payment. No live provider write is
performed by this proposal. Fixtures and provider fakes remain deterministic
offline tests and must never be represented as sandbox evidence.

ADR-0061 currently says sandbox E2E is required before live enablement. That
existing accepted gate conflicts with the new explicit live-only direction and
must be reconciled by root before production enablement. This proposal does not
silently edit or weaken the ADR. A non-completed LIVE Checkout validates only
session creation and read-back; it cannot prove `invoice.paid`, paid access,
refund, cancellation, retry, or reconciliation behavior. Until authorized
real payment lifecycle evidence exists, those states remain fixture-tested
only and no subscriber entitlement is granted from them.

## Target flow and authorities

```text
HTTP route (root-owned)
  â†’ authenticated Principal + selected Tenant (identity boundary, unresolved)
  â†’ membership and purchase-scope authorization (AXIGNAL-owned)
  â†’ approved immutable offer catalogue + immutable PurchaseIntent
  â†’ durable CheckoutAttempt before network call
  â†’ Stripe LIVE Checkout Session (idempotency key = attempt reference)
  â†’ signed webhook inbox (event identity + payload fingerprint; durable)
  â†’ retrieve current Session + all pages of Session line items
  â†’ retrieve current Subscription + all pages of Subscription items
  â†’ Phase-A provider-neutral `validate_checkout_binding`
  â†’ independent billing/payment projection (invoice authority remains Stripe)
  â†’ independent AXIGNAL entitlement policy/authority (unknown = no access)
  â†’ AuthorizedXeed read path only after identity, membership and entitlement checks
```

The browser return URL is display/navigation only. It is not a payment callback
and cannot set billing state. A signed event is an authenticated notification,
not a complete current-state snapshot. The event handler acknowledges durable
inbox acceptance; processing/reconciliation is idempotent and may be deferred.

The new subscriber path must not call `checkout_mapping_from_verified_event()`
or otherwise reuse metadata-derived capacity. Existing AO-10 remains its
separate Admin implementation until a separately reviewed remediation changes
it. Metadata may carry an opaque intent correlation reference only; it cannot
choose capacity, offer, payer, Principal, Tenant, Organization, payment, or
entitlement.

### Existing subscription: request a larger total capacity

The subscriber chooses a **desired total** of Organizations/Observation Focuses
for one already-authorized consumption scope. This is not a new subscription
and does not buy a second base unit:

```text
observed current capacity C  â†’ requested total D, where D > C
current additional quantity  â†’ desired additional quantity D - 1
billable change              â†’ provider-calculated increase from C to D only
```

Before mutation, re-check authenticated Principal, current membership, scope
ownership, current subscription binding, current full item snapshot, payment
state and lifecycle. Revoked membership or a cancelled/unpaid/unknown binding
blocks the update. The operation targets the already-bound Subscription ID;
it never creates another Checkout subscription or a second base item for that
scope. Any Portal path must be configured to the same allowlisted additional
Price and policy; if the portal cannot enforce those controls, it must not
expose subscription changes.

**Proposed deterministic proration policy:** apply the absolute desired
additional quantity (`D - 1`) with Stripe `proration_behavior=always_invoice`
and `payment_behavior=pending_if_incomplete`. This attempts the proration
invoice now and keeps the requested increase pending until the corresponding
invoice is paid and a provider-current complete subscription item snapshot
matches D. This charges only the difference for the remaining period according
to Stripe's calculation; the next regular renewal then bills the full desired
quantity. This selection is an architecture proposal for root review and must
be confirmed against the configured Stripe API version and desired failure/SCA
behavior before implementation. No entitlement or capacity increase occurs at
request, Session/Portal return, subscription update response, or
`invoice.created`.

An immutable `CapacityChangeIntent` records the current verified total C,
desired total D, subscription reference, complete evidence version, catalogue
version, membership/scope authorization reference and provider API revision.
Use one durable open intent per `(billing scope, subscription)` and only one
pending desired total. An exact repeated click returns/reuses the same pending
intent and mutation idempotency key; it does not make a second provider update
or invoice. A different target while an update is pending returns pending or
conflict until reconciliation determines the first outcome. Before an update,
compare-and-set the observed provider revision/current capacity; if it changed,
reconcile and recompute rather than applying a stale delta. On timeout, fetch
current subscription/invoice state before retry. Never express the request as
an additive `+delta` mutation; set absolute additional quantity to Dâˆ’1 so
retries cannot compound quantities.

`pending_purchase` is a local non-entitled state. If payment fails or the
subscriber abandons an action-required hosted payment, desired capacity stays
pending and effective capacity remains the last separately verified paid
capacity. If Stripe's update is pending/incomplete, canceled, or only partially
observed (for example provider quantity has changed but the matching invoice
is unpaid), do not expose the requested increase; reconcile subscription and
invoice until the result is known. If the requested total is already present
from a prior verified paid update, return idempotent success without a new
invoice. A request with D <= C is a no-op or a separately governed downgrade;
this feature does not infer downgrade semantics.

## Exact proposed file ownership

All source entries below are proposals, not authorization to implement them.
The architecture review approves or changes them before coding.

| File | Responsibility | Must not own |
|---|---|---|
| `domain/admin_billing/checkout_binding.py` | Existing Phase-A provider-neutral types and pure binding semantics; extend only if review identifies a missing provider-neutral fact. | Stripe SDK, auth, persistence, payment success, entitlement grants. |
| `application/admin_billing/checkout_binding.py` | Existing pure deterministic validator; remain the single item/terms/completeness/correlation validator. | Provider calls or state writes. |
| `application/admin_billing/subscriber_checkout.py` | Orchestrate server-authorized purchase intent, catalogue resolution, durable attempt, provider-neutral checkout port, and pending result. | Authentication establishment, payer cardinality, direct Stripe SDK, entitlement grant. |
| `application/admin_billing/subscriber_billing.py` | Apply binding and separately verified payment facts to a billing-state port with monotonic/idempotent transitions; emit an entitlement evaluation request, not an implicit grant. Own immutable `CapacityChangeIntent` application policy and `pending_purchase` state. | Organization truth, Xeed creation, or implicit conversion from metadata. |
| `pipeline/admin_billing/subscriber_store.py` | Durable subscriber intent/attempt, webhook inbox, billing projection, outbox/retry records and transaction/idempotency boundaries; isolated from Admin-only records. | Auth secrets, raw card data, canonical AXIGLAND writes. |
| `pipeline/admin_billing/stripe_subscriber.py` | Stripe-specific HTTP/SDK adapter: initial Checkout create, signed event verification, Session/Subscription/Invoice retrieval, exhaustive cursor pagination, absolute existing-subscription quantity update with reviewed idempotency/proration policy, normalized evidence. | Domain policy, identity resolution, direct entitlement writes, creating a second subscription for capacity expansion. |
| `pipeline/admin_billing/subscriber_reconciliation.py` | Provider-neutral reconciliation worker/use case that calls a read port, validates current facts, persists monotonic state, schedules bounded retry or DLQ. | Guessing an event order, metadata authority, implicit repairs. |
| `tools/runtime/stripe_billing.py` | Existing Admin webhook runtime; unchanged in this slice unless root separately approves the narrow runtime bridge. | Subscriber decisions via current metadata mapper. |
| `tools/runtime/subscriber_checkout.py` | Runtime composition/configuration seam for subscriber checkout and signed webhook dependency; no route ownership. | HTTP route registration/root-owned route policy, UI, auth provider. |
| `tests/admin_billing/test_subscriber_checkout.py` | Offline use-case scenarios, capacities 1/2/100, authorization/catalogue failures and idempotent attempt creation. | Live calls. |
| `tests/admin_billing/test_subscriber_webhook.py` | Offline signed-event/inbox/idempotency/current-state/replay/out-of-order behavior. | Pretending fixtures prove live provider behavior. |
| `tests/admin_billing/test_subscriber_reconciliation.py` | Offline missing-event, incomplete-page, retry, DLQ, re-fetch, conflict and revoke transitions. | Live calls. |
| `tests/admin_billing/test_stripe_subscriber_adapter.py` | HTTP transport/SDK stubs asserting request and pagination contracts, normalized full snapshots, mode/account checks. | Live network. |
| `specs/047-subscriber-billing-bridge/*` | Evolving feature contract, tasks, data model, architecture/review and verification evidence. | Override MASTER, Constitution or accepted ADRs. |

Do not add package `__init__.py` exports, schema/migrations, or edits to the
existing Stripe mapper/runtime/store until root reviews this boundary. If the
chosen durable store is SQLite, its ownership, transaction semantics and
migration lifecycle must be reviewed against existing repository persistence
conventions before implementation.

## Required sequence and invariants

1. **Authorize scope before billing.** The root-owned HTTP boundary must supply
   an authenticated AXIGNAL `Principal` and untrusted selected `Tenant`; an
   AXIGNAL membership check must succeed before a purchase intent is created.
   Spec 022 does not establish a production auth adapter, membership persistence,
   payer identity, or payer-to-Tenant cardinality. If the identity/scope adapter
   cannot return one unambiguous authorized consumption scope, return
   `UNKNOWN`/unavailable before any Stripe call. A Stripe Customer is never a
   Principal, Tenant, payer authority, Organization, or proof of membership.
2. **Resolve approved terms before provider contact.** An injected,
   environment-specific, versioned catalogue must identify exactly one
   configured monthly EUR base price and one configured monthly EUR additional
   price, match current provider facts, and be explicitly approved by the
   product/business owner. MASTER Â§27's EUR 9.95 base + EUR 4.95 per additional
   focus remains a pricing hypothesis, not validated willingness-to-pay.
   Missing, duplicate, inactive, wrong-mode, wrong-currency, wrong-interval or
   changed price facts yield `UNKNOWN` and no Checkout request. Never fall back
   to the first active Stripe Price or embed live Price IDs in domain code.
3. **Persist before create.** Create an immutable AXIGNAL purchase intent and
   attempt in durable storage before calling Stripe. Derive quantities only
   from the approved intent: one base item quantity `1`; additional item
   quantity `max(0, capacity - 1)`. Capacity must be positive and finite within
   a reviewed limit; Xignals are never billable. Use the attempt reference as
   Stripe request idempotency key. Persist returned Session/customer references
   transactionally with the attempt; ambiguous timeout triggers read/reconcile,
   not a second non-idempotent create or a capacity guess.
4. **Verify full binding by current provider reads.** The Stripe adapter checks
   account/mode/customer/Session/subscription identities against stored intent
   and attempt. It retrieves the Session's full paginated line-items endpoint
   and the Subscription's full paginated item list; embedded first-page items
   are never treated as complete. Every cursor page must be consumed with
   progress checks, duplicate item IDs rejected, `has_more == false` required,
   and partial/time-out/malformed results mapped to `UNKNOWN`. Normalize Price
   ID, active state, livemode, recurring interval/count, currency, integer
   amount and quantity; unsupported/decimal/unknown terms stay non-positive.
   Phase-A validator then compares exact expected items and all cross-object
   references. Provider metadata remains correlation-only.
5. **Keep states separate.** `CheckoutSessionState`, `BindingState`,
   `PaymentVerificationState`, `SubscriptionLifecycleState`,
   `IdentityScopeState` and `EntitlementState` are independent. Session
   creation/completion and a verified item binding do not mean payment. `invoice.paid`
   is the accepted payment-success signal under ADR-0061, after verifying its
   customer/subscription association and reconciling current subscription
   status/binding. No access on Checkout redirect, `checkout.session.completed`,
   `invoice.payment_succeeded` unless separately reconciled to the governing
   invoice policy, metadata, or stale/partial reads.
6. **Grant through an explicit authority only.** Entitlement remains UNKNOWN
   until identity/scope, paid billing state, valid current item binding,
   lifecycle/refund policy and a separately approved provider-neutral
   entitlement policy all agree. `EntitlementPort` or its reviewed equivalent
   is an explicit application boundary. Billing cannot create a Tenant/Xeed or
   authorize AXIGLAND reads. The existing `AuthorizedXeedReader` sequence
   (Principal â†’ membership â†’ Xeed â†’ Tenant match) remains an independent access
   gate. Unknown or conflict revokes/withholds paid access according to the
   approved policy; it never becomes an affirmative grant.
7. **Durable inbox and retries.** Verify Stripe signature/account/mode and
   timestamp before accepting an event. In one transaction, persist event ID,
   type, provider-created time, livemode/account, canonical payload fingerprint,
   correlation references and processing status before acknowledging. Store
   only required/redacted event facts, never secrets or payment credentials.
   Exact event-ID/fingerprint replay is a no-op; same event ID with changed
   fingerprint is a security/data conflict quarantined for reconciliation.
   Event timestamps alone are not a total order: for stale/equal/conflicting
   updates, retrieve provider-current objects and compare provider versions and
   lifecycle facts; unresolved order remains UNKNOWN. Retries are bounded with
   exponential backoff/jitter and classified transient/permanent. Exhaustion
   goes to DLQ with reason and redacted references; recovery re-fetches current
   state and reruns validators instead of replaying a stale grant command.
8. **Reconcile without trusting event completeness.** Reconcile by stored
   Stripe object references on event gaps, incomplete reads, conflicts, periodic
   sweeps and safe ambiguous create recovery. Fetch current Session,
   Subscription, invoice/payment and full items; validate before replacing
   projections. Persist `observed_at`, provider `created/updated`/version facts,
   evidence reference and catalogue version. Cancellation-at-period-end,
   immediate cancel, delinquency, full/partial refunds, disputes and grace
   periods require explicit service-access semantics from AO-09/AO-10 and
   governance; until selected, those transitions remain `UNKNOWN` and cannot
   expand capacity or access. Revoke/withhold idempotently once an approved
   policy determines ineligibility.

## Contracts and ownership interfaces

- Root-owned route accepts an authenticated request and delegates a selected
  Tenant only after membership validation; no auth files are in this worktree
  slice. Until the production identity adapter is available, a typed
  `SubscriberPurchaseAuthority` port is injected and tests use a deterministic
  fake. The port must not be implemented by trusting request IDs or Stripe
  metadata.
- `OfferCatalogueReader.resolve(environment, catalogue_version)` returns
  configured approved terms or `UNKNOWN`; read-only provider catalogue
  verification belongs in the Stripe adapter, while product approval is
  external governance.
- `CheckoutProvider.create_session(intent, idempotency_key)` returns provider
  references and an external redirect value; it does not mark payment or access.
- `SubscriptionChangeProvider.apply_desired_capacity(subscription_ref,
  desired_total, idempotency_key, proration_policy)` updates absolute quantity
  on the existing subscription. It must not create a subscription; result
  remains pending until invoice and complete item snapshot reconcile.
- `BillingProviderReader.read_checkout_binding(session_ref)` and
  `read_current_billing_state(customer_ref, subscription_ref, invoice_ref)`
  return normalized, complete, provider-current evidence or typed UNKNOWN.
- `WebhookInbox` is durable/idempotent and separate from auth/account state.
- `SubscriberBillingStore` applies compare-and-set/monotonic projection updates
  keyed by opaque intent and provider references; replay does not duplicate
  effects.
- `EntitlementPort.evaluate(...)` is only invoked after all required verified
  evidence is present. The chosen consumer scope and capacity mapping require
  spec-022/AO-09 decisions; no grant behavior is inferred here.

## Required offline acceptance fixtures

Tests use a fake provider and in-memory or isolated durable test store with zero
network calls. They must distinguish these independent planes:

- **capacity**: 1 (no addon), 2 (one addon), 100 (99 addons), and invalid/over-limit;
- **capacity expansion**: exact target Dâˆ’1 quantity on one existing
  subscription; duplicate clicks return one intent/invoice; payment failure
  never activates requested capacity; target already reached is a no-op; stale
  quantity forces reconciliation; membership revocation blocks update before
  provider contact;
- **payment**: created/completed session with payment pending, then paid/failed;
- **identity**: authenticated/member, unauthenticated, non-member, ambiguous payer
  scope, and cross-Tenant replay;
- **binding**: exact items, metadata-only, wrong customer/subscription/mode,
  wrong item/quantity/price/terms, missing pages, repeated cursor, duplicate item;
- **delivery**: exact webhook replay, same ID/different payload, missing event,
  delayed/out-of-order/equal provider timestamps, event before Session persistence;
- **recovery**: transient read/create timeout, permanent provider error, bounded
  retry, DLQ, reconciliation after current state changes;
- **lifecycle**: active, incomplete/unpaid, delinquent, period-end cancel,
  immediate cancel, refund/dispute; unresolved product semantics must stay
  UNKNOWN and never grant.

Assertions must prove that (a) metadata cannot set capacity, (b) completion is
not payment, (c) payment is not identity or entitlement, (d) verified binding
is not access, (e) every positive access decision has separate identity,
membership, current binding, payment, lifecycle and entitlement-policy evidence,
and (f) replay/reconciliation does not duplicate or revive an unauthorized
grant. Capacity 1/2/100 tests use fixture terms and do not assert the real
catalogue price.

## Live-only evidence ladder and limits

| Evidence | Allowed in this proposal | What it proves | What it does not prove |
|---|---|---|---|
| Offline fake fixtures | Yes | Deterministic policy and failure handling. | Stripe API compatibility, live payment, or production configuration. |
| Read-only live catalogue verification | Root-controlled and separately reviewed | Current account's configured live Price/product facts match an approved catalogue. | Willingness-to-pay, Checkout creation, payment, entitlement, or tax/legal compliance. |
| Live Checkout Session creation, not completed | Root-controlled after review of exact request/config | Request configuration, idempotency and returned Session can be reconciled/read back. | `invoice.paid`, payment failure/retry, refunds, cancellation/revocation, paid access, webhook delivery/recovery. |
| Live subscription capacity update | Root-controlled after review of exact request/config | One existing subscription receives the intended absolute quantity and proration settings. | Paid increased capacity until its invoice and complete current items reconcile; no evidence for cancellation/refund policy. |
| Completed live payment | Not authorized by this proposal | Would produce real payment lifecycle facts after separate explicit authorization. | Does not resolve subscriber identity cardinality, access policy, taxes or launch readiness on its own. |

All CI and deterministic tests remain offline and default-disabled for live
mode. Production requires explicit environment configuration and separate root
deployment controls. No secrets belong in specs, logs, fixtures, or test
artifacts.

## Root-resolved architecture decisions and remaining activation controls

1. The consumer capacity scope is the authorized Tenant. Root's identity/purchase
   owner store resolves Principal membership and ownership for each command;
   the purchasing Principal is linked to the initial Tenant through bootstrap.
   This does not define wider payer cardinality or roles.
2. Root controls the versioned live base/add-on catalogue and every live write.
   MASTER's â‚¬9.95/â‚¬4.95 remains a pricing hypothesis. Legal/tax copy and public
   contracting stay disabled until operator/address/contact details and
   responsible-party obligations are verified.
3. The subscriber billing store is a separate durable SQLite store. Root owns
   route/auth composition and supplies an entitlement snapshot reader; absence
   never defaults capacity or creates a grant.
4. Expansion uses `always_invoice` / `pending_if_incomplete`; provider API
   version and payment-method/collection eligibility are verified by the
   adapter. A hosted invoice link is returned only after current invoice
   retrieval and exact HTTPS Stripe host allowlist validation.
5. Overdue/unknown blocks increases; there is no affirmative grace. Period-end
   cancellation preserves previously paid-through capacity only to the
   provider-verified paid-through boundary. Full refund/dispute holds expansion
   until policy is explicit.
6. Root will record the human's LIVE-only direction in a new ADR that reconciles
   ADR-0061. No sandbox will be invented. A LIVE Checkout/update not completed
   and reconciled does not prove successful payment or production access.
7. Reconciliation cadence, alerts, operator repair authority and deployed
   webhook secret remain operational/deployment controls owned by root. The
   implementation supplies bounded retry/DLQ contracts and tests.

Root reports that the Stripe credentials are not available in this process and
will control provider configuration; this implementation performs no Stripe
calls or writes. Axignal SLU's tax/address/contact facts are not complete here,
so public contracting cannot be enabled by this slice.

## External technical references

- [Stripe Checkout Session line items API](https://docs.stripe.com/api/checkout/sessions/line_items): Session retrieval may contain only the first handful of line items; use the paginated line-items endpoint and consume all pages.
- [Stripe subscription items list API](https://docs.stripe.com/api/subscription_items/list): list items for the subscription with cursor pagination and `has_more`.
- [Stripe Checkout Sessions API](https://docs.stripe.com/api/checkout/sessions): Session lifecycle and subscription-mode fields.
- [Stripe update a subscription API](https://docs.stripe.com/api/subscriptions/update): absolute item-quantity updates, idempotency, proration and payment-behavior parameters must be bound to the account's pinned API version.
- [Stripe pending subscription updates](https://docs.stripe.com/billing/subscriptions/pending-updates): `items.quantity` is supported and an invoice-backed update applies after successful payment; [Invoice object](https://docs.stripe.com/api/invoices/object) defines nullable `hosted_invoice_url`.
- [ADR-0061](../../docs/adr/ADR-0061-stripe-billing-payment-authority.md) and [ADR-0066](../../docs/adr/ADR-0066-api-webhook-operations-boundary.md) govern payment and webhook operations; any live-only exception must be reconciled at those authorities before production activation.
