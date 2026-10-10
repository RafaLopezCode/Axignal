import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import snapshot from "../lib/demo/synthetic-observatory.json";
import { SYNTHETIC_PHRASES } from "../lib/demo/synthetic-phrases";

type Discovery = { kind: string; detail: Record<string, unknown>; statement: string };
type Item = { sourceType: string; observedAt: string; normalizedStateChanged: boolean | null };
type Output = { firstObservation: { discoveries: Discovery[] }; projection: { temporalHistory: { items: Item[] } } };
const outputs = snapshot.outputs as unknown as Record<string, Output>;
const seoGeo = outputs[snapshot.portfolio[1].focusId];
const energy = outputs[snapshot.portfolio[0].focusId];
const measurements = (output: Output) => output.firstObservation.discoveries.filter(d => d.kind === "SEARCH_VISIBILITY" || d.kind === "GENERATIVE_VISIBILITY");

test("every SEO and GEO measurement states how it was made and what it does not cover", () => {
  const found = measurements(seoGeo);
  assert.ok(found.filter(d => d.kind === "SEARCH_VISIBILITY").length >= 2);
  assert.ok(found.filter(d => d.kind === "GENERATIVE_VISIBILITY").length >= 1);
  for (const d of found) {
    for (const key of ["instrument", "conditions", "sample", "coverage", "limitation"]) assert.equal(typeof d.detail[key], "string", `${d.statement}: ${key}`);
  }
});

test("a change is stated only against a comparable earlier observation", () => {
  const found = measurements(seoGeo);
  for (const d of found) if ("previous" in d.detail) assert.equal(d.detail.comparison, "COMPARABLE", d.statement);
  // The demo shows both what is claimed and what is not: a comparable change and a first observation.
  assert.ok(found.some(d => d.detail.comparison === "COMPARABLE"));
  assert.ok(found.some(d => d.detail.comparison === "FIRST_OBSERVATION" && !("previous" in d.detail)));
  for (const type of ["PUBLIC_SEARCH_VISIBILITY", "GENERATIVE_ANSWER_SURFACES"]) {
    const series = seoGeo.projection.temporalHistory.items.filter(i => i.sourceType === type).sort((a, b) => a.observedAt.localeCompare(b.observedAt));
    assert.ok(series.length >= 2, type);
    assert.equal(series[0].normalizedStateChanged, null, `${type}: the first observation cannot claim a change`);
    assert.equal(series.at(-1)?.normalizedStateChanged, true, type);
  }
});

test("where nothing was measured nothing is invented: the energy organization has no SEO or GEO measurement", () => {
  assert.deepEqual(measurements(energy), []);
  assert.ok(!energy.projection.temporalHistory.items.some(i => i.sourceType === "PUBLIC_SEARCH_VISIBILITY" || i.sourceType === "GENERATIVE_ANSWER_SURFACES"));
});

test("every phrase of the synthetic measurements is translated into the other five locales", () => {
  const strings = measurements(seoGeo).flatMap(d => [d.statement, ...["conditions", "sample", "coverage", "previous", "limitation"].map(key => d.detail[key])])
    .filter((value): value is string => typeof value === "string");
  assert.ok(strings.length >= 15);
  for (const text of strings) {
    const phrase = SYNTHETIC_PHRASES[text];
    assert.ok(phrase, `no translation for: ${text}`);
    for (const locale of ["es", "de", "pt", "fr", "it"] as const) assert.ok(phrase[locale]?.length > 8, `${locale}: ${text}`);
  }
});

test("the rail's language select fills its label, so no language name is clipped", () => {
  const css = readFileSync(resolve(process.cwd(), "components/observatory.css"), "utf8");
  assert.match(css, /\.obs-rail-locale \.locale-selector select \{ flex: 1 1 auto; min-inline-size: 0; inline-size: 100%;/);
});
