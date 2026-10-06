import assert from "node:assert/strict";
import test from "node:test";

import { factsAt } from "../lib/cognition/facts";
import { runtimeFactsAt } from "../lib/cognition/runtime-facts";
import { runtimeProjectionSchema } from "../lib/runtime-projection";

const baseCognition = {
  asOf: "2026-10-05T12:00:00Z",
  sources: [
    {
      id: "source:capability",
      title: "Public capability sheet",
      observedAt: "2026-10-04T09:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: "2026-10-05T12:00:00Z",
      instrument: "Public document, deterministic reading",
      limitation: "A declaration does not establish available capacity.",
      sourceRef: "https://supplier.example/capability",
      provenanceRef: "basis:capability:01",
    },
    {
      id: "source:demand",
      title: "Buyer project notice",
      observedAt: "2026-10-04T10:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: "2026-10-05T12:00:00Z",
      instrument: "Public project notice",
      limitation: "Commercial fit and eligibility remain unknown.",
      sourceRef: "https://buyer.example/project",
      provenanceRef: "basis:demand:01",
    },
  ],
  signals: [{ id: "signal:opportunity", familyId: "demand" }],
  opportunities: [
    {
      id: "opportunity:1",
      familyId: "demand",
      opportunityFamily: "PRIVATE_PROJECT_SIGNALS",
      title: "Potential project relevance",
      buyer: "Buyer organization",
      market: "Spain · scope stated by source",
      form: "Private project signal",
      deadline: null,
      epistemic: "POTENTIAL",
      capability: {
        label: "Thermal renovation",
        excerpt: "The organization describes thermal renovation work.",
        sourceId: "source:capability",
      },
      demand: {
        label: "Building envelope works",
        code: null,
        sourceId: "source:demand",
      },
      known: [{ label: "Project stage", value: "Announced" }],
      unknown: ["Available capacity", "Commercial access"],
      matchBasis: ["CAPABILITY_NEED_RELEVANCE", "PROJECT_REQUIREMENT_RELEVANCE"],
      whyPotential: "A declared capability could address the source-stated need.",
      whyLooked: ["A source-stated project need overlaps the declared capability."],
      observedAt: "2026-10-04T11:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: "2026-10-05T12:00:00Z",
    },
  ],
};

function signal(overrides: Record<string, unknown> = {}) {
  return {
    id: "signal:opportunity",
    nodeKind: "XIGNAL",
    title: "Potential project relevance",
    whyAttention: "The available evidence warrants attention.",
    interpretation: "A declared capability could address a stated need.",
    uncertainty: "Commercial fit remains unknown.",
    epistemicState: "POTENTIAL",
    currentness: "CURRENT",
    observedAt: "2026-10-04T11:00:00Z",
    evidenceAccess: "AVAILABLE",
    sourceRefs: ["https://supplier.example/capability"],
    observationSupportRefs: ["source:capability"],
    unknowns: ["Available capacity"],
    evidenceNarrative: {
      xignalId: "signal:opportunity",
      focusStepId: "signal:opportunity:step:xignal",
      steps: [
        {
          id: "signal:opportunity:step:xignal",
          kind: "XIGNAL",
          label: "Potential project relevance",
          sourceRef: null,
          observedAt: "2026-10-04T11:00:00Z",
          currentness: "CURRENT",
          artifactVerified: null,
        },
        {
          id: "signal:opportunity:step:source",
          kind: "OBSERVATION",
          label: "Public capability statement",
          sourceRef: "https://supplier.example/capability",
          observedAt: "2026-10-04T09:00:00Z",
          currentness: "CURRENT",
          artifactVerified: null,
        },
      ],
    },
    ...overrides,
  };
}

function projection(cognition: unknown, nodes: unknown[] = [signal()]) {
  return runtimeProjectionSchema.parse({
    realityLevel: "CONTROLLED_ECONOMIC_PRODUCT_PROOF",
    runtimeCodeSha: "sha",
    lifecycleStatus: "LIVE",
    context: { id: "focus:runtime", label: "Runtime focus" },
    organization: { id: "org:norte", name: "Norte Renovable" },
    nodes,
    cognition,
    temporalHistory: { disposition: "EMPTY", items: [] },
    today: { disposition: "READY", items: [] },
    reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  });
}

test("maps governed opportunities and keeps source provenance intact", () => {
  const facts = runtimeFactsAt(projection(baseCognition), "demand", "2026-10-05T12:00:00Z");

  assert.equal(facts.opportunities?.length, 1);
  assert.equal(facts.opportunities?.[0]?.epistemic, "POTENTIAL");
  assert.equal(facts.opportunities?.[0]?.currentness, "CURRENT");
  assert.equal(facts.opportunities?.[0]?.opportunityFamily, "PRIVATE_PROJECT_SIGNALS");
  assert.equal(facts.opportunities?.[0]?.observedAt, "2026-10-04T11:00:00Z");
  assert.deepEqual(facts.opportunities?.[0]?.unknown.map((item) => item.en), [
    "Available capacity",
    "Commercial access",
  ]);
  assert.deepEqual(facts.opportunities?.[0]?.matchBasis?.map((item) => item.en), [
    "CAPABILITY_NEED_RELEVANCE",
    "PROJECT_REQUIREMENT_RELEVANCE",
  ]);
  assert.deepEqual(
    facts.sources.map(({ id, sourceRef, provenanceRef, currentness, currentnessEvaluatedAt }) => ({
      id,
      sourceRef,
      provenanceRef,
      currentness,
      currentnessEvaluatedAt,
    })),
    [
      {
        id: "source:capability",
        sourceRef: "https://supplier.example/capability",
        provenanceRef: "basis:capability:01",
        currentness: "CURRENT",
        currentnessEvaluatedAt: "2026-10-05T12:00:00Z",
      },
      {
        id: "source:demand",
        sourceRef: "https://buyer.example/project",
        provenanceRef: "basis:demand:01",
        currentness: "CURRENT",
        currentnessEvaluatedAt: "2026-10-05T12:00:00Z",
      },
    ],
  );
  assert.equal(facts.sources[0]?.instrument.en, "Public document, deterministic reading");
  assert.equal(facts.sources[0]?.limitation.en, "A declaration does not establish available capacity.");
  assert.equal(facts.signals[0]?.id, "signal:opportunity");
});

test("future observations and post-cut currentness evaluations cannot leak into a historical cut", () => {
  const cognition = {
    ...baseCognition,
    asOf: "2026-10-06T12:00:00Z",
    sources: baseCognition.sources.map((source) =>
      source.id === "source:demand"
        ? { ...source, observedAt: "2026-10-06T09:00:00Z" }
        : source,
    ),
    opportunities: baseCognition.opportunities.map((item) => ({
      ...item,
      currentnessEvaluatedAt: "2026-10-06T12:00:00Z",
    })),
  };
  const signalNode = signal({
    currentness: "STALE",
    sourceRefs: ["https://supplier.example/capability"],
  });
  const facts = runtimeFactsAt(projection(cognition, [signalNode]), "demand", "2026-10-05T00:00:00Z");

  assert.equal(facts.opportunities?.length, 0, "the demand evidence was not yet observed");
  assert.deepEqual(facts.sources.map((source) => source.id), ["source:capability"]);
  assert.equal(facts.sources[0]?.currentness, "UNKNOWN");
  assert.equal(facts.sources[0]?.currentnessEvaluatedAt, "2026-10-05T12:00:00Z");
  assert.equal(facts.signals[0]?.currentness, "UNKNOWN");
  assert.equal(facts.signals[0]?.currentnessEvaluatedAt, "2026-10-06T12:00:00Z");

  const supportedButLaterEvaluated = {
    ...baseCognition,
    asOf: "2026-10-06T12:00:00Z",
    sources: baseCognition.sources.map((source) => ({
      ...source,
      currentnessEvaluatedAt: "2026-10-06T12:00:00Z",
    })),
    opportunities: baseCognition.opportunities.map((item) => ({
      ...item,
      currentness: "CURRENT",
      currentnessEvaluatedAt: "2026-10-06T12:00:00Z",
    })),
  };
  const historicalOpportunity = runtimeFactsAt(
    projection(supportedButLaterEvaluated),
    "demand",
    "2026-10-05T00:00:00Z",
  );
  assert.equal(historicalOpportunity.opportunities?.[0]?.epistemic, "POTENTIAL");
  assert.equal(historicalOpportunity.opportunities?.[0]?.currentness, "UNKNOWN");
});

test("UNKNOWN opportunity and missing buyer stay unknown; families do not share facts", () => {
  const cognition = {
    ...baseCognition,
    opportunities: baseCognition.opportunities.map((item) => ({
      ...item,
      epistemic: "UNKNOWN",
      currentness: "UNKNOWN",
      buyer: null,
    })),
  };
  const runtime = projection(cognition);
  const demandFacts = runtimeFactsAt(runtime, "demand", "2026-10-05T12:00:00Z");
  const valueFacts = runtimeFactsAt(runtime, "value", "2026-10-05T12:00:00Z");
  const presenceFacts = runtimeFactsAt(runtime, "presence", "2026-10-05T12:00:00Z");

  assert.equal(demandFacts.opportunities?.[0]?.epistemic, "UNKNOWN");
  assert.equal(demandFacts.opportunities?.[0]?.buyer.en, "Unknown");
  assert.equal(demandFacts.opportunities?.[0]?.currentness, "UNKNOWN");
  assert.equal(valueFacts.opportunities?.length, 0);
  assert.equal(presenceFacts.opportunities, undefined);
  assert.equal(presenceFacts.signals.length, 0);
  assert.equal(presenceFacts.sources.length, 0);
});

test("an unsupported runtime context never falls back to the Norte fixture", () => {
  assert.ok(factsAt("norte", "2026-10-05").opportunities?.length);

  const emptyRuntime = projection(undefined, []);
  const facts = runtimeFactsAt(emptyRuntime, "demand", "2026-10-05T12:00:00Z");

  assert.deepEqual(facts.sources, []);
  assert.deepEqual(facts.signals, []);
  assert.deepEqual(facts.opportunities, []);
});

test("organization provenance retains authorized sources without requiring a node", () => {
  const facts = runtimeFactsAt(projection(baseCognition, []), "organization", "2026-10-05T12:00:00Z");

  assert.deepEqual(
    facts.sources.map((source) => source.id),
    ["source:capability", "source:demand"],
  );
  assert.deepEqual(facts.signals, []);
});

test("signal provenance selects exact support ids before falling back to source URLs", () => {
  const signalNode = signal({ observationSupportRefs: ["source:capability"] });
  const newerSameUrlSource = {
    ...baseCognition.sources[0],
    id: "source:capability:newer",
    observedAt: "2026-10-04T11:30:00Z",
    provenanceRef: "basis:capability:later-observation",
  };
  const cognition = {
    ...baseCognition,
    sources: [...baseCognition.sources, newerSameUrlSource],
    signals: [{ id: "signal:opportunity", familyId: "activity" }],
  };
  const facts = runtimeFactsAt(projection(cognition, [signalNode]), "activity", "2026-10-05T12:00:00Z");

  assert.equal(facts.signals.length, 1);
  assert.deepEqual(facts.sources.map((source) => source.id), ["source:capability"]);

  const evidenceRefsOnly = runtimeFactsAt(
    projection(
      {
        ...cognition,
        sources: [baseCognition.sources[0]],
      },
      [signal({ observationSupportRefs: [] })],
    ),
    "activity",
    "2026-10-05T12:00:00Z",
  );
  assert.deepEqual(evidenceRefsOnly.sources.map((source) => source.id), ["source:capability"]);
});

test("invalid asOf is rejected instead of widening the temporal cut", () => {
  assert.throws(
    () => runtimeFactsAt(projection(baseCognition), "demand", "not-a-date"),
    RangeError,
  );
});
