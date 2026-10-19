import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import { translate } from "../lib/copy-catalog";
import { translateLoaded } from "../lib/client-copy-catalog";
import { dateLabel } from "../lib/projection";
import { locales } from "../lib/languages";

const source: Record<string, string[]> = JSON.parse(
  fs.readFileSync(new URL("../lib/translations.json", import.meta.url), "utf8"),
);
test("every delivery catalog is an exact canonical column, without missing or additional keys", () => {
  for (const [column, locale] of ["de", "pt", "fr", "it"].entries()) {
    const delivered = JSON.parse(
      fs.readFileSync(
        new URL(`../lib/translation-delivery/${locale}.json`, import.meta.url),
        "utf8",
      ),
    );
    assert.deepEqual(
      delivered,
      Object.fromEntries(
        Object.entries(source).map(([key, values]) => [key, values[column]]),
      ),
      `Regenerate with node tools/split-translation-catalog.mjs (${locale})`,
    );
    for (const key of Object.keys(source)) {
      assert.equal(
        translateLoaded("texto", key, locale as "de", delivered),
        translate("texto", key, locale as "de"),
      );
    }
  }
  assert.equal(
    translateLoaded("AXENT observa", "AXENT observes", "es"),
    "Axent observa",
  );
  assert.equal(
    translateLoaded("AXENT observa", "AXENT observes", "en"),
    "Axent observes",
  );
});
test("unsupported dates retain their exact canonical six-language meaning", () => {
  for (const { id } of locales) {
    assert.equal(
      dateLabel(null, id),
      translate("Sin fecha acreditada", "No supported date", id),
    );
    assert.equal(dateLabel("invalid", id), dateLabel(null, id));
  }
});

test("font delivery files have the declared checksum, retain their source and reduce transfer", async () => {
  const { createHash } = await import("node:crypto");
  const manifest = JSON.parse(
    fs.readFileSync(
      new URL("../lib/landing-lab-fonts.json", import.meta.url),
      "utf8",
    ),
  );
  let before = 0,
    after = 0;
  for (const font of manifest.fonts) {
    const data = fs.readFileSync(
      new URL("../public" + font.url, import.meta.url),
    );
    assert.equal(data.length, font.bytes);
    assert.equal(createHash("sha256").update(data).digest("hex"), font.sha256);
    assert.equal(
      fs.statSync(new URL("../public" + font.source, import.meta.url)).size,
      font.sourceBytes,
    );
    before += font.sourceBytes;
    after += font.bytes;
  }
  assert.ok(
    after < before * 0.65,
    "The four official faces should save at least 35% together",
  );
});
