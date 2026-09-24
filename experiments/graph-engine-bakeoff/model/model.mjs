/**
 * Neutral AXIGLAND benchmark model.
 *
 * This is BENCHMARK infrastructure. It deliberately mirrors the MASTER's
 * conceptual entities only enough to exercise rendering architectures. It is
 * NOT canonical production domain architecture and must not be imported by
 * product code.
 *
 * Doctrine references: MASTER §16 (observed/potential/historical), §18
 * (FAXT/INXIGHT/PATHX), §20 (temporality), §25 (visual grammar), §36 (data model).
 */

export const NodeKind = Object.freeze({
  ORGANIZATION: "Organization",
  MARKET: "Market",
  CAPABILITY: "Capability",
  PRODUCT: "Product",
});

export const EpistemicClass = Object.freeze({
  OBSERVED: "OBSERVED",
  POTENTIAL: "POTENTIAL",
  HISTORICAL: "HISTORICAL",
});

export const Currentness = Object.freeze({
  CURRENTLY_OBSERVED: "CURRENTLY_OBSERVED",
  HISTORICAL: "HISTORICAL",
  STALE: "STALE",
  UNKNOWN_CURRENTNESS: "UNKNOWN_CURRENTNESS",
});

export const RelationshipNature = Object.freeze({
  SUPPLIES: "SUPPLIES",
  DISTRIBUTES: "DISTRIBUTES",
  MANUFACTURES_FOR: "MANUFACTURES_FOR",
  PARTNERS_WITH: "PARTNERS_WITH",
  SUBSIDIARY_OF: "SUBSIDIARY_OF",
  PARENT_OF: "PARENT_OF",
  OWNS: "OWNS",
  BRAND_OF: "BRAND_OF",
  DIVISION_OF: "DIVISION_OF",
  JOINT_VENTURE_WITH: "JOINT_VENTURE_WITH",
  AFFILIATED_WITH: "AFFILIATED_WITH",
  CUSTOMER_OF: "CUSTOMER_OF",
  CERTIFIED_BY: "CERTIFIED_BY",
});

export const Topology = Object.freeze({
  NEIGHBOURHOOD: "neighbourhood",
  CORPORATE: "corporate",
  SUPPLY: "supply",
  CLUSTERED: "clustered",
  HAIRBALL: "hairball",
  TEMPORAL: "temporal",
});

export const SCALES = Object.freeze({
  tiny: { nodes: 100, edges: 500 },
  small: { nodes: 1000, edges: 5000 },
  medium: { nodes: 10000, edges: 50000 },
  large: { nodes: 50000, edges: 250000 },
  stress: { nodes: 100000, edges: 500000 },
});

/** Visual-mapping fields used by every adapter identically. */
export function nodeVisualFields(node) {
  return {
    relevance: node.relevance, // NODE SIZE hypothesis
    evidenceCertainty: node.evidenceCertainty, // SHARPNESS hypothesis
    temporalActivity: node.temporalActivity, // HALO hypothesis
    kind: node.kind,
  };
}

export function edgeVisualFields(edge) {
  return {
    materiality: edge.materiality, // EDGE WIDTH hypothesis
    evidenceStrength: edge.evidenceStrength, // EDGE OPACITY hypothesis
    epistemicClass: edge.epistemicClass, // EDGE PATTERN hypothesis
    direction: edge.direction, // EDGE DIRECTION hypothesis
    currentness: edge.currentness,
    nature: edge.nature,
  };
}
