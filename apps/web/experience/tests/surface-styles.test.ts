import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { createHash } from "node:crypto";
import styles from "../lib/surface-styles.json";
import { isLandingLabPath } from "../lib/surface-style-path";

test("the legacy stylesheet preserves every original rule in original import order", () => {
  const original = [
    "app/globals.css",
    "app/public.css",
    "app/typography.css",
    "app/acquisition.css",
    "app/funnel.css",
    "app/public-layout.css",
    "components/cognition/cognition.css",
  ];
  assert.deepEqual(styles.sources, original);
  const expected = original
    .map(
      (path) =>
        `/* ${path} */\n${fs.readFileSync(new URL("../" + path, import.meta.url), "utf8").replace(/\r\n/g, "\n")}`,
    )
    .join("\n");
  assert.equal(
    fs.readFileSync(
      new URL("../public" + styles.legacy.url, import.meta.url),
      "utf8",
    ),
    expected,
    "Regenerate with node tools/surface-styles.mjs",
  );
});
test("shared foundation retains accessibility, dialog, privacy and real request controls", () => {
  const base = fs.readFileSync(
    new URL("../public" + styles.base.url, import.meta.url),
    "utf8",
  );
  for (const selector of [
    ".skip-link",
    ".sr-only",
    ".dialog",
    ".icon-button",
    ".privacy-preferences-button",
    ".privacy-document-links",
    ".draft-form",
    ".brief-consent",
  ]) {
    assert.ok(base.includes(selector), selector);
  }
  assert.ok(
    base.length < 40000,
    "The lab must not receive a workspace-sized foundation",
  );
  for (const asset of [styles.base, styles.legacy, styles.lab]) {
    const data = fs.readFileSync(
      new URL("../public" + asset.url, import.meta.url),
    );
    assert.equal(data.length, asset.bytes);
    assert.equal(createHash("sha256").update(data).digest("hex"), asset.sha256);
  }
});
test("only the isolated lab omits the legacy skin", () => {
  for (const locale of ["", "es/", "en/", "de/", "pt/", "fr/", "it/"])
    assert.equal(isLandingLabPath("/" + locale + "landing-lab"), true);
  for (const path of [
    null,
    "/",
    "/es",
    "/demo",
    "/account",
    "/login",
    "/es/pricing",
    "/es/landing-lab-other",
  ])
    assert.equal(isLandingLabPath(path), false);
});

test("only exact immutable style assets enter the public router; the lab remains isolated", () => {
  const edge = fs.readFileSync(
    new URL(
      "../../../../deploy/production/traefik/axignal-public-seo.yml",
      import.meta.url,
    ),
    "utf8",
  );
  for (const asset of [styles.base, styles.legacy, styles.lab])
    assert.ok(edge.includes(`Path(\`${asset.url}\`)`));
  assert.ok(!edge.includes("PathPrefix(`/styles"));
  assert.ok(!edge.includes("landing-lab"));
});

test("the isolated lab gets one exact combined stylesheet, with its own skin after the foundation", () => {
  const read = (path: string) =>
    fs
      .readFileSync(new URL("../" + path, import.meta.url), "utf8")
      .replace(/\r\n/g, "\n");
  assert.equal(
    read("public" + styles.lab.url),
    read("public" + styles.base.url) +
      "\n/* components/landing-lab.css */\n" +
      read("components/landing-lab.css"),
  );
  assert.ok(
    styles.lab.bytes < 120000,
    "The complete landing skin must remain far below the legacy skin",
  );
});
