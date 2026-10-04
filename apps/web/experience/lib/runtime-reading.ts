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
