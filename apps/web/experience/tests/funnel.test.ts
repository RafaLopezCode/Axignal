import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import sitemap from "../app/sitemap";
import { funnelCta, funnelPayload, landingChapters, exampleDepth } from "../lib/funnel-events";
import { gardenAt } from "../lib/cognition/facts";
import { makeContext, project } from "../lib/projection";

// Spec 060: the public funnel is a contract, not a mood. These tests read the public
// surfaces' source so a regression (a staff link, a second demo, prototype copy) fails
// before anyone has to notice it in a browser.
const root = path.resolve(import.meta.dirname, "..");
const read = (file: string) => fs.readFileSync(path.join(root, file), "utf8");
const PUBLIC_SURFACES = [
  "components/landing.tsx",
  "components/landing-extras.tsx",
  "components/landing-observatory.tsx",
  "components/public-shell.tsx",
  "components/ui.tsx",
  "components/access.tsx",
  "components/panorama.tsx",
  "components/economic-garden.tsx",
  "components/axent.tsx",
  "app/api/axent/route.ts",
];
const PUBLIC_ROUTES = new Set([
  "/", "/demo", "/signup", "/login", "/knowledge", "/contact", "/policies", "/gdpr",
  "/policies/terms", "/policies/privacy", "/policies/cookies", "/knowledge/basis/product-model",
]);
const literalHrefs = (source: string) =>
  [...source.matchAll(/href[=:]\s*\{?"(\/[^"#?]*)/g)].map((match) => match[1]);

test("public surfaces link only to public destinations, never to staff tools", () => {
  for (const file of PUBLIC_SURFACES) {
    for (const href of literalHrefs(read(file))) {
      assert.ok(PUBLIC_ROUTES.has(href), `${file} links to non-public ${href}`);
    }
  }
});

test("there is one public example and every 'show me' converges on it", () => {
  const landing = read("components/landing.tsx");
  assert.match(landing, /export const EXAMPLE_HREF = "\/demo";/);
  for (const file of PUBLIC_SURFACES) {
    const source = read(file);
    assert.doesNotMatch(source, /["'`]\/(examples?|dashboard|tour)\b/, `${file} opens a second demo route`);
  }
  // Landing example links are built from the one constant, never retyped.
  assert.doesNotMatch(landing, /href="\/demo/);
});

test("no public copy makes the product feel like a prototype", () => {
  const prototype = [
    /Esta demo/i, /This demo/i, /versión local/i, /local version/i, /datos ilustrativos/i,
    /illustrative data/i, /revisión visual humana/i, /human visual review/i, /\bDemo ·/,
    /sesión de demostración/i, /para revisión/i, /for review/i,
  ];
  for (const file of PUBLIC_SURFACES) {
    // The staff-only Admin label shares ui.tsx; it never renders on a public page.
    const source = read(file).replace(/"Vista privada · datos ilustrativos",\s*"Private view · illustrative data",/, "");
    for (const pattern of prototype) assert.doesNotMatch(source, pattern, `${file}: ${pattern}`);
  }
});

test("the home page is in the sitemap", () => {
  assert.ok(sitemap().some((entry) => entry.url === "https://axignal.com/"));
});

test("funnel events reuse the AO-12 contract and stay within its bounds", () => {
  const kinds = new Set(["LANDING_VIEWED", "CHAPTER_VIEWED", "CTA_ACTIVATED"]);
  const context = { session: "session:" + "a".repeat(32), locale: "es-ES", path: "/", referrer: null, now: new Date("2026-10-08T10:00:00Z"), id: "b".repeat(32) };
  const events = [
    { kind: "LANDING_VIEWED", surface: "landing" } as const,
    ...Object.values(landingChapters).map((chapter) => ({ kind: "CHAPTER_VIEWED", surface: "landing", chapter }) as const),
    ...Object.values(exampleDepth).map((chapter) => ({ kind: "CHAPTER_VIEWED", surface: "example", chapter }) as const),
    ...Object.values(funnelCta).map((cta) => ({ kind: "CTA_ACTIVATED", surface: "landing", cta }) as const),
  ];
  for (const event of events) {
    const payload = funnelPayload(event, context);
    assert.ok(kinds.has(payload.kind));
    assert.match(payload.eventId, /^[a-z][a-z0-9:_-]{2,159}$/);
    assert.match(payload.sessionRef, /^[a-z][a-z0-9:_-]{2,159}$/);
    assert.equal(payload.locale, "es");
    if ("chapter" in event) assert.ok(event.chapter >= 1 && event.chapter <= 15 && payload.chapter === event.chapter);
    if ("cta" in event) assert.ok(event.cta.length <= 120 && payload.cta === event.cta);
    // No identity, ever: the endpoint rejects these fields as PII.
    for (const field of ["email", "name", "userId", "principalId", "companyName"]) assert.ok(!(field in payload));
  }
});

test("measurement stays inert unless the runtime reports the model enabled", () => {
  const source = read("lib/funnel-events.ts");
  assert.match(source, /data\.enabled === true/);
  assert.match(source, /OBSERVED_TOUCH_V1/);
});

test("the example garden keeps reach, expansion and exposure apart", () => {
  const garden = gardenAt("norte", "2026-10-03");
  assert.ok(garden);
  assert.ok(garden.operating.every((place) => place.state === "OBSERVED" && place.source));
  assert.ok(garden.expansion.every((place) => place.state === "POTENTIAL"));
  // Expansion needs the organization's own act; demand elsewhere is never expansion.
  assert.ok(garden.expansion.every((place) => place.source?.id !== "src-programme"));
  assert.ok(garden.unknown.every((place) => place.state === "UNKNOWN" && !place.source));
  assert.ok(garden.exposure.length > 0);
  // Before the hiring evidence existed, the expansion is not known yet.
  const july = gardenAt("norte", "2026-07-01");
  assert.equal(july?.expansion.length, 0);
  assert.equal(gardenAt("atlas", "2026-10-03"), null);
});

test("the landing glance shows all three epistemic states from the same example", () => {
  const now = project(makeContext("norte", "markets", "2026-10-03"));
  const states = new Set(
    ["renovation", "representation", "reputation-gap"].map((id) => now.signals.find((signal) => signal.id === id)?.epistemic),
  );
  assert.deepEqual([...states].sort(), ["OBSERVED", "POTENTIAL", "UNKNOWN"]);
});

test("the subscriber reading shows the real garden with the example's grammar, never stronger", async () => {
  const { gardenFromRuntime } = await import("../lib/runtime-garden");
  const { runtimeCognitionSchema } = await import("../lib/runtime-projection");
  const place = (geography: string, stated: boolean, current: boolean) => ({
    geography, label: geography === "EU/ES/ES3/ES30" ? "Comunidad de Madrid" : null, mode: "CUSTOMER_SITE",
    stated, current, evidence: "obs:home:1", source: "https://solartec.example/",
    excerpt: "Instalamos autoconsumo fotovoltaico en la Comunidad de Madrid.", observedAt: "2026-10-01T09:00:00+00:00",
  });
  const cognition = runtimeCognitionSchema.parse({
    asOf: "2026-10-08T00:00:00+00:00", sources: [], signals: [], opportunities: [],
    economicGarden: {
      operatingModelFingerprint: "fp", exposureChannels: ["FUEL_AND_TRAVEL", "NOT_A_CHANNEL"], evidence: ["obs:home:1"],
      capabilities: [
        { capabilityId: "solar", label: "Solar", deliveryModes: ["CUSTOMER_SITE"], operating: [place("EU/ES/ES3/ES30", false, true), place("EU/ES/ES3/ES30", true, true)], expansion: [place("EU/ES/ES5/ES52/ES523", true, true)], excluded: [], unknown: [] },
        { capabilityId: "monitoring", label: "Monitoring", deliveryModes: ["DIGITAL"], operating: [place("EU/ES", false, false)], expansion: [], excluded: [], unknown: [] },
      ],
    },
  });
  const garden = gardenFromRuntime(cognition.economicGarden, cognition.asOf);
  assert.ok(garden);
  const madrid = garden.operating.find((p) => p.code === "EU/ES/ES3/ES30");
  assert.equal(garden.operating.filter((p) => p.code === "EU/ES/ES3/ES30").length, 1);
  assert.equal(madrid?.state, "OBSERVED");
  assert.equal(madrid?.label.es, "Comunidad de Madrid");
  assert.equal(madrid?.source?.observedAt, "2026-10-01T09:00:00+00:00");
  // Site-wide or stale statements are POTENTIAL; expansion is never OBSERVED.
  assert.equal(garden.operating.find((p) => p.code === "EU/ES")?.state, "POTENTIAL");
  assert.equal(garden.operating.find((p) => p.code === "EU/ES")?.currentness, "STALE");
  assert.ok(garden.expansion.every((p) => p.state === "POTENTIAL"));
  assert.deepEqual(garden.exposure.map((e) => e.id), ["FUEL_AND_TRAVEL"]);
  // A malformed garden degrades to nothing; it never breaks the reading.
  const broken = runtimeCognitionSchema.parse({ asOf: "2026-10-08", sources: [], signals: [], opportunities: [], economicGarden: { nope: true } });
  assert.equal(broken.economicGarden, undefined);
  assert.equal(gardenFromRuntime(undefined, "2026-10-08"), null);
});

test("the landing's living window is the one public example, honestly labelled and time-faithful", async () => {
  const { exampleInsights, exampleNewSince, EXAMPLE_ORGANIZATION } = await import("../lib/landing-observatory");
  const copy = (value: { en: string }) => value.en;
  assert.equal(EXAMPLE_ORGANIZATION, "norte");
  // Only what was available at each moment is shown; nothing from later leaks backwards.
  const july = exampleInsights("2026-07-01", copy).map((i) => i.id);
  const october = exampleInsights("2026-10-03", copy).map((i) => i.id);
  assert.ok(!july.includes("renovation") && !july.includes("representation"));
  assert.ok(october.includes("renovation") && october.includes("representation"));
  // Epistemic state passes through unchanged: potential stays potential, unknown stays unknown.
  const now = exampleInsights("2026-10-03", copy);
  assert.equal(now.find((i) => i.id === "renovation")?.nature, "POTENTIAL");
  assert.equal(now.find((i) => i.id === "reputation-gap")?.nature, "UNKNOWN");
  // The lamps light exactly what appeared since the previous moment.
  assert.deepEqual([...exampleNewSince("2026-09-01")], ["renovation"]);
  assert.deepEqual([...exampleNewSince("2026-10-03")], ["representation"]);
  assert.equal(exampleNewSince("2026-07-01").size, 0);
  const window = read("components/landing-observatory.tsx");
  assert.match(window, /Organización ficticia/);
  assert.match(window, /InsightCard|InsightBody/);
});
