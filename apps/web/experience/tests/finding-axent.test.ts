import test from "node:test";
import assert from "node:assert/strict";
import { explainFinding } from "../lib/finding-axent";
import { insightsFor, type Reading } from "../lib/observatory";
import { intentOf } from "../lib/runtime-axent";
import { translate } from "../lib/copy-catalog";
import type { Locale } from "../lib/languages";

const at = "2026-10-15T00:20:23Z";
const d = (kind: string, code: string, statement: string, state: string, detail: Record<string, unknown> = {}, sourceUrl: string | null = "https://acme.example/") =>
  ({ kind, code, statement, epistemicState: state, sourceUrl, excerpt: null, observedAt: at, detail });

// One finding (or more) in every family, plus an unknown, a change and the case that broke it.
const reading: Reading = { projection: null, firstObservation: { state: "FIRST_PROOF_READY", firstProofReady: true, discoveries: [
  d("REPRESENTATION_GAP", "AUDIT:IMAGES_DESCRIBED", "IMAGES_DESCRIBED", "POTENTIAL", { impact: "LOW", instrument: "representation-audit.v1", value: { images: 5, withoutAlt: 3 } }),
  d("GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY", "0/2", "OBSERVED", { sample: "3 questions, 1 answer each", conditions: "Fixed questions, no web search" }),
  d("MENTION", "PRESS_MENTION", "Acme opens a plant", "OBSERVED", { source: "El Diario" }, "https://news.example/acme"),
  d("ACTIVITY", "web-design", "Web design and development", "POTENTIAL", { method: "LEXICON", routingCodes: ["CPV:72413000"] }),
  d("DECLARED_LOCATION", "LOCATION_STATED_IN_TEXT", "EU/ES", "DECLARED"),
  d("RELATIONSHIP", "CLIENT_DECLARED", "Iberdrola", "DECLARED", { limitation: "Shown by the organization itself as a client; the counterparty has not confirmed it." }),
  d("DEMAND", "POTENTIAL_BUYER", "Endesa", "POTENTIAL", { signalTypes: ["CUSTOMER_OF_COMPETITOR"], independentSignals: 1,
    signals: [{ type: "CUSTOMER_OF_COMPETITOR", via: "Rival SA", basis: "Awarded public contracts in this activity to Rival SA.", sourceUrl: "https://award.example/1", observedAt: "2026-09-01T00:00:00Z" }] }),
  d("OPERATING_SIGNAL", "JOB_POSTINGS_PUBLISHED", "12 open positions", "OBSERVED", { count: 12 }),
  d("ECONOMIC_FACT", "WIKIDATA:revenue", "12000000", "POTENTIAL", { source: "Wikidata", value: 12000000 }, "https://www.wikidata.org/wiki/Q1"),
  d("IDENTITY_HINT", "LEGAL_NAME_DECLARED", "Acme Ingeniería S.L.", "DECLARED"),
  d("SIGNIFICANT_UNKNOWN", "IDENTITY_NOT_VERIFIED", "Legal identity not verified yet", "UNKNOWN", {}, null),
  d("CONTEXT_SIGNAL", "REGULATION", "New energy efficiency rule", "POTENTIAL", { source: "BOE" }, "https://boe.example/1"),
  d("SIGNIFICANT_UNKNOWN", "NO_PRESS_MENTION_FOUND", "No headline names it", "UNKNOWN", {}, null),
  d("CHANGE", "presence:presence.ai_named_share:EVOLUTION", "0.25 -> 0.5", "OBSERVED", { previous: "0.25", comparison: "COMPARABLE" }),
] } as unknown as Reading["firstObservation"] };

const QUESTIONS: Array<[string, string, ReturnType<typeof intentOf>]> = [
  ["Qué sabes", "What do you know", "known"],
  ["Qué cambió", "What changed", "changed"],
  ["Por qué importa", "Why it matters", "why"],
  ["Qué sigue abierto", "What remains open", "unknown"],
  ["Cómo lo sabes", "How do you know", "evidence"],
  ["Qué investigarías después", "What would you investigate next", "research"],
];
const LOCALES: Locale[] = ["es", "en", "de", "pt", "fr", "it"];
const RAW = /\b(UNKNOWN|OBSERVED|POTENTIAL|DECLARED|DESCONOCIDAS)\b|governed source sensor|Xignal|[A-Z][A-Z0-9]*_[A-Z0-9_]+/;

test("AXENT answers every question about every finding of every family from that finding, in the reader's language", () => {
  for (const locale of LOCALES) {
    const t = (es: string, en: string) => translate(es, en, locale);
    const insights = insightsFor(reading, t, locale);
    const families = new Set(insights.map(i => i.family).filter(Boolean));
    assert.equal(families.size, 10, `${locale}: every family is represented (${[...families].join(",")})`);
    for (const insight of insights) {
      for (const [es, en, expected] of QUESTIONS) {
        const question = t(es, en);
        assert.equal(intentOf(question), expected, `${locale}: «${question}» is read as ${expected}`);
        const answer = explainFinding({ insight, related: insights, prompt: question, organizationId: "org", contextId: "ctx", t, locale });
        const texts = [answer.summary, ...answer.known, ...answer.openQuestions, ...answer.evidenceBasis];
        const where = `${locale} · ${insight.id} · ${question}`;
        assert.ok(answer.summary.trim(), `${where}: an answer`);
        assert.equal(new Set(texts).size, texts.length, `${where}: no sentence twice`);
        for (const text of texts) assert.doesNotMatch(text, RAW, `${where}: no internal code in «${text}»`);
        if (expected === "evidence") {
          assert.equal(answer.evidenceBasis.length, insight.sources.length, `${where}: every source shown`);
          for (const url of insight.sources.map(s => s.url).filter(Boolean)) assert.ok(answer.sourceRefs.includes(url!), `${where}: link kept`);
        }
        if (expected === "research") assert.ok(answer.known.length === 1, `${where}: one concrete next step`);
      }
    }
  }
});

test("the case that broke it: «how do you know» about images answers with that finding, not the organization's narrative", () => {
  const t = (es: string, en: string) => translate(es, en, "es");
  const insights = insightsFor(reading, t, "es");
  const images = insights.find(i => i.id.startsWith("REPRESENTATION_GAP:AUDIT:IMAGES_DESCRIBED"))!;
  const answer = explainFinding({ insight: images, related: insights, prompt: "Cómo lo sabes", organizationId: "org", contextId: "ctx", t, locale: "es" });
  assert.match(answer.summary, /^Lo sabemos por esta fuente/);
  assert.ok(answer.evidenceBasis[0].includes("acme.example"));
  assert.ok(!JSON.stringify(answer).match(/homepage was reachable|página pública autorizada|presencia generativa/));
  // «What do you know» and «how do you know» are different questions.
  const known = explainFinding({ insight: images, related: insights, prompt: "Qué sabes", organizationId: "org", contextId: "ctx", t, locale: "es" });
  assert.notEqual(known.summary, answer.summary);
  assert.equal(known.summary, images.headline);
});

test("a change is said against the earlier reading; without one, no change is declared", () => {
  const t = (es: string, en: string) => translate(es, en, "en");
  const insights = insightsFor(reading, t, "en");
  const buyer = insights.find(i => i.id.startsWith("DEMAND:POTENTIAL_BUYER"))!;
  const answer = explainFinding({ insight: buyer, related: insights, prompt: "What changed", organizationId: "org", contextId: "ctx", t, locale: "en" });
  assert.match(answer.summary, /no comparable earlier reading/);
});
