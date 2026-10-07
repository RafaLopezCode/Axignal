# ADR-0086: Subscriber Product MCP over OAuth 2.1 (read-only)

- **Status:** Accepted
- **Date:** 2026-10-07
- **Authority:** MASTER PRODUCT MODEL (§13 replaceable providers, §14 models are not truth, §15.1 CLAIM ≠ WRITE, §15.4 UNKNOWN ≠ FALSE, §20 currentness, §53.3 derived opportunity stays POTENTIAL); Constitution; ADR-0084; ADR-0085; direct human product decision.
- **Scope:** a public, subscriber-facing Model Context Protocol endpoint that lets a subscriber's own assistant (Claude, ChatGPT or another MCP client) read that subscriber's authorized Xeeds.

## Context

Subscribers and design partners want to question their AXIGNAL reading from the assistant they already use. Doing it through AXENT costs a Luna call per turn. The subscriber's assistant can do the conversational reasoning itself if AXIGNAL hands it the same governed reading the web product shows, with its epistemic state, evidence and limits.

That only works if authorization is exactly as strict as the web product: an external client must never become a way to read another tenant, widen a pilot, bypass entitlement or write.

## Decision

1. **Resource.** The runtime serves `POST {origin}/mcp` (MCP Streamable HTTP, stateless, JSON responses; protocol versions 2025-11-25, 2025-06-18, 2025-03-26). No SSE stream, no sessions, no batching.
2. **Authorization server.** AXIGNAL is its own OAuth 2.1 authorization server for this resource: RFC 9728 protected-resource metadata, RFC 8414 server metadata, RFC 7591 dynamic registration of **public clients only**, authorization code with **PKCE S256 mandatory**, RFC 8707 resource indicator bound to `{origin}/mcp`. Unauthenticated calls get `401` with `WWW-Authenticate: Bearer resource_metadata=…`.
3. **Consent.** The authorization request is decided by the subscriber in an authenticated first-party session (`/account/connect`). The grant binds `principal_id + tenant_id + client_id + resource`; it is never derived from email, a client-supplied tenant, organization or Xeed id, or a frontend claim.
4. **Tokens.** Opaque, high-entropy, stored only as SHA-256 digests. Access 1 h; refresh 30 d with rotation; refresh reuse revokes the whole grant. Codes are single-use, 5 min, bound to client, redirect, PKCE challenge and resource. Requests are single-use, 10 min.
5. **Per-call authorization.** Each tool/resource call re-checks, in order: live grant → Principal–Tenant membership → effective entitlement (current paid Billing **or** live pilot grant, via the same `EntitlementPort` the web product uses, no duplicated logic) → Xeed ∈ that tenant's ACTIVE portfolio within capacity → the existing authorized subscriber read. Any failure fails closed with a stable code and no foreign data.
6. **Read-only.** Scope is `xeed:read` only. Tools: `list_xeeds`, `get_xeed_overview`, `get_xeed_evidence` (cursor bound to its Xeed), `get_xeed_timeline`; resources `axignal://xeeds/{id}/{overview|evidence|timeline}`. All annotated `readOnlyHint`. No EvidenceAdmission, no portfolio mutation, no observation trigger, no Admin MCP.
7. **No model on reads.** The MCP path imports nothing from `cognition`, AXENT or provider SDKs (AST-tested). Audit rows record `model_calls = 0`. Reasoning is the subscriber's assistant's own; AXIGNAL output stays inspectable data with OBSERVED / POTENTIAL / UNKNOWN and currentness, and states that content is data, not instructions.
8. **Pilot lifecycle.** Pilot expiry or revocation denies MCP reads (`ENTITLEMENT_INACTIVE`) exactly as on the web; AXIGLAND, history and the Xeed are kept, and the same Xeed reads again when paid Billing later applies.
9. **Audit.** One row per audited call: time, principal, tenant, client, method, tool or resource, Xeed, outcome, denial code, duration, response bytes, model calls. Never tokens, codes, query strings or payloads.
10. **Revocation.** Subscribers list and revoke their own connections from the account; revocation deletes the grant's tokens. A grant of another principal or tenant is invisible.

## Consequences

- Subscriber questions answered in the subscriber's own assistant cost AXIGNAL a deterministic read, not a Luna call.
- AXIGNAL is not the source of the assistant's wording; the consent screen says the assistant can be wrong.
- Write capabilities, Admin MCP, confidential clients and SSE are out of scope and require a new decision.
- The edge exposes exact paths only (`/mcp`, `/oauth/{register,authorize,token}`, the three `/.well-known` documents); nothing broader.
