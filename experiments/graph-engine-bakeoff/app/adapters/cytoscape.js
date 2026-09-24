/** Cytoscape.js adapter (canvas). Adoptable: MIT. */

import cytoscape from "cytoscape";

const KIND_COLOR = {
  Organization: "#7aa2f7",
  Market: "#e0af68",
  Capability: "#9ece6a",
  Product: "#bb9af7",
};
const EPI = {
  OBSERVED: { color: "#565f89", style: "solid" },
  POTENTIAL: { color: "#e0af68", style: "dashed" },
  HISTORICAL: { color: "#414868", style: "dotted" },
};

function nodeEl(n) {
  return {
    group: "nodes",
    data: {
      id: n.id,
      label: n.label,
      kind: n.kind,
      relevance: n.relevance,
      evidenceCertainty: n.evidenceCertainty,
    },
    position: { x: n.x, y: n.y },
  };
}
function edgeEl(e) {
  return {
    group: "edges",
    data: {
      id: e.id,
      source: e.source,
      target: e.target,
      nature: e.nature,
      first_observed_at: e.first_observed_at,
      valid_from: e.valid_from,
      valid_until: e.valid_until,
      epistemicClass: e.epistemicClass,
      materiality: e.materiality,
      evidenceStrength: e.evidenceStrength,
    },
  };
}
export function elementsOf({ nodes, edges }) {
  return [...nodes.map(nodeEl), ...edges.map(edgeEl)];
}

export default function createCytoscapeAdapter({ container, base, pending, onReady }) {
  const cy = cytoscape({
    container,
    elements: elementsOf(base),
    layout: { name: "preset", fit: true },
    wheelSensitivity: 0.25,
    style: [
      {
        selector: "node",
        style: {
          width: "mapData(relevance, 0, 1, 4, 22)",
          height: "mapData(relevance, 0, 1, 4, 22)",
          "background-color": (ele) => KIND_COLOR[ele.data("kind")] || "#888",
          label: "",
          "border-width": 1,
          "border-color": "rgba(255,255,255,0.25)",
        },
      },
      {
        selector: "edge",
        style: {
          width: "mapData(materiality, 0, 1, 0.4, 3)",
          "line-color": (ele) => (EPI[ele.data("epistemicClass")] || EPI.OBSERVED).color,
          "line-style": (ele) => (EPI[ele.data("epistemicClass")] || EPI.OBSERVED).style,
          "target-arrow-shape": "triangle",
          "arrow-scale": 0.5,
          "curve-style": "bezier",
          opacity: "mapData(evidenceStrength, 0, 1, 0.15, 0.9)",
        },
      },
      { selector: ".hidden", style: { display: "none" } },
      { selector: ".dim", style: { opacity: 0.06 } },
      { selector: "edge.path", style: { "line-color": "#f7768e", width: 4, opacity: 1, "z-index": 99 } },
      { selector: "node.path", style: { "border-color": "#f7768e", "border-width": 3 } },
    ],
  });
  onReady?.();

  const pendingNodes = pending.nodes.map(nodeEl);
  const pendingEdges = pending.edges.map(edgeEl);
  const addedEdgeIds = new Set(base.edges.map((edge) => edge.id));
  let pendingNodeIndex = 0;

  return {
    engine: "cytoscape",
    async expand(count) {
      const chunkNodes = pendingNodes.slice(pendingNodeIndex, pendingNodeIndex + count);
      pendingNodeIndex += chunkNodes.length;
      const availableNodeIds = new Set(cy.nodes().map((node) => node.id()));
      for (const node of chunkNodes) availableNodeIds.add(node.data.id);
      const chunkEdges = pendingEdges.filter((edge) => {
        if (addedEdgeIds.has(edge.data.id)) return false;
        if (!availableNodeIds.has(edge.data.source) || !availableNodeIds.has(edge.data.target)) return false;
        addedEdgeIds.add(edge.data.id);
        return true;
      });
      cy.batch(() => cy.add([...chunkNodes, ...chunkEdges]));
      return chunkNodes.length;
    },
    async recenter(id) {
      const node = cy.getElementById(id);
      if (node.nonempty?.() !== false && node.length) {
        cy.center(node);
        cy.zoom({ level: Math.min(2, cy.zoom() * 1.6), renderedPosition: node.renderedPosition() });
      }
    },
    async filter(pred) {
      cy.batch(() => {
        cy.elements().forEach((el) => {
          const data = el.data();
          const ok =
            el.isNode?.() === true ? pred.node(data) : pred.edge(data, cy.getElementById(data.source).data(), cy.getElementById(data.target).data());
          el.toggleClass("hidden", !ok);
        });
      });
    },
    async highlightPath(edgeIds) {
      const idSet = new Set(edgeIds);
      cy.batch(() => {
        cy.elements().addClass("dim").removeClass("path");
        for (const id of idSet) {
          const e = cy.getElementById(id);
          if (e.empty()) continue;
          e.removeClass("dim").addClass("path");
          e.source().removeClass("dim").addClass("path");
          e.target().removeClass("dim").addClass("path");
        }
      });
    },
    async clearPath() {
      cy.batch(() => cy.elements().removeClass("dim").removeClass("path"));
    },
    async setEpistemic(visible) {
      cy.batch(() => {
        cy.edges().forEach((e) => {
          e.toggleClass("hidden", !visible.includes(e.data("epistemicClass")));
        });
      });
    },
    destroy() {
      cy.destroy();
    },
    instance: cy,
  };
}
