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
  intent: "known" | "changed" | "why" | "unknown" | "evidence" | "research";
  summary: string;
  known: string[];
  openQuestions: string[];
  evidenceBasis: string[];
  researchPlan: string[];
  passages: string[];
  action: "evidence" | "focus" | "unknown" | "research-unavailable";
  sourceRefs: string[];
  observedAt: string[];
  currentness: string[];
};

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

  const t = (es: string, en: string) => translate(es, en, locale);
  const unknownIntent =
    /unknown|desconoc|abiert|open|unbekannt|inconnu|sconosciut/i.test(prompt);
  const evidenceIntent =
    /evidenc|fuente|source|sabes|sabe|know|quelle|preuve|fonte/i.test(prompt);
  const researchIntent =
    /investig|research|recherch|ricerc|indag|nächst/i.test(prompt);
  const whyIntent = /por qué|why|import|warum|pourquoi|perché|porquê/i.test(prompt);
  const changedIntent = /camb|chang|mud|änder/i.test(prompt);
  const intent: RuntimeAnswer["intent"] = researchIntent
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
        ? t(
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
