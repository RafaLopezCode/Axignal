import type { RuntimeProjection } from "./runtime-projection";

export type RuntimeTemporalItem = RuntimeProjection["temporalHistory"]["items"][number];

export function orderedTemporalHistory(
  projection: RuntimeProjection,
): RuntimeTemporalItem[] {
  return [...projection.temporalHistory.items].sort(
    (a, b) =>
      Date.parse(b.observedAt) - Date.parse(a.observedAt) ||
      a.observationId.localeCompare(b.observationId),
  );
}

export function temporalHistoryForSource(
  projection: RuntimeProjection,
  sourceRefs?: readonly string[],
): RuntimeTemporalItem[] {
  const ordered = orderedTemporalHistory(projection);
  if (!sourceRefs?.length) return ordered;
  const allowed = new Set(sourceRefs);
  return ordered.filter((item) => allowed.has(item.sourceRef));
}
