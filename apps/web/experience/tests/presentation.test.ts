import test from "node:test";
import assert from "node:assert/strict";
import { monthlyReferenceCents } from "../lib/presentation";
import { locales, isLocale } from "../lib/languages";
import { translate } from "../lib/copy-catalog";
import { makeContext, dateLabel } from "../lib/projection";
import { POST } from "../app/api/axent/route";

test("reference pricing uses exact cents and rejects invalid attention allocations", () => {
  for (const [n, cents] of [
    [1, 995],
    [2, 1490],
    [5, 2975],
    [10, 5450],
    [25, 12875],
    [50, 25250],
    [100, 50000],
  ])
    assert.equal(monthlyReferenceCents(n), cents);
  for (const n of [0, -1, 101, 1.2, NaN, Infinity])
    assert.throws(() => monthlyReferenceCents(n), RangeError);
});
test("six supported languages preserve unknown dates and local draft boundaries", () => {
  assert.equal(locales.length, 6);
  assert.equal(isLocale("zz"), false);
  for (const { id } of locales) {
    assert.equal(isLocale(id), true);
    assert.ok(dateLabel(null, id).length);
    assert.ok(
      translate(
        "AXIGNAL · BORRADOR LOCAL · NO ENVIADO",
        "AXIGNAL · LOCAL DRAFT · NOT SENT",
        id,
      ).includes("AXIGNAL"),
    );
  }
  assert.notEqual(dateLabel(null, "de"), dateLabel(null, "en"));
});
test("all six languages can receive a scoped deterministic Axent stream; other languages fail", async () => {
  for (const locale of [...locales.map((l) => l.id), "zz"]) {
    const request = new Request("http://127.0.0.1:3810/api/axent", {
      method: "POST",
      headers: {
        origin: "http://127.0.0.1:3810",
        host: "127.0.0.1:3810",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        locale,
        context: makeContext(),
        messages: [
          { role: "user", parts: [{ type: "text", text: "context" }] },
        ],
      }),
    });
    const response = await POST(request);
    assert.equal(response.status, locale === "zz" ? 400 : 200);
    if (locale !== "zz") {
      const text = await response.text();
      assert.ok(text.includes("compose-context"));
      assert.ok(text.includes("FIXTURE") === false);
      assert.equal(response.headers.get("set-cookie"), null);
      assert.equal(response.headers.get("cache-control"), "no-store");
    }
  }
});
