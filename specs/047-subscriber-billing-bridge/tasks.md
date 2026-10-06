# Tasks: Subscriber Checkout, Billing Binding and Capacity Expansion

**Feature**: [spec.md](spec.md)
**Architecture**: [phase-b-architecture.md](phase-b-architecture.md) â€” root approved 2026-10-06
**Execution boundary**: LIVE account is authorized; root owns provider writes. This slice uses offline fixtures only and makes no payment completion or production deploy.

## Phase A â€” Pure binding validation (completed)

- [x] T001 Define provider-neutral recurring catalogue, intent, binding, snapshot and result contracts.
- [x] T002 Implement deterministic exact item/term/completeness/currentness validation with tri-state output.
- [x] T003 Add positive capacities 1/2/100 and discriminating malformed, stale, mismatch, replay-corruption fixtures.
- [x] T004 Record Phase-A data model and versioned contract.
- [x] T005 Run focused pytest, Ruff, mypy and Spec Kit prerequisite checks.
- [x] T006 Root ran 1,404-test seven-gate baseline on shared candidate.

## Phase B â€” Provider-neutral subscriber orchestration

- [x] T007 Add immutable subscriber purchase and capacity-change commands/results; make desired total and `pending_purchase` explicit, preserving Phase-A validator contract.
- [x] T008 Re-read Principal, membership and durable initial purchase-owner receipt before mutation; identity/auth implementation stays owned by 049/root.
- [x] T009 Consume injected approved environment/versioned catalogue and derive exact initial/expansion quantity; absent/mismatched catalogue blocks Stripe.
- [x] T010 Implement initial Checkout: persist intent before provider call, one base + max(0,totalâˆ’1) add-ons, idempotent recovery, URL returned for allowlist validation.
- [x] T011 Implement same-subscription absolute addon quantity Dâˆ’1 and `always_invoice`/`pending_if_incomplete`; persist one pending change and re-read current binding before mutation. Out-of-band Dashboard edits can still race between read and update; Stripe has no compare-and-set in this adapter, so that external race remains a limitation.
- [x] T012 Define route integration API and typed auth handoff without editing root-owned HTTP routes.

## Phase C â€” Durable subscriber billing store

- [x] T013 Add separate SQLite subscriber tables for attempts, current billing projection, event inbox metadata, retries/DLQ and purchase-owner receipt. No Admin store changes or raw webhook payload/secrets/card data.
- [ ] T014 Store persists attempts/projections/webhook fingerprints/owner receipts and fails on conflicting scope or replay; retry receipts survive reopen. Store-specific duplicate-request, conflicting webhook fingerprint, and monotonic revision conflict tests remain incomplete.
- [x] T015 Persist effective capacity separately from requested/pending desired total. Unknown/overdue/failure never raises effective capacity.

## Phase D â€” Stripe adapter and provider-current reads

- [x] T016 Add injectable Stripe transport/adapter with explicit API version and live/test environment; mutation enablement defaults false.
- [x] T017 Implement server-created subscription Checkout Session with approved catalogue line items, idempotency key and explicit `automatic_tax`; metadata is correlation only. Checkout stays blocked until the approved tax reader contains confirmed current active-registration evidence.
- [x] T018 Implement complete paginated Checkout Session line-item and Subscription-item reads with cursor progress/duplicate checks and account/mode/customer/subscription cross-checks; validate Checkout/Subscription/Invoice automatic-tax state and associated paid invoice, PaymentIntent and Charge.
- [x] T019 Implement absolute existing-subscription add-on quantity update with `always_invoice`/`pending_if_incomplete`, configured add-on Price and operation idempotency key.
- [x] T020 Validate invoice/Checkout redirect HTTPS hosts in runtime; invalid or absent URLs remain null while purchase stays pending.
- [x] T021 Stripe's official [Subscription](https://docs.stripe.com/api/subscriptions/update?api-version=2025-04-30.basil) and [Subscription Item](https://docs.stripe.com/api/subscription_items/update) update references document quantity updates with `pending_if_incomplete` and `always_invoice`; the pinned local API version is 2025-06-30.basil. Offline fixtures assert the outgoing absolute Dâˆ’1 quantity and idempotency key. No live update/payment was attempted; unsupported shapes remain fail-closed.

## Phase E â€” Signed webhook and reconciliation

- [x] T022 Verify Stripe signature, timestamp tolerance, configured direct-account scope and livemode before durable inbox replay/dedupe; do not use AO-10 metadata mapper.
- [x] T023 Store bounded event refs/fingerprint only; exact replay is a no-op and conflicting replay is quarantined.
- [x] T024 Route events to provider-current reconciliation; payload item/payment state and arrival order are non-authoritative.
- [x] T025 Implement bounded retries and DLQ with capped deterministic exponential delay. Jitter and operator-facing inbox repair workflow are not included in this slice.
- [x] T026 Partial provider pages and non-current/future/stale facts remain non-positive; projection rejects stale provider revisions.

## Phase F â€” Billing/entitlement separation and verification

- [x] T027 Verify associated current paid invoice plus bound customer/subscription/intent and current item snapshot; Checkout completion alone never equals payment.
- [x] T028 Keep identity, membership, binding, payment, lifecycle and entitlement independent; billing projection does not write an entitlement or grant on signup.
- [x] T029 Enforce current paid/lifecycle gates; verified paid-through capacity survives cancel-at-period-end only until expiry. Overdue, expired and UNKNOWN remain non-positive; current refund/dispute evidence returns UNKNOWN and cannot authorize an increase.
- [ ] T030 Offline subscriber billing E2E covers initial 1/2/100, expansion 1â†’2/100 on one subscription, duplicate clicks, pending payment, prepared retry with stable idempotency, transient UNKNOWN recovery, paid-through cancellation expiry and no positive grant for unknown/refunded/disputed facts. Full identity/auth/HTTP/entitlement/customer journey is root-owned and not covered by this feature-only suite.
- [ ] T031 Focused billing Ruff and pytest pass (68 cases at the last run); compile, mypy, architecture guard, governance, full suite and root cross-review remain root-owned/pending.
- [x] T032 Compare provisioned LIVE Prices with the approved catalogue: base `price_1UNYXv8feyjV8PemcFisvBJ2` EUR 9.95/month and add-on `price_1UNYY88feyjV8PemyuI3unra` EUR 4.95/month, both active, per-unit, recurring monthly, `tax_behavior=exclusive` (readback recorded by root in `docs/audits/production-readiness-2026-10-06/APPROVED_LIVE_CATALOGUE.md`).
- [ ] T033 Keep live Checkout disabled until a current approved tax configuration has at least one explicitly confirmed active registration. Root's read-only live lookup found Tax Settings `active`, active registration list empty; neither the Stripe tax setting nor exclusive price behavior alone proves tax collection readiness or a legal registration.

## Explicitly out of scope

- Any edits to root-owned identity/auth routes, front-end/dashboard, economic pipeline, global gates, deployment, environment secrets or live-payment completion.
- No Stripe writes from this agent. Root owns LIVE write actions and external account access.
- Any assertion that fixture-based end-to-end coverage proves Stripe sandbox or real payment outcomes.
