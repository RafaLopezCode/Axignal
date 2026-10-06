/**
 * Adapter from the governed subscriber projection to the cognitive read model.
 * It deliberately has no dependency on the illustrative factsAt() fixture.
 */
import type { Copy } from "../locale";
import type { FamilyId } from "../projection";
import type { Currentness, FactSource, FamilyFacts, OpportunityFacts } from "./facts";
import type { RuntimeCognition, RuntimeProjection, RuntimeSignal } from "../runtime-projection";

export type RuntimeFactSource = FactSource & {
  sourceRef: string;
  provenanceRef: string;
  currentness: Currentness;
  currentnessEvaluatedAt: string;
};

export type RuntimeCognitiveSignal = RuntimeSignal & {
  currentnessEvaluatedAt: string;
};

export type RuntimeOpportunityFact = OpportunityFacts & {
  familyId: "value" | "demand";
  opportunityFamily?: RuntimeCognition["opportunities"][number]["opportunityFamily"];
  currentness: Currentness;
  currentnessEvaluatedAt: string;
  whyLooked: Copy[];
  matchBasis?: Copy[];
};

/** Extra runtime lineage remains available while the result stays FamilyFacts-compatible. */
export type RuntimeFamilyFacts = Omit<FamilyFacts, "sources" | "opportunities"> & {
  sources: RuntimeFactSource[];
  signals: RuntimeCognitiveSignal[];
  opportunities?: RuntimeOpportunityFact[];
};

const copy = (value: string): Copy => ({ es: value, en: value });
const UNKNOWN_COPY: Copy = { es: "Desconocido", en: "Unknown" };

function instant(value: string): number | null {
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function requiredInstant(value: string, field: string): number {
  const parsed = instant(value);
  if (parsed === null) throw new RangeError(`${field} must be a valid ISO date or timestamp`);
  return parsed;
}

function effectiveCurrentness(
  currentness: Currentness,
  evaluatedAt: string,
  cutoff: number,
): Currentness {
  const evaluation = instant(evaluatedAt);
  return evaluation === null || evaluation > cutoff ? "UNKNOWN" : currentness;
}

function emptyFacts(family: FamilyId): RuntimeFamilyFacts {
  return {
    sources: [],
    signals: [],
    ...(family === "value" || family === "demand" ? { opportunities: [] } : {}),
  };
}

function sourceFact(source: RuntimeCognition["sources"][number], cutoff: number): RuntimeFactSource {
  return {
    id: source.id,
    title: copy(source.title),
    observedAt: source.observedAt,
    instrument: copy(source.instrument),
    limitation: copy(source.limitation),
    sourceRef: source.sourceRef,
    provenanceRef: source.provenanceRef,
    currentness: effectiveCurrentness(source.currentness, source.currentnessEvaluatedAt, cutoff),
    currentnessEvaluatedAt: source.currentnessEvaluatedAt,
  };
}

function isObservedBy(value: string, cutoff: number): boolean {
  const observedAt = instant(value);
  return observedAt !== null && observedAt <= cutoff;
}

function familySignals(
  projection: RuntimeProjection,
  cognition: RuntimeCognition,
  family: FamilyId,
  cutoff: number,
  availableSourceRefs: Set<string>,
  availableSourceIds: Set<string>,
): RuntimeCognitiveSignal[] {
  const nodesById = new Map(projection.nodes.map((node) => [node.id, node]));
  const output: RuntimeCognitiveSignal[] = [];

  for (const entry of cognition.signals) {
    if (entry.familyId !== family) continue;
    const node = nodesById.get(entry.id);
    if (!node || !isObservedBy(node.observedAt, cutoff) || node.sourceRefs.length === 0) continue;
    if (node.observationSupportRefs.length > 0) {
      if (node.observationSupportRefs.some((sourceId) => !availableSourceIds.has(sourceId))) continue;
    } else if (node.sourceRefs.some((sourceRef) => !availableSourceRefs.has(sourceRef))) {
      continue;
    }

    output.push({
      ...node,
      // cognition.asOf is the evaluation time for signal currentness. A later
      // evaluation cannot establish currentness in an earlier historical cut.
      currentness: effectiveCurrentness(node.currentness, cognition.asOf, cutoff),
      currentnessEvaluatedAt: cognition.asOf,
    });
  }

  return output;
}

function opportunityFact(
  opportunity: RuntimeCognition["opportunities"][number],
  currentness: Currentness,
): RuntimeOpportunityFact {
  return {
    id: opportunity.id,
    familyId: opportunity.familyId,
    ...(opportunity.opportunityFamily ? { opportunityFamily: opportunity.opportunityFamily } : {}),
    title: copy(opportunity.title),
    buyer: opportunity.buyer === null ? UNKNOWN_COPY : copy(opportunity.buyer),
    market: copy(opportunity.market),
    form: copy(opportunity.form),
    deadline: opportunity.deadline,
    epistemic: opportunity.epistemic,
    capability: {
      label: copy(opportunity.capability.label),
      excerpt: copy(opportunity.capability.excerpt),
      sourceId: opportunity.capability.sourceId,
    },
    demand: {
      label: copy(opportunity.demand.label),
      code: opportunity.demand.code,
      sourceId: opportunity.demand.sourceId,
    },
    known: opportunity.known.map((item) => ({ label: copy(item.label), value: copy(item.value) })),
    unknown: opportunity.unknown.map(copy),
    whyPotential: copy(opportunity.whyPotential),
    whyLooked: opportunity.whyLooked.map(copy),
    ...(opportunity.matchBasis ? { matchBasis: opportunity.matchBasis.map(copy) } : {}),
    observedAt: opportunity.observedAt,
    currentness,
    currentnessEvaluatedAt: opportunity.currentnessEvaluatedAt,
  };
}

/**
 * Build family facts solely from the real runtime projection.
 *
 * Data observed after `asOf` is excluded. When the currentness evaluation is
 * later than the cut, currentness becomes UNKNOWN while its evaluation time and
 * provenance are retained. A requested cut later than the projection's own
 * `cognition.asOf` cannot extend the projection's knowledge horizon.
 */
export function runtimeFactsAt(
  projection: RuntimeProjection,
  family: FamilyId,
  asOf: string,
): RuntimeFamilyFacts {
  const requestedCutoff = requiredInstant(asOf, "asOf");
  const cognition = projection.cognition;
  if (!cognition) return emptyFacts(family);

  const projectionAsOf = instant(cognition.asOf);
  if (projectionAsOf === null) return emptyFacts(family);
  const cutoff = Math.min(requestedCutoff, projectionAsOf);

  const eligibleSources = cognition.sources.filter((source) => isObservedBy(source.observedAt, cutoff));
  const sourceById = new Map(eligibleSources.map((source) => [source.id, source]));
  const sourceIds = new Set<string>();
  if (family === "organization") {
    // This family is the provenance trail itself; every source in the
    // authorized projection context is relevant even without an attributed node.
    for (const source of eligibleSources) sourceIds.add(source.id);
  }

  const sourcesByRef = new Map<string, RuntimeCognition["sources"]>();
  for (const source of eligibleSources) {
    const refs = sourcesByRef.get(source.sourceRef) ?? [];
    refs.push(source);
    sourcesByRef.set(source.sourceRef, refs);
  }

  const nodesById = new Map(projection.nodes.map((node) => [node.id, node]));
  for (const signal of cognition.signals) {
    if (signal.familyId !== family) continue;
    const node = nodesById.get(signal.id);
    if (!node || !isObservedBy(node.observedAt, cutoff) || node.sourceRefs.length === 0) continue;
    if (node.observationSupportRefs.length > 0) {
      if (node.observationSupportRefs.every((sourceId) => sourceById.has(sourceId))) {
        for (const sourceId of node.observationSupportRefs) sourceIds.add(sourceId);
      }
    } else if (node.sourceRefs.every((ref) => sourcesByRef.has(ref))) {
      for (const ref of node.sourceRefs) {
        for (const source of sourcesByRef.get(ref) ?? []) sourceIds.add(source.id);
      }
    }
  }

  const opportunities: RuntimeOpportunityFact[] = [];
  if (family === "value" || family === "demand") {
    for (const opportunity of cognition.opportunities) {
      if (opportunity.familyId !== family || !isObservedBy(opportunity.observedAt, cutoff)) continue;
      const capabilitySource = sourceById.get(opportunity.capability.sourceId);
      const demandSource = sourceById.get(opportunity.demand.sourceId);
      // An opportunity is not intelligible without both sides of its basis.
      if (!capabilitySource || !demandSource) continue;

      sourceIds.add(capabilitySource.id);
      sourceIds.add(demandSource.id);
      opportunities.push(
        opportunityFact(
          opportunity,
          effectiveCurrentness(
            opportunity.currentness,
            opportunity.currentnessEvaluatedAt,
            cutoff,
          ),
        ),
      );
    }
  }

  const signals = familySignals(
    projection,
    cognition,
    family,
    cutoff,
    new Set(eligibleSources.map((source) => source.sourceRef)),
    new Set(eligibleSources.map((source) => source.id)),
  );
  return {
    sources: eligibleSources
      .filter((source) => sourceIds.has(source.id))
      .map((source) => sourceFact(source, cutoff)),
    signals,
    ...(family === "value" || family === "demand" ? { opportunities } : {}),
  };
}
