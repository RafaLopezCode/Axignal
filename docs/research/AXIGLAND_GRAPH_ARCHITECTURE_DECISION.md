# AXIGLAND Graph Architecture Decision

- **Status:** CTO accepted in ADR-0009. Research evidence remains historical;
  architecture acceptance does not authorize runtime implementation.
- **Date:** 2026-09-24
- **Evidence:** [`AXIGLAND_GRAPH_ENGINE_BAKEOFF.md`](AXIGLAND_GRAPH_ENGINE_BAKEOFF.md)

```
ARCHITECTURE_DECISION=HYBRID
FOUNDATION_FRAMEWORK=NONE
INITIAL_RENDERER=sigma + graphology   # replaceable adapter implementation
SEMANTIC_LAYER_OWNED_BY_AXIGNAL=YES
```

## What "HYBRID" means here, precisely

AXIGNAL owns the **semantic/cartographic layer**. The renderer is a replaceable
adapter. The hybrid element is narrow and intentional: Graphology is used as an
in-memory graph structure and algorithm host **behind the adapter**, but it is
**not** the semantic authority and **not** a canonical model. Canonical meaning
lives in AXIGLAND projections that AXIGNAL owns.

```
AXIGLAND (canonical, demand-materialized, temporal, evidence-driven)
        │  AXIGNAL projection (LOD, epistemic grammar, temporal, PATHX, filter)
        ▼
AXIGNAL Graph Model + Controller        ← AXIGNAL-owned semantics (the moat)
        ▼
Renderer Adapter (sigma | future WebGPU engine)
        ├── graphology (in-memory structure/algorithms; replaceable)
        └── Sigma.js WebGL renderer (buffers, drawing, camera, hit-testing)
```

### AXIGNAL-owned (semantic)
Semantic LOD (WORLD→EVIDENCE), epistemic visual grammar
(OBSERVED/POTENTIAL/HISTORICAL + STALE/UNKNOWN), temporal projection, PATHX
state, selection/recenter/focus, filter/cluster/graph-distance projection,
incremental materialization, label strategy, accessibility complement.

### Renderer-owned (mechanical)
GPU buffers, drawing, camera, hit testing, low-level interaction, render
scheduling.

## Why not the alternatives

- **Framework-first (Hypothesis A):** G6 v5 — the strongest framework-first
  candidate — failed at 10k/50k (RangeError + main-thread lockup) with its
  default renderer, and its item model invites vendor-semantic coupling.
  Cytoscape is stable only to small scale (≈11 s first render at 50k/250k).
- **cosmos.gl as the GPU foundation:** **CC-BY-NC-4.0** (NonCommercial) with a
  non-public core repository → `LICENSE_FIT=BLOCKED`. It remains the reference
  for the GPU-renderer *ceiling* (first render 150 ms @ 10k/50k; 1.5 s @
  100k/500k) but cannot be adopted.
- **Ogma:** not publicly installable → executable benchmark blocked; used only to
  enumerate requirements a mature product bundles.

## Why Sigma (initial implementation choice)

Among adoptable (MIT) candidates it is the only one that:
- recorded an idle P95 of 16.8 ms at stress in the benchmark harness (first
  render 3.7 s; heap ~600 MB); these are fixture- and environment-specific
  measurements, not product guarantees;
- showed useful recenter (7 ms) and PATHX highlight (40 ms) timings in the
  historical medium scenario; the filter and temporal timings came from the
  pre-repair harness and are not treated as validated facts. The nominal
  +20,000 expansion request had only 3,900 pending nodes on Sigma's final
  medium-fixture addition, so 190 ms does not measure 20,000 new nodes in that
  single call;
- exposes node/edge reducers and custom WebGL programs (a high ceiling for a
  distinctive AXIGLAND grammar) with a small, well-typed interface;
- keeps Graphology (MIT) as an explicitly replaceable substrate behind an
  adapter, preserving renderer replaceability.

## Decision gates (Section 19) — pass/fail

| Gate | cosmos | G6 | Sigma | Cytoscape |
| --- | --- | --- | --- | --- |
| LICENSE_FIT | BLOCKED | PASS | PASS | PASS |
| Represent required semantic grammar | PASS* | PASS | PASS | PASS |
| Dynamic materialization without full rebuild at realistic scale | PASS | FAIL | PASS | FAIL (≥large) |
| No forced vendor-object semantics | PASS (low-level) | WEAK | PASS | WEAK |
| Supplies AXIGNAL-required accessibility architecture | NOT ESTABLISHED | NOT ESTABLISHED | NOT ESTABLISHED | NOT ESTABLISHED |

No tested renderer establishes AXIGNAL's required accessibility architecture;
the accessible complement is an AXIGNAL-owned design and validation requirement.

## Scope note

This decision does **not** add a production graph dependency, implement UI, or
freeze unvalidated visual mappings. The AXIGNAL-specific
`.opencode/skills/axignal-graph-design/` skill records design guidance and
validation requirements; it does not implement runtime behavior.

## Evidence gaps (do not overstate)

Semantic LOD end-to-end, empirical accessibility, empirical React 19 / Next 16
integration, label strategy at scale, WebGPU alternatives, layout quality, and
G6-with-WebGL remain unproven. See bakeoff §23.
