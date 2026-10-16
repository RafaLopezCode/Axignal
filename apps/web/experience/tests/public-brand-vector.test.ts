import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  PublicBrandVector,
  PUBLIC_BRAND_SOURCE_SHA256,
} from "../components/public-brand-vector";

const source = fs.readFileSync(
  path.resolve("public/brand/logo-light.svg"),
  "utf8",
);
const attributes = (html: string, tag: string, name: string) =>
  [
    ...html.matchAll(
      new RegExp("<" + tag + "\\b[^>]*\\b" + name + '="([^"]+)"', "g"),
    ),
  ].map((match) => match[1]);

test("public vector logos retain the approved original geometry, transforms and fills", () => {
  const html = renderToStaticMarkup(createElement(PublicBrandVector));
  assert.equal(
    createHash("sha256").update(source).digest("hex"),
    PUBLIC_BRAND_SOURCE_SHA256,
  );
  assert.deepEqual(
    attributes(html, "path", "d"),
    attributes(source, "path", "d"),
  );
  assert.equal(attributes(html, "path", "d").length, 2);
  assert.deepEqual(
    attributes(html, "g", "transform"),
    attributes(source, "g", "transform"),
  );
  for (const fill of ["rgb(76,76,76)", "rgb(53,79,152)"])
    assert.ok(html.includes('fill="' + fill + '"'));
});

test("public vector logos contain no raster, font substitution or external image", () => {
  const html = renderToStaticMarkup(createElement(PublicBrandVector));
  assert.doesNotMatch(
    html,
    /<(?:image|img|text|foreignObject)\b|data:image|\.(?:png|jpe?g)/i,
  );
  assert.match(html, /viewBox="0 0 3011 873"/);
  assert.match(html, /width="147" height="43"/);
  assert.match(html, /aria-hidden="true"/);
  const footer = renderToStaticMarkup(
    createElement(PublicBrandVector, { width: 195, height: 57 }),
  );
  assert.match(footer, /width="195" height="57"/);
  assert.deepEqual(
    attributes(footer, "path", "d"),
    attributes(html, "path", "d"),
  );
});
