import test from "node:test";
import assert from "node:assert/strict";
import { locales } from "../lib/languages";
import { landingLanguagePath, marketingPath } from "../lib/marketing-locale";
import sitemap from "../app/sitemap";
import { publicNavigation, publicNavigationCopy } from "../lib/public-navigation";
import fs from "node:fs";
import postcss from "postcss";
import styles from "../lib/surface-styles.json";

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

test("the global menu reaches published pages and real landing anchors in all six languages", () => {
  const published = new Set(sitemap().map(entry => new URL(entry.url).pathname));
  const landing = fs.readFileSync(new URL("../components/landing-lab.tsx", import.meta.url), "utf8");
  for (const { id } of locales) {
    const nav = publicNavigation(id);
    for (const link of [...nav.chapters, ...nav.pages, ...nav.trust]) {
      const [path, fragment] = link.href.split("#");
      // Contact and legal pages are intentionally public/noindex, absent from sitemap.
      assert.ok(published.has(path) || ["/contact", "/policies", "/gdpr"].includes(path), `Published menu target: ${link.href}`);
      if (["/contact", "/policies", "/gdpr"].includes(path))
        assert.ok(fs.existsSync(new URL(`../app${path}/page.tsx`, import.meta.url)), "Public noindex route actually exists");
      if (fragment) assert.ok(landing.includes(`id="${fragment}"`), `Existing home section: ${fragment}`);
      assert.ok(link.label.trim().length > 0);
      assert.ok(!link.href.includes("landing-lab") && !link.href.includes("admin"));
    }
    for (const copy of Object.values(publicNavigationCopy)) assert.ok(copy[id].trim());
    assert.ok(publicNavigation(id, true).chapters.every(link => link.href.startsWith(`/${id}/landing-lab#`)));
  }
});

test("both public entrypoints use one unskinned header with a native no-JS menu", () => {
  const read = (path: string) => fs.readFileSync(new URL("../components/" + path, import.meta.url), "utf8");
  const header = read("public-header.tsx");
  for (const source of [read("landing-lab.tsx"), read("public-shell.tsx")]) {
    assert.match(source, /import \{ PublicHeader \} from "\.\/public-header"/);
    assert.match(source, /<PublicHeader[\s/>]/);
    assert.doesNotMatch(source, /<header\b|className="(?:lab-header|public-header)/);
    assert.ok(source.indexOf("<PublicHeader") < source.indexOf('<div className='), "Header lives outside page-specific skin");
  }
  assert.match(header, /<details\b/);
  assert.match(header, /<summary\b/);
  assert.doesNotMatch(header, /<Dialog|aria-modal|showModal|import\(.*gsap/);
  for (const asset of [styles.base, styles.lab, styles.legacy]) {
    const css = postcss.parse(fs.readFileSync(new URL("../public" + asset.url, import.meta.url), "utf8"));
    const rules: string[] = [];
    css.walkRules(rule => { rules.push(...postcss.list.comma(rule.selector)); });
    assert.ok(rules.includes(".ax-site-header"), `Shared header survives ${asset.url}`);
    assert.ok(rules.includes(".ax-site-menu"), "Menu is available at desktop and mobile widths");
    assert.ok(rules.includes(".ax-site-panel"), "Disclosure panel styles survive delivery");
  }
});
