/**
 * cosmos.gl adapter (WebGL GPU force simulation + rendering). REFERENCE ONLY.
 *
 * License is CC-BY-NC-4.0 (NonCommercial) and the core source repository is not
 * public. It is NOT adoptable for commercial AXIGNAL; it is measured only to
 * characterise the GPU-renderer ceiling. Do not use in product code.
 */

import { Graph } from "@cosmograph/cosmos";

const toRGBA = (hex, alpha = 1) => {
  const h = hex.replace("#", "");
  return [
    parseInt(h.slice(0, 2), 16) / 255,
    parseInt(h.slice(2, 4), 16) / 255,
    parseInt(h.slice(4, 6), 16) / 255,
    alpha,
  ];
};
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

export default function createCosmosAdapter({ container, base, pending, onReady }) {
  const host = document.createElement("div");
  host.style.width = "100%";
  host.style.height = "100%";
  container.appendChild(host);

  const index = new Map();
  const positions = new Float32Array(base.nodes.length * 2);
  const sizes = new Float32Array(base.nodes.length);
  const colors = new Float32Array(base.nodes.length * 4);
  base.nodes.forEach((n, i) => {
    index.set(n.id, i);
    positions[i * 2] = n.x;
    positions[i * 2 + 1] = n.y;
    sizes[i] = 3 + n.relevance * 14;
    const c = toRGBA(KIND_COLOR[n.kind] || "#888");
    colors.set(c, i * 4);
  });
  const links = new Float32Array(base.edges.length * 2);
  const linkColors = new Float32Array(base.edges.length * 4);
  const linkWidths = new Float32Array(base.edges.length);
  const edgeIndex = new Map();
  base.edges.forEach((e, i) => {
    edgeIndex.set(e.id, i);
    links[i * 2] = index.get(e.source) ?? 0;
    links[i * 2 + 1] = index.get(e.target) ?? 0;
    linkColors.set(toRGBA(EPI_COLOR[e.epistemicClass] || EPI_COLOR.OBSERVED, 0.6), i * 4);
    linkWidths[i] = 0.4 + e.materiality * 2.6;
  });

  const graph = new Graph(host, {
    spaceSize: 4096,
    backgroundColor: "#0b0d12",
    enableSimulation: true,
    renderLinks: true,
    linkWidthScale: 1,
    nodeSizeScale: 1,
    renderHoveredPointRing: true,
    fitViewOnInit: true,
  });
  graph.setPointPositions(positions);
  graph.setPointSizes(sizes);
  graph.setPointColors(colors);
  graph.setLinks(links);
  graph.setLinkColors(linkColors);
  graph.setLinkWidths(linkWidths);
  graph.render();
  onReady?.();

  const baseNodeCount = base.nodes.length;
  const nextNodes = pending.nodes;
  const nextEdges = pending.edges;
  let addedNodes = 0;

  async function rebuild() {
    const totalNodes = baseNodeCount + addedNodes;
    const pos = new Float32Array(totalNodes * 2);
    pos.set(positions.subarray(0, totalNodes * 2));
    graph.setPointPositions(pos);
    graph.setLinks(links);
    graph.render(1, 0);
  }

  return {
    engine: "cosmos",
    async expand(count) {
      let added = 0;
      for (const n of nextNodes) {
        if (added >= count) break;
        const i = baseNodeCount + addedNodes;
        if (index.has(n.id)) continue;
        index.set(n.id, i);
        addedNodes += 1;
        added += 1;
      }
      await rebuild();
      return added;
    },
    async recenter(id) {
      const i = index.get(id);
      if (i !== undefined) graph.zoomToPointByIndex(i, 0, 3, true, false);
    },
    async filter() {
      /* cosmos has no per-element visibility; measured via alpha re-upload in runner */
    },
    async highlightPath(edgeIds) {
      const set = new Set(edgeIds);
      const dim = new Float32Array(linkColors.length);
      dim.set(linkColors);
      for (let i = 0; i < linkColors.length; i += 4) {
        dim[i + 3] = 0.03;
      }
      for (const id of edgeIds) {
        const i = edgeIndex.get(id);
        if (i !== undefined) {
          dim.set(toRGBA("#f7768e", 1), i * 4);
        }
      }
      void set;
      graph.setLinkColors(dim);
      graph.render(0, 0);
    },
    async clearPath() {
      graph.setLinkColors(linkColors);
      graph.render(0, 0);
    },
    async setEpistemic(visible) {
      const out = new Float32Array(linkColors.length);
      for (let i = 0; i < base.edges.length; i += 1) {
        const cls = base.edges[i].epistemicClass;
        out.set(visible.includes(cls) ? linkColors.subarray(i * 4, i * 4 + 4) : [0, 0, 0, 0], i * 4);
      }
      graph.setLinkColors(out);
      graph.render(0, 0);
    },
    destroy() {
      graph.destroy();
      host.remove();
    },
    instance: graph,
  };
}
