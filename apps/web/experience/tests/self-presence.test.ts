import test from "node:test";
import assert from "node:assert/strict";
import { HOME_METADATA } from "../lib/public-home-metadata";
import { siteStructuredData } from "../lib/site-seo";

// AXIGNAL applies to itself the representation audit it runs on subscribers' websites
// (application/first_observation/representation_audit.py): titles 15–65, descriptions 50–170.
test("AXIGNAL's own home titles and descriptions stay inside the audit's ranges", () => {
  for (const [locale, meta] of Object.entries(HOME_METADATA)) {
    assert.ok(meta.title.length >= 15 && meta.title.length <= 65, `${locale} title ${meta.title.length}`);
    assert.ok(meta.description.length >= 50 && meta.description.length <= 170, `${locale} description ${meta.description.length}`);
  }
});

test("its Organization declares a real contact channel and nothing invented", () => {
  const graph = siteStructuredData(null)["@graph"] as Array<Record<string, unknown>>;
  const organization = graph.find(node => node["@type"] === "Organization")!;
  const contact = organization.contactPoint as Record<string, unknown>;
  assert.equal(contact["@type"], "ContactPoint");
  assert.match(String(contact.url), /\/contact$/);
  assert.equal(organization.address, undefined); // no address until the legal operator is published
});
