# ADR-0061: Stripe billing facts are external payment authority; AXIGNAL owns service entitlement

## Status

Accepted for AO-10 implementation. Live enablement remains gated by sandbox E2E and production deployment controls.

## Context

AXIGNAL needs recurring billing for the self-service offer while preserving the product boundary established by the MASTER and ADR-0055. The commercial model is EUR 9.95/month including one Xeed plus EUR 4.95/month for each additional Xeed. Xignals are outputs of observation and are never billable quantities. AO-09 owns AXIGNAL account, subscription and Xeed entitlement state; AO-18 owns integration/credential governance. Stripe owns payment, invoice and Stripe-subscription facts, but must not become authority over AXIGLAND, Organization identity or economic truth.

The confirmed Stripe merchant is AXIGNAL's own direct Stripe account. This integration does not use Stripe Connect or connected merchant accounts.

## Decision

- AXIGNAL uses one direct Stripe merchant account. Customer-specific Stripe Customer and Subscription objects map to AXIGNAL service accounts; there is no Stripe account per AXIGNAL customer.
- Billing mapping is explicit: AXIGNAL Account != Stripe Customer != Stripe Subscription != AXIGLAND Organization.
- The self-service subscription has exactly one base recurring quantity plus an additional-Xeed recurring quantity derived as max(0, xeed_capacity - 1). Xignal count cannot affect billing quantity.
- checkout.session.completed may establish the verified provider mapping and link the pending AXIGNAL service subscription, but it cannot verify payment or grant Xeed service access.
- invoice.paid is the authoritative payment-success event for AO-10. invoice.payment_failed, effective cancellation/unpaid subscription states and supported refund events fail closed for service access.
- Xeed entitlement and Xeed reads require AXIGNAL account/subscription state plus PaymentVerificationState.VERIFIED. Stripe never writes AXIGLAND.
- Stripe webhook authenticity is verified server-side with the endpoint signing secret, timestamp tolerance and constant-time signature comparison. Secret material is process-local, excluded from repr, and never persisted or projected.
- Provider events are append-only and replay-safe. The Stripe event ID is the idempotency identity; exact replay is accepted without duplicating AXIGNAL account effects.
- Current billing state is ordered by Stripe provider event time, not arrival time. A late-arriving older event cannot roll back a newer fact.
- Provider-authenticated webhook writes use a dedicated BillingAuthorityGrant; they do not impersonate an Admin human session.
- The webhook route is absent unless the complete Stripe runtime configuration is present. Public AXIGNAL writes remain closed.
- MRR/ARR and recurring-revenue methodology are AO-11 concerns. Invoice/legal-document ownership, accounting, Tax/VAT/AEAT and VeriFactu/SIF remain AO-20→AO-23 concerns.
- No live Stripe write or live webhook enablement is authorized by AO-10 implementation alone. A real Stripe sandbox E2E must pass before live enablement.

## Alternatives considered

- Stripe Connect: rejected because AXIGNAL is the merchant and does not operate a marketplace of connected merchants.
- Treat Checkout success/redirect as payment authority: rejected because browser return state is not authoritative payment evidence.
- Store Stripe secret keys or webhook secrets in SQLite/Admin: rejected; AO-18 requires deployment-managed secret material.
- Bill per Xignal: rejected because Xignals are observation outputs, not commercial units.
- Let Stripe own AXIGNAL account/Organization identity: rejected because provider billing identity is not service identity or AXIGLAND truth.
- Compute MRR directly from the last paid invoice in AO-10: rejected because recurring-revenue methodology belongs to AO-11 and invoice amount can include proration/tax/non-MRR components.

## Consequences

- A subscription can be linked and active while payment remains EXTERNAL_PENDING; no Xeed service is granted until verified billing evidence arrives.
- Failed/refunded payment makes service access fail closed without deleting historical entitlement records.
- Webhook delivery order and replay do not corrupt current payment state.
- Production can ship the dormant implementation safely with Stripe ingress disabled until deployment-managed configuration and sandbox evidence are available.
