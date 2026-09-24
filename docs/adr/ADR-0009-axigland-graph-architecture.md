# ADR-0009: AXIGLAND Graph Architecture (PROPOSED)

- **Status:** **PROPOSED — NOT ACCEPTED.** CTO authorization is required before
  this becomes architectural doctrine.
- **Date:** 2026-09-24
- **Source doctrine:** MASTER §3, §8, §16–§18, §20, §24–§26, §46.28, §46.40;
  Engineering Constitution "Model Provider Abstraction", "Architectural
  Constraints".
- **Evidence:** `docs/research/AXIGLAND_GRAPH_ENGINE_BAKEOFF.md`,
  `docs/research/AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md`,
  `experiments/graph-engine-bakeoff/` (raw `results/*.json`, screenshots).

## Context

AXIGLAND is a first-class product surface: a living, temporal, evidence-driven
economic world that must express observed/potential/historical distinctions,
PATHX trajectories, and semantic levels of detail. The renderer choice must not
capture canonical semantics (renderer replaceability, analogous to the model
provider doctrine) and must survive large graphs and continuous materialization.
A bakeoff measured the mandatory candidates (cosmos.gl, G6, Sigma, Cytoscape)
and documented Ogma as a commercial reference.

## Decision (proposed)

1. **AXIGNAL owns the semantic/cartographic layer.** Canonical meaning
   (epistemic grammar, semantic LOD, temporal projection, PATHX state, filters,
   projection, materialization) lives in AXIGNAL, never in vendor objects.
2. **Renderer is a replaceable adapter** behind an AXIGNAL Graph Controller.
3. **Preferred provisional renderer: Sigma.js v3 + Graphology (MIT).**
   Graphology is an in-memory structure/algorithm host behind the adapter, not
   semantic authority.
4. **Reject** cosmos.gl as a foundation (CC-BY-NC-4.0; non-public core) and Ogma
   (not publicly installable). **Reject** G6 as the cartography foundation
   (large-graph failure). **Retain** Cytoscape only as an algorithm/reference
   control.
5. No production dependency is added by this ADR; a separate authorized slice
   introduces it.

## Consequences

- The renderer can be swapped (e.g., to a future WebGPU engine) without
  rewriting semantics.
- AXIGNAL must build: semantic LOD projector, epistemic grammar, temporal
  projection, PATHX state, accessible complement, label strategy.
- A future `axignal-graph-design` skill is derived from this decision + doctrine
  + benchmark evidence (not created yet).

## Status / governance

**PROPOSED, NOT ACCEPTED.** Until the CTO accepts it, the graph architecture is
not doctrine and no production graph dependency may be introduced. The licensed
constraint (no CC-BY-NC in production) is a hard legal gate independent of
acceptance.

## Evidence gaps

See bakeoff §23 (LOD end-to-end, empirical a11y, React/Next, labels, WebGPU,
layout quality, G6 WebGL).
