import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { locales } from "../lib/languages";
import { FAMILY_ORDER } from "../lib/observation-families";
import { familyDetails } from "../lib/marketing-families";
import {
  familyNames,
  familyQuestions,
  marketingCopy,
  marketingPath,
} from "../lib/marketing-content";
import { industries, industryBySlug } from "../lib/marketing-industries";
import {
  publicCopy,
  methodSteps,
  audiences,
  trustItems,
  marketingFaq,
} from "../lib/marketing-ui";
import {
  marketingLanguages,
  marketingMetadata,
  marketingPaths,
} from "../lib/marketing-seo";
import sitemap from "../app/sitemap";
import { newsletterCopy } from "../lib/marketing-newsletter";
import {
  localizeStaticPublicHtml,
  localizedPublicPagePaths,
} from "../tools/localize-static-html-lang.mjs";

test("the public catalog explains every canonical family in all supported languages", () => {
  assert.deepEqual(Object.keys(familyDetails).sort(), [...FAMILY_ORDER].sort());
  for (const f of FAMILY_ORDER)
    for (const { id } of locales) {
      assert.ok(familyNames[f][id].trim());
      assert.ok(familyQuestions[f][id].trim());
      for (const field of Object.values(familyDetails[f]))
        assert.ok(
          field[id].trim().length > 20,
          `${f}/${id} missing evidence or limits`,
        );
    }
});

test("six industry paths have distinct questions and only canonical related families", () => {
  assert.deepEqual(
    industries.map((i) => i.slug),
    [
      "industry",
      "construction",
      "energy",
      "logistics",
      "professional-services",
      "agencies",
    ],
  );
  assert.equal(
    new Set(industries.flatMap((i) => i.questions.map((q) => q.en))).size,
    18,
  );
  for (const industry of industries) {
    assert.equal(industry.questions.length, 3);
    assert.equal(new Set(industry.families).size, industry.families.length);
    for (const f of industry.families) assert.ok(FAMILY_ORDER.includes(f));
    for (const { id } of locales) {
      for (const text of [
        industry.title,
        industry.intro,
        industry.limit,
        ...industry.questions,
      ])
        assert.ok(text[id].trim());
    }
  }
  for (const invalid of [
    "unknown",
    "admin",
    "../admin",
    "industry/extra",
    "INDUSTRY",
    "",
  ])
    assert.equal(industryBySlug(invalid), undefined);
});

test("editorial examples retain the specific epistemic boundaries they explain", () => {
  assert.match(
    familyDetails.presence.limit.en,
    /mention.*citation.*endorsement/i,
  );
  assert.match(
    familyDetails.relationships.limit.en,
    /customer|contract|relationship/i,
  );
  assert.match(
    industryBySlug("construction")!.limit.en,
    /does not establish a subcontract/,
  );
  assert.match(
    industryBySlug("energy")!.limit.en,
    /funding, permits, execution/,
  );
  assert.match(
    industryBySlug("agencies")!.limit.en,
    /does not execute SEO or promise rankings/,
  );
  assert.match(
    industryBySlug("professional-services")!.limit.en,
    /Missing public accounts do not imply/,
  );
});

test("every new public canonical has reciprocal language versions published in sitemap", () => {
  assert.equal(marketingPaths.length, 9);
  const entries = sitemap();
  const map = new Map(entries.map((entry) => [entry.url, entry]));
  for (const route of marketingPaths) {
    const languages = marketingLanguages(route);
    for (const { id } of locales) {
      const url = `https://axignal.com${marketingPath(route, id)}`;
      const entry = map.get(url);
      assert.ok(entry, `unpublished ${url}`);
      assert.deepEqual(entry.alternates?.languages, languages);
      assert.equal(languages[id], url);
      assert.equal(languages["x-default"], `https://axignal.com/en${route}`);
      assert.equal(marketingMetadata(route, id).alternates?.canonical, url);
      assert.ok(marketingMetadata(route, id).description);
    }
  }
  assert.throws(() => marketingMetadata("/admin", "es"), /Unpublished/);
});

test("new shared copy is authored for every locale without a two-language fallback", () => {
  const texts = [
    ...Object.values(publicCopy),
    ...Object.values(newsletterCopy),
    ...Object.values(marketingCopy),
    ...methodSteps.flatMap((i) => [i.title, i.body]),
    ...audiences.flatMap((i) => [i.title, i.body]),
    ...trustItems.flatMap((i) => [i.title, i.body]),
    ...marketingFaq.flatMap((i) => [i.question, i.answer]),
  ];
  for (const text of texts)
    for (const { id } of locales)
      assert.ok(text[id]?.trim(), `${text.en}/${id}`);
});

test("static public HTML language processing is complete and leaves private output untouched", () => {
  assert.deepEqual(
    [...localizedPublicPagePaths].sort(),
    ["", ...marketingPaths.map((p) => p.slice(1))].sort(),
  );
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "axignal-public-lang-"));
  try {
    for (const locale of ["es", "fr"])
      for (const page of localizedPublicPagePaths) {
        const file = path.join(
          root,
          page ? `${locale}/${page}.html` : `${locale}.html`,
        );
        fs.mkdirSync(path.dirname(file), { recursive: true });
        fs.writeFileSync(
          file,
          '<!doctype html><html class="root" lang="en"><body>Public</body></html>',
        );
      }
    fs.writeFileSync(
      path.join(root, "admin.html"),
      '<html lang="en">Private</html>',
    );
    const files = localizeStaticPublicHtml({
      appDir: root,
      locales: ["es", "fr"],
    });
    assert.equal(files.length, 20);
    for (const file of files)
      assert.match(
        fs.readFileSync(file, "utf8"),
        file.includes(`${path.sep}es`) ? /lang="es"/ : /lang="fr"/,
      );
    assert.equal(
      fs.readFileSync(path.join(root, "admin.html"), "utf8"),
      '<html lang="en">Private</html>',
    );
    fs.unlinkSync(path.join(root, "fr", "data.html"));
    assert.throws(
      () => localizeStaticPublicHtml({ appDir: root, locales: ["fr"] }),
      /Missing prerendered public page/,
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
