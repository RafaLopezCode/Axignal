import { test } from "node:test";
import assert from "node:assert/strict";
import { gzipSync } from "node:zlib";
import { getLandingLabContent } from "../lib/landing-lab-content";
import { locales } from "../lib/languages";

for (const { id: locale } of locales) {
  test(`server-delivered landing wording preserves every ${locale} text and non-text value`, () => {
    const { runtime: _canonicalRuntime, ...canonical } =
      getLandingLabContent(null);
    const { runtime: _deliveredRuntime, ...delivered } =
      getLandingLabContent(locale);
    function compare(source: unknown, result: unknown): void {
      if (Array.isArray(source)) {
        assert.ok(Array.isArray(result));
        assert.equal(result.length, source.length);
        source.forEach((item, i) => compare(item, result[i]));
      } else if (source && typeof source === "object") {
        const a = source as Record<string, unknown>;
        const b = result as Record<string, unknown>;
        assert.deepEqual(Object.keys(b), Object.keys(a));
        if (locales.every(({ id }) => typeof a[id] === "string")) {
          for (const { id } of locales) assert.equal(b[id], a[locale]);
        } else for (const key of Object.keys(a)) compare(a[key], b[key]);
      } else assert.equal(result, source);
    }
    compare(canonical, delivered);
    assert.ok(
      gzipSync(JSON.stringify(delivered)).length <
        gzipSync(JSON.stringify(canonical)).length * 0.5,
      "A localized route must not transfer all six commercial catalogs",
    );
  });
}
test("landing delivery does not mutate canonical wording or transfer industry article bodies", () => {
  const before = JSON.stringify(getLandingLabContent(null));
  for (const { id } of locales) getLandingLabContent(id);
  assert.equal(JSON.stringify(getLandingLabContent(null)), before);
  for (const item of getLandingLabContent(null).industries)
    assert.deepEqual(Object.keys(item).sort(), ["slug", "title"]);
});

import { labInsight } from "../lib/landing-lab-model";
import { exampleInsights, EXAMPLE_MOMENTS } from "../lib/landing-observatory";
import { translate } from "../lib/copy-catalog";
for (const { id: locale } of locales) {
  test(`all 15 server-delivered ${locale} states and the hero exactly match the existing models`, () => {
    const data = getLandingLabContent(locale);
    const unprefixed = getLandingLabContent(null);
    const copy = (value: { es: string; en: string }) =>
      translate(value.es, value.en, locale);
    for (const moment of EXAMPLE_MOMENTS)
      for (const question of data.labQuestions) {
        const expected = labInsight(moment, question.id, copy);
        assert.deepEqual(
          data.runtime.byLocale[locale].views[moment][question.id],
          expected,
        );
        assert.deepEqual(
          unprefixed.runtime.byLocale[locale].views[moment][question.id],
          expected,
        );
      }
    assert.deepEqual(
      data.runtime.byLocale[locale].hero,
      exampleInsights("2026-10-03", copy).find(
        (item) => item.id === "renovation",
      ),
    );
    for (const { id } of locales)
      assert.equal(
        data.runtime.byLocale[id],
        data.runtime.byLocale[locale],
        "Localized routes serialize one reading, with reference aliases",
      );
  });
}
