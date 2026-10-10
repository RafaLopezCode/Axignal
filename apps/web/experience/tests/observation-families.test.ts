import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import {
  FAMILY_ORDER, NO_FACET, countByFacet, facetOfDiscovery, facetOfOpportunity, facetOfSourceType,
  facetParams, litByChannel, litByFamily, matchesFacet, parseFacet,
} from "../lib/observation-families";
import { insightsFor } from "../lib/observatory";
import { subscriberOutputSchema } from "../lib/subscriber-contracts";
import { syntheticOutput } from "../lib/demo/synthetic-source";

const en = (_es: string, english: string) => english;

test("a discovery is placed by its typed kind and code, never by its wording", () => {
  assert.deepEqual(facetOfDiscovery({ kind: "PUBLIC_PRESENCE", code: "PUBLIC_WEBSITE_OBSERVED" }), { family: "presence", channel: "WEB" });
  assert.deepEqual(facetOfDiscovery({ kind: "SEARCH_VISIBILITY", code: "ANY" }), { family: "presence", channel: "SEO" });
  assert.deepEqual(facetOfDiscovery({ kind: "GENERATIVE_VISIBILITY", code: "ANY" }), { family: "presence", channel: "GEO" });
  assert.deepEqual(facetOfDiscovery({ kind: "ACTIVITY", code: "isic-J" }), { family: "value", channel: null });
  assert.deepEqual(facetOfDiscovery({ kind: "DECLARED_LOCATION", code: "ADDRESS_DECLARED" }), { family: "markets", channel: null });
  assert.deepEqual(facetOfDiscovery({ kind: "DEMAND", code: "POTENTIAL_DEMAND" }), { family: "demand", channel: null });
  // The function receives no text at all, so a headline that says "SEO" cannot move a finding into SEO.
  assert.equal(facetOfDiscovery.length, 1);
});

test("a grounded unknown names its family through its code; an unknown code is left unplaced", () => {
  assert.deepEqual(facetOfDiscovery({ kind: "SIGNIFICANT_UNKNOWN", code: "ROBOTS_DISALLOWED" }), { family: "presence", channel: "WEB" });
  assert.deepEqual(facetOfDiscovery({ kind: "SIGNIFICANT_UNKNOWN", code: "NO_GOVERNED_DEMAND_SOURCE:EU/ES" }), { family: "demand", channel: null });
  assert.deepEqual(facetOfDiscovery({ kind: "SIGNIFICANT_UNKNOWN", code: "IDENTITY_NOT_VERIFIED" }), { family: "organization", channel: null });
  assert.deepEqual(facetOfDiscovery({ kind: "SIGNIFICANT_UNKNOWN", code: "SOMETHING_NEW" }), NO_FACET);
});

test("opportunities and observation sources are placed from their typed fields", () => {
  assert.deepEqual(facetOfOpportunity({ familyId: "demand" }), { family: "demand", channel: null });
  assert.deepEqual(facetOfSourceType("PUBLIC_WEBSITE"), { family: "presence", channel: "WEB" });
  assert.deepEqual(facetOfSourceType("PUBLIC_SEARCH_VISIBILITY"), { family: "presence", channel: "SEO" });
  assert.deepEqual(facetOfSourceType("GENERATIVE_ANSWER_SURFACES"), { family: "presence", channel: "GEO" });
  assert.deepEqual(facetOfSourceType("a source we do not know"), NO_FACET);
});

test("the selection travels in the URL, ignores anything unrecognised and keeps channels inside Presence", () => {
  assert.deepEqual(parseFacet("presence", "seo"), { family: "presence", channel: "SEO" });
  assert.deepEqual(parseFacet("presence", "GEO"), { family: "presence", channel: "GEO" });
  assert.deepEqual(parseFacet("presence", "nonsense"), { family: "presence", channel: null });
  assert.deepEqual(parseFacet("value", "seo"), { family: "value", channel: null });
  assert.deepEqual(parseFacet("not-a-family", "seo"), NO_FACET);
  assert.deepEqual(parseFacet(null, null), NO_FACET);
  for (const facet of [NO_FACET, { family: "presence" as const, channel: "SEO" as const }, { family: "demand" as const, channel: null }]) {
    const { family, channel } = facetParams(facet);
    assert.deepEqual(parseFacet(family, channel), facet);
  }
});

test("a finding matches a selection only inside its family and channel; an unplaced finding matches none", () => {
  const web = { family: "presence" as const, channel: "WEB" as const };
  assert.equal(matchesFacet(web, NO_FACET), true);
  assert.equal(matchesFacet(web, { family: "presence", channel: null }), true);
  assert.equal(matchesFacet(web, { family: "presence", channel: "WEB" }), true);
  assert.equal(matchesFacet(web, { family: "presence", channel: "SEO" }), false);
  assert.equal(matchesFacet(web, { family: "value", channel: null }), false);
  assert.equal(matchesFacet(NO_FACET, { family: "presence", channel: null }), false);
  assert.equal(matchesFacet(NO_FACET, NO_FACET), true);
});

test("counts exist only for placed findings and cover every family", () => {
  const counts = countByFacet([
    { family: "presence", channel: "WEB" }, { family: "presence", channel: "SEO" },
    { family: "demand", channel: null }, NO_FACET,
  ]);
  assert.equal(counts.families.presence, 2);
  assert.equal(counts.families.demand, 1);
  assert.equal(counts.channels.SEO, 1);
  assert.equal(counts.channels.GEO, 0);
  assert.deepEqual(Object.keys(counts.families), [...FAMILY_ORDER]);
  const lit = litByFamily([{ family: "presence", channel: "WEB", changeKey: "a" }, { family: "demand", channel: null, changeKey: "b" }], new Set(["a"]));
  assert.equal(lit.presence, 1);
  assert.equal(lit.demand, 0);
});

test("real readings carry a typed family on every finding the contract can place, and none by guesswork", () => {
  const output = subscriberOutputSchema.parse(syntheticOutput("focus_ae5bbf52b76149b4af22a67a9fbafeb6", "en"));
  const insights = insightsFor({ projection: output.projection, firstObservation: output.firstObservation ?? null }, en, "en");
  assert.ok(insights.length > 0);
  for (const insight of insights) {
    assert.ok(insight.family === null || FAMILY_ORDER.includes(insight.family), insight.id);
    // SEO and GEO are never inferred: with no search or generative measurement in the reading, no finding is in them.
    assert.ok(insight.channel === null || insight.channel === "WEB" || insight.id.startsWith("SEARCH_VISIBILITY") || insight.id.startsWith("GENERATIVE_VISIBILITY"), insight.id);
  }
});

test("the chips count what is unread: the number goes when it has been read, and a family with nothing reads quieter", () => {
  const items = [
    { family: "presence" as const, channel: "SEO" as const, changeKey: "a" },
    { family: "presence" as const, channel: "WEB" as const, changeKey: "b" },
    { family: "demand" as const, channel: null, changeKey: "c" },
  ];
  assert.deepEqual(litByChannel(items, new Set(["a"])), { SEO: 1, GEO: 0, WEB: 0 });
  assert.equal(litByFamily(items, new Set(["a", "b"])).presence, 2);
  // Once everything is read there is no number anywhere.
  assert.deepEqual(litByChannel(items, new Set()), { SEO: 0, GEO: 0, WEB: 0 });
  assert.ok(Object.values(litByFamily(items, new Set())).every(n => n === 0));
  const nav = readFileSync(resolve(process.cwd(), "components/family-nav.tsx"), "utf8");
  assert.match(nav, /unread\(lit\[id\]\)/);
  assert.match(nav, /unread\(litChannels\[channel\]\)/);
  assert.match(nav, /obs-facet-empty/);
  assert.doesNotMatch(nav, /obs-facet-lamp|counts\.families\[id\]\}<\/span>/);
});
