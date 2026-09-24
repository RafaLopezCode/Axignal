/** Sigma.js v3 + Graphology adapter (WebGL). Adoptable: MIT. */

import Graph from "graphology";
import Sigma from "sigma";

const KIND_COLOR = {
  Organization: "#7aa2f7",
  Market: "#e0af68",
  Capability: "#9ece6a",
  Product: "#bb9af7",
};
const EPI_COLOR = {
  OBSERVED: "#565f89",
  POTENTIAL: "#e0af68",
  HISTORICAL: "#414868",
};

function toHex(hex) {
  const h = hex.replace("#", "");
  return { r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4, 6), 16) };
}

export default function createSigmaAdapter({ container, base, pending, onReady }) {
  const graph = new Graph({ multi: true });
  for (const n of base.nodes) {
    graph.addNode(n.id, {
      x: n.x,
      y: n.y,
      size: 3 + n.relevance * 18,
      color: KIND_COLOR[n.kind] || "#888",
      kind: n.kind,
      relevance: n.relevance,
      evidenceCertainty: n.evidenceCertainty,
    });
  }
  for (const e of base.edges) {
    graph.addEdgeWithKey(e.id, e.source, e.target, {
      size: 0.4 + e.materiality * 2.6,
      color: EPI_COLOR[e.epistemicClass] || EPI_COLOR.OBSERVED,
      epistemicClass: e.epistemicClass,
      evidenceStrength: e.evidenceStrength,
      type: "arrow",
    });
  }

  let visibleEpi = ["OBSERVED", "POTENTIAL", "HISTORICAL"];
  let pathEdges = null;
  let filterPred = null;

  const renderer = new Sigma(graph, container, {
    renderEdgeLabels: false,
    defaultEdgeType: "arrow",
    minCameraRatio: 0.02,
    maxCameraRatio: 8,
    nodeReducer: (node, data) => {
      const res = { ...data };
      if (pathEdges) res.color = pathEdges.nodes.has(node) ? "#f7768e" : "#2a2e3a";
      if (filterPred && !filterPred.node(graph.getNodeAttributes(node))) res.hidden = true;
      return res;
    },
    edgeReducer: (edge, data) => {
      const res = { ...data };
      if (!visibleEpi.includes(data.epistemicClass)) res.hidden = true;
      if (filterPred && !filterPred.edge(data)) res.hidden = true;
      if (pathEdges) {
        if (pathEdges.edges.has(edge)) {
          res.color = "#f7768e";
          res.size = 4;
        } else {
          res.color = "#1b1e29";
        }
      }
      return res;
    },
  });
  onReady?.();

  const { r, g, b } = { r: 1, g: 1, b: 1 };
  void toHex; void r; void g; void b;

  return {
    engine: "sigma",
    async expand(count) {
      let added = 0;
      const nodes = pending.nodes;
      const edges = pending.edges;
      // add any pending node whose endpoints are already present, up to count
      graph.batch?.(() => {});
      const known = new Set(graph.nodes());
      for (const n of nodes) {
        if (added >= count) break;
        if (known.has(n.id)) continue;
        graph.addNode(n.id, {
          x: n.x,
          y: n.y,
          size: 3 + n.relevance * 18,
          color: KIND_COLOR[n.kind] || "#888",
          kind: n.kind,
          relevance: n.relevance,
        });
        known.add(n.id);
        added += 1;
      }
      for (const e of edges) {
        if (graph.hasEdge(e.id)) continue;
        if (known.has(e.source) && known.has(e.target)) {
          graph.addEdgeWithKey(e.id, e.source, e.target, {
            size: 0.4 + e.materiality * 2.6,
            color: EPI_COLOR[e.epistemicClass] || EPI_COLOR.OBSERVED,
            epistemicClass: e.epistemicClass,
            evidenceStrength: e.evidenceStrength,
            type: "arrow",
          });
        }
      }
      renderer.refresh();
      return added;
    },
    async recenter(id) {
      if (graph.hasNode(id)) {
        const d = renderer.getNodeDisplayData(id);
        renderer.getCamera().animate({ x: d.x, y: d.y, ratio: 0.4 }, { duration: 0 });
      }
    },
    async filter(pred) {
      filterPred = pred;
      renderer.refresh();
    },
    async highlightPath(edgeIds) {
      const edges = new Set(edgeIds);
      const nodes = new Set();
      for (const id of edgeIds) {
        nodes.add(graph.source(id));
        nodes.add(graph.target(id));
      }
      pathEdges = { edges, nodes };
      renderer.refresh();
    },
    async clearPath() {
      pathEdges = null;
      renderer.refresh();
    },
    async setEpistemic(visible) {
      visibleEpi = visible;
      renderer.refresh();
    },
    destroy() {
      renderer.kill();
      graph.clear();
    },
    instance: renderer,
  };
}
