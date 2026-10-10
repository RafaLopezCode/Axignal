import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { exampleInsights, EXAMPLE_MOMENTS } from "../lib/landing-observatory";

const src = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

test("public /panorama renders the actual Observatory reading surface, not retired Panorama", () => {
  const page = src("app/panorama/page.tsx");
  const demo = src("components/example-observatory.tsx");
  const subscriber = src("components/subscriber-portfolio.tsx");
  const live = src("components/observatory.tsx");
  assert.match(page, /<ExampleObservatory\s*\/>/);
  assert.doesNotMatch(page, /<Panorama\b/);
  assert.doesNotMatch(demo, /useSearchParams/); // Static HTML must contain the example before hydration.
  assert.match(subscriber, /import \{ Observatory \} from "\.\/observatory"/);
  assert.match(live, /data-product-surface="living-observatory"/);
  assert.match(demo, /import \{ InsightBody, SummaryView \} from "\.\/observatory"/);
  assert.match(demo, /data-product-surface="living-observatory"/);
  assert.match(demo, /data-example="fictional"/);
  assert.doesNotMatch(demo, /fetch\(|\/api\/admin|\/api\/subscriber|localStorage|sessionStorage/);
  assert.match(demo, /href="\/signup"/);
});

test("fictional example is temporal, epistemically labeled and has no invented external evidence URLs", () => {
  const tr = (value: { es: string; en: string }) => value.es;
  const old = exampleInsights(EXAMPLE_MOMENTS[0], tr);
  const newest = exampleInsights(EXAMPLE_MOMENTS.at(-1)!, tr);
  assert.ok(newest.length >= old.length);
  assert.ok(newest.length > 0);
  for (const insight of newest) {
    assert.ok(["POTENTIAL", "UNKNOWN", "OBSERVED", "DECLARED"].includes(insight.nature));
    assert.ok(insight.sources.every(source => source.url === null));
  }
});

test("production release entrypoint cannot silently drop configured subscriber profile", () => {
  const script = src("../../../deploy/production/deploy-axignal.sh");
  assert.match(script, /compose\.subscriber\.override\.yml/);
  assert.match(script, /refusing to downgrade to base-only Compose/i);
  assert.match(script, /AXIGNAL_DEPLOY_PROFILE/);
  assert.match(script, /config --quiet/);
  assert.match(script, /--no-build runtime experience landing/);
  assert.match(script, /verify-product-surface\.sh/);
  const smoke = src("../../../deploy/production/verify-product-surface.sh");
  assert.match(smoke, /expect \/panorama 200/);
  assert.match(smoke, /expect \/account 200/);
  assert.match(smoke, /Google sign-in available/);
  assert.match(smoke, /expect \/api\/subscriber\/portfolio 401/);
  assert.match(smoke, /expect \/admin\/customer-zero 404/);
  const overlay = src("../../../deploy/production/compose.subscriber.override.yml");
  assert.match(overlay, /AXIGNAL_EXPERIENCE_ORIGIN: https:\/\/axignal\.com/);
  assert.match(overlay, /subscriber-edge-nginx.conf/);
  const edge = src("../../../deploy/production/subscriber-edge-nginx.conf");
  assert.match(edge, /location \^~ \/api\/subscriber\//);
  assert.doesNotMatch(edge, /location \^~ \/api\/admin\//);
});
