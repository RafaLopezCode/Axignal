import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { discoveryCopy, observationStateCopy } from "../components/first-observation";
import { evidenceUrl, firstObservationSchema, observationStates, pendingOutputSchema, portfolioSchema, subscriberResultSchema, type Discovery } from "../lib/subscriber-contracts";
import { subscriberProxy } from "../lib/subscriber-server";

const savedFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = savedFetch; });
const token = "a".repeat(48);
const en = (_es: string, english: string) => english;
const es = (spanish: string) => spanish;

function discovery(kind: Discovery["kind"], code: string, extra: Partial<Discovery> = {}): Discovery {
  return { kind, code, statement: "Statement", epistemicState: "POTENTIAL", sourceUrl: null, excerpt: null, observedAt: "2026-10-08T10:00:00+00:00", detail: {}, ...extra };
}

// Every code the Python First Observation emits (application/first_observation/service.py).
const BACKEND_UNKNOWN_CODES = ["IDENTITY_NOT_VERIFIED", "WEBSITE_LINK_NOT_REGISTRY_VERIFIED", "ACTIVITY_NOT_ESTABLISHED", "LOCATION_NOT_DECLARED", "DEMAND_NOT_ROUTABLE", "NO_ROUTABLE_DEMAND_QUESTION", "NO_RELEVANT_DEMAND_FOUND", "NOT_AN_OPERATING_BUSINESS_SITE", "NO_PUBLIC_WEBSITE"];

test("every backend unknown code has its own fixed copy, never a generic or generated one", () => {
  const generic = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", "ROBOTS_DISALLOWED"), en).finding;
  for (const code of BACKEND_UNKNOWN_CODES) {
    const copy = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", code), en);
    assert.notEqual(copy.finding, generic, code);
    assert.ok(copy.why.length > 10, code);
  }
  const gap = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", "NO_GOVERNED_DEMAND_SOURCE:US/US-AR", { detail: { jurisdiction: "US/US-AR" } }), en);
  assert.match(gap.finding, /Arkansas, United States/);  // a place a person reads, not a code
  assert.match(gap.why, /not no market/);
  for (const state of observationStates) assert.ok(observationStateCopy(state, es).length > 10, state);
});

test("findings explain why they matter without promoting potential to fact", () => {
  const demand = discoveryCopy(discovery("DEMAND", "POTENTIAL_DEMAND", { detail: { title: "Solar works" } }), en);
  assert.match(demand.finding, /Solar works/);
  assert.match(demand.why, /not a customer/);
  assert.match(discoveryCopy(discovery("ACTIVITY", "isic-P"), en).why, /not a verified capability/);
  assert.match(discoveryCopy(discovery("IDENTITY_HINT", "LEGAL_NAME_DECLARED"), en).why, /Only a registry/);
  assert.match(discoveryCopy(discovery("REPRESENTATION_GAP", "OFFER_NOT_MACHINE_READABLE"), en).why, /not a measured cause/);
});

test("only public http(s) evidence links are rendered", () => {
  assert.equal(evidenceUrl("https://ted.europa.eu/en/notice/-/detail/1"), "https://ted.europa.eu/en/notice/-/detail/1");
  for (const value of ["javascript:alert(1)", "https://user:secret@example.com/", "data:text/html,x", "not a url", null]) {
    assert.equal(evidenceUrl(value), null, String(value));
  }
});

test("new observation states are accepted end to end", () => {
  for (const state of ["QUEUED", "CAPACITY_REQUIRED"]) {
    assert.equal(subscriberResultSchema.safeParse({ state: "IDENTITY_PENDING", observationState: state }).success, true);
  }
  const portfolio = portfolioSchema.parse({ state: "success", capacity: 1, capacityCurrentness: "CURRENT", canPurchase: null, contractingEnabled: false,
    organizations: [{ focusId: "pending_abc", organizationId: null, label: "https://example.com", state: "IDENTITY_PENDING", reason: "IDENTITY_SOURCE_UNAVAILABLE",
      observation: { state: "FIRST_PROOF_READY", firstProofReady: true, headline: "Education", observedAt: "2026-10-08T10:00:00+00:00" } }] });
  assert.equal(portfolio.organizations[0].observation?.state, "FIRST_PROOF_READY");
  assert.equal(firstObservationSchema.safeParse({ state: "INVENTED", firstProofReady: true, discoveries: [] }).success, false);
});

test("pending attention output passes the proxy and drops the private ledger", async () => {
  process.env.AXIGNAL_RUNTIME_ORIGIN = "http://127.0.0.1:18181"; process.env.AXIGNAL_EXPERIENCE_ORIGIN = "https://axignal.com";
  globalThis.fetch = async () => Response.json({ state: "success", kind: "PENDING_ATTENTION", firstObservation: {
    state: "FIRST_PROOF_READY", firstProofReady: true, authority: "OPERATIONAL_NOT_CANONICAL",
    target: { kind: "PENDING", website: "https://example.com/", name: null, identityLink: "IDENTITY_PENDING" },
    discoveries: [discovery("ACTIVITY", "isic-P", { sourceUrl: "https://example.com/", excerpt: "Spanish classes." })],
    ledger: { httpRequests: { value: 3, basis: "MEASURED" } }, judged: { isicSection: "P" } } });
  const response = await subscriberProxy(new Request("https://axignal.com/api/subscriber/organizations/pending_abc/output", { headers: { host: "axignal.com", cookie: `__Host-axignal-subscriber=${token}` } }), "/subscriber/organizations/pending_abc/output");
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(pendingOutputSchema.safeParse(body).success, true);
  assert.equal(body.firstObservation.discoveries[0].excerpt, "Spanish classes.");
  assert.ok(!JSON.stringify(body).includes("httpRequests"));
});
