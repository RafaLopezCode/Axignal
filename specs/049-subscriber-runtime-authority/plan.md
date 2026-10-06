# Implementation Plan: Subscriber Runtime Authority

**Branch**: `codex/production-closure` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Subscriber identity, durable session and private portfolio E2E requirements in this feature.

## Summary

Deliver the first durable subscriber runtime boundary: configured OIDC login/registration, transactional first-subscriber provisioning, revocable server-side sessions, authorization-before-private-load, and tenant-scoped Organization Focus lifecycle bounded by a fresh server-confirmed entitlement. Google is the first provider. Sign in with ChatGPT is represented as an officially documented but unavailable-until-authorized provider; no client is assumed to exist. Identity binding is exact issuer + subject and may include a configured client ID for pairwise-subject scope. User-supplied Organization locators direct attention and cannot become canonical Organization, FAXT, or output truth.

## Technical Context

**Language/Version**: Python 3.11+.

**Primary Dependencies**: Existing `uv` project and standard library SQLite; add only a maintained OIDC/JWT dependency if implementation requires it for discovery, PKCE, JWKS signature and OIDC claim validation. No handwritten cryptographic verification and no provider SDK dependency.

**Storage**: File-backed SQLite under the configured AXIGNAL data directory. OIDC transactions, identity bindings, Principal/Tenant/membership, hashed sessions, private portfolio, idempotency and capacity reservations are durable. No cached private-data authorization on database errors.

**Testing**: pytest; file-backed SQLite integration tests reopen the database to prove transaction replay, session revocation/expiry, membership changes, portfolio lifecycle and capacity state survive process/service reconstruction. Run focused subscriber identity/portfolio tests and the root-selected regressions; root owns baseline and final deterministic gates.

**Target Platform**: AXIGNAL Python runtime on local development and configured server runtime. Callback URI and cookie policy are environment-specific; production requires HTTPS and exact registered redirect URIs.

**Project Type**: Python application/runtime service and durable pipeline adapters; HTTP routing and frontend API proxy are composed by root outside this feature.

**Performance Goals**: No numeric SLO is specified. Serialize mutation transactions sufficiently to prevent duplicate bootstrap and over-capacity reservations; do not claim production throughput or multi-host SQLite support.

**Constraints**: Unknown or stale entitlement denies capacity-increasing commands. Active and paused Focuses consume capacity. Tenant is only an entitlement-consumption scope, never a payer inference. Only verified billing authority changes entitlements. Login cannot auto-register; explicit registration may atomically create one Principal, one private Tenant and one binary membership. After commit, explicit REGISTER invokes a billing-owned idempotent port that records purchase authority for the initial scope only; it grants no capacity, is never inferred from membership, and REGISTER retry repairs a cross-store failure. Each checkout rechecks that authority. Each private operation rechecks membership before loading portfolio/projections. No session token or OAuth credential in logs, exception reprs, or persistent plaintext. Provider enabled only if client registration/config is complete. Public registries are candidates, not canonical Organization stores.

**Scale/Scope**: A subscriber may manage 1, 2 or 100 Organization Focuses whenâ€”and only whenâ€”the current verified entitlement supports that capacity. Multiple memberships are representable, but v1 bootstrap creates one Tenant per Principal and does not choose arbitrarily if additional memberships later exist.

## Constitution Check

- **Epistemic authority**: Pass. Subscriber inputs direct attention only. Organization/FAXT canonical writes stay behind existing governed identity/evidence admission.
- **Tenant and Focus boundaries**: Pass. Organization remains global AXIGLAND truth; Focus and membership are private tenant scope; Tenant is not payer.
- **Unknown handling**: Pass. Missing, stale or unavailable membership/session/entitlement/database state fails closed and remains explicitly unknown or unavailable.
- **Provider independence**: Pass. Application consumes a provider port and validated identity pair; no model or auth provider becomes domain authority. Google and conditional OpenAI are adapters/configuration only.
- **Security and privacy**: Pass. PKCE S256, state/nonce/browser-bound one-time transactions, validated OIDC claims, opaque hashed server sessions, secure host-only cookies in root-owned HTTP composition, and membership-before-load.
- **Governance**: Pass. Feature files and runtime modules remain in the approved 049 scope; no changes to MASTER, billing, web UI, economic discovery, deployment, or gates.

## Architecture and Interfaces

JOSE signature verification uses maintained `PyJWT[crypto]` in the explicit
`subscriber-auth` dependency group. The default core retains no runtime
dependencies and the existing graph architecture gate is unchanged. Development
gates include this group; the opt-in subscriber image installs this group from
the frozen lock without LLM, graph or development packages. The baseline runtime
image remains separate and cannot be presented as subscriber-auth capable.

The exact public service and durable-port contracts are recorded in [subscriber-identity-and-session.md](contracts/subscriber-identity-and-session.md), [subscriber-portfolio-and-capacity.md](contracts/subscriber-portfolio-and-capacity.md), and [runtime-composition.md](contracts/runtime-composition.md). The module boundary is:

- `application/subscriber_identity/`: provider-neutral registration, login intent, transaction consumption, and session policy.
- `pipeline/subscriber_identity/`: SQLite implementations for identity binding, Principal/Tenant/membership bootstrap, OIDC transaction, and session stores.
- `tools/runtime/subscriber_identity.py`: runtime faÃ§ade consumed by root-owned HTTP composition.
- `application/subscriber_portfolio/`: authorized portfolio commands, capacity policy and Organization identity resolution port.
- `pipeline/subscriber_portfolio/`: SQLite private portfolio, reservations and idempotency implementations.
- `tools/runtime/subscriber_portfolio.py`: runtime faÃ§ade consumed by root-owned API composition.
- `tests/subscriber_identity/` and `tests/subscriber_portfolio/`: real file-backed persistence and authorization-order integration tests, plus focused policy tests.

Root-owned composition in `tools/runtime/config.py` and `tools/runtime/service.py` constructs these faÃ§ades and the HTTP routes/cookies. It injects typed provider configuration including exact issuer, client, callback, server-only credential path and optional subject client scope. It does not receive OAuth secrets as user-facing output or log fields.

## Data and Transaction Design

Use database constraints as final guards for unique `(issuer, subject, client_scope)` identity binding, one-time transaction consumption, session token hash uniqueness, idempotency, and `(tenant_id, organization_id)` Focus uniqueness. Registration inserts identity binding, Principal, Tenant and membership atomically. After commit, explicit REGISTER calls billing's idempotent purchase-scope provisioner; a failed billing write leaves the durable subscriber intact but unable to checkout until repeat REGISTER repairs the authority. Session issue stores only a hash. Each portfolio command resolves session/context and current membership before private reads; mutation rechecks membership inside the transaction. Add locks/serializes the capacity decision with live reservations and Focus insertion. Checkout request records an exact positive delta but creates no Focus. Replace stages resolution and swaps references atomically; a failed stage leaves the old Focus and output available. Reobserve retains the last successful output until a new run is accepted.

## Validation Plan

1. Prove login for unknown identity denies without creating Principal/Tenant; explicit registration creates exactly one of each under duplicate/concurrent callback races.
2. Prove state/nonce/PKCE/provider/client/callback mismatches and replay are rejected, including after restart, with no token or code in errors/logs.
3. Prove valid session works after restart; expired/revoked session and removed membership fail before private portfolio/projection loading.
4. Prove entitlement capacity 1, 2 and 100 permits exactly that many slots; unknown/stale capacity blocks; active and paused consume; concurrent adds cannot exceed capacity; excess requests checkout for exact delta and browser return alone grants nothing.
5. Prove pending/rejected Organization identity creates no canonical Organization, FAXT, Focus or output; add/replace/reobserve failure preserves previous successful output; remove affects only private Focus.
6. Run the focused subscriber suites, relevant existing authorization/identity tests and Architecture Guard. Root runs full deterministic gates and convergence after integrating its HTTP/config/billing work.

## Project Structure

```text
application/
  subscriber_identity/
  subscriber_portfolio/
pipeline/
  subscriber_identity/
  subscriber_portfolio/
tools/runtime/
  subscriber_identity.py
  subscriber_portfolio.py
tests/
  subscriber_identity/
  subscriber_portfolio/
specs/049-subscriber-runtime-authority/
  contracts/
  data-model.md
  research.md
  quickstart.md
  plan.md
  clarify.md
  tasks.md
```

**Structure Decision**: Add provider-neutral application services, durable pipeline adapters, and small runtime faÃ§ades in the existing Python package layout. HTTP and frontend remain root-owned integration boundaries.

## Complexity Tracking

No Constitution exceptions requested. SQLite is the approved first durable adapter and does not claim multi-host coordination or production backup/restore readiness.
