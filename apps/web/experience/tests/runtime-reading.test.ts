import { test } from "node:test";
import assert from "node:assert/strict";
import { firstMapBrief, latestObservedSignal, orderedSignals, signalGroups } from "../lib/runtime-reading";
import { runtimeProjectionSchema, type RuntimeSignal } from "../lib/runtime-projection";

function signal(
  id: string,
  epistemicState: RuntimeSignal["epistemicState"],
  currentness: RuntimeSignal["currentness"],
  observedAt: string,
): RuntimeSignal {
  return {
    id,
    nodeKind: "XIGNAL",
    title: id,
    whyAttention: id + " attention",
    interpretation: id + " interpretation",
    uncertainty: id + " uncertainty",
    epistemicState,
    currentness,
    observedAt,
    evidenceAccess: "AVAILABLE",
    sourceRefs: [],
    observationSupportRefs: [],
    unknowns: [],
    evidenceNarrative: { xignalId: id, focusStepId: id, steps: [] },
  };
}

test("Signals prioritizes epistemic state, currentness and recency without mutation", () => {
  const nodes = [
    signal("unknown-new", "UNKNOWN", "CURRENT", "2026-10-04T12:00:00Z"),
    signal("observed-old", "OBSERVED", "CURRENT", "2026-10-03T12:00:00Z"),
    signal("observed-new", "OBSERVED", "CURRENT", "2026-10-04T12:00:00Z"),
    signal("observed-stale", "OBSERVED", "STALE", "2026-10-05T12:00:00Z"),
    signal("potential", "POTENTIAL", "CURRENT", "2026-10-04T12:00:00Z"),
  ];
  const before = nodes.map((item) => item.id);
  assert.deepEqual(
    orderedSignals(nodes).map((item) => item.id),
    ["observed-new", "observed-old", "observed-stale", "potential", "unknown-new"],
  );
  assert.deepEqual(nodes.map((item) => item.id), before);
  assert.deepEqual(
    signalGroups(nodes).map((group) => [group.state, group.signals.length]),
    [["OBSERVED", 3], ["POTENTIAL", 1], ["UNKNOWN", 1]],
  );
});

test("Today fallback selects latest known observation but does not fabricate a Today item", () => {
  const nodes = [
    signal("older", "OBSERVED", "CURRENT", "2026-10-01T12:00:00Z"),
    signal("latest", "UNKNOWN", "CURRENT", "2026-10-03T12:00:00Z"),
  ];
  const projection = { nodes, today: { disposition: "READY", items: [] } };
  assert.equal(latestObservedSignal(projection)?.id, "latest");
  assert.equal(projection.today.items.length, 0);
});

test("Today fallback is null when no observation exists", () => {
  assert.equal(latestObservedSignal({ nodes: [] }), null);
});


test("FIRST_MAP brief increases comprehension density without inventing graph facts", () => {
  const projection = runtimeProjectionSchema.parse({
    realityLevel: "LIVE",
    runtimeCodeSha: "sha",
    lifecycleStatus: "LIVE",
    context: { id: "ctx", label: "Subject" },
    organization: { id: "org", name: "Subject" },
    nodes: [{
      id: "signal:one",
      nodeKind: "XIGNAL",
      title: "Public surface observed",
      whyAttention: "Governed source observed",
      interpretation: "The source was reachable",
      uncertainty: "Commercial relationships remain UNKNOWN",
      epistemicState: "OBSERVED",
      currentness: "CURRENT",
      observedAt: "2026-10-04T10:00:00Z",
      evidenceAccess: "AVAILABLE",
      sourceRefs: ["https://example.org/"],
      observationSupportRefs: ["obs:one"],
      unknowns: ["Customers remain UNKNOWN"],
      evidenceNarrative: {
        xignalId: "signal:one",
        focusStepId: "obs:one",
        steps: [],
      },
    }],
    temporalHistory: {
      disposition: "MULTIPLE_OBSERVATIONS",
      items: [
        { observationId:"obs:one", sourceRef:"https://example.org/", sourceType:"OFFICIAL_WEB", observedAt:"2026-10-03T10:00:00Z", currentness:"CURRENT", normalizedStateChanged:null },
        { observationId:"obs:two", sourceRef:"https://example.org/", sourceType:"OFFICIAL_WEB", observedAt:"2026-10-04T10:00:00Z", currentness:"CURRENT", normalizedStateChanged:false },
      ],
    },
    today: { disposition: "READY", items: [] },
    reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  });
  const before = JSON.stringify(projection);
  const brief = firstMapBrief(projection);
  assert.equal(brief.isSparse, true);
  assert.equal(brief.signalCount, 1);
  assert.equal(brief.observedCount, 1);
  assert.equal(brief.sourceCount, 1);
  assert.equal(brief.observationCount, 2);
  assert.equal(brief.currentCount, 1);
  assert.equal(brief.primarySignal?.id, "signal:one");
  assert.deepEqual(brief.openQuestions, [
    "Commercial relationships remain UNKNOWN",
    "Customers remain UNKNOWN",
  ]);
  assert.equal(JSON.stringify(projection), before);
});

test("FIRST_MAP brief never fabricates a finding for an empty projection", () => {
  const brief = firstMapBrief({ nodes: [], temporalHistory: { disposition:"EMPTY", items:[] } });
  assert.equal(brief.isSparse, true);
  assert.equal(brief.primarySignal, null);
  assert.deepEqual(brief.openQuestions, []);
  assert.equal(brief.sourceCount, 0);
});

test("an acquired source without a representable page remains visible without a finding", () => {
  const brief = firstMapBrief({ nodes: [], temporalHistory: { disposition: "SINGLE_OBSERVATION", items: [{
    observationId: "obs:limited", sourceRef: "https://axignal.com/", sourceType: "OFFICIAL_WEB",
    observedAt: "2026-10-06T20:00:00Z", currentness: "CURRENT", normalizedStateChanged: null,
  }] }, digitalRepresentation: { state: "NOT_MEASURED", reason: {
    code: "REPRESENTATION_VISIBILITY_UNRESOLVED", explanation: "Rendered visibility remains unknown.",
  } } });
  assert.equal(brief.sourceCount, 1);
  assert.equal(brief.observedCount, 0);
  assert.equal(brief.primarySignal, null);
  assert.deepEqual(brief.openQuestions, ["Rendered visibility remains unknown."]);
});
