import test from "node:test";
import assert from "node:assert/strict";
import { approvedMcpRedirect, clearMcpConnect, mcpConnectionsSchema, mcpConsentSchema, pendingMcpConnect, rememberMcpConnect } from "../lib/mcp-connect";
function storage() {
  const values = new Map<string, string>();
  return { getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => { values.set(key, value); },
    removeItem: (key: string) => { values.delete(key); } };
}
test("consent return path survives sign-in for a bounded time and carries only a request reference", () => {
  const store = storage(), request = "r".repeat(32);
  assert.equal(rememberMcpConnect("../account?x=1", store, 100), false);
  assert.equal(pendingMcpConnect(store, 101), null);
  assert.equal(rememberMcpConnect(request, store, 100), true);
  assert.equal(pendingMcpConnect(store, 101), request);
  assert.equal(pendingMcpConnect(store, 100 + 10 * 60 * 1000), null);
  assert.equal(pendingMcpConnect(store, 102), null);
  rememberMcpConnect(request, store, 200);
  clearMcpConnect(store);
  assert.equal(pendingMcpConnect(store, 201), null);
  store.setItem("axignal_mcp_connect", JSON.stringify({ request, expiresAt: 10 ** 12 }));
  assert.equal(pendingMcpConnect(store, 0), null, "a far-future expiry is not trusted");
});
test("only HTTPS or loopback client redirects are followed", () => {
  assert.equal(approvedMcpRedirect("https://claude.ai/api/mcp/auth_callback?code=a&state=b"), "https://claude.ai/api/mcp/auth_callback?code=a&state=b");
  assert.ok(approvedMcpRedirect("http://127.0.0.1:33418/callback?code=a"));
  assert.ok(approvedMcpRedirect("http://localhost:8080/cb?code=a"));
  for (const value of ["http://evil.example/cb", "javascript:alert(1)", "https://u:p@claude.ai/cb", "https://claude.ai/cb#code", "not a url", "data:text/html,x"]) {
    assert.equal(approvedMcpRedirect(value), null, value);
  }
});
test("consent and connection payloads are strict and read-only", () => {
  const consent = { client: "Claude", redirectHost: "claude.ai", scope: "xeed:read", expiresAt: "2026-10-07T10:00:00+00:00", access: "ACTIVE", xeeds: ["Solartec"] };
  assert.ok(mcpConsentSchema.parse(consent));
  assert.throws(() => mcpConsentSchema.parse({ ...consent, scope: "xeed:write" }));
  assert.throws(() => mcpConsentSchema.parse({ ...consent, tenantId: "tenant:a" }));
  assert.ok(mcpConnectionsSchema.parse({ connections: [{ grantId: "mcpgrant_" + "a".repeat(24), client: "Claude", connectedAt: "2026-10-07", scope: "xeed:read" }] }));
  assert.throws(() => mcpConnectionsSchema.parse({ connections: [{ grantId: "../x", client: "Claude", connectedAt: "2026-10-07", scope: "xeed:read" }] }));
});
