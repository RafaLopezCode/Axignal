import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { isWebSubject } from "../lib/identity";

test("a web-anchored subject is never presented as verified by registry (biocultor.com canary)", () => {
  assert.equal(isWebSubject("org:web:064fbf8a"), true);
  assert.equal(isWebSubject("org:id:abc"), false);
  assert.equal(isWebSubject(null), false);
  const source = readFileSync(new URL("../components/observatory.tsx", import.meta.url), "utf8");
  // The registry chip is guarded by the anchored check, which comes first.
  assert.match(source, /anchored \? t\("Identidad anclada a su web", "Identity anchored to its website"\) : identified \? t\("Identidad verificada por registro"/);
});
