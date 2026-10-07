import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
// @ts-expect-error Build helper is plain ESM and intentionally framework-independent.
import { localizeStaticKnowledgeHtml } from "../tools/localize-static-html-lang.mjs";

test("localized knowledge build helper rewrites only prerendered knowledge html lang", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "axignal-lang-"));
  try {
    for (const locale of ["es", "en"]) {
      const directory = path.join(root, locale, "knowledge");
      fs.mkdirSync(directory, { recursive: true });
      fs.writeFileSync(path.join(root, locale, "knowledge.html"), '<html lang="es"><body>hub</body></html>');
      fs.writeFileSync(path.join(directory, "article.html"), '<html lang="es"><body>article</body></html>');
    }
    const updated = localizeStaticKnowledgeHtml({
      appDir: root,
      locales: ["es", "en"],
      expectedPerLocale: 2,
    });
    assert.equal(updated.length, 4);
    assert.match(fs.readFileSync(path.join(root, "es", "knowledge.html"), "utf8"), /<html lang="es">/);
    assert.match(fs.readFileSync(path.join(root, "en", "knowledge.html"), "utf8"), /<html lang="en">/);
    assert.match(fs.readFileSync(path.join(root, "en", "knowledge", "article.html"), "utf8"), /<html lang="en">/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("localized knowledge build helper fails closed on incomplete prerender output", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "axignal-lang-missing-"));
  try {
    fs.mkdirSync(path.join(root, "en"), { recursive: true });
    fs.writeFileSync(path.join(root, "en", "knowledge.html"), '<html lang="es"><body>hub</body></html>');
    assert.throws(
      () =>
        localizeStaticKnowledgeHtml({
          appDir: root,
          locales: ["en"],
          expectedPerLocale: 2,
        }),
      /Unexpected prerendered knowledge count/,
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
