# ADR-0020: Authorized Xeed FAXT Collection Read

- **Status:** Accepted and implemented for P0-CORE-03; production persistence
  and reference writing remain unimplemented
- **Date:** 2026-09-28
- **Authority:** CTO P0-CORE-03 decision; MASTER §§4.5, 5, 6, 15, 20; ADR-0018
  and ADR-0019
- **Scope:** enumerating and resolving explicit FAXT references for one
  authorized Xeed

## Context

P0-CORE-02 permits an `AuthorizedXeed` to read one known FAXT after checking
its exact `(XeedId, FaxtId)` reference. Subscriber projection needs the set of
explicitly admitted FAXTs, but must not enumerate global knowledge and filter
afterward.

## Decision

- The collection means only the explicit references belonging to one
  `AuthorizedXeed`, resolved to their existing global FAXT objects.
- The application entry point requires `AuthorizedXeed`. Raw Xeed, Tenant or
  Organization IDs cannot authorize a collection read.
- The reference reader lists by the Xeed identity taken from that authorized
  capability. It exposes no global reference enumeration.
- The complete reference set is validated before resolving global FAXTs.
  Malformed/mismatched references, duplicate membership, dangling FAXTs,
  mismatched identity and wrong object types fail closed; no partial result is
  returned.
- Results reuse `AuthorizedXeedFaxt` and preserve original FAXT object
  identity/state. They do not mutate or duplicate FAXT and do not read
  Evidence, create provenance, grant source rights or infer membership from
  Organization subject equality.
- The immutable result is ordered by stable `FaxtId` solely for deterministic
  output: `ORDERING_SEMANTICS=NONE` and `ORDERING_PURPOSE=DETERMINISM_ONLY`.
- In-memory scoped enumeration remains test/dev-only. Production persistence,
  reference writing and external adapters are not implemented.

## Alternatives considered

- **Enumerate global FAXTs or references then filter:** rejected because
  private scope must constrain selection before global knowledge resolution.
- **Infer Xeed membership from Organization:** rejected; observer context is
  private and every FAXT requires its own explicit reference.
- **Return a partial collection when one reference dangles:** rejected because
  it would misrepresent completeness.
- **Sort by relevance, currentness, epistemic state or recency:** rejected;
  no such ordering authority exists.

## Tradeoffs

The collection proves a deterministic application contract, not production
storage, admission lifecycle or evidence access. A dangling reference makes
the entire collection unavailable until separately repaired by an authorized
future writer.

## Consequences

- HFX or another authorized consumer can use the collection boundary without
  defining its own reference enumeration.
- The same canonical FAXT remains shareable across Xeeds/Tenants through
  independent references.
- Evidence rights, provenance, history, non-FAXT binding, ranking and
  persistence remain separate authorities.
- P0-HFX-01 remains unstarted by this ADR and requires its own authorization.
