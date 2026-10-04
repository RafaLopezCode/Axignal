import type { RuntimeProjection } from "./runtime-projection";

export type RuntimeAnswer = {
  organizationId: string;
  contextId: string;
  signalIds: string[];
  passages: string[];
  action: "evidence" | "focus" | "unknown" | "research-unavailable";
  sourceRefs: string[];
};
// Bounded read-only explanation. Every economic passage is runtime-authored.
// User words select a reading lens; they are never evidence or a write.
export function explainRuntime(
  projection: RuntimeProjection,
  prompt: string,
  selectedId?: string,
): RuntimeAnswer {
  const selected = selectedId
    ? projection.nodes.filter((s) => s.id === selectedId)
    : projection.nodes;
  if (selectedId && !selected.length)
    throw new Error("FOCUS_OUTSIDE_PROJECTION");
  const unknown =
    /unknown|desconoc|abiert|open|unbekannt|inconnu|sconosciut/i.test(prompt);
  const evidence =
    /evidenc|fuente|source|sabes|sabe|know|quelle|preuve|fonte/i.test(prompt);
  const research = /investig|research|recherch|ricerc|indag|nächst/i.test(prompt);
  const why = /por qué|why|import|warum|pourquoi|perché|porquê/i.test(prompt);
  const changed = /camb|chang|mud|änder/i.test(prompt);
  const passages =
    research || unknown
      ? selected.flatMap((s) => [s.uncertainty, ...s.unknowns])
      : evidence
        ? selected.flatMap((s) =>
            s.evidenceNarrative.steps.map((step) => step.label),
          )
        : why
          ? selected.map((s) => s.whyAttention)
          : changed
            ? projection.today.items
                .filter((item) => selected.some((s) => s.id === item.xignalId))
                .map((item) => item.whatChanged)
            : selected.map((s) => s.interpretation);
  return {
    organizationId: projection.organization.id,
    contextId: projection.context.id,
    signalIds: selected.map((s) => s.id),
    passages: [...new Set(passages)],
    action: research
      ? "research-unavailable"
      : unknown
        ? "unknown"
        : evidence
          ? "evidence"
          : "focus",
    sourceRefs: [...new Set(selected.flatMap((s) => s.sourceRefs))],
  };
}
