# AO-10 — Stripe Payments and Billing Integration

## User story

As AXIGNAL operations, I need Stripe-owned subscription/payment facts to deterministically control AXIGNAL service billing state and Xeed entitlement without making Stripe an authority over AXIGLAND or allowing browser success state to claim payment.

## Scope

- One direct AXIGNAL Stripe merchant account; no Connect.
- Explicit AXIGNAL Account ↔ Stripe Customer ↔ Stripe Subscription mapping.
- EUR 9.95/month includes one Xeed; EUR 4.95/month per additional Xeed; Xignals are not billable.
- Signed webhook verification, replay/idempotency, out-of-order protection and bounded request size.
- Checkout completion mapping without payment verification.
- Subscription quantity synchronization from the two approved recurring price references.
- Payment success/failure, effective cancellation and supported refund handling.
- Fail-closed Xeed entitlement/read unless billing is verified.
- Dormant-by-default runtime integration; secret material stays deployment-managed and process-local.

## Out of scope

- Stripe Connect or connected accounts.
- MRR/ARR/cohort/unit-economics methodology (AO-11).
- Legal invoice-document authority, accounting reconciliation, VAT/AEAT, VeriFactu/SIF (AO-20→AO-23).
- Live Stripe mutations or live production enablement before sandbox E2E.
- AXIGLAND writes or Organization identity mutation.

## Contracts

- STRIPE_STATE != AXIGLAND_TRUTH.
- STRIPE_CUSTOMER != AXIGNAL_ACCOUNT != AXIGLAND_ORGANIZATION.
- CHECKOUT_COMPLETED != PAYMENT_VERIFIED.
- XIGNAL_COUNT != BILLING_QUANTITY.
- UNKNOWN/EXTERNAL_PENDING != VERIFIED.
- Provider webhook authority is signature-derived, not an Admin-session impersonation.
- Event ID replay is idempotent and conflicting replay fails.
- Current payment/subscription state follows provider event time; late-arriving older events cannot roll back newer state.
- Runtime ingress is unavailable unless account ID, both price references and webhook signing secret are configured together.
- No secret value is stored in Git, SQLite, Admin bootstrap, error response or logs.

## Acceptance criteria

1. A verified Checkout event maps one AXIGNAL account to one Stripe customer/subscription but leaves payment pending.
2. invoice.paid changes billing verification to VERIFIED; browser/Checkout success alone does not.
3. invoice.payment_failed, effective cancellation and supported refund state fail closed for service access.
4. Xeed capacity is derived as one base item plus additional-Xeed quantity; Xignal count never participates.
5. Duplicate webhook delivery does not duplicate account effects.
6. An older webhook arriving later cannot overwrite a newer billing fact.
7. Missing/invalid signature is rejected before business mutation.
8. Provider ingress is disabled when Stripe runtime configuration is absent.
9. Focused, regression and deterministic repository gates pass.
10. Real Stripe sandbox E2E passes before any live enablement.

## Current external gate

The connected AXIGNAL Stripe context is live-only. AO-10 implementation must remain live-disabled until a Stripe sandbox/test context is made available and the real external E2E is executed.
