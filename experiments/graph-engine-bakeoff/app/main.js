/** AXIGLAND bakeoff harness entry. Exposes window.AXIGBench for the runner. */

import { ADAPTERS } from "./adapters/index.js";
import { heapMB, mark, measureWheel, metrics, nextFrame, record, sampleFrames, since } from "./instrumentation.js";
import { baseSplit, loadFixture, pickPath } from "./model.js";

const params = new URLSearchParams(location.search);
const engine = params.get("engine") || "cytoscape";
const fixture = params.get("fixture") || "tiny.clustered.json";
const baseFraction = Number(params.get("base") || 0.3);

const container = document.getElementById("graph");

const state = {
  timeT: Number.POSITIVE_INFINITY,
  epistemic: ["OBSERVED", "POTENTIAL", "HISTORICAL"],
  natures: null,
};

let adapter = null;
let data = null;

function activeEdge(edge) {
  if (edge.first_observed_at > state.timeT) return false;
  if (edge.valid_from != null && edge.valid_from > state.timeT) return false;
  if (edge.valid_until != null && edge.valid_until < state.timeT) return false;
  return true;
}

function buildPred() {
  return {
    node: () => true,
    edge: (e) =>
      state.epistemic.includes(e.epistemicClass) &&
      (state.natures == null || state.natures.includes(e.nature)) &&
      activeEdge(e),
  };
}

async function applyFilter() {
  await adapter.filter(buildPred());
}

const api = {
  engine,
  fixture,
  errors: [],
  results: {},
  ready: null,
  async init() {
    mark("t0");
    const loaded = await loadFixture(`/fixtures/data/${fixture}`);
    metrics.marks.fixture_loaded = performance.now();
    data = loaded.data;
    record("data_fetch_ms", Math.round(loaded.timings.fetchMs));
    record("data_parse_ms", Math.round(loaded.timings.parseMs));
    record("data_bytes", loaded.timings.bytes);

    const split = baseSplit(data, baseFraction);
    this._base = split.base;
    metrics.marks.graph_init_start = performance.now();
    let readyResolve;
    const onReady = () => {
      metrics.marks.graph_ready = performance.now();
      readyResolve?.();
    };
    const readyPromise = new Promise((r) => {
      readyResolve = r;
    });
    const factory = ADAPTERS[engine];
    if (!factory) throw new Error(`unknown engine: ${engine}`);
    adapter = await factory({ container, base: split.base, pending: split.pending, onReady });
    if (!metrics.marks.graph_ready) {
      onReady();
    }
    await Promise.race([readyPromise, nextFrame()]);
    await nextFrame();
    mark("first_render");
    record("graph_init_ms", Math.round(metrics.marks.graph_ready - metrics.marks.graph_init_start));
    record("first_render_ms", Math.round(metrics.marks.first_render - metrics.marks.t0));
    record("time_to_interactive_ms", Math.round(metrics.marks.first_render - metrics.marks.t0));
    record("base_nodes", split.base.nodes.length);
    record("base_edges", split.base.edges.length);
    record("pending_nodes", split.pending.nodes.length);
    record("pending_edges", split.pending.edges.length);
    record("js_heap_mb", heapMB());
    const initialMetrics = Object.fromEntries(
      metrics.events.map(({ name, value }) => [name, value]),
    );
    this.results = {
      engine,
      fixture,
      ...initialMetrics,
      meta: { engine, fixture, ...metrics.marks },
    };
    return this;
  },
  async idleFrames(n = 90) {
    const stats = await sampleFrames(n);
    record("idle", stats);
    record("js_heap_mb", heapMB());
    return stats;
  },
  async panZoomFrames(n = 90) {
    const stats = await measureWheel(container, n);
    record("pan_zoom", stats);
    return stats;
  },
  async expand(count) {
    const t = performance.now();
    const added = await adapter.expand(count);
    await nextFrame();
    const ms = performance.now() - t;
    record(`expand_${count}_ms`, Math.round(ms));
    record(`expand_${count}_added`, added);
    return { added, ms };
  },
  async recenter(id) {
    const t = performance.now();
    await adapter.recenter(id);
    await nextFrame();
    const ms = performance.now() - t;
    record("recenter_ms", Math.round(ms));
    return ms;
  },
  async pathx() {
    const edges = pickPath(this._base ?? data, 6);
    const t = performance.now();
    await adapter.highlightPath(edges.map((e) => e.id));
    await nextFrame();
    const ms = performance.now() - t;
    record("pathx_highlight_ms", Math.round(ms));
    return { edges: edges.map((e) => e.id), ms };
  },
  async clearPath() {
    await adapter.clearPath();
    await nextFrame();
  },
  async epistemic(classes) {
    state.epistemic = classes;
    const t = performance.now();
    await applyFilter();
    await nextFrame();
    record("epistemic_ms", Math.round(performance.now() - t));
  },
  async filterByNatures(natures) {
    state.natures = natures;
    const t = performance.now();
    await applyFilter();
    await nextFrame();
    record("filter_ms", Math.round(performance.now() - t));
  },
  async setTime(t) {
    state.timeT = t;
    const start = performance.now();
    await applyFilter();
    await nextFrame();
    record("temporal_transition_ms", Math.round(performance.now() - start));
  },
  async sampleWhile(action, frames = 120) {
    const sampler = sampleFrames(frames);
    await action();
    return sampler;
  },
  metrics() {
    return { marks: metrics.marks, events: metrics.events };
  },
  destroy() {
    try {
      adapter?.destroy();
    } catch (e) {
      this.errors.push(String(e));
    }
  },
};

window.AXIGBench = api;
api.ready = api
  .init()
  .then(() => {
    api.ok = true;
  })
  .catch((e) => {
    api.ok = false;
    api.errors.push(String(e && e.stack ? e.stack : e));
    // eslint-disable-next-line no-console
    console.error(e);
  });

void since;
