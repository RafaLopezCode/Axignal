import test from "node:test";
import assert from "node:assert/strict";
import LoginPage from "../app/login/page";

test("failed callback is visible on first render and still requires explicit registration", async () => {
  const page = await LoginPage({ searchParams: Promise.resolve({ access: "failed" }) });
  assert.equal(page.props.callbackFailed, true);
  assert.equal(page.props.intent, "login");
});

test("ordinary, unrelated and duplicate query values do not report an authentication failure", async () => {
  for (const query of [{}, { access: "success" }, { access: ["failed", "failed"] }]) {
    const page = await LoginPage({ searchParams: Promise.resolve(query) });
    assert.equal(page.props.callbackFailed, false);
    assert.equal(page.props.intent, "login");
  }
});
