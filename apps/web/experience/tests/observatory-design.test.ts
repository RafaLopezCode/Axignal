/**
 * The Observatory follows the global design scale: radii, spacing between blocks and disabled contrast.
 * The radius test reads the global stylesheet itself, so the scale cannot drift from what the product defines.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const read = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");
const observatory = read("components/observatory.css");
const global = read("app/globals.css");

/** The border-radius declared by the first global rule whose selector is exactly `selector`. */
function globalRadius(selector: string): string {
  const escaped = selector.replace(/[.[\]()]/g, "\\$&");
  const match = global.match(new RegExp(`(?:^|\\n|\\})\\s*${escaped}\\s*\\{[^}]*?border-radius:\\s*([^;}]+)`));
  assert.ok(match, `global rule ${selector} declares a radius`);
  return match[1].trim();
}
const token = (name: string) => observatory.match(new RegExp(`--${name}:\\s*([^;]+);`))?.[1].trim();

test("the Observatory's radius tokens are the global ones", () => {
  assert.equal(token("obs-r-control"), globalRadius(".button"));
  assert.equal(token("obs-r-badge"), globalRadius(".badge"));
  assert.equal(token("obs-r-field"), globalRadius(".search-field"));
  assert.match(token("obs-r-card") ?? "", /var\(--radius, 14px\)/);
  assert.match(global, /--radius:\s*14px/);
});

test("no Observatory rule invents a radius outside the scale", () => {
  const allowed = /^(var\(--obs-r-(card|control|field|badge)\)|var\(--obs-radius\)|50%|0|3px|3px 3px 0 0|6px|14px)$/;
  const radii = [...observatory.matchAll(/border-radius:\s*([^;}]+)/g)].map(m => m[1].trim());
  assert.ok(radii.length > 30);
  const outside = radii.filter(value => !allowed.test(value));
  assert.deepEqual(outside, [], "pills and ad-hoc radii are not part of the scale");
  assert.doesNotMatch(observatory, /border-radius:\s*999px/);
});

test("disabled controls keep their contrast through colour, never through opacity", () => {
  for (const selector of [".obs-button:disabled", ".obs-rail-cta:disabled", ".obs-rail-foot .obs-rail-action:not(.obs-rail-cta):disabled"]) {
    const rule = observatory.match(new RegExp(selector.replace(/[.[\]():]/g, "\\$&") + "\\s*\\{([^}]*)\\}"))?.[1] ?? "";
    assert.match(rule, /opacity:\s*1/, selector);
  }
});

test("the selected chip's count is a solid pill, so its number keeps its contrast", () => {
  assert.match(observatory, /\.obs-facet\[aria-pressed="true"\] \.obs-facet-count \{ background: #fff; color: var\(--obs-blue\); \}/);
  assert.doesNotMatch(observatory, /obs-facet-count \{[^}]*rgba\(255, 255, 255/);
});

test("a family without findings is spaced and sized like the lanes it replaces", () => {
  assert.match(observatory, /\.obs-brief \+ \.obs-empty-state \{ margin-block-start: 24px; max-inline-size: none; \}/);
});

test("the facet bar cannot widen the page: its grid column is constrained", () => {
  assert.match(observatory, /\.obs-facets \{ display: grid; grid-template-columns: minmax\(0, 1fr\);/);
});

test("the portfolio list keeps a stable gutter between its rows and its scrollbar", () => {
  assert.match(observatory, /\.obs-orgs \{ padding-inline-end: 10px; scrollbar-gutter: stable;/);
});

test("the actions menu stays on screen: it opens from its start on narrow screens", () => {
  assert.match(observatory, /@media \(max-width: 599px\) \{ \.obs-menu-list \{ inset-inline-start: 0; inset-inline-end: auto; max-inline-size: calc\(100vw - 32px\); \} \}/);
});

test("disabled menu actions keep their contrast through colour", () => {
  assert.match(observatory, /\.obs-menu-list button:disabled \{ opacity: 1; color: var\(--obs-muted\);/);
});

test("the rail's controls centre their label alike", () => {
  assert.match(observatory, /\.obs-rail-cta \{ justify-content: center;/);
  assert.match(observatory, /\.obs-rail-foot \.obs-rail-action:not\(\.obs-rail-cta\) \{ justify-content: center; \}/);
  assert.match(observatory, /\.obs-rail-locale \.locale-selector \{[^}]*justify-content: center/);
});
