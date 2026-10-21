import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import postcss from "postcss";
import { gzipSync } from "node:zlib";
import { minifyLabStyles } from "../tools/minify-lab-styles.mjs";
import { createHash } from "node:crypto";
import styles from "../lib/surface-styles.json";
import { isLandingSurfacePath } from "../lib/surface-style-path";

test("the legacy stylesheet preserves every original rule in original import order", () => {
  const original = [
    "app/globals.css",
    "app/public.css",
    "app/typography.css",
    "app/acquisition.css",
    "app/funnel.css",
    "app/public-layout.css",
    "components/cognition/cognition.css",
    "components/public-header.css",
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
    ".dialog-body",
    ".dialog-header",
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
  for (const asset of [styles.base, styles.lab]) {
    const css = postcss.parse(fs.readFileSync(new URL("../public" + asset.url, import.meta.url), "utf8"));
    const declarations = (selector: string, property: string) => {
      const values: string[] = [];
      css.walkRules(rule => {
        if (postcss.list.comma(rule.selector).includes(selector))
          rule.walkDecls(property, declaration => { values.push(declaration.value); });
      });
      return values;
    };
    assert.ok(declarations(".dialog-body", "padding").some(value => value !== "0"), "Dialog content must retain its inset in the delivered CSS");
    assert.ok(declarations(".dialog-header", "display").includes("flex"), "Dialog title and close action must retain their layout");
  }
});
test("the public home and isolated landing preview use the focused landing skin", () => {
  for (const locale of ["", "es/", "en/", "de/", "pt/", "fr/", "it/"])
    assert.equal(isLandingSurfacePath("/" + locale + "landing-lab"), true);
  for (const path of [
    null,
    "/demo",
    "/account",
    "/login",
    "/es/pricing",
    "/es/landing-lab-other",
  ])
    assert.equal(isLandingSurfacePath(path), false);
  for (const path of ["/", "/es", "/en", "/fr/", "/de", "/it", "/pt"])
    assert.equal(isLandingSurfacePath(path), true);
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

// Compare the complete ordered tree, including values, importance and at-rule
// parameters. Formatting may shrink; the cascade and custom properties may not.
function semanticCss(css: string): unknown {
  const tree = (node: any): unknown => {
    const children = node.nodes
      ?.filter((child: any) => child.type !== "comment")
      .map(tree);
    if (node.type === "decl")
      return [node.type, node.prop, node.value, !!node.important];
    if (node.type === "rule")
      return [node.type, postcss.list.comma(node.selector), children];
    if (node.type === "atrule")
      return [node.type, node.name, node.params, children];
    return [node.type, children];
  };
  return tree(postcss.parse(css));
}

test("the isolated lab keeps every source rule and declaration in order after lossless minification", () => {
  const read = (path: string) =>
    fs
      .readFileSync(new URL("../" + path, import.meta.url), "utf8")
      .replace(/\r\n/g, "\n");
  const original =
    read("public" + styles.base.url) +
    "\n/* components/landing-lab.css */\n" +
    read("components/landing-lab.css");
  const delivered = read("public" + styles.lab.url);
  assert.equal(delivered, minifyLabStyles(original));
  assert.deepEqual(semanticCss(delivered), semanticCss(original));
  assert.ok(
    gzipSync(delivered).length < 14000,
    "Keep the lab wire stylesheet below 14 KB gzip",
  );
  assert.ok(
    styles.lab.bytes < 120000,
    "The complete landing skin must remain far below the legacy skin",
  );
});

test("font provenance uses Git LF text, independent of Windows working-copy newlines", () => {
  const source = fs.readFileSync(
    new URL("../lib/landing-lab-fonts.json", import.meta.url),
    "utf8",
  );
  const lf = source.replace(/\r\n/g, "\n");
  assert.equal(
    styles.fontManifestSha256,
    createHash("sha256").update(lf).digest("hex"),
    "The committed source and local generator must agree across operating systems",
  );
});

test("formatting compression preserves custom-property whitespace, quoted commas and nested rules", () => {
  const original = `/*! retain license */
    :root { --empty: ; --tokens: a b; --string: "a, b"; }
    @supports (display: grid) { @media (min-width: 700px) {
      .a:is(.b,.c), [title="a, b"] { width: calc(100% - 2px); opacity: .75 !important; }
    } }
    @keyframes example { from { transform: translateX(0); } to { transform: translateX(1px); } }
  `;
  const delivered = minifyLabStyles(original);
  assert.deepEqual(semanticCss(delivered), semanticCss(original));
  assert.ok(delivered.includes("retain license"));
  assert.ok(delivered.includes("--empty: ;"));
});
