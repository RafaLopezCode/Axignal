import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { exampleInsights, EXAMPLE_MOMENTS } from "../lib/landing-observatory";

const src = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

test("public /demo is the subscriber Observatory over a fictional snapshot, with no account surface", () => {
  const page = src("app/demo/page.tsx");
  const subscriber = src("components/subscriber-portfolio.tsx");
  const live = src("components/observatory.tsx");
  const snapshot = src("lib/demo/synthetic-source.ts");
  assert.match(page, /<SubscriberPortfolioExperience source="synthetic"/);
  assert.doesNotMatch(page, /<Panorama\b/);
  assert.doesNotMatch(page, /example-observatory/);
  assert.match(subscriber, /source = "live"/);
  assert.match(subscriber, /import \{ Observatory \} from "\.\/observatory"/);
  assert.match(live, /data-product-surface="living-observatory"/);
  assert.match(live, /canAct: boolean/);
  // The demo reads only the snapshot: no request, storage or private surface in its source.
  assert.doesNotMatch(snapshot, /fetch\(|\/api\/|localStorage|sessionStorage|\/admin/);
  assert.match(subscriber, /if \(!live\) return syntheticOutput\(focusId, demoLocale \?\? "es"\);/);
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
  assert.match(smoke, /expect \/demo 200/);
  assert.match(smoke, /expect \/panorama 308/);
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
