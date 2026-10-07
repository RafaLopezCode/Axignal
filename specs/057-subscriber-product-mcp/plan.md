# 057 — Plan

```
Claude ──HTTPS──▶ Traefik ▶ landing nginx (exact paths) ▶ runtime :18181
                                   │                         ├─ ProductMcpHttp (edge: OAuth + /mcp)
                                   │                         │    ├─ OAuthService (application/product_mcp/oauth.py)
                                   │                         │    └─ ProductMcpServer (JSON-RPC, tools, resources, audit)
                                   │                         │         └─ SubscriberMemory → EntitlementPort + portfolio
                                   │                         │              → SubscriberEconomicRuntime.read (authorized read)
                                   │                         └─ /subscriber/mcp/* (consent, connections; session auth)
                                   └▶ experience (Next) /account/connect, /api/subscriber/mcp/* → runtime /subscriber/mcp/*
```

- `application/product_mcp/` — OAuth core, MCP server, governed views. Pure;
  no transport, no model.
- `pipeline/product_mcp/sqlite_store.py` — clients, requests, grants, codes,
  token digests, audit (`product-mcp.sqlite3` in the subscriber data root).
- `tools/runtime/product_mcp.py` — HTTP edge, runtime adapters, consent port.
- `tools/runtime/service.py` — routes exact MCP paths before other handlers;
  bounded body; path-only access log.
- `tools/runtime/subscriber_composition.py` — composes the MCP from the same
  portfolio, entitlement and economic runtime as the web product.
- `apps/web/experience` — consent page, connections block, proxies.
- `deploy/production/subscriber-edge-nginx.conf` — exact routes.
- Operator CLI: `subscriber_pilot grants|revoke` for pilot lifecycle.
