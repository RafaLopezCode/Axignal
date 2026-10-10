import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import config from "../next.config";

const source = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

test("public demo has one canonical route; old deep links redirect permanently", async () => {
  const redirects = await config.redirects?.();
  assert.ok(redirects);
  assert.ok(redirects.some(rule =>
    rule.source === "/panorama" && rule.destination === "/demo" && rule.permanent === true));
  assert.match(source("app/demo/page.tsx"), /<DemoObservatory\s*\/>/);
  assert.match(source("components/landing.tsx"), /EXAMPLE_HREF = "\/demo"/);
  assert.match(source("../../../deploy/production/subscriber-edge-nginx.conf"), /location = \/demo \{/);
  assert.match(source("../../../deploy/production/verify-product-surface.sh"), /expect \/panorama 308/);
});

test("Admin home opens Customer Zero without exposing its operator API", async () => {
  const redirects = await config.redirects?.();
  assert.ok(redirects?.some(rule =>
    rule.source === "/admin/customer-zero" && rule.destination === "/admin" && rule.permanent === true));
  const admin = source("components/admin.tsx");
  assert.match(admin, /initialDomain = CUSTOMER_ZERO/);
  assert.match(admin, /const CUSTOMER_ZERO = "customer-zero"/);
  // The home is the address /admin itself; the other domains hang from it as /admin#domain. No address names "customer-zero".
  assert.match(admin, /window\.history\.pushState\(null, "", id === CUSTOMER_ZERO \? "\/admin" : "\/admin#" \+ id\)/);
  const edge = source("../../../deploy/production/subscriber-edge-nginx.conf");
  assert.doesNotMatch(edge, /location\s+(?:=|\^~)\s*\/admin\b/);
  const publicEdge = source("../../../deploy/production/traefik/axignal-public-seo.yml");
  assert.doesNotMatch(publicEdge, /Path(?:Prefix)?\(`\/admin/);
});
