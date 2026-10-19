import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import sharp from "sharp";
import delivery from "../lib/marketing-delivery.json";
import labFonts from "../lib/landing-lab-fonts.json";
import surfaceStyles from "../lib/surface-styles.json";
import config from "../next.config";
import { HERO_SRC_SET, INDUSTRY_SRC_SET } from "../lib/marketing-media";

test("responsive art keeps the approved full plate and bounded, correctly hashed variants", async () => {
  const edge = fs.readFileSync(
    path.resolve("../../../deploy/production/traefik/axignal-public-seo.yml"),
    "utf8",
  );
  for (const [name, image] of Object.entries(delivery.images)) {
    const full = fs.readFileSync(path.resolve("public" + image.src));
    const last = image.variants.at(-1)!;
    assert.deepEqual(
      fs.readFileSync(path.resolve("public" + last.url)),
      full,
      name + " full plate unchanged",
    );
    assert.ok(
      image.variants[0].bytes < image.bytes * 0.25,
      name + " mobile bytes reduced",
    );
    for (const v of image.variants) {
      const bytes = fs.readFileSync(path.resolve("public" + v.url));
      const digest = createHash("sha256").update(bytes).digest("hex");
      assert.equal(bytes.length, v.bytes);
      assert.equal(digest, v.sha256);
      assert.ok(v.url.includes(digest.slice(0, 8)));
      const meta = await sharp(bytes).metadata();
      assert.equal(meta.width, v.width);
      assert.ok(
        Math.abs(meta.height! - (v.width * image.height) / image.width) <= 1,
      );
      assert.ok(
        edge.includes("Path(`" + v.url + "`)"),
        v.url + " exact public ingress",
      );
    }
  }
  assert.match(HERO_SRC_SET, /640w.*960w.*1440w.*1931w/);
  assert.match(INDUSTRY_SRC_SET, /640w.*960w.*1440w.*2007w/);
  assert.ok(!edge.includes("PathPrefix(`/marketing`)"));
});

test("WOFF2 delivery preserves the original font assets with a smaller immutable transfer", () => {
  for (const f of delivery.fonts) {
    const data = fs.readFileSync(path.resolve("public" + f.url));
    assert.equal(data.subarray(0, 4).toString(), "wOF2");
    assert.equal(data.length, f.bytes);
    assert.equal(createHash("sha256").update(data).digest("hex"), f.sha256);
  }
  assert.ok(
    delivery.fonts.reduce((s, f) => s + f.bytes, 0) < (164700 + 403648) * 0.41,
  );
  assert.ok(fs.existsSync("public/fonts/manrope.ttf"));
  assert.ok(fs.existsSync("public/fonts/caveat.ttf"));
});

test("year-long cache is limited to content-hashed public assets", async () => {
  const headers = await config.headers!();
  const cached = headers.filter((rule) =>
    rule.headers.some((h) => h.key === "Cache-Control"),
  );
  const expected = [
    ...delivery.fonts.map((asset) => asset.url),
    ...Object.values(delivery.images).flatMap((image) =>
      image.variants.map((asset) => asset.url),
    ),
    ...labFonts.fonts.map((asset) => asset.url),
    surfaceStyles.base.url,
    surfaceStyles.legacy.url,
    surfaceStyles.lab.url,
  ];
  assert.deepEqual(cached.map((rule) => rule.source).sort(), expected.sort());
  for (const rule of cached) {
    assert.match(
      rule.source,
      /^\/(?:marketing|fonts|styles)\/[a-z0-9-]+\.(?:[a-f0-9]{8}|[a-f0-9]{12})\.(?:webp|woff2|css)$/,
    );
    assert.ok(
      rule.headers.some(
        (h) =>
          h.key === "Cache-Control" &&
          h.value === "public, max-age=31536000, immutable",
      ),
    );
  }
});
