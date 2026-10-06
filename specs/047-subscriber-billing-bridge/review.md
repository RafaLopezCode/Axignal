# Architecture Review Record â€” 047

## Phase A disposition

Root approved and reviewed the provider-neutral offline binding validator before
implementation. It passes focused tests and is not connected to Checkout,
webhooks, payment or entitlement. COMM-09 remains open until Phase B removes the
subscriber metadata-only authority path.

## Phase B architecture disposition

**Status:** APPROVED by root on 2026-10-06 before Phase B implementation.
**Approved scope:** Exact file ownership in [phase-b-architecture.md](phase-b-architecture.md), separate subscriber SQLite store, signed bounded inbox, complete current provider reads, reconciliation/retry/DLQ, one subscription per authorized Tenant capacity scope, and no capacity from metadata.
**Capacity increase:** Use same Subscription; set absolute add-on quantity `desired_totalâˆ’1`; no second base/subscription. Approved proration/payment parameters are `always_invoice` and `pending_if_incomplete`. `pending_purchase` remains non-entitled until associated invoice is paid and full current item evidence matches. Duplicate clicks reuse one durable intent/idempotency key.
**Identity:** Tenant is consumption scope. Root's bootstrap links the purchasing Principal to authorized Tenant through an explicit purchase-authority port. No auth runtime, general roles or payer cardinality is introduced.
**Lifecycle:** No default entitlement on signup. Unknown/overdue blocks increases and no affirmative grace is inferred. Period-end cancellation retains only verified paid-through capacity. Full refund/dispute does not expand until policy is explicit.
**LIVE:** Explicit human direction is LIVE-only. Root will document this exception in a new ADR against ADR-0061. No sandbox is claimed; this feature does not complete a payment. Root controls all live writes.

## Constraints for implementation and root integration

- Root owns route registration/auth and any Stripe writes. The implementation
  must provide the exact runtime interface from
  [subscriber-checkout.v1.md](contracts/subscriber-checkout.v1.md).
- No auth files, frontend/dashboard, economic pipeline, existing AO-10 mapper,
  global gates, environment credentials, live payment completion, commit, or
  deployment changes in this slice.
- Stripe metadata remains correlation only. The existing metadata mapper is not
  invoked by the subscriber checkout/webhook path.
- Catalogue values are root-approved configuration, never hardcoded into the
  provider-neutral domain. â‚¬9.95/â‚¬4.95 are still a willingness-to-pay
  hypothesis, not validated market evidence.
- `invoice.paid` association, complete binding, current lifecycle, authorized
  Principal/Tenant membership and explicit entitlement policy are all required
  as independent gates. Unknown is non-authorizing.

## Remaining root-only activation controls

- Reconcile ADR-0061's sandbox language in root-owned ADR before production
  activation; do not fabricate sandbox evidence.
- Root verifies active live catalogue and reviews each concrete LIVE write.
- Production auth/membership runtime and configured signed webhook secret remain
  root deployment responsibilities; no Stripe credentials are persisted.
- A LIVE Checkout/session or subscription quantity update that is not paid does
  not prove invoice payment or paid access. Completed real payment requires its
  own explicit authorization.
