# ADR-0018: Canonical Xeed Identity and Tenant Authorization Boundary

- **Status:** Accepted for P0-CORE-01; implemented as a domain/application
  authority on the P0-CORE-01 branch
- **Date:** 2026-09-27
- **Authority:** CTO P0-CORE-01 decision; MASTER §§3–7, §55; Constitution
  IV, VI, XX and XXI
- **Scope:** private observer identity and authorized Xeed reads

## Context

Organization is a shared AXIGLAND world entity. It cannot identify private
subscriber context or serve as an isolation boundary. ObservationSeed is an
observation assignment associated with Organization; it is not a Xeed.
P0-CORE-01 reconciliation found no Principal, Tenant, Xeed, authentication,
authorization, persistence or application read implementation.

The CTO resolved the current authority: Tenant owns private Xeeds; a Principal
must have an authoritative Tenant membership; a Xeed references one
Organization; and a trusted request context carries the Principal and selected
Tenant without authenticating either.

## Decision

- Organization remains global economic/world identity and is never a Tenant.
- Tenant is the current canonical private isolation and Xeed-ownership
  boundary. A Tenant may own multiple Xeeds.
- Principal is a stable internal identity for an actor authenticated by a
  future outer adapter. This decision does not add authentication.
- Principal–Tenant membership is the authority for acting within a Tenant.
  Caller selection of tenant_id is not proof of membership.
- Each Xeed has a stable identity, belongs to exactly one Tenant, and
  references one Organization. Different Tenants may create distinct Xeeds
  referencing the same Organization. Labels are presentation data only.
- ObservationSeed remains an Organization observation assignment. No
  ObservationSeed–Xeed cardinality or binding is established.
- The application read sequence is:

      trusted context → resolve Principal → verify membership
        → resolve Xeed → verify Xeed Tenant → AuthorizedXeed

- Missing context, unknown Principal, denied membership, unknown Xeed and
  cross-Tenant Xeed access remain distinct internal failures. The authorized
  result is a separate type returned only after all checks.
- Future private external adapters must map unknown-Xeed and cross-Tenant
  denial to the same non-enumerating not-found response. No external API is
  implemented here.
- Production persistence, migration, knowledge-to-Xeed binding, Client
  authority, Workspace authority, Context Broker, Subscriber read model and
  AXIGLAND projection remain unimplemented. In-memory authority exists only
  as test/dev infrastructure.

## Alternatives considered

- **Use Organization as the private boundary:** rejected; Organization is
  global, observer-independent world identity.
- **Use ObservationSeed as Xeed identity:** rejected; it represents an
  observation assignment and has no established Xeed ownership semantics.
- **Trust caller-provided tenant_id:** rejected; context selection cannot
  establish Principal membership.
- **Add authentication or provider-specific identity:** rejected; a future
  adapter supplies a trusted Principal identity.
- **Add production database and repository infrastructure:** rejected; no
  canonical persistence architecture exists and this slice does not require
  one to prove the domain/application boundary.
- **Make Client a second isolation entity now:** rejected; Tenant is the
  current boundary; client_context remains reserved until a concrete need is
  established.

## Tradeoffs

Typed string identities prevent accidental cross-plane substitutions during
static checking while preserving the repository's current string ID
representation. The application boundary can prove policy ordering, but
production identity/membership storage and authentication remain responsibilities
of future, separately authorized work.

## Consequences

- A future authenticated adapter must create TrustedRequestContext only from
  verified identity; this value object does not authenticate.
- Private knowledge must not be retrieved until an AuthorizedXeed exists.
- The in-memory test/dev authority is not production persistence.
- Future APIs must conceal Xeed existence across unknown and cross-Tenant
  outcomes.
- P0-HFX-01 remains not started because canonical knowledge-to-Xeed binding
  is not implemented.
- ADR-0017 remains the broader target for private continuity and AXENT routing;
  this ADR implements only the root Xeed identity/read boundary.
