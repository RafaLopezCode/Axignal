import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import sitemap from "../app/sitemap";
import robots from "../app/robots";
import { generateMetadata as articleMetadata } from "../app/[locale]/knowledge/[slug]/page";
import { generateMetadata as hubMetadata } from "../app/[locale]/knowledge/page";
import { acquisitionPages, localizedPagePath, pageByLocalizedSlug, validateAcquisitionPages } from "../lib/acquisition";
import { articleStructuredData, hreflangMap, hubStructuredData } from "../lib/acquisition-seo";
import { locales } from "../lib/languages";

test("acquisition corpus is substantial and every published page passes editorial gates", () => {
  const counts = Object.fromEntries(
    (["commercial", "knowledge", "jtbd", "comparison"] as const).map((type) => [
      type,
      acquisitionPages.filter((page) => page.type === type).length,
    ]),
  );
  assert.ok(counts.commercial >= 25 && counts.commercial <= 40, `commercial target 25–40, got ${counts.commercial}`);
  assert.ok(counts.knowledge >= 40 && counts.knowledge <= 60, `knowledge target 40–60, got ${counts.knowledge}`);
  assert.ok(counts.jtbd >= 10 && counts.jtbd <= 20, `audience/JTBD target 10–20, got ${counts.jtbd}`);
  assert.ok(counts.comparison >= 10 && counts.comparison <= 15, `comparison target 10–15, got ${counts.comparison}`);
  assert.deepEqual(validateAcquisitionPages(), []);
});

test("each page has six localized slugs and route lookup is one-to-one", () => {
  const routes = new Set<string>();
  for (const page of acquisitionPages) {
    for (const { id: locale } of locales) {
      const content = page.locales[locale];
      assert.ok(content, `${page.id} is missing ${locale}`);
      const route = localizedPagePath(page, locale);
      assert.equal(routes.has(route), false, `duplicate published route ${route}`);
      routes.add(route);
      assert.equal(pageByLocalizedSlug(locale, content.slug)?.page.id, page.id);
    }
  }
  assert.equal(routes.size, acquisitionPages.length * locales.length);
});

test("all canonical, hreflang and x-default URLs are reciprocal and in the sitemap", () => {
  const entries = sitemap();
  const byUrl = new Map(entries.map((entry) => [entry.url, entry]));
  assert.equal(byUrl.size, entries.length);
  // Articles and hubs per locale, plus the home page (spec 060: the funnel's front door).
  assert.equal(entries.length, (acquisitionPages.length + 1) * locales.length + 1);
  assert.ok(byUrl.has("https://axignal.com/"));
  for (const page of acquisitionPages) {
    for (const locale of locales) {
      const content = page.locales[locale.id]!;
      const path = localizedPagePath(page, locale.id);
      const entry = byUrl.get(`https://axignal.com${path}`);
      assert.ok(entry, `${path} missing from sitemap`);
      const languages = entry.alternates?.languages as Record<string, string> | undefined;
      assert.ok(languages);
      assert.equal(languages[locale.id], entry.url);
      assert.equal(languages["x-default"], `https://axignal.com/es/knowledge/${page.locales.es!.slug}`);
      for (const other of locales) {
        const sibling = page.locales[other.id]!;
        const siblingUrl = `https://axignal.com/${other.id}/knowledge/${sibling.slug}`;
        assert.equal(languages[other.id], siblingUrl, `${path} missing hreflang ${other.id}`);
      }
      assert.equal(pageByLocalizedSlug(locale.id, content.slug)?.content, content);
    }
  }
  const hub = byUrl.get("https://axignal.com/es/knowledge");
  assert.ok(hub);
  assert.equal((hub.alternates?.languages as Record<string, string>)["x-default"], hub.url);
});

test("article and breadcrumb structured data matches the visible localized document", () => {
  const page = acquisitionPages[0]!;
  for (const locale of locales) {
    const content = page.locales[locale.id]!;
    const [article, breadcrumb] = articleStructuredData(page, content, locale.id);
    assert.equal(article["@type"], "Article");
    assert.equal(article.headline, content.title);
    assert.equal(article.description, content.description);
    assert.equal(article.inLanguage, locale.id);
    assert.equal(article.datePublished, "2026-10-07");
    assert.equal(article.dateModified, "2026-10-07");
    assert.equal(article.image.url, "https://axignal.com/brand/og-image-1200x630.png");
    assert.equal(article.author.logo.url, "https://axignal.com/brand/organization-logo-512.png");
    assert.equal(article.publisher.logo.url, "https://axignal.com/brand/organization-logo-512.png");
    assert.equal(breadcrumb["@type"], "BreadcrumbList");
    const items = breadcrumb.itemListElement;
    assert.ok(items);
    assert.equal(items.length, 3);
    assert.ok(items.every((item) => item.item.startsWith("https://axignal.com/")));
  }
});

test("hub structured data identifies the localized Knowledge collection", () => {
  for (const { id: locale } of locales) {
    const schema = hubStructuredData(locale);
    assert.equal(schema["@type"], "CollectionPage");
    assert.equal(schema.inLanguage, locale);
    assert.equal(schema.url, `https://axignal.com/${locale}/knowledge`);
    assert.equal(schema.isPartOf.url, "https://axignal.com/");
  }
});

test("route metadata localizes canonical, hreflang, OpenGraph and Twitter for every page", async () => {
  for (const page of acquisitionPages) {
    for (const { id: locale } of locales) {
      const content = page.locales[locale]!;
      const metadata = await articleMetadata({ params: Promise.resolve({ locale, slug: content.slug }) });
      const canonical = `https://axignal.com/${locale}/knowledge/${content.slug}`;
      assert.deepEqual(metadata.title, { absolute: content.title });
      assert.equal(metadata.description, content.description);
      assert.equal(metadata.alternates?.canonical, canonical);
      assert.equal(metadata.openGraph?.url, canonical);
      assert.equal(metadata.openGraph?.title, content.title);
      assert.deepEqual(metadata.openGraph?.images, ["/brand/og-image-1200x630.png"]);
      assert.equal(metadata.twitter?.title, content.title);
      assert.deepEqual(metadata.twitter?.images, ["/brand/og-image-1200x630.png"]);
      assert.deepEqual(metadata.alternates?.languages, hreflangMap(Object.fromEntries(locales.map(({ id }) => [id, localizedPagePath(page, id)]))));
      assert.deepEqual(metadata.robots, { index: true, follow: true });
    }
  }
  for (const { id: locale } of locales) {
    const metadata = await hubMetadata({ params: Promise.resolve({ locale }) });
    assert.equal(metadata.alternates?.canonical, `https://axignal.com/${locale}/knowledge`);
    assert.ok(typeof metadata.title === "object" && metadata.title !== null && "absolute" in metadata.title);
    assert.ok(metadata.alternates?.languages);
    assert.deepEqual(metadata.openGraph?.images, ["/brand/og-image-1200x630.png"]);
    assert.deepEqual(metadata.twitter?.images, ["/brand/og-image-1200x630.png"]);
  }
  assert.deepEqual(await articleMetadata({ params: Promise.resolve({ locale: "es", slug: "missing" }) }), { robots: { index: false, follow: false } });
});

test("hreflang uses the Spanish x-default and robots expose the XML sitemap", () => {
  const languages = hreflangMap({ es: "/es/knowledge", fr: "/fr/knowledge" });
  assert.equal(languages.es, "https://axignal.com/es/knowledge");
  assert.equal(languages.fr, "https://axignal.com/fr/knowledge");
  assert.equal(languages["x-default"], languages.es);
  assert.equal(robots().sitemap, "https://axignal.com/sitemap.xml");
});

test("GSC sitemap contains only canonical public indexable pages, not redirects, demo or private sessions", () => {
  const entries = sitemap();
  const forbidden = ["/demo", "/panorama", "/account", "/admin", "/login", "/signup", "/api/"];
  assert.ok(entries.length > 0);
  for (const entry of entries) {
    const { origin, pathname } = new URL(entry.url);
    assert.equal(origin, "https://axignal.com", `noncanonical origin: ${entry.url}`);
    assert.ok(!forbidden.some(path => pathname === path || pathname.startsWith(path + "/")), `nonindexable URL in sitemap: ${entry.url}`);
  }
  const policy = robots().rules;
  const rules = Array.isArray(policy) ? policy : [policy];
  const disallow = rules.flatMap((rule) => {
    const values = rule.disallow;
    return values ? Array.isArray(values) ? values : [values] : [];
  });
  for (const path of ["/account", "/admin", "/api/", "/login", "/signup"]) {
    assert.ok(disallow.includes(path), `${path} must be excluded from crawlers`);
  }
  // Google must be able to crawl the redirect and read the demo noindex directive.
  for (const path of ["/panorama", "/demo"]) {
    assert.ok(!disallow.includes(path), `${path} needs to remain crawlable for redirect/noindex`);
  }
  const demoSource = readFileSync(resolve(import.meta.dirname, "../app/demo/page.tsx"), "utf8");
  assert.match(demoSource, /robots:\s*\{\s*index:\s*false,\s*follow:\s*false/);
});
