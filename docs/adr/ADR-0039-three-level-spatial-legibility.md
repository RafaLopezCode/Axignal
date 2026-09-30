# ADR-0039 — Three-Level Spatial Legibility

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§9, 25, 26, 46, 55; ADR-0016, ADR-0035, ADR-0037.

## Context

AXIGLAND already had camera zoom, collision-aware labels and relationship
rendering, but visual density was governed by one overview threshold while all
available synthetic relationships remained drawable at every scale. That made
zoom a geometric operation rather than a cognitive one.

FR-13 establishes semantic zoom without inventing graph structure that AXIGNAL
does not know.

## Decision

The subscriber field has three deterministic spatial scales:

### WORLD

WORLD is orientation, not inspection.

- all governed objects remain present as marks;
- organization and current focus retain label priority;
- other labels are semantically suppressed before collision layout;
- relationship lines are not rendered;
- zone/cardinal orientation remains strongest;
- Fit/Reset targets WORLD.
### NEIGHBORHOOD

NEIGHBORHOOD answers "what is around the current focus?"

- focus and organization retain first priority;
- directly connected objects gain label priority;
- only direct focus relationships are rendered;
- relationship rendering has a deterministic budget of six;
- focusing an object targets this scale.

### RELATION / PROOF

RELATION/PROOF supports close inspection without expanding into an everything
graph.

- all labels become semantically eligible, while collision/off-screen
  decluttering still applies;
- direct focus relationships are selected first;
- one-hop context may be added after direct relationships;
- visual relationship budget is twelve;
- non-focus context edges remain attenuated;
- the underlying dense fixture may contain more relationships than are rendered.

The thresholds are versioned UI policy:

- WORLD: zoom < 0.84;
- NEIGHBORHOOD: 0.84 <= zoom < 1.55;
- RELATION/PROOF: zoom >= 1.55.
## Aggregation rule

AXIGNAL MUST NOT fabricate semantic clusters merely to simplify the picture.
Without governed grouping metadata, WORLD aggregates visually by preserving
marks while suppressing labels and edges. The world remains reversible and no
new domain entity or relationship is created.

VISUAL_AGGREGATION != CANONICAL_CLUSTER

## Accessibility and non-hover path

Every graph node remains a native keyboard-focusable button with an accessible
name at every scale. Keyboard focus always reveals its label and restores
contrast even when semantic decluttering hid that label.

The existing relationship list remains independent of visual edge budgets. A
user can therefore inspect and enter a focus relationship from the list even
when WORLD renders zero relationship lines. FR-15 still owns the complete
non-graph projection; FR-13 does not claim to finish that larger accessibility
slice.

A live spatial status announces current scale plus visible label/relation
counts and is bound to the AXIGLAND field through aria-describedby.

## Invariants
SEMANTIC_ZOOM != GEOMETRIC_ZOOM_ONLY

WORLD != EVERYTHING_VISIBLE

RELATION_PROOF != DRAW_EVERY_EDGE

VISUAL_EDGE_BUDGET != RELATIONSHIP_DELETION

HIDDEN_LABEL != HIDDEN_OBJECT

KEYBOARD_FOCUS_REVEALS_LABEL

VISUAL_AGGREGATION != CANONICAL_CLUSTER

## Consequences

Large/dense projections remain navigable without giving every label and edge
equal authority. Zoom now changes information density, not merely pixel scale.
Relationship data is never deleted by visual budgets, and direct keyboard/list
navigation remains available.

FR-14 remains responsible for the final motion/input contract. FR-15 remains
responsible for a complete accessible non-graph representation.

## Non-goals

No canonical clustering model, new relationship type, graph database, layout
engine, persistence, provider behavior, production deployment or mobile
projection is introduced by this ADR.
