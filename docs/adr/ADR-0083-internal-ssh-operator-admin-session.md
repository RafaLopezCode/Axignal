# ADR-0083: Internal SSH Operator Admin Session Adapter

- **Status:** Accepted
- **Date:** 2026-10-04
- **Implements:** AO-01 production composition required by AO-24A Customer Zero
- **Authority:** MASTER, Constitution, ADR-0056, ADR-0082

## Context

AO-01 defines provider-neutral Admin identity, RBAC and opaque server-side sessions, but deliberately does not select a public browser identity provider. AO-24A Customer Zero is an internal operator-only production surface already restricted to loopback port 18182 and an authenticated SSH tunnel. Production previously left `runtime.admin_access` uncomposed, so the surface failed closed but no real AO-01 session could be validated.

## Decision

For internal Customer Zero only, authenticated root SSH is the trusted outer operator authentication event. A root-only one-shot CLI may bootstrap the single founder event when no privilege history exists and issue a normal AO-01 opaque session. The raw token is written exclusively to an operator-selected `0600` file and is never stored in Git, runtime configuration, logs, projections or SQLite; AO-01 persists only its SHA-256 digest.

The production runtime composes `AdminAccessService` with the durable `SqliteAdminAccessStore` only when `AXIGNAL_ADMIN_ACCESS_ENABLED=true`. Its authenticator is validation-only and rejects every external credential. Therefore the runtime cannot exchange SSH material, passwords or arbitrary provider claims for an Admin session. Every request continues to enforce expiry, revocation, active roles and exact scopes.

The SSH-issued session uses PRIMARY assurance. It is sufficient for ordinary READ and WRITE scopes such as Customer Zero observation, but not SENSITIVE or CRITICAL operations that require fresh STEP_UP/dual approval.

## Non-goals

This does not select the future public/staff browser identity provider, does not make SSH a subscriber authentication mechanism, does not expose a public login endpoint, and does not grant Admin scopes from subscriber membership, email domain, payer state or frontend claims.

## Consequences

- Customer Zero can be dogfooded in production through the already-authorized SSH operator channel.
- A later provider adapter can replace session issuance without changing AO-01 authorization or stored privilege/session semantics.
- Loss of SSH/root authority remains a host-security incident; this adapter adds no weaker remote credential path.
