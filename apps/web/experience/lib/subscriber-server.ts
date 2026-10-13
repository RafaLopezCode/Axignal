import { z } from "zod";
import { createHash } from "node:crypto";
import { authStartSchema, preparedAuthStart, preparedProviders } from "./public-contracts";
import { approvedPaymentUrl, pendingOutputSchema, pilotRedemptionSchema, portfolioSchema, subscriberCommandSchema, subscriberOutputSchema, subscriberResultSchema } from "./subscriber-contracts";
import type { RuntimeProjection } from "./runtime-projection";
import { poolReading, poolToken, type PoolReading } from "./marketing-pool";
import { approvedMcpRedirect, mcpConnectionsSchema, mcpConsentSchema, mcpDecisionSchema, mcpGrantId, mcpRequestId, mcpRevokeSchema } from "./mcp-connect";

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
export const legalOperatorSchema = z.object({
  state: z.literal("PUBLISHED"), name: z.string().min(1).max(200), kind: z.string().max(80).nullable(),
  taxId: z.string().min(1).max(40), address: z.string().min(1).max(400), contact: z.string().min(3).max(254),
  termsVersion: z.string().min(1).max(80),
});
export type LegalOperator = z.infer<typeof legalOperatorSchema>;
/** The service holder (LSSI art. 10) as configured on the server; null when not published. */
export async function legalOperator(): Promise<LegalOperator | null> {
  if (!process.env.AXIGNAL_RUNTIME_ORIGIN) return null;
  try {
    const response = await upstream("/subscriber/legal/operator");
    if (!response.ok) return null;
    const parsed = legalOperatorSchema.safeParse(await checkedJson(response));
    return parsed.success ? parsed.data : null;
  } catch { return null; }
}
/** A marketing pool recipient's reading (their token is the only authority). */
export async function poolReadingFor(token: string): Promise<PoolReading | null> {
  if (!process.env.AXIGNAL_RUNTIME_ORIGIN || !poolToken.test(token)) return null;
  try {
    const response = await upstream("/public/marketing-pool/reading/" + token);
    if (!response.ok) return null;
    const parsed = poolReading.safeParse(await checkedJson(response));
    return parsed.success ? parsed.data : null;
  } catch { return null; }
}
/** Opt-out: always answers the same, whether the token is known or not. */
export async function poolUnsubscribe(token: string): Promise<boolean> {
  if (!process.env.AXIGNAL_RUNTIME_ORIGIN || !poolToken.test(token)) return false;
  try { return (await upstream("/public/marketing-pool/unsubscribe/" + token, null, {})).ok; }
  catch { return false; }
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
/** Tenant-grounded AXENT turn. Scope comes from the session cookie and path only. */
export async function subscriberAxent(request: Request, contextId: string, body: { question: string; locale: string; memory?: unknown }): Promise<Record<string, unknown> | null> {
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return null;
  try {
    const response = await upstream(`/subscriber/organizations/${encodeURIComponent(contextId)}/axent`, token, body);
    if (!response.ok) return null;
    const payload = await checkedJson(response);
    return typeof payload === "object" && payload !== null ? (payload as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Registry candidates for "verify identity": suggestions only; nothing is admitted here. */
export const identityCandidatesSchema = z.object({
  state: z.enum(["success", "UNAVAILABLE"]),
  candidates: z.array(z.object({
    lei: z.string().regex(/^[A-Z0-9]{18}[0-9]{2}$/), legalName: z.string().min(1).max(512),
    country: z.string().max(8).nullable(), city: z.string().max(200).nullable(),
  }).strict()).max(20),
}).strict();
export async function subscriberIdentityCandidates(request: Request): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const input = z.object({ query: z.string().trim().min(2).max(120), country: z.string().regex(/^[A-Z]{2}$/).optional() }).strict().parse(
      await boundedSubscriberJson(request, 512),
    );
    const response = await upstream("/subscriber/identity/candidates", token, input);
    if (!response.ok) return rejected(response.status === 401 ? "AUTHENTICATION_REQUIRED" : "REGISTRY_UNAVAILABLE", response.status);
    return Response.json(identityCandidatesSchema.parse(await checkedJson(response)), { headers });
  } catch {
    return rejected("REGISTRY_UNAVAILABLE", 503);
  }
}

export async function subscriberDemandMarkets(request: Request, focus: string): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  if (!/^[A-Za-z0-9:_-]{1,160}$/.test(focus)) return rejected("INVALID_REFERENCE", 400);
  try {
    const input = z.object({ markets: z.array(z.string().regex(/^EU\/[A-Z]{2}$/)).max(5) }).strict().parse(await boundedSubscriberJson(request, 512));
    const response = await upstream(`/subscriber/organizations/${encodeURIComponent(focus)}/demand-markets`, token, input);
    if (!response.ok) return rejected(response.status === 401 ? "AUTHENTICATION_REQUIRED" : "ACCESS_DENIED", response.status);
    return Response.json(z.object({ state: z.literal("success"), directed: z.array(z.string()) }).parse(await checkedJson(response)), { headers });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("RUNTIME_UNAVAILABLE", 503);
  }
}

export async function subscriberPilotRedeem(request: Request): Promise<Response> {
  if (!subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const input = z.object({ inviteToken: z.string().min(20).max(256) }).strict().parse(
      await boundedSubscriberJson(request, 512),
    );
    const response = await upstream("/subscriber/pilot/redeem", token, input);
    if (!response.ok) {
      return rejected(
        response.status === 401
          ? "AUTHENTICATION_REQUIRED"
          : response.status === 404
            ? "PILOT_NOT_ENABLED"
            : "PILOT_REDEMPTION_UNAVAILABLE",
        response.status,
      );
    }
    return Response.json(pilotRedemptionSchema.parse(await checkedJson(response)), {
      status: response.status,
      headers,
    });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("PILOT_REDEMPTION_UNAVAILABLE", 503);
  }
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
    if (!write && path.endsWith("/output") && typeof payload === "object" && payload !== null && (payload as { kind?: unknown }).kind === "PENDING_ATTENTION") {
      return Response.json(pendingOutputSchema.parse(payload), { status: response.status, headers });
    }
    const schema = write ? subscriberResultSchema : path.endsWith("/output") ? subscriberOutputSchema : portfolioSchema;
    const result = schema.parse(payload);
    if (write) {
      const commandResult = subscriberResultSchema.parse(result);
      for (const value of [commandResult.checkoutUrl, commandResult.paymentUrl]) if (value && !approvedPaymentUrl(value)) throw new Error("PAYMENT_URL_REJECTED");
    }
    const safeResult = !write && path.endsWith("/output") ? {
      ...subscriberOutputSchema.parse(result),
      revision: subscriberOutputRevision(subscriberOutputSchema.parse(result)),
    } : result;
    return Response.json(safeResult, { status: response.status, headers });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("RUNTIME_UNAVAILABLE", 503);
  }
}

/** A reevaluation clock does not invalidate an otherwise identical reading.
 * Evidence, support refs, effective currentness and content remain in the hash.
 */
export function subscriberProjectionRevision(projection: RuntimeProjection): string {
  const canonical = JSON.parse(JSON.stringify(projection)) as RuntimeProjection;
  if (canonical.cognition) {
    const { asOf: _evaluationClock, ...content } = canonical.cognition;
    const sources = content.sources.map(({ currentnessEvaluatedAt: _clock, ...source }) => source);
    const opportunities = content.opportunities.map(({ currentnessEvaluatedAt: _clock, ...opportunity }) => opportunity);
    Object.assign(canonical, { cognition: { ...content, sources, opportunities } });
  }
  const measurement = canonical.digitalRepresentation;
  if (measurement && "kind" in measurement && measurement.currentnessEvaluation) {
    const { asOf: _evaluationClock, ...evaluation } = measurement.currentnessEvaluation;
    Object.assign(measurement, { currentnessEvaluation: evaluation });
  }
  return createHash("sha256").update(JSON.stringify(canonical)).digest("hex");
}

/** Product MCP consent and connections (ADR-0086). Identity comes from the session cookie only. */
export async function subscriberMcpRequest(request: Request, requestId: string, decide: boolean): Promise<Response> {
  if (decide && !subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  if (!mcpRequestId.test(requestId)) return rejected("INVALID_REFERENCE", 400);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const command = decide ? z.object({ decision: z.enum(["approve", "deny"]) }).strict().parse(await boundedSubscriberJson(request, 256)) : undefined;
    const response = await upstream(`/subscriber/mcp/requests/${encodeURIComponent(requestId)}`, token, command);
    if (!response.ok) return rejected(response.status === 401 ? "AUTHENTICATION_REQUIRED" : response.status === 400 ? "REQUEST_EXPIRED" : "REQUEST_UNAVAILABLE", response.status === 400 ? 410 : response.status);
    const payload = await checkedJson(response);
    if (!decide) return Response.json(mcpConsentSchema.parse(payload), { headers });
    const redirect = approvedMcpRedirect(mcpDecisionSchema.parse(payload).redirect);
    if (!redirect) throw new Error("REDIRECT_REJECTED");
    return Response.json({ redirect }, { headers });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("RUNTIME_UNAVAILABLE", 503);
  }
}
export async function subscriberMcpConnections(request: Request, revoke: boolean): Promise<Response> {
  if (revoke && !subscriberSameOrigin(request)) return rejected("ORIGIN_REQUIRED", 403);
  const token = cookie(request, subscriberSessionCookie);
  if (!token) return rejected("AUTHENTICATION_REQUIRED", 401);
  try {
    const command = revoke ? z.object({ action: z.literal("revoke"), grantId: z.string().regex(mcpGrantId) }).strict().parse(await boundedSubscriberJson(request, 256)) : undefined;
    const response = await upstream("/subscriber/mcp/connections", token, command);
    if (!response.ok) return rejected(response.status === 401 ? "AUTHENTICATION_REQUIRED" : "REQUEST_UNAVAILABLE", response.status);
    const payload = await checkedJson(response);
    return Response.json(revoke ? mcpRevokeSchema.parse(payload) : mcpConnectionsSchema.parse(payload), { headers });
  } catch (error) {
    if (error instanceof z.ZodError) return rejected("INVALID_REQUEST_OR_RESPONSE", 400);
    return rejected("RUNTIME_UNAVAILABLE", 503);
  }
}

/** Bind the subscriber reading to its private conditioned report without changing canonical projection identity. */
export function subscriberOutputRevision(output: z.infer<typeof subscriberOutputSchema>): string {
  const revision = subscriberProjectionRevision(output.projection);
  const report = output.firstObservation?.publicUnderstanding;
  return report ? createHash("sha256").update(JSON.stringify([revision, report.reportId, report.currentness])).digest("hex") : revision;
}
