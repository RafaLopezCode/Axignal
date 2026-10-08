import { test } from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_LOCALE,
  localeFromLanguageTags,
  resolveInitialLocale,
} from "../lib/languages";

test("English is the international fallback locale", () => {
  assert.equal(DEFAULT_LOCALE, "en");
  assert.equal(resolveInitialLocale({}), "en");
  assert.equal(resolveInitialLocale({ browserLanguages: ["nl-NL"] }), "en");
});

test("browser language selects a supported locale by preference order", () => {
  assert.equal(localeFromLanguageTags(["en-GB"]), "en");
  assert.equal(localeFromLanguageTags(["en-US"]), "en");
  assert.equal(localeFromLanguageTags(["es-ES"]), "es");
  assert.equal(localeFromLanguageTags(["fr-FR", "en-US"]), "fr");
  assert.equal(localeFromLanguageTags(["nl-NL", "de-DE", "en-US"]), "de");
  assert.equal(localeFromLanguageTags(["pt-BR"]), "pt");
});

test("explicit route wins over saved preference and browser language", () => {
  assert.equal(
    resolveInitialLocale({
      routeLocale: "fr",
      savedLocale: "es",
      browserLanguages: ["en-GB"],
    }),
    "fr",
  );
});

test("saved preference wins over browser language", () => {
  assert.equal(
    resolveInitialLocale({
      savedLocale: "it",
      browserLanguages: ["en-US"],
    }),
    "it",
  );
});
