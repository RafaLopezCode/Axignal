import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CanvasEvidenceSheet } from "../components/canvas-evidence-sheet";

test("canvas proof is a labelled non-modal dialog so the separate AXENT rail stays usable", () => {
  const html = renderToStaticMarkup(createElement(CanvasEvidenceSheet, {
    title: "Evidence and its limits", focusKey: "authorized:finding", onClose() {},
    children: createElement("p", null, "Observed source; commercial outcome remains unknown."),
  }));
  assert.match(html, /role="dialog" aria-labelledby="obs-evidence-title"/);
  assert.doesNotMatch(html, /aria-modal="true"/);
  assert.match(html, /<h2 id="obs-evidence-title" tabindex="-1">Evidence and its limits<\/h2>/);
  assert.match(html, /aria-label="Close evidence"/);
  assert.match(html, /Observed source; commercial outcome remains unknown\./);
  assert.doesNotMatch(html, /axent-panel|textarea|iframe/);
});

test("the sheet preserves the provided source, currentness and uncertainty verbatim", () => {
  const source = "https://example.org/source?observed=2026-10-15";
  const html = renderToStaticMarkup(createElement(CanvasEvidenceSheet, {
    title: "Source", focusKey: "authorized:source", onClose() {},
    children: createElement("article", null,
      createElement("a", { href: source, target: "_blank", rel: "noopener noreferrer" }, "Preserved source"),
      createElement("time", { dateTime: "2026-10-15" }, "Historical observation"),
      createElement("p", null, "POTENTIAL; reach remains UNKNOWN")),
  }));
  assert.ok(html.includes(source));
  assert.match(html, /datetime="2026-10-15"/i);
  assert.match(html, /POTENTIAL; reach remains UNKNOWN/);
});
