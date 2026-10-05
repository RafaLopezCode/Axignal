import assert from "node:assert/strict";
import test from "node:test";

import { firstMapBrief } from "../lib/runtime-reading";
import { runtimeProjectionSchema } from "../lib/runtime-projection";

test("economic POTENTIAL Xignal uses the existing runtime/read-model contract", () => {
  const projection = runtimeProjectionSchema.parse({
    realityLevel: "CONTROLLED_ECONOMIC_PRODUCT_PROOF",
    runtimeCodeSha: "sha",
    lifecycleStatus: "LIVE",
    context: { id: "xeed:1", label: "Supplier" },
    organization: { id: "org:supplier", name: "Supplier" },
    nodes: [{
      id: "xignal:economic:abc123",
      nodeKind: "XIGNAL",
      title: "Potential project relevance",
      whyAttention: "The available public evidence warrants investigation.",
      interpretation: "CNC machining could address the stated project need.",
      uncertainty: "Price has not been assessed.",
      epistemicState: "POTENTIAL",
      currentness: "CURRENT",
      observedAt: "2026-10-05T10:00:00+00:00",
      evidenceAccess: "AVAILABLE",
      sourceRefs: [
        "https://supplier.example/capability",
        "https://buyer.example/project",
      ],
      observationSupportRefs: ["obs:supplier:1", "obs:need:1"],
      unknowns: ["Price has not been assessed."],
      evidenceNarrative: {
        xignalId: "xignal:economic:abc123",
        focusStepId: "xignal:economic:abc123:step:xignal",
        steps: [{
          id: "xignal:economic:abc123:step:xignal",
          kind: "XIGNAL",
          label: "CNC machining could address the stated project need.",
          sourceRef: null,
          observedAt: "2026-10-05T10:00:00+00:00",
          currentness: "CURRENT",
          artifactVerified: null,
        }, {
          id: "xignal:economic:abc123:step:evidence:01",
          kind: "OBSERVATION",
          label: "Supplier states CNC machining capability.",
          sourceRef: "https://supplier.example/capability",
          observedAt: "2026-10-05T10:00:00+00:00",
          currentness: "CURRENT",
          artifactVerified: null,
        }],
      },
    }],
    temporalHistory: { disposition: "EMPTY", items: [] },
    today: {
      disposition: "READY",
      items: [{
        xignalId: "xignal:economic:abc123",
        whatChanged: "Potential project relevance",
        whyItMatters: "The available public evidence warrants investigation.",
        observedAt: "2026-10-05T10:00:00+00:00",
        showHowRef: "xignal:economic:abc123",
      }],
    },
    reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  });

  const brief = firstMapBrief(projection);
  assert.equal(brief.primarySignal?.id, "xignal:economic:abc123");
  assert.equal(brief.primarySignal?.epistemicState, "POTENTIAL");
  assert.equal(brief.currentCount, 1);
  assert.deepEqual(brief.openQuestions, ["Price has not been assessed."]);
});
