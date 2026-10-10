import test from "node:test";
import assert from "node:assert/strict";
import snapshot from "../lib/demo/synthetic-observatory.json";

test("the demo snapshot is labelled synthetic and points only at reserved example hosts", () => {
  assert.match(String(snapshot.provenance), /^SYNTHETIC:/);
  const text = JSON.stringify(snapshot);
  const hosts = new Set([...text.matchAll(/https?:\/\/([^/"\\ ]+)/g)].map(m => m[1].replace(/^www\./, "")));
  assert.ok(hosts.size > 0);
  for (const host of hosts) assert.match(host, /\.(example|test|invalid)$|^example\.(com|org|net)$|\.example\.com$|^demo-[a-z-]+\.com$/, host);
  // Names and hosts that could match a real company, public body or procurement platform.
  assert.doesNotMatch(text, /Solartec|Solaria Norte|Ledgerly|Boulangerie de la Lune|Little Rock Language|Getafe|ted\.europa|\bTED\b/);
});

test("every snapshot read parses with the same contracts as the live subscriber read", async () => {
  const { syntheticOutput, syntheticPortfolio } = await import("../lib/demo/synthetic-source");
  const { pendingOutputSchema, subscriberOutputSchema } = await import("../lib/subscriber-contracts");
  assert.ok(syntheticPortfolio("es").organizations.length > 0);
  for (const focusId of Object.keys(snapshot.outputs)) {
    const payload = syntheticOutput(focusId, "es") as { kind?: string };
    if (payload.kind === "PENDING_ATTENTION") pendingOutputSchema.parse(payload);
    else subscriberOutputSchema.parse(payload);
  }
});

test("demo domains and names follow the reader's locale, with valid ASCII domains", async () => {
  const { syntheticPortfolio } = await import("../lib/demo/synthetic-source");
  for (const locale of ["es", "en", "de", "pt", "fr", "it"] as const) {
    for (const org of syntheticPortfolio(locale).organizations) {
      if (org.label.startsWith("Demo ")) assert.match(org.label, /^Demo [A-Za-zÀ-ÿ-]+$/, `${locale}: ${org.label}`);
    }
  }
  assert.equal(syntheticPortfolio("fr").organizations[6]?.label, "Demo Distributeur");
  assert.equal(syntheticPortfolio("es").organizations[6]?.label, "Demo Distribuidor");
});

test("the SEO and GEO demonstration organization is named Demo Seo-Geo in every language", async () => {
  const { syntheticPortfolio } = await import("../lib/demo/synthetic-source");
  for (const locale of ["es", "en", "de", "pt", "fr", "it"] as const) {
    const labels = syntheticPortfolio(locale).organizations.map(item => item.label);
    assert.ok(labels.includes("Demo Seo-Geo"), `${locale}: ${labels.join(", ")}`);
    assert.ok(!labels.some(label => /Seo-geo/.test(label)), locale);
  }
});
