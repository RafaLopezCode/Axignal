import test from "node:test";
import assert from "node:assert/strict";
import { readWeeklyBriefAvailability } from "../lib/weekly-brief-availability";

test("weekly brief distinguishes explicit pause from unknown availability", async (t) => {
  for (const enabled of [true, false]) {
    const mock = t.mock.method(
      globalThis,
      "fetch",
      async (url: string | URL | Request, options?: RequestInit) => {
        assert.equal(url, "/api/weekly-brief/status");
        assert.equal(options?.cache, "no-store");
        return Response.json({ enabled });
      },
    );
    assert.equal(
      await readWeeklyBriefAvailability(new AbortController().signal),
      enabled,
    );
    mock.mock.restore();
  }
});

test("weekly brief never enables requests from malformed, failed or missing status", async (t) => {
  for (const payload of [
    null,
    {},
    { enabled: "true" },
    { enabled: 1 },
    { enabled: null },
  ]) {
    const mock = t.mock.method(globalThis, "fetch", async () =>
      Response.json(payload),
    );
    assert.equal(
      await readWeeklyBriefAvailability(new AbortController().signal),
      null,
    );
    mock.mock.restore();
  }
  for (const response of [
    new Response("unavailable", { status: 503 }),
    new Response("not JSON"),
  ]) {
    const mock = t.mock.method(globalThis, "fetch", async () => response);
    assert.equal(
      await readWeeklyBriefAvailability(new AbortController().signal),
      null,
    );
    mock.mock.restore();
  }
  t.mock.method(globalThis, "fetch", async () => {
    throw new Error("offline");
  });
  assert.equal(
    await readWeeklyBriefAvailability(new AbortController().signal),
    null,
  );
});

test("weekly brief status reads use the caller's cancellation signal", async (t) => {
  const controller = new AbortController();
  controller.abort();
  t.mock.method(
    globalThis,
    "fetch",
    async (_url: string | URL | Request, options?: RequestInit) => {
      assert.equal(options?.signal, controller.signal);
      options?.signal?.throwIfAborted();
      throw new Error("unreachable");
    },
  );
  assert.equal(await readWeeklyBriefAvailability(controller.signal), null);
});
