# Feature Specification: P0-CORE-02 Canonical Knowledge-to-Xeed Binding

**Feature Branch**: `architecture/p0-core-02-knowledge-xeed-binding`
**Created**: 2026-09-28
**Status**: CTO-authorized implementation
**Input**: CTO P0-CORE-02 reconciliation decision

## Scope and authority

Implement the minimum domain and application authority for explicit private
contextual references from a Xeed to global canonical FAXT objects. A
reference means only that a FAXT was explicitly admitted into that Xeed's
cognitive context. It does not establish ownership, truth, provenance,
relevance, importance, discovery, derivation, source rights or epistemic
promotion.

Only FAXT is supported. FAXT identity remains global and its canonical state
is returned by reference, never copied into a Tenant/Xeed-specific object.
Private reads require an `AuthorizedXeed`. In-memory reference authority is
test/dev-only; production writing and persistence are absent.

## Reconciliation

- Organization and FAXT remain global world identity/knowledge.
- `XeedFaxtReference` contains only `XeedId` and `FaxtId`.
- Each Xeed must have its own explicit reference; one FAXT can be referenced
  by multiple Xeeds, including across Tenants.
- A reference cannot change or duplicate FAXT identity, evidence references,
  epistemic state or currentness.
- Provenance, binding time and lifecycle history are not established by the
  reference.
- Evidence, Observation, Relationship, INXIGHT and PATHX direct binding are
  not authorized and require separate reconciliation.

## User scenarios and acceptance

1. An authorized Xeed with an explicit reference can read the original global
   FAXT object.
2. A Xeed without its own reference cannot obtain access merely because its
   Tenant owns another Xeed with a reference.
3. Another Tenant's authorized Xeed cannot use a different Xeed's reference.
4. Two independently referenced Xeeds can resolve the same global FAXT
   object without cloning or mutating it.
5. Raw Xeed, Tenant, Organization or knowledge IDs cannot replace
   `AuthorizedXeed`.
6. Missing reference or missing canonical FAXT fails closed. Reference lookup
   occurs before global FAXT resolution.
7. UNKNOWN, currentness and evidence references are returned unchanged.

## Requirements

- **FR-001**: Give FAXT a distinct string-backed `FaxtId` identity type.
- **FR-002**: Model the contextual reference as an immutable `(XeedId,
  FaxtId)` pair with no copied FAXT state or invented metadata.
- **FR-003**: Provide an application reader that accepts only `AuthorizedXeed`
  and a FAXT identity.
- **FR-004**: Check the exact Xeed reference before resolving global FAXT.
- **FR-005**: Fail closed for invalid IDs, missing reference and missing FAXT.
- **FR-006**: Keep deterministic in-memory reference support in test fixtures
  only; do not implement a production writer or persistence.
- **FR-007**: Preserve FAXT identity, epistemic state, currentness and evidence
  references when released through a contextual read.
- **FR-008**: Keep all non-FAXT object types unsupported at this boundary.
- **FR-009**: Document temporal/provenance/lifecycle limits and all
  unimplemented capabilities.

## Out of scope

Production storage or writer, migrations, auth providers, APIs, RLS,
Subscriber, AXIGLAND projection, Context Broker, HFX-01, non-FAXT binding,
provenance trace, binding timestamps/lifecycle history, UI, Jev, TypeSafe,
OpenAI, models, external services and dependencies.

## Failure conditions

Stop implementation if the code requires copying FAXT state, treating a
reference as provenance or epistemic evidence, bypassing `AuthorizedXeed`,
adding production persistence/writing, or supporting another knowledge type.

## Validation and acceptance

Deterministic tests cover authorized read, same-Tenant/different-Xeed
isolation, cross-Tenant denial, shared global FAXT identity, raw-ID denial,
enumeration, missing FAXT/reference, type identity, label independence,
UNKNOWN/currentness/provenance preservation, Xeed-germination-state non-authority,
and lookup ordering. Repository gates are required before commit/PR; no merge
is authorized.
