import type { RuntimeProjection } from "./runtime-projection";

function materialProjection(projection: RuntimeProjection) {
  return {
    organizationId: projection.organization.id,
    nodes: projection.nodes
      .map((signal) => ({
        title: signal.title,
        whyAttention: signal.whyAttention,
        interpretation: signal.interpretation,
        uncertainty: signal.uncertainty,
        epistemicState: signal.epistemicState,
        evidenceAccess: signal.evidenceAccess,
        sourceRefs: [...signal.sourceRefs].sort(),
        unknowns: [...signal.unknowns].sort(),
        evidence: signal.evidenceNarrative.steps.map((step) => ({
          kind: step.kind,
          label: step.label,
          sourceRef: step.sourceRef,
          artifactVerified: step.artifactVerified,
        })),
      }))
      .sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b))),
  };
}

export function hasMaterialReobservationChange(
  before: RuntimeProjection,
  after: RuntimeProjection,
): boolean {
  return JSON.stringify(materialProjection(before)) !== JSON.stringify(materialProjection(after));
}

export function latestObservationStatus(
  projection: RuntimeProjection,
): { observedAt: string; currentness: string } | null {
  const latest = [...projection.nodes]
    .filter((signal) => Number.isFinite(Date.parse(signal.observedAt)))
    .sort((a, b) => Date.parse(b.observedAt) - Date.parse(a.observedAt))[0];
  return latest
    ? { observedAt: latest.observedAt, currentness: latest.currentness }
    : null;
}
