# ADR-0009: AXIGLAND Graph Architecture

- **Status:** **ACCEPTED.** Accepted by the CTO for the governed P0-GRAPH-02
  architecture slice; this accepts architecture and design governance only,
  not runtime implementation.
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

## Decision

The accepted architecture is **HYBRID**, with **no foundation framework**.
AXIGNAL owns economic meaning and cartographic projection. Sigma.js with
Graphology is the initial implementation choice only, behind an AXIGNAL-owned,
replaceable renderer contract.

```text
Canonical AXIGLAND
        ↓
AXIGNAL graph projection
        ↓
AXIGNAL semantic cartography
        ↓
AXIGNAL renderer contract
        ↓
Replaceable renderer adapter
        ↓
Initial implementation: Sigma + Graphology
```

AXIGNAL owns semantic LOD, economic hierarchy, graph projection, epistemic and
temporal visual grammar, relationship and PATHX semantics, corporate and
hierarchical semantics, clustering, focus/recenter, progressive materialization,
label policy, accessibility projection and complement, representation-anomaly
semantics, and evidence inspection/provenance semantics.

The renderer owns mechanical concerns only: GPU buffers, primitive drawing,
low-level camera mechanics, hit testing, render scheduling, and other
renderer-local mechanics. **No renderer types may exist above the renderer
adapter boundary.** Sigma and Graphology types are not canonical domain truth
and must not enter canonical entities, Evidence, FAXTs, INXIGHTs, PATHXs,
Knowledge Frontier, cognition, JEV state, temporal authority, source
acquisition, entity resolution, claim review, or representation-anomaly
authority. Graphology may serve as an in-memory substrate behind the boundary.

The future contract consumes an AXIGNAL-owned cartographic projection. Its exact
schema is intentionally not frozen by this ADR. This ADR adds no production
renderer dependency and implements no renderer runtime, graph UI, or graph
algorithm.

The P0-GRAPH-01 bakeoff decision is accepted without reopening its selection.
Cosmos remains historical bakeoff evidence only: it is absent from the current
harness and blocked from production by CC-BY-NC-4.0. Historical results are not
represented as currently reproducible.

## Alternatives considered

- **Framework-first graph semantics (G6):** rejected as the architecture
  foundation based on the bakeoff's large-graph failure and the risk of coupling
  semantic behavior to vendor objects.
- **Cosmos as the renderer foundation:** rejected for production because its
  CC-BY-NC-4.0 license is incompatible; its measurements remain historical only.
- **Cytoscape as the primary cartography layer:** not selected as the initial
  renderer implementation based on the measured scale/performance evidence.
- **A custom framework or no renderer decision:** no foundation framework is
  selected; Sigma + Graphology is the initial, replaceable adapter choice.

## Tradeoffs

AXIGNAL must own and validate semantic LOD, evidence/temporal grammar,
accessibility, labels, provenance, and progressive transitions instead of
receiving those product semantics from a renderer. This increases AXIGNAL's
implementation responsibility but preserves canonical boundaries and
replaceability. Sigma's in-memory substrate and WebGL implementation remain
replaceable concerns; benchmark measurements do not establish product budgets
or empirical accessibility.

## Consequences

- Renderer replacement must not rewrite canonical meaning or AXIGNAL-owned
  cartographic semantics.
- `.opencode/skills/axignal-graph-design/` defines implementation guidance;
  it does not implement those semantics.
- Accessibility, labels, full semantic LOD, temporal reconstruction, and
  end-to-end product behavior remain future validation and implementation work.

## Status / governance

This ADR is accepted architecture doctrine. It does not authorize production
dependencies, graph UI, runtime contract/adapter, or deployment. The licensed
constraint (no CC-BY-NC in production) remains a hard legal gate.

## Evidence gaps

See bakeoff §23 (LOD end-to-end, empirical a11y, React/Next, labels, WebGPU,
layout quality, G6 WebGL).
