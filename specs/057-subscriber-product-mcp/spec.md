# 057 — Subscriber Product MCP

**Status:** IMPLEMENTED · **Date:** 2026-10-07 · **Decision:** ADR-0086
**Doctrine:** MASTER §13, §14, §15.1, §15.4, §20, §53.3. Consumes 049–052
(subscriber runtime, authorized read), ADR-0084 (billing entitlement) and
ADR-0085 (design-partner pilot).

## Problem

A subscriber cannot question their AXIGNAL reading from Claude or ChatGPT.
AXENT can, but each turn costs a Luna call. The subscriber's own assistant can
reason over the same governed reading if AXIGNAL exposes it safely.

## Requirements

- FR-1 Remote MCP over HTTPS at `{origin}/mcp`, usable by Claude (claude.ai
  connector, Claude Code `--transport http`) and other MCP clients.
- FR-2 OAuth 2.1 with discovery (RFC 9728, RFC 8414), dynamic client
  registration (RFC 7591), PKCE S256, resource indicators; consent from an
  authenticated subscriber session.
- FR-3 Authorization chain on every call: credential → Principal → Tenant →
  effective entitlement (paid Billing or live pilot grant) → authorized Xeed
  set → read. Fail closed.
- FR-4 Read-only tools and resources: list, overview, evidence (paged),
  timeline. POTENTIAL/UNKNOWN/currentness preserved.
- FR-5 Pilot expiry/revocation denies reads; memory and history are kept;
  Billing later restores the same Xeed.
- FR-6 Audit per call without secrets or payloads; `model_calls = 0`.
- FR-7 Subscribers list and revoke connections from their account.

## Acceptance

- Cross-tenant attempts by tool, resource URI, forged ids, foreign or garbage
  cursors, injected arguments, unknown/write tools all fail closed, both ways.
- Stale, expired, revoked and replayed tokens fail; refresh reuse revokes.
- Pilot revoked → `ENTITLEMENT_INACTIVE`; other tenants unaffected; billing →
  same Xeed, identical opportunities.
- No import path from the MCP to cognition/AXENT/provider SDKs.
- Real Claude connected to production on a real pilot Xeed.

## Out of scope

Writes of any kind, EvidenceAdmission, Admin MCP, SSE/sessions, confidential
clients, CRM/workflow features.
