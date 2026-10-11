# ADR-0094: Billing currentness follows AXIGNAL's verification, not the provider's last change

**Status:** Proposed (needs CTO acceptance before integration).
**Date:** 2026-10-11
**Authority:** MASTER (authorized billing; UNKNOWN ≠ FALSE), Constitution, spec 047 (subscriber billing bridge), ADR-0092 (staff capacity), ADR-0093 (price book).

## Context

Before this change, `_ProjectionEntitlements` marked a billing projection `STALE` when `now - provider_state_at > 5 minutes`. With Stripe, `provider_state_at` is `max(subscription.updated, latest payment)`, the last time the subscription **changed**, which seldom happens. As a result, a paid, current, unchanged subscription lost confirmed capacity five minutes after payment. `refresh_purchase` could not recover it, because re-reading an unchanged subscription returns the same `provider_state_at`:

- the store either ignored the write as identical, so the projection stayed STALE;
- or it rejected the write ("equal provider state time cannot raise billing capacity"), which led to the projection being marked UNKNOWN.

Reproduced deterministically with the paid-journey composition: 10 minutes after paying, capacity was None and STALE, `refresh_purchase` returned UNKNOWN, and `add` returned CAPACITY_UNKNOWN.

## Decision

1. **Two distinct times.**
   - `provider_state_at`: when the subscription last changed at the provider. It keeps governing ordering, staleness of evidence and anti-replay, unchanged.
   - `verified_at` (new, on `BillingProjection`): when AXIGNAL last retrieved and fully re-validated that state.
2. **Operational freshness is governed by `verified_at`.** The window stays at 5 minutes; no TTL was extended. Projections written before this field existed fall back to `provider_state_at`, the previous and stricter rule.
3. **`verified_at` is only set by a full re-validation.** That means items bound to the approved catalogue, payment VERIFIED, eligible lifecycle and `paid_through > now`. It is set only when capacity results; otherwise it is None.
   - A retrieval that precedes its state, lies in the future or is not timezone-aware yields no verification.
   - The constructor rejects a `verified_at` earlier than `provider_state_at`.
4. **Re-verification of the same state.** The store accepts a write with an equal `provider_state_at` only when every projected fact is identical and only `verified_at` is newer.
   - An older or equal verification is ignored: no regression.
   - Any other difference (capacity, payment, paid-through, invoice, binding) keeps the existing equal-state-time rules and conflicts.
   - Contradictory or ambiguous evidence never refreshes.
5. **Automatic re-verification when capacity is needed.** This applies to a portfolio read and to `add`, `retry_pending`, `resume`, `replace` and `expand`.
   - If the subscription is STALE, the composition asks the checkout service to `reverify_current_projection`. This is a read-only provider read that buys, changes and grants nothing.
   - It runs at most once per Tenant per 60 seconds. A provider failure leaves capacity unconfirmed.
   - Recovery always comes from new provider evidence, never from time.

## Consequences

- An unchanged, paid subscription stays usable for its whole paid period, confirmed by a provider read at most every 5 minutes of use.
- An expired period, a failed or cancelled payment, or a contradictory read never becomes capacity.
- Provider reads are bounded: one per Tenant per minute, only while STALE.

## Acceptance

Covered by `tests/integration/test_subscriber_billing_currentness.py`:

- re-verification at 5 minutes, 10 minutes and 24 hours, with `provider_state_at` unchanged and `verified_at` advancing;
- `refresh_purchase` recovering a stale projection by consulting the provider;
- an expired paid period that is never refreshed;
- a contradictory same-state read that does not refresh;
- bounded re-verification, including a provider failure;
- an older verification that never replaces a newer one, and a capacity change at equal state time that conflicts;
- a legacy projection without `verified_at`;
- invalid retrieval times.

This change does not enable contracting, does not alter prices, and is not production E2E.
