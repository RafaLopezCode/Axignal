import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { GET as assistantDirectory } from "../app/llms.txt/route";
import { locales } from "../lib/languages";
import { HOME_METADATA } from "../lib/public-home-metadata";
import { marketingMetadata, marketingPaths } from "../lib/marketing-seo";
import { marketingPath } from "../lib/marketing-content";
import { EUR_REFERENCE } from "../lib/commercial-prices";
import { homeLanguages, localizedHomeMetadata, PUBLIC_SOCIAL_IMAGE, publicSocialMetadata, siteStructuredData } from "../lib/site-seo";
import labFonts from "../lib/landing-lab-fonts.json";
import config from "../next.config";

test("every home and catalog language retains its own complete social preview", async () => {
  for (const { id } of locales) {
    const home = localizedHomeMetadata(id);
    assert.deepEqual(home.title, { absolute: HOME_METADATA[id].title });
    assert.equal(home.description, HOME_METADATA[id].description);
    assert.deepEqual(home.alternates?.languages, homeLanguages());
    const cases = [
      { metadata: home, path: `/${id}` },
      ...marketingPaths.map(path => ({ metadata: marketingMetadata(path, id), path: marketingPath(path, id) })),
    ];
    for (const { metadata, path } of cases) {
      assert.equal(metadata.alternates?.canonical, `https://axignal.com${path}`);
      assert.equal(metadata.openGraph?.url, `https://axignal.com${path}`);
      assert.equal(metadata.openGraph?.siteName, "AXIGNAL");
      assert.match(String(metadata.openGraph?.locale), new RegExp(`^${id}_[A-Z]{2}$`));
      const images = metadata.openGraph?.images as Array<{ url: string; width: number; height: number; alt: string }>;
      assert.equal(images.length, 1, path);
      assert.equal(images[0].url, PUBLIC_SOCIAL_IMAGE);
      assert.equal(images[0].width, 1200);
      assert.equal(images[0].height, 630);
      assert.ok(images[0].alt.includes("AXIGNAL"));
      assert.deepEqual(metadata.twitter?.images, images);
      assert.equal((metadata.twitter as { card: string }).card, "summary_large_image");
    }
  }
  const root = publicSocialMetadata({ ...HOME_METADATA.en, path: "/", locale: "en" });
  assert.equal(root.openGraph?.url, "https://axignal.com/");
});

test("entity graph connects the real page, service and approved organization identity", () => {
  for (const locale of [null, ...locales.map(({ id }) => id)]) {
    const graph = siteStructuredData(locale)["@graph"] as Array<Record<string, unknown>>;
    const find = (type: string) => graph.find(node => node["@type"] === type)!;
    const org = find("Organization"), site = find("WebSite"), page = find("WebPage"), service = find("Service");
    assert.deepEqual(page.mainEntity, { "@id": service["@id"] });
    assert.deepEqual(site.about, { "@id": service["@id"] });
    assert.deepEqual(service.provider, { "@id": org["@id"] });
    assert.equal((org.logo as { url: string }).url, "https://axignal.com/brand/organization-logo-512.png");
    assert.equal(service.areaServed, undefined, "global ontology is not commercial reach evidence");
    const offers = service.offers as Array<{ price: string; description: string; priceSpecification: { billingDuration: string; valueAddedTaxIncluded: boolean } }>;
    assert.deepEqual(offers.map(offer => offer.price), [EUR_REFERENCE.baseMinor, EUR_REFERENCE.additionalMinor].map(minor => (minor / 100).toFixed(2)));
    assert.match(offers[0].description, /reference price.*invitation.*without payment/i);
    assert.ok(offers.every(offer => offer.priceSpecification.billingDuration === "P1M" && !offer.priceSpecification.valueAddedTaxIncluded));
  }
});

test("public home routes preload only the same two essential fonts as the accepted preview", async () => {
  const headers = await config.headers!();
  const sources = ["/", "/:locale(es|en|de|pt|fr|it)", "/landing-lab", "/:locale(es|en|de|pt|fr|it)/landing-lab"];
  for (const source of sources) {
    const link = headers.find(rule => rule.source === source)?.headers.find(header => header.key === "Link")?.value;
    assert.ok(link, source);
    for (const asset of labFonts.fonts.slice(0, 2)) assert.ok(link.includes(`<${asset.url}>; rel=preload; as=font; type="font/woff2"; crossorigin=anonymous; fetchpriority=high`));
    assert.equal(link.split(", ").length, 2);
  }
});

test("conventional favicon preserves one approved asset in Next and the production fallback", async () => {
  const redirects = await config.redirects!();
  assert.ok(redirects.some(rule => rule.source === "/favicon.ico" && rule.destination === "/brand/favicon.ico" && rule.permanent));
  const nginx = readFileSync(resolve("../../../deploy/production/docker/landing-nginx.conf"), "utf8");
  assert.match(nginx, /location = \/favicon\.ico\s*\{ return 308 \/brand\/favicon\.ico; \}/);
});

test("assistant directory exposes existing language URLs, current access terms and evidence limits", async () => {
  const response = assistantDirectory();
  assert.equal(response.headers.get("Content-Type"), "text/plain; charset=utf-8");
  const body = await response.text();
  for (const { id } of locales) assert.ok(body.includes(`https://axignal.com/${id})`));
  assert.match(body, /without payment during the programme/);
  assert.match(body, /opportunity is potential/);
  assert.match(body, /fictional organizations and illustrative sources/);
  assert.match(body, /mention is not a citation; a citation is not an endorsement/);
  assert.ok(body.includes(`${(EUR_REFERENCE.baseMinor / 100).toFixed(2)} EUR`));
});
