import test from "node:test";
import assert from "node:assert/strict";
import {
  validateContext,
  validatePlan,
  denyAdminMutation,
} from "../lib/governance";
import { makeContext, project } from "../lib/projection";
const context = makeContext();
const valid = {
  version: 1,
  revision: context.revision,
  items: [{ component: "signal", ref: "renovation", priority: "primary" }],
};
test("known scoped plan passes", () =>
  assert.equal(validatePlan(valid, context).success, true));
test("arbitrary component, content and unknown references fail closed", () => {
  for (const item of [
    { component: "html", ref: "renovation", priority: "primary" },
    { component: "signal", ref: "fake", priority: "primary" },
    {
      component: "signal",
      ref: "renovation",
      priority: "primary",
      title: "Invented",
    },
  ])
    assert.equal(
      validatePlan({ ...valid, items: [item] }, context).success,
      false,
    );
});
test("foreign organization reference and stale revision fail", () => {
  assert.equal(
    validatePlan(
      {
        ...valid,
        items: [
          { component: "signal", ref: "circular-pilot", priority: "primary" },
        ],
      },
      context,
    ).success,
    false,
  );
  assert.equal(
    validatePlan({ ...valid, revision: "stale" }, context).success,
    false,
  );
});
test("future evidence and signal are not visible historically", () => {
  const old = makeContext("norte", "markets", "2026-07-01");
  assert.equal(
    project(old).signals.some((s) => s.id === "renovation"),
    false,
  );
  assert.equal(
    validatePlan({ ...valid, revision: old.revision }, old).success,
    false,
  );
  assert.equal(
    project(old).evidence.some((e) => e.id === "surface"),
    false,
  );
});
test("duplicate refs, zero and >3 items reject", () => {
  for (const items of [
    [],
    [...valid.items, ...valid.items],
    Array.from({ length: 4 }, () => valid.items[0]),
  ])
    assert.equal(validatePlan({ ...valid, items }, context).success, false);
});
test("unknown is not false and potential remains potential", () => {
  const p = project(context);
  assert.equal(
    p.signals.find((s) => s.id === "reputation-gap")?.epistemic,
    "UNKNOWN",
  );
  assert.equal(
    p.signals.find((s) => s.id === "renovation")?.epistemic,
    "POTENTIAL",
  );
});
test("context validates organization/date/signal association and revision", () => {
  assert.equal(validateContext(context).success, true);
  for (const value of [
    { ...context, organizationId: "other" },
    { ...context, asOf: "2027-01-01" },
    { ...context, signalId: "circular-pilot" },
    { ...context, revision: "wrong" },
    { ...context, tenant: "injected" },
  ])
    assert.equal(validateContext(value).success, false);
});
test("browser role cannot authorize a private operational write", () => {
  assert.equal(denyAdminMutation().status, 403);
  assert.equal(denyAdminMutation().code, "AUTHORITY_REQUIRED");
});

test("local browser origin follows public Host and rejects foreign or mismatched origins", async () => {
  const { validateBrowserOrigin } = await import("../lib/governance");
  assert.equal(
    validateBrowserOrigin("http://127.0.0.1:3810", "127.0.0.1:3810"),
    true,
  );
  assert.equal(
    validateBrowserOrigin("http://localhost:3810", "localhost:3810"),
    true,
  );
  assert.equal(
    validateBrowserOrigin("https://external.example", "127.0.0.1:3810"),
    false,
  );
  assert.equal(
    validateBrowserOrigin("http://127.0.0.1:3810", "localhost:3810"),
    false,
  );
  assert.equal(
    validateBrowserOrigin("http://127.0.0.1:4000", "127.0.0.1:4000"),
    false,
  );
});
