import test from "node:test";
import assert from "node:assert/strict";
import { familyValue, type Insight } from "../lib/observatory";
import { FAMILY_ORDER } from "../lib/observation-families";

function insight(id: string, family: Insight["family"], extra: Partial<Insight> = {}): Insight {
  return { id, family, lane: "understood", nature: "OBSERVED", headline: id, why: "", observedAt: "2026-10-17T09:00:00Z",
    meaning: [], reasoning: [], proposal: null, sources: [], proof: [], dimensions: [], previous: null, changeKey: id, channel: null, ...extra } as Insight;
}

test("every family gets one row, in the fixed family order (spec 093)", () => {
  const rows = familyValue([]);
  assert.deepEqual(rows.map(r => r.family), [...FAMILY_ORDER]);
  assert.ok(rows.every(r => r.pick === null && r.unknown === null && r.findings === 0));
});

test("a crossing comes first, then the family's most telling finding, by a visible order", () => {
  const rows = familyValue([
    insight("LANGUAGES:LANGUAGES_PUBLISHED:0", "presence"),
    insight("GENERATIVE_VISIBILITY:AI_KNOWS_BRAND:1", "presence"),
    insight("GENERATIVE_VISIBILITY:AI_NOT_NAMED_FOR_CATEGORY:2", "presence"),
    insight("MENTION:WIKIPEDIA_NOTORIETY:3", "reputation"),
    insight("MENTION:PRESS_MENTION:4", "reputation", { observedAt: "2026-10-01T00:00:00Z" }),
    insight("INXIGHT:demand:OPEN_DEMAND_OFFER_NOT_DECLARED:5", "demand", { nature: "POTENTIAL" }),
    insight("DEMAND:POTENTIAL_BUYER:6", "demand", { nature: "POTENTIAL" }),
  ]);
  const by = Object.fromEntries(rows.map(r => [r.family, r]));
  assert.equal(by.presence.pick?.id, "GENERATIVE_VISIBILITY:AI_NOT_NAMED_FOR_CATEGORY:2");
  assert.equal(by.presence.findings, 3);
  assert.equal(by.reputation.pick?.id, "MENTION:PRESS_MENTION:4");
  assert.equal(by.demand.pick?.id, "INXIGHT:demand:OPEN_DEMAND_OFFER_NOT_DECLARED:5");
});

test("a family with nothing observed names what is unknown, never another family's value", () => {
  const rows = familyValue([
    insight("SIGNIFICANT_UNKNOWN:NO_PRESS_MENTION_FOUND:0", "reputation", { nature: "UNKNOWN", lane: "unknown" }),
    insight("DEMAND:POTENTIAL_DEMAND:1", "demand", { group: "otherDemand", nature: "POTENTIAL" }),
  ]);
  const by = Object.fromEntries(rows.map(r => [r.family, r]));
  assert.equal(by.reputation.pick, null);
  assert.equal(by.reputation.unknown?.id, "SIGNIFICANT_UNKNOWN:NO_PRESS_MENTION_FOUND:0");
  assert.equal(by.reputation.findings, 0);
  assert.equal(by.demand.pick, null, "a call set apart as other possible is never a family's headline");
});
