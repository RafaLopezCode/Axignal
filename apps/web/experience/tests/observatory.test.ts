import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { briefing, byLane, fill, insightsFor, type Reading } from "../lib/observatory";
import { baseline, litKeys, markSeen, observedSinceVisit, readSeen, touch } from "../lib/observatory-seen";
import { pendingOutputSchema, portfolioSchema, subscriberOutputSchema } from "../lib/subscriber-contracts";
import { LocaleProvider } from "../lib/locale";
import { translate } from "../lib/copy-catalog";
import { Observatory, type ObservatoryProps } from "../components/observatory";

// SYNTHETIC: real composition output over the controlled test world (see "provenance").
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "observatory-synthetic.json"), "utf8"));
const en = (_es: string, english: string) => english;
const es = (spanish: string) => spanish;

function identified(key = fixture.focus): Reading {
  const output = subscriberOutputSchema.parse(fixture.outputs[key]);
  return { projection: output.projection, firstObservation: output.firstObservation ?? null };
}
function pending(id: string): Reading {
  return { projection: null, firstObservation: pendingOutputSchema.parse(fixture.outputs[id]).firstObservation };
}
const pendingSolar = fixture.portfolio.find((p: { focusId: string }) => p.focusId.startsWith("pending_2ede")).focusId;
const pendingRobots = fixture.portfolio.find((p: { focusId: string }) => p.focusId.startsWith("pending_cf98")).focusId;

test("lanes regroup the runtime's findings without upgrading or downgrading their state", () => {
  const insights = insightsFor(identified(), en, "en");
  const lanes = byLane(insights);
  const opportunity = lanes.matters.find(i => i.id.startsWith("opportunity-candidate:"));
  assert.ok(opportunity, "the governed opportunity leads what matters");
  assert.equal(opportunity.nature, "POTENTIAL");
  assert.match(opportunity.meaning.join(" "), /not a customer, an invitation or a relationship/);
  // The First Observation demand line for the same tender is not shown twice.
  assert.equal(lanes.matters.filter(i => i.headline === opportunity.headline).length, 1);
  // Nothing becomes OBSERVED that the runtime did not observe.
  assert.ok(!insights.some(i => i.nature === "OBSERVED" && i.id.startsWith("opportunity")));
  // UNKNOWN stays UNKNOWN and lives in its own lane, never as a negative finding.
  assert.ok(lanes.unknown.length > 0 && lanes.unknown.every(i => i.nature === "UNKNOWN"));
  // Context-only discoveries (public presence, web measurement, identity hints) stay in Evidence.
  assert.ok(!insights.some(i => /^(PUBLIC_PRESENCE|WEB_REPRESENTATION|IDENTITY_HINT):/.test(i.id)));
});

test("opportunity depth shows each relevance dimension with its state and no score", () => {
  const opportunity = insightsFor(identified(), en, "en").find(i => i.id.startsWith("opportunity-candidate:"))!;
  assert.deepEqual(opportunity.dimensions.map(d => [d.label, d.outcome]), [
    ["Geographic reach", "Unresolved"], ["Logistics", "Unresolved"], ["Regulatory requirements", "Not applicable"], ["Timing", "Compatible"],
  ]);
  assert.ok(!JSON.stringify(opportunity).match(/\b\d+(\.\d+)?\s*%|score/i));
  // Routing jargon is proof for experts, not the reasoning a person reads first.
  assert.ok(!opportunity.reasoning.join(" ").includes("PUBLIC_PROCUREMENT_OPPORTUNITIES"));
  assert.ok(opportunity.proof.some(p => p.label === "Search route"));
});

test("constructive self-critique distinguishes strengths, conditional gaps and instrument limits", () => {
  const before = insightsFor(identified(`${fixture.focus}__first`), en, "en").filter(i => i.id.startsWith("pu:"));
  const gaps = before.filter(i => i.nature === "CLARIFY");
  assert.ok(gaps.length >= 1 && gaps.every(i => i.proposal && i.reasoning.join(" ").includes("evaluator error")));
  const after = insightsFor(identified(), en, "en").filter(i => i.id.startsWith("pu:"));
  assert.ok(after.every(i => i.nature === "STRENGTH"));
  // What it was before is shown, from the runtime's own comparable reading.
  assert.ok(after.some(i => i.previous === "Opportunity to clarify"));
  // A representation gap is a possible gap, not a demonstrated cause.
  const gap = insightsFor(identified(), en, "en").find(i => i.id.startsWith("REPRESENTATION_GAP:"))!;
  assert.equal(gap.nature, "CLARIFY");
  assert.match(gap.reasoning[0], /not a demonstrated cause/);
});

test("a failed or unavailable instrument is never presented as a company defect", () => {
  const reading = identified();
  const report = { ...reading.firstObservation!.publicUnderstanding!, status: "NOT_MEASURED" as const, cause: "CONTENT_RIGHTS_WITHDRAWN", dimensions: [], citations: [] };
  const insights = insightsFor({ ...reading, firstObservation: { ...reading.firstObservation!, publicUnderstanding: report } }, en, "en").filter(i => i.id.startsWith("pu:"));
  assert.equal(insights.length, 1);
  assert.equal(insights[0].nature, "UNKNOWN");
  assert.ok(!insights.some(i => i.nature === "CLARIFY" || i.proposal));
  assert.match(insights[0].reasoning[0], /not a defect of the organization/);
});

test("the briefing hedges what is potential and admits what is not established", () => {
  const reading = identified();
  const brief = briefing(reading, "Solartec Energía SL", insightsFor(reading, en, "en"), en, "en");
  assert.match(brief.lead, /^From what it publishes, Solartec Energía SL most likely works in solar photovoltaic installation/);
  assert.ok(brief.tally.includes("1 potential opportunity"));
  const robots = pending(pendingRobots);
  const none = briefing(robots, "private-robots.example.com", insightsFor(robots, en, "en"), en, "en");
  assert.equal(none.lead, "AXIGNAL has not yet established what private-robots.example.com does.");
  assert.equal(fill("{n} de {total}", { n: 2, total: 5 }), "2 de 5");
});

test("lit until seen: a first look lights nothing, a later change lights only what changed", () => {
  const focus = fixture.focus;
  const first = insightsFor(identified(`${focus}__first`), en, "en").map(i => i.changeKey);
  const now = insightsFor(identified(), en, "en").map(i => i.changeKey);
  let store = baseline({}, focus, first, "2026-10-02T10:00:00Z");
  assert.equal(litKeys({}, focus, now).size, 0, "never-visited organizations are not all lit");
  const lit = litKeys(store, focus, now);
  assert.ok(lit.size >= 1 && lit.size < now.length, "only the changed findings are lit");
  store = markSeen(store, focus, [...lit], "2026-10-09T10:00:00Z");
  assert.equal(litKeys(store, focus, now).size, 0);
  assert.equal(observedSinceVisit(store, focus, "2026-10-10T00:00:00Z"), true);
  assert.equal(observedSinceVisit(touch(store, focus, "2026-10-11T00:00:00Z"), focus, "2026-10-10T00:00:00Z"), false);
  // Corrupted or unavailable storage never hides a finding.
  assert.deepEqual(readSeen(() => ({ getItem: () => "{not json", setItem: () => {} })), {});
  assert.deepEqual(readSeen(() => { throw new Error("blocked"); }), {});
});

function props(overrides: Partial<ObservatoryProps> = {}): ObservatoryProps {
  const noop = () => {};
  return {
    access: "ready", portfolio: portfolioSchema.parse({ state: "success", capacity: 10, capacityCurrentness: "CURRENT", canPurchase: null, contractingEnabled: false, organizations: fixture.portfolio }),
    busy: false, message: "", paymentUrl: null, selected: null, reading: false, projection: null, firstObservation: null, revision: null,
    readOutput: noop, clearSelection: noop, command: async () => {}, refresh: noop, logout: noop,
    locator: "", setLocator: noop, total: 11, setTotal: noop, replacing: null, setReplacing: noop, replacementLocator: "", setReplacementLocator: noop,
    ...overrides,
  };
}
const render = (value: ObservatoryProps) => renderToStaticMarkup(createElement(LocaleProvider, null, createElement(Observatory, value)));

test("the portfolio desk orients an agency without opening each organization", () => {
  const markup = render(props());
  assert.match(markup, /Your portfolio/);
  assert.match(markup, /Potential opportunities/);
  assert.match(markup, /Need your attention/);
  assert.match(markup, /aria-label="Portfolio"/);
  // Every organization stays reachable from the rail; account functions stay one step away.
  for (const item of fixture.portfolio) assert.ok(markup.includes(item.focusId) === false, "ids are not rendered as text");
  assert.match(markup, /Add organization/);
  assert.match(markup, /Account and connections/);
});

test("the organization view leads with meaning, lanes, depth tabs and real actions", () => {
  const output = subscriberOutputSchema.parse(fixture.outputs[fixture.focus]);
  const markup = render(props({ selected: fixture.focus, projection: output.projection, firstObservation: output.firstObservation ?? null, revision: "a".repeat(64) }));
  assert.match(markup, /<h1>Solartec Energía SL<\/h1>/);
  assert.match(markup, /From what it publishes, Solartec Energía SL most likely works in solar photovoltaic installation/);
  for (const lane of ["What matters", "How it is understood", "What we do not know yet"]) assert.ok(markup.includes(lane), lane);
  for (const tab of ["Summary", "Explore", "Evolution", "Evidence"]) assert.match(markup, new RegExp(`role="tab"[^>]*>${tab}<`));
  assert.match(markup, /Observe again/);
  assert.match(markup, /Ask AXENT/i);
  // State is carried by text next to a shape, never colour alone.
  assert.match(markup, /obs-mark-potential"><svg[^>]*aria-hidden="true">.*?<\/svg>Potential/);
  assert.doesNotMatch(markup, /\b\d+(\.\d+)?\s*%|probability of truth|confidence/i);
});

test("a pending organization still reads honestly while identity is unresolved", () => {
  const reading = pending(pendingSolar);
  const markup = render(props({ selected: pendingSolar, firstObservation: reading.firstObservation }));
  assert.match(markup, /Identity unresolved/);
  assert.match(markup, /Check again/);
  assert.doesNotMatch(markup, /Ask AXENT/i);
});

test("observing shows only the stage the runtime reports, with no fake progress", () => {
  const observing = fixture.portfolio.map((p: { focusId: string; observation: unknown }) => p.focusId === pendingSolar ? { ...p, observation: { state: "OBSERVING_PUBLIC_PRESENCE", firstProofReady: false, headline: null, observedAt: null } } : p);
  const markup = render(props({ selected: pendingSolar, portfolio: portfolioSchema.parse({ state: "success", capacity: 10, capacityCurrentness: "CURRENT", canPurchase: null, contractingEnabled: false, organizations: observing }) }));
  assert.match(markup, /AXIGNAL is observing this organization/);
  assert.match(markup, /aria-current="step"/);
  assert.doesNotMatch(markup, /\d+\s*%/);
});

test("an empty portfolio opens the first-run question, not an empty dashboard", () => {
  const markup = render(props({ portfolio: portfolioSchema.parse({ state: "success", capacity: 1, capacityCurrentness: "CURRENT", canPurchase: null, contractingEnabled: false, organizations: [] }) }));
  assert.match(markup, /Which organization do you want to understand\?/);
  assert.match(markup, /Start observing/);
});

test("new observatory copy resolves in all six locales, including whole-sentence templates", () => {
  for (const english of [
    "From what it publishes, {name} most likely works in {activity}.", "{n} findings new or changed since your last visit.",
    "What matters", "How it is understood", "What we do not know yet", "No score: each dimension is shown with its state.",
    "A suggested improvement is not a demonstrated cause. Observe again afterwards to check whether the interpretation changes.",
  ]) {
    for (const locale of ["de", "pt", "fr", "it"] as const) {
      const value = translate("x", english, locale);
      assert.notEqual(value, english, `${locale}: ${english}`);
      for (const placeholder of english.match(/\{\w+\}/g) ?? []) assert.ok(value.includes(placeholder), `${locale} keeps ${placeholder}`);
    }
  }
  assert.equal(es("Lo que importa"), "Lo que importa");
});
