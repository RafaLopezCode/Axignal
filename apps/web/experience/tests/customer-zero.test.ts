import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  customerZeroCommand,
  readCustomerZeroResponse,
  safeSourceLink,
} from "../lib/runtime-projection";
import { POST as connectSession } from "../app/api/admin/session/route";

const projection = {
  realityLevel: "CONTROLLED_TEST",
  runtimeCodeSha: "test-sha",
  lifecycleStatus: "LIVE",
  organization: {
    id: "org:test",
    name: "Contract subject",
    privateRevenue: 999,
  },
  context: { id: "focus:test", label: "Contract focus" },
  nodes: [
    {
      id: "signal:test",
      nodeKind: "XIGNAL",
      title: "Observed surface",
      whyAttention: "Source changed",
      interpretation: "A bounded reading",
      uncertainty: "Other surfaces remain unknown",
      epistemicState: "OBSERVED",
      currentness: "CURRENT",
      observedAt: "2026-10-04T00:00:00Z",
      evidenceAccess: "AVAILABLE",
      sourceRefs: ["https://example.org/"],
      observationSupportRefs: ["observation:test"],
      unknowns: ["Reach unknown"],
      evidenceNarrative: {
        xignalId: "signal:test",
        focusStepId: "step:source",
        steps: [
          {
            id: "step:source",
            kind: "SOURCE",
            label: "Observed source",
            sourceRef: "https://example.org/",
            observedAt: "2026-10-04T00:00:00Z",
            currentness: "CURRENT",
            artifactVerified: true,
          },
        ],
      },
    },
  ],
  today: {
    disposition: "READY",
    items: [
      {
        xignalId: "signal:test",
        whatChanged: "Surface observed",
        whyItMatters: "A bounded observation",
        observedAt: "2026-10-04T00:00:00Z",
        showHowRef: "step:source",
      },
    ],
  },
  reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL",
  privateAccounts: ["secret"],
};
test("distinct runtime states never create a fallback signal", () => {
  for (const [payload, status, state] of [
    [{ state: "NO_XEED" }, 200, "NO_XEED"],
    [
      { state: "INSUFFICIENT_EVIDENCE", reason: "NO_BODY" },
      422,
      "INSUFFICIENT_EVIDENCE",
    ],
    [{ status: "failed", reason: "HTTP_FAILURE" }, 502, "failure"],
    [{ status: "rejected", reason: "POLICY" }, 400, "rejected"],
    [{ state: "rejected", reason: "POLICY" }, 400, "rejected"],
    [{}, 401, "unauthorized"],
    [{}, 200, "failure"],
  ] as const)
    assert.equal(readCustomerZeroResponse(payload, status).state, state);
});
test("projection identity, narrative, currentness and sources survive persisted reload; private fields do not", () => {
  const first = readCustomerZeroResponse(projection, 201);
  const reload = readCustomerZeroResponse(
    JSON.parse(JSON.stringify(projection)),
    200,
  );
  assert.deepEqual(first, reload);
  assert.equal(first.state, "success");
  if (first.state !== "success") throw new Error("projection not accepted");
  assert.equal(first.projection.organization.name, "Contract subject");
  assert.equal(first.projection.nodes[0].currentness, "CURRENT");
  assert.equal(
    first.projection.nodes[0].evidenceNarrative.steps[0].artifactVerified,
    true,
  );
  assert.deepEqual(first.projection.nodes[0].sourceRefs, [
    "https://example.org/",
  ]);
  assert.ok(!JSON.stringify(first).includes("privateRevenue"));
  assert.ok(!JSON.stringify(first).includes("privateAccounts"));
});
test("source navigation rejects credentials and potentially private URL material", () => {
  assert.equal(safeSourceLink("https://example.org/"), "https://example.org/");
  for (const ref of [
    "javascript:alert(1)",
    "https://user:password@example.org/",
    "https://example.org/?token=secret",
    "https://example.org/#secret",
    "artifact:sha256:test",
  ])
    assert.equal(safeSourceLink(ref), null);
});
test("Customer Zero only sends canonical attention, and consumes the real read endpoint", () => {
  assert.deepEqual(customerZeroCommand, {
    label: "AXIGNAL self-observation",
    targetUri: "https://axignal.com/",
  });
  const client = readFileSync("components/customer-zero.tsx", "utf8");
  const renderer = readFileSync("components/runtime-product.tsx", "utf8");
  const adapter = readFileSync("lib/customer-zero-server.ts", "utf8");
  const subscriber = readFileSync("components/runtime-panorama.tsx", "utf8");
  assert.ok(client.includes('"/api/subscriber-context"'));
  assert.ok(client.includes('"/api/xeeds"'));
  assert.ok(adapter.includes('"/internal/admin/customer-zero/access"'));
  for (const content of [client, renderer, adapter, subscriber]) {
    assert.doesNotMatch(
      content,
      /Norte|Atlas|adminRecords|subscriberFixture|from ["'].*\/projection["']/,
    );
    assert.doesNotMatch(
      content,
      /nodeKind:\s*["']XIGNAL|epistemicState:\s*["']OBSERVED/,
    );
  }
  assert.ok(renderer.includes("signal.evidenceNarrative.steps"));
  assert.ok(renderer.includes("signal.uncertainty"));
  assert.ok(renderer.includes("signal.currentness"));
  assert.ok(subscriber.includes("<RuntimeProductProjection"));
  assert.ok(client.includes("<RuntimeProductProjection"));
});
test("session transport rejects foreign origin, malformed, oversized and non-JSON bodies", async () => {
  const url = "http://127.0.0.1:3810/api/admin/session";
  const headers = {
    origin: "http://127.0.0.1:3810",
    host: "127.0.0.1:3810",
    "content-type": "application/json",
  };
  for (const [body, overrides, expected] of [
    ["{}", { origin: "https://foreign.example" }, 403],
    ["{}", { host: "foreign.example" }, 403],
    ["{", {}, 400],
    ["{}", {}, 400],
    ["a".repeat(1025), {}, 413],
    ["{}", { "content-type": "text/plain" }, 415],
  ] as const) {
    const response = await connectSession(
      new Request(url, {
        method: "POST",
        headers: { ...headers, ...overrides },
        body,
      }),
    );
    assert.equal(response.status, expected);
    assert.equal(response.headers.get("set-cookie"), null);
  }
});
