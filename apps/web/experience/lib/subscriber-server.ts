import { z } from "zod";
import { createHash } from "node:crypto";
import { authStartSchema, preparedAuthStart, preparedProviders } from "./public-contracts";
import { approvedPaymentUrl, portfolioSchema, subscriberCommandSchema, subscriberOutputSchema, subscriberResultSchema } from "./subscriber-contracts";

export const subscriberSessionCookie = "__Host-axignal-subscriber";
const transactionCookie = "__Host-axignal-oidc";
const headers = { "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" };
const opaque = /^[A-Za-z0-9_-]{32,256}$/;
function cookie(request: Request, name: string): string | null {
  const matches = (request.headers.get("cookie") ?? "").split(";").map(x => x.trim()).filter(x => x.startsWith(name + "="));
  if (matches.length !== 1) return null;
  const value = matches[0].slice(name.length + 1);
  return opaque.test(value) ? value : null;
}
function setCookie(name: string, value: string, seconds: number) {
  if (value && !opaque.test(value)) throw new Error("INVALID_SESSION");
  return `${name}=${value}; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=${seconds}`;
}
export function subscriberSameOrigin(request: Request): boolean {
  const allowed = process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810";
  const actual = request.headers.get("origin");
  try { return actual === allowed && new URL(allowed).host === request.headers.get("host"); }
  catch { return false; }
}
function runtimeOrigin(): URL {
  const url = new URL(process.env.AXIGNAL_RUNTIME_ORIGIN ?? "");
  const compose = process.env.AXIGNAL_CONTAINERIZED === "true" && url.hostname === "runtime" && url.port === "18181";
  if (url.protocol !== "http:" || (!compose && !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)) || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("RUNTIME_ORIGIN_REJECTED");
  return url;
}
export async function boundedSubscriberJson(request: Request, limit = 4096): Promise<unknown> {
  if (request.headers.get("content-type")?.split(";")[0].trim() !== "application/json") throw new Error("JSON_REQUIRED");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("INVALID_REQUEST");
  let size = 0; const chunks: Uint8Array[] = [];
  while (true) {
    const item = await reader.read(); if (item.done) break;
    size += item.value.byteLength;
    if (size > limit) { await reader.cancel(); throw new Error("BODY_LIMIT"); }
    chunks.push(item.value);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}
async function upstream(path: string, token?: string | null, body?: unknown): Promise<Response> {
  return fetch(new URL(path, runtimeOrigin()), {
    method: body === undefined ? "GET" : "POST", cache: "no-store", redirect: "error",
    signal: AbortSignal.timeout(20000),
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}),
      "Content-Type": "application/json", Origin: process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}
const rejected = (code: string, status: number) => Response.json({ state: "rejected", code }, { status, headers });
export async function subscriberBillingWebhook(request: Request): Promise<Response> {
  try {
    const signature = request.headers.get("stripe-signature");
    if (!signature || signature.length > 4096 || request.headers.get("content-type")?.split(";")[0].trim() !== "application/json") return rejected("INVALID_WEBHOOK", 400);
    const reader = request.body?.getReader();
    if (!reader) return rejected("INVALID_WEBHOOK", 400);
    const chunks: Uint8Array[] = []; let received = 0;
    while (true) {
      const chunk = await reader.read(); if (chunk.done) break;
      received += chunk.value.byteLength;
      if (received > 1_000_000) { await reader.cancel(); return rejected("BODY_LIMIT", 413); }
      chunks.push(chunk.value);
    }
    if (!received) return rejected("INVALID_WEBHOOK", 400);
    const raw = Buffer.concat(chunks);
    const response = await fetch(new URL("/internal/webhooks/subscriber-stripe", runtimeOrigin()), {
      method: "POST", cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000),
      headers: { "Content-Type": "application/json", "Stripe-Signature": signature }, body: raw,
    });
    const receipt = z.object({ accepted: z.boolean(), disposition: z.string().min(1).max(80) }).parse(await checkedJson(response));
    return Response.json(receipt, { status: response.status, headers });
  } catch { return rejected("BILLING_INGRESS_UNAVAILABLE", 503); }
}
async function checkedJson(response: Response): Promise<unknown> {
  const size = Number(response.headers.get("content-length"));
  if (size > 1048576) throw new Error("UPSTREAM_BODY_LIMIT");
  const reader = response.body?.getReader();
  if (!reader) throw new Error("UPSTREAM_BODY_REQUIRED");
  const chunks: Uint8Array[] = []; let received = 0;
  while (true) {
    const chunk = await reader.read(); if (chunk.done) break;
    received += chunk.value.byteLength;
    if (received > 1048576) { await reader.cancel(); throw new Error("UPSTREAM_BODY_LIMIT"); }
    chunks.push(chunk.value);
  }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}
export async function subscriberAuthStart(input: z.infer<typeof authStartSchema>): Promise<Response> {
  if (!process.env.AXIGNAL_RUNTIME_ORIGIN) return Response.json(preparedAuthStart(input), { status: 503, headers });
  try {
    const response = await upstream("/subscriber/auth/start", null, input);
    if (!response.ok) return rejected("AUTH_PROVIDER_UNAVAILABLE", response.status >= 500 ? 503 : 400);
    const result = z.object({ authorizationUrl: z.url(), transactionToken: z.string().regex(opaque) }).parse(await checkedJson(response));
    const url = new URL(result.authorizationUrl);
    const expected = input.provider === "google" ? "accounts.google.com" : "auth.openai.com";
    if (url.protocol !== "https:" || url.hostname !== expected || url.username || url.password || (url.port && url.port !== "443")) throw new Error("PROVIDER_URL_REJECTED");
    return Response.json({ status: "REDIRECT", authorizationUrl: result.authorizationUrl, sessionCreated: false }, {
      headers: { ...headers, "Set-Cookie": setCookie(transactionCookie, result.transactionToken, 600) },
    });
  } catch { return rejected("AUTH_PROVIDER_UNAVAILABLE", 503); }
}
export async function subscriberAuthStatus(): Promise<Response> {
  const unavailable = () => Response.json({ providers: preparedProviders, identityScopes: ["openid", "profile", "email"], sessionCreated: false }, { headers });
  if (!process.env.AXIGNAL_RUNTIME_ORIGIN) return unavailable();
  try {
    const response = await upstream("/subscriber/auth/status");
    if (!response.ok) return unavailable();
    const status = z.object({ providers: z.array(z.object({ id: z.enum(["google", "openai"]), status: z.enum(["AVAILABLE", "UNAVAILABLE"]), registrationRequired: z.boolean() })).length(2) }).parse(await checkedJson(response));
    if (new Set(status.providers.map(item => item.id)).size !== 2) return unavailable();
    return Response.json({ ...status, identityScopes: ["openid", "profile", "email"], sessionCreated: false }, { headers });
  } catch { return unavailable(); }
}
export async function subscriberAuthCallback(request: Request, provider: string): Promise<Response> {
  const target = new URL("/login?access=failed", process.env.AXIGNAL_EXPERIENCE_ORIGIN ?? "http://127.0.0.1:3810");
  const responseHeaders = new Headers(headers);
  responseHeaders.append("Set-Cookie", setCookie(transactionCookie, "", 0));
  try {
    if (!["google", "openai"].includes(provider)) throw new Error("PROVIDER_REJECTED");
    const tx = cookie(request, transactionCookie), query = new URL(request.url).searchParams;
    if (!tx || query.has("error") || query.getAll("state").length !== 1 || query.getAll("code").length !== 1) throw new Error("TRANSACTION_REQUIRED");
    const state = query.get("state"), code = query.get("code");
    if (!state || !code || state.length > 512 || code.length > 4096) throw new Error("TRANSACTION_REQUIRED");
    const result = await upstream("/subscriber/auth/callback", null, { provider, transactionToken: tx, state, code });
    if (!result.ok) throw new Error("CALLBACK_REJECTED");
    const issued = z.object({ sessionToken: z.string().regex(opaque), maxAge: z.number().int().min(1).max(86400) }).parse(await checkedJson(result));
    responseHeaders.append("Set-Cookie", setCookie(subscriberSessionCookie, issued.sessionToken, issued.maxAge));
    target.pathname = "/account"; target.search = "";
  } catch { /* Never put callback codes or provider errors in a URL or log. */ }
  responseHeaders.set("Location", target.href);
  return new Response(null, { status: 303, headers: responseHeaders });
}
export async function subscriberLogout(request: Request): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const response = await upstream("/subscriber/auth/logout", token, {});
    if (!response.ok) return rejected("SESSION_REVOCATION_UNAVAILABLE", 503);
    return Response.json({ state: "signed_out" }, { headers: { ...headers, "Set-Cookie": setCookie(subscriberSessionCookie, "", 0) } });
  } catch { return rejected("SESSION_REVOCATION_UNAVAILABLE", 503); }
}
export async function subscriberProxy(request: Request, path: string, write = false): Promise<Response> {
  if (write && !subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const command = write ? subscriberCommandSchema.parse(await boundedSubscriberJson(request)) : undefined;
    const response = await upstream(path, token, command);
    if (!response.ok) return rejected(response.status === 401 ? "AUTHENTICATION_REQUIRED" : response.status === 403 || response.status === 404 ? "ACCESS_DENIED" : "REQUEST_UNAVAILABLE", response.status);
    const payload = await checkedJson(response);
    const schema = write ? subscriberResultSchema : path.endsWith("/output") ? subscriberOutputSchema : portfolioSchema;
    const result = schema.parse(payload);
    if (write) {
      const commandResult = subscriberResultSchema.parse(result);
      for (const value of [commandResult.checkoutUrl, commandResult.paymentUrl]) if (value && !approvedPaymentUrl(value)) throw new Error("PAYMENT_URL_REJECTED");
    }
    const safeResult = !write && path.endsWith("/output") ? {
      ...subscriberOutputSchema.parse(result),
      revision: createHash("sha256").update(JSON.stringify(subscriberOutputSchema.parse(result).projection)).digest("hex"),
    } : result;
    return Response.json(safeResult, { status: response.status, headers });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("RUNTIME_UNAVAILABLE", 503);
  }
}
