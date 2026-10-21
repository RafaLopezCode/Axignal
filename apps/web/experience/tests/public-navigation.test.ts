import test from "node:test";
import assert from "node:assert/strict";
import { locales } from "../lib/languages";
import { landingLanguagePath, marketingPath } from "../lib/marketing-locale";
import sitemap from "../app/sitemap";

test("changing a public home language preserves the fragment and never enters the isolated preview", () => {
  const published = new Set(sitemap().map(entry => new URL(entry.url).pathname));
  for (const { id } of locales) {
    for (const current of ["/", ...locales.map(locale => `/${locale.id}`)]) {
      const target = landingLanguagePath(current, id, "#discover");
      assert.equal(target, `/${id}#discover`);
      assert.ok(published.has(target.split("#")[0]));
      assert.ok(!target.includes("landing-lab"));
    }
    assert.ok(published.has(marketingPath("/knowledge", id)), "Every editorial menu destination must be published in its own language");
  }
});

test("language changes inside the isolated preview keep its route and narrative state", () => {
  for (const { id } of locales) {
    for (const current of ["/landing-lab", "/es/landing-lab", "/it/landing-lab"])
      assert.equal(landingLanguagePath(current, id, "#pricing"), `/${id}/landing-lab#pricing`);
  }
});
