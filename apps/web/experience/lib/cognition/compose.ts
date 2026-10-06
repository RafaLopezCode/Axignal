/**
 * Family-aware cognitive composition.
 *
 * family + question intent + epistemic content + available data + temporal state
 * + device → an ordered, layered plan of allowlisted components. A model may
 * propose a plan; ``validateCognitivePlan`` decides whether it may render. Facts,
 * epistemic state, currentness and provenance are never part of a plan.
 */
import type { Copy } from "../locale";
import type { Epistemic, FamilyId } from "../projection";
import type { FamilyFacts } from "./facts";
import {
  COGNITIVE_REGISTRY,
  compatible,
  shapesOf,
  type CognitiveComponentId,
  type Intent,
  type Layer,
} from "./registry";

export type Device = "desktop" | "mobile";
export type CognitivePlanItem = { component: CognitiveComponentId; layer: Layer };
export type CognitivePlan = {
  version: 2;
  family: FamilyId;
  intent: Intent;
  items: CognitivePlanItem[];
};

/** The cognitive question each family's first layer must answer. */
const c = (es: string, en: string): Copy => ({ es, en });

export const FAMILY_QUESTION: Record<FamilyId, Copy> = {
  presence: c(
    "¿Cómo está cambiando mi presencia y dónde existo en las respuestas generativas?",
    "How is my presence changing, and where do I exist in generative answers?",
  ),
  reputation: c(
    "¿Qué se dice, dónde y con qué materialidad?",
    "What is said, where, and how material is it?",
  ),
  value: c(
    "¿Dónde puede existir valor económico y qué sabemos realmente sobre él?",
    "Where could economic value exist, and what do we really know about it?",
  ),
  markets: c(
    "¿Dónde opera, dónde hay evidencia y qué mercados siguen desconocidos?",
    "Where does it operate, where is there evidence, and which markets remain unknown?",
  ),
  relationships: c(
    "¿Con quién hay una relación observable y cuáles merece la pena investigar?",
    "With whom is there an observable relationship, and which are worth investigating?",
  ),
  demand: c(
    "¿Dónde puede existir valor económico y qué sabemos realmente sobre él?",
    "Where could economic value exist, and what do we really know about it?",
  ),
  activity: c(
    "¿Qué ha cambiado y desde cuándo podemos sostenerlo?",
    "What changed, and since when can we support it?",
  ),
  economics: c(
    "¿Qué ha cambiado y desde cuándo podemos sostenerlo?",
    "What changed, and since when can we support it?",
  ),
  organization: c(
    "¿Cómo sabe AXIGNAL lo que sabe de esta empresa?",
    "How does AXIGNAL know what it knows about this company?",
  ),
  context: c(
    "¿Qué ha cambiado y desde cuándo podemos sostenerlo?",
    "What changed, and since when can we support it?",
  ),
};

export function epistemicContent(facts: FamilyFacts, family: FamilyId): Set<Epistemic> {
  const states = new Set<Epistemic>();
  for (const shape of shapesOf(family)) {
    if (shape === "DEMAND_MATCH") facts.opportunities?.forEach((o) => states.add(o.epistemic));
    if (shape === "NETWORK") facts.network?.edges.forEach((e) => states.add(e.state));
    if (shape === "TERRITORY") facts.territory?.markets.forEach((m) => states.add(m.state));
    if (shape === "TREND" && facts.trend?.points.some((p) => p.value === null)) states.add("UNKNOWN");
    if (shape === "TREND" && facts.trend?.points.some((p) => p.value !== null)) states.add("OBSERVED");
    if (shape === "ANSWER_SPACE" && facts.answerSpace) states.add("OBSERVED").add("UNKNOWN");
    if (shape === "DISCOURSE" && facts.discourse) states.add("OBSERVED").add("UNKNOWN");
  }
  return states;
}

export function composeFamily({
  family,
  intent,
  facts,
  device,
}: {
  family: FamilyId;
  intent: Intent;
  facts: FamilyFacts;
  device: Device;
}): CognitivePlan {
  const candidates = Object.values(COGNITIVE_REGISTRY).filter(
    (d) => compatible(d, family) && d.requires(facts),
  );
  // Family-specific components lead; cross-family ones (time, provenance) follow.
  const specific = candidates.filter((d) => d.shapes !== "ANY");
  const items: CognitivePlanItem[] = [];
  const add = (id: CognitiveComponentId, layer: Layer) => {
    if (!items.some((item) => item.component === id) && candidates.some((d) => d.id === id))
      items.push({ component: id, layer });
  };
  const provenanceFamily = shapesOf(family).includes("PROVENANCE");
  if (provenanceFamily || intent === "how_known") add("provenance-trail", 1);
  if (intent === "change" || (specific.length === 0 && !provenanceFamily))
    add("change-timeline", 1);
  for (const declaration of specific) {
    if (declaration.answers.includes(intent) || intent === "overview")
      add(declaration.id, intent === "overview" ? declaration.layer : Math.min(declaration.layer, 2) as Layer);
  }
  if (intent !== "change" && items.length === 0) add("change-timeline", 1);
  add("provenance-trail", intent === "how_known" ? 1 : 3);
  // Small screens keep the first layer to one primary component.
  if (device === "mobile") {
    let primary = false;
    for (const item of items) {
      if (item.layer === 1) {
        if (primary) item.layer = 2;
        primary = true;
      }
    }
  }
  items.sort((a, b) => a.layer - b.layer);
  return { version: 2, family, intent, items };
}

export type PlanCheck = { success: true; plan: CognitivePlan } | { success: false; error: string };

/** Fail closed on anything a governed composition could not honestly render. */
export function validateCognitivePlan(input: unknown, facts: FamilyFacts): PlanCheck {
  if (typeof input !== "object" || input === null) return { success: false, error: "INVALID_PLAN" };
  const plan = input as Partial<CognitivePlan>;
  const extra = Object.keys(plan).filter((k) => !["version", "family", "intent", "items"].includes(k));
  if (plan.version !== 2 || extra.length || !Array.isArray(plan.items) || !plan.family)
    return { success: false, error: "INVALID_PLAN" };
  if (!(plan.family in FAMILY_QUESTION)) return { success: false, error: "UNKNOWN_FAMILY" };
  if (plan.items.length === 0 || plan.items.length > 6) return { success: false, error: "PLAN_SIZE" };
  const states = epistemicContent(facts, plan.family);
  const seen = new Set<string>();
  for (const item of plan.items) {
    if (typeof item !== "object" || item === null || Object.keys(item).sort().join() !== "component,layer")
      return { success: false, error: "INVALID_ITEM" };
    const declaration = COGNITIVE_REGISTRY[item.component as CognitiveComponentId];
    if (!declaration) return { success: false, error: "COMPONENT_NOT_ALLOWLISTED" };
    if (seen.has(item.component)) return { success: false, error: "DUPLICATE_COMPONENT" };
    seen.add(item.component);
    if (![1, 2, 3, 4].includes(item.layer)) return { success: false, error: "INVALID_LAYER" };
    if (!compatible(declaration, plan.family)) return { success: false, error: "FAMILY_INCOMPATIBLE" };
    if (!declaration.requires(facts)) return { success: false, error: "DATA_UNAVAILABLE" };
    if ([...states].some((s) => !declaration.epistemicStates.includes(s) && declaration.shapes !== "ANY"))
      return { success: false, error: "EPISTEMIC_STATE_UNSUPPORTED" };
  }
  return { success: true, plan: plan as CognitivePlan };
}
