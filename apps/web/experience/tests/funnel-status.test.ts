import { test } from "node:test";
import assert from "node:assert/strict";
import { fetchMeasurementAuthority } from "../lib/funnel-events";

test("only explicit authority for the current model enables measurement", async () => {
  for (const [payload, expected] of [
    [{ enabled: true, model: "OBSERVED_TOUCH_V1" }, "ENABLED"],
    [{ enabled: false, model: "OBSERVED_TOUCH_V1" }, "DISABLED"],
    [{ enabled: true, model: "other" }, "UNAVAILABLE"],
    [{ enabled: "true", model: "OBSERVED_TOUCH_V1" }, "UNAVAILABLE"],
    [null, "UNAVAILABLE"],
  ] as const) {
    const request = (async () => Response.json(payload)) as typeof fetch;
    assert.equal(await fetchMeasurementAuthority(request), expected);
  }
});
test("an error response releases its unread body and stays unavailable", async () => {
  let signal: AbortSignal | undefined;
  const request = (async (_url: unknown, init?: RequestInit) => {
    signal = init?.signal ?? undefined;
    return new Response(new ReadableStream({ start() {} }), { status: 503 });
  }) as typeof fetch;
  assert.equal(await fetchMeasurementAuthority(request), "UNAVAILABLE");
  assert.equal(signal?.aborted, true);
});
test("deadline bounds even a transport that ignores cancellation", async () => {
  let signal: AbortSignal | undefined;
  const request = ((_url: unknown, init?: RequestInit) => {
    signal = init?.signal ?? undefined;
    return new Promise<Response>(() => {});
  }) as typeof fetch;
  assert.equal(await fetchMeasurementAuthority(request, 5), "UNAVAILABLE");
  assert.equal(signal?.aborted, true);
});
test("deadline also bounds a stalled JSON body", async () => {
  const request = (async () =>
    new Response(new ReadableStream({ start() {} }), {
      headers: { "Content-Type": "application/json" },
    })) as typeof fetch;
  assert.equal(await fetchMeasurementAuthority(request, 5), "UNAVAILABLE");
});
