# ADR-0041 — Accessible Non-Graph Projection

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 25, 26, 46, 55; ADR-0035, ADR-0039, ADR-0040.

## Context

AXIGLAND is spatial by design, but graph geometry, color and pointer precision
cannot be the only route to governed meaning. FR-13 and FR-14 made the canvas
legible and controllable; FR-15 establishes a parallel semantic projection
that can be traversed without reading graph position or edge drawing.

The canonical subscriber projection currently exposes FAXT state, currentness
and observation time, while canonical semantic edges and direct evidence
access may remain unsupported. The accessible projection must preserve that
truth rather than fabricate missing relationships or evidence.

## Decision

The subscriber reader includes a visible non-graph region generated from the
same current projection and focus.

It provides:

- an ordered focus path/breadcrumb;
- current focus name;
- textual epistemic state;
- textual currentness and observation time where available;
- a hierarchical/list relationship view for every relationship currently
  exposed by the same presentation projection;
- keyboard-operable navigation to related items without recentering the
  canvas;
- a truthful evidence action that exposes available evidence context or states
  that evidence access is not exposed by the projection;
- semantic headings, lists and definition lists suitable for accessibility
  APIs.

## Relationship equivalence

The non-graph relationship list is independent of visual edge budgets and
semantic zoom. WORLD may render zero edges while the list still exposes every
relationship available from the current focus.

FR-15 does not grant canonical authority to synthetic UX-lab edges. In the
current lab they remain explicitly synthetic presentation fixtures. If the
canonical runtime exposes governed relationships later, the same semantic
projection must consume those governed relationships rather than infer them.

VISUAL_EDGE_VISIBILITY != RELATIONSHIP_AVAILABILITY

NON_GRAPH_VIEW != SECOND_TRUTH_MODEL

## Evidence boundary

Internal projection enums are not subscriber language. When evidence access is
unsupported, the UI says that evidence access is not exposed by this
projection. It does not display internal enum values or fabricate provenance.

EVIDENCE_ACTION != FABRICATED_EVIDENCE

INTERNAL_STATUS != SUBSCRIBER_COPY

## Accessibility

Every relationship action is a native button. Activating a non-graph
relationship keeps navigation in the reader path, does not require camera
movement, rebuilds the semantic projection for the new focus and restores
focus to its heading.

Critical epistemic and relationship state is written as text. Color may
supplement that state but is never the only carrier.

The projection remains visible under narrow reflow used to review 200% and
400% browser zoom equivalents. At <=680 CSS px the legacy compact connection
strip is hidden to avoid duplicate relationship surfaces and horizontal
overflow; the semantic projection remains available and reflows to one column.

## Invariants

GRAPH_POSITION != REQUIRED_MEANING

COLOR != SOLE_EPISTEMIC_STATE

NON_GRAPH_NAVIGATION != CAMERA_DEPENDENCE

VISUAL_EDGE_BUDGET != NON_GRAPH_RELATIONSHIP_BUDGET

EVIDENCE_UNAVAILABLE != EVIDENCE_FALSE

UNKNOWN != FALSE

## Consequences

A keyboard or screen-reader user can traverse focus relationships, inspect
epistemic/temporal state and invoke the evidence boundary without using graph
geometry, hover or color.

FR-16 remains responsible for the product-level mobile value subset; FR-15
only ensures the governed non-graph path survives narrow zoom/reflow.

## Non-goals

This ADR does not create canonical semantic relationships, new evidence
authority, a screen-reader-specific data model, mobile product scope,
persistence, provider behavior or production deployment.
