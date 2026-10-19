import { test } from "node:test";
import assert from "node:assert/strict";
import { gzipSync } from "node:zlib";
import { getLandingLabContent } from "../lib/landing-lab-content";
import { locales } from "../lib/languages";

for (const { id: locale } of locales) {
  test(`server-delivered landing wording preserves every ${locale} text and non-text value`, () => {
    const canonical = getLandingLabContent(null);
    const delivered = getLandingLabContent(locale);
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
