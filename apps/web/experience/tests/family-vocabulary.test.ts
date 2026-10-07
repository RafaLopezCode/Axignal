import test from "node:test";
import assert from "node:assert/strict";
import { families, makeContext, type FamilyId } from "../lib/projection";
import { familiesForText, familyTerms, familyVocabulary, fold } from "../lib/family-vocabulary";
import { locales } from "../lib/languages";
import { validatePlan } from "../lib/governance";

// The five-second test, made objective: where a person looks for X, X is written.
const findable: [string, FamilyId][] = [
  ["SEO", "presence"], ["GEO", "presence"], ["Comentarios", "reputation"], ["Opiniones", "reputation"],
  ["Oportunidades", "demand"], ["Licitaciones", "demand"], ["Clientes", "relationships"],
  ["Proveedores", "relationships"], ["Servicios", "value"], ["Capacidades", "value"],
  ["Sectores", "markets"], ["Proyectos", "activity"], ["Regulación", "context"], ["Facturación", "economics"],
];

test("the ten canonical families are unchanged and every one has everyday words", () => {
  assert.deepEqual(
    families.map((f) => f.id),
    ["presence", "reputation", "value", "markets", "relationships", "demand", "activity", "economics", "organization", "context"],
  );
  for (const f of families) {
    assert.ok(familyVocabulary[f.id].terms.length >= 3, f.id);
    for (const { id: locale } of locales) assert.ok(familyTerms(f.id, locale).every((term) => term.trim()), `${f.id}/${locale}`);
  }
});

test("each searched topic is visibly written in exactly one family, in Spanish", () => {
  for (const [word, family] of findable) {
    const holders = families.filter((f) => familyTerms(f.id, "es").some((term) => fold(term) === fold(word)));
    assert.deepEqual(holders.map((f) => f.id), [family], word);
  }
});

test("one concept, one expression: no visible term is shared by two families in any language", () => {
  for (const { id: locale } of locales) {
    const seen = new Map<string, FamilyId>();
    for (const f of families)
      for (const term of familyTerms(f.id, locale)) {
        const key = fold(term);
        assert.ok(!seen.has(key) || seen.get(key) === f.id, `${locale}: "${term}" in ${seen.get(key)} and ${f.id}`);
        seen.set(key, f.id);
      }
  }
});

test("everyday questions in any product language reach the canonical family", () => {
  const questions: [string, FamilyId][] = [
    ["¿Cómo está mi SEO?", "presence"], ["¿Aparecemos en ChatGPT?", "presence"],
    ["¿Qué dicen de nosotros?", "reputation"], ["¿Hay reseñas?", "reputation"],
    ["¿Hay oportunidades?", "demand"], ["Which tenders could we bid for?", "demand"],
    ["¿Qué clientes aparecen?", "relationships"], ["Wer sind unsere Lieferanten?", "relationships"],
    ["¿Qué servicios ofrecemos?", "value"], ["Quels projets récents ?", "activity"],
    ["Quale regolamentazione ci riguarda?", "context"], ["Qual é a faturação?", "economics"],
    ["¿En qué mercados estamos?", "markets"], ["¿Quién es esta empresa?", "organization"],
  ];
  for (const [question, family] of questions) assert.equal(familiesForText(question)[0], family, question);
  assert.deepEqual(familiesForText("buenos días"), []);
  // Talk about the conversation itself is not a topic.
  assert.deepEqual(familiesForText("Explain this context"), []);
  assert.deepEqual(familiesForText("Explícame este contexto"), []);
  // Short words only match on their own: "geo" is not "geografía".
  assert.notEqual(familiesForText("geografías")[0], "presence");
});

test("Axent may only point at a canonical family", () => {
  const context = makeContext();
  const plan = (ref: string) => ({ version: 1, revision: context.revision, items: [{ component: "family", ref, priority: "primary" }] });
  assert.equal(validatePlan(plan("presence"), context).success, true);
  assert.equal(validatePlan(plan("seo-family"), context).success, false);
});

async function ask(text: string, locale = "es") {
  const { POST } = await import("../app/api/axent/route");
  const response = await POST(
    new Request("http://127.0.0.1:3810/api/axent", {
      method: "POST",
      headers: { origin: "http://127.0.0.1:3810", host: "127.0.0.1:3810", "content-type": "application/json" },
      body: JSON.stringify({ locale, context: makeContext(), messages: [{ role: "user", parts: [{ type: "text", text }] }] }),
    }),
  );
  assert.equal(response.status, 200);
  return response.text();
}

test("Axent answers an everyday question by pointing at the family where it lives", async () => {
  // The illustrative context is Markets; SEO lives in Presence.
  const seo = await ask("¿Cómo está mi SEO?");
  assert.ok(seo.includes('"component":"family","ref":"presence"'));
  assert.ok(seo.includes("Presencia (SEO · GEO · Visibilidad digital)"));
  const reviews = await ask("What do people say about us?", "en");
  assert.ok(reviews.includes('"ref":"reputation"'));
  // A question about change stays with the family in view.
  const changed = await ask("¿Qué cambió?");
  assert.equal(changed.includes('"component":"family"'), false);
  // A question already about the family in view is answered there.
  const markets = await ask("¿En qué mercados hay contexto?");
  assert.equal(markets.includes('"component":"family"'), false);
});

test("the funnel has one name per depth across lenses, signal tabs and Axent", async () => {
  const { readFileSync } = await import("node:fs");
  const { funnelLayers } = await import("../lib/funnel");
  const source = (path: string) => readFileSync(new URL(path, import.meta.url), "utf8");
  // Every surface reads the depths from the funnel authority instead of its own words.
  for (const file of ["../components/cognition/grammar.tsx", "../components/panorama.tsx", "../components/axent.tsx"])
    assert.ok(source(file).includes("funnelLayers"), file);
  for (const retired of ["¿Por qué merece atención?", "¿Qué evidencia la sostiene?"])
    assert.equal(source("../components/axent.tsx").includes(retired), false, retired);
  assert.deepEqual(Object.keys(funnelLayers), ["1", "2", "3", "4"]);
  // Axent's own "how does AXIGNAL know?" question composes the evidence behind the signal.
  const answer = await ask("¿Cómo lo sabe AXIGNAL?");
  assert.ok(answer.includes('"component":"evidence"'));
});
