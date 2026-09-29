# ADR-0018: Canonical Xeed Identity and Tenant Authorization Boundary

- **Status:** Accepted; terminology reconciled by ADR-0023. P0-CORE-01 identity/read authority and P0-CORE-02 FAXT contextual-read boundary are implemented as domain/application contracts with deterministic test/dev authority
- **Date:** 2026-09-27
- **Authority:** CTO P0-CORE-01 decision; MASTER §§3–7, §55; Constitution
  IV, VI, XX and XXI
- **Scope:** private observer identity and authorized Xeed reads

## Context

Organization is a shared AXIGLAND world entity. It cannot identify private
subscriber context or serve as an isolation boundary. ADR-0023 later clarified
that the customer-planted persistent observation seed is the Xeed itself;
`XeedGerminationState` carries lifecycle/work state for that Xeed, while a
Xignal is an observation-derived economic signal.
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
- `XeedGerminationState` is keyed by one Xeed and is operational/cognitive
  lifecycle state only. It grants no knowledge membership or canonical write
  authority. Xignals produced during germination are not authorization tokens.
- The application read sequence is:

      trusted context → resolve Principal → verify membership
        → resolve Xeed → verify Xeed Tenant → AuthorizedXeed

- Missing context, unknown Principal, denied membership, unknown Xeed and
  cross-Tenant Xeed access remain distinct internal failures. The authorized
  result is a separate type returned only after all checks.
- Future private external adapters must map unknown-Xeed and cross-Tenant
  denial to the same non-enumerating not-found response. No external API is
  implemented here.
- Production persistence, migration, knowledge reference writing, Client
  authority, Workspace authority, Context Broker, Subscriber read model and
  AXIGLAND projection remain unimplemented. In-memory authority exists only
  as test/dev infrastructure.

## Alternatives considered

- **Use Organization as the private boundary:** rejected; Organization is
  global, observer-independent world identity.
- **Keep a separate legacy ObservationSeed beside Xeed:** superseded by
  ADR-0023; the planted seed is the Xeed, while germination lifecycle is a
  separate state keyed by Xeed.
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
- P0-CORE-02 establishes a private Xeed-to-global-FAXT reference and an
  AuthorizedXeed-only read boundary. Production reference writing and
  persistence remain unimplemented; see ADR-0019.
- P0-HFX-01 remains not started.
- ADR-0017 remains the broader target for private continuity and AXENT routing;
  this ADR implements only the root Xeed identity/read boundary.

[executed on device: DESKTOP-7L6CMEJ (d615520f-0404-49b0-83c7-620cc18c31f4)]