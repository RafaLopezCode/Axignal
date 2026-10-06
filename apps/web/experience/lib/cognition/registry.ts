/**
 * Governed allowlist of cognitive components.
 *
 * A component is chosen for the shape of the knowledge it explains and the
 * question it answers, never invented. Each one declares what it needs and which
 * epistemic states it can render honestly; the validator enforces it.
 */
import type { Epistemic, FamilyId } from "../projection";
import { familyShapes, type FamilyFacts, type KnowledgeShape } from "./facts";

export type Intent = "overview" | "why" | "how_known" | "change" | "coverage";
/** 1 · understand in 10 seconds · 2 · why it matters · 3 · how AXIGNAL knows · 4 · all evidence. */
export type Layer = 1 | 2 | 3 | 4;

export type CognitiveComponentId =
  | "trend-chart"
  | "topic-deltas"
  | "answer-space-matrix"
  | "claim-support"
  | "opportunity-brief"
  | "capability-demand-match"
  | "requirement-matrix"
  | "relationship-network"
  | "territory-matrix"
  | "discourse-map"
  | "change-timeline"
  | "provenance-trail";

export type ComponentDeclaration = {
  id: CognitiveComponentId;
  shapes: KnowledgeShape[] | "ANY";
  answers: Intent[];
  layer: Layer;
  epistemicStates: Epistemic[];
  requires: (facts: FamilyFacts) => boolean;
  responsive: "stack" | "scroll-table" | "list-fallback";
  accessibleFallback: string;
  states: { empty: string; error: string };
};

const ALL: Epistemic[] = ["OBSERVED", "POTENTIAL", "UNKNOWN"];

export const COGNITIVE_REGISTRY: Record<CognitiveComponentId, ComponentDeclaration> = {
  "trend-chart": {
    id: "trend-chart",
    shapes: ["TREND"],
    answers: ["overview", "change"],
    layer: 1,
    epistemicStates: ["OBSERVED", "UNKNOWN"],
    requires: (f) => (f.trend?.points.length ?? 0) > 0,
    responsive: "stack",
    accessibleFallback: "data table of every measurement, UNKNOWN points named",
    states: { empty: "no measurement yet", error: "measurement unavailable" },
  },
  "topic-deltas": {
    id: "topic-deltas",
    shapes: ["TREND"],
    answers: ["overview", "why", "change"],
    layer: 2,
    epistemicStates: ["OBSERVED", "UNKNOWN"],
    requires: (f) => (f.trend?.topics.length ?? 0) > 0,
    responsive: "list-fallback",
    accessibleFallback: "list of topics with signed deltas or 'not measured'",
    states: { empty: "no topics measured", error: "topics unavailable" },
  },
  "answer-space-matrix": {
    id: "answer-space-matrix",
    shapes: ["ANSWER_SPACE"],
    answers: ["overview", "coverage"],
    layer: 1,
    epistemicStates: ["OBSERVED", "UNKNOWN"],
    requires: (f) => (f.answerSpace?.questions.length ?? 0) > 0,
    responsive: "scroll-table",
    accessibleFallback: "table of questions × surfaces with textual cell states",
    states: { empty: "no generative surface observed", error: "answer sample unavailable" },
  },
  "claim-support": {
    id: "claim-support",
    shapes: ["ANSWER_SPACE"],
    answers: ["why", "how_known", "coverage"],
    layer: 2,
    epistemicStates: ALL,
    requires: (f) => (f.answerSpace?.claims.length ?? 0) > 0,
    responsive: "list-fallback",
    accessibleFallback: "list of claims with their support state",
    states: { empty: "no claims observed", error: "claims unavailable" },
  },
  "opportunity-brief": {
    id: "opportunity-brief",
    shapes: ["DEMAND_MATCH"],
    answers: ["overview", "why"],
    layer: 1,
    epistemicStates: ["POTENTIAL", "UNKNOWN"],
    requires: (f) => (f.opportunities?.length ?? 0) > 0,
    responsive: "stack",
    accessibleFallback: "one heading and sentence per opportunity",
    states: { empty: "no plausible demand found yet", error: "opportunities unavailable" },
  },
  "capability-demand-match": {
    id: "capability-demand-match",
    shapes: ["DEMAND_MATCH"],
    answers: ["why"],
    layer: 2,
    epistemicStates: ["POTENTIAL", "UNKNOWN"],
    requires: (f) => (f.opportunities?.length ?? 0) > 0,
    responsive: "stack",
    accessibleFallback: "capability statement, then demand statement, each with source",
    states: { empty: "no match to explain", error: "match unavailable" },
  },
  "requirement-matrix": {
    id: "requirement-matrix",
    shapes: ["DEMAND_MATCH"],
    answers: ["why", "how_known"],
    layer: 3,
    epistemicStates: ["POTENTIAL", "UNKNOWN"],
    requires: (f) => (f.opportunities?.length ?? 0) > 0,
    responsive: "list-fallback",
    accessibleFallback: "two lists: known requirements and still unknown requirements",
    states: { empty: "no requirements read", error: "requirements unavailable" },
  },
  "relationship-network": {
    id: "relationship-network",
    shapes: ["NETWORK"],
    answers: ["overview", "why", "coverage"],
    layer: 1,
    epistemicStates: ["OBSERVED", "POTENTIAL"],
    requires: (f) => (f.network?.edges.length ?? 0) > 0,
    responsive: "list-fallback",
    accessibleFallback: "observed relationships list, then a separate potential list",
    states: { empty: "no relationship observed", error: "relationships unavailable" },
  },
  "territory-matrix": {
    id: "territory-matrix",
    shapes: ["TERRITORY"],
    answers: ["overview", "coverage", "why"],
    layer: 1,
    epistemicStates: ALL,
    requires: (f) => (f.territory?.markets.length ?? 0) > 0,
    responsive: "list-fallback",
    accessibleFallback: "list of markets grouped by epistemic state",
    states: { empty: "no market scoped", error: "markets unavailable" },
  },
  "discourse-map": {
    id: "discourse-map",
    shapes: ["DISCOURSE"],
    answers: ["overview", "why", "change"],
    layer: 1,
    epistemicStates: ["OBSERVED", "UNKNOWN"],
    requires: (f) => (f.discourse?.statements.length ?? 0) + (f.discourse?.absences.length ?? 0) > 0,
    responsive: "stack",
    accessibleFallback: "statements with where/when/sample, contradictions and absences listed",
    states: { empty: "no public statement observed", error: "statements unavailable" },
  },
  "change-timeline": {
    id: "change-timeline",
    shapes: "ANY",
    answers: ["overview", "change"],
    layer: 1,
    epistemicStates: ALL,
    requires: (f) => (f.change?.events.length ?? 0) > 0,
    responsive: "stack",
    accessibleFallback: "ordered list of dated changes",
    states: { empty: "no change observed in this cut", error: "history unavailable" },
  },
  "provenance-trail": {
    id: "provenance-trail",
    shapes: "ANY",
    answers: ["how_known"],
    layer: 3,
    epistemicStates: ALL,
    requires: (f) => f.sources.length > 0,
    responsive: "stack",
    accessibleFallback: "ordered list of sources with instrument, date and limitation",
    states: { empty: "no source observed in this cut", error: "sources unavailable" },
  },
};

export function shapesOf(family: FamilyId): KnowledgeShape[] {
  return familyShapes[family];
}

export function compatible(
  declaration: ComponentDeclaration,
  family: FamilyId,
): boolean {
  if (declaration.shapes === "ANY") return true;
  return declaration.shapes.some((shape) => shapesOf(family).includes(shape));
}
