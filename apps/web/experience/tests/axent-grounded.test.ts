import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { POST as subscriberAxent } from "../app/api/subscriber/axent/route";

const saved = {
  fetch: globalThis.fetch,
  runtime: process.env.AXIGNAL_RUNTIME_ORIGIN,
  origin: process.env.AXIGNAL_EXPERIENCE_ORIGIN,
  grounded: process.env.AXIGNAL_AXENT_GROUNDED,
};
afterEach(() => {
  globalThis.fetch = saved.fetch;
  for (const [key, value] of [
    ["AXIGNAL_RUNTIME_ORIGIN", saved.runtime],
    ["AXIGNAL_EXPERIENCE_ORIGIN", saved.origin],
    ["AXIGNAL_AXENT_GROUNDED", saved.grounded],
  ] as const) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
});

const token = "a".repeat(48);
const projection = {
  realityLevel: "CONTROLLED_CONTRACT_TEST", runtimeCodeSha: "test", lifecycleStatus: "LIVE",
  context: { id: "focus:one", label: "Organization" }, organization: { id: "org:one", name: "Organization" },
  nodes: [], temporalHistory: { disposition: "EMPTY" as const, items: [] }, today: { disposition: "EMPTY", items: [] },
  reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL" as const,
};
const revision = createHash("sha256").update(JSON.stringify(projection)).digest("hex");
const grounded = {
  organizationId: "org:one", contextId: "focus:one", signalIds: [], intent: "known",
  summary: "Hay demanda potencial en Getafe.", known: ["Potencial · Hay demanda potencial en Getafe."],
  openQuestions: [], evidenceBasis: ["Instalación fotovoltaica"], researchPlan: [], passages: [],
  action: "focus", sourceRefs: ["https://ted.europa.eu/notice/1"], observedAt: ["2026-10-06T00:00:00+00:00"],
  currentness: ["CURRENT"], grounding: { route: "MODEL", claims: [], evidence: [] },
  memory: { focusId: "focus:one", family: "demand", geographies: [], previousRefs: [], turn: 1 },
};

function ask(body: Record<string, unknown>) {
  return new Request("https://axignal.com/api/subscriber/axent", {
    method: "POST",
    headers: { host: "axignal.com", origin: "https://axignal.com", cookie: `__Host-axignal-subscriber=${token}`, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function runtime(onAxent: (body: Record<string, unknown>) => Response) {
  const calls: string[] = [];
  globalThis.fetch = async (url, init) => {
    const path = new URL(String(url)).pathname;
    calls.push(`${init?.method ?? "GET"} ${path}`);
    assert.equal(new Headers(init?.headers).get("authorization"), `Bearer ${token}`);
    if (path.endsWith("/output")) return Response.json({ state: "INSUFFICIENT_EVIDENCE", projection });
    return onAxent(JSON.parse(String(init?.body)));
  };
  return calls;
}

test("grounded AXENT answers through the runtime with only question, locale and compact memory", async () => {
  process.env.AXIGNAL_RUNTIME_ORIGIN = "http://127.0.0.1:18181";
  process.env.AXIGNAL_EXPERIENCE_ORIGIN = "https://axignal.com";
  process.env.AXIGNAL_AXENT_GROUNDED = "true";
  let sent: Record<string, unknown> = {};
  const calls = runtime((body) => { sent = body; return Response.json(grounded); });
  const memory = { focusId: "focus:one", family: "demand", geographies: [], previousRefs: [], turn: 0 };
  const response = await subscriberAxent(ask({ prompt: "¿Y en Getafe?", contextId: "focus:one", revision, locale: "es", memory }));
  assert.equal(response.status, 200);
  const payload = await response.json();
  assert.equal(payload.summary, grounded.summary);
  assert.equal(payload.revision, revision);
  assert.deepEqual(Object.keys(sent).sort(), ["locale", "memory", "question"]);
  assert.deepEqual(calls, ["GET /subscriber/organizations/focus%3Aone/output", "POST /subscriber/organizations/focus%3Aone/axent"]);
});

test("without the flag or when the runtime cannot answer, the deterministic explanation is kept", async () => {
  process.env.AXIGNAL_RUNTIME_ORIGIN = "http://127.0.0.1:18181";
  process.env.AXIGNAL_EXPERIENCE_ORIGIN = "https://axignal.com";
  delete process.env.AXIGNAL_AXENT_GROUNDED;
  let calls = runtime(() => Response.json(grounded));
  let response = await subscriberAxent(ask({ prompt: "Qué sabes", contextId: "focus:one", revision, locale: "es" }));
  assert.equal(response.status, 200);
  assert.notEqual((await response.json()).summary, grounded.summary);
  assert.equal(calls.length, 1);
  process.env.AXIGNAL_AXENT_GROUNDED = "true";
  calls = runtime(() => Response.json({ state: "rejected", code: "AXENT_NOT_CONFIGURED" }, { status: 503 }));
  response = await subscriberAxent(ask({ prompt: "Qué sabes", contextId: "focus:one", revision, locale: "es" }));
  assert.equal(response.status, 200);
  assert.notEqual((await response.json()).summary, grounded.summary);
});
