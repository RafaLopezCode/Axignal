import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import { metadata } from "../app/layout";
import { siteIcons } from "../lib/site-icons";
import robots from "../app/robots";

test("the actual root metadata exposes a square search favicon and approved browser fallbacks", () => {
  assert.equal(metadata.icons, siteIcons);
  const png = siteIcons.icon.find(icon => icon.type === "image/png");
  assert.ok(png);
  assert.equal(png.sizes, "96x96");
  const bytes = readFileSync(resolve("public" + png.url));
  assert.equal(bytes.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.equal(bytes.toString("ascii", 12, 16), "IHDR");
  assert.equal(bytes.readUInt32BE(16), 96);
  assert.equal(bytes.readUInt32BE(20), 96);
  assert.ok(siteIcons.icon.some(icon => icon.type === "image/svg+xml" && icon.sizes === "any"));
  assert.ok(siteIcons.icon.some(icon => icon.type === "image/x-icon"));
});

test("declared favicons remain exact approved derivatives and publicly crawlable", () => {
  const manifest = JSON.parse(readFileSync("public/brand/brand-assets.v1.json", "utf8"));
  const policy = robots().rules;
  const rules = Array.isArray(policy) ? policy : [policy];
  const ingress = readFileSync(resolve("../../../deploy/production/traefik/axignal-public-seo.yml"), "utf8");
  assert.ok(ingress.includes("PathPrefix(`/brand/`)"));
  for (const icon of [...siteIcons.icon, ...siteIcons.apple, ...siteIcons.other]) {
    const filename = icon.url.split("/").at(-1);
    assert.ok(filename);
    const entry = manifest.assets.find((asset: { output_file: string }) => asset.output_file === filename);
    assert.ok(entry, `missing official provenance: ${filename}`);
    const bytes = readFileSync(resolve("public" + icon.url));
    assert.equal(createHash("sha256").update(bytes).digest("hex"), entry.output_sha256, filename);
    for (const rule of rules) {
      const disallow = rule.disallow ? (Array.isArray(rule.disallow) ? rule.disallow : [rule.disallow]) : [];
      assert.ok(!disallow.some(prefix => prefix && icon.url.startsWith(prefix)), `blocked favicon: ${icon.url}`);
    }
  }
});
