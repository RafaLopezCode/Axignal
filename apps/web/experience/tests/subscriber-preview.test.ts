import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const src = (path: string) => readFileSync(resolve(process.cwd(), path), "utf8");

test("the subscriber preview is the account's component over the synthetic snapshot, never served in production", () => {
  const page = src("app/preview/subscriber/page.tsx");
  assert.match(page, /if \(process\.env\.NODE_ENV === "production"\) notFound\(\);/);
  assert.match(page, /<SubscriberPortfolioExperience source="synthetic" \/>/);
  assert.match(page, /robots: \{ index: false, follow: false \}/);
  assert.doesNotMatch(page, /fetch\(|\/api\//);
});
