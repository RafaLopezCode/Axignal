import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { resolveRuntimeOrigin } from "../lib/customer-zero-server";

test("runtime origin remains loopback by default and admits only the Compose runtime peer when containerized", () => {
  assert.equal(resolveRuntimeOrigin("http://127.0.0.1:8765/").host, "127.0.0.1:8765");
  assert.equal(resolveRuntimeOrigin("http://localhost:18181/").host, "localhost:18181");
  assert.throws(() => resolveRuntimeOrigin("http://runtime:18181/", false), /RUNTIME_ORIGIN_REJECTED/);
  assert.equal(resolveRuntimeOrigin("http://runtime:18181/", true).host, "runtime:18181");
  assert.throws(() => resolveRuntimeOrigin("http://runtime:9999/", true), /RUNTIME_ORIGIN_REJECTED/);
  assert.throws(() => resolveRuntimeOrigin("http://example.com:18181/", true), /RUNTIME_ORIGIN_REJECTED/);
  assert.throws(() => resolveRuntimeOrigin("https://runtime:18181/", true), /RUNTIME_ORIGIN_REJECTED/);
  assert.throws(() => resolveRuntimeOrigin("http://runtime:18181/private", true), /RUNTIME_ORIGIN_REJECTED/);
});

test("production experience is loopback-only and shares the isolated AXIGNAL Compose network", () => {
  const compose = readFileSync(resolve(process.cwd(), "../../../deploy/production/compose.yml"), "utf8");
  assert.match(compose, /container_name: axignal-prod-experience/);
  assert.match(compose, /127\.0\.0\.1:18182:3810/);
  assert.match(compose, /AXIGNAL_RUNTIME_ORIGIN: http:\/\/runtime:18181/);
  assert.match(compose, /AXIGNAL_EXPERIENCE_ORIGIN: http:\/\/127\.0\.0\.1:18182/);
  assert.doesNotMatch(compose, /0\.0\.0\.0:18182:3810/);
});
