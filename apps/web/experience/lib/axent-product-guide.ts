import catalog from "./axent-product-guide.json";
import type { Locale } from "./languages";
import type { RuntimeProjection } from "./runtime-projection";
import type { RuntimeAnswer } from "./runtime-axent";

export const productGuideCatalog = catalog;
type GuideTopic = "overview" | "value" | "limits";
export function guideTopic(question: string): GuideTopic | null {
  const normalized = question.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[¿?¡!.,:;]+/g, "").trim();
  for (const [topic, patterns] of Object.entries(catalog.patterns)) {
    if (patterns.some(pattern => new RegExp(`^(?:${pattern})$`).test(normalized))) return topic as GuideTopic;
  }
  return null;
}
export function productGuideAnswer(projection: RuntimeProjection, question: string, locale: Locale): RuntimeAnswer | null {
  const topic = guideTopic(question);
  if (!topic) return null;
  const copy = catalog.locales[locale];
  return {
    organizationId: projection.organization.id, contextId: projection.context.id,
    signalIds: [], intent: "known", summary: copy[topic], known: [], openQuestions: [],
    evidenceBasis: [], researchPlan: [], passages: [], action: "unknown", sourceRefs: [],
    observedAt: [], currentness: [], productGuide: {
      version: catalog.version, label: copy.label, topic, authority: catalog.authority, followUps: copy.followUps,
    },
  };
}
