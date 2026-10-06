# Quickstart: Subscriber Registration and Portfolio E2E

This guide describes the deterministic local E2E. It does not claim that external Google/OpenAI clients, production domains, checkout or backup/restore are configured.

## Preconditions

- Root-provided AXIGNAL runtime config supplies an enabled provider entry and exact callback for local testing. Tests use a local OIDC/JWKS authority and do not require a production client or external network.
- File-backed SQLite is created beneath a unique temporary data directory.
- A durable entitlement fixture is seeded with confirmed capacity 1, 2, or 100. No account-creation default is seeded.
- Canonical Organization fixtures are inserted through the global Organization test authority; registry candidates alone are not canonical.

## Scenarios

1. Start `REGISTER` at Google provider adapter; capture the opaque transaction cookie and authorization URL. Complete callback with exact issuer/client, valid key/signature, state, nonce, PKCE verifier and code; reopen the database and resume the same session/Principal/Tenant.
2. Replay callback or use wrong client, issuer, redirect, nonce, browser token or signature; each attempt is denied. Revoke a valid session, reopen store, and prove its token remains rejected. Expired session similarly stays rejected after restart.
3. Add exactly 1, then 2, then 100 canonical Organization references under matching confirmed entitlement. Reopen the portfolio store and verify private Focus count, references and lifecycle. Duplicate idempotency key/Organization creates no duplicate run or slot.
4. Attempt an additional add above capacity; assert exact checkout increment and zero new active Focus. Simulate browser return without trusted billing update and retry; still denied. Apply a confirmed durable billing update, reopen and retry; only then add succeeds.
5. Create a second Tenant referencing one of the same canonical Organizations. Assert membership is checked before any private row load and neither Tenant can read the other's Focus IDs.
6. Pause a Focus and verify it remains visible, retains its output and consumes capacity after restart. Resume checks entitlement/currentness. Remove excludes it and prevents future work without deleting the Organization/FAXT fixture.
7. Replace one Focus; before target resolution, on capacity unknown, and when the new run fails, assert old Focus/output remain. On success, one transaction activates replacement without a transient capacity overrun.
8. Reobserve one Focus; preserve prior projection through interrupted/insufficient runs and replace only on a valid new result.
9. Resolve only public registry candidates; assert `IDENTITY_PENDING` and no canonical Organization, Focus or economic output. Resolve via the global identity authority and rerun to create a Focus.

## Required test evidence

- Real SQLite adapters, uniqueness and transaction behavior; reopen store or launch a fresh process between operations.
- Authorization-before-load order for every private read and mutation (including Tenant spoofing, revoked membership and cross-Tenant IDs).
- Auth state single-use, replay/expiry rejection, issuer/client binding and session revocation/expiry across restart.
- Capacity concurrency/reservation under multiple calls, exact 1/2/100 behavior and no browser-return grant.
- OIDC/JWKS/billing/Organization services may use deterministic protocol fixtures, but no in-memory fake may substitute for persistent identity, session, membership, capacity or portfolio authority.

Root owns full repository gates and subscriber HTTP/frontend composition. Provider sign-in remains unavailable until actual external registration/configuration is confirmed.
