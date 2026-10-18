import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { LocaleProvider } from "../lib/locale";
import { insightsFor, type Reading } from "../lib/observatory";
import type { Discovery, FirstObservation } from "../lib/subscriber-contracts";
import { VisibilityCanvas } from "../components/family-canvas";

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
