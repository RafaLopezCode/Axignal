# Research: Subscriber Runtime Authority

## OIDC client and identity validation

**Decision:** Place a maintained OIDC client/JWT validator behind a provider-neutral adapter. Use Authorization Code with PKCE, exact configured issuer/client/redirect, browser-bound state consumed atomically once, nonce, signature/JWKS and time/audience validation. The adapter returns only the verified issuer, subject and configured client scope; provider tokens never enter portfolio/application state.

**Rationale:** The runtime must not implement signing algorithms, key rotation or claim validation itself. Authlib's current official client guide documents PKCE support, state validation and OIDC ID-token parsing/validation through JOSERFC. This confirms a maintained library is necessary rather than handcrafted JWT verification. Authlib does not own AXIGNAL's durable single-use transaction, account bootstrap, authorization or session policy; those remain our application contracts.

**Alternatives considered:**

- Custom JWT/JOSE verification: rejected; it creates unnecessary cryptographic protocol code.
- Use provider email as the user key or trust provider organization/role claims: rejected by Spec 022 and the MASTER.
- Treat a ChatGPT or Codex session, API key, OpenAI API token or provider access token as AXIGNAL subscriber identity: rejected.
- A shared OIDC adapter interface for Google and SIWC: accepted, but each client is separately configured and disabled until its exact issuer, callback, credentials and registration are approved.

**Provider sources:** [Authlib OIDC client documentation](https://docs.authlib.org/en/stable/oauth2/client/http/index.html); [Google OpenID Connect documentation](https://developers.google.com/identity/openid-connect/openid-connect); [OpenAI Sign in with ChatGPT for websites](https://developers.openai.com/siwc/website). The OpenAI flow has a registered-client and selected-partner availability condition; runtime configuration alone cannot claim eligibility.

## Durable private authority

**Decision:** Use SQLite-backed adapters under `AXIGNAL_DATA_DIR` for this single-runtime implementation slice, with schema versions, SQLite foreign keys, unique identity/membership/focus constraints, `BEGIN IMMEDIATE`-style serialized transactions, and explicit corruption/unavailable failure. A single durable subscriber database supports atomic first-registration bootstrap and local restart continuity. Portfolio capacity reservation and swap use a durable transactional store.

**Rationale:** The runtime already uses `AXIGNAL_DATA_DIR` and file-backed SQLite for single-host internal state. SQLite is an appropriate first durable adapter for an explicitly single-runtime launch footprint and can exercise transactions and restart semantics with the real adapter. This is not evidence of backup/restore, replication, multi-host consistency, or production deployment readiness; those remain UNKNOWN until operated and tested.

**Alternatives considered:**

- In-memory or fixture-only subscriber authority: rejected; it cannot prove persistence or restart continuity.
- Introduce a hosted SQL provider without configuration evidence: rejected; no subscriber database URL/provider setting exists in the production environment template.
- Treat Admin's local Customer Zero data as subscriber authority: rejected; separate Principal/Tenant and Admin authority planes are mandatory.

## Capacity, checkout and Organization resolution

**Decision:** Read capacity through a server-side `EntitlementPort`; request checkout only for the exact positive difference; never activate a Focus from browser return. Tenant is the capacity consumption scope only, while payer binding remains billing-owned and separate. Any active or paused Focus counts. A stale/unknown snapshot cannot authorize additional capacity.

**Organization decision:** Resolve existing Organizations only from global canonical authority. Public registration/directory search can produce candidates for governed resolution but cannot create canonical identity directly. A pending request directs attention without a FAXT, Organization, or Focus.

**Integration boundary:** Root coordinates the typed capacity snapshot and checkout request contracts with the billing work. A verified billing-authority event changes entitlement; callback query fields do not.

## Test strategy

Use actual file-backed stores and reopen/restart boundaries for registration, mapping, transaction replay, session revocation/expiry, memberships, capacity reservations and portfolio lifecycle. Use deterministic local OIDC/JWKS and billing/Organization ports only as external service fixtures; assert real JWT checks and real SQLite constraints. Every subscriber data test proves membership is checked before any private Focus/projection load. A dedicated 1/2/100 sequence verifies entitlement capacity, Organization references, independent observation runs and persistence after restart.
