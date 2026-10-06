# Tasks: Subscriber Runtime Authority

**Source**: approved `spec.md`, `clarify.md`, `plan.md`, data model and contracts. Tasks are ordered to keep identity authorization and durable portfolio state in scope before runtime integration.

## Phase 1: Identity, OIDC and sessions

- [ ] T001 Add typed subscriber identity, OIDC transaction, session, provider config and result models in `application/subscriber_identity/`.
- [ ] T002 Define provider-neutral ports for identity binding, transactional subscriber bootstrap, one-time OIDC transaction, session persistence, membership read and OIDC verification in `application/subscriber_identity/`.
- [ ] T003 Add minimal maintained OIDC/JWT dependency only if required; record exact lockfile delta in `pyproject.toml` and `uv.lock`.
- [ ] T004 Implement Google OIDC Authorization Code + PKCE S256 and OIDC claim verification behind the provider port; implement OpenAI SIWC adapter only using official issuer/protocol config, disabled absent approved client registration.
- [ ] T005 Implement SQLite identity binding, atomic Principal/Tenant/binary membership bootstrap, transaction replay barrier, hashed session storage, expiry and revocation in `pipeline/subscriber_identity/`.
- [ ] T006 Implement login/register intent, transaction verification/consumption, bootstrap race handling, session resolution and membership recheck in `application/subscriber_identity/`; add the billing-owned idempotent `InitialPurchaseScopeProvisioner` port and invoke it on explicit REGISTER for both new and existing bindings, never LOGIN. Provisioning failure remains retryable and grants neither checkout authority nor capacity until billing confirms.
- [ ] T007 Expose `build_subscriber_identity_runtime(data_dir, providers, clock)` and the start/callback/authenticate/logout faÃ§ade in `tools/runtime/subscriber_identity.py`.
- [ ] T008 Add tests for explicit REGISTER vs LOGIN, exact issuer/subject/client-scope binding, provider disabled state, one-time replay, mismatch rejection and sanitized exceptions in `tests/subscriber_identity/`.
- [ ] T009 Add file-backed restart tests for registration uniqueness races, active/expired/revoked sessions and membership revocation before private-data load in `tests/subscriber_identity/`.

## Phase 2: Private portfolio and confirmed capacity

- [ ] T010 Add private Focus lifecycle, typed Organization resolution, entitlement snapshot, checkout and command result models/ports in `application/subscriber_portfolio/`.
- [ ] T011 Implement SQLite portfolio, durable retryable/cancellable pending identity request, idempotency tombstones and serialized capacity reservation stores with uniqueness/FK constraints in `pipeline/subscriber_portfolio/`.
- [ ] T012 Implement authorization-before-read and membership recheck, add/pause/resume/remove/replace/reobserve lifecycle and prior-output preservation in `application/subscriber_portfolio/`.
- [ ] T013 Enforce fresh server-confirmed entitlement, active+paused slot consumption, exact positive checkout delta and matching typed `PurchaseAuthorityPort.resolve(context, now)` receipt before checkout creation.
- [ ] T014 Expose portfolio runtime faÃ§ade, pending list/retry/cancel commands and `get_authorized`/`list_authorized` store boundaries in `tools/runtime/subscriber_portfolio.py`.
- [ ] T015 Add 1/2/100 capacity tests, unknown/stale denial, concurrent reservation serialization, paused-slot accounting and browser-return-no-grant regressions in `tests/subscriber_portfolio/`.
- [ ] T016 Add file-backed restart tests proving membership-before-private-load, pending identity without canonical writes, full lifecycle idempotency and old-output preservation in `tests/subscriber_portfolio/`.

## Phase 3: Integration and verification

- [ ] T017 Update `quickstart.md` with exact local callback/client prerequisites, disabled-provider behavior, SQLite restart walkthrough, portfolio lifecycle and entitlement setup for tests.
- [ ] T018 Run focused identity/portfolio tests, relevant existing authorization and identity regressions, formatting/lint/type checks for changed files, and Architecture Guard; report exact results to root for full gates and convergence.
