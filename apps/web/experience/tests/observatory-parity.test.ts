/**
 * Parity between /account and /demo. They are one product experience: the same Observatory, in two contexts.
 * The only thing that may differ is the source (where data comes from) and the capabilities it grants.
 * These tests fail when a visual or functional capability is added to one surface and not the other.
 * They do not compare permissions: the demo must stay unable to act.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { accountSource, type ObservatorySource } from "../lib/observatory-source";
import { demoSource, syntheticOutput } from "../lib/demo/synthetic-source";
import snapshot from "../lib/demo/synthetic-observatory.json";
import { locales } from "../lib/languages";
import { CHANNEL_ORDER, FAMILY_ORDER } from "../lib/observation-families";
import { insightsFor } from "../lib/observatory";
import { pendingOutputSchema, subscriberOutputSchema } from "../lib/subscriber-contracts";

const read = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");
const en = (_es: string, english: string) => english;

test("/account and /demo mount the same Observatory container; only the source differs", () => {
  assert.match(read("app/account/page.tsx"), /<SubscriberPortfolioExperience\s*\/>/);
  assert.match(read("components/demo-observatory.tsx"), /<SubscriberPortfolioExperience source=\{demoSource\}/);
  const container = read("components/subscriber-portfolio.tsx");
  assert.match(container, /source = accountSource/);
  assert.match(container, /import \{ Observatory \} from "\.\/observatory"/);
});

test("pages are thin: no route carries Observatory interface of its own", () => {
  const allowed = ["@/components/subscriber-portfolio", "@/components/demo-observatory"];
  for (const page of ["app/account/page.tsx", "app/demo/page.tsx", "app/preview/subscriber/page.tsx"]) {
    const text = read(page);
    for (const [, target] of text.matchAll(/from "(@\/components\/[^"]+)"/g)) assert.ok(allowed.includes(target), `${page} imports ${target}`);
    assert.doesNotMatch(text, /className=|<(main|section|nav|aside|button|header)\b/, page);
  }
});

test("there is one subscriber Observatory implementation", () => {
  const observatories = readdirSync(resolve(process.cwd(), "components")).filter(file => /observatory\.tsx$/.test(file)).sort();
  // demo-observatory is only the demonstration entry: it mounts the container with the demo source and adds no interface.
  // landing-observatory is the marketing window and customer-zero-observatory the Admin entry; neither is the subscriber reading. customer-zero-observatory mounts the container over the Admin source.
  assert.deepEqual(observatories, ["customer-zero-observatory.tsx", "demo-observatory.tsx", "landing-observatory.tsx", "observatory.tsx"]);
  assert.doesNotMatch(read("components/demo-observatory.tsx"), /className=|<(main|section|nav|aside|button|header)\b/);
});

test("shared components never ask which context they run in", () => {
  for (const file of ["components/observatory.tsx", "components/family-nav.tsx", "components/subscriber-portfolio.tsx", "lib/observation-families.ts", "lib/observatory.ts"]) {
    const text = read(file);
    assert.doesNotMatch(text, /source\.mode|isDemo|demoSource|"demo"|mode ===/, file);
  }
  // Capabilities reach the components as one flag, never as a second tree.
  assert.match(read("components/observatory.tsx"), /canAct: boolean/);
});

test("both contexts expose the same source contract and differ only in data and capability", () => {
  const sources: ObservatorySource[] = [accountSource, demoSource];
  for (const source of sources) {
    assert.equal(typeof source.readPortfolio, "function");
    assert.equal(typeof source.readOutput, "function");
    assert.equal(typeof source.canAct, "boolean");
    assert.equal(typeof source.localized, "boolean");
  }
  assert.equal(accountSource.canAct, true);
  assert.equal(demoSource.canAct, false);
  assert.equal(accountSource.mode, "account");
  assert.equal(demoSource.mode, "demo");
});

test("the demo reads its snapshot only: no network, no storage, in every locale and for every organization", async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = (async () => { calls += 1; throw new Error("the demo must not use the network"); }) as typeof fetch;
  try {
    const signal = new AbortController().signal;
    for (const { id } of locales) {
      const portfolio = await demoSource.readPortfolio(signal, id);
      assert.notEqual(portfolio, "SESSION_REQUIRED");
      if (portfolio === "SESSION_REQUIRED") continue;
      assert.equal(portfolio.organizations.length, snapshot.portfolio.length);
      for (const organization of portfolio.organizations) {
        const payload = await demoSource.readOutput(organization.focusId, signal, id) as { kind?: string };
        if (payload.kind === "PENDING_ATTENTION") pendingOutputSchema.parse(payload); else subscriberOutputSchema.parse(payload);
      }
    }
  } finally { globalThis.fetch = originalFetch; }
  assert.equal(calls, 0);
  assert.doesNotMatch(read("lib/demo/synthetic-source.ts"), /fetch\(|\/api\/|localStorage|sessionStorage|\/admin/);
});

test("the demo cannot act and says so in its own words", () => {
  const demo = read("components/demo-observatory.tsx");
  assert.match(demo, /<DemoNotice\/>/);
  assert.match(read("components/demo-notice.tsx"), /role="note"/);
  assert.match(read("components/demo-notice.tsx"), /datos ficticios", "Guided example · fictional data/);
});

test("the same reading pipeline serves both contexts: every organization yields findings placed by typed values only", () => {
  for (const organization of snapshot.portfolio) {
    const payload = syntheticOutput(organization.focusId, "en") as { kind?: string };
    if (payload.kind === "PENDING_ATTENTION") continue;
    const output = subscriberOutputSchema.parse(payload);
    const insights = insightsFor({ projection: output.projection, firstObservation: output.firstObservation ?? null }, en, "en");
    for (const insight of insights) {
      assert.ok(insight.family === null || FAMILY_ORDER.includes(insight.family), insight.id);
      if (insight.channel) assert.equal(insight.family, "presence", insight.id);
    }
  }
});

test("thematic navigation is part of the shared Observatory: ten families, three channels, in the URL, on every filtered view", () => {
  assert.equal(FAMILY_ORDER.length, 10);
  assert.deepEqual([...CHANNEL_ORDER], ["SEO", "GEO", "WEB"]);
  const observatory = read("components/observatory.tsx");
  assert.match(observatory, /<FamilyNav /);
  assert.match(observatory, /searchParams\.get\("family"\)/);
  assert.match(observatory, /searchParams\.get\("channel"\)/);
  assert.match(observatory, /<EvolutionView reading=\{reading\} facet=\{facet\}/);
  assert.match(observatory, /<EvidenceView reading=\{reading\} facet=\{facet\}/);
  assert.match(observatory, /scope=\{scope\}/);
});

test("the shared Observatory keeps its four states: loading, sign-in required, failure and ready", () => {
  const observatory = read("components/observatory.tsx");
  for (const state of ["loading", "required", "failure"]) assert.match(observatory, new RegExp(`access === "${state}"`));
  assert.match(observatory, /access: "loading" \| "required" \| "failure" \| "ready"/);
});

test("responsive: the family bar scrolls sideways on narrow screens with touch-sized targets, and wraps on wide ones", () => {
  const css = read("components/observatory.css");
  const narrow = css.slice(css.indexOf("@media (max-width: 699px)", css.indexOf(".obs-facets {")));
  assert.match(narrow, /\.obs-facet-nav ul[^{]*\{[^}]*overflow-x: auto/);
  assert.match(narrow, /\.obs-facet \{[^}]*min-block-size: 44px/);
  assert.match(css, /\.obs-facet-nav ul[^{]*\{[^}]*flex-wrap: wrap/);
  assert.match(css, /prefers-reduced-motion: reduce\) \{ \.obs-facet/);
});
