# ADR-0056: Admin Identity, RBAC and Privileged Session Boundary

- **Status:** Accepted
- **Date:** 2026-10-01
- **Source doctrine:** MASTER §2.1A, §5, §39, §46; Constitution §§II, IV, VI, XII, XIV, XX–XXI; ADR-0017, ADR-0018, ADR-0055
- **Implementation:** AO-01

## Context

AXIGNAL already has a subscriber/private-scope authority based on `Principal`, `Tenant`, binary `PrincipalTenantMembership`, `TrustedRequestContext` and membership-first `AuthorizedXeed` reads. That authority is intentionally not an Admin role model and has no production authentication runtime.

Admin V0.2 needs a stronger and separate authority for staff-only operational state, including future customer, billing, finance, fiscal, governance and system controls. Reusing subscriber membership, provider roles, email domains or a frontend `isAdmin` flag would collapse independent trust planes and make privileged access dependent on ungoverned external claims.

## Decision

AXIGNAL establishes a separate provider-neutral Admin security plane.

```text
SUBSCRIBER
Principal + Tenant + Membership
!=
ADMIN
AdminPrincipal + AdminRole/Scope + AdminSession
```

An authentication provider may verify a staff identity, but AXIGNAL owns Admin authorization. Provider roles, organization claims, email domains, subscriber membership and payer state never grant Admin scopes directly.

Admin bearer credentials are issued by AXIGNAL only after a trusted outer authentication adapter has mapped a verified staff identity to an `AdminPrincipalId` with at least one active Admin role. Subscriber/product credentials are never accepted as Admin credentials. A future deployment may reuse an identity provider, but Admin and subscriber sessions/audiences/cookies must remain logically distinct.

## Roles and scopes

AO-01 defines these roles:

- `FOUNDER`
- `BUSINESS`
- `FINANCE_FISCAL`
- `OPERATIONS`
- `RESEARCH_INTELLIGENCE`
- `TECHNICAL_SYSTEM`
- `SUPPORT`
- `AGENT_SAFE_READER`

Roles expand deterministically to explicit `admin:*` scopes. `FOUNDER` receives all currently declared Admin scopes. Other roles receive only the scopes required for their operating function. `AGENT_SAFE_READER` receives only `admin:agent-safe:read`; it does not inherit customer, billing, finance, governance or system reads.

No Admin role changes canonical AXIGLAND authority.

## Session contract

Admin sessions are server-side, bounded and fail closed:

- the raw bearer token is generated with cryptographic randomness;
- only its SHA-256 digest is persisted;
- the downstream authorization grant contains no raw credential;
- default lifetime is eight hours and implementation maximum is twelve hours;
- expiration is checked on every authorization;
- revocation is checked on every authorization;
- active roles are re-read on every authorization, so privilege revocation applies to an existing session without waiting for session expiry;
- a principal with no active Admin roles cannot receive or use an Admin session.

The current session service is provider-neutral. It does not select Clerk, Google, password/TOTP implementation, cookie transport, CSRF policy or browser login UX.

## Risk and assurance

Admin commands declare a risk class:

```text
READ
WRITE
SENSITIVE
CRITICAL
```

`READ` and ordinary `WRITE` require a valid session and the exact scope. `SENSITIVE` requires `STEP_UP` assurance that is no more than 15 minutes old; after that window the session may remain valid for ordinary access but sensitive operations require fresh step-up.

`CRITICAL` requires:

1. a valid actor session with `STEP_UP`;
2. the exact required scope;
3. a second, distinct Admin principal;
4. a live second Admin session with `STEP_UP`;
5. the same required scope for that approver.

Founder-role changes are critical once a two-founder quorum exists. The one exception is establishing the second founder: the initial founder may grant the second `FOUNDER` role with step-up because a distinct founder approver cannot exist before that grant. The last active founder cannot be revoked.

Future destructive financial/fiscal/security operations should classify themselves through this same risk contract rather than inventing route-local approval rules.

## Bootstrap

Exactly one initial `BOOTSTRAP_FOUNDER` privilege event may exist before any other Admin privilege history. Bootstrap is not a reusable bypass. After the first privilege event, all role changes use authenticated Admin sessions.

## Audit

Role grants, revocations and founder bootstrap are immutable `AdminPrivilegeEvent` records. Current roles are reconstructed from append-only history rather than overwritten in place. The durable ledger carries its own append sequence so replay order never depends on a random event ID or equal timestamps.

Session issuance and revocation are stored separately from privilege history. Raw bearer credentials are never stored in the Admin database or emitted in an `AdminAuthorizationGrant`.

## Consequences

- Subscriber `PrincipalTenantMembership` is not silently upgraded to RBAC.
- Admin authorization can evolve independently of subscriber account roles.
- A compromised or stale provider-side role claim cannot by itself grant Admin.
- Future Admin HTTP routes and read models must require an `AdminAuthorizationGrant` with the exact scope.
- Future exports and Admin MCP receive scoped, secret-free grants rather than raw session credentials.
- Provider selection and browser/session transport remain separate future adapter decisions.
- The session/privilege store is operational private state and has no AXIGLAND write authority.

## Enforcement

- `domain/admin_access/` owns provider-neutral roles, scopes, session records, risk classes and secret-free grants.
- `application/admin_access/` owns fail-closed authorization, expiry, step-up/dual approval and privilege-change commands.
- `pipeline/admin_access/` persists session digests, revocations and append-only privilege events in SQLite.
- `tools/runtime/admin_access.py` is the HTTP bearer guard future Admin routes must use; AO-01 itself exposes no Admin route.
- AO-01 unit/integration/contracts prove denied scopes, expiry, revocation, fresh step-up, dual approval, founder bootstrap/quorum, deterministic append replay and no persisted raw tokens.
