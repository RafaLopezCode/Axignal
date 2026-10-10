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
  assert.deepEqual(adminSource.capabilities, { account: false, manage: false, recheck: true, axent: "admin" });
  assert.equal(accountSource.capabilities.account, true);
  assert.equal(typeof adminSource.command, "function");
  assert.equal(demoSource.command, undefined);
});

test("an Admin command adds attention or observes again, and refuses anything an account would purchase or manage", async () => {
  await withService(inventoryRoute, async calls => {
    const signal = new AbortController().signal;
    const posts = () => calls.filter(call => call.url === "/api/xeeds");
    assert.deepEqual(await adminSource.command!({ action: "add", locator: "empresa.com" }, "r1", signal), { state: "ACCEPTED", observationState: "COMPLETED" });
    assert.deepEqual(posts()[0], { url: "/api/xeeds", body: { action: "add", name: "empresa.com", targetUri: "https://empresa.com/" } });
    assert.deepEqual(await adminSource.command!({ action: "add", locator: "Empresa SL" }, "r2", signal), { state: "WEBSITE_REQUIRED" });
    assert.equal(posts().length, 1, "a name without a site never reaches the service");
    await adminSource.command!({ action: "reobserve", focusId: "xeed_1" }, "r3", signal);
    assert.deepEqual(posts()[1], { url: "/api/xeeds", body: { action: "reobserve", id: "xeed_1" } });
    for (const action of ["purchase", "expand", "pause", "remove", "replace"]) await assert.rejects(adminSource.command!({ action }, "r4", signal), /COMMAND_NOT_AVAILABLE/);
  });
});

test("Customer Zero reads through the one Observatory: no reading interface of its own", () => {
  const entry = read("components/customer-zero-observatory.tsx");
  assert.match(entry, /<SubscriberPortfolioExperience source=\{adminSource\}/);
  assert.doesNotMatch(entry, /<(main|section|nav|aside|header|button)\b/);
  // The shared components read capabilities, never the context.
  assert.doesNotMatch(read("components/observatory.tsx"), /source\.mode|adminSource|mode ===/);
});

test("inside the Admin shell there is one sidebar: the portfolio navigation is drawn in the shell's own", () => {
  const css = read("components/observatory.css");
  assert.match(css, /\.obs-in-shell \.obs-rail-brand, \.obs-in-shell \.obs-rail-locale \{ display: none; \}/);
  const observatory = read("components/observatory.tsx");
  assert.match(observatory, /props\.shell \? \(props\.shell\.host \? createPortal\(/);
  assert.match(observatory, /\{!props\.shell && <MobileBar/);
  const entry = read("components/customer-zero-observatory.tsx");
  assert.match(entry, /shell=\{embedded \? \{ host: navigationHost \?\? null, active, onNavigate \} : undefined\}/);
  // The language lives in the shell's top bar, once.
  assert.match(entry, /createPortal\(<>[\s\S]*<LocaleToggle\/>[\s\S]*<\/>, toolbarHost\)/);
});

function withService(routes: (url: string, body: unknown) => Response | undefined, run: (calls: Array<{ url: string; body: unknown }>) => Promise<void>) {
  const calls: Array<{ url: string; body: unknown }> = [];
  const original = globalThis.fetch;
  globalThis.fetch = (async (url: string, init?: RequestInit) => {
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ url: String(url), body });
    return routes(String(url), body) ?? new Response("{}", { status: 200 });
  }) as typeof fetch;
  return run(calls).finally(() => { globalThis.fetch = original; });
}
const withAvailable = organizationInventorySchema.parse({
  ...inventory, available: [{ name: "Cooperativa Ribera", targetUri: "https://ribera.example/" }],
  organizations: [...inventory.organizations, { id: "xeed_3", requestedLabel: "Revocada", name: "Revocada", organizationId: "org_3", targetUri: "https://revocada.example/", state: "AUTHORIZATION_REVOKED", projectionContextId: "ctx_3" }],
});
const inventoryRoute = (url: string) => url === "/api/organizations" ? Response.json(withAvailable) : undefined;
const signal = new AbortController().signal;

test("the authorized organizations are offered while adding, and a chosen name carries the address the service holds", async () => {
  await withService(inventoryRoute, async calls => {
    assert.deepEqual(await adminSource.suggestions!(signal), ["Cooperativa Ribera"]);
    await adminSource.command!({ action: "add", locator: "cooperativa ribera" }, "r", signal);
    assert.deepEqual(calls.at(-1), { url: "/api/xeeds", body: { action: "add", name: "Cooperativa Ribera", targetUri: "https://ribera.example/" } });
  });
});

test("an attention without an organization is asked again with the label and address it already holds", async () => {
  await withService(inventoryRoute, async calls => {
    await adminSource.command!({ action: "retry_pending", focusId: "xeed_2" }, "r", signal);
    assert.deepEqual(calls.at(-1), { url: "/api/xeeds", body: { action: "add", name: "Pendiente", targetUri: "https://pendiente.example/" } });
    // An identified organization or a revoked authorization is not asked again.
    for (const focusId of ["xeed_1", "xeed_3", "missing"]) await assert.rejects(adminSource.command!({ action: "retry_pending", focusId }, "r", signal), /COMMAND_NOT_AVAILABLE/);
  });
});

test("the service's answers keep their meaning: unresolved identity and insufficient evidence are saved, not concluded", async () => {
  for (const [status, expected] of [[202, { state: "IDENTITY_PENDING", reason: "UNRESOLVED" }], [422, { state: "ACCEPTED", observationState: "INSUFFICIENT_EVIDENCE" }], [200, { state: "ACCEPTED", observationState: "COMPLETED" }]] as const) {
    await withService(() => new Response("{}", { status }), async () => {
      assert.deepEqual(await adminSource.command!({ action: "reobserve", focusId: "xeed_1" }, "r", signal), expected, String(status));
    });
  }
  await withService(() => new Response("{}", { status: 401 }), async () => {
    assert.equal(await adminSource.command!({ action: "reobserve", focusId: "xeed_1" }, "r", signal), "SESSION_REQUIRED");
  });
});

test("a revoked authorization is listed with its reason and is never opened as a reading", () => {
  const revoked = adminPortfolio(withAvailable).organizations.find(item => item.focusId === "xeed_3")!;
  assert.equal(revoked.organizationId, null);
  assert.equal(revoked.reason, "AUTHORIZATION_REVOKED");
  assert.match(read("components/observatory.tsx"), /item\.reason === "AUTHORIZATION_REVOKED"/);
});

test("Customer Zero is functional, never synthetic: it reads the service and nothing from the demonstration", () => {
  for (const file of ["lib/admin-source.ts", "components/customer-zero-observatory.tsx", "components/customer-zero.tsx"]) {
    const text = read(file);
    assert.doesNotMatch(text, /lib\/demo|synthetic|demoSource|syntheticPortfolio/i, file);
  }
  // The only reads are the Admin session's: the attention inventory and the governed runtime projection.
  const endpoints = [...read("lib/admin-source.ts").matchAll(/"(\/api\/[a-z-]+)"/g)].map(match => match[1]);
  assert.deepEqual([...new Set(endpoints)].sort(), ["/api/organizations", "/api/subscriber-context", "/api/xeeds"]);
});

test("inside the shell the reading and the sidebar keep one rhythm: no stray indentation, no flush blocks", () => {
  const shell = read("components/observatory.css");
  assert.match(shell, /\.obs\.obs-in-shell \{ margin-block: 8px 12px; \}/);
  assert.match(shell, /\.obs-in-shell \.obs-rail-head \{ padding-inline: 12px; \}/);
  const canvas = read("components/customer-zero-observatory.css");
  // The staff controls and the technical reading align with the reading's own gutters.
  assert.match(canvas, /\.obs-customer-zero \.obs-cz-staff \{ padding: 0; margin-block-end: 14px; \}/);
  assert.match(canvas, /\.obs-cz-detail \{ margin: 8px clamp\(20px, 3vw, 44px\) 40px;/);
});

test("the Admin menu is one system: shell entries and the portfolio navigation share type, radius and states", () => {
  const css = read("components/admin-menu.css");
  assert.match(css, /--menu-radius: 9px;/);
  // The hierarchy runs titles over functions: a group title is larger, heavier and darker than the entries under it,
  // and the functions share one size and weight whether they come from the shell or from the portfolio.
  assert.match(css, /\.admin-shell > \.product-sidebar \.nav-group-label \{[^}]*font-family: var\(--font-ui\); font-size: 14px; font-weight: 800;[^}]*color: var\(--menu-title\);/);
  assert.match(css, /\.admin-nav-group > \.admin-nav-item \{ font-family: var\(--font-ui\); font-size: var\(--type-control\); font-weight: var\(--weight-control\); \}/);
  assert.match(css, /\.obs-rail-head h2 \{ font-family: var\(--font-ui\); font-size: 14px; font-weight: 800;/);
  assert.match(css, /\.admin-shell \.obs-in-shell \.obs-org \{ border-radius: var\(--menu-radius\); \}/);
  // The radius is the global scale's control radius, so the menu cannot drift from it.
  assert.equal(read("components/observatory.css").match(/--obs-r-control:\s*([^;]+);/)?.[1].trim(), "9px");
});

test("the Admin carries no sample records and no demonstration label", () => {
  const admin = read("components/admin.tsx");
  assert.doesNotMatch(admin, /adminRecords|DemoLabel|ilustrativ|illustrative|\/api\/admin\/action/i);
  const model = read("lib/admin-model.ts");
  assert.doesNotMatch(model, /ilustrativ|illustrative|\bdemo\b|\bexample\b|\bejemplo\b|AdminRecord/i);
});

test("every Admin function stays in the menu; a domain not yet connected says so and shows nothing", () => {
  const admin = read("components/admin.tsx");
  const model = read("lib/admin-model.ts");
  const ids = [...model.matchAll(/id: "([a-z]+)"/g)].map(match => match[1]);
  assert.deepEqual(ids, ["command", "customers", "acquisition", "revenue", "focus", "quality", "brain", "governance", "integrations", "finance", "advisor", "system"]);
  // The menu is grouped the way the operator works: observe, operate, govern; the attention centre stays one click away.
  assert.match(admin, /GROUPS\.map\(group =>/);
  assert.match(admin, /href="\/admin#command"/);
  // Only a connected domain draws content; the others state that nothing is connected and render no record.
  assert.match(model, /connectedDomains: ReadonlySet<string> = new Set\(\["customers"\]\)/);
  assert.match(admin, /!connectedDomains\.has\(domain\.id\)/);
  assert.doesNotMatch(admin, /adminRecords/);
});

test("the phone drawer is modal: a real scrim closes it, the page behind does not scroll, targets fit a thumb", () => {
  const admin = read("components/admin.tsx");
  assert.match(admin, /\{mobile && <div className="admin-scrim" aria-hidden="true" onClick=\{\(\) => setMobile\(false\)\} \/>\}/);
  assert.match(admin, /document\.body\.style\.overflow = "hidden"/);
  const css = read("components/admin-menu.css");
  assert.match(css, /\.admin-scrim \{ position: fixed; inset: 0; z-index: 29;/);
  // The drawer sits above its scrim; the scrim covers the page, which the old in-drawer pseudo-element never did.
  assert.match(css, /\.product-sidebar\.mobile-open::after \{ display: none; \}/);
  assert.match(css, /\.icon-button, \.admin-shell \.product-sidebar \.obs-icon \{ min-inline-size: 44px; min-block-size: 44px; \}/);
});
