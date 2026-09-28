# Feature Specification: P0-CORE-03 Authorized Xeed FAXT Collection Read

**Feature Branch**: `architecture/p0-core-03-authorized-faxt-collection`
**Status**: CTO-authorized implementation
**Authority**: CTO P0-CORE-03 decision; ADR-0018 and ADR-0019

## Scope and canonical meaning

An authorized collection is the set of explicit `XeedFaxtReference` values
belonging to one `AuthorizedXeed`, resolved to their original global canonical
FAXT objects. It is a contextual read result, not canonical world truth.
References retain only `(XeedId, FaxtId)` semantics: they grant no ownership,
truth, provenance, source rights or epistemic promotion.

Only FAXT is supported. Collection reads require `AuthorizedXeed`; reference
enumeration is scoped to exactly its Xeed and happens before global FAXT
resolution. Organization subject equality, Tenant identity and raw IDs never
establish membership. Production storage/writing and Evidence reads remain
absent.

## Requirements

- **FR-001**: The application collection entry point accepts only
  `AuthorizedXeed`.
- **FR-002**: Enumerate references for that Xeed only; never enumerate global
  references or FAXTs to filter afterward.
- **FR-003**: Resolve only the referenced global FAXTs and return the original
  objects through the existing `AuthorizedXeedFaxt` wrapper.
- **FR-004**: Return an immutable collection; an empty authorized context
  returns an empty collection.
- **FR-005**: Fail closed on malformed/mismatched references, duplicate
  membership, dangling references, mismatched FAXTs and wrong object types.
  Never return a partial collection after an unresolved reference.
- **FR-006**: Preserve epistemic state, currentness, evidence references and
  canonical object identity without enriching or mutating FAXT.
- **FR-007**: Do not load Evidence or infer source rights, provenance,
  relationships or subject-based membership.
- **FR-008**: Use stable FAXT identity ordering only when returning results;
  ordering has no semantic meaning and exists only for determinism.
- **FR-009**: In-memory reference enumeration remains test/dev-only. No
  production persistence, writer, API, auth provider or external service.

## Adversarial acceptance

Cover empty/single/multiple collections; same global FAXT referenced by
multiple Xeeds/Tenants; same Organization with distinct Xeed isolation; raw
Xeed/Tenant/Organization ID rejection; no global enumeration; unreferenced
FAXT exclusion; malformed, duplicate and dangling references; mismatched and
wrong-type FAXTs; label independence; UNKNOWN/currentness preservation; no
Evidence dereference; ObservationSeed non-authority; and authorization and
lookup ordering.

## Out of scope

Subscriber Projection, AXIGLAND/Golden Master integration, P0-HFX-01, graph
edges, cardinal or epistemic-layer mapping, provenance, timeline, Evidence,
other object types, persistence/writer, database, ORM, HTTP/API, auth provider,
Context Broker, ranking, search, pagination, models, Jev, OpenAI and
dependencies.
