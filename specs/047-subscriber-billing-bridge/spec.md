# Feature Specification: Subscriber Billing Binding Validation

**Feature Branch**: `codex/production-closure`
**Created**: 2026-10-06
**Status**: Phase A offline contract implemented and verified; Phase B architecture approved by root; provider-neutral implementation in progress; LIVE execution remains root-controlled
**Input**: Production-readiness TASK-04/TASK-05, COMM-09, AO-10 and ADR-0061.

## User Scenarios & Testing

### User Story 0 â€” Start the first subscription through server-owned checkout (Priority: P1)

An authenticated subscriber with an authorized Tenant can start one initial monthly subscription for a desired total Organization-observation capacity. AXIGNAL resolves an explicitly approved environment-specific base/add-on catalogue, persists an immutable intent before contacting Stripe, and creates one Checkout Session. The browser return is informational. Missing authentication/scope authority, membership, or approved price facts returns unavailable/UNKNOWN before a provider write.

**Independent Test**: Inject identity/scope, catalogue, persistence and provider fakes. Verify invalid identity/scope/catalogue never contacts the provider; capacities 1, 2 and 100 create exactly one base quantity and `max(0, capacityâˆ’1)` add-on quantity; retries reuse a durable attempt/idempotency key; session completion does not mark payment or entitlement.

### User Story 0A â€” Increase total capacity on the existing subscription (Priority: P1)

An authorized subscriber can select a larger desired total capacity for the already-bound Tenant subscription. AXIGNAL updates the same Stripe Subscription to absolute add-on quantity `desired_totalâˆ’1`, never creates a second subscription or base quantity, and displays the expansion as `pending_purchase` until both payment and current complete item evidence verify the desired total.

**Independent Test**: From verified current capacities 1 and 2, request totals 2, 100, and repeated identical targets. Assert one existing subscription, exact absolute add-on quantity, `always_invoice` + `pending_if_incomplete`, one durable intent/invoice for duplicate clicks, no entitlement before paid invoice and complete matching snapshot, and no update after membership revocation.

### User Story 1 â€” Verify the purchased recurring capacity (Priority: P1)

AXIGNAL operations need to know whether a completed subscription Checkout is bound to the capacity in the server-authorized purchase intent. A signed Checkout event and its metadata alone do not establish that the expected recurring products and quantities were purchased.

**Why this priority**: COMM-09 records the current gap: `checkout_mapping_from_verified_event()` reads `axignal_xeed_capacity` from event metadata without verifying it against subscription items. A mismatch must not be treated as a verified billing binding.

**Independent Test**: Feed a provider-neutral validator offline fixtures for complete normalized subscription-item snapshots at capacities 1, 2 and 100, then vary item identities, quantities and completeness. Verify that only exact matches are `VERIFIED`; missing or incomplete evidence remains `UNKNOWN`; mismatches cannot increase capacity.

**Acceptance Scenarios**:

1. **Given** an immutable locally authorized intent and a complete provider-verified recurring-item snapshot that matches its approved offer and capacity, **When** binding validation runs, **Then** it returns a verified binding with the derived capacity and inspectable evidence references.
2. **Given** a complete snapshot whose items, quantities, currency, recurrence or offer reference do not match the intent, **When** binding validation runs, **Then** it returns a mismatch and no verified capacity binding.
3. **Given** only a signed Checkout completion event or metadata, with subscription items absent, truncated, unavailable or not known to be complete, **When** binding validation runs, **Then** the result remains `UNKNOWN`/pending and does not authorize positive entitlement.
4. **Given** metadata that conflicts with the locally authorized intent or provider item snapshot, **When** binding validation runs, **Then** metadata is treated as correlation input and cannot override either source.

### User Story 2 â€” Preserve payment, identity and entitlement boundaries (Priority: P1)

AXIGNAL operations need billing-binding validation to remain a necessary evidence check rather than a new authority for payment success, subscriber identity, Tenant/Xeed ownership or service access.

**Why this priority**: AO-10 and ADR-0061 assign payment facts to Stripe and service entitlement to AXIGNAL. The identity/payer relationship and auth provider remain unresolved in spec 022.

**Independent Test**: Validate a matching purchase snapshot while payment is pending and while the payer/scope authority is absent or ambiguous. Confirm validation can report binding facts but does not grant access or resolve an identity mapping.

**Acceptance Scenarios**:

1. **Given** a verified billing binding but no authoritative `invoice.paid` evidence, **When** the result is consumed by billing policy, **Then** payment stays pending and access is not granted.
2. **Given** a verified billing binding and payment facts but unresolved subscriber authority, Tenant/Xeed mapping or entitlement policy, **When** the result is consumed, **Then** those unknowns remain unknown and no new access is granted.
3. **Given** a valid recurring capacity, **When** it is derived, **Then** it is one base quantity plus `max(0, capacity - 1)` additional-Xeed quantity; Xignal count does not affect billing.

### User Story 3 â€” Process retries and changing provider facts safely (Priority: P2)

AXIGNAL operations need exact retries to remain idempotent and stale or conflicting provider evidence to trigger safe pending/reconciliation behavior rather than silently changing capacity.

**Why this priority**: AO-10 establishes event-ID idempotency and provider-time ordering; TASK-05 calls for provider-current reconciliation that is not yet implemented.

**Independent Test**: Replay identical normalized evidence and conflicting evidence under the same identity, then apply older and newer snapshots in either arrival order. Verify deterministic outcomes and that stale evidence never increases or rolls back validated capacity.

**Acceptance Scenarios**:

1. **Given** an exact retry of a previously processed provider event/evidence identity, **When** processed again, **Then** it produces no duplicate binding or entitlement effect.
2. **Given** conflicting payloads for the same provider event identity, **When** processed, **Then** validation fails closed and records a conflict for reconciliation.
3. **Given** an older provider event arriving after newer provider facts, **When** processed, **Then** it cannot roll current binding or payment state backward.
4. **Given** ambiguous ordering or a provider read that cannot establish a current, complete snapshot, **When** evaluated, **Then** the result becomes pending/`UNKNOWN` until reconciliation; no positive entitlement follows from uncertainty.

### Edge Cases

- Base item absent, duplicated or quantity other than one.
- Additional-Xeed item absent for capacity one, duplicated, non-recurring, or quantity inconsistent with capacity minus one.
- Unknown, retired or unapproved offer/price reference; unknown currency, amount, billing interval or interval count.
- Snapshot pagination says more items exist, any page is missing, or the provider response does not attest complete enumeration.
- Checkout session/customer/subscription references disagree with the immutable local intent or with one another.
- Metadata missing, malformed, forged, stale or contradictory. Metadata never supplies authority by itself.
- Provider read timeout, permission failure, missing configuration, unsupported event, or unavailable current-state version.
- Repeated delivery with identical event ID and payload versus same ID with conflicting payload.
- Out-of-order events or two different snapshots with indistinguishable ordering timestamps.
- Capacity boundary examples 1 â†’ 0 additional units, 2 â†’ 1, 100 â†’ 99; no Xignal quantity is introduced.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST represent an AXIGNAL-owned, immutable purchase intent reference before provider Checkout creation. It MUST NOT use provider metadata as the authority that creates the intent or chooses subscriber identity/scope.
- **FR-002**: The system MUST validate a completed recurring Checkout against the corresponding complete, provider-verified subscription-item snapshot and the immutable local intent before marking the billing binding verified.
- **FR-003**: The binding validator MUST consume provider-neutral normalized evidence. Provider-specific SDKs, event shapes and retrieval calls MUST remain behind the existing provider adapter boundary.
- **FR-004**: The validated recurring-item set MUST match the approved offer catalogue exactly: one base recurring item with quantity one, plus the approved additional-Xeed recurring item with quantity `max(0, capacity - 1)`. Unknown or extra billable items MUST fail closed. Xignals MUST NOT be billable.
- **FR-005**: Validation MUST establish full item enumeration, including all pages when the provider paginates. A partial/truncated/unknown snapshot MUST produce `UNKNOWN` or pending, never a verified binding.
- **FR-006**: Validation MUST check configured offer/price reference, quantity, recurrence, currency and amount against the immutable intent and the versioned approved offer catalogue. Missing or unapproved catalogue facts MUST remain `UNKNOWN`; prices documented as hypotheses MUST NOT be converted to validated willingness-to-pay.
- **FR-007**: Metadata MAY carry an opaque correlation reference, but MUST NOT independently establish or change payer, account, Tenant, Xeed capacity, product/price, payment or entitlement. Conflicting metadata MUST be surfaced as a mismatch.
- **FR-008**: Binding status, payment verification and service entitlement MUST remain separate states. A verified binding MUST NOT imply `invoice.paid`, authentication, membership, Tenant/Xeed authority or access.
- **FR-009**: The validator MUST preserve exact replay idempotency and reject conflicting reuse of an event/evidence identity. It MUST NOT duplicate binding records or grant effects.
- **FR-010**: Provider event ordering MUST follow accepted provider event/version facts rather than receipt order. Stale facts MUST NOT roll back a newer state; ambiguous order MUST request reconciliation and remain non-authoritative for positive access.
- **FR-011**: Results MUST retain enough provenance to explain the decision: opaque intent/evidence references, configured offer-catalogue version, provider/environment identity, provider object references, complete item facts, event identity/time, retrieval/currentness time, and validation outcome/reason. Secrets and payment credentials MUST NOT be stored in the domain result.
- **FR-012**: The design MUST define a provider-neutral reconciliation input boundary for obtaining a current complete snapshot. This feature does not itself authorize scheduled polling, credentials, retry/DLQ operations, alerts or repair authority; those operational tasks remain TASK-05 and require separate acceptance.
- **FR-013**: No UNKNOWN, pending, partial, mismatched or stale result may be coerced into a positive capacity binding or entitlement.
- **FR-014**: This feature MUST NOT decide subscriber authentication provider, payer-to-Principal/Tenant cardinality, tenant membership roles, checkout authorization UX, price willingness-to-pay, legal/tax treatment, or entitlement grant policy. These remain unresolved or owned by their governing specs/ADRs.
- **FR-015**: Required CI and deterministic tests MUST remain offline and LIVE provider calls MUST NOT default on. LIVE catalog reads/session/update activity is permitted only through root-owned controlled execution after a concrete request is reviewed. This feature itself never completes a live payment; non-completed LIVE activity does not prove payment, entitlement or production readiness.
- **FR-016**: Initial purchase MUST persist the intent and attempt before Checkout Session creation; capacity is selected server-side and metadata cannot establish it.
- **FR-017**: Capacity expansion MUST update the single existing subscription for the authorized Tenant to absolute add-on quantity `desired_totalâˆ’1`; it MUST NOT create a second subscription or sell a second base item.
- **FR-018**: Expansion uses `proration_behavior=always_invoice` and `payment_behavior=pending_if_incomplete`, bound to the pinned Stripe API version. `pending_purchase` remains non-entitled until the associated invoice is paid and full current subscription item evidence matches the desired total.
- **FR-019**: Duplicate command for the same pending target and observed provider revision MUST reuse one immutable capacity-change intent and idempotency key. A different target while one update is unresolved MUST remain pending/conflict; do not apply additive deltas or double invoice.
- **FR-020**: Present the hosted invoice/payment URL only when non-null HTTPS and its host matches a configured Stripe-host allowlist. Otherwise return pending without redirect; never pass through arbitrary provider/request URLs.
- **FR-021**: Subscription update is blocked before provider contact if Principal/Tenant authority or current membership is revoked, paid-through state is unknown/overdue, binding is unknown, or subscription lifecycle is ineligible.
- **FR-022**: Cancellation at period end retains only previously paid-through verified capacity until its provider-verified paid-through boundary. Overdue/unknown blocks increases; no grace-period entitlement is inferred. Full refund/dispute holds expansions pending explicit service policy and cannot expand capacity.

### Key Entities

- **PurchaseIntentReference**: AXIGNAL-owned immutable correlation to an authorized intended offer and desired total capacity. Subscriber purchasing authority is validated by a typed application port; consumption capacity is scoped to the authorized Tenant. Stripe Customer is not Principal, Tenant, payer, or Organization.
- **CapacityChangeIntent**: immutable desired-total change for the currently verified Tenant subscription, including previous verified capacity/provider revision, catalogue version, request-authority reference, proration policy and idempotency identity.
- **ApprovedOfferCatalogue**: Versioned allowlist of recurring offer references and their expected recurring terms. Current production price references/configuration are not assumed available; economic willingness-to-pay remains a hypothesis.
- **NormalizedSubscriptionItemSnapshot**: Provider-neutral complete enumeration of recurring item references and their offer, quantity and terms, bound to opaque provider objects and currentness evidence.
- **BindingValidationResult**: `VERIFIED`, `MISMATCH`, or `UNKNOWN` outcome with reason and provenance. Only `VERIFIED` establishes item-to-intent binding, not payment or access.
- **ReconciliationRequest**: Typed request for provider-current complete Session, Subscription, Invoice and item facts when events are absent, stale, conflicting or incomplete. It confers no authority to write AXIGLAND or grant access.
- **PendingPurchase**: Local lifecycle state for an initial checkout or desired capacity increase that has not passed binding, payment and entitlement policy. It never increases effective capacity.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Offline fixtures for capacities 1, 2 and 100 return verified capacity only when all expected recurring items and quantities match exactly.
- **SC-002**: Every missing, incomplete, unknown, unapproved or ambiguous item snapshot yields a non-positive (`UNKNOWN`/pending or mismatch) result; none produces a verified capacity.
- **SC-003**: Matching billing evidence while payment, identity/scope or entitlement authority is unresolved never grants service access.
- **SC-004**: Exact replay produces one stable result; conflicting replay and stale/out-of-order evidence cannot duplicate or roll back a binding.
- **SC-005**: All tests in the initial implementation slice run offline against deterministic provider-neutral fixtures, with zero network/provider calls.
- **SC-006**: For initial checkout and expansions, exact retries create at most one session/update/invoice per durable intent; capacities 1, 2 and 100 derive add-on quantities 0, 1 and 99.
- **SC-007**: Effective capacity never exceeds the last complete verified binding with paid-through authority; pending, unknown, failed or partial updates never grant the desired increase.

## Assumptions

- AO-10 and ADR-0061 remain governing for direct AXIGNAL merchant billing, recurring capacity formula, event authenticity/idempotency/order and payment verification.
- Existing Admin billing code is evidence for current behavior, not the subscriber checkout authority. Checkout creation and subscriber identity mapping are not present as established production capabilities.
- Human explicitly selected LIVE-only development; no sandbox is required or claimed. Stripe LIVE writes remain controlled by root. No completed payment is authorized by this feature.
- The present â‚¬9.95 base + â‚¬4.95 per additional Xeed is an offer hypothesis in MASTER Â§27, not proof of willingness-to-pay or permission to embed price facts as domain invariants.
- Provider-neutral offline behavior can be implemented using an injected purchase-authority port. Root's accepted bootstrap decision associates the purchasing Principal to an authorized Tenant; this does not create general payer-to-Tenant cardinality. Authentication runtime remains outside this feature.

## Governing References

- `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` Â§Â§27, 46.34, 54.
- `.specify/memory/constitution.md` principles IV, VIII, IX, X, XII.
- `docs/adr/ADR-0061-stripe-billing-payment-authority.md`, ADR-0066.
- `specs/031-p0-admin-stripe-billing/` (AO-10 contracts and current implementation).
- `specs/022-p0-identity-account-authority/` (identity and payer/scope questions remain unresolved).
- `docs/audits/production-readiness-2026-10-06/findings.md` COMM-09 and `execution-register.md` TASK-04/TASK-05.
- Current behavior: `pipeline/admin_billing/stripe.py::checkout_mapping_from_verified_event` reads capacity from Checkout metadata; `tests/contracts/test_ao10_stripe_billing.py` verifies metadata mapping and that Checkout is not payment proof.
- Stripe documentation: [Checkout Session line items](https://docs.stripe.com/api/checkout/sessions/line_items), [Subscription object](https://docs.stripe.com/api/subscriptions/object), and [Subscription item list](https://docs.stripe.com/api/subscription_items/list).
- Stripe pending updates: [pending subscription updates](https://docs.stripe.com/billing/subscriptions/pending-updates) confirms item quantity is supported; the [Invoice object](https://docs.stripe.com/api/invoices/object) defines nullable `hosted_invoice_url`.
