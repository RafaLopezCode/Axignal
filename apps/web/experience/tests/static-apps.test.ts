import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, join } from "node:path";
import { execFileSync } from "node:child_process";
import { runInNewContext } from "node:vm";

const webRoot = resolve(process.cwd(), "..");

function source(...segments: string[]) {
  return readFileSync(join(webRoot, ...segments), "utf8");
}

const STATIC_APP_SCRIPTS = [
  ["admin", "admin.js"],
  ["admin", "admin-acquisition.js"],
  ["subscriber", "app.js"],
  ["subscriber", "presentation.js"],
  ["subscriber", "locale-es.js"],
  ["landing", "marketing.js"],
  ["landing", "newsletter.js"],
];

test("static app scripts stay syntactically valid JavaScript", () => {
  for (const [app, file] of STATIC_APP_SCRIPTS) {
    const path = join(webRoot, app, file);
    execFileSync(process.execPath, ["--check", path], { stdio: "pipe" });
  }
});

function catalogKeys(block: string) {
  const keys: string[] = [];
  for (const match of block.matchAll(/^ +'([a-zA-Z0-9_.-]+)':/gm)) {
    keys.push(match[1]!);
  }
  return keys;
}

test("subscriber Spanish catalog translates every English key exactly once", () => {
  const presentation = source("subscriber", "presentation.js");
  const spanish = source("subscriber", "locale-es.js");

  const englishBlock = presentation.slice(
    presentation.indexOf("const COPY = Object.freeze({"),
    presentation.indexOf("const SPANISH_COPY"),
  );
  const spanishBlock = spanish.slice(
    spanish.indexOf("root.AXIGNAL_ES_COPY = Object.freeze({"),
    spanish.indexOf("})"),
  );

  const englishKeys = catalogKeys(englishBlock);
  const spanishKeys = catalogKeys(spanishBlock);
  assert.ok(englishKeys.length > 100, "english catalog unexpectedly small");

  const duplicatedEnglish = englishKeys.filter(
    (key, index) => englishKeys.indexOf(key) !== index,
  );
  assert.deepEqual(duplicatedEnglish, [], "duplicate keys inside the en catalog");
  const duplicatedSpanish = spanishKeys.filter(
    (key, index) => spanishKeys.indexOf(key) !== index,
  );
  assert.deepEqual(duplicatedSpanish, [], "duplicate keys inside the es catalog");

  assert.deepEqual(
    [...new Set(spanishKeys)].sort(),
    [...new Set(englishKeys)].sort(),
    "es catalog must translate exactly the en catalog key set",
  );
});

test("subscriber presentation resolves both locales after script evaluation", () => {
  const sandbox: Record<string, unknown> = {};
  runInNewContext(
    `${source("subscriber", "locale-es.js")}\n${source("subscriber", "presentation.js")}`,
    sandbox,
  );
  const presentation = sandbox.AXIGNAL_PRESENTATION as
    | { supportedLocales: string[] }
    | undefined;
  assert.ok(presentation, "AXIGNAL_PRESENTATION must attach after both scripts load");
  assert.deepEqual([...presentation.supportedLocales].sort(), ["en", "es"]);
});

test("landing chapter navigation cannot crash before storyboard data resolves", () => {
  const landing = source("landing", "index.html");
  assert.match(
    landing,
    /async function goTo\(target,dir=1\)\{\s*if\(!data\.length\)return;/,
    "goTo must bail out until storyboard data has loaded",
  );
  assert.match(
    landing,
    /Number\.isFinite\(chapterParam\)/,
    "the ?c= query parameter must be validated before clamping",
  );
});

test("subscriber context search binds exactly one input listener", () => {
  const app = source("subscriber", "app.js");
  const configureStart = app.indexOf("function configureUxLab()");
  const configureEnd = app.indexOf("function ", configureStart + 1);
  const configureBody = app.slice(configureStart, configureEnd);
  assert.doesNotMatch(
    configureBody,
    /addEventListener\('input'/,
    "configureUxLab runs per projection load; it must not attach input listeners",
  );
  const bindStart = app.indexOf("function bindInteractions()");
  const bindEnd = app.indexOf("function ", bindStart + 1);
  const bindBody = app.slice(bindStart, bindEnd);
  assert.match(
    bindBody,
    /\$\('#lab-context-search'\)\.addEventListener\('input'/,
    "the context search listener must live in the one-time bindInteractions pass",
  );
});
