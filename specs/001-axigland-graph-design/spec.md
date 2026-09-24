# Feature Specification: AXIGLAND Graph Architecture and Design Governance

**Feature Branch**: `feature/axignal-graph-design`
**Created**: 2026-09-25
**Status**: Implemented for CTO review
**Input**: P0-GRAPH-02 accepted architecture and AXIGNAL-specific graph design skill.

## User Scenarios & Testing

### User Story 1 — Governed graph implementation guidance (P1)

An implementation agent designing an AXIGLAND graph surface needs AXIGNAL-
specific cartographic rules so that the map remains economically meaningful,
evidence-backed, temporal, and accessible.

**Independent Test**: Read the skill entrypoint and relevant references; confirm
the rules align with ADR-0009 and keep canonical semantics separate from visual
projection.

**Acceptance Scenarios**

1. Given graph UI, projection, grammar, or renderer work, when the skill applies,
   then it routes the agent to focused AXIGLAND references and preserves the
   authority hierarchy.
2. Given a surprising or potential relationship, when designed for inspection,
   then observed/potential/unknown distinctions and evidence lineage remain
   visible and review does not grant edit authority.

### User Story 2 — Replaceable renderer boundary (P1)

An architect needs the accepted renderer choice documented without making the
vendor's types or data model canonical.

**Independent Test**: Contract tests verify ADR-0009 acceptance, replaceability,
and absence of renderer dependencies/imports in canonical runtime layers.

**Acceptance Scenarios**

1. Given Sigma + Graphology as the initial implementation, when architecture is
   inspected, then AXIGNAL remains the semantic cartography owner and the
   renderer remains replaceable behind its contract.
2. Given canonical domain, cognition, or pipeline modules, when inspected, then
   no Sigma/Graphology implementation types or imports have leaked there.

### User Story 3 — Evidence-aware visual decisions (P2)

A design agent needs to distinguish bakeoff measurements from future product
targets and retain known evidence gaps.

**Independent Test**: Read performance, accessibility, label, and visual
validation references; check that none assert unmeasured properties.

**Acceptance Scenarios**

1. Given historical bakeoff data, when proposing a product budget, then measured
   results and future targets are explicitly separate.
2. Given accessibility or label design, when no empirical validation exists,
   then it is recorded as an open validation requirement.

## Edge Cases

- An unexpected cluster or tie may reflect real public signals rather than an
  AXIGNAL defect; design must expose provenance instead of silently hiding it.
- Unknown currentness or an unknown relationship state must not be presented as
  false or ended.
- A PATHX with multiple edges must not appear to be a direct endpoint tie.
- A renderer may support more nodes than the semantic projection should expose.

## Requirements

- **FR-001**: ADR-0009 MUST state ACCEPTED and define AXIGNAL-owned semantics,
  replaceable adapter, renderer-local mechanics, and no-leak boundary.
- **FR-002**: The project-local `axignal-graph-design` skill MUST be discovered
  under `.opencode/skills/` and cover all required cartographic topics.
- **FR-003**: Visual guidance MUST preserve epistemic, temporal, relationship,
  corporate, PATHX, and evidence distinctions.
- **FR-004**: Guidance MUST keep request-review separate from edit authority.
- **FR-005**: Bakeoff measurements MUST remain distinguished from product targets
  and current reproducibility.
- **FR-006**: Deterministic tests MUST protect ADR status, skill resources,
  forbidden production dependencies, and canonical-layer import boundaries.
- **FR-007**: This feature MUST NOT implement a renderer runtime, graph UI,
  semantic LOD runtime, graph algorithms, or production renderer dependency.

## Key Concepts

- **Canonical AXIGLAND**: The one economic world; not a renderer graph.
- **Cartographic projection**: An AXIGNAL-owned, purpose-specific presentation
  of canonical meaning.
- **Renderer adapter**: Replaceable mechanical drawing implementation.
- **Evidence trace**: Persisted derivation, FAXTs, evidence, source lineage, and
  temporal/currentness context.

## Success Criteria

- **SC-001**: ADR-0009 and design governance report the accepted architecture
  and its implementation limits consistently.
- **SC-002**: All 17 required references are linked by the skill and exist.
- **SC-003**: Deterministic contract tests prevent prohibited dependency/import
  coupling without network access.
- **SC-004**: The skill and docs make accessibility, labels, and product budgets
  explicit future validation work where empirical evidence is absent.

## Assumptions and Boundaries

- CTO acceptance is authoritative and does not require reconsidering bakeoff
  candidates.
- No product graph UI, production renderer package, or runtime contract is in
  scope.
- The new P0-GRAPH-02 branch will be submitted as a PR but will not be merged.
