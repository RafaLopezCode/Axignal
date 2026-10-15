import test from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Reading, Sources } from "../components/admin-operational";
import { formatValue, humanValue, isUnknown, matchesRecord, operationalCopy, recordReference, recordTitle, text } from "../lib/admin-presentation";
import type { Locale } from "../lib/languages";

const locales: Locale[] = ["es", "en", "de", "pt", "fr", "it"];
test("unknown never becomes zero, false, currency or a successful health state", () => {
  for (const locale of locales) {
    const format = (value: null | string | number | boolean) => formatValue("value", value, { unit: "CURRENCY", currency: "EUR" }, locale);
    assert.notEqual(format(null), format(0));
    assert.notEqual(format(false), format(null));
    for (const value of [undefined, null, "UNKNOWN", "NOT_AVAILABLE"]) assert.equal(isUnknown(value), true);
    for (const value of [0, false, "0", "NOT_CONFIGURED"]) assert.equal(isUnknown(value), false);
    assert.equal(format("UNKNOWN"), format(null));
  }
});
test("amounts respect source units and currency exponents", () => {
  assert.equal(formatValue("value", "1234.50", { unit: "CURRENCY", currency: "EUR" }, "en"), "€1,234.50");
  assert.equal(formatValue("grossMinor", 123450, { currency: "EUR" }, "en"), "€1,234.50");
  assert.equal(formatValue("grossMinor", 1234, { currency: "JPY" }, "en"), "¥1,234");
  assert.equal(formatValue("grossMinor", 1234, { currency: "BHD" }, "en"), new Intl.NumberFormat("en", { style: "currency", currency: "BHD" }).format(1.234));
  assert.equal(formatValue("value", "HEALTHY", { unit: "STATUS" }, "en"), "Healthy");
});
test("identity uses the supplied record reference when a display name is unavailable", () => {
  const record = { xeedId: "focus:truthful-reference", displayName: "Energía Pública", state: "UNKNOWN" };
  assert.equal(recordTitle(record, "es", 0), "Energía Pública");
  assert.equal(recordReference(record), "focus:truthful-reference");
  assert.equal(recordTitle({ xeedId: record.xeedId }, "es", 0), record.xeedId);
  assert.equal(recordTitle({ family: "canonical-admission" }, "es", 0), "Admisión de evidencia");
});
test("search matches readable names, localized state and reference without indexing arbitrary private payload", () => {
  const record = { displayName: "Energía Pública", xeedId: "focus:17", state: "UNKNOWN", hiddenPayload: "not-searchable" };
  for (const query of ["energia", "PÚBLICA", "focus:17", "desconocido"]) assert.equal(matchesRecord(record, query, "es", 0), true, query);
  assert.equal(matchesRecord(record, "not-searchable", "es", 0), false);
});
test("large collections expose eight records, a named search and reversible paging", () => {
  const html = renderToStaticMarkup(createElement(Reading, { locale: "en", record: { xeeds: Array.from({ length: 19 }, (_, i) => ({ xeedId: `focus:${i}`, observationsAdded: i })) } }));
  assert.equal((html.match(/class="admin-record-card"/g) ?? []).length, 8);
  assert.ok(html.includes("Search records: Observation focuses"));
  assert.match(html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " "), /Showing\s+1\s*–\s*8\s+of\s+19/);
  assert.ok(html.includes("Previous"));
  assert.ok(html.includes("Next"));
  assert.ok(!html.includes("focus:18"));
});
test("governance alerts preserve known zero, unknown and source evidence in compact rows", () => {
  const html = renderToStaticMarkup(createElement(Reading, { locale: "es", record: { alerts: [{ alertClass: "SOURCE_FAILURE", count: 0, completeness: "KNOWN", sourceRefs: ["evidence:0"] }, { alertClass: "COST_SPIKE", count: null, completeness: "UNKNOWN" }] } }));
  assert.ok(html.includes("Fallos de fuentes")); assert.ok(html.includes("Picos de coste"));
  assert.ok(html.includes(">0<")); assert.ok(html.includes("Desconocido")); assert.ok(html.includes("evidence:0"));
});
test("source disclosure retains field meaning, period, uncertainty and escaped hostile text", () => {
  const html = renderToStaticMarkup(createElement(Sources, { locale: "en", record: { sourceRecordIds: ["billing:admitted"], periodStart: "2026-10-01T00:00:00Z", unknownReason: "<script>unsafe()</script>", coverageNotes: ["Private operations only"] } }));
  for (const value of ["Source records", "billing:admitted", "Period start", "Reason for limitation", "Private operations only", "&lt;script&gt;"]) assert.ok(html.includes(value), value);
  assert.ok(!html.includes("<script>"));
});
test("all new operational vocabulary is available in six languages", () => {
  for (const [key, values] of Object.entries(operationalCopy)) {
    assert.equal(values.length, 6, key);
    for (const locale of locales) assert.ok(text(key, locale).length > 0);
  }
  for (const locale of locales) assert.notEqual(humanValue("SOURCE_FAILURE", locale), "SOURCE_FAILURE");
});
test("missing real source explains the limitation while retaining its exact reason code", () => {
  for (const locale of locales) {
    const html = renderToStaticMarkup(createElement(Sources, { locale, record: { unknownReason: "SOURCE_PROJECTION_UNAVAILABLE", sourceProjectionId: "business-revenue-summary" } }));
    assert.ok(html.includes(text("source_projection_unavailable", locale)));
    assert.ok(html.includes("<code>SOURCE_PROJECTION_UNAVAILABLE</code>"));
    assert.ok(html.includes("business-revenue-summary"));
  }
});
