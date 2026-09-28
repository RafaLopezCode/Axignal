# P0-HFX-01 — Minimum Truthful AXIGLAND

**Status:** CTO-authorized implementation; local/test-dev projection only
**Authority:** MASTER §55; Constitution; ADR-0003, ADR-0005, ADR-0009, ADR-0016–0021; P0-CORE-05; HFX-00 integration matrix
**Golden Master:** `D:\AXIGNAL\UX DEEPSEEK`, read-only, Manifest V1

## Goal

Integrate the existing Golden Master experience with the minimum truthful
subscriber projection available through the established application contracts:

`TrustedRequestContext (test/dev) → AuthorizedXeed → Authorized Organization
context + authorized FAXT collection → immutable Subscriber Projection →
AXIGLAND presentation and session navigation`.

The delivered browser flow is explicitly a deterministic test/dev in-memory
demonstration, not production authentication, persistence, or live AXIGLAND
data. The single canonical Organization and each global FAXT remain unchanged.

## Supported projection

- The root is the original global Organization obtained only through
  `AuthorizedXeedOrganizationReader`.
- FAXT nodes are original global objects returned by
  `AuthorizedXeedFaxtCollectionReader`; only explicit references for the same
  AuthorizedXeed appear.
- The projection carries canonical IDs and direct fields unchanged. Subject
  kind/resolution, semantic relationships, FAXT cardinal assignment, Evidence
  rights/content, provenance, and historical state remain
  `UNKNOWN_UNSUPPORTED` or unavailable.
- No semantic graph lines are rendered. The dotted boundary is presentation
  containment for the active Xeed context; it is not Organization ownership,
  subject identity, provenance, relevance, or ranking. The serialized
  membership pairs retain the canonical XeedId → FaxtId endpoints.
- Positions, camera, selection, depth, minimap, and session Focus History are
  presentation state. They do not alter canonical records.
- AXENT integration is limited to updating the selected canonical identity
  context; no prompt, transcript, model/provider, reasoning, or write path is
  included.
- Unsupported Evidence, provenance, relationship, and historical controls
  remain disabled or state their limitation.

## Failure and empty states

Missing/invalid authorization, missing Organization, malformed/dangling FAXT
reference, mismatched identity, or projection failure release no partial data.
External failure text must not distinguish unknown from cross-Tenant Xeed.
An empty authorized collection means only that this Xeed has zero explicit
FAXT references in this test/dev authority; it does not assert world-level
absence.

## Golden Master and scope

The external Golden Master is an executable visual/behavioral authority and is
read-only. Preserve its overall shell, hierarchy, proportions, graph field,
focus behavior, Bottom Context, AXENT rail, Focus Trail, minimap, motion, and
responsive behavior. Add only truthful labels/disabled states and required
test/dev reality disclosure. Do not copy its fixture knowledge into the
projection. Do not modify any Manifest V1 input.

No production auth, persistence, API, AXENT broker/reasoning, Evidence
dereference, provenance, semantic Relationship reader, historical graph,
database, migration, provider, dependency, or deployment is included.

## Acceptance

1. Projection accepts only one AuthorizedXeedOrganization and a tuple of
   AuthorizedXeedFaxt values belonging to that exact authorized context.
2. Organization and FAXT canonical identity/data are preserved; no subject ID
   cast, semantic edge, cardinal mapping, provenance, or evidence disclosure is
   invented.
3. Empty/error cases fail closed and do not reveal cross-Tenant existence.
4. The local browser demo is assembled through real domain/application
   contracts using test/dev in-memory authorities, and visibly discloses that
   reality level.
5. Selection updates the protagonist, supported Bottom Context, AXENT active
   identity context, session Focus History, and minimap/camera only.
6. Back/Forward/Home and branching history are deterministic; pan/zoom and
   cognitive depth do not change canonical data. Timeline/provenance/evidence
   affordances cannot fabricate unsupported results.
7. Keyboard operation, reduced motion, errors, empty results, unknown fields,
   and a narrow viewport are covered.
8. Golden Master Manifest V1 verifies before/after with the authorized digest.
9. Deterministic local gates, browser E2E, Graphify, build, scope, secret
   safety, and self-audit pass before remote delivery.
10. Exactly one PR is opened against `main`; it remains unmerged and awaits CTO
    review and human visual acceptance.

## Readiness

This slice may begin because existing AuthorizedXeed, Organization, and FAXT
collection contracts provide enough canonical data for the minimum vertical
slice. FAXT subject semantics, semantic Relationships, cardinal assignment,
Evidence rights/provenance and historical reconstruction are explicitly not
required to render supported identities/context plus truthful unknown states.
P0-HFX-01 must not promote any of those remaining UNKNOWN boundaries.
