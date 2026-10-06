# Data Model: Subscriber Billing Binding

This model is intentionally provider-neutral. The domain contracts are in
`domain/admin_billing/checkout_binding.py`; the deterministic policy is in
`application/admin_billing/checkout_binding.py`.

## Entities

| Entity | Fields / invariants | Authority |
|---|---|---|
| `PurchaseIntent` | `intent_ref`, `attempt_ref`, approved catalogue reference/version, requested Xeed capacity, opaque environment reference, authorization time. Capacity is positive. | AXIGNAL-owned intent. No payer, Principal, Tenant or membership identity is represented here. |
| `ApprovedOfferCatalogue` | Catalogue reference/version; exactly one base recurring offer and one additional-Xeed recurring offer, each with opaque offer reference and recurring terms. The two references must differ. | Local configured approval input. The fixture catalogue is synthetic; this code does not approve real prices. |
| `RecurringTerms` | Normalized recurrence unit/count, 3-letter currency and unit amount in minor units. Unit is case-folded and currency upper-cased. | Normalized offer facts, not payment or willingness-to-pay evidence. |
| `CheckoutAttemptBinding` | Opaque binding, intent and attempt references; Checkout session, customer, subscription and environment references; establishment time. | Contract for a server-owned persisted association. This type does not authenticate its creator; a future adapter/application boundary must supply it from trusted server-owned state, never metadata alone. |
| `NormalizedRecurringItem` | Opaque item/offer refs; quantity, recurring flag and recurring terms. Unknown provider facts use `None`. Known item quantities must be positive. | Normalized provider facts; no SDK/object type enters domain. |
| `SubscriptionItemSnapshot` | Evidence and object references, environment, provider state reference/time, retrieval time, currentness, full-enumeration and pagination indicators, optional metadata intent correlation, immutable item tuple. | Provider adapter is expected to attest normalized completeness/currentness; Phase A consumes the attestation but performs no retrieval. |
| `BindingValidationResult` | Tri-state `VERIFIED` / `MISMATCH` / `UNKNOWN`, reason, intent/evidence references, canonical evidence fingerprint, provider state time; capacity/quantities only on VERIFIED. | Pure application result; never payment state, access grant, membership or AXIGLAND truth. |

## Relationships and cardinality

- One intent references one approved catalogue version and one authorized capacity. Its authorization time must not be later than the attempt-binding time or the provider state time.
- One attempt binding refers to one intent/attempt and one session/customer/subscription/environment tuple.
- One complete snapshot refers to one session/customer/subscription/environment tuple and contains the enumerated subscription items.
- The validator requires references in the binding and snapshot to agree. It does not determine payer-to-Principal/Tenant cardinality or associate any Organization.
- Exact replay uses `(evidence_ref, canonical content fingerprint)`. The validator always recomputes from the current normalized inputs; it never returns prior capacity as authority. Same reference and same content must produce the same complete result. If a prior VERIFIED result disagrees in any output field, the replay is a non-positive conflict. Same reference with changed content is a conflict. A prior result with an unrelated intent is a mismatch.
- Different evidence with an older provider state time is stale; equal state times with different evidence identities are ambiguous. Neither yields a positive capacity result. The time constraints are `authorized_at <= binding.established_at <= retrieved_at` and `authorized_at <= provider_state_at <= retrieved_at`; the provider state and local binding establishment may occur in either order.

## Capacity derivation

For intent capacity `C >= 1`, the complete recurring item set must contain exactly:

- one base offer at quantity `1`; and
- no additional-Xeed item when `C = 1`, otherwise one additional-Xeed offer at quantity `C - 1`.

Derived capacity is base quantity plus additional-Xeed quantity. Xignal quantities and arbitrary extra recurring items are not accepted. Amount, currency, interval and offer references must match the versioned catalogue input; there are no embedded production price IDs or price constants.

## Epistemic outcome

`UNKNOWN` is used when intent/catalogue/snapshot/binding is missing, catalogue version does not resolve, currentness or provider state is incomplete, full item enumeration is not established (`has_more` must be explicitly false), the item set is incomplete, or an item fact is unknown. `MISMATCH` is used for known contradictory references, unapproved items, wrong terms/quantities or conflicting reuse of an evidence reference. Only an exact complete match produces `VERIFIED` and non-null capacity fields. Booleans and floats are rejected wherever integer-valued quantities, amounts or intervals are required.

This distinction only describes billing-item binding. It does not upgrade invoice/payment verification or grant subscriber access.

## Phase B subscriber billing persistence and capacity changes

The root-approved subscriber path adds a separate SQLite storage boundary in
`pipeline/admin_billing/subscriber_store.py`; it does not reuse AO-10 Admin
account records or infer subscriber identity from those records.

| Record | Key and required facts | Invariant |
|---|---|---|
| `SubscriberPurchaseIntent` | Opaque intent/attempt ref, authorized Principal/Tenant evidence refs, initial desired total, catalogue ref/version, environment, creation/authorization times, immutable request fingerprint. | Tenant is consumption scope. Authenticated Principal/membership authority comes from the root route. Stripe references are absent until provider response. |
| `CheckoutAttempt` | Intent ref, unique provider idempotency key, state, Checkout Session/customer/subscription refs, provider environment/API version, safe checkout URL ref. | Persist before create; one initial subscription for one authorized Tenant billing scope; browser return does not change payment/access. |
| `CapacityChangeIntent` | Unique intent, Tenant scope, existing subscription ref, previous verified total and state revision, desired total D, target addon quantity Dâˆ’1, catalogue version, proration/payment behavior, idempotency key, state. | One unresolved change per `(Tenant scope, subscription)`. Duplicate request reuses its intent. A second subscription/base item is impossible through this command. |
| `SubscriberBillingProjection` | Tenant billing scope, Stripe Customer/Subscription refs, current verified binding evidence, paid invoice/payment evidence, lifecycle status, effective paid capacity, paid-through bound, provider/API version and currentness. | Effective capacity never equals an unverified requested target. Unknown/overdue state blocks increase. |
| `WebhookInboxEntry` | Provider event ref/type/created time/account/environment, canonical fingerprint, received time, bounded process attempts, disposition, safe reference set. | Signature/account/mode verification precedes idempotency lookup. No raw event body, authorization header, signature, secret or payment credentials are stored. |
| `RetryOrDeadLetterEntry` | Operation/evidence ref, bounded attempt count, next-attempt time, transient/permanent category, DLQ disposition and audited recovery ref. | Recovery always re-fetches provider-current state and reruns validators; it never replays a stale entitlement command. |

### Capacity expansion transitions

For current effective capacity C and requested total D>C, the target is an
absolute additional item quantity Dâˆ’1. The provider update uses the existing
additional subscription-item ID and existing Subscription ID. `Dâˆ’C` is never
sent as an additive quantity. `always_invoice` creates/attempts the immediate
proration invoice; `pending_if_incomplete` keeps the provider update pending
until successful payment. Local `pending_purchase` is non-entitled. Effective
capacity changes only after invoice association/payment and complete current
item binding validate the target. Duplicate clicks reuse the same durable
target intent/idempotency key. New target requests are blocked while the
current provider revision or existing pending update is unresolved.

Stripe documentation confirms that pending updates support `items.quantity`,
and Stripe's hosted invoice URL is nullable. Adapter must pin the live account's
API version and treat unsupported collection/payment behavior, an expired
pending update, a missing hosted URL, or an invalid URL host as pending/UNKNOWN.

### State separation

`purchase_state`, `binding_state`, `payment_state`, `subscription_lifecycle`,
`identity_scope_state`, and `entitlement_state` are persisted as independent
dimensions. `effective_capacity` is a projection backed by the most recent
complete binding plus separately verified paid-through facts. It is not copied
from event metadata, customer-provided input, pending desired total, Checkout
completion or a partial current snapshot. Entitlement remains UNKNOWN until the
root-approved policy/port evaluates all required current authorities.
