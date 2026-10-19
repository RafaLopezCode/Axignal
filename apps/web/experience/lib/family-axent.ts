/**
 * AXENT about one family, when no finding is selected: the reader is looking at a family
 * (Visibility, Value…), so that is the context, never "the whole organization" by default.
 * Built from the family's own findings — the most telling first, what is still unknown, what
 * changed, what to do and what to look into — in the reader's language and deterministic.
 * A question these findings cannot answer returns null, so the grounded runtime answers it
 * with the family named in the question; in the illustrative demo it says so instead.
 */
import { fill, type Insight } from "./observatory";
import { intentOf, type RuntimeAnswer } from "./runtime-axent";

type Translate = (es: string, en: string) => string;

const unique = (values: Array<string | null | undefined>, exclude: Set<string> = new Set()) => {
  const seen = new Set(exclude);
  return values.map(v => v?.trim() ?? "").filter(v => v && !seen.has(v) && (seen.add(v), true));
};

/** "What do you know" asks for the content itself, not for something more specific. */
export const asksWhatIsKnown = (prompt: string) =>
  /qu[eé] sabe|what do you know|was wei(ß|ss)t|que sais|cosa sai|o que sabe|resum|summar|zusammenfass|résum|riassum|lo m[aá]s importante|most important|wichtigste|plus important|più importante|mais importante/i.test(prompt);

/** A question none of the fixed intents reads: free text for the grounded runtime. */
export const isFreeQuestion = (prompt: string) => intentOf(prompt) === "known" && !asksWhatIsKnown(prompt);

export function explainFamily({ family, insights, prompt, organizationId, contextId, t, illustrative }: {
  /** The family's name as the reader sees it ("Visibilidad"). */
  family: string;
  /** The findings of that family, in the order the reader sees them. */
  insights: Insight[];
  prompt: string;
  organizationId: string;
  contextId: string;
  t: Translate;
  illustrative: boolean;
}): RuntimeAnswer | null {
  // "What is most important" asks for the family's content, even though it says "important".
  const summarizing = asksWhatIsKnown(prompt);
  const intent = summarizing ? "known" : intentOf(prompt);
  const known = insights.filter(i => i.lane !== "unknown" && !i.id.startsWith("CHANGE:"));
  const unknowns = insights.filter(i => i.lane === "unknown");
  const changes = insights.filter(i => i.id.startsWith("CHANGE:") || i.previous !== null);
  const top = known.slice(0, 3);
  const name = { family };
  let summary: string;
  let items: string[] = [];
  let open: string[] = [];
  // A free question goes to the grounded runtime even when the family holds nothing yet.
  if (!illustrative && !summarizing && intent === "known") return null;
  if (!insights.length) {
    summary = fill(t("En {family} todavía no hay hallazgos observados. Una ausencia aquí no demuestra ausencia en el mundo.", "There are no observed findings in {family} yet. An absence here does not prove an absence in the world."), name);
  } else if (intent === "act") {
    const steps = unique(top.flatMap(i => i.actions?.length ? i.actions.slice(0, 2) : i.proposal ? [i.proposal] : [])).slice(0, 5);
    summary = steps.length
      ? fill(t("En {family}, por dónde empezar (de los hallazgos más importantes):", "In {family}, where to start (from the most important findings):"), name)
      : fill(t("Los hallazgos de {family} no traen un paso concreto. Abre uno y pregunta «Qué puedo hacer» para verlo con su contexto.", "The findings in {family} carry no concrete step. Open one and ask “What can I do” to see it in its context."), name);
    items = steps;
  } else if (intent === "research") {
    summary = fill(t("En {family}, lo que investigaría a continuación:", "In {family}, what I would look into next:"), name);
    items = unique([...top.flatMap(i => i.research?.slice(0, 1) ?? []), ...unknowns.map(i => i.headline)]).slice(0, 5);
    if (!items.length) items = [t("Si cambia en la próxima observación y frente a qué.", "Whether it changes at the next observation, and against what.")];
  } else if (intent === "unknown") {
    summary = unknowns.length
      ? fill(t("En {family}, esto sigue abierto:", "In {family}, this remains open:"), name)
      : fill(t("En {family} no hay incógnitas declaradas en esta lectura.", "No unknowns are declared in {family} in this reading."), name);
    items = unknowns.map(i => i.headline);
  } else if (intent === "changed") {
    summary = changes.length
      ? fill(t("En {family}, esto cambió desde la lectura anterior:", "In {family}, this changed since the previous reading:"), name)
      : fill(t("En {family} no hay una lectura anterior comparable, así que no se declara ningún cambio.", "There is no comparable earlier reading in {family}, so no change is declared."), name);
    items = changes.map(i => i.previous !== null ? fill(t("{now} (antes: {before})", "{now} (before: {before})"), { now: i.headline, before: i.previous }) : i.headline);
  } else if (intent === "why") {
    summary = fill(t("Por qué importa lo observado en {family}:", "Why what was observed in {family} matters:"), name);
    items = unique(top.map(i => i.why || i.headline));
  } else if (intent === "evidence") {
    const sources = unique(insights.flatMap(i => i.sources.map(s => s.label)));
    summary = fill(t("Lo observado en {family} se apoya en {n} fuentes; abre un hallazgo para ver cada una con su fecha:", "What was observed in {family} rests on {n} sources; open a finding to see each with its date:"), { ...name, n: sources.length });
    items = sources.slice(0, 8);
  } else if (summarizing) {
    summary = fill(t("En {family}, lo más importante:", "In {family}, the most important:"), name);
    items = top.map(i => i.headline);
    open = unknowns.slice(0, 2).map(i => i.headline);
  } else {
    // A free question: the grounded runtime answers it in this family's context.
    if (!illustrative) return null;
    summary = fill(t("Los hallazgos de {family} no tienen un dato que responda exactamente a eso. Lo más importante que sí establecen:", "The findings in {family} hold no data that answers exactly that. The most important they do establish:"), name);
    items = top.map(i => i.headline);
  }
  return {
    organizationId, contextId, signalIds: [], intent, summary,
    known: unique(items, new Set([summary])), openQuestions: unique(open), evidenceBasis: [], evidenceLimits: [],
    researchPlan: [], passages: [], action: "focus",
    sourceRefs: [], observedAt: [], currentness: [],
  };
}

/** The question sent to the grounded runtime, framed with what the reader is looking at. */
export function framed(question: string, context: string): string {
  return `${context}: ${question}`.slice(0, 1000);
}
