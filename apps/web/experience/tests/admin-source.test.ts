/**
 * Customer Zero is the Admin's AXIGNAL: the one Observatory over the Admin session's source.
 * The Admin adds organizations as attention, never through checkout, and has no account to manage.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { adminPortfolio, adminSource, attentionFromLocator } from "../lib/admin-source";
import { accountSource } from "../lib/observatory-source";
import { demoSource } from "../lib/demo/synthetic-source";
import { organizationInventorySchema } from "../lib/organization-attention";

const read = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

const inventory = organizationInventorySchema.parse({
  accessMode: "INTERNAL_ADMIN", canObserve: true, selectedId: "xeed_1",
  organizations: [
    { id: "xeed_1", requestedLabel: "Axignal", name: "AXIGNAL", organizationId: "org_1", targetUri: "https://axignal.com/", state: "LIVE", projectionContextId: "ctx_1" },
    { id: "xeed_2", requestedLabel: "Pendiente", name: null, organizationId: null, targetUri: "https://pendiente.example/", state: "IDENTITY_UNRESOLVED", projectionContextId: null },
  ],
  available: [],
});

test("a locator becomes the label and public address an attention needs", () => {
  assert.deepEqual(attentionFromLocator("empresa.com"), { name: "empresa.com", targetUri: "https://empresa.com/" });
  assert.deepEqual(attentionFromLocator("https://www.empresa.com/es"), { name: "empresa.com", targetUri: "https://www.empresa.com/es" });
  // A name alone, an address with credentials or an internal host is not a public site to observe.
  for (const bad of ["", "Empresa SL", "https://user:pass@empresa.com", "localhost", "ftp://empresa.com"]) assert.equal(attentionFromLocator(bad), null, bad);
});

test("the Admin portfolio is the inventory read as the Observatory's: readable when identified, pending when not", () => {
  const portfolio = adminPortfolio(inventory);
  assert.equal(portfolio.organizations.length, 2);
  assert.deepEqual(portfolio.organizations.map(item => item.state), ["ACTIVE", "IDENTITY_PENDING"]);
  assert.equal(portfolio.organizations[0].label, "AXIGNAL");
  // The unresolved attention keeps its reason; nothing is invented about it.
  assert.equal(portfolio.organizations[1].organizationId, null);
  assert.equal(portfolio.organizations[1].reason, "IDENTITY_UNRESOLVED");
});

test("an Admin has no capacity, purchase or contracting: capacity is unknown, never zero or free", () => {
  const portfolio = adminPortfolio(inventory);
  assert.equal(portfolio.capacity, null);
  assert.equal(portfolio.capacityCurrentness, "UNKNOWN");
  assert.equal(portfolio.canPurchase, false);
  assert.equal(portfolio.contractingEnabled, false);
  // Nothing in the Admin source reaches a payment or subscriber endpoint.
  const source = read("lib/admin-source.ts");
  assert.doesNotMatch(source, /\/api\/subscriber\/|checkoutUrl|stripe\.com/i);
});

test("the three contexts expose one source contract; only data and capabilities differ", () => {
  for (const source of [accountSource, demoSource, adminSource]) {
    assert.equal(typeof source.readPortfolio, "function");
    assert.equal(typeof source.readOutput, "function");
    assert.ok(source.capabilities);
  }
  assert.equal(adminSource.mode, "admin");
  assert.equal(adminSource.canAct, true);
  assert.deepEqual(adminSource.capabilities, { account: false, manage: false, axent: "admin" });
  assert.equal(accountSource.capabilities.account, true);
  assert.equal(typeof adminSource.command, "function");
  assert.equal(demoSource.command, undefined);
});

test("an Admin command adds attention or observes again, and refuses anything an account would purchase or manage", async () => {
  const calls: Array<{ url: string; body: unknown }> = [];
  const original = globalThis.fetch;
  globalThis.fetch = (async (url: string, init?: RequestInit) => {
    calls.push({ url: String(url), body: init?.body ? JSON.parse(String(init.body)) : null });
    return new Response("{}", { status: 200 });
  }) as typeof fetch;
  try {
    const signal = new AbortController().signal;
    assert.deepEqual(await adminSource.command!({ action: "add", locator: "empresa.com" }, "r1", signal), { state: "ACCEPTED", observationState: "COMPLETED" });
    assert.deepEqual(calls[0], { url: "/api/xeeds", body: { action: "add", name: "empresa.com", targetUri: "https://empresa.com/" } });
    assert.deepEqual(await adminSource.command!({ action: "add", locator: "Empresa SL" }, "r2", signal), { state: "WEBSITE_REQUIRED" });
    assert.equal(calls.length, 1, "a name without a site never reaches the service");
    await adminSource.command!({ action: "reobserve", focusId: "xeed_1" }, "r3", signal);
    assert.deepEqual(calls[1], { url: "/api/xeeds", body: { action: "reobserve", id: "xeed_1" } });
    for (const action of ["purchase", "expand", "pause", "remove", "replace"]) await assert.rejects(adminSource.command!({ action }, "r4", signal), /COMMAND_NOT_AVAILABLE/);
  } finally { globalThis.fetch = original; }
});

test("Customer Zero reads through the one Observatory: no reading interface of its own", () => {
  const entry = read("components/customer-zero-observatory.tsx");
  assert.match(entry, /<SubscriberPortfolioExperience source=\{adminSource\}/);
  assert.doesNotMatch(entry, /<(main|section|nav|aside|header|button)\b/);
  // The shared components read capabilities, never the context.
  assert.doesNotMatch(read("components/observatory.tsx"), /source\.mode|adminSource|mode ===/);
});

test("inside the Admin shell the rail does not repeat the brand the shell already carries", () => {
  assert.match(read("components/customer-zero-observatory.css"), /\.obs-customer-zero \.obs-rail-brand \{ display: none; \}/);
});
