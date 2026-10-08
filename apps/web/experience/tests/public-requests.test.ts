import test, { type TestContext } from "node:test";
import assert from "node:assert/strict";
import {
  publicChannelStatus,
  publicChannelSubmit,
  publicWeeklyBriefStatus,
  publicWeeklyBriefSubmit,
} from "../lib/public-requests-server";
import {
  publicRequestError,
  publicRequestSchema,
  rightsCategories,
} from "../lib/public-requests";

function setEnv(t: TestContext, key: string, value: string) {
  const previous = process.env[key];
  process.env[key] = value;
  t.after(() => {
    if (previous === undefined) delete process.env[key];
    else process.env[key] = previous;
  });
}
const payload = {
  name: "Test Visitor",
  email: "visitor@example.invalid",
  message: "Synthetic functional request for testing.",
  subject: "Product question",
  category: "contact",
  locale: "es",
  noticeVersion: "contact-request-notice-v1",
  requestRef: "0123456789abcdef0123456789abcdef",
};
function request(value = payload, origin = "http://127.0.0.1:3810") {
  return new Request("http://127.0.0.1:3810/api/contact", {
    method: "POST",
    headers: {
      Origin: origin,
      Host: "127.0.0.1:3810",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(value),
  });
}
test("status relays actual availability and never invents a public email", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  t.mock.method(globalThis, "fetch", async () =>
    Response.json({
      enabled: false,
      controller: "AXIGNAL",
      country: "Spain",
      publicEmail: null,
    }),
  );
  const response = await publicChannelStatus("contact");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    enabled: false,
    controller: "AXIGNAL",
    country: "Spain",
    publicEmail: null,
  });
  assert.equal(response.headers.get("cache-control"), "no-store");
});
test("unknown channel status remains unavailable, distinct from a verified disabled status", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  t.mock.method(globalThis, "fetch", async () =>
    Response.json({
      enabled: false,
      controller: "Unknown",
      country: "Spain",
      publicEmail: null,
    }),
  );
  const response = await publicChannelStatus("gdpr");
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), {
    status: "rejected",
    reason: "REQUEST_UNAVAILABLE",
  });
});
test("cross-origin requests and wrong notice versions do not reach the runtime", async (t) => {
  const fetch = t.mock.method(globalThis, "fetch", async () => {
    throw new Error("must not fetch");
  });
  assert.equal(
    (
      await publicChannelSubmit(
        request(payload, "https://other.invalid"),
        "contact",
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await publicChannelSubmit(
        request({ ...payload, noticeVersion: "privacy-rights-notice-v1" }),
        "contact",
      )
    ).status,
    400,
  );
  assert.equal(fetch.mock.calls.length, 0);
});
test("submission preserves notice, category and request reference; receipt carries no delivery assertion", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  setEnv(t, "AXIGNAL_EXPERIENCE_ORIGIN", "http://127.0.0.1:3810");
  t.mock.method(
    globalThis,
    "fetch",
    async (url: string | URL | Request, options?: RequestInit) => {
      assert.equal(String(url), "http://127.0.0.1:18999/api/contact");
      assert.deepEqual(JSON.parse(String(options?.body)), payload);
      return Response.json(
        { status: "received", requestId: "a".repeat(32) },
        { status: 202 },
      );
    },
  );
  assert.deepEqual(
    await (await publicChannelSubmit(request(), "contact")).json(),
    { status: "received", requestId: "a".repeat(32) },
  );
});
test("all canonical GDPR categories use the privacy endpoint, never the contact endpoint", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  t.mock.method(
    globalThis,
    "fetch",
    async (url: string | URL | Request, options?: RequestInit) => {
      assert.equal(String(url), "http://127.0.0.1:18999/api/privacy/request");
      const body = JSON.parse(String(options?.body));
      assert.equal(body.noticeVersion, "privacy-rights-notice-v1");
      assert.ok(rightsCategories.includes(body.category));
      return Response.json(
        { status: "received", requestId: "b".repeat(32) },
        { status: 202 },
      );
    },
  );
  for (const category of rightsCategories)
    assert.equal(
      (
        await publicChannelSubmit(
          request({
            ...payload,
            category,
            noticeVersion: "privacy-rights-notice-v1",
          }),
          "gdpr",
        )
      ).status,
      202,
    );
});
test("runtime rejections stay rejections and infrastructure messages are human-readable", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  t.mock.method(globalThis, "fetch", async () =>
    Response.json(
      { status: "rejected", reason: "RATE_LIMITED" },
      { status: 429 },
    ),
  );
  const response = await publicChannelSubmit(request(), "contact");
  assert.equal(response.status, 429);
  assert.deepEqual(await response.json(), {
    status: "rejected",
    reason: "RATE_LIMITED",
  });
  for (const reason of [
    "RATE_LIMITED",
    "INVALID_REQUEST",
    "INVALID_EMAIL",
    "INVALID_MESSAGE",
    "INVALID_CATEGORY",
    "INVALID_LOCALE",
    "REQUEST_REF_CONFLICT",
    "CHANNEL_UNAVAILABLE",
    "REQUEST_UNAVAILABLE",
    "SMTP_SECRET_EXCEPTION",
  ]) {
    for (const message of publicRequestError(reason))
      assert.equal(message.includes(reason), false);
  }
});
test("public requests reject extra authority, malformed identifiers and unknown rights", () => {
  for (const extra of [
    { canonical: true },
    { category: "automated" },
    { requestRef: "short" },
    { noticeVersion: "" },
    { message: "short" },
  ])
    assert.equal(
      publicRequestSchema.safeParse({ ...payload, ...extra }).success,
      false,
    );
});
test("remote runtime URLs are refused before forwarding private request data", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "https://remote.invalid");
  const fetch = t.mock.method(globalThis, "fetch", async () => {
    throw new Error("must not fetch");
  });
  assert.equal((await publicChannelSubmit(request(), "contact")).status, 503);
  assert.equal(fetch.mock.calls.length, 0);
});
test("weekly brief stays disabled when the owning runtime disables it", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  t.mock.method(globalThis, "fetch", async () =>
    Response.json({ enabled: false }),
  );
  assert.deepEqual(await (await publicWeeklyBriefStatus()).json(), {
    enabled: false,
  });
});
test("brief processing notice is mandatory; optional newsletter consent has its own version", async (t) => {
  setEnv(t, "AXIGNAL_RUNTIME_ORIGIN", "http://127.0.0.1:18999");
  const base = {
    companyName: "Synthetic Company",
    companyDomain: "company.example.invalid",
    professionalEmail: "brief@example.invalid",
    purpose: "Synthetic functional brief request only.",
    requestProcessingAcknowledged: true,
    requestNoticeVersion: "weekly-brief-request-v1",
    newsletterConsent: false,
  };
  const make = (value: unknown) =>
    new Request("http://127.0.0.1:3810/api/weekly-brief/requests", {
      method: "POST",
      headers: {
        Origin: "http://127.0.0.1:3810",
        Host: "127.0.0.1:3810",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(value),
    });
  const fetch = t.mock.method(
    globalThis,
    "fetch",
    async (_url: string | URL | Request, options?: RequestInit) => {
      const body = JSON.parse(String(options?.body));
      if (body.newsletterConsent)
        assert.equal(
          body.newsletterNoticeVersion,
          "weekly-newsletter-consent-v1",
        );
      else assert.equal(body.newsletterNoticeVersion, undefined);
      return Response.json(
        {
          status: "received",
          requestId: "brief:" + "c".repeat(24),
          reviewState: "NEEDS_REVIEW",
        },
        { status: 202 },
      );
    },
  );
  for (const value of [
    { ...base, requestProcessingAcknowledged: false },
    { ...base, requestNoticeVersion: "wrong" },
    { ...base, newsletterConsent: true },
  ])
    assert.equal((await publicWeeklyBriefSubmit(make(value))).status, 400);
  assert.equal(fetch.mock.calls.length, 0);
  assert.equal((await publicWeeklyBriefSubmit(make(base))).status, 202);
  assert.equal(
    (
      await publicWeeklyBriefSubmit(
        make({
          ...base,
          newsletterConsent: true,
          newsletterNoticeVersion: "weekly-newsletter-consent-v1",
        }),
      )
    ).status,
    202,
  );
});
