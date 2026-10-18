import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { basisRows, discoveryCopy, observationStateCopy, searchRows } from "../components/first-observation";
import { evidenceUrl, firstObservationSchema, observationStates, pendingOutputSchema, portfolioSchema, subscriberResultSchema, type Discovery } from "../lib/subscriber-contracts";
import { subscriberProxy } from "../lib/subscriber-server";

const savedFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = savedFetch; });
const token = "a".repeat(48);
const en = (_es: string, english: string) => english;
const es = (spanish: string) => spanish;

function discovery(kind: Discovery["kind"], code: string, extra: Partial<Discovery> = {}): Discovery {
  return { kind, code, statement: "Statement", epistemicState: "POTENTIAL", sourceUrl: null, excerpt: null, observedAt: "2026-10-08T10:00:00+00:00", detail: {}, ...extra };
}

// Every code the Python First Observation emits (application/first_observation/service.py).
const BACKEND_UNKNOWN_CODES = ["IDENTITY_NOT_VERIFIED", "WEBSITE_LINK_NOT_REGISTRY_VERIFIED", "ACTIVITY_NOT_ESTABLISHED", "LOCATION_NOT_DECLARED", "DEMAND_NOT_ROUTABLE", "NO_ROUTABLE_DEMAND_QUESTION", "NO_RELEVANT_DEMAND_FOUND", "NO_BUYER_SIGNALS", "NOT_AN_OPERATING_BUSINESS_SITE", "NO_PUBLIC_WEBSITE"];

test("every backend unknown code has its own fixed copy, never a generic or generated one", () => {
  const generic = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", "ROBOTS_DISALLOWED"), en).finding;
  for (const code of BACKEND_UNKNOWN_CODES) {
    const copy = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", code), en);
    assert.notEqual(copy.finding, generic, code);
    assert.ok(copy.why.length > 10, code);
  }
  const gap = discoveryCopy(discovery("SIGNIFICANT_UNKNOWN", "NO_GOVERNED_DEMAND_SOURCE:US/US-AR", { detail: { jurisdiction: "US/US-AR" } }), en);
  assert.match(gap.finding, /Arkansas, United States/);  // a place a person reads, not a code
  assert.match(gap.why, /not no market/);
  for (const state of observationStates) assert.ok(observationStateCopy(state, es).length > 10, state);
});

test("findings explain why they matter without promoting potential to fact", () => {
  const demand = discoveryCopy(discovery("DEMAND", "POTENTIAL_DEMAND", { detail: { title: "Solar works" } }), en);
  assert.match(demand.finding, /Solar works/);
  assert.match(demand.why, /not a customer/);
  assert.match(discoveryCopy(discovery("ACTIVITY", "isic-P"), en).why, /not a verified capability/);
  assert.match(discoveryCopy(discovery("IDENTITY_HINT", "LEGAL_NAME_DECLARED"), en).why, /Only a registry/);
  assert.match(discoveryCopy(discovery("REPRESENTATION_GAP", "OFFER_NOT_MACHINE_READABLE"), en).why, /not a measured cause/);
});

test("only public http(s) evidence links are rendered", () => {
  assert.equal(evidenceUrl("https://ted.europa.eu/en/notice/-/detail/1"), "https://ted.europa.eu/en/notice/-/detail/1");
  for (const value of ["javascript:alert(1)", "https://user:secret@example.com/", "data:text/html,x", "not a url", null]) {
    assert.equal(evidenceUrl(value), null, String(value));
  }
});

test("new observation states are accepted end to end", () => {
  for (const state of ["QUEUED", "CAPACITY_REQUIRED"]) {
    assert.equal(subscriberResultSchema.safeParse({ state: "IDENTITY_PENDING", observationState: state }).success, true);
  }
  const portfolio = portfolioSchema.parse({ state: "success", capacity: 1, capacityCurrentness: "CURRENT", canPurchase: null, contractingEnabled: false,
    organizations: [{ focusId: "pending_abc", organizationId: null, label: "https://example.com", state: "IDENTITY_PENDING", reason: "IDENTITY_SOURCE_UNAVAILABLE",
      observation: { state: "FIRST_PROOF_READY", firstProofReady: true, headline: "Education", observedAt: "2026-10-08T10:00:00+00:00" } }] });
  assert.equal(portfolio.organizations[0].observation?.state, "FIRST_PROOF_READY");
  assert.equal(firstObservationSchema.safeParse({ state: "INVENTED", firstProofReady: true, discoveries: [] }).success, false);
});

test("pending attention output passes the proxy and drops the private ledger", async () => {
  process.env.AXIGNAL_RUNTIME_ORIGIN = "http://127.0.0.1:18181"; process.env.AXIGNAL_EXPERIENCE_ORIGIN = "https://axignal.com";
  globalThis.fetch = async () => Response.json({ state: "success", kind: "PENDING_ATTENTION", firstObservation: {
    state: "FIRST_PROOF_READY", firstProofReady: true, authority: "OPERATIONAL_NOT_CANONICAL",
    target: { kind: "PENDING", website: "https://example.com/", name: null, identityLink: "IDENTITY_PENDING" },
    discoveries: [discovery("ACTIVITY", "isic-P", { sourceUrl: "https://example.com/", excerpt: "Spanish classes." })],
    ledger: { httpRequests: { value: 3, basis: "MEASURED" } }, judged: { isicSection: "P" } } });
  const response = await subscriberProxy(new Request("https://axignal.com/api/subscriber/organizations/pending_abc/output", { headers: { host: "axignal.com", cookie: `__Host-axignal-subscriber=${token}` } }), "/subscriber/organizations/pending_abc/output");
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(pendingOutputSchema.safeParse(body).success, true);
  assert.equal(body.firstObservation.discoveries[0].excerpt, "Spanish classes.");
  assert.ok(!JSON.stringify(body).includes("httpRequests"));
});

test("a provider's confidence is never shown as a percentage or a probability of truth", () => {
  const judged = discovery("ACTIVITY", "isic-P", { excerpt: "Spanish classes for adults.", detail: { method: "SEMANTIC_JUDGMENT", model: "jev-1.13.0", confidence: 0.91 } });
  const rows = basisRows(judged, en, "en");
  const text = rows.map(([label, value]) => `${label} ${value}`).join(" | ");
  assert.ok(!/%|0\.91|91/.test(text), text);
  assert.match(text, /non-authoritative judgment, not a probability of truth/);
  assert.match(text, /Source excerpt/);  // the original source excerpt is distinct from the controlled tokens judged by JEV
});

test("own-site signals keep their voice: observed technology, declared clients, hiring and ratings", () => {
  const tech = discoveryCopy(discovery("RELATIONSHIP", "TECHNOLOGY_SUPPLIER_OBSERVED", { statement: "Stripe", detail: { category: "PAYMENTS" } }), en);
  assert.match(tech.finding, /Technology supplier: Stripe \(payments\)/);
  assert.match(tech.why, /contract, plan or spend is not established/);
  const client = discoveryCopy(discovery("RELATIONSHIP", "CLIENT_DECLARED", { statement: "Iberdrola", detail: { heading: "Nuestros clientes" } }), en);
  assert.match(client.finding, /Client it shows: Iberdrola/);
  assert.match(client.why, /Nuestros clientes.*not confirmed/);
  assert.match(discoveryCopy(discovery("OPERATING_SIGNAL", "JOB_POSTINGS_PUBLISHED", { statement: "2", detail: { titles: ["Engineer"] } }), en).finding, /2 job posting\(s\): Engineer/);
  assert.match(discoveryCopy(discovery("RATING", "RATING_SELF_PUBLISHED", { statement: "4.7/5.0", detail: { count: 212 } }), en).why, /not an independent review/);
  assert.match(discoveryCopy(discovery("CREDENTIAL", "CERTIFICATION_CLAIMED", { statement: "ISO 9001" }), en).why, /register has not been checked/);
});

test("a change in time names the metric, both readings and its direction, never a cause", () => {
  const geo = discoveryCopy(discovery("CHANGE", "presence:presence.ai_named_share:EVOLUTION", { detail: { family: "presence",
    values: { metric: "presence.ai_named_share", before: 0, after: 0.5, beforeDay: "2026-10-01", afterDay: "2026-10-13", direction: "EVOLUTION" } } }), en);
  assert.match(geo.finding, /AI answers naming it in its category: 0 % . 50 %/);
  assert.match(geo.why, /improving.*2026-10-01.*not why/);
  const clients = discoveryCopy(discovery("CHANGE", "relationships:relationships.public_clients:ADDED", { detail: { family: "relationships",
    values: { metric: "relationships.public_clients", before: ["A"], after: ["A", "B"], added: ["B"], removed: [], direction: "ADDED" } } }), en);
  assert.match(clients.finding, /Public clients: new: B$/);
  assert.match(clients.why, /no judgement/);
});

test("an evaluator's fit judgment labels a tender and a set-aside list survives the contract (spec 075)", () => {
  const adjacent = discoveryCopy(discovery("DEMAND", "POTENTIAL_DEMAND", { statement: "Obras", detail: { title: "Obras de ventilación", fit: "ADJACENT", fitBy: { model: "jev-1.13.0" } } }), es);
  assert.match(adjacent.finding, /^Afín, otro trabajo principal · /);
  const core = discoveryCopy(discovery("DEMAND", "POTENTIAL_DEMAND", { statement: "Estudio", detail: { title: "Estudio", fit: "CORE" } }), es);
  assert.doesNotMatch(core.finding, /Afín|parcial/);
  const parsed = firstObservationSchema.parse({
    state: "FIRST_PROOF_READY", firstProofReady: true, observedAt: "2026-10-15T10:00:00+00:00", discoveries: [],
    demand: { live: true, asOf: "2026-10-15T10:00:00+00:00", total: 3, new: 0, setAsideByFit: 1,
      setAside: [{ title: "Captación de familias acogedoras", url: "https://contrataciondelestado.es/x", fitBy: { model: "jev-1.13.0" } }] },
  });
  assert.equal(parsed.demand?.setAsideByFit, 1);
  assert.equal(parsed.demand?.setAside?.[0]?.title, "Captación de familias acogedoras");
});

test("a call's published size is shown as facts, and nothing published shows nothing (spec 081)", () => {
  const call = discovery("DEMAND", "POTENTIAL_DEMAND", { detail: { deadline: "2026-11-01", scale: { estimatedValue: 564231.36, currency: "EUR", lots: 3, smallestLotValue: 34982.34, durationMonths: 12 } } });
  const text = basisRows(call, en, "en").map(([label, value]) => `${label} ${value}`).join(" | ");
  assert.match(text, /Published estimated value €564,231/);
  assert.match(text, /3 lots; the smallest, €34,982/);
  assert.match(text, /Published duration 1 year/);
  const unknown = basisRows(discovery("DEMAND", "POTENTIAL_DEMAND", { detail: { scale: { estimatedValue: null, lots: null, durationMonths: null } } }), en, "en");
  assert.ok(!unknown.some(([label]) => /value|Lots|duration/.test(label)));
});

test("an unclear offer is a representation gap in the reader's language (spec 084)", () => {
  const gap = discovery("REPRESENTATION_GAP", "OFFER_NATURE_UNCLEAR", { detail: { judgment: "UNCERTAIN" } });
  const copy = discoveryCopy(gap, en);
  assert.match(copy.finding, /does not make clear whether it sells products, performs services or carries out works/);
  assert.match(copy.why, /a reading of its own text, not a fact/);
});

test("AI visibility shows share of voice, position, who it names instead and cited sites (spec 090)", () => {
  const named = discovery("GENERATIVE_VISIBILITY", "AI_NAMED_FOR_CATEGORY", { statement: "2/6", detail: { shareOfVoice: 0.2, averagePosition: 2, competitorFrequency: [["Systemair", 5], ["Soler & Palau", 4]] } });
  const text = basisRows(named, en, "en").map(([label, value]) => `${label} ${value}`).join(" | ");
  assert.match(text, /Share of voice in the answers 20 % of the organizations named/);
  assert.match(text, /Average position when named 2/);
  assert.match(text, /Who it names instead Systemair \(5\) · Soler & Palau \(4\)/);
  const cited = discoveryCopy(discovery("GENERATIVE_VISIBILITY", "AI_CITED_SOURCES", { statement: "clima.example, ranking.example" }), en);
  assert.match(cited.finding, /Websites an AI assistant cites when asked about its activity: clima\.example/);
});

test("search ranking shows each search, its position, who ranks instead and a Google link (spec 091)", () => {
  const rows = [
    { keyword: "humus de lombriz", position: 2, ranksInstead: ["amazon.es", "leroymerlin.es"], googleUrl: "https://www.google.com/search?q=humus+de+lombriz&hl=es&gl=es" },
    { keyword: "abono orgánico", position: null, ranksInstead: ["amazon.es"], googleUrl: "javascript:alert(1)" },
  ];
  const ranked = discovery("SEARCH_VISIBILITY", "SEARCH_RANKS_MEASURED", { statement: "1/2", detail: { averagePosition: 2, rankingInstead: [["amazon.es", 2]], rows } });
  assert.match(discoveryCopy(ranked, en).finding, /It appears in 1 of 2 searches for its activity/);
  const text = basisRows(ranked, en, "en").map(([label, value]) => `${label} ${value}`).join(" | ");
  assert.match(text, /Average position where it appears 2/);
  assert.match(text, /Websites that appear instead amazon\.es \(2\)/);
  const shown = searchRows(ranked);
  assert.equal(shown[0]?.googleUrl, rows[0]?.googleUrl);
  assert.equal(shown[1]?.position, null);
  assert.equal(shown[1]?.googleUrl, null);
  const none = discovery("SEARCH_VISIBILITY", "SEARCH_NOT_RANKED", { statement: "0/3" });
  assert.match(discoveryCopy(none, en).finding, /does not appear among the top results of 3 searches/);
});

test("a declared register identifier reads as people say it, not as a scheme code (spec 094)", () => {
  const cif = discovery("IDENTITY_HINT", "IDENTIFIER_DECLARED:ES_CIF", { statement: "ES_CIF B54941729" });
  assert.match(discoveryCopy(cif, en).finding, /Its website declares: Spanish tax ID \(CIF\) B54941729/);
  const hr = discovery("IDENTITY_HINT", "IDENTIFIER_DECLARED:DE_HR", { statement: "DE_HR HRB 3771 Bonn" });
  assert.match(discoveryCopy(hr, en).finding, /German commercial register entry HRB 3771 Bonn/);
  const other = discovery("IDENTITY_HINT", "LEGAL_NAME_DECLARED", { statement: "Webpositer S.L." });
  assert.match(discoveryCopy(other, en).finding, /Its website declares: Webpositer S\.L\./);
});

test("its sector's market reads as the sector's, and its size as an order of magnitude (spec 095)", () => {
  const market = discovery("ECONOMIC_FACT", "SECTOR_MARKET:FR", { statement: "FR J62 2024", epistemicState: "DECLARED",
    detail: { fact: "sectorMarket", country: "FR", year: "2024", enterprises: 139348, personsEmployed: 560858, turnoverMeur: 104075, employmentGrowthPc: 0.58, divisions: ["J62"], industryReadFrom: "REGISTER_ACTIVITY_CODE" } });
  const copy = discoveryCopy(market, en);
  assert.match(copy.finding, /Its sector in France: 139,348 enterprises turn over €104(\.1)?B and employ 560,858 people \(2024\)/);
  assert.match(copy.why, /\+0\.58% over the last year/);
  assert.match(copy.why, /not for the organization/);
  const rows = basisRows(market, en, "en").map(([l, v]) => `${l} ${v}`).join(" | ");
  assert.match(rows, /Sector read from its register activity code/);
  const size = discovery("INXIGHT", "economics:SIZE_IN_SECTOR", { detail: { rule: "SIZE_IN_SECTOR", values: { country: "FR", sizeClass: "50-249", revenue: 16353415, revenueYear: "2023", timesSizeClassAverage: 0.7, timesSectorAverage: 21.9, shareAtLeastItsSize: 0.007 } } });
  const said = discoveryCopy(size, en).finding;
  assert.match(said, /Its revenue, €16\.4M \(2023\), is 0\.7 times the average of enterprises of its size \(50–249 people\) in its sector in France, and 21\.9 times/);
  assert.match(said, /Only 0\.7% of enterprises in its sector in France are its size \(50–249 people\) or larger/);
});

test("its own channel's pace and its country versions read in people's words (spec 096)", () => {
  const pace = discovery("OPERATING_SIGNAL", "PUBLISHING_CADENCE", { statement: "12 in 90 days", detail: { last90Days: 12, last365Days: 30, lastPublishedAt: "2026-10-06T10:00:00+00:00" } });
  assert.match(discoveryCopy(pace, en).finding, /It publishes on its own channel: 12 posts in 90 days \(latest 2026-10-06\)/);
  const quiet = discovery("OPERATING_SIGNAL", "PUBLISHING_CADENCE", { statement: "0 in 90 days", detail: { last90Days: 0, last365Days: 0, lastPublishedAt: "2025-12-23T10:00:00+00:00" } });
  assert.match(discoveryCopy(quiet, en).finding, /Its news channel is quiet: last post 2025-12-23/);
  const versions = discovery("DECLARED_SERVICE_AREA", "SITE_VERSIONS_FOR_COUNTRIES", { statement: "DE, FR", detail: { countries: { DE: ["HREFLANG"], FR: ["COUNTRY_DOMAIN"] } } });
  assert.match(discoveryCopy(versions, en).finding, /Its website has versions for: Germany, France/);
});

test("what it sells reads in its own catalog's words (spec 097)", () => {
  const offer = discovery("OFFER", "CATALOG_CATEGORIES", { statement: "Soaps, Candles", epistemicState: "DECLARED", detail: { categories: ["Soaps", "Candles"], basis: "PRODUCT_TYPES" } });
  const copy = discoveryCopy(offer, en);
  assert.match(copy.finding, /What it sells, according to its catalog: Soaps, Candles/);
  assert.match(copy.why, /not what it sells most/);
});
