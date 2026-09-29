# Feature Specification: P0-CORE-01 Canonical Xeed Authority

**Feature Branch**: architecture/p0-core-01-xeed-authority  
**Created**: 2026-09-27  
**Status**: Authorized implementation  
**Input**: CTO decision and execution order P0-CORE-01

## Scope and authority

Establish the smallest canonical private-observer identity and deterministic
authorized-read boundary for a Xeed. Organization remains a global AXIGLAND
entity. A Xeed is private observation context owned by one Tenant and refers to
one Organization. A Principal may read a Tenant's Xeed only through an
authoritative Principal–Tenant membership.

This slice does not authenticate Principals. Its request context is trusted
input from a future authenticated outer boundary. It does not add production
persistence, an external API, Client/Workspace authority, knowledge binding,
Subscriber projection, Context Broker, or P0-HFX-01.

## User Scenarios & Testing

### User Story 1 — Keep private Xeed identity separate from world identity (P1)

A future trusted application boundary must distinguish private observation
contexts even when multiple tenants observe the same Organization or use the
same presentation label.

**Why this priority**: Authorization cannot be reliable if private context is
identified by a shared world entity or mutable label.

**Independent Test**: Construct two tenants, two Xeeds, one Organization and
identical labels; prove distinct Xeed IDs and unchanged Organization identity.

**Acceptance Scenarios**:

1. Given two tenants observing one Organization, when each has a Xeed, then
   each Xeed has a distinct identity and its own tenant owner.
2. Given equal or changed presentation labels, when identity is compared, then
   the Xeed ID remains unchanged and no cross-tenant identity collision occurs.
3. Given a Xeed germination state, when its identity is inspected, then it is
   keyed by the Xeed and does not replace the Xeed's canonical private identity.

### User Story 2 — Read a Xeed only inside an authorized Tenant context (P1)

A trusted request context identifies a Principal and selected Tenant. The
application boundary checks that membership before resolving the requested
Xeed and returns an authorized wrapper only if the Xeed belongs to that Tenant.

**Why this priority**: This is the minimum security boundary needed before any
private Xeed context can be consumed.

**Independent Test**: Exercise authorized, cross-tenant, spoofed-tenant,
missing-context, unknown-principal, missing-membership and unknown-Xeed cases
against deterministic in-memory test authorities.

**Acceptance Scenarios**:

1. Given a Principal with membership in Tenant A and Xeed A owned by Tenant A,
   when read is requested in that context, then an AuthorizedXeed is returned.
2. Given a Xeed owned by another Tenant, when the request context lacks
   membership in that Tenant, then access is denied and no authorized object
   is returned.
3. Given no context, unknown Principal, missing membership or unknown Xeed,
   when read is requested, then the corresponding internal failure is
   deterministic and fail-closed.
4. Given unknown and cross-tenant Xeed outcomes, when a future private external
   adapter is implemented, then both map to the same non-enumerating response.

## Edge Cases

- Missing context or blank canonical IDs fail closed.
- A Principal selecting a Tenant without membership is denied before Xeed
  lookup.
- A member requesting another Tenant's known Xeed receives an internal access
  denial; a future external boundary must conceal the distinction.
- Unknown Principal, unknown Xeed, and known Xeed owned by another Tenant are
  distinct internal outcomes.
- Duplicate Xeed IDs cannot overwrite another record in the deterministic
  test authority.
- Xeed germination state grants no additional authorization or canonical write authority.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST represent Principal, Tenant, Xeed and
  Organization identities as distinct typed identities.
- **FR-002**: A Xeed MUST be owned by exactly one Tenant and reference one
  canonical Organization without copying Organization truth.
- **FR-003**: Multiple tenants MUST be able to reference the same Organization
  through distinct Xeeds.
- **FR-004**: A trusted request context MUST identify a Principal and selected
  Tenant but MUST NOT claim to authenticate the Principal.
- **FR-005**: The authorized-read boundary MUST resolve Principal, verify
  Principal–Tenant membership, resolve Xeed, verify Xeed ownership, and only
  then return an AuthorizedXeed.
- **FR-006**: Missing context, unknown Principal, absent membership, unknown
  Xeed and cross-tenant access MUST fail closed with precise internal outcomes.
- **FR-007**: Caller-supplied Tenant selection MUST NOT prove membership or
  ownership.
- **FR-008**: Labels MUST remain optional presentation data and MUST NOT
  influence Xeed identity.
- **FR-009**: The external disclosure rule MUST document that future private
  adapters collapse unknown-Xeed and cross-tenant outcomes to the same
  non-enumerating response; no HTTP API is added.
- **FR-010**: The implementation MUST use only deterministic in-memory
  test/dev authority, with production persistence and authentication absent.
- **FR-011**: Xeed germination lifecycle state MUST remain subordinate to the
  authorized Xeed identity and MUST NOT itself grant knowledge membership or canonical write authority.
- **FR-012**: Subscriber read model, Context Broker, AXIGLAND projection and
  P0-HFX-01 MUST remain unimplemented.

### Key Entities

- **Principal**: canonical internal identity of an authenticated actor; this
  slice does not authenticate it.
- **Tenant**: canonical private ownership/isolation boundary.
- **PrincipalTenantMembership**: authoritative binding permitting a Principal
  to act within a Tenant.
- **Xeed**: private observation context owned by one Tenant and referencing one
  Organization.
- **Organization**: shared global economic identity, never a Tenant.
- **TrustedRequestContext**: Principal and selected Tenant already established
  by a trusted outer layer.
- **AuthorizedXeed**: application result returned only after membership and
  Xeed ownership checks succeed.

## Success Criteria

- **SC-001**: All ten CTO security matrix cases pass deterministically,
  including ownership, spoofing, missing context, membership, unknown Xeed,
  same Organization across tenants, label collision and label mutation.
- **SC-002**: Membership is checked before Xeed resolution; failed membership
  produces no Xeed lookup and no AuthorizedXeed.
- **SC-003**: Static type checking distinguishes PrincipalId, TenantId,
  XeedId and OrganizationId.
- **SC-004**: Tests and source prove production persistence, authentication,
  HTTP API and private knowledge retrieval are not introduced.
- **SC-005**: Repository deterministic quality gates pass without suppressions
  or weakened governance.

## Assumptions

- A future authenticated adapter will construct TrustedRequestContext from a
  verified Principal identity; this slice does not provide that adapter.
- Principal–Tenant membership is the only current authorization relation.
- Client context and Workspace remain reserved/presentation concepts.
- Test/dev in-memory records are not production data or persistence.
