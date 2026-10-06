# Data Model: Subscriber Runtime Authority

This model separates provider identity, subscriber authority, purchased capacity, private attention and canonical economic truth.

## Entities

### VerifiedExternalIdentity

- Exact OIDC issuer and subject claims after signature, audience, issuer, time and nonce validation.
- Optional `client_id` is sourced from the validated server configuration, not a claim or caller. It is included in binding keys for client-scoped pairwise subjects.
- Email and profile fields are not keys or authority.

### IdentityBinding

- Stable mapping from exact `(issuer, configured client scope?, subject)` to exactly one `PrincipalId`.
- Unique key and foreign key to Principal.
- Existing 048 two-field lookup remains compatible when `client_id=None`.
- Duplicate, orphan, corrupt or unavailable binding is non-authorizing.

### Principal, Tenant and membership

- `Principal`: stable AXIGNAL actor ID generated independently from provider identifiers.
- `Tenant`: private isolation and Focus ownership scope.
- `PrincipalTenantMembership`: binary Principal/Tenant authority, without roles.
- First registration creates these records and its identity binding atomically. It creates no capacity grant.

### OIDC transaction

- Provider ID, configured issuer/client/redirect, opaque transaction-token hash, state hash, nonce, PKCE verifier, created/expiry timestamps and single-use consumption marker.
- The raw transaction token exists only for the browser cookie; OIDC callback secrets never enter logs. The transaction is usable once and only for its initiating provider/client/browser binding.

### Subscriber session

- Hash of a high-entropy opaque bearer, Principal, selected initial Tenant, issue/expiry and revocation timestamps.
- The bearer is returned once to the HTTP boundary; the durable store contains only its hash.
- Every private operation rechecks active session and current membership; sessions do not cache indefinite membership authority.

### EntitlementSnapshot and CheckoutRequest

- Entitlement snapshot: optional confirmed capacity, currentness and confirmation timestamp for a consumption scope.
- Checkout request: exact additional quantity, idempotency reference and pending/confirmed correlation. It is not a grant.
- Payer identity and payer-to-Tenant cardinality remain owned by billing and unspecified here.

### Observation Focus and PortfolioEntry

- Existing `Xeed` identity remains internal; public product terminology is Organization/Observation Focus.
- One Tenant-owned private Focus references one global `OrganizationId`, never an Organization copy.
- Portfolio lifecycle is `ACTIVE`, `PAUSED`, `REMOVED`, with a separately tracked pending replacement/reobservation run. Active and paused entries consume capacity; removed entries do not.
- A pending unresolved Organization locator is a private attention request, not a Focus or canonical node.
- Labels/locators are presentation or research inputs, never Organization facts.

### ObservationRun

- Focus ID, unique idempotency key, trigger, lifecycle/progress outcome, start/end times and optional successful output reference.
- Failed/incomplete run does not replace the latest successful output.
- A run has no authority to write canonical truth; admission remains independent.

## Authority relations

```text
validated OIDC provider/client
  -> exact external identity binding -> Principal
  -> initial Tenant + binary membership
  -> current session + membership authorization
  -> confirmed capacity snapshot -> private Observation Focus
  -> global Organization resolution -> independent observation run
  -> evidence admission -> shared AXIGLAND truth (only through existing authority)
```

## Invariants

1. Provider, Principal, Tenant, membership, payer, Focus and Organization are distinct identities.
2. Membership and session are checked before private record load; mutation transactions recheck membership.
3. Durable unique constraints and transactions make registration, capacity reservation, Focus creation and replacement safe under retries/races.
4. An unknown/stale entitlement cannot authorize extra Focuses; browser checkout return is never a grant.
5. Public registry candidates and user-supplied Organization locators cannot create canonical Organizations or FAXTs.
6. Private Focus create/pause/remove/replace cannot delete or mutate canonical Organization/evidence/truth.
7. OIDC/session credentials are not logged; raw session and transaction tokens are not persisted.
8. Restart restores valid sessions and private portfolio state; expired/revoked authority stays denied.
9. `UNKNOWN` capacity, unresolved Organization identity, or unavailable authority stays explicitly unavailable/unknown.
