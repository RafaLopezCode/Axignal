import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { RuntimeLens } from "../components/cognition/runtime-lens";
import { CognitiveComponent } from "../components/cognition/lenses";
import { dateLabel } from "../lib/projection";
import { composeFamily, validateCognitivePlan } from "../lib/cognition/compose";
import { runtimeFactsAt } from "../lib/cognition/runtime-facts";
import { runtimeProjectionSchema, type RuntimeProjection } from "../lib/runtime-projection";

const cut = "2026-10-07T12:00:00Z";
const revision = "a".repeat(64);

test("AXENT provenance renders real ISO instants and preserves evaluated currentness", () => {
  assert.equal(dateLabel("2026-10-04T09:00:00Z", "en"), dateLabel("2026-10-04", "en"));
  assert.equal(dateLabel("not-a-date", "en"), dateLabel(null, "en"));
  const facts = {
    sources: [{
      id: "source:real", title: { es: "Fuente real", en: "Real source" },
      observedAt: "2026-10-04T09:00:00Z", currentness: "HISTORICAL" as const,
      instrument: { es: "Instrumento", en: "Instrument" },
      limitation: { es: "Alcance limitado", en: "Bounded scope" },
    }],
  };
  const html = renderToStaticMarkup(createElement(CognitiveComponent, {
    id: "provenance-trail", facts, asOf: "2026-10-05T12:00:00Z", glance: false,
  }));
  assert.match(html, /data-currentness="HISTORICAL"/);
  assert.doesNotMatch(html, /data-currentness="CURRENT"/);
});

const cognition = {
  asOf: cut,
  sources: [
    {
      id: "source:capability",
      title: "Public capability description",
      observedAt: "2026-10-04T09:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: cut,
      instrument: "Public document, deterministic reading",
      limitation: "A declaration does not establish available capacity.",
      sourceRef: "https://organization.example/capability",
      provenanceRef: "basis:capability:01",
    },
    {
      id: "source:demand",
      title: "Public project notice",
      observedAt: "2026-10-04T10:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: cut,
      instrument: "Public project notice",
      limitation: "Eligibility and commercial fit remain unknown.",
      sourceRef: "https://buyer.example/project",
      provenanceRef: "basis:demand:01",
    },
  ],
  signals: [{ id: "signal:potential", familyId: "demand" }],
  opportunities: [
    {
      id: "opportunity:potential",
      familyId: "demand",
      opportunityFamily: "PRIVATE_PROJECT_SIGNALS",
      title: "Potential project relevance",
      buyer: "Buyer organization",
      market: "Market stated by the source",
      form: "Project notice",
      deadline: null,
      epistemic: "POTENTIAL",
      capability: {
        label: "Declared capability",
        excerpt: "The public document describes a capability.",
        sourceId: "source:capability",
      },
      demand: {
        label: "Source-stated need",
        code: null,
        sourceId: "source:demand",
      },
      known: [{ label: "Project stage", value: "Announced" }],
      unknown: ["Available capacity", "Commercial access"],
      matchBasis: ["CAPABILITY_NEED_RELEVANCE"],
      whyPotential: "The described capability could relate to the stated need.",
      whyLooked: ["The two source-backed descriptions overlap."],
      observedAt: "2026-10-06T11:00:00Z",
      currentness: "CURRENT",
      currentnessEvaluatedAt: cut,
    },
  ],
};

function signal(overrides: Record<string, unknown> = {}) {
  return {
    id: "signal:potential",
    nodeKind: "XIGNAL",
    title: "Potential project relevance",
    whyAttention: "The available evidence warrants attention.",
    interpretation: "A declared capability could relate to a stated need.",
    uncertainty: "Eligibility and available capacity remain unknown.",
    epistemicState: "POTENTIAL",
    currentness: "CURRENT",
    observedAt: "2026-10-06T11:00:00Z",
    evidenceAccess: "AVAILABLE",
    sourceRefs: ["https://organization.example/capability", "https://buyer.example/project"],
    observationSupportRefs: ["source:capability", "source:demand"],
    unknowns: ["Available capacity"],
    evidenceNarrative: {
      xignalId: "signal:potential",
      focusStepId: "signal:potential:step:source",
      steps: [
        {
          id: "signal:potential:step:source",
          kind: "SOURCE",
          label: "Public project notice",
          sourceRef: "https://buyer.example/project",
          observedAt: "2026-10-04T10:00:00Z",
          currentness: "CURRENT",
          artifactVerified: true,
        },
      ],
    },
    ...overrides,
  };
}

function realProjection(
  cognitionValue: unknown = cognition,
  nodeValues: unknown[] = [signal()],
): RuntimeProjection {
  return runtimeProjectionSchema.parse({
    realityLevel: "CONTROLLED_ECONOMIC_PRODUCT_PROOF",
    runtimeCodeSha: "controlled-test-revision",
    lifecycleStatus: "LIVE",
    context: { id: "focus:controlled", label: "Controlled focus" },
    organization: { id: "org:controlled", name: "Observed Organization" },
    nodes: nodeValues,
    cognition: cognitionValue,
    temporalHistory: { disposition: "EMPTY", items: [] },
    today: { disposition: "READY", items: [] },
    reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  });
}

function render(
  projection: RuntimeProjection,
  selectedRevision = revision,
  options: {
    asOf?: string;
    family?: "presence" | "demand";
    intent?: "overview" | "why" | "how_known" | "change";
    responsePlan?: unknown;
  } = {},
) {
  return renderToStaticMarkup(
    createElement(RuntimeLens, {
      projection,
      revision: selectedRevision,
      initialFamily: options.family ?? "demand",
      ...(options.intent ? { initialIntent: options.intent } : {}),
      ...(options.asOf ? { asOf: options.asOf } : {}),
      ...(options.responsePlan ? { responsePlan: options.responsePlan } : {}),
    }),
  );
}

test("runtime lens renders only source-backed POTENTIAL and keeps UNKNOWN explicit", () => {
  const runtime = realProjection();
  const facts = runtimeFactsAt(runtime, "demand", cut);
  const plan = composeFamily({ family: "demand", intent: "overview", device: "mobile", facts });
  for (const item of plan.items) {
    const itemCheck = validateCognitivePlan({ ...plan, items: [item] }, facts);
    assert.equal(itemCheck.success, true, `${item.component}: ${itemCheck.success ? "valid" : itemCheck.error}`);
  }
  assert.equal(validateCognitivePlan(plan, facts).success, true, JSON.stringify(validateCognitivePlan(plan, facts)));
  const html = render(runtime);
  assert.match(html, /data-family="demand"/);
  assert.match(html, /data-epistemic="POTENTIAL"/);
  assert.match(html, /data-epistemic="UNKNOWN"/);
  assert.match(html, /Commercial access/);
  assert.match(html, /href="https:\/\/buyer\.example\/project"/);
  assert.match(html, /basis:demand:01/);
  assert.doesNotMatch(html, /badge-observed/);
});

test("requirement matrix keeps potential opportunity context without promoting known details", () => {
  const html = render(realProjection(), revision, { intent: "how_known" });
  assert.match(html, /data-cognitive-component="requirement-matrix"/);
  assert.match(html, /class="cg-requirements" data-epistemic="POTENTIAL"/);
  assert.match(html, /Potential relevance does not confirm a commercial relationship/);
  assert.match(html, /Project stage: Announced/);
  assert.match(html, /Available capacity/);
  assert.doesNotMatch(html, /data-epistemic="OBSERVED"/);
});

test("historical cut hides later opportunity and currentness evaluation without inventing a zero", () => {
  const projection = realProjection();
  const asOf = "2026-10-05T12:00:00Z";
  const facts = runtimeFactsAt(projection, "demand", asOf);
  assert.equal(facts.opportunities?.length, 0);
  assert.equal(facts.sources.length, 0);

  const html = render(projection, revision, { asOf });
  assert.match(html, /data-as-of="2026-10-05T12:00:00Z"/);
  const cutInput = html.match(/<input[^>]*type="datetime-local"[^>]*>/)?.[0];
  assert.ok(cutInput);
  assert.match(cutInput, /value="2026-10-05T12:00:00\.000"/);
  assert.match(cutInput, /max="2026-10-07T12:00:00\.000"/);
  assert.match(html, /data-epistemic="UNKNOWN"/);
  assert.doesNotMatch(html, /data-epistemic="POTENTIAL"/);
  assert.doesNotMatch(html, /Potential project relevance|source:demand|buyer\.example|Currentness evaluated/);
  assert.doesNotMatch(html, /0 opportunities|0 oportunidades/);
});

test("runtime cut clamps a caller-provided future cut to the projection horizon", () => {
  const html = render(realProjection(), revision, { asOf: "2026-10-09T12:00:00Z" });
  const cutInput = html.match(/<input[^>]*type="datetime-local"[^>]*>/)?.[0];
  assert.ok(cutInput);
  assert.match(html, /data-as-of="2026-10-07T12:00:00Z"/);
  assert.match(cutInput, /value="2026-10-07T12:00:00\.000"/);
  assert.match(cutInput, /max="2026-10-07T12:00:00\.000"/);
});

test("new runtime revision replaces its previous reading", () => {
  const first = render(realProjection(), revision);
  const nextRevision = "b".repeat(64);
  const nextCognition = {
    ...cognition,
    asOf: "2026-10-08T12:00:00Z",
    opportunities: cognition.opportunities.map((item) => ({
      ...item,
      title: "Potential relevance after reobservation",
      observedAt: "2026-10-08T11:00:00Z",
      currentnessEvaluatedAt: "2026-10-08T12:00:00Z",
    })),
  };
  const next = render(realProjection(nextCognition, [signal({
    observedAt: "2026-10-08T11:00:00Z",
    title: "Potential relevance after reobservation",
  })]), nextRevision);

  assert.match(first, new RegExp(`data-revision="${revision}"`));
  assert.match(next, new RegExp(`data-revision="${nextRevision}"`));
  assert.match(next, /Potential relevance after reobservation/);
  assert.doesNotMatch(next, /Potential project relevance/);
});

test("forged server plan is dropped before the local validated family plan renders", () => {
  const projection = realProjection();
  const facts = runtimeFactsAt(projection, "demand", cut);
  const validPlan = composeFamily({ family: "demand", intent: "overview", device: "mobile", facts });
  const forged = {
    version: 1,
    revision,
    intent: "summary",
    refs: ["signal:potential"],
    method: "DETERMINISTIC_EVIDENCE_PRESENTATION",
    cognition: {
      request: { family: "demand", asOf: cut, intent: "overview", device: "mobile" },
      plan: { ...validPlan, items: [{ component: "invented-market-zero", layer: 1 }] },
    },
  };

  const html = render(projection, revision, { responsePlan: forged });
  assert.match(html, /data-plan-source="local"/);
  assert.match(html, /data-cognitive-component="opportunity-brief"/);
  assert.doesNotMatch(html, /invented-market-zero|Norte Renovable|Navarra/);
});

test("empty runtime projection stays UNKNOWN and never falls back to illustrative facts", () => {
  const empty = realProjection({ asOf: cut, sources: [], signals: [], opportunities: [] }, []);
  const html = render(empty, revision, { family: "presence" });
  assert.match(html, /data-runtime-empty="unsupported"/);
  assert.match(html, /data-epistemic="UNKNOWN"/);
  assert.doesNotMatch(html, /Norte Renovable|Navarra|Atlas Circular|0%/);
});
