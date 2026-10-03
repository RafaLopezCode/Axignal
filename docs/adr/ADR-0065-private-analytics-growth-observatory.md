# ADR-0065 — Private Analytics and Growth Observatory Boundary

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-14, AO-17

## Decision

AXIGNAL may maintain a private, first-party analytics and commercial-growth projection for operating its own acquisition funnel. This projection is operational evidence, not AXIGLAND truth and not evidence admission.

Analytics definitions are versioned. Events carry only bounded operational references such as opaque session, request, issue, account, Xeed, evidence or advisory identifiers. Subscriber content, professional email and free-text request purpose are excluded.

Traffic/engagement is explicitly classified as HUMAN, BOT, AMBIGUOUS, INTERNAL or UNKNOWN. Unknown or ambiguous opens are never upgraded to human readership.

Free-to-paid conversion requires an explicit request-to-account link plus an observed provider-owned paid billing event. Additional-Xeed attach derives from observed billing capacity. Sequence and attribution are descriptive correlation only and do not establish causality.

Delivery cost and paid revenue remain private commercial facts. Gross contribution is derived per currency; currencies are not combined without an explicit conversion authority.

## Consequences

- AO-12 remains authority for first-party public marketing touches.
- AO-15 remains authority for brief request/consent lifecycle.
- AO-16 remains authority for weekly-brief issue, delivery and correction history.
- AO-10/Stripe remains authority for payment and subscription facts.
- AO-14/AO-17 may project those facts together but may not mutate them or write AXIGLAND.
- Replay is idempotent and conflicting event identity fails closed.
