# AXIGLAND Graph Engine Bakeoff (P0-GRAPH-01)

- **Status:** Research report. Evidence-driven. No production decision is final here.
- **Date:** 2026-09-24
- **Baseline:** `main` @ `90e588ecc2f26782bbeeaf5b23fe545cdb3955e1`
- **Branch:** `experiment/axigland-graph-engine-bakeoff`
- **Experiment:** `experiments/graph-engine-bakeoff/`
- **Doctrine:** subordinate to the MASTER
  (`../product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`) and the Engineering
  Constitution. See `../design/DESIGN_GOVERNANCE.md`.

> A fast hairball is still a hairball. This bakeoff evaluates whether an engine
> can host AXIGNAL's *economic cartography*, not merely draw many points.

---

## 1. Executive summary

- Two of the five mandatory candidates are **license-gated for commercial
  AXIGNAL**: `@cosmograph/cosmos` (cosmos.gl) is **CC-BY-NC-4.0** with a
  **non-public core repository**, and **Ogma** is not publicly installable
  (private npm). Both are therefore ineligible as foundations.
- Among the adoptable (MIT) candidates, **Sigma.js v3 + Graphology** is the only
  one that holds interactive frame budgets and dynamic mutation at
  **100,000 nodes / 500,000 edges**, while exposing enough low-level control
  (node/edge reducers, WebGL programs, camera) for AXIGNAL to own semantics.
- **G6 v5** fails hard at medium scale with its default renderer (RangeError /
  main-thread lockup at 10k/50k). **Cytoscape.js** is stable to small scale but
  becomes unusable at large (≈11 s first render, ≈0.3 fps idle at 50k/250k).
- The evidence supports **Hypothesis B/C**, not **Hypothesis A**: an
  **AXIGNAL-owned semantic/cartographic layer** over a **renderer adapter**,
  with a hybrid element (Graphology as a *replaceable* in-memory structure, never
  as semantic authority). Framework-first (G6) is rejected on large-graph
  failure; cosmos is rejected on license; Ogma informs missing requirements only.
- Accepted architecture (ADR-0009): **AXIGNAL cartography layer + replaceable
  renderer adapter; initial renderer = Sigma.js v3 + Graphology**. The decision
  does not authorize runtime implementation. See
  [`AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md`](AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md)
  and the accepted `../adr/ADR-0009-axigland-graph-architecture.md`.

---

## 2. AXIGNAL requirements (derived, not invented)

From the MASTER: one canonical AXIGLAND (§3, §8), observed ≠ potential (§16),
FAXT ≠ INXIGHT ≠ PATHX (§17–§18), temporality on edges (§20), semantic visual
grammar (§25), semantic LOD WORLD→EVIDENCE (§25.2), truthful FIRST_MAP (§9),
infrastructure invisible to users (§26, §46.40), and provider/engine
replaceability by analogy with the model abstraction doctrine (§13, §46.28).

Concrete engineering requirements tested here:

1. **Large-graph headroom** ≥ 10k/50k comfortable; target ≥ 50k/250k.
2. **Dynamic materialization** without destructive full rebuild at realistic
   scales (MASTER §8 demand-materialized graph).
3. **Epistemic edge grammar**: OBSERVED / POTENTIAL / HISTORICAL (+ STALE /
   UNKNOWN currentness) simultaneously.
4. **PATHX** highlighting over a large context; cheap clear; interactive change.
5. **Temporal** transition/T1–T2 with cognitive continuity.
6. **Semantic LOD** architecture (not just geometric zoom).
7. **Visual extensibility** sufficient to invent a distinctive grammar.
8. **Accessibility** complement (canvas is never sufficient alone).
9. **React 19 / Next 16** integration without forcing graph state into React.
10. **Semantic ownership**: canonical meaning must not live in vendor objects.

---

## 3. Candidate reconnaissance (as of 2026-09-24)

| Candidate | Version | License | Latest release | Backend | Notes |
| --- | --- | --- | --- | --- | --- |
| cosmos.gl (`@cosmograph/cosmos`) | 3.4.1 | **CC-BY-NC-4.0** | 2026-08-24 | WebGL (luma.gl), GPU simulation | Core repo `cosmograph-org/cosmograph` is **404/private**; org exposes only integrations/issues. Non-commercial. |
| AntV G6 | 5.1.1 | MIT | 2026-09-21 | Canvas default (WebGL/WebGPU via plugins) | High-level framework, layouts/behaviors/plugins. |
| Sigma.js | 3.0.3 (stable); 4.0.0-beta.6 (pre) | MIT | 2026-09-16 | WebGL | Renderer + Graphology data/algorithm ecosystem. |
| Graphology | 0.26.0 | MIT | 2025-01-26 | n/a (data/algorithms) | In-memory graph + community layouts/algorithms. |
| Cytoscape.js | 3.34.3 | MIT | 2026-09-07 | Canvas (WebGL renderer exists separately) | Mature algorithms, control candidate. |
| Ogma (`@linkurious/ogma`) | — | Commercial | — | WebGL/canvas | **Not on public npm** → `OGMA_EXECUTABLE_BENCHMARK=BLOCKED`; doc-only reference. |
| Reference-only explored | reagraph 4.32.0 (Apache-2.0), force-graph 1.51.4 (MIT), 3d-force-graph 1.80.0 (MIT) | mixed | 2026 | WebGL/Canvas | Not stronger than Sigma/cosmos for this requirement; not benchmarked. |

No clearly superior, maintained **WebGPU graph renderer** surfaced as of the
research date (searches returned nothing adoptable); cosmos remains the main
GPU force-graph, blocked by license.

---

## 4. License analysis

| Candidate | Core | Integration | Commercial use | SaaS | Attribution | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| cosmos.gl | CC-BY-NC-4.0 | luma.gl (MIT) | **No** | **No** | Required | `LICENSE_FIT=BLOCKED` |
| G6 | MIT | @antv/* (MIT) | Yes | Yes | Notice | `LICENSE_FIT=PASS` |
| Sigma | MIT | Graphology (MIT) | Yes | Yes | Notice | `LICENSE_FIT=PASS` |
| Graphology | MIT | — | Yes | Yes | Notice | `LICENSE_FIT=PASS` |
| Cytoscape | MIT | plugins vary | Yes | Yes | Notice | `LICENSE_FIT=PASS` |
| Ogma | Commercial | — | Paid license required | Per contract | Per contract | `LICENSE_FIT=BLOCKED` (not installed) |

The cosmos npm tarball ships the full CC-BY-NC-4.0 text and `"license":
"CC-BY-NC-4.0"` in `package.json`; NonCommercial explicitly forbids "commercial
advantage or monetary compensation". AXIGNAL is a commercial product, so cosmos
cannot be a foundation (Section 19 gate). It was still **measured** (license
permits non-commercial evaluation) to characterise the GPU-renderer ceiling, and
is marked reference-only in the adapter.

---

## 5. Benchmark methodology

- **Isolation:** all candidate dependencies live under
  `experiments/graph-engine-bakeoff/` (not AXIGNAL production deps); removable.
- **Neutral model:** `experiments/graph-engine-bakeoff/model/model.mjs`. Every
  engine consumes the **same** fixtures through adapter modules
  (`app/adapters/*.js`). No engine gets a favourable data model.
- **Deterministic fixtures:** `fixtures/generate.mjs` (seeded mulberry32,
  `SEED=20260924`). Positions are precomputed so rendering throughput is compared
  independently of layout. Hashes in `fixtures/manifest.json`.
- **Harness:** Vite dev server (programmatic, `benchmark/lib.mjs`), Playwright
  driving **system Chrome** (`channel: 'chrome'`), real GPU (no SwiftShader).
- **Measurement:** `app/instrumentation.js` — `performance.now()` marks and
  `requestAnimationFrame` frame sampling. Metrics: data fetch/parse, graph init,
  first render, time-to-interactive, idle frames, wheel pan/zoom frames, heap,
  and per-scenario operations.
- **Raw results:** `results/perf.json`, `results/scenarios.json`,
  `results/environment.json`. Screenshots: `screenshots/*.jpg`.
- **Reproduction:** `experiments/graph-engine-bakeoff/README.md`.

### Caveats

- Single machine; results are **relative**, not absolute.
- The G6 adapter uses G6's default (canvas) renderer with custom stateful edges;
  its medium failure is both an engine and a configuration result (documented).
- cosmos node positions were not pinned (`enableSimulation: true`), so its
  screenshots look collapsed; perf numbers remain valid API measurements.

---

## 6. Hardware / software environment

```
OS        win32 x64 (10.0.26200)
CPU       Intel Core i5-10400F (6c/12t, 2.90GHz)
RAM       16 GB
GPU       NVIDIA GeForce GTX 1650 (4 GB), driver 32.0.15.9186
Browser   Chrome 153.0.8010.53 (Playwright, headed-capable headless=new)
WebGL     WebGL 2.0; ANGLE (NVIDIA ... D3D11 vs_5_0 ps_5_0)   # real GPU
Node      v24.14.1 / npm 11.9.0
Viewport  1440x900, DPR 1
Fixture seed  20260924
```

---

## 7. Fixture definitions

Deterministic topologies (identical semantics across engines): neighbourhood,
corporate, supply, clustered, hairball, temporal. Scales: tiny 100/500, small
1,000/5,000, medium 10,000/50,000, large 50,000/250,000, stress 100,000/500,000.

Clustered-fixture SHA-256 (full manifest in `experiments/graph-engine-bakeoff/fixtures/manifest.json`):

| Scale | Nodes/edges | SHA-256 |
| --- | --- | --- |
| tiny | 100 / 500 | `28a50c796cd597f3d60be19eb45ee0006c5e5357d91bbc31a9621fff4429c72c` |
| small | 1,000 / 5,000 | `f9fd339026ab29fa96f17c67514cd61508fafe4219963db3c2a7b9c4893e061a` |
| medium | 10,000 / 50,000 | `7cfc2560e8acb50ff82e5af613fb85e0cc4aff9299ea030bcda634444131696e` |
| large | 50,000 / 250,000 | `76d03da64dac521ad6aae9261204f1494c19747068024b2d3c9e7a0c9d37c10c` |
| stress | 100,000 / 500,000 | `16cf1ba72712395295980a8f5a474a278288d72d9c92607f9d7613371c063f7d` |

Edge fields: `nature`, `epistemicClass` (OBSERVED/POTENTIAL/HISTORICAL),
`currentness` (CURRENTLY_OBSERVED/HISTORICAL/STALE/UNKNOWN_CURRENTNESS),
`materiality`, `evidenceStrength`, `direction`, `valid_from`, `valid_until`,
`first_observed_at`, `last_observed_at`, `last_verified_at`.

---

## 8. Raw benchmark results (clustered fixture, base 50%)

First render = fixture load + engine init + first painted frame after ready.
Frame stats sampled over 60 idle frames / 90 wheel frames. Units: ms (lower is
better), heap MB.

| Engine | Scale | Init | First render | Idle P95 | Pan/Zoom P95 | Heap | OK |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cosmos *(NC)* | tiny | 2 | **9** | 16.8 | 16.8 | 20 | ✓ |
| cosmos *(NC)* | small | 3 | **36** | 16.8 | 16.8 | 18 | ✓ |
| cosmos *(NC)* | medium | 11 | **150** | 16.9 | 16.8 | 35 | ✓ |
| cosmos *(NC)* | large | 63 | **736** | 16.8–33 | 16.8 | 224 | ✓ |
| cosmos *(NC)* | stress | 97 | **1504** | 33–50 | 16.8 | 217 | ✓ |
| sigma | tiny | 67 | 81 | 16.8 | 16.8 | 14 | ✓ |
| sigma | small | 33 | 65 | 16.8 | 16.8 | 16 | ✓ |
| sigma | medium | 157 | 298 | 16.8 | 16.8 | 65 | ✓ |
| sigma | large | 1058 | 1724 | 16.8 | 16.8 | 141 | ✓ |
| sigma | stress | 2321 | 3668 | 16.8 | 16.8 | 598 | ✓ |
| cytoscape | tiny | 63 | 119 | 16.8 | 16.8 | 20 | ✓ |
| cytoscape | small | 196 | 405 | 16.8 | 33.3 | 24 | ✓ |
| cytoscape | medium | 1118 | 2141 | **283** | 16.8 | 222 | ✓ |
| cytoscape | large | 5406 | 11286 | **3169** | **3103** | 1221 | ✓ |
| g6 | tiny | 1019 | 1036 | 16.8 | 16.8 | 57 | ✓ |
| g6 | small | 2306 | 2368 | 16.8 | 16.8 | 89 | ✓ |
| g6 | medium | — | **FAIL** | — | — | — | ✗ |

**G6 medium failure mode:** `RangeError: Maximum call stack size exceeded` and a
main-thread lockup that never yielded (the harness could not even time out via
page JS). Run terminated externally. Recorded as an observed result; not in
`perf.json`.

Idle P95 ≈ 16.8 ms = 60 fps (vsync-bound). Values above ~33 ms indicate dropped
frames.

---

## 9. Scenario results (medium 10k/50k unless noted; ms)

| Scenario metric | cytoscape | sigma | cosmos *(NC; historical only)* |
| --- | ---: | ---: | ---: |
| Progressive expand +100 | 36 | 15 | 36 |
| +500 | 71 | 13 | 48 |
| +5,000 | 436 | **134** | 53 |
| +20,000 | **1980** | **190** | 30 |
| Recenter | 77 | **7** | 28 |
| Epistemic toggle (OBSERVED-only) | **857** | **30** | 16 |
| PATHX highlight | **715** | **40** | 14 |
| Filter by nature | **1238** | **29** | 17 |
| Temporal T1→T2 | **629** | **27** | 13 |
| Hairball idle P95 | 16.8 | 16.8 | 16.8 |

These are committed historical raw-run results. The later P0-GRAPH-01R review
found adapter/harness defects that affect interpretation of some scenario rows;
the raw evidence is preserved and has not been rewritten. In particular, filter
and temporal timings came from the pre-repair harness and are not trusted as
validated performance facts or product targets. The current harness removed the
Cosmos adapter, so historical Cosmos rows cannot be reproduced by the current
harness. The repair did not change the architecture conclusion.

### 9.1 FIRST_MAP (Scenario 1)
Base 5% initial render cost is dominated by engine init (see §8). The historical
run reported “useful first render” for tested engines at small/medium; historical
Sigma/Cosmos values were < 350 ms at medium and Cytoscape ≈ 2.1 s. Cosmos is no
longer in the current harness, and these remain harness measurements rather
than product budgets.

### 9.2 Progressive expansion (Scenario 2)
The historical scenario requested a +20,000 expansion; on the medium fixture
the final Sigma operation had only 3,900 pending nodes remaining after earlier
stages. Its 190 ms record therefore is not a measurement of adding 20,000 new
nodes in that single call. Treat expansion timings as harness-specific
historical evidence, not as a universal scale guarantee. The large/stress
first-render and idle/frame measurements remain the clearest unaffected
comparative evidence for provisional Sigma headroom; the selection remains
accepted by ADR-0009.

### 9.3 Recenter (Scenario 3)
Sigma camera recenter 7 ms; cosmos (index zoom) 28 ms; Cytoscape 77 ms.

### 9.4 Semantic LOD (Scenario 4) — architectural
None of the engines provides semantic LOD out of the box. Sigma/cosmos expose
enough low-level control (custom WebGL programs; per-node/edge reducers) for an
AXIGNAL LOD projector to add/remove/aggregate elements per zoom band. G6 has
built-in aggregation/combo but fails at scale with the tested renderer.
**Verdict:** LOD must be owned by AXIGNAL in all cases; tested only at the
capability level, not as a finished LOD implementation (evidence gap).

### 9.5 Epistemic relationships (Scenario 5)
Edge pattern/colour/opacity by epistemic class is feasible on all engines.
Sigma reducers toggle classes in **30 ms** at medium; Cytoscape class toggling
costs **857 ms** (style recalculation); cosmos re-uploads link colours in 16 ms.
Observed vs Potential distinction is expressible in every engine; only Sigma
keeps it interactive at medium.

### 9.6 PATHX (Scenario 6)
Sigma highlight **40 ms**; cosmos 14 ms; Cytoscape **715 ms**. Clear is cheap on
Sigma/cosmos (reducer/colour reset). PATHX is a strong Sigma/cosmos scenario.

### 9.7 Corporate structure (Scenario 7)
Rendered from the corporate fixture; mixed hierarchy/network is a *layout and
grammar* concern, not a renderer feature. G6’s combos would help but failed at
medium; Sigma/cosmos require AXIGNAL-side hierarchical projection. Screenshots
captured.

### 9.8 Temporal transition (Scenario 8)
Approximated as an edge-population filter between T1 and T2: Sigma **27 ms**,
cosmos **13 ms**, Cytoscape **629 ms**. Cognitive continuity (animated enter/exit)
must be AXIGNAL-owned; engines only render the resulting frame.

### 9.9 Filtering (Scenario 9)
Nature/epistemic filter: Sigma **29 ms**, cosmos 17 ms, Cytoscape **1238 ms**.
Depth/market filters require AXIGNAL-side precomputation in all cases.

### 9.10 Continuous AXENT discovery (Scenario 10)
Sigma/cosmos accept continuous incremental adds while remaining interactive
(expansion deltas above). Cytoscape’s per-add cost breaks interaction at medium.

---

## 10. Visual extensibility findings

All adapters implemented: kind-based node colour/size, edge width by materiality,
opacity by evidence strength, line-style/pattern by epistemic class, directional
arrowheads, PATHX emphasis/dim, and class-based filtering — using only public
engine APIs. Screenshots: `experiments/graph-engine-bakeoff/screenshots/*.jpg`.

- **Sigma:** cleanest out-of-the-box legibility; node/edge reducers make the
  epistemic grammar natural. Custom node/edge WebGL programs available for
  higher ceilings; labels are the main limitation (see §12).
- **cosmos:** GPU rendering + simulation, but default config produced tiny marks
  at auto-fit; a distinctive grammar would require substantial custom shaders
  (and it is license-blocked anyway).
- **G6:** rich visual item set, but the default renderer’s scale failure and
  built-in item model pull semantics toward the framework.
- **Cytoscape:** expressive style sheet (patterns, dashed lines) but style
  recalculation dominates at scale.

**Conclusion:** the renderer does not, by itself, prevent a distinctive AXIGLAND
grammar, but the semantic layer that maps meaning → visual channels must be
AXIGNAL-owned so it is not rewritten per engine.

---

## 11. Semantic LOD findings

Extends §9.4. Required levels WORLD → SECTOR/CLUSTER → ECOSYSTEM →
ORGANIZATION → RELATIONSHIP → EVIDENCE are not a renderer feature. They require
aggregation, visibility rules, label rules, edge reduction and progressive
disclosure on a **projection** above the renderer. The bakeoff shows the renderer
can accept the projected element set fast enough (Sigma incremental add; cosmos
GPU), but the projection itself is AXIGNAL work. **Evidence gap:** no end-to-end
LOD prototype was built; only feasibility was established.

---

## 12. Temporal findings

Time belongs on edges (MASTER §20). All engines render whatever the projection
provides; none models temporal validity. Sigma/cosmos re-render a filtered edge
set in < 30 ms at medium, making scrubbing feasible if AXIGNAL precomputes
interval state. Label and continuity work remains AXIGNAL-owned.

---

## 13. PATHX findings

See §9.6. PATHX is a re-emphasis operation over a large context. Sigma/cosmos
handle it interactively; Cytoscape does not at medium. This is a core AXIGLAND
interaction and is a meaningful differentiator toward Sigma/cosmos.

---

## 14. Accessibility findings (architectural)

A WebGL/canvas surface is not accessible on its own. All four engines require an
AXIGNAL-owned **parallel interaction model**: a DOM inspector/sidebar with focus
management, a virtualized accessible list of the current selection, keyboard
navigation that drives the camera/selection, and non-colour-only semantics
(patterns + shape + text). The bakeoff deliberately kept the graph out of React
(imperative controller), which makes it straightforward to expose a React
inspector bound to AXIGNAL selection state. No engine provides this; no engine
blocks it. **Evidence gap:** no screen-reader/keyboard prototype was built.

---

## 15. React / Next findings (architectural)

The intended stack is React 19 / Next 16.

- **Recommended architecture** (matches MASTER §16 and avoids graph state in
  React):

  ```
  React application shell            (server components, routing, inspector UI)
        │  selection / filters / camera intent  (events + small shared state)
        ▼
  AXIGNAL Graph Controller           (AXIGNAL-owned; imperative)
        ▼
  Renderer Adapter (sigma | …)       (imperative GPU renderer)
  ```

- All engines are client-only (canvas/WebGL) → `"use client"` / dynamic import
  with `ssr: false`. Sigma/cosmos/G6/Cytoscape all need a mounted DOM node.
- Strict Mode double-invoke requires idempotent init + full `destroy()`; the
  adapters already implement `destroy()`.
- Worker/off-thread: layout and projections can run off the main thread; the
  renderer stays on it. Sigma/cosmos do not require React integration at all,
  which is an advantage over G6’s component-oriented model.
- **Evidence gap:** no Next.js SSR/hydration prototype was built; assessment is
  architectural.

---

## 16. Developer-experience findings

- **Sigma + Graphology:** small, focused TypeScript surface; reducers are the
  cleanest mechanism for epistemic styling; Graphology gives algorithms/layouts
  (MIT). Type quality good.
- **cosmos:** TypeScript API is typed but the core source is closed; debugging
  and contribution are limited; distribution-only.
- **G6 v5:** large API surface (behaviors, plugins, items, layouts); powerful but
  the default renderer failed at medium in this configuration, and its item model
  invites semantic coupling.
- **Cytoscape:** mature, well-documented, extensive algorithms; TypeScript good;
  performance is the limit, not DX.

---

## 17. Failure modes

| Engine | Failure | Evidence |
| --- | --- | --- |
| G6 v5 | `RangeError: Maximum call stack size exceeded` + main-thread lockup at 10k/50k (default renderer). | observed; run terminated externally |
| Cytoscape | 11.3 s first render, 0.3 fps idle, 1.2 GB heap at 50k/250k. | `results/perf.json` (`cytoscape large`) |
| cosmos | License (NC) blocks adoption; default visual config collapses positions (not pinned). | `results/environment.json`, npm license |
| Ogma | Not installable (private npm) → cannot benchmark. | `npm view @linkurious/ogma` → 404 |
| All | Labels/LOD/accessibility/temporal are not provided; must be AXIGNAL-owned. | §9–§15 |

Bottleneck attribution: Cytoscape large = **rendering + style + data**; G6 medium
= **graph-algorithm/renderer recursion**; cosmos/sigma medium = **none of the
above** (vsync-bound). Do not attribute all slowdowns to “the renderer”.

---

## 18. Framework-first analysis (Hypothesis A)

`AXIGLAND → high-level framework → renderer`.

- Gains: built-in layouts/behaviors/plugins, faster first feature.
- Costs measured: G6 (the strongest framework-first candidate) **fails at
  medium** with its default renderer, and pulls semantics into vendor items.
  Cytoscape (framework-like) fails at large. cosmos is not a framework.
- **Verdict:** framework-first cannot be the foundation. It cannot meet the
  large-graph and semantic-ownership gates. A framework may still be used for
  *ancillary* surfaces, not the canonical cartography.

## 19. AXIGNAL-cartography-layer analysis (Hypothesis B)

`AXIGLAND projection → AXIGNAL semantic/cartographic layer → renderer adapter →
GPU renderer`.

- Sigma and cosmos demonstrate the renderer can consume a projected element set
  fast enough (incremental add, epistemic reducers, PATHX, temporal frame swaps).
- AXIGNAL owns: semantic LOD, epistemic grammar, temporal projection, PATHX
  state, selection/recenter/focus, filter/cluster/distance projection,
  incremental materialization.
- Renderer owns: GPU buffers, drawing, camera, hit testing, scheduling.
- **Verdict:** strongly supported; renderer replaceability (e.g., a future
  WebGPU engine) is preserved by the adapter seam.

## 20. Commercial-reference lessons (Ogma, doc-only)

`OGMA_EXECUTABLE_BENCHMARK=BLOCKED` (private npm; no license accepted). From
public documentation, a mature commercial product bundles: semantic grouping/
combos, transformations (filter/aggregate/expand), view/animation control, path
interaction, annotations, label management, and mixed hierarchy/network layouts.
**Lesson:** these are the AXIGNAL-owned deliverables our layer must provide; the
renderer is not expected to. This does not penalize open-source candidates.

## 21. Risks

- Sigma v3 vs v4-beta churn; pin to v3.0.3 and track v4 readiness.
- Graphology as a single in-memory store may not hold 500k+ edges comfortably
  (598 MB heap at stress); projections/server-side materialization will matter.
- LOD/accessibility/temporal are unbuilt; they are the real cost, not the
  renderer.
- If AXIGNAL semantics are written directly into engine reducers without the
  adapter seam, renderer replaceability is lost.

## 22. Recommendation

- **Reject** cosmos.gl (license) and Ogma (not installable) as foundations.
- **Reject** G6 as the cartography foundation (large-graph failure).
- **Retain** Cytoscape only as an algorithm/reference control.
- **Adopt** an **AXIGNAL-owned cartography layer + replaceable renderer
  adapter**, with **Sigma.js v3 + Graphology** as the initial implementation
  choice, as accepted by CTO in ADR-0009. Runtime implementation remains a
  separate authorized slice.
- Build the missing AXIGNAL-owned pieces before any production graph: semantic
  LOD projector, epistemic grammar, temporal projection, PATHX state,
  accessibility complement, label strategy.

## 23. Evidence still missing

- End-to-end semantic LOD prototype (aggregation/disclosure).
- Empirical accessibility (keyboard + screen reader) prototype.
- Empirical React 19 / Next 16 SSR/hydration integration.
- Label strategy at scale (collision, level-of-detail labels).
- WebGPU renderer evaluation (no adoptable candidate found yet).
- Layout quality comparison (positions were precomputed to isolate rendering).
- G6 with its WebGL renderer/plugins at medium+ (only the default renderer was
  tested).

## 24. Reproduction

```powershell
cd experiments/graph-engine-bakeoff
npm install
node fixtures/generate.mjs --only tiny --topology all
node fixtures/generate.mjs --only small --topology all
node fixtures/generate.mjs --only medium --topology all
node fixtures/generate.mjs --only large --topology clustered
node fixtures/generate.mjs --only stress --topology clustered
node fixtures/hash.mjs
node benchmark/smoke.mjs                                  # adapter sanity
node benchmark/run.mjs --mode=perf --engines=cytoscape,sigma --scales=tiny,small,medium
node benchmark/run.mjs --mode=perf --engines=g6 --scales=tiny,small
node benchmark/run.mjs --mode=perf --engines=sigma --scales=large,stress
node benchmark/run.mjs --mode=perf --engines=cytoscape --scales=large
node benchmark/run.mjs --mode=scenarios --engines=cytoscape,sigma
node benchmark/run.mjs --mode=screenshots
```

Requires Python-free; needs Node 18+ and system Chrome. Heavy runs are not part
of required CI.
