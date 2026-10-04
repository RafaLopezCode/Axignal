import { test } from "node:test";
import assert from "node:assert/strict";
import {
  presentEvidenceStepLabel,
  presentRuntimeCode,
  presentRuntimePassage,
  presentRuntimeText,
} from "../lib/runtime-presentation";
import type { Locale } from "../lib/languages";
import type { RuntimeProjection } from "../lib/runtime-projection";

const locales: Locale[] = ["es", "en", "de", "pt", "fr", "it"];
const uncertainty =
  "This observation covers only the authorized public homepage at this observation time. Search, generative, social, reputation and other public surfaces remain UNKNOWN.";
const projection = {
  realityLevel: "LIVE",
  runtimeCodeSha: "sha",
  lifecycleStatus: "LIVE",
  context: { id: "xeed:1", label: "AXIGNAL" },
  organization: { id: "org:axignal", name: "AXIGNAL" },
  nodes: [
    {
      id: "x:1",
      nodeKind: "XIGNAL",
      title: "AXIGNAL's public homepage is observable from the outside",
      whyAttention:
        "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation.",
      interpretation:
        "The authorized public homepage was reachable and contained visible text when AXIGNAL observed it.",
      uncertainty,
      epistemicState: "OBSERVED",
      currentness: "CURRENT",
      observedAt: "2026-10-04T20:22:04Z",
      evidenceAccess: "AVAILABLE",
      sourceRefs: ["https://axignal.com/"],
      observationSupportRefs: ["obs:1"],
      unknowns: [uncertainty],
      evidenceNarrative: {
        xignalId: "x:1",
        focusStepId: "obs:1",
        steps: [
          {
            id: "x",
            kind: "XIGNAL",
            label:
              "AXIGNAL retrieved the public homepage through the governed source sensor and can trace this Xignal back to the stored observation.",
            sourceRef: null,
            observedAt: null,
            currentness: "CURRENT",
            artifactVerified: null,
          },
          {
            id: "obs",
            kind: "OBSERVATION",
            label: "AXIGNAL — Observe the economic world from the outside",
            sourceRef: null,
            observedAt: "2026-10-04T20:22:04Z",
            currentness: "CURRENT",
            artifactVerified: true,
          },
          {
            id: "src",
            kind: "SOURCE",
            label: "OFFICIAL_WEB",
            sourceRef: "https://axignal.com/",
            observedAt: "2026-10-04T20:22:04Z",
            currentness: "CURRENT",
            artifactVerified: true,
          },
          {
            id: "u",
            kind: "UNKNOWN",
            label: uncertainty,
            sourceRef: null,
            observedAt: null,
            currentness: null,
            artifactVerified: null,
          },
        ],
      },
    },
  ],
  temporalHistory: {
    disposition: "SINGLE_OBSERVATION",
    items: [{
      observationId: "obs:1",
      sourceRef: "https://axignal.com/",
      sourceType: "OFFICIAL_WEB",
      observedAt: "2026-10-04T20:22:04Z",
      currentness: "CURRENT",
      normalizedStateChanged: null,
    }],
  },
  today: { disposition: "READY", items: [] },
  reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
} as RuntimeProjection;

test("runtime-authored copy localizes in all supported locales without rewriting evidence", () => {
  const raw = "AXIGNAL — Observe the economic world from the outside";
  for (const locale of locales) {
    const title = presentRuntimeText(
      projection.nodes[0].title,
      "AXIGNAL",
      locale,
    );
    assert.ok(title.length > 10);
    assert.equal(
      presentEvidenceStepLabel(
        projection.nodes[0].evidenceNarrative.steps[1],
        "AXIGNAL",
        locale,
      ),
      raw,
    );
  }
  assert.equal(
    presentRuntimeText(projection.nodes[0].title, "AXIGNAL", "es"),
    "La página pública de AXIGNAL es observable desde fuera",
  );
  assert.equal(
    presentRuntimeText(projection.nodes[0].title, "AXIGNAL", "en"),
    projection.nodes[0].title,
  );
  assert.notEqual(
    presentRuntimeText(projection.nodes[0].title, "AXIGNAL", "fr"),
    projection.nodes[0].title,
  );
});

test("runtime metadata is humanized without changing canonical codes", () => {
  assert.equal(presentRuntimeCode("OFFICIAL_WEB", "es"), "Web oficial");
  assert.equal(presentRuntimeCode("CURRENT", "es"), "Actual");
  assert.equal(presentRuntimeCode("UNKNOWN", "fr"), "Inconnu");
  assert.equal(presentRuntimeCode("FUTURE_CODE", "es"), "FUTURE_CODE");
  assert.equal(projection.nodes[0].currentness, "CURRENT");
});

test("AXENT presentation localizes governed discourse but preserves source-observed text", () => {
  const raw = "AXIGNAL — Observe the economic world from the outside";
  assert.equal(presentRuntimePassage(raw, projection, "es"), raw);
  assert.equal(
    presentRuntimePassage("OFFICIAL_WEB", projection, "es"),
    "Web oficial",
  );
  assert.equal(
    presentRuntimePassage(projection.nodes[0].whyAttention, projection, "es"),
    "AXIGNAL recuperó la página pública mediante el sensor de fuentes gobernado y puede rastrear esta señal hasta la observación almacenada.",
  );
});


test("dynamic organization title localizes in every supported locale", () => {
  const canonical = "ACME's public homepage is observable from the outside";
  for (const locale of locales) {
    const presented = presentRuntimeText(canonical, "ACME", locale);
    assert.ok(presented.includes("ACME"));
    if (locale !== "en") assert.notEqual(presented, canonical);
  }
});
