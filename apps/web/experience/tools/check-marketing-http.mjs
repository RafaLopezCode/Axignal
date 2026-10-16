import test from "node:test";
import assert from "node:assert/strict";

const origin = process.env.AXIGNAL_MARKETING_TEST_ORIGIN;
if (!origin || !/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(origin))
  throw new Error(
    "Set AXIGNAL_MARKETING_TEST_ORIGIN to the task-owned local production server",
  );
const locales = ["es", "en", "fr", "de", "it", "pt"];
const sectors = [
  "industry",
  "construction",
  "energy",
  "logistics",
  "professional-services",
  "agencies",
];
const pages = [
  "",
  "/data",
  "/industries",
  "/pricing",
  ...sectors.map((i) => `/industries/${i}`),
];

test("the production build serves every localized public journey with its own canonical and language", async () => {
  for (const locale of locales)
    for (const page of pages) {
      const route = `/${locale}${page}`;
      const response = await fetch(origin + route);
      assert.equal(response.status, 200, route);
      const html = await response.text();
      assert.match(html, new RegExp(`<html[^>]*lang="${locale}"`), route);
      assert.ok(
        html.includes(`href="https://axignal.com${route}"`),
        `canonical ${route}`,
      );
      assert.equal((html.match(/<h1\b/g) || []).length, 1, route);
      assert.doesNotMatch(
        html,
        /href="\/(?:admin|control-plane|panorama\/live)(?:["/#?])/,
      );
      if (page === "/data")
        for (const family of [
          "presence",
          "reputation",
          "value",
          "markets",
          "relationships",
          "demand",
          "activity",
          "economics",
          "organization",
          "context",
        ])
          assert.ok(html.includes(`id="${family}"`), `${route}#${family}`);
    }
});
test("aliases redirect, while unsupported languages and sectors fail closed", async () => {
  for (const route of [
    "/data",
    "/industries",
    ...sectors.map((i) => `/industries/${i}`),
  ]) {
    const r = await fetch(origin + route, { redirect: "manual" });
    assert.equal(r.status, 308, route);
    assert.equal(
      new URL(r.headers.get("location"), origin).pathname,
      `/en${route}`,
    );
  }
  for (const route of [
    "/es/industries/unknown",
    "/en/industries/admin",
    "/industries/unknown",
    "/zz/data",
    "/es/data/unknown",
  ])
    assert.equal((await fetch(origin + route)).status, 404, route);
});
test("all marketing rasters and the canonical brand load as real images", async () => {
  for (const name of ["hero-art", "industries", "focus", "memory", "explain"]) {
    const r = await fetch(`${origin}/marketing/${name}.webp`);
    assert.equal(r.status, 200);
    assert.match(r.headers.get("content-type"), /image\/webp/);
    assert.ok((await r.arrayBuffer()).byteLength > 1000);
  }
  assert.equal((await fetch(`${origin}/brand/logo-light.svg`)).status, 200);
});

test("Knowledge hubs and articles retain reading routes inside the shared public frame", async () => {
  for (const locale of locales) {
    const hub = await fetch(origin + "/" + locale + "/knowledge");
    assert.equal(hub.status, 200);
    const html = await hub.text();
    assert.match(html, /class="[^"]*marketing-site[^"]*marketing-reading/);
    assert.match(html, /class="marketing-footer"/);
    assert.ok(html.includes('href="/' + locale + '/data"'));
    assert.ok(html.includes('href="/' + locale + '/industries"'));
    assert.ok(html.includes('href="/' + locale + '/pricing"'));
    const articleTag = [...html.matchAll(/<a\b[^>]*>/g)]
      .map((match) => match[0])
      .find((tag) => /class="acquisition-card"/.test(tag));
    const article = articleTag?.match(/href="([^"]+)"/)?.[1];
    assert.ok(article, "published article link in " + locale);
    const articleResponse = await fetch(origin + article);
    assert.equal(articleResponse.status, 200);
    const articleHtml = await articleResponse.text();
    assert.match(articleHtml, /class="marketing-footer"/);
    assert.match(articleHtml, /marketing-reading/);
    assert.ok(articleHtml.includes('href="/' + locale + '/knowledge"'));
    assert.equal((articleHtml.match(/<h1\b/g) || []).length, 1);
  }
});

test("the home publishes the governed newsletter invitation without fabricating availability or subscriptions", async () => {
  for (const locale of locales) {
    const html = await (await fetch(origin + "/" + locale)).text();
    assert.ok(html.includes('id="weekly-brief"'));
    assert.match(html, /marketing-newsletter-channel/);
    assert.match(html, /aria-live="polite"/);
    assert.doesNotMatch(html, /name="newsletterConsent"[^>]*checked/);
  }
});

test("public header and footer render canonical vector paths without resized logo rasters", async () => {
  for (const route of ["/es", "/en/data", "/es/knowledge"]) {
    const html = await (await fetch(origin + route)).text();
    assert.equal(
      (html.match(/class="public-brand-vector"/g) || []).length,
      2,
      route,
    );
    assert.equal(
      (html.match(/data-brand-source="Logo_Claro.svg"/g) || []).length,
      2,
      route,
    );
    assert.doesNotMatch(html, /<img[^>]*src="[^"]*logo[^"]*\.(?:png|jpe?g)/i);
  }
});


test("the advisory launch price is295EUR in every localized home and pricing page", async () => {
  for(const locale of locales) for(const suffix of ["", "/pricing"]) {
    const route="/"+locale+suffix;
    const html=await (await fetch(origin+route)).text();
    const aside=html.match(/<aside class="marketing-advisory"[\s\S]*?<\/aside>/)?.[0];
    assert.ok(aside,route);
    const text=aside.replace(/<[^>]*>/g,"").replace(/\s/g,"");
    const expected=new Intl.NumberFormat(locale,{style:"currency",currency:"EUR"}).format(295).replace(/\s/g,"");
    assert.ok(text.includes(expected),route+" separate295EURhuman service");
    assert.ok(aside.includes('href="/contact"'),route+" actual scope contact");
    assert.doesNotMatch(aside,/(?:995[,.]00|["'](?:USD|GBP)["'])/);
  }
});

test("critical HTML ships responsive eager artwork and only the two critical font preloads", async () => {
  const html=await(await fetch(origin+"/es")).text();
  const hero=html.match(/<img[^>]*class="marketing-hero-art"[^>]*>/)?.[0];
  assert.ok(hero);
  assert.match(hero,/srcSet="[^"]+640w[^"]+1931w"/i);
  assert.match(hero,/sizes="[^"]+620px/);
  assert.match(hero,/loading="eager"/);
  assert.match(hero,/fetchPriority="high"/i);
  assert.ok(html.includes('href="/fonts/font-01.woff2"'));
  assert.ok(html.includes('href="/fonts/manrope-full.15e95cd6.woff2"'));
});
