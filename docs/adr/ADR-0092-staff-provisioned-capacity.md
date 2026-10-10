# ADR-0092: Staff-provisioned capacity — Admin adds organizations without checkout

- **Status:** Proposed (awaiting CTO acceptance)
- **Date:** 2026-10-10
- **Issue:** #177 (Phase 3, Admin Executive)
- **Authority:** MASTER (no CRM/workflow/sponsored functionality; user, agency or subscriber
  input never mutates canonical truth); Constitution; ADR-0056 (Admin identity, RBAC and
  session boundary); ADR-0087 (organization admission); ADR-0091 (attention-first observation).
- **Does not amend:** billing, Stripe, checkout, invoices, subscription lifecycle or the
  design-partner pilot (capacity exactly 1).

## Context

An authorized AXIGNAL operator must be able to add organizations for internal research and
for client accounts without checkout or prior payment, and to use AXIGNAL as Customer Zero
through the same subscriber experience. Before this ADR the only capacity sources were a
verified paid subscription and the single-organization design-partner pilot. Simulating a
purchase (fake subscription, forged invoice, Stripe edits) is forbidden.

## Decision

1. **A separate, explicit capacity source: `STAFF_GRANT`.** A staff grant gives a tenant
   N organizations (1–500) until an expiry of at most 366 days. It lives in its own store
   (`subscriber-staff-capacity.sqlite3`) and is never written to, or read as, billing.
   Its wire provenance is always `STAFF_GRANT_NOT_BILLING`.
2. **One entitlement projection, additive provenance.** The existing
   `_ProjectionEntitlements` (subscriber composition, observation enrollment, observation
   research) adds active staff capacity to verified paid capacity
   (`BILLING+STAFF_GRANT`), or uses it alone (`STAFF_GRANT`). Paid capacity is never
   replaced or edited. Policy version: `subscriber-entitlement-snapshot-v3`.
3. **Authority.** Reads need `admin:customers:read`. Every write (preview, grant, revoke,
   add organization) needs `admin:customers:write` at `SENSITIVE` risk, i.e. a `STEP_UP`
   session no older than 15 minutes (ADR-0056). The Admin HTTP guard authorizes; the
   application service re-checks scope and assurance (defense in depth).
4. **Destinations.** `CUSTOMER_ACCOUNT` or `AXIGNAL_INTERNAL`. Internal capacity is only
   accepted for the configured AXIGNAL tenant (`AXIGNAL_STAFF_INTERNAL_TENANT_ID`), and that
   tenant can never receive customer capacity, so an internal grant cannot leak to a client.
5. **Tenant isolation.** Staff acts only on a tenant that exists with an active member.
   The organization add is a distinct `STAFF_ADD` portfolio operation: no subscriber
   membership is borrowed or created, the actor (`admin:<principal>`) is in the idempotency
   fingerprint, and capacity is the target tenant's own entitlement. Other tenants never
   see the work.
6. **Idempotency, expiry, revocation, audit.** Grants are idempotent by key; a reused key
   with different terms is `IDEMPOTENCY_CONFLICT`. Expired or revoked grants stop counting
   immediately; revocation is idempotent and keeps the first record. Organizations already
   added are kept (no silent deletion). `staff_capacity_audit` is append-only (UPDATE and
   DELETE abort in SQLite triggers) and records `CAPACITY_GRANTED`, `CAPACITY_REVOKED` and
   `ORGANIZATION_ADDED_BY_STAFF` with actor, tenant, reason and outcome.
7. **Never a checkout.** A full portfolio returns `CAPACITY_REQUIRED` to staff; no checkout,
   payment intent, subscription or invoice is created by any staff action.
8. **Identity is unchanged.** Staff adds resolve identity exactly as a subscriber add
   (ADR-0087/0091): pending or rejected identities create nothing. Opportunity, relationship
   and observation semantics are unchanged.

## Operations

| Variable | Default | Meaning |
|---|---|---|
| `AXIGNAL_STAFF_CAPACITY_ENABLED` | `false` | Enables the store and the Admin routes. Off ⇒ `503 STAFF_CAPACITY_DISABLED`, entitlement unchanged. |
| `AXIGNAL_STAFF_INTERNAL_TENANT_ID` | empty | AXIGNAL's own subscriber tenant for Customer Zero. Empty ⇒ internal grants refused. |

Admin routes: `GET /internal/admin/staff-capacity?tenantId=…`,
`POST /internal/admin/staff-capacity/{preview|grant|revoke|organizations}` (JSON ≤ 4 KiB).
Web proxy: `/api/admin/staff-capacity[/{action}]` (same origin, Admin cookie, strict schema).

**Customer Zero.** The operator signs in to `/account` with their own Google account (this
creates a normal subscriber tenant), configures that tenant as
`AXIGNAL_STAFF_INTERNAL_TENANT_ID`, grants `AXIGNAL_INTERNAL` capacity, and then uses exactly
the subscriber experience. Privileged controls stay in Admin.

## Known limits (explicit, not hidden)

- **No production step-up issuer yet.** The SSH operator channel issues `PRIMARY` sessions,
  so in production every staff write returns `403 STEP_UP_REQUIRED` until a step-up issuer
  exists. This ADR does not lower the risk class to make it usable; the CTO decides the
  issuer (e.g. a short-lived SSH-issued `STEP_UP` session ≤ 15 minutes) separately.
- **Observation latency.** Staff never acts as the client, so the immediate post-add
  observation trigger (which runs in the subscriber's request context) is skipped. The
  scheduled enrollment cycle, which iterates the tenant's real members, picks the Focus up.
- **Account reference discovery.** AXIGNAL stores no subscriber emails, so staff cannot look
  a tenant up by email. The client (or the operator, for Customer Zero) provides the account
  reference. Showing that reference in `/account` is a follow-up after the workspace
  redesign merges.

## Consequences

- Positive: governed, reversible, audited capacity with no billing forgery; one projection
  for every runtime reader; Customer Zero uses the real product.
- Negative: another capacity source to reason about; mitigated by explicit provenance in
  the entitlement source and on every grant.

## Verification

`tests/subscriber_access/test_staff_capacity.py` (scope, step-up, validation, idempotency,
conflict, isolation, expiry, revocation, append-only audit, wire provenance) and
`tests/integration/test_staff_capacity_e2e.py` (real Admin HTTP: grant → add → the client
sees it, the other tenant does not; billing rows unchanged, no pilot, no checkout; 401/403/404;
revocation; full portfolio ⇒ `CAPACITY_REQUIRED`; staff capacity is additive to verified
billing without editing it). Web: `apps/web/experience/tests/staff-capacity.test.ts`.
