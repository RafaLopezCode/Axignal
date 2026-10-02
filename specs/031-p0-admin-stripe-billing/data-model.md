# AO-10 data model

- BillingMapping: AXIGNAL account, provider, Stripe customer/subscription IDs, base/additional-Xeed price references and provider-event creation time.
- BillingEvent: immutable Stripe-normalized billing fact with provider event ID/time, account, event kind, payment/subscription state, optional amount/currency and Xeed capacity.
- BillingSnapshot: deterministic current provider billing projection ordered by Stripe event time.
- BillingAuthorityGrant: provider-authenticated capability proving which verified Stripe event is allowed to cause an AXIGNAL service-state effect.
- BillingQuantities: exactly one base quantity and max(0, xeed_capacity - 1) additional-Xeed quantity.
- AO-09 AccountSnapshot.payment_verification: EXTERNAL_PENDING | VERIFIED | FAILED; service entitlement requires VERIFIED.

No Stripe credential or webhook secret has a persistence/domain-record type.
