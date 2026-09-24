# AXIGLAND Graph Engine Bakeoff (experiment)

Isolated, removable experiment that measures candidate graph-rendering
architectures for AXIGLAND on a neutral benchmark model.

**This is not production code.** Candidate engines here are **not** AXIGNAL
production dependencies, and nothing in this folder may be imported by the
domain, pipeline or cognition layers.

- Report: [`../../docs/research/AXIGLAND_GRAPH_ENGINE_BAKEOFF.md`](../../docs/research/AXIGLAND_GRAPH_ENGINE_BAKEOFF.md)
- Decision: [`../../docs/research/AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md`](../../docs/research/AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md)
- Proposed ADR: [`../../docs/adr/ADR-0009-axigland-graph-architecture.md`](../../docs/adr/ADR-0009-axigland-graph-architecture.md)

## Layout

```
model/model.mjs          neutral benchmark model + visual-mapping fields
fixtures/generate.mjs    deterministic seeded fixtures (mulberry32, seed 20260924)
fixtures/hash.mjs        writes fixtures/manifest.json (SHA-256 per fixture)
fixtures/manifest.json   committed fixture hashes
app/adapters/*.js        per-engine adapters (same model every engine)
app/instrumentation.js   rAF frame sampling + marks
app/main.js              harness entry (window.AXIGBench)
benchmark/lib.mjs        Vite server + Playwright Chrome management
benchmark/smoke.mjs      adapter sanity check
benchmark/run.mjs        perf / scenarios / screenshots runner
results/*.json           raw results (committed)
screenshots/*.jpg        human-review captures (committed)
```

## Reproduce

```powershell
npm install
node fixtures/generate.mjs --only tiny --topology all
node fixtures/generate.mjs --only small --topology all
node fixtures/generate.mjs --only medium --topology all
node fixtures/generate.mjs --only large --topology clustered
node fixtures/generate.mjs --only stress --topology clustered
node fixtures/hash.mjs
node benchmark/smoke.mjs
node benchmark/run.mjs --mode=perf --engines=cytoscape,sigma --scales=tiny,small,medium
node benchmark/run.mjs --mode=perf --engines=g6 --scales=tiny,small
node benchmark/run.mjs --mode=perf --engines=sigma --scales=large,stress
node benchmark/run.mjs --mode=perf --engines=cytoscape --scales=large
node benchmark/run.mjs --mode=scenarios --engines=cytoscape,sigma,g6
node benchmark/run.mjs --mode=screenshots
```

Requires Node 18+, a locally installed Chrome, and (for `ui-ux-pro-max`
screenshots review) Python 3. Heavy fixtures (`fixtures/data/`) are generated,
**not** committed. Results and screenshots are committed for review.

## License warnings

- Cosmos measurements in the committed report, results, and screenshots are
  historical bakeoff evidence. The Cosmos adapter and package were removed
  because `@cosmograph/cosmos` is **CC-BY-NC-4.0** (NonCommercial) and its core
  repository is not public. Current runs cannot reproduce those measurements;
  Cosmos must never become an AXIGNAL dependency.
- `@linkurious/ogma` is not publicly installable and is not included.

## Determinism

- Fixtures: seeded PRNG only; identical bytes for every engine.
- Positions are precomputed so rendering throughput is measured independently of
  layout.
- Benchmark runs are **not** part of required CI (machine/GPU dependent).
