# ADR-0019: Canonical Xeed–FAXT Contextual Reference

- **Status:** Accepted and implemented for P0-CORE-02; production writer and
  persistence remain unimplemented
- **Date:** 2026-09-28
- **Authority:** CTO P0-CORE-02 decision; MASTER §§4.5, 5, 6, 15, 20; ADR-0018
- **Scope:** explicit private contextual references to canonical FAXT objects

## Context

P0-CORE-01 established Tenant-owned Xeeds and the `AuthorizedXeed` boundary,
but did not define what it means for a Xeed to know or access canonical
knowledge. CTO resolved that question for one initial object class: FAXT.

## Decision

- FAXT identity is global world identity. A Xeed reference never owns, copies,
  mutates or duplicates canonical FAXT state.
- `XeedFaxtReference` is the immutable pair `(XeedId, FaxtId)`. It means only
  that the canonical FAXT was explicitly admitted into that Xeed's private
  cognitive context.
- A reference means no ownership, truth, provenance, relevance, importance,
  discovery, derivation, source rights or epistemic upgrade.
- The same FAXT may be referenced by multiple Xeeds and Tenants, but each
  Xeed requires its own explicit reference.
- The application reader requires an `AuthorizedXeed`, checks that Xeed's
  reference before resolving the global FAXT, and fails closed for a missing
  reference or canonical FAXT. Raw XeedId, TenantId, OrganizationId or
  knowledge ID cannot substitute for the authorized context.
- FAXT is the only supported knowledge type in this slice. Evidence,
  Observation, Relationship, INXIGHT and PATHX direct references are not
  authorized and require separate reconciliation.
- The reference copies no FAXT state, epistemic state, currentness or
  provenance. Provenance and temporal/lifecycle history are not established
  by this reference. No timestamps are added.
- In-memory authority is deterministic test/dev support only. Production
  reference writing and persistence are not implemented.

## Alternatives considered

- **Add `xeed_id` to FAXT:** rejected; would turn global knowledge into
  Xeed-owned truth and prevent legitimate sharing.
- **Copy FAXT into each Xeed:** rejected; duplicates canonical world state.
- **Treat a reference as provenance, relevance or discovery:** rejected by
  explicit CTO decision and unsupported by existing provenance authority.
- **Bind heterogeneous knowledge through a generic tag:** rejected; only FAXT
  is authorized, so a generic knowledge union is unnecessary.
- **Add production persistence or a writer adapter:** rejected; no such
  architecture is authorized or required to prove the domain/read boundary.

## Tradeoffs

The pair reference is intentionally narrow and cannot represent admission
time, lifecycle history, source rights or derivation. Those remain unknown
until separately authorized. The application can enforce read ordering, but
production storage and write policy remain absent.

## Consequences

- The shared FAXT object is returned by identity; contextual access does not
  alter its truth or epistemic state.
- A missing reference is fail-closed before global FAXT lookup.
- A future object type requires separate ontological reconciliation and CTO
  authorization.
- P0-HFX-01, Subscriber, AXIGLAND projection, Context Broker and persistence
  remain outside this decision.
