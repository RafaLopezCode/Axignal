import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { subscriberCommandSchema, approvedPaymentUrl, monthlyCapacityCents } from "../lib/subscriber-contracts";
import { subscriberAuthStart, subscriberAuthCallback, subscriberProxy, subscriberLogout, boundedSubscriberJson, subscriberBillingWebhook } from "../lib/subscriber-server";
import { acceptsReadingPlan } from "../lib/subscriber-presentation";
import { POST as reading } from "../app/api/subscriber/reading/route";
import { digitalRepresentationSchema } from "../lib/runtime-projection";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const savedFetch = globalThis.fetch;
const savedEnvironment = { runtime: process.env.AXIGNAL_RUNTIME_ORIGIN, origin: process.env.AXIGNAL_EXPERIENCE_ORIGIN };
afterEach(() => {
  globalThis.fetch = savedFetch;
  for (const [key, value] of [["AXIGNAL_RUNTIME_ORIGIN", savedEnvironment.runtime], ["AXIGNAL_EXPERIENCE_ORIGIN", savedEnvironment.origin]] as const) {
    if (value === undefined) delete process.env[key]; else process.env[key] = value;
  }
});
const token = "a".repeat(48), tx = "b".repeat(48);
test("public landing enters real account routes only when identity is available and recovers from unavailable status", async () => {
  const html = readFileSync(new URL("../../landing/index.html", import.meta.url), "utf8");
  const script = html.slice(html.indexOf("async function openSubscriberAccess("), html.indexOf("$('loginButton').onclick="));
  for (const [status, intent, expected] of [
    [{ providers: [{ id: "google", status: "AVAILABLE" }] }, "signup", "/signup"],
    [{ providers: [{ id: "google", status: "AVAILABLE" }] }, "login", "/login"],
    [{ providers: [{ id: "google", status: "UNAVAILABLE" }] }, "signup", null],
    [{ providers: [{ id: "openai", status: "UNAVAILABLE" }] }, "login", null],
    [{}, "signup", null], [null, "login", null],
  ] as const) {
    let target: string | null = null, notices = 0;
    const sandbox = { fetch: async (path: string, options: RequestInit) => {
      assert.equal(path, "/api/auth/status"); assert.equal(options.cache, "no-store"); assert.equal(options.redirect, "error");
      if (status === null) throw new Error("Disconnected");
      return { ok: true, json: async () => status };
    }, AbortSignal, location: { assign: (value: string) => { target = value; } }, openAccessDialog: () => { notices++; } };
    runInNewContext(script, sandbox);
    await (sandbox as typeof sandbox & { openSubscriberAccess: (intent: string) => Promise<void> }).openSubscriberAccess(intent);
    assert.equal(target, expected); assert.equal(notices, expected ? 0 : 1);
  }
});
function setup() { process.env.AXIGNAL_RUNTIME_ORIGIN = "http://127.0.0.1:18181"; process.env.AXIGNAL_EXPERIENCE_ORIGIN = "https://axignal.com"; }
function request(body?: unknown, cookie = `__Host-axignal-subscriber=${token}`) {
  return new Request("https://axignal.com/api/subscriber/portfolio", { method: body === undefined ? "GET" : "POST", headers: { host: "axignal.com", origin: "https://axignal.com", cookie, "content-type": "application/json" }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
}
const projection = {
  realityLevel: "CONTROLLED_CONTRACT_TEST", runtimeCodeSha: "test", lifecycleStatus: "LIVE",
  context: { id: "focus:one", label: "Organization" }, organization: { id: "org:one", name: "Organization" },
  nodes: [], temporalHistory: { disposition: "EMPTY" as const, items: [] }, today: { disposition: "EMPTY", items: [] }, reloadContinuity: "PERSISTED_RUNTIME_READ_MODEL" as const,
};
const measurement = {
  kind: "DRI_PUBLIC_PAGE_REPRESENTATION", instrument: { ref: "page-title", version: "1" },
  surface: "PUBLIC_WEB_PAGE", resourceRef: "https://public.example/",
  source: { ref: "source:one", policyRef: "policy:one", policyVersion: "1", rightsBasisRef: null,
    rightsStatus: "UNKNOWN", accessStatus: "ACCESSIBLE", reuseScope: "PUBLIC", retentionPolicyRef: null, robotsPolicyRef: null },
  representation: { ref: "page:one", fingerprint: "captured-content", representationVersion: "1", normalizationVersion: "1" },
  observedAt: "2026-10-06T10:00:00Z", conditions: { geography: "UNKNOWN", language: "UNKNOWN", deviceContext: "UNKNOWN" },
  sample: { eligible: 1, informative: 1 }, currentness: "UNKNOWN",
  fields: [{ name: "canonical_organization_name_in_page_title", state: "MEASURED_ABSENCE_WITHIN_SCOPE", value: null }],
  uncertainty: "One captured page", humanMeaning: "Name missing from this title", scopeLimit: "One page only",
  representationGap: { type: "INXIGHT_REPRESENTATION_GAP", state: "MEASURED_ABSENCE_WITHIN_SCOPE",
    expectedPhrase: "Organization", measuredField: "title", scope: "One page", cause: "UNKNOWN", notEstablished: ["SEO performance"],
    contextRecommendation: { state: "CONTEXT_REQUIRED", condition: "Confirm page purpose and expected public name",
      requiredContext: { pagePurpose: "UNKNOWN", expectedPublicBrandName: "UNKNOWN" },
      recommendedAction: "Review with responsible team if confirmed", actionMode: "HUMAN_REVIEW_ONLY", performanceBenefit: "NOT_ESTABLISHED" },
  },
};

test("representation proxy retains bounded evidence and conditional context, strips private extensions and binds revision", async () => {
  setup(); let latest = measurement;
  globalThis.fetch = async () => Response.json({ state: "INSUFFICIENT_EVIDENCE", projection: { ...projection,
    digitalRepresentation: { ...latest, privateSourceBody: "private-capture", representationGap: { ...latest.representationGap,
      contextRecommendation: { ...latest.representationGap.contextRecommendation, internalActor: "private-principal" } } } } });
  const first = await (await subscriberProxy(request(), "/subscriber/organizations/focus%3Aone/output")).json();
  assert.equal(first.projection.digitalRepresentation.representationGap.contextRecommendation.requiredContext.pagePurpose, "UNKNOWN");
  assert.equal(first.projection.digitalRepresentation.source.rightsStatus, "UNKNOWN");
  assert.ok(!JSON.stringify(first).includes("private-capture")); assert.ok(!JSON.stringify(first).includes("private-principal"));
  latest = { ...measurement, observedAt: "2026-10-06T11:00:00Z" };
  const second = await (await subscriberProxy(request(), "/subscriber/organizations/focus%3Aone/output")).json();
  assert.notEqual(first.revision, second.revision);
});

test("representation context cannot silently become confirmed or promise performance", () => {
  assert.equal(digitalRepresentationSchema.safeParse(measurement).success, true);
  for (const alteration of [{ actionMode: "AUTOMATIC_EXECUTION" }, { performanceBenefit: "ESTABLISHED" },
    { requiredContext: { pagePurpose: "CONFIRMED", expectedPublicBrandName: "UNKNOWN" } }]) {
    assert.equal(digitalRepresentationSchema.safeParse({ ...measurement, representationGap: { ...measurement.representationGap,
      contextRecommendation: { ...measurement.representationGap.contextRecommendation, ...alteration } } }).success, false);
  }
  assert.equal(digitalRepresentationSchema.safeParse({ state: "NOT_MEASURED", reason: "Version mismatch",
    currentness: "UNKNOWN", recordedMeasurement: measurement }).success, true);
});

test("subscriber commands reject client authority and preserve exact capacity for 1/2/100", () => {
  for (const total of [1, 2, 100]) {
    const command = subscriberCommandSchema.parse({ action: "purchase", requestRef: "request:one", desiredOrganizationTotal: total });
    assert.ok("desiredOrganizationTotal" in command); assert.equal(command.desiredOrganizationTotal, total);
  }
  for (const extra of [{ tenantId: "other" }, { priceId: "price_forged" }, { paid: true }, { organizationId: "canonical" }]) assert.equal(subscriberCommandSchema.safeParse({ action: "add", locator: "public.example", requestRef: "request:one", ...extra }).success, false);
  for (const total of [true, 1.1, 0, -1, 100001]) assert.equal(subscriberCommandSchema.safeParse({ action: "expand", requestRef: "request:one", desiredOrganizationTotal: total }).success, false);
  assert.deepEqual([1, 2, 100].map(monthlyCapacityCents), [995, 1490, 50000]);
});
test("payment navigation accepts only exact Stripe HTTPS hosts", () => {
  assert.ok(approvedPaymentUrl("https://checkout.stripe.com/c/pay/cs_live_example"));
  for (const url of ["http://checkout.stripe.com/c", "https://checkout.stripe.com.evil.example/c", "https://u:p@invoice.stripe.com/c", "https://pay.stripe.com:8443/c"]) assert.equal(approvedPaymentUrl(url), null);
});

test("billing ingress preserves signed raw bytes and uses no subscriber identity", async () => {
  setup(); const raw = '{ "type": "invoice.paid", "data": {} }\n';
  globalThis.fetch = async (url, init) => {
    assert.equal(String(url), "http://127.0.0.1:18181/internal/webhooks/subscriber-stripe");
    assert.equal(Buffer.from(init!.body as Uint8Array).toString(), raw);
    const sent = new Headers(init?.headers);
    assert.equal(sent.get("stripe-signature"), "t=100,v1=signed");
    assert.equal(sent.get("authorization"), null);
    assert.equal(sent.get("cookie"), null);
    return Response.json({ accepted: true, disposition: "ACCEPTED", privateBody: "never" });
  };
  const response = await subscriberBillingWebhook(new Request("https://axignal.com/api/subscriber/billing/webhook", { method: "POST", headers: { "content-type": "application/json", "stripe-signature": "t=100,v1=signed" }, body: raw }));
  assert.deepEqual(await response.json(), { accepted: true, disposition: "ACCEPTED" });
});

test("unsigned and oversized billing ingress never reaches backend", async () => {
  setup(); let calls = 0; globalThis.fetch = async () => { calls++; throw new Error("not reached"); };
  for (const signed of [false, true]) {
    const response = await subscriberBillingWebhook(new Request("https://axignal.com/api/subscriber/billing/webhook", { method: "POST", headers: { "content-type": "application/json", ...(signed ? { "stripe-signature": "t=100,v1=signed" } : {}) }, body: signed ? "x".repeat(1_000_001) : "{}" }));
    assert.equal(response.status, signed ? 413 : 400);
  }
  assert.equal(calls, 0);
});
test("configured sign-in keeps browser transaction token solely in a secure HttpOnly cookie", async () => {
  setup();
  globalThis.fetch = async (_url, init) => {
    assert.deepEqual(JSON.parse(String(init?.body)), { provider: "google", intent: "signup" });
    return Response.json({ authorizationUrl: "https://accounts.google.com/o/oauth2/v2/auth?state=opaque", transactionToken: tx, ignoredSecret: "never-send" });
  };
  const response = await subscriberAuthStart({ provider: "google", intent: "signup" });
  assert.equal(response.status, 200);
  assert.match(response.headers.get("set-cookie")!, /Secure; HttpOnly; SameSite=Lax/);
  const payload = JSON.stringify(await response.json()); assert.ok(!payload.includes(tx)); assert.ok(!payload.includes("never-send"));
});
test("provider redirect rejection creates no transaction cookie", async () => {
  setup(); globalThis.fetch = async () => Response.json({ authorizationUrl: "https://evil.example/auth", transactionToken: tx });
  const response = await subscriberAuthStart({ provider: "google", intent: "login" });
  assert.equal(response.status, 503); assert.equal(response.headers.get("set-cookie"), null);
});
test("callback forwards only browser-bound transaction to fixed backend and returns no token in body or URL", async () => {
  setup(); globalThis.fetch = async (url, init) => {
    assert.equal(String(url), "http://127.0.0.1:18181/subscriber/auth/callback");
    assert.equal(JSON.parse(String(init?.body)).transactionToken, tx);
    return Response.json({ sessionToken: token, maxAge: 3600 });
  };
  const response = await subscriberAuthCallback(new Request("https://axignal.com/api/auth/callback/google?state=opaque&code=secret-code", { headers: { cookie: `__Host-axignal-oidc=${tx}` } }), "google");
  assert.equal(response.status, 303); assert.equal(response.headers.get("location"), "https://axignal.com/account");
  assert.ok(response.headers.get("set-cookie")?.includes("Max-Age=0")); assert.ok(response.headers.get("set-cookie")?.includes(token)); assert.equal(await response.text(), "");
});
test("callback without a unique transaction cookie or with duplicate state never exchanges the code", async () => {
  setup(); let calls = 0; globalThis.fetch = async () => { calls++; throw new Error("not reached"); };
  for (const [url, cookie] of [["?state=x&code=c", ""], ["?state=x&state=y&code=c", `__Host-axignal-oidc=${tx}`], ["?state=x&code=c", `__Host-axignal-oidc=${tx}; __Host-axignal-oidc=${tx}`]]) {
    const response = await subscriberAuthCallback(new Request("https://axignal.com/api/auth/callback/google" + url, { headers: { cookie } }), "google");
    assert.equal(response.headers.get("location"), "https://axignal.com/login?access=failed");
  }
  assert.equal(calls, 0);
});
test("subscriber proxy never substitutes Customer Zero or browser identity for its own session", async () => {
  setup(); let calls = 0; globalThis.fetch = async () => { calls++; throw new Error("not reached"); };
  assert.equal((await subscriberProxy(request(undefined, "axignal-admin-session=" + token), "/subscriber/portfolio")).status, 401);
  const crossSite = new Request("https://axignal.com/api/subscriber/portfolio", { method: "POST", headers: { origin: "https://evil.example", host: "axignal.com", cookie: `__Host-axignal-subscriber=${token}` }, body: "{}" });
  assert.equal((await subscriberProxy(crossSite, "/subscriber/portfolio", true)).status, 403);
  assert.equal(calls, 0);
});
test("revocation outage preserves cookie so sign-out is not falsely claimed", async () => {
  setup(); globalThis.fetch = async () => new Response(null, { status: 503 });
  const response = await subscriberLogout(request({})); assert.equal(response.status, 503); assert.equal(response.headers.get("set-cookie"), null);
});
test("streaming request limit is enforced without trusting Content-Length", async () => {
  await assert.rejects(() => boundedSubscriberJson(new Request("https://axignal.com", { method: "POST", headers: { "content-type": "application/json" }, body: "x".repeat(4097) })), /BODY_LIMIT/);
});
test("subscriber reading reauthorizes fresh output and refuses stale or foreign plans", async () => {
  setup(); let reads = 0;
  globalThis.fetch = async (url, init) => { reads++; assert.ok(String(url).endsWith("/focus%3Aone/output")); assert.equal(new Headers(init?.headers).get("authorization"), `Bearer ${token}`); return Response.json({ state: "INSUFFICIENT_EVIDENCE", projection, privateSource: "never-send" }); };
  const revision = createHash("sha256").update(JSON.stringify(projection)).digest("hex");
  const response = await reading(request({ focusId: "focus:one", revision, intent: "evidence", locale: "es" }));
  assert.equal(response.status, 200); const stream = await response.text();
  assert.ok(stream.includes("data-presentation")); assert.ok(stream.includes("DETERMINISTIC_EVIDENCE_PRESENTATION")); assert.ok(!stream.includes("never-send"));
  assert.equal((await reading(request({ focusId: "focus:one", revision: "f".repeat(64), intent: "summary", locale: "es" }))).status, 409);
  assert.equal(reads, 2);
  assert.equal(acceptsReadingPlan({ version: 1, revision, intent: "summary", refs: ["foreign:signal"], method: "DETERMINISTIC_EVIDENCE_PRESENTATION" }, projection, revision), false);
});
