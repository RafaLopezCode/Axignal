import test from "node:test";
import assert from "node:assert/strict";
import { insightsFor, weekHighlights, type Reading } from "../lib/observatory";
import { translate } from "../lib/copy-catalog";

const now = new Date("2026-10-17T12:00:00Z");
const day = (n: number) => new Date(now.getTime() - n * 86400000).toISOString();
const d = (kind: string, code: string, statement: string, observedAt: string, detail: Record<string, unknown> = {}) =>
  ({ kind, code, statement, epistemicState: "POTENTIAL", sourceUrl: "https://s.example/", excerpt: null, observedAt, detail });
const reading = (discoveries: unknown[]): Reading => ({ projection: null, firstObservation: {
  state: "FIRST_PROOF_READY", firstProofReady: true, discoveries } as unknown as Reading["firstObservation"] });
const t = (es: string, en: string) => translate(es, en, "en");

test("this week: three different kinds of news, consequential first, never older than 7 days (spec 088)", () => {
  const insights = insightsFor(reading([
    d("CHANGE", "presence:presence.ai_named_share:EVOLUTION", "0.25 -> 0.5", day(1), { previous: "0.25", comparison: "COMPARABLE" }),
    d("MENTION", "PRESS_MENTION", "Acme opens a plant", day(2), { outlet: "El Diario" }),
    d("DEMAND", "POTENTIAL_DEMAND", "Suministro de abono", day(3), { title: "Suministro de abono", isNew: true, focus: "BEST" }),
    d("DEMAND", "POTENTIAL_DEMAND", "Otra licitación nueva", day(4), { title: "Otra licitación nueva", isNew: true, focus: "BEST" }),
    d("CONTEXT_SIGNAL", "REGULATION", "Nueva norma", day(9)),  // older than a week: not news
    d("DEMAND", "POTENTIAL_DEMAND", "Lateral", day(1), { title: "Lateral", isNew: true, focus: "OTHER", otherReasons: ["ADJACENT_FIT"] }),
  ]), t, "en");
  const week = weekHighlights(insights, now).map(i => i.news);
  assert.deepEqual(week, ["NEW_DEMAND", "PRESS", "EVOLUTION"]);
});

test("nothing new in seven days says so: no filler", () => {
  const insights = insightsFor(reading([d("MENTION", "PRESS_MENTION", "Old news", day(30))]), t, "en");
  assert.deepEqual(weekHighlights(insights, now), []);
});
