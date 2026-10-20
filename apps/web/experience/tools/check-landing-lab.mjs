import assert from "node:assert/strict";
import fs from "node:fs";
const base = new URL(process.argv[2] ?? "http://127.0.0.1:3822");
assert.ok(
  ["127.0.0.1", "localhost"].includes(base.hostname) &&
    base.protocol === "http:",
  "Local preview only",
);
const rows = [];
for (const locale of ["es", "en", "de", "fr", "it", "pt"]) {
  const route = "/" + locale + "/landing-lab";
  const response = await fetch(new URL(route, base));
  assert.equal(response.status, 200, route);
  const html = await response.text();
  assert.equal((html.match(/<h1\b/g) ?? []).length, 1, route + " one H1");
  assert.match(html, /<meta name="robots" content="noindex, follow"/);
  assert.ok(
    html.includes('href="https://axignal.com' + route + '"'),
    route + " canonical",
  );
  assert.match(
    html,
    new RegExp('<html[^>]+lang="' + locale + '"'),
    route + " SSR lang",
  );
  const structured = JSON.parse(
    html.match(
      /<script type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/,
    )?.[1] ?? "null",
  );
  assert.ok(structured, route + " JSON-LD");
  const graph = structured["@graph"];
  assert.equal(
    graph.find((node) => node["@type"] === "WebPage")?.url,
    "https://axignal.com" + route,
  );
  for (const type of ["Organization", "WebSite", "WebPage", "Service"])
    assert.ok(
      graph.some((node) => node["@type"] === type),
      type,
    );
  assert.match(
    html,
    /property="og:image" content="https:\/\/axignal.com\/brand\/og-image-1200x630.png"/,
  );
  assert.match(html, /name="twitter:card" content="summary_large_image"/);
  assert.match(
    html,
    /name="twitter:image" content="https:\/\/axignal.com\/brand\/og-image-1200x630.png"/,
  );
  assert.match(html, /<details/);
  assert.match(html, /href="\/signup"/);
  assert.match(html, /href="\/demo"/);
  assert.match(html, /id="lab-count"/);
  assert.doesNotMatch(html, /<iframe\b/);
  for (const id of ["discover", "audience", "how", "trust", "pricing"])
    assert.ok(html.includes('id="' + id + '"'), id);
  rows.push({
    route,
    status: response.status,
    bytes: Buffer.byteLength(html),
    h1: html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/)?.[1].replace(/<[^>]+>/g, ""),
  });
}
const sitemap = await (await fetch(new URL("/sitemap.xml", base))).text();
assert.ok(
  !sitemap.includes("/landing-lab"),
  "Preview must not enter the sitemap",
);
const lab = await (await fetch(new URL("/es/landing-lab", base))).text();
const destinations = [
  ...new Set(
    [...lab.matchAll(/href="(\/[^"#?]*)"/g)]
      .map((match) => match[1])
      .filter(
        (path) => !path.startsWith("/_next/") && !path.startsWith("/fonts/"),
      ),
  ),
];
for (const path of destinations) {
  const response = await fetch(new URL(path, base), { redirect: "follow" });
  assert.ok(response.ok, path + " returned " + response.status);
}
const report = {
  checkedAt: new Date().toISOString(),
  base: base.origin,
  locales: rows,
  publicDestinations: destinations.length,
  ssr: true,
  noindex: true,
  sitemapExcluded: true,
};
if (process.argv[3])
  fs.writeFileSync(process.argv[3], JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify(report, null, 2));
