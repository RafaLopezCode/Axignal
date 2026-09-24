/** AntV G6 v5 adapter (canvas; WebGL available via optional renderer). Adoptable: MIT. */

import { Graph } from "@antv/g6";

const KIND_COLOR = {
  Organization: "#7aa2f7",
  Market: "#e0af68",
  Capability: "#9ece6a",
  Product: "#bb9af7",
};
const EPI = {
  OBSERVED: { color: "#565f89", dash: [] },
  POTENTIAL: { color: "#e0af68", dash: [6, 4] },
  HISTORICAL: { color: "#414868", dash: [2, 4] },
};

function nodeData(n) {
  return {
    id: n.id,
    data: { kind: n.kind, relevance: n.relevance, evidenceCertainty: n.evidenceCertainty },
    style: { x: n.x, y: n.y },
  };
}
function edgeData(e) {
  return {
    id: e.id,
    source: e.source,
    target: e.target,
    data: { epistemicClass: e.epistemicClass, materiality: e.materiality, evidenceStrength: e.evidenceStrength },
  };
}

export default async function createG6Adapter({ container, base, pending, onReady }) {
  const graph = new Graph({
    container,
    autoFit: "view",
    node: {
      style: {
        size: (d) => 4 + (d.data?.relevance ?? 0.3) * 14,
        fill: (d) => KIND_COLOR[d.data?.kind] || "#888",
        stroke: "rgba(255,255,255,0.25)",
        lineWidth: 1,
        labelText: "",
      },
      state: { dim: { opacity: 0.08 }, hidden: { visibility: "hidden" } },
    },
    edge: {
      style: {
        stroke: (d) => (EPI[d.data?.epistemicClass] || EPI.OBSERVED).color,
        lineWidth: (d) => 0.4 + (d.data?.materiality ?? 0.2) * 2,
        lineDash: (d) => (EPI[d.data?.epistemicClass] || EPI.OBSERVED).dash,
        endArrow: true,
        endArrowType: "triangle",
        opacity: (d) => 0.15 + (d.data?.evidenceStrength ?? 0.3) * 0.7,
      },
      state: {
        dim: { opacity: 0.05 },
        hidden: { visibility: "hidden" },
        path: { stroke: "#f7768e", lineWidth: 4, opacity: 1 },
      },
    },
    behaviors: ["zoom-canvas", "drag-canvas"],
    data: { nodes: base.nodes.map(nodeData), edges: base.edges.map(edgeData) },
  });
  await graph.render();
  onReady?.();

  const allNodes = pending.nodes.map(nodeData);
  const allEdges = pending.edges.map(edgeData);
  let pendingNodeIndex = 0;

  async function setStates(ids, state) {
    for (const id of ids) {
      try {
        graph.setElementState(id, state);
      } catch {
        /* element may not exist yet */
      }
    }
  }

  return {
    engine: "g6",
    async expand(count) {
      const chunkNodes = allNodes.slice(pendingNodeIndex, pendingNodeIndex + count);
      pendingNodeIndex += chunkNodes.length;
      const present = new Set(graph.getNodeData().map((n) => n.id));
      for (const n of chunkNodes) present.add(n.id);
      const chunkEdges = allEdges.filter((e) => present.has(e.source) && present.has(e.target) && e.id);
      graph.addNodeData(chunkNodes);
      graph.addEdgeData(chunkEdges);
      await graph.draw();
      return chunkNodes.length;
    },
    async recenter(id) {
      try {
        await graph.focusElement(id, { duration: 0 });
      } catch {
        /* ignore */
      }
    },
    async filter(pred) {
      const nodeIds = graph.getNodeData().map((n) => n.id);
      for (const n of graph.getNodeData()) {
        const keep = pred.node(n.data || {});
        graph.setElementState(n.id, keep ? [] : "hidden");
      }
      void nodeIds;
      for (const e of graph.getEdgeData()) {
        const keep = pred.edge(e.data || {});
        graph.setElementState(e.id, keep ? [] : "hidden");
      }
      await graph.draw();
    },
    async highlightPath(edgeIds) {
      const set = new Set(edgeIds);
      const keepNodes = new Set();
      for (const e of graph.getEdgeData()) {
        if (set.has(e.id)) {
          keepNodes.add(e.source);
          keepNodes.add(e.target);
        }
      }
      for (const n of graph.getNodeData()) graph.setElementState(n.id, keepNodes.has(n.id) ? [] : "dim");
      for (const e of graph.getEdgeData()) {
        graph.setElementState(e.id, set.has(e.id) ? "path" : "dim");
      }
      await graph.draw();
    },
    async clearPath() {
      for (const n of graph.getNodeData()) graph.setElementState(n.id, []);
      for (const e of graph.getEdgeData()) graph.setElementState(e.id, []);
      await graph.draw();
    },
    async setEpistemic(visible) {
      for (const e of graph.getEdgeData()) {
        const cls = e.data?.epistemicClass;
        graph.setElementState(e.id, visible.includes(cls) ? [] : "hidden");
      }
      await graph.draw();
    },
    destroy() {
      graph.destroy();
    },
    instance: graph,
  };
}
