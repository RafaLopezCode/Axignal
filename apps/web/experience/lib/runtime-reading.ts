import type { RuntimeProjection, RuntimeSignal } from "./runtime-projection";

const epistemicRank: Record<RuntimeSignal["epistemicState"], number> = {
  OBSERVED: 0,
  POTENTIAL: 1,
  UNKNOWN: 2,
};

const currentnessRank: Record<RuntimeSignal["currentness"], number> = {
  CURRENT: 0,
  STALE: 1,
  HISTORICAL: 2,
  UNKNOWN: 3,
};

function observedTime(signal: RuntimeSignal): number {
  const value = Date.parse(signal.observedAt);
  return Number.isFinite(value) ? value : Number.NEGATIVE_INFINITY;
}

export function orderedSignals(nodes: readonly RuntimeSignal[]): RuntimeSignal[] {
  return [...nodes].sort((a, b) => {
    const epistemic = epistemicRank[a.epistemicState] - epistemicRank[b.epistemicState];
    if (epistemic) return epistemic;
    const currentness = currentnessRank[a.currentness] - currentnessRank[b.currentness];
    if (currentness) return currentness;
    return observedTime(b) - observedTime(a) || a.id.localeCompare(b.id);
  });
}

export function signalGroups(nodes: readonly RuntimeSignal[]) {
  const ordered = orderedSignals(nodes);
  return (["OBSERVED", "POTENTIAL", "UNKNOWN"] as const)
    .map((state) => ({
      state,
      signals: ordered.filter((signal) => signal.epistemicState === state),
    }))
    .filter((group) => group.signals.length > 0);
}

export function latestObservedSignal(
  projection: Pick<RuntimeProjection, "nodes">,
): RuntimeSignal | null {
  return [...projection.nodes].sort(
    (a, b) => observedTime(b) - observedTime(a) || a.id.localeCompare(b.id),
  )[0] ?? null;
}

export type FirstMapBrief = {
  isSparse: boolean;
  signalCount: number;
  observedCount: number;
  sourceCount: number;
  observationCount: number;
  currentCount: number;
  primarySignal: RuntimeSignal | null;
  openQuestions: string[];
};

export function firstMapBrief(
  projection: Pick<RuntimeProjection, "nodes" | "temporalHistory">,
): FirstMapBrief {
  const ordered = orderedSignals(projection.nodes);
  const sourceRefs = new Set(
    projection.nodes.flatMap((signal) => signal.sourceRefs),
  );
  const openQuestions = [
    ...new Set(
      projection.nodes.flatMap((signal) => [
        signal.uncertainty,
        ...signal.unknowns,
      ]),
    ),
  ].filter(Boolean);

  return {
    isSparse: projection.nodes.length <= 2,
    signalCount: projection.nodes.length,
    observedCount: projection.nodes.filter(
      (signal) => signal.epistemicState === "OBSERVED",
    ).length,
    sourceCount: sourceRefs.size,
    observationCount: projection.temporalHistory.items.length,
    currentCount: projection.nodes.filter(
      (signal) => signal.currentness === "CURRENT",
    ).length,
    primarySignal: ordered[0] ?? null,
    openQuestions,
  };
}
