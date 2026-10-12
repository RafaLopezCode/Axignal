import { test } from "node:test";
import assert from "node:assert/strict";
import { exampleInsights, selectedExampleInsight } from "../lib/landing-observatory";
import { focusCopy } from "../lib/landing-focus-copy";
import { locales } from "../lib/languages";

const copy = (value: { en: string }) => value.en;

test("focused attention never substitutes another nature for a missing lane", () => {
  const july = exampleInsights("2026-07-01", copy);
  assert.equal(selectedExampleInsight(july, "matters", "renovation"), null);
  assert.equal(selectedExampleInsight(july, "unknown", null)?.nature, "UNKNOWN");
});

test("returning to an earlier moment discards an unavailable selection", () => {
  const october = exampleInsights("2026-10-03", copy);
  assert.equal(selectedExampleInsight(october, "understood", "representation")?.id, "representation");
  const july = exampleInsights("2026-07-01", copy);
  const fallback = selectedExampleInsight(july, "understood", "representation");
  assert.ok(fallback && fallback.id !== "representation");
  assert.equal(fallback.nature, "OBSERVED");
  assert.equal(selectedExampleInsight(october, "matters", "capability")?.nature, "POTENTIAL");
});

test("focus instructions and accessible control names exist in every supported locale", () => {
  for (const { id } of locales) {
    assert.ok(Object.values(focusCopy[id]).every(value => value.length > 0));
  }
});
