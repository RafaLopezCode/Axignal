import { productGuideAnswer, productGuideCatalog } from "./axent-product-guide";
import type { Locale } from "./languages";
import { translate } from "./copy-catalog";
import type { RuntimeProjection } from "./runtime-projection";
import type { CognitiveReadingRequest } from "./subscriber-presentation";
import type { CognitivePlan } from "./cognition/compose";

export type RuntimeAnswer = {
  revision?: string;
  cognition?: { request: CognitiveReadingRequest; plan: CognitivePlan };
  organizationId: string;
  contextId: string;
  signalIds: string[];
  publicUnderstandingReportId?: string;
  intent: "known" | "changed" | "why" | "unknown" | "evidence" | "research" | "act";
  summary: string;
  known: string[];
  openQuestions: string[];
  evidenceBasis: string[];
  evidenceLimits?: string[];
  researchPlan: string[];
  passages: string[];
  action: "evidence" | "focus" | "unknown" | "research-unavailable";
  sourceRefs: string[];
  observedAt: string[];
  currentness: string[];
  /** Present when tenant-grounded AXENT answered: claims, evidence, research request. */
  grounding?: unknown;
  productGuide?: { version: string; label: string; topic: string; authority: string[]; followUps: string[] };
  /** Compact memory of this turn, sent back with the next question. */
  memory?: Record<string, unknown>;
};

/** What a question asks, in any of the six languages (same rules for every AXENT path). */
export function intentOf(prompt: string): RuntimeAnswer["intent"] {
  const unknownIntent =
    /unknown|desconoc|abiert|open|offen|ouvert|unbekannt|inconnu|sconosciut|em aberto|eclaircir|éclaircir|aperto/i.test(prompt);
  // "How do you know" asks for the basis; "what do you know" asks for the content.
  const evidenceIntent =
    /evidenc|fuente|source|c[oó]mo (lo )?sab|how do you know|woher|wei(ß|ss)t du das|comment le sais|come lo sai|quelle|preuve|fonte|fundament|basis/i.test(prompt);
  const researchIntent =
    /investig|research|recherch|ricerc|indag|nächst/i.test(prompt);
  // "How do I fix it", "what can I do", "how do I improve": the reader wants to act.
  const actIntent =
    /corrij|corregi|arregl|mejor(o|ar)|soluc|qu[eé] (puedo|debo) hacer|qu[eé] hago|c[oó]mo (lo )?(hago|consigo|aparezco)|fix|improve|solve|what (can|should) i do|how (do|can) i|beheb|verbesser|was kann ich|corrig|amélior|que faire|correg|miglior|cosa posso|corrijo|melhor|o que fa[cç]o|posso fazer|puis-je faire/i.test(prompt);
  const whyIntent = /por qué|why|import|warum|pourquoi|perché|porquê/i.test(prompt);
  const changedIntent = /camb|chang|mud|änder/i.test(prompt);
  return actIntent
    ? "act"
    : researchIntent
    ? "research"
    : unknownIntent
      ? "unknown"
      : evidenceIntent
        ? "evidence"
        : whyIntent
          ? "why"
          : changedIntent
            ? "changed"
            : "known";
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

export function explainRuntime(
  projection: RuntimeProjection,
  prompt: string,
  selectedId?: string,
  locale: Locale = "es",
): RuntimeAnswer {
  const selected = selectedId
    ? projection.nodes.filter((signal) => signal.id === selectedId)
    : projection.nodes;
  if (selectedId && !selected.length) throw new Error("FOCUS_OUTSIDE_PROJECTION");

  const guide = productGuideAnswer(projection, prompt, locale);
  if (guide) return guide;
  const t = (es: string, en: string) => translate(es, en, locale);
  const intent = intentOf(prompt);
  const researchIntent = intent === "research", unknownIntent = intent === "unknown",
    evidenceIntent = intent === "evidence", whyIntent = intent === "why", changedIntent = intent === "changed";

  const known = unique(selected.map((signal) => signal.interpretation));
  const openQuestions = unique(
    selected.flatMap((signal) => [signal.uncertainty, ...signal.unknowns]),
  );
  const evidenceBasis = unique(
    selected.flatMap((signal) =>
      signal.evidenceNarrative.steps.map((step) => step.label),
    ),
  );
  const sourceRefs = unique(selected.flatMap((signal) => signal.sourceRefs));
  const observedAt = unique(selected.map((signal) => signal.observedAt));
  const currentness = unique(selected.map((signal) => signal.currentness));

  const changed = projection.today.items
    .filter((item) => selected.some((signal) => signal.id === item.xignalId))
    .map((item) => item.whatChanged);
  const passages = researchIntent || unknownIntent
    ? openQuestions
    : evidenceIntent
      ? evidenceBasis
      : whyIntent
        ? selected.map((signal) => signal.whyAttention)
        : changedIntent
          ? changed
          : known;

  const summary = researchIntent
    ? t(
        "La evidencia actual permite delimitar qué sabemos y qué sigue abierto. Lo siguiente es un plan propuesto de investigación; no se ha ejecutado ninguna investigación nueva.",
        "Current evidence lets us separate what is known from what remains open. The following is a proposed research plan; no new research has been executed.",
      )
    : unknownIntent
      ? t(
          "La lectura actual conserva límites explícitos: lo no observado sigue abierto y no se interpreta como falso.",
          "The current reading preserves explicit limits: what has not been observed remains open and is not interpreted as false.",
        )
      : evidenceIntent
        ? !evidenceBasis.length && !sourceRefs.length ? productGuideCatalog.locales[locale].noEvidence : t(
            "Esta lectura se sostiene únicamente en la evidencia autorizada y trazable que figura a continuación.",
            "This reading is supported only by the authorized, traceable evidence shown below.",
          )
        : changedIntent
          ? changed.length
            ? t(
                "Hay una observación registrada en Hoy para este contexto. Eso describe una nueva lectura, no prueba por sí solo cuándo ocurrió un cambio económico.",
                "There is an observation recorded in Today for this context. That describes a new reading; by itself it does not prove when an economic change occurred.",
              )
            : t(
                "No hay una novedad registrada en Hoy para este contexto. La ausencia de novedad no invalida observaciones anteriores.",
                "There is no novelty recorded in Today for this context. Absence of novelty does not invalidate earlier observations.",
              )
          : whyIntent
            ? t(
                "AXIGNAL prioriza esta señal porque la evidencia gobernada permite sostener una lectura concreta, manteniendo visibles sus límites.",
                "AXIGNAL prioritizes this signal because governed evidence supports a concrete reading while keeping its limits visible.",
              )
            : t(
                "AXIGNAL puede sostener la lectura conocida que sigue, pero no extiende esa evidencia a superficies que no ha observado.",
                "AXIGNAL can support the known reading below, but it does not extend that evidence to surfaces it has not observed.",
              );

  const researchPlan = openQuestions.length
    ? [
        t(
          "1. Contrastar la principal incertidumbre con una fuente pública adicional y autorizada.",
          "1. Check the leading uncertainty against an additional authorized public source.",
        ),
        t(
          "2. Reobservar el mismo alcance más adelante para distinguir persistencia de cambio.",
          "2. Reobserve the same scope later to distinguish persistence from change.",
        ),
        t(
          "3. Buscar corroboración pública independiente antes de elevar cualquier conclusión potencial.",
          "3. Seek independent public corroboration before promoting any potential conclusion.",
        ),
      ]
    : [];

  return {
    organizationId: projection.organization.id,
    contextId: projection.context.id,
    signalIds: selected.map((signal) => signal.id),
    intent,
    summary,
    known,
    openQuestions,
    evidenceBasis,
    researchPlan,
    passages: unique(passages),
    action: researchIntent
      ? "research-unavailable"
      : unknownIntent
        ? "unknown"
        : evidenceIntent
          ? "evidence"
          : "focus",
    sourceRefs,
    observedAt,
    currentness,
  };
}


/** Read-only demo explanations: no authorization grants, network, model or research. */
export function explainIllustrative(projection: RuntimeProjection, prompt: string, selectedId: string | undefined, locale: Locale): RuntimeAnswer {
  const answer = explainRuntime(projection, prompt, selectedId, locale);
  if (answer.productGuide) return answer;
  return { ...answer, summary: translate("Explicación ilustrativa de datos ficticios; sin investigación en vivo. ", "Illustrative explanation of fictional data; without live research. ", locale) + answer.summary };
}
