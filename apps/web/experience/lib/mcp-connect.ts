import { z } from "zod";

/** Product MCP consent (ADR-0086). The runtime authorizes; this file only carries and checks shapes. */
export const mcpRequestId = /^[A-Za-z0-9_-]{20,160}$/;
export const mcpGrantId = /^mcpgrant_[a-f0-9]{24}$/;

export const mcpConsentSchema = z.object({
  client: z.string().min(1).max(100),
  redirectHost: z.string().min(1).max(260),
  scope: z.literal("xeed:read"),
  expiresAt: z.string().min(1).max(64),
  access: z.enum(["ACTIVE", "ENTITLEMENT_INACTIVE"]),
  xeeds: z.array(z.string().min(1).max(300)).max(100),
}).strict();
export const mcpDecisionSchema = z.object({ redirect: z.string().min(1).max(4096) }).strict();
export const mcpConnectionsSchema = z.object({
  connections: z.array(z.object({
    grantId: z.string().regex(mcpGrantId),
    client: z.string().min(1).max(100),
    connectedAt: z.string().min(1).max(64),
    scope: z.literal("xeed:read"),
  }).strict()).max(100),
}).strict();
export const mcpRevokeSchema = z.object({ revoked: z.boolean() }).strict();
export type McpConsent = z.infer<typeof mcpConsentSchema>;
export type McpConnection = z.infer<typeof mcpConnectionsSchema>["connections"][number];

const loopback = new Set(["localhost", "127.0.0.1", "[::1]"]);
/** The client redirect was registered and checked by the runtime; check it again before navigating. */
export function approvedMcpRedirect(value: string): string | null {
  try {
    const url = new URL(value);
    if (url.username || url.password || url.hash) return null;
    if (url.protocol === "https:" || (url.protocol === "http:" && loopback.has(url.hostname))) return url.href;
  } catch { /* An unparseable redirect is never followed. */ }
  return null;
}

const key = "axignal_mcp_connect";
const lifetimeMs = 10 * 60 * 1000;
type ConnectStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;
type StorageSource = ConnectStorage | (() => ConnectStorage);
const resolveStorage = (source: StorageSource): ConnectStorage => typeof source === "function" ? source() : source;

// Transient return path across sign-in. It carries no authority: the runtime re-checks the request.
export function rememberMcpConnect(requestId: string, storage: StorageSource, now = Date.now()): boolean {
  if (!mcpRequestId.test(requestId)) return false;
  try { resolveStorage(storage).setItem(key, JSON.stringify({ request: requestId, expiresAt: now + lifetimeMs })); return true; }
  catch { return false; }
}
export function clearMcpConnect(storage: StorageSource): void {
  try { resolveStorage(storage).removeItem(key); } catch { /* Storage failure grants no access. */ }
}
export function pendingMcpConnect(storage: StorageSource, now = Date.now()): string | null {
  try {
    const raw = resolveStorage(storage).getItem(key);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (typeof value === "object" && value !== null &&
        "request" in value && typeof value.request === "string" && mcpRequestId.test(value.request) &&
        "expiresAt" in value && typeof value.expiresAt === "number" &&
        value.expiresAt > now && value.expiresAt <= now + lifetimeMs) return value.request;
  } catch { /* A malformed return path is dropped. */ }
  clearMcpConnect(storage);
  return null;
}
