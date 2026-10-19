import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { InsightSources } from "../components/insight-sources";
import { SyntheticEvidenceProvider } from "../components/evidence-link-context";
import { labInsight } from "../lib/landing-lab-model";
import { exampleInsights } from "../lib/landing-observatory";
import {
  labCopy,
  labQuestions,
  labPersonas,
  labFaq,
} from "../lib/landing-lab-copy";
import { locales } from "../lib/languages";

const sources = [
  {
    url: "https://example.org/document",
    label: "Public record",
    observedAt: "2026-09-01",
    quote: "Exact supporting quotation.",
  },
];
test("the same source is linked for a real reading and explicitly non-navigable in the synthetic context", () => {
  const view = createElement(InsightSources, {
    sources,
    proof: [{ label: "Eligibility", value: "Unknown" }],
  });
  const real = renderToStaticMarkup(view);
  assert.match(real, /href="https:\/\/example.org\/document"/);
  assert.match(real, /rel="noopener noreferrer"/);
  assert.match(real, /datetime="2026-09-01"/i);
  const synthetic = renderToStaticMarkup(
    createElement(SyntheticEvidenceProvider, null, view),
  );
  assert.doesNotMatch(synthetic, /<a\b/);
  assert.match(synthetic, /Fictional source, non-navigable example/);
  assert.match(synthetic, /Exact supporting quotation\./);
  assert.match(synthetic, /<dt>Eligibility<\/dt><dd>Unknown<\/dd>/);
});
test("sharing proof does not turn a missing source, quotation or date into a fact", () => {
  const html = renderToStaticMarkup(
    createElement(InsightSources, {
      sources: [
        {
          url: null,
          label: "Source with missing metadata",
          quote: null,
          observedAt: null,
        },
      ],
      proof: [],
    }),
  );
  assert.doesNotMatch(html, /<a\b|<time\b|<blockquote\b/);
  assert.match(html, /Source with missing metadata/);
});
test("all discovery choices resolve to an existing fixture and earlier time never borrows a future finding", () => {
  const copy = (value: { en: string }) => value.en;
  const now = exampleInsights("2026-10-03", copy);
  for (const question of labQuestions)
    assert.ok(
      now.some((item) => item.id === question.id),
      question.id,
    );
  assert.equal(
    now.find((item) => item.id === "renovation")?.nature,
    "POTENTIAL",
  );
  assert.equal(
    now.find((item) => item.id === "reputation-gap")?.nature,
    "UNKNOWN",
  );
  assert.equal(
    exampleInsights("2026-07-01", copy).find(
      (item) => item.id === "renovation",
    ),
    undefined,
  );
  for (const persona of labPersonas)
    assert.ok(
      labQuestions.some((question) => question.id === persona.scenario),
    );
});
test("the new commercial narrative has authored copy for all six languages", () => {
  const texts = [
    ...Object.values(labCopy).flatMap((value) =>
      Array.isArray(value) ? value : [value],
    ),
    ...labQuestions.map((item) => item.label),
    ...labPersonas.flatMap((item) => [
      item.title,
      item.before,
      item.after,
      item.output,
    ]),
    ...labFaq.flatMap((item) => [item.question, item.answer]),
  ];
  for (const text of texts)
    for (const { id } of locales)
      assert.ok(text[id]?.trim(), id + " / " + text.en);
});

test("digital proof preserves the instrument, sample and uncertainty, without borrowing future evidence", () => {
  const copy = (value: { en: string }) => value.en;
  const result = labInsight("2026-10-03", "representation", copy);
  assert.ok(result);
  assert.match(result.sources[0].quote, /DEMO-DRI v1/);
  assert.match(result.sources[0].quote, /2 samples/);
  assert.match(result.sources[0].quote, /No population estimate/);
  assert.equal(labInsight("2026-09-01", "representation", copy), null);
  for (const date of ["2026-07-01", "2026-09-01", "2026-10-03"] as const)
    for (const question of labQuestions)
      for (const source of labInsight(date, question.id, copy)?.sources ?? [])
        assert.ok(source.observedAt <= date);
});
