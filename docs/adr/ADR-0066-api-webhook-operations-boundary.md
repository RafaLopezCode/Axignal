# ADR-0066 — API/Webhook Operations Boundary

**Status:** ACCEPTED  
**Date:** 2026-10-03  
**Scope:** AO-19

## Decision

AXIGNAL maintains a private API/Webhook Operations projection over predefined governed endpoints and webhook ingress. This surface exists for diagnosis and bounded operational recovery; it is not an unrestricted HTTP client and it has no AXIGLAND write authority.

API inventory entries declare method, path template, exposure, direction, schema/version and authority boundary. Runtime observations may record status, latency, error category, quota and rate-limit state. Missing telemetry remains UNKNOWN.

Webhook inbox records contain only bounded operational metadata: integration/provider event identity, event type, timestamps, payload fingerprint, payload size, schema version, disposition, bounded attempt counters and safe result/failure references. Raw payload bodies, authorization headers, signatures, credential values and secret material are not stored or projected.

Replay identity is the provider event identity plus payload fingerprint. Reuse of one provider event ID with different payload content fails closed. Transient failures consume a bounded retry budget and then enter DEAD_LETTER. Permanent failures enter REJECTED.

Provider authentication remains provider-specific and must occur before a successful replay can be short-circuited. Stripe signature/account/environment verification remains mandatory, while AO-10 billing/account persistence remains the idempotent authority preventing duplicate financial or entitlement effects.

## Consequences

- AO-18 remains authority for integration definitions, credential references and connection health.
- AO-19 can observe and diagnose provider/API operations but cannot mint credentials or bypass AO-18.
- There is no arbitrary request console with unrestricted credentials.
- Operators can inspect failures, telemetry and DLQ state from Admin without SSH/database archaeology.
- API/Webhook operational facts remain private Admin state and never become FAXT, INXIGHT, Xignal or AXIGLAND truth.
