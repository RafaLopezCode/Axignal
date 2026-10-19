import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FamilyCanvas } from "../components/family-canvas";
import { insightsFor, type Reading } from "../lib/observatory";
import { translate } from "../lib/copy-catalog";

const t = (es: string, en: string) => translate(es, en, "es");
const month = (k: number) => new Date(new Date().getFullYear(), new Date().getMonth() - k, 10).toISOString();
const mention = (code: string, url: string, k: number) => ({ kind: "MENTION", code, statement: `Acme ${code} ${k}`, epistemicState: "POTENTIAL",
  sourceUrl: url, excerpt: "… Acme …", observedAt: month(k), detail: { outlet: new URL(url).hostname, notEndorsement: true } });
const reading = (discoveries: unknown[]): Reading => ({ projection: null,
  firstObservation: { state: "FIRST_PROOF_READY", firstProofReady: true, discoveries } } as unknown as Reading);

test("a family canvas shows states, the most telling findings, months and sources, each with its proof", () => {
  const insights = insightsFor(reading([
    mention("WEB_MENTION", "https://www.expansion.com/a", 0),
    mention("WEB_MENTION", "https://www.expansion.com/b", 2),
    mention("REVIEW_PAGE", "https://www.ocu.org/r", 1),
    mention("REVIEW_PAGE", "https://www.ocu.org/s", 14),  // older than the window
  ]), t, "es");
  const html = renderToStaticMarkup(createElement(FamilyCanvas, { family: "reputation", title: "Reputación", insights, onOpen() {} }));
  // Rendered without a locale provider: the English copy.
  for (const title of ["What has been observed", "The most important", "Over time", "Where it comes from"]) assert.match(html, new RegExp(title));
  assert.match(html, /Potential/);  // the state in words, never color alone
  assert.equal((html.match(/class="obs-months"/g) ?? []).length, 1);
  assert.equal((html.match(/<li style="--i:\d+">/g) ?? []).length >= 12, true);
  assert.match(html, /\(1 earlier\)/);  // the finding older than twelve months is said, not hidden
  assert.match(html, /expansion\.com/);
  assert.match(html, /Show me how AXIGNAL knows/);
  // The most important: same rank, the most recent first (the 14-month-old review last).
  assert.ok(html.indexOf("REVIEW_PAGE 1<") < html.indexOf("REVIEW_PAGE 14<"));
  assert.doesNotMatch(html, /\/100|universal/i);  // counts, never a score
});

test("a family with fewer than two known findings gets no canvas: the lanes already say it", () => {
  const insights = insightsFor(reading([
    mention("WEB_MENTION", "https://www.expansion.com/a", 0),
    { kind: "SIGNIFICANT_UNKNOWN", code: "NO_PRESS_MENTION_FOUND", statement: "x", epistemicState: "UNKNOWN", sourceUrl: null, excerpt: null, observedAt: month(0), detail: {} },
  ]), t, "es");
  assert.equal(renderToStaticMarkup(createElement(FamilyCanvas, { family: "reputation", title: "Reputación", insights, onOpen() {} })), "");
});
