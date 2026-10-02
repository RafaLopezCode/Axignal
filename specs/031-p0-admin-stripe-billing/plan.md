# AO-10 implementation plan

## Constitution check

- AO-09 remains authority for AXIGNAL service account/subscription/entitlement state.
- AO-18 remains authority for integration and secret-reference governance.
- Stripe supplies payment/subscription facts only; no provider event can write AXIGLAND.
- Pricing follows the current MASTER contract and never bills Xignals.
- UNKNOWN and EXTERNAL_PENDING remain distinct from VERIFIED.

## Architecture

Add provider-neutral billing types under domain/admin_billing, application orchestration under application/admin_billing, replay-safe SQLite persistence and a narrow Stripe boundary under pipeline/admin_billing. Compose a gated webhook runtime in tools/runtime. Provider-authenticated effects use a billing authority grant rather than a fabricated Admin identity.

The Stripe endpoint is absent unless all required runtime configuration is present. No outbound live API mutation is part of this slice.

## Temporal/idempotency model

Stripe event ID is immutable replay identity. provider_created_at orders current billing facts; receipt time is operational metadata only. Exact re-delivery is idempotent even when received at a different time. Checkout mapping uses Stripe event time so retry does not change immutable mapping content.

## Failure handling

Invalid signatures and malformed contracts fail closed. Unmapped dependencies return a retryable provider-ingress failure. Failed/refunded billing denies Xeed service but preserves historical account/entitlement records. Quantity reductions below active entitlement remain a contract conflict rather than silently choosing which Xeed to revoke.

## Validation

Focused AO-10 contracts, AO-09/AO-18 regression, full deterministic repo validation, secret scanning/CI and a real Stripe sandbox E2E before live enablement.
