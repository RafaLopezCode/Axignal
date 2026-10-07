import test from "node:test";
import assert from "node:assert/strict";
import {
  authStartSchema,
  preparedAuthStart,
  preparedProviders,
  acceptsPublicAuthOrigin,
  localDraftSchema,
  draftText,
} from "../lib/public-contracts";
import { POST } from "../app/api/auth/start/route";
import { GET } from "../app/api/auth/status/route";
import { legalIdentity, publicContactHref } from "../lib/legal";

const request = (
  body: string,
  options: { origin?: string; host?: string; contentType?: string } = {},
) =>
  new Request("http://localhost:3810/api/auth/start", {
    method: "POST",
    headers: {
      host: options.host ?? "127.0.0.1:3810",
      origin: options.origin ?? "http://127.0.0.1:3810",
      "Content-Type": options.contentType ?? "application/json",
    },
    body,
  });
test("sign-in refuses caller-supplied scopes, return URLs, identities and privilege claims", () => {
  for (const extra of [
    { scopes: "responses.write" },
    { returnTo: "https://evil.example" },
    { PrincipalId: "founder" },
    { isAdmin: true },
  ])
    assert.equal(
      authStartSchema.safeParse({
        provider: "google",
        intent: "signup",
        ...extra,
      }).success,
      false,
    );
  assert.equal(
    authStartSchema.safeParse({ provider: "github", intent: "login" }).success,
    false,
  );
});
test("prepared identity options never imply verification, membership or sessions", () => {
  for (const provider of preparedProviders) {
    const result = preparedAuthStart({
      provider: provider.id,
      intent: "login",
    });
    assert.equal(result.verified, false);
    assert.equal(result.sessionCreated, false);
    assert.equal(result.status, "UNAVAILABLE");
  }
});
test("public sign-in requires exact approved origin and matching public Host", () => {
  assert.equal(acceptsPublicAuthOrigin(null, "127.0.0.1:3810"), false);
  assert.equal(
    acceptsPublicAuthOrigin("http://127.0.0.1:3810", "localhost:3810"),
    false,
  );
  assert.equal(
    acceptsPublicAuthOrigin("https://evil.example", "evil.example"),
    false,
  );
  assert.equal(
    acceptsPublicAuthOrigin("http://127.0.0.1:3810", "127.0.0.1:3810"),
    true,
  );
});
test("both prepared provider routes return 503 without a cookie or redirect", async () => {
  for (const provider of preparedProviders) {
    const response = await POST(
      request(JSON.stringify({ provider: provider.id, intent: "signup" })),
    );
    assert.equal(response.status, 503);
    assert.equal(response.headers.get("set-cookie"), null);
    assert.equal(response.headers.get("location"), null);
    assert.equal((await response.json()).sessionCreated, false);
  }
});
test("start endpoint rejects malformed/cross-site/oversized and wrong content type", async () => {
  assert.equal((await POST(request('{"provider":"google"}'))).status, 400);
  assert.equal((await POST(request("{"))).status, 400);
  assert.equal(
    (await POST(request("{}", { origin: "https://evil.example" }))).status,
    403,
  );
  assert.equal((await POST(request("{}".repeat(700)))).status, 413);
  assert.equal(
    (await POST(request("{}", { contentType: "text/plain" }))).status,
    415,
  );
  const missingOrigin = new Request("http://localhost:3810/api/auth/start", {
    method: "POST",
    headers: { host: "localhost:3810", "content-type": "application/json" },
    body: "{}",
  });
  assert.equal((await POST(missingOrigin)).status, 403);
});
test("status discloses identity-only scopes and unavailable connections", async () => {
  const response = await GET();
  const result = await response.json();
  assert.deepEqual(result.identityScopes, ["openid", "profile", "email"]);
  assert.equal(result.sessionCreated, false);
  assert.equal(response.headers.get("cache-control"), "no-store");
});
test("public legal identity is explicit and contactable", () => {
  assert.deepEqual(legalIdentity, {
    controller: "Axignal SL",
    country: "España",
    publicEmail: "contacto@axignal.com",
  });
  assert.equal(publicContactHref, "mailto:contacto@axignal.com");
});

test("draft preview/download retains multiline content and never claims receipt", () => {
  const local = {
    subject: "Acceso",
    name: "Persona de prueba",
    email: "test@example.invalid",
    message:
      "Quisiera comprender el alcance.\nSegunda línea literal <script> no se interpreta.",
  };
  const text = draftText(local, "es");
  assert.ok(text.includes(local.message));
  assert.ok(text.includes("NO ENVIADO"));
  assert.ok(text.includes("Destinatario: contacto@axignal.com"));
  assert.ok(
    text.endsWith(
      "Este borrador no registra una solicitud ni acredita recepción.",
    ),
  );
  assert.ok(draftText(local, "en").includes("NOT SENT"));
});
test("draft validation refuses missing identity, bad address, excessive text and hidden fields", () => {
  const valid = {
    subject: "Question",
    name: "Test",
    email: "test@example.invalid",
    message: "A specific question with context.",
  };
  for (const changed of [
    { name: "" },
    { email: "bad" },
    { message: "" },
    { message: "x".repeat(3001) },
    { consent: true },
  ])
    assert.equal(
      localDraftSchema.safeParse({ ...valid, ...changed }).success,
      false,
    );
});
