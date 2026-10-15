import test from "node:test";
import assert from "node:assert/strict";
import { HOME_METADATA } from "../lib/public-home-metadata";
import { siteStructuredData } from "../lib/site-seo";
import { auditCopy } from "../lib/representation-audit";

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
  // The profile the footer links is declared for machines too (sameAs).
  assert.deepEqual(organization.sameAs, ["https://www.linkedin.com/company/axignal/"]);
});

test("a profile linked for people but not declared is named, not reported as missing", () => {
  const t = (es: string) => es;
  const linked = auditCopy("ENTITY_PROFILES_LINKED", t, { declared: [], linkedOnPage: ["linkedin.com"] });
  assert.match(linked.title, /Enlaza sus perfiles en la web/);
  assert.match(linked.action, /LinkedIn/);
  // Nothing linked anywhere: the original finding stands.
  assert.match(auditCopy("ENTITY_PROFILES_LINKED", t, { declared: [], linkedOnPage: [] }).title, /No enlaza/);
  // Already declared, but only one: it is said so, not "does not link".
  const one = auditCopy("ENTITY_PROFILES_LINKED", t, { declared: ["www.linkedin.com"], linkedOnPage: ["linkedin.com"] });
  assert.match(one.title, /un solo perfil/);
  assert.match(one.why, /LinkedIn/);
});
