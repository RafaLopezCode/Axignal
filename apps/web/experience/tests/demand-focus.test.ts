import test from "node:test";
import assert from "node:assert/strict";
import { briefing, byLane, insightsFor, otherDemandOf, type Reading } from "../lib/observatory";
import { translate } from "../lib/copy-catalog";

const at = "2026-10-17T09:00:00Z";
const call = (title: string, detail: Record<string, unknown>) =>
  ({ kind: "DEMAND", code: "POTENTIAL_DEMAND", statement: title, epistemicState: "POTENTIAL", sourceUrl: "https://placsp.example/1", excerpt: null, observedAt: at, detail: { title, ...detail } });
const reading: Reading = { projection: null, firstObservation: { state: "FIRST_PROOF_READY", firstProofReady: true,
  demand: { live: true, asOf: at, total: 3, new: 0, best: 1 },
  discoveries: [
    call("Suministro de abono orgánico", { focus: "BEST", otherReasons: [] }),
    call("Mantenimiento de zonas verdes", { focus: "OTHER", otherReasons: ["SECONDARY_ACTIVITY"] }),
    call("Obras de urbanización", { focus: "OTHER", otherReasons: ["ADDITIONAL_CODE", "ADJACENT_FIT"] }),
  ] } as unknown as Reading["firstObservation"] };

test("what fits best leads; the rest is apart, each saying why (spec 087)", () => {
  const t = (es: string, en: string) => translate(es, en, "en");
  const insights = insightsFor(reading, t, "en");
  const matters = byLane(insights).matters.map(i => i.headline);
  assert.equal(matters.length, 1);
  assert.match(matters[0], /abono/);
  const others = otherDemandOf(insights);
  assert.equal(others.length, 2);
  assert.match(others[0].why, /secondary activity/);
  assert.match(others[1].why, /additional code.*main work is something else/);
  const { tally } = briefing(reading, "Biocultor", insights, t, "en");
  assert.ok(tally.includes("1 open tender that fits best"), tally.join(" | "));
  assert.ok(tally.includes("2 other possible ones, with their reason"), tally.join(" | "));
});
