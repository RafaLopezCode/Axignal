import { test } from "node:test";
import assert from "node:assert/strict";
import { hasMaterialReobservationChange, latestObservationStatus } from "../lib/reobservation-feedback";
import { runtimeProjectionSchema } from "../lib/runtime-projection";

const base = runtimeProjectionSchema.parse({
  realityLevel: "LIVE",
  runtimeCodeSha: "sha",
  lifecycleStatus: "LIVE",
  context: { id: "ctx:one", label: "Subject" },
  organization: { id: "org:one", name: "Subject" },
  nodes: [{
    id: "signal:one",
    nodeKind: "XIGNAL",
    title: "Public surface observed",
    whyAttention: "Governed source observed",
    interpretation: "The source was reachable",
    uncertainty: "Other surfaces remain UNKNOWN",
    epistemicState: "OBSERVED",
    currentness: "CURRENT",
    observedAt: "2026-10-04T10:00:00Z",
    evidenceAccess: "AVAILABLE",
    sourceRefs: ["https://example.org/"],
    observationSupportRefs: ["obs:one"],
    unknowns: ["Other surfaces remain UNKNOWN"],
    evidenceNarrative: {
      xignalId: "signal:one",
      focusStepId: "obs:one",
      steps: [{
        id: "obs:one",
        kind: "OBSERVATION",
        label: "Observed text",
        sourceRef: null,
        observedAt: "2026-10-04T10:00:00Z",
        currentness: "CURRENT",
        artifactVerified: true,
      }],
    },
  }],
  temporalHistory: {
    disposition: "SINGLE_OBSERVATION",
    items: [{
      observationId: "obs:one",
      sourceRef: "https://example.org/",
      sourceType: "OFFICIAL_WEB",
      observedAt: "2026-10-04T10:00:00Z",
      currentness: "CURRENT",
      normalizedStateChanged: null,
    }],
  },
  today: { disposition: "READY", items: [] },
  reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
});

test("reobservation timestamp/context churn is not a material change", () => {
  const after = structuredClone(base);
  after.context.id = "ctx:two";
  after.nodes[0].observedAt = "2026-10-04T11:00:00Z";
  after.nodes[0].observationSupportRefs = ["obs:two"];
  after.nodes[0].evidenceNarrative.focusStepId = "obs:two";
  after.nodes[0].evidenceNarrative.steps[0].id = "obs:two";
  after.nodes[0].evidenceNarrative.steps[0].observedAt = "2026-10-04T11:00:00Z";
  assert.equal(hasMaterialReobservationChange(base, after), false);
  assert.deepEqual(latestObservationStatus(after), {
    observedAt: "2026-10-04T11:00:00Z",
    currentness: "CURRENT",
  });
});

test("epistemic or evidence-content differences are material to the projection", () => {
  const changed = structuredClone(base);
  changed.nodes[0].uncertainty = "Search remains UNKNOWN";
  assert.equal(hasMaterialReobservationChange(base, changed), true);
});
