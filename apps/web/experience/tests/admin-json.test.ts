import test from "node:test";
import assert from "node:assert/strict";
import { AdminBodyLimitError, ADMIN_RESPONSE_BYTE_LIMIT, readAdminText, readAdminRequestJson, readAdminResponseJson } from "../lib/admin-json";

const encoder = new TextEncoder();
function streamed(parts: Uint8Array[], cancellationFails = false) {
  let reads = 0, cancelled = 0;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (reads < parts.length) controller.enqueue(parts[reads++]);
      else controller.close();
    },
    cancel() { cancelled++; if (cancellationFails) throw new Error("private cleanup detail"); },
  }, { highWaterMark: 0 });
  return { stream, reads: () => reads, cancelled: () => cancelled };
}

test("valid UTF-8 split across chunks is lossless, including at the exact byte limit", async () => {
  const bytes = encoder.encode('{"name":"acción 🌍"}');
  for (let split = 1; split < bytes.length; split++) {
    const source = streamed([bytes.slice(0, split), bytes.slice(split)]);
    const request = new Request("http://localhost/test", { method: "POST", body: source.stream, duplex: "half" } as RequestInit);
    assert.deepEqual(await readAdminRequestJson(request, bytes.length), { name: "acción 🌍" });
    assert.equal(source.stream.locked, false);
    assert.equal(source.cancelled(), 0);
  }
});

test("byte limit stops consumption before later chunks and releases its lock", async () => {
  const source = streamed([encoder.encode("1234"), encoder.encode("5"), encoder.encode("must not be read")]);
  await assert.rejects(readAdminText(source.stream, 4), AdminBodyLimitError);
  assert.equal(source.reads(), 2);
  assert.equal(source.cancelled(), 1);
  assert.equal(source.stream.locked, false);
});

test("Unicode cannot pass a byte limit using its shorter JavaScript string length", async () => {
  const body = '{"value":"éééé"}';
  const request = new Request("http://localhost/test", { method: "POST", body });
  await assert.rejects(readAdminRequestJson(request, body.length), AdminBodyLimitError);
});

test("failed cancellation cannot mask an oversize rejection or expose its error text", async () => {
  const source = streamed([encoder.encode("too large")], true);
  await assert.rejects(readAdminText(source.stream, 1), error => error instanceof AdminBodyLimitError && !error.message.includes("private"));
  assert.equal(source.stream.locked, false);
});

test("a cancellation that never settles cannot stall an already known limit rejection", { timeout: 1000 }, async () => {
  let cancelled = false;
  const source = new ReadableStream<Uint8Array>({
    pull(controller) { controller.enqueue(encoder.encode("too large")); },
    cancel() { cancelled = true; return new Promise(() => {}); },
  }, { highWaterMark: 0 });
  await assert.rejects(readAdminText(source, 1), AdminBodyLimitError);
  assert.equal(cancelled, true);
  assert.equal(source.locked, false);
});

test("stream failure releases the reader and preserves the transport error", async () => {
  const failure = new Error("transport failure");
  const source = new ReadableStream<Uint8Array>({ pull() { throw failure; } });
  await assert.rejects(readAdminText(source, 1024), error => error === failure);
  assert.equal(source.locked, false);
});

test("invalid or truncated UTF-8 is rejected, never silently repaired", async () => {
  for (const bytes of [new Uint8Array([0x22, 0xc3, 0x22]), new Uint8Array([0xf0, 0x9f])]) {
    const source = streamed([bytes]);
    await assert.rejects(readAdminText(source.stream, 1024), SyntaxError);
    assert.equal(source.stream.locked, false);
  }
});

test("empty or malformed input stays a request syntax error", async () => {
  for (const value of ["", "{", "\uFEFF{}"]) {
    const request = new Request("http://localhost/test", { method: "POST", body: value });
    await assert.rejects(readAdminRequestJson(request, 1024), SyntaxError);
  }
  await assert.rejects(readAdminText(null, 1024), SyntaxError);
});

test("upstream syntax, bytes and stream failures never masquerade as request errors", async () => {
  const responses = [new Response("{"), new Response("x".repeat(ADMIN_RESPONSE_BYTE_LIMIT + 1)), new Response(new ReadableStream({ pull() { throw new Error("private-upstream-detail"); } }))];
  for (const response of responses) {
    await assert.rejects(readAdminResponseJson(response), error => error instanceof Error && !(error instanceof SyntaxError) && !(error instanceof AdminBodyLimitError) && !error.message.includes("private"));
    assert.equal(response.body?.locked, false);
  }
});

test("a misleading Content-Length never bypasses the actual upstream byte cap", async () => {
  const source = streamed([new Uint8Array(ADMIN_RESPONSE_BYTE_LIMIT), new Uint8Array(1), encoder.encode("not read")]);
  await assert.rejects(readAdminResponseJson(new Response(source.stream, { headers: { "Content-Length": "1" } })));
  assert.equal(source.cancelled(), 1);
  assert.equal(source.reads(), 2);
});

test("invalid limit configuration fails before consuming the body", async () => {
  for (const limit of [0, -1, 1.5, Infinity, NaN]) {
    const source = streamed([encoder.encode("ok")]);
    await assert.rejects(readAdminText(source.stream, limit), RangeError);
    assert.equal(source.reads(), 0);
    assert.equal(source.stream.locked, false);
  }
});
