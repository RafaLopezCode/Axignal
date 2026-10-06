# Clarification Record: Subscriber Runtime Authority

**Date:** 2026-10-06
**Feature:** [spec.md](spec.md)
**Status:** Architecture decisions approved by root; no unresolved user clarification is needed to prepare implementation tasks.

## Decisions confirmed before planning

1. **Initial subscriber scope:** A new verified registration creates an AXIGNAL Principal, one initial Tenant, binary membership and identity binding atomically. This is self-service provisioning, not an entitlement grant. The data shape may support multiple memberships, but v1 does not promise additional Tenants or membership administration.
2. **Provider availability:** Google OIDC is the first provider. Sign in with ChatGPT is only enabled if AXIGNAL has an official, provisioned SIWC client and authorized access; until then it returns an explicit unavailable outcome. Provider client IDs/secrets are injected from the root-owned AXIGNAL secrets/configuration loader. No provider credentials or unrelated secret values were inspected.
3. **OIDC client scope:** Keep 048's exact issuer/subject reader contract backward compatible. Add optional configured `client_id` to the verified-identity key and use `(issuer, configured_client_id, subject)` where pairwise subjects are client-scoped; never trust client ID from browser or identity claims.
4. **Durability:** Use file-backed SQLite adapters under the configured AXIGNAL runtime data directory with schema versioning, unique/FK constraints and transactions. Root approved a separate `pipeline/subscriber_portfolio/` adapter boundary. This establishes local restart continuity, not HA, backup/restore, or multi-host guarantees.
5. **Observation capacity:** Resolve an `EntitlementSnapshot(capacity: int | None, currentness, confirmed_at)` server-side for Tenant as consumption scope only. There is no capacity on signup. Active and paused Focuses consume capacity. A checkout return cannot activate an Organization; a billing-authority update must confirm new capacity first.
6. **HTTP boundary:** Root owns `tools/runtime/config.py`, runtime composition and the frontend/API proxy. The subscriber modules provide typed services/ports; HTTP sets a `__Host-` secure, HttpOnly, SameSite=Lax session cookie and an opaque browser-bound one-time transaction cookie.
7. **Organization boundary:** Existing global Organization authority is reused where present. Directory/registry records are candidate evidence only. A pending/unresolved identity cannot create a canonical Organization, private Focus or economic output.
8. **Portfolio lifecycle:** Pause preserves visibility and consumes the slot; resume checks currentness/capacity; remove ends private observation without deleting AXIGLAND; replacement is an atomic swap only after target resolution; reobserve leaves the prior successful output available until a new run passes its evidence/readiness checks.
9. **Initial purchase authority (ADR-0084):** A verified self-service registration records separate, idempotent purchase authority for its initial Tenant scope through a billing-owned provisioning port. This authorizes that Principal to request paid capacity for that scope; it does not grant capacity and is not inferred from membership. Repeated explicit REGISTER may retry provisioning after a cross-store failure; LOGIN never provisions. Every checkout request rechecks current purchase authority in billing.

## External configuration availability

At review time, the environment exposed only unrelated Codex verification variable names. The production environment template contains general AXIGNAL runtime, existing billing, and disabled-feature names, but no OIDC client, subscriber session, or external database names. No values were read. Callback URIs proposed by the runtime owner are exact per environment: production Google `/api/auth/callback/google`, production OpenAI `/api/auth/callback/openai`, and localhost callbacks on `127.0.0.1:3810`. Providers remain disabled until their client registration/configuration is complete.

## Repository and product limits

- MASTER Â§Â§3â€“7 preserve one canonical AXIGLAND and private Focus ownership boundaries; Â§Â§23 and 46 prohibit user-controlled truth; Â§Â§51/55/56 require outputs grounded in evidence and human-readable uncertainty; P13 values professional portfolios in the tens/hundreds.
- ADR-0018/0021 preserve membership-first Focus reads and global Organization resolution.
- Spec 022 continues to defer payer cardinality, membership roles, account linking, deletion/retention and additional Tenant policy. No assumptions here settle those subjects.
- Customer Zero remains internal Admin self-use and is not a subscriber acceptance fixture.
