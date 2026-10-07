# ADR-0085: Private design-partner pilot entitlement before public contracting

- **Status:** Accepted
- **Date:** 2026-10-07
- **Authority:** MASTER PRODUCT MODEL; Constitution; ADR-0084 except where explicitly narrowed here; direct human product decision.
- **Scope:** private subscriber access for pre-commercial design-partner validation.

## Context

AXIGNAL needs real buyer-persona usage before public commercial launch to validate product value, Human First UX, autonomous observation and real unit economics per observed Organization. Two to three known design partners are willing to use the real product at EUR 0 specifically to help iterate it.

ADR-0084 requires paid capacity for new private observation. That rule remains correct for public commercial contracting, but would force Stripe/fiscal activation merely to run a controlled pre-commercial validation. The human has explicitly authorized a narrower pilot authority instead.

## Decision

1. AXIGNAL MAY grant a private design partner exactly **one Organization/Xeed of observation capacity** without a Stripe payment while public contracting remains disabled.
2. Pilot capacity is a distinct service-entitlement authority. It MUST NOT create, emulate, backfill or imply Checkout, invoice, subscription, payment, tax-registration or paid-entitlement facts.
3. Billing remains the only commercial payment authority. A current verified paid entitlement takes precedence when present; the pilot grant is only a pre-commercial service-access source.
4. Pilot admission is invite-only. An operator issues a high-entropy, single-use, expiring invitation secret out of band. AXIGNAL stores only its digest. Redemption requires an already authenticated first-party subscriber session and atomically binds the resulting grant to that exact principal_id + tenant_id.
5. Email is a delivery/possession channel for the invitation, not an identity key, account-linking key or authorization fact. OIDC issuer/subject identity and current Principal-Tenant membership remain authoritative.
6. A pilot grant has capacity exactly 1, is durable, expiring and revocable, and grants the **same subscriber product path** as the base commercial Xeed. There is no pilot-only Brain, AXIGLAND, Signal, Evidence, AXENT or observation implementation.
7. Exhausting pilot capacity MUST NOT silently expand it. Additional capacity remains unavailable while commercial contracting is disabled.
8. Pilot expiry/revocation stops authority for new capacity-dependent operation but MUST NOT erase canonical AXIGLAND knowledge, admitted evidence or historical observations.
9. AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED=false and Stripe live mutations remain false during this pilot. Public launch remains a separate operator gate.
10. Pilot data MUST be instrumentable for unit economics so AXIGNAL can measure actual observation/model/storage/AXENT cost per Xeed before confirming pricing.

## Consequences

ADR-0084 decision 4 is narrowed only for explicitly granted private design partners. It remains unchanged for ordinary subscribers and public contracting. No fiscal conclusion follows from this technical pilot mechanism; legal/tax status remains an external operator responsibility.

The pilot is considered technically proven only after invite issuance, authenticated redemption, one-Xeed creation, restart continuity, tenant isolation, real observation/output and revocation/expiry behavior have evidence. It is not evidence that paid Billing is production-verified.
