import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { LocaleProvider } from "../lib/locale";
import { insightsFor, type Reading } from "../lib/observatory";
import type { Discovery, FirstObservation } from "../lib/subscriber-contracts";
import { FamilyCanvas, VisibilityCanvas } from "../components/family-canvas";
import { translate } from "../lib/copy-catalog";

const when = "2026-10-17T10:00:00+00:00";
const d = (kind: Discovery["kind"], code: string, statement: string, detail: Record<string, unknown>, epistemicState: Discovery["epistemicState"] = "OBSERVED"): Discovery =>
  ({ kind, code, statement, epistemicState, sourceUrl: null, excerpt: null, observedAt: when, detail }) as Discovery;

function render(discoveries: Discovery[]): string {
  const reading: Reading = { projection: null, firstObservation: { state: "FIRST_PROOF_READY", firstProofReady: true, discoveries } as FirstObservation };
  const insights = insightsFor(reading, (_es, en) => en, "en");
  return renderToStaticMarkup(createElement(LocaleProvider, null, createElement(VisibilityCanvas, { reading, insights, onOpen: () => undefined })));
}

test("Visibilidad's canvas reads the production measurements as they are (design base phase 2)", () => {
  const markup = render([
    d("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", "2/6", { instrument: { model: "assistant-x" }, sample: "6 category questions", measuredAt: when,
      shareOfVoice: 0.11, averagePosition: 3.5, competitorFrequency: [["Rumbo", 5], ["Faro", 4]] }),
    d("GENERATIVE_VISIBILITY", "AI_CITED_SOURCES", "guias.example", { sitesCited: [["guias.example", 3]] }),
    d("GENERATIVE_VISIBILITY", "AI_KNOWS_BRAND", "Demo", {}),
    d("SEARCH_VISIBILITY", "SEARCH_RANKS_MEASURED", "1/2", { rows: [
      { keyword: "humus de lombriz", position: 2, googleUrl: "https://www.google.com/search?q=humus+de+lombriz" },
      { keyword: "abono", position: null, googleUrl: "javascript:alert(1)" }] }),
    d("WEB_REPRESENTATION", "PUBLIC_WEB_REPRESENTATION_MEASURED", "checks", { audit: { checks: [
      { section: "SEARCH_FINDABILITY", status: "PASS" }, { section: "SEARCH_FINDABILITY", status: "ATTENTION" }, { section: "AI_ANSWER_READINESS", status: "UNKNOWN" }] } }),
    d("DECLARED_SERVICE_AREA", "SITE_VERSIONS_FOR_COUNTRIES", "ES, FR", { countries: { ES: ["HREFLANG"], FR: ["COUNTRY_DOMAIN"] } }, "DECLARED"),
  ]);
  assert.match(markup, /aria-label="Share of voice: 11% of the organizations named"/);
  assert.match(markup, />11%</);
  assert.match(markup, /2 of 6/);
  assert.match(markup, /Rumbo/);
  assert.match(markup, /guias\.example/);
  assert.match(markup, /«humus de lombriz»/);
  assert.match(markup, /position 2/);
  assert.match(markup, /not in the top 20/);
  assert.equal((markup.match(/https:\/\/www\.google\.com\/search/g) ?? []).length, 1, "only Google search links are rendered");
  assert.doesNotMatch(markup, /javascript:/);
  assert.match(markup, /Search findability|SEARCH_FINDABILITY|findability/i);
  assert.match(markup, /Spain, France/);
  assert.match(markup, /Observed/);
  assert.match(markup, /Declared/);
});

test("a panel with nothing measured says so and is unknown, never zero", () => {
  const markup = render([]);
  assert.equal((markup.match(/Not measured yet/g) ?? []).length, 2);
  assert.match(markup, /Its website could not be read yet/);
  assert.match(markup, /Its website declares no languages or country versions/);
  assert.equal((markup.match(/>Unknown</g) ?? []).length, 4);
  assert.doesNotMatch(markup, />0%</);
});

// Phase 3: any other family as a canvas.
const t = (es: string, en: string) => translate(es, en, "es");
const month = (k: number) => new Date(new Date().getFullYear(), new Date().getMonth() - k, 10).toISOString();
const mention = (code: string, url: string, k: number) => ({ kind: "MENTION", code, statement: `Acme ${code} ${k}`, epistemicState: "POTENTIAL",
  sourceUrl: url, excerpt: "… Acme …", observedAt: month(k), detail: { outlet: new URL(url).hostname, notEndorsement: true } });
const reading = (discoveries: unknown[]): Reading => ({ projection: null,
  firstObservation: { state: "FIRST_PROOF_READY", firstProofReady: true, discoveries } } as unknown as Reading);

test("a family canvas shows states, the most telling findings, months and sources, each with its proof", () => {
  const insights = insightsFor(reading([
    mention("WEB_MENTION", "https://www.expansion.com/a", 0),
    mention("WEB_MENTION", "https://www.expansion.com/b", 2),
    mention("REVIEW_PAGE", "https://www.ocu.org/r", 1),
    mention("REVIEW_PAGE", "https://www.ocu.org/s", 14),  // older than the window
  ]), t, "es");
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "reputation", title: "Reputación", insights, onOpen() {} }));
  // Rendered without a locale provider: the English copy.
  for (const title of ["What has been observed", "The most important", "Over time", "Where it comes from"]) assert.match(html, new RegExp(title));
  assert.match(html, /Potential/);  // the state in words, never color alone
  assert.equal((html.match(/class="obs-months"/g) ?? []).length, 1);
  assert.equal((html.match(/<li style="--i:\d+">/g) ?? []).length >= 12, true);
  assert.match(html, /\(1 earlier\)/);  // the finding older than twelve months is said, not hidden
  assert.match(html, /expansion\.com/);
  assert.match(html, /Show me how AXIGNAL knows/);
  // The most important: same rank, the most recent first (the 14-month-old review last).
  assert.ok(html.indexOf("REVIEW_PAGE 1<") < html.indexOf("REVIEW_PAGE 14<"));
  assert.doesNotMatch(html, /\/100|universal/i);  // counts, never a score
});

test("a family with fewer than two known findings gets no canvas: the lanes already say it", () => {
  const insights = insightsFor(reading([
    mention("WEB_MENTION", "https://www.expansion.com/a", 0),
    { kind: "SIGNIFICANT_UNKNOWN", code: "NO_PRESS_MENTION_FOUND", statement: "x", epistemicState: "UNKNOWN", sourceUrl: null, excerpt: null, observedAt: month(0), detail: {} },
  ]), t, "es");
  assert.equal(renderToStaticMarkup(createElement(FamilyCanvas, { family: "reputation", title: "Reputación", insights, onOpen() {} })), "");
});

// The panel compares calendar deadlines with local today; UTC serialization can
// silently move this fixture to yesterday around local midnight.
const inDays = (n: number) => {
  const day = new Date(); day.setDate(day.getDate() + n);
  return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
};
const call = (title: string, days: number, fit: string) => ({ kind: "DEMAND", code: "POTENTIAL_DEMAND", statement: title, epistemicState: "POTENTIAL",
  sourceUrl: "https://ted.europa.eu/x", excerpt: null, observedAt: month(0), detail: { deadline: inDays(days), fit, buyer: "Ayuntamiento" } });

test("Demand's canvas shows open calls by deadline and their fit, never past deadlines", () => {
  const r = reading([call("Paneles solares escuela", 20, "CORE"), call("Alumbrado público", 5, "PARTIAL"), call("Obra cerrada", -3, "CORE")]);
  const insights = insightsFor(r, t, "es");
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "demand", title: "Demanda", insights, onOpen() {}, reading: r }));
  assert.match(html, /Upcoming deadlines/);
  assert.ok(html.indexOf("in 5 days") >= 0 && html.indexOf("in 5 days") < html.indexOf("in 20 days"), "soonest first");
  assert.doesNotMatch(html, /Obra cerrada<\/button>/);  // a past deadline is not upcoming
  assert.match(html, /Fit with its activity/);
  assert.match(html, /Its main work/);
  assert.doesNotMatch(html, /Over time/);  // deadlines replace the generic months
});

test("Economics' canvas tells each figure's source kind and year apart", () => {
  const fact = (code: string, kind: string, year: string) => ({ kind: "ECONOMIC_FACT", code, statement: "120000000", epistemicState: "POTENTIAL",
    sourceUrl: "https://example.org/f", excerpt: null, observedAt: month(0), detail: { fact: "revenue", value: 120000000, unit: "EUR", year, sourceKind: kind, source: "x" } });
  const r = reading([fact("WIKIDATA:revenue", "SECONDARY_COMMUNITY_EDITED", "2023"), fact("REPORTED:revenue", "THIRD_PARTY_REPORT", "2025")]);
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "economics", title: "Economía", insights: insightsFor(r, t, "es"), onOpen() {}, reading: r }));
  assert.match(html, /Figures, their source and year/);
  assert.match(html, /Wikidata/);
  assert.match(html, /Third-party report/);
  assert.match(html, /2025/);
});

test("Relationships' canvas draws ties around the organization and keeps their epistemic state", () => {
  const tie = (kind: string, code: string, statement: string, state: string) => ({ kind, code, statement, epistemicState: state,
    sourceUrl: "https://example.org/r", excerpt: null, observedAt: month(0), detail: {} });
  const r = reading([
    tie("RELATIONSHIP", "PUBLIC_CONTRACT_AWARDED", "Ayuntamiento de Bilbao", "OBSERVED"),
    tie("RELATIONSHIP", "PARTNER_DECLARED", "Siemens", "DECLARED"),
    tie("RELATIONSHIP", "VALUE_CHAIN_SUPPLIERS", "Sector metal", "POTENTIAL"),
    tie("COMPETITION", "SAME_MARKET_COMPETITOR", "Acciona", "POTENTIAL"),
  ]);
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "relationships", title: "Relaciones", insights: insightsFor(r, t, "es"), onOpen() {}, reading: r, organization: "Ingeteam" }));
  assert.match(html, /Who it is tied to/);
  assert.match(html, /Ingeteam and 3 ties/);
  assert.match(html, /stroke-dasharray="6 4"/);  // declared
  assert.match(html, /stroke-dasharray="2 4"/);  // potential
  assert.doesNotMatch(html, /Sector metal<\/button>/);  // sectors are not organizations
  assert.match(html, /is not a confirmed one/);
});

test("Activity's canvas shows its pace as counted facts and what happened, newest first", () => {
  const ev = (kind: string, code: string, statement: string, at: string, detail: Record<string, unknown> = {}) => ({ kind, code, statement, epistemicState: "OBSERVED",
    sourceUrl: "https://example.org/a", excerpt: null, observedAt: at, detail });
  const r = reading([
    ev("OPERATING_SIGNAL", "PUBLISHING_CADENCE", "4 in 90 days", month(0), { last90Days: 4 }),
    ev("OPERATING_SIGNAL", "WEBSITE_HISTORY", "2009-03-01", month(0)),
    ev("MENTION", "OWN_PUBLICATION", "Nueva planta en Valencia", month(2)),
    ev("MENTION", "OWN_PUBLICATION", "Informe anual", month(1)),
  ]);
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "activity", title: "Actividad", insights: insightsFor(r, t, "es"), onOpen() {}, reading: r }));
  assert.match(html, /Its pace/);
  assert.match(html, /Own publications in 90 days/);
  assert.match(html, /2009/);
  assert.match(html, /What happened/);
  assert.match(html, /not an absence of activity/);
  assert.doesNotMatch(html, /\/100|score of/i);
});

test("Organization's canvas shows each identity anchor with its state, and that only a registry admits", () => {
  const hint = (kind: string, code: string, statement: string, state: string, detail: Record<string, unknown> = {}) => ({ kind, code, statement, epistemicState: state,
    sourceUrl: "https://example.org/legal", excerpt: null, observedAt: month(0), detail });
  const r = reading([
    hint("IDENTITY_HINT", "LEGAL_NAME_DECLARED", "Ecoalf Recycled Fabrics S.L.", "DECLARED"),
    hint("IDENTITY_HINT", "IDENTIFIER_DECLARED:ES_NIF", "ES_NIF B86040357", "DECLARED"),
    hint("IDENTITY_HINT", "IDENTITY_CORROBORATED", "Ecoalf Recycled Fabrics S.L.", "POTENTIAL",
      { anchors: [{ anchor: "WIKIDATA_OFFICIAL_WEBSITE", value: "Q123" }, { anchor: "OFFICIAL_REGISTER", value: "B86040357" }] }),
    hint("SIGNIFICANT_UNKNOWN", "IDENTITY_NOT_VERIFIED", "x", "UNKNOWN"),
  ]);
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "organization", title: "Organización", insights: insightsFor(r, t, "es"), onOpen() {}, reading: r }));
  assert.match(html, /Who it is, anchor by anchor/);
  assert.match(html, /Ecoalf Recycled Fabrics S\.L\./);
  assert.match(html, /Q123/);
  assert.match(html, /Not found yet/);  // no LEI: not found yet, never false
  assert.match(html, /Admitted by a registry/);
  assert.match(html, /corroboration, not an admission/);
});
