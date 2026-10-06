# Feature Specification: Subscriber Runtime Identity, Portfolio and Observation Authority

**Feature Branch**: `codex/production-closure`
**Created**: 2026-10-06
**Status**: Draft â€” architecture reviewed; implementation awaits Spec Kit prerequisites
**Input**: Production E2E for subscriber registration and persistent observation of 1, 2 or 100 Organizations, including trusted identity, private Tenant authority, purchased capacity and portfolio lifecycle.

## Purpose

Let a subscriber register through a supported identity provider, receive one private AXIGNAL Tenant, purchase observation capacity, and maintain a private portfolio of public Organizations. Each portfolio entry directs independent Brain observation and produces inspectable Organization and Signal outputs. It does not create tenant-owned economic facts or give the subscriber authority to edit AXIGLAND.

The end-to-end journey begins when a subscriber registers Organizations. AXIGNAL's Customer Zero remains internal self-use under Admin authority and cannot substitute for subscriber authentication, membership, entitlement or portfolio tests.

## Authority and approved decisions

- The MASTER and Constitution remain controlling: there is one global AXIGLAND; Organization and admitted evidence are never tenant-owned; user input directs attention and never determines canonical conclusions.
- ADR-0018 remains the private authority: Tenant owns private Observation Focuses, binary Principalâ€“Tenant membership authorizes access, and each Focus references one global Organization.
- ADR-0021 remains the only path from an authorized Focus to its global Organization. A raw Organization, Focus or Tenant identifier does not authorize a read.
- A new subscriber's first verified registration atomically provisions an AXIGNAL Principal, one initial Tenant, its binary membership, and the exact external-identity binding. This creates no entitlement and grants no observation capacity by itself.
- The data model may represent a Principal with multiple memberships, but v1 self-service creates one initial Tenant and makes no additional multi-Tenant product promise. No membership roles, invitations or payer cardinality are introduced.
- Google OpenID Connect is the first configured sign-in path. ChatGPT sign-in may be enabled only through OpenAI's official Sign in with ChatGPT mechanism when AXIGNAL has a provisioned client and access; until then it is explicitly unavailable. Codex sessions, OpenAI API credentials and provider email claims are never subscriber identity.
- Identity bindings use exact issuer and subject, with the configured client identifier included when the provider's subject is client-scoped. Email, profile text, provider organization and browser-supplied IDs never link accounts.
- Tenant is the capacity-consumption scope only when the separately governed entitlement authority says so. Tenant is not a payer, legal customer or Organization.
- A confirmed entitlement snapshot is authoritative for capacity. Browser return/callback is correlation only. Unknown or stale capacity blocks any add that would exceed confirmed capacity. Active, paused and currently reserved Focus slots consume capacity.
- Public directories and registries may supply candidate evidence and locators; they are not canonical Organization records. A canonical Organization must already resolve globally or pass the separately governed identity/bootstrap authority. An unresolved target remains pending and cannot create a Focus or economic claim.

## User Scenarios & Testing

### User Story 1 â€” Register securely and resume a subscriber session (Priority: P1)

As a new subscriber, I need to establish a secure AXIGNAL identity through a supported sign-in path so that my private portfolio is isolated and recoverable across sessions.

**Why this priority**: Every subscriber action depends on a verified actor, durable internal identity, private Tenant and revocable session.

**Independent Test**: Complete a provider callback against a deterministic local OIDC authority, restart the runtime, resolve the issued session to the same Principal and initial Tenant, then prove replay, expiry, invalid issuer/client/nonce/signature and revoked session do not authorize.

**Acceptance Scenarios**:

1. **Given** a complete enabled provider configuration, **When** the subscriber begins sign-in, **Then** AXIGNAL creates a browser-bound, expiring, single-use authorization transaction using Authorization Code with PKCE and returns only the authorization URL and opaque transaction token to the HTTP boundary.
2. **Given** a valid callback for the exact configured provider/client/redirect and unconsumed transaction, **When** the callback completes, **Then** AXIGNAL verifies the identity and atomically creates one Principal, one initial Tenant, one binary membership, one client-scoped external binding and one revocable session.
3. **Given** the same exact issuer/subject/client registers twice or callbacks race, **When** both complete, **Then** only one subscriber authority set exists and both successful resolutions identify the same Principal/Tenant.
4. **Given** matching email text but different verified external identities, **When** either identity is used, **Then** AXIGNAL does not link or merge Principals.
5. **Given** ChatGPT sign-in is not provisioned or enabled, **When** it is requested, **Then** the user sees a clear unavailable state and no fake provider flow or local bypass is used.

### User Story 2 â€” Add Organizations within confirmed capacity (Priority: P1)

As a subscriber, I need to add 1, 2 or 100 Organizations to my portfolio so AXIGNAL can observe each independently and return evidence-backed outputs.

**Why this priority**: The portfolio is the subscriber's durable way to direct AXIGNAL's attention and demonstrate the core OaaS value.

**Independent Test**: With a durable subscriber store reopened after process restart and confirmed capacity of 100, add 100 globally resolved Organizations idempotently, verify 100 private Focuses reference the expected canonical Organization IDs, then inspect an independently produced observation/output without mutating Organization truth.

**Acceptance Scenarios**:

1. **Given** an authenticated Principal, current membership and confirmed capacity, **When** an Organization is added, **Then** the request is resolved through global Organization authority, exactly one private Focus is created for the Tenant, and an independent observation is triggered.
2. **Given** the entered URL/name matches only a public directory candidate, **When** canonical identity remains unresolved, **Then** the request stays pending, creates no canonical Organization or Focus, and reports that resolution is still required.
3. **Given** confirmed current capacity is exhausted, **When** an authorized purchase owner adds another Organization, **Then** AXIGNAL requests checkout for the exact additional quantity and creates no active Focus until billing confirms the resulting entitlement. If capacity is unknown/stale or purchase authority is false/unknown, no checkout request or Focus is created.
4. **Given** concurrent or repeated add requests for the same Tenant/Organization or idempotency key, **When** they race or replay, **Then** no duplicate Focus or observation job is created and reserved capacity cannot exceed confirmed capacity.
5. **Given** a Tenant with sufficient confirmed capacity, **When** it adds a portfolio of 1, 2 or 100 Organizations, **Then** each entry remains isolated to that Tenant while shared Organizations still resolve to the same global object.

### User Story 3 â€” Manage a private Organization portfolio safely (Priority: P1)

As a subscriber, I need to pause, resume, remove, replace and reobserve an Organization so my portfolio reflects current intent without erasing shared economic knowledge.

**Why this priority**: Persistent observation must remain under subscriber control while preserving AXIGNAL's independent and shared truth.

**Independent Test**: Exercise every transition against a file-backed store across restart; assert membership before private record loading, verify paused entries consume capacity, failed replacement/reobservation preserves the previous successful output, and removed entries do not delete canonical Organizations or evidence.

**Acceptance Scenarios**:

1. **Given** an active Focus and current membership, **When** the subscriber pauses it, **Then** future scheduled observation stops, existing inspectable output remains available, and the slot remains counted against capacity.
2. **Given** a paused Focus and current entitlement, **When** the subscriber resumes it, **Then** AXIGNAL restores observation only after rechecking currentness and capacity.
3. **Given** an active or paused Focus, **When** the subscriber removes it, **Then** it disappears from the active portfolio and no new observation is scheduled, while global Organization/evidence/history remain independent of that private removal.
4. **Given** a replacement target whose global identity is unresolved or capacity is not current, **When** replacement is requested, **Then** the existing Focus remains active and selected until an authorized atomic swap can occur.
5. **Given** a valid replacement target, **When** replacement completes, **Then** one authorized transaction activates the replacement and removes the previous Focus from active use without transiently exceeding capacity.
6. **Given** an active Focus with a previous successful output, **When** reobservation is requested, **Then** AXIGNAL records one new run; the prior output remains available until the new run passes its own readiness/evidence gates.
7. **Given** an unauthenticated, expired, revoked or non-member Principal, **When** any portfolio command/read is attempted, **Then** authorization fails before the private portfolio record is loaded.

## Edge Cases

- OIDC state, browser transaction token, PKCE verifier, nonce, callback code or session is replayed, expired, mismatched, revoked or used with a disabled client.
- Callback arrives after a runtime restart; if the exact one-time transaction cannot be recovered safely, restart sign-in rather than authorizing from partial state.
- Same email with a different issuer, subject or configured client remains a distinct identity unless both identities are explicitly linked through a separately approved verified flow.
- Duplicate external binding, orphan Principal, corrupted store, transaction failure or partial bootstrap never returns an authenticated subscriber.
- Membership is absent/revoked, Tenant identifier is spoofed, Focus belongs to another Tenant, or authorization storage is unavailable.
- Canonical Organization lookup is missing, ambiguous, stale or available only as an untrusted public-directory candidate.
- Entitlement is unknown, stale, partially paid, below requested capacity, or changes during a concurrent add/replace.
- Checkout browser return precedes a verified billing update; capacity remains unchanged until the billing authority confirms it.
- A paused Focus consumes capacity. A removed Focus frees capacity but cannot erase AXIGLAND facts.
- A replacement target fails resolution or first observation; the existing Focus and last successful projection remain intact.
- A reobservation fails, returns insufficient evidence or is interrupted; the previous successful output remains intact and the new run is reported truthfully.
- A subscriber with 100 Organizations repeats, races or retries add; uniqueness, capacity reservation and run idempotency remain enforced.

## Functional Requirements

- **FR-001**: Authentication MUST use an enabled, explicitly configured OIDC provider; callback verification MUST use a maintained OIDC/JWT validation library and validate configured issuer, client/audience, signing keys, time claims, nonce, state, PKCE and exact redirect.
- **FR-002**: Authorization transactions MUST be browser-bound, expiring and atomically single-use. Tokens, codes, verifiers, session secrets and sensitive provider responses MUST NOT appear in logs or exception representations.
- **FR-003**: The system MUST resolve an exact verified issuer/subject and configured client scope to exactly one existing or atomically provisioned AXIGNAL Principal. Email/profile/provider claims MUST NOT be an identity key or permission.
- **FR-004**: A first valid subscriber registration MUST atomically provision Principal, one initial Tenant, binary membership, identity binding and a durable revocable session; it MUST NOT grant observation capacity automatically.
- **FR-005**: Every portfolio read or mutation MUST establish Principal existence and current Principalâ€“Tenant membership before loading private portfolio, Focus or projection data; mutation transactions MUST recheck the authority to prevent races.
- **FR-006**: Each private Observation Focus MUST belong to exactly one Tenant and reference one globally resolved Organization ID. No user-supplied ID, registry row or tenant portfolio record may create or mutate canonical Organization, evidence, FAXT, Relationship, Signal or economic truth.
- **FR-007**: The public portfolio API MUST use Organization/Signal/Observation Focus product language; legacy Xeed identifiers may remain internal only.
- **FR-008**: Capacity MUST come from a current server-side `EntitlementSnapshot` for the governed consumption scope. Capacity absent/unknown/stale MUST NOT authorize an add beyond known allowance; active and paused Focuses consume capacity.
- **FR-009**: If requested additions exceed confirmed current capacity and the principal is explicitly authorized to purchase for that Tenant, the system MUST request checkout for the exact additional quantity and MUST create no active Focus until trusted billing authority confirms the updated entitlement. Unknown/stale capacity or unknown/denied purchase authority MUST block checkout creation. Browser checkout return is not confirmation.
- **FR-010**: Add, pause, resume, remove, replace and reobserve MUST be idempotent and durable across runtime restart. Concurrent requests MUST NOT duplicate a Focus/run or exceed confirmed capacity.
- **FR-011**: Pause MUST stop future observation while retaining the existing output and consuming its capacity slot. Resume MUST recheck capacity/currentness before new work.
- **FR-012**: Remove MUST stop future private observation and exclude the Focus from the active portfolio without deleting shared canonical knowledge. Any longer-term private-history retention/erasure policy remains a separate authority.
- **FR-013**: Replace MUST preserve the previous active Focus until the new canonical Organization resolves and an atomic authorized swap can complete within confirmed capacity.
- **FR-014**: Reobserve MUST preserve the latest successful human output until the new run independently meets output/readiness criteria; failure or interruption MUST not be presented as success.
- **FR-015**: Google OIDC MUST be the first supported subscriber sign-in path. ChatGPT sign-in MAY be enabled only through official Sign in with ChatGPT OIDC after AXIGNAL obtains a registered, authorized client; absent that configuration, it MUST be explicitly unavailable.
- **FR-016**: Tenant MAY be passed as an entitlement-consumption scope but MUST NOT be treated as payer, legal customer, Organization or subscriber-company identity.
- **FR-017**: Before creating a checkout request, the system MUST resolve explicit purchase authority for `(principal_id, tenant_id)` through a billing-owned port; it MUST NOT infer purchase authority from membership or Tenant ownership.
- **FR-017**: Durable stores MUST enforce uniqueness, referential integrity and transactional bootstrap/portfolio capacity invariants; corrupt or unavailable authority MUST fail closed.

## Key Entities

- **Verified provider identity**: Exact issuer and subject under a validated OIDC client configuration; optional configured client scope disambiguates pairwise subjects.
- **Principal**: AXIGNAL's durable internal actor identifier; never a provider identifier.
- **Tenant**: The private isolation and Focus ownership boundary; not an Organization or payer.
- **Membership**: Binary Principalâ€“Tenant authority checked for every private operation.
- **Session**: Revocable, expiring server-side authority issued only after validated identity and Principal/Tenant resolution.
- **Entitlement snapshot**: Server-confirmed maximum observation capacity for a governed consumption scope, with currentness and confirmation time.
- **Portfolio entry / Observation Focus**: Private Tenant-owned pointer to one globally resolved Organization with lifecycle and run references; contains no duplicate Organization truth.
- **Organization resolution**: Governed result distinguishing a global canonical Organization from an unresolved candidate or pending request.
- **Observation run**: One idempotent request to independently observe or reobserve a Focus, with explicit progress/outcome and access to its successful output.
- **Checkout request**: Correlation for the exact additional capacity requested; not itself an entitlement or authorization.

## Success Criteria

- **SC-001**: A new subscriber completes an enabled Google registration and can resume the same Principal/Tenant session after runtime restart.
- **SC-002**: Invalid, expired, replayed, wrong-issuer/client, bad-signature, wrong-nonce or revoked-session cases never authorize.
- **SC-003**: A file-backed integration suite proves private authorization-before-load and continuity across restart for identity, Tenant, membership, sessions and Focus lifecycle.
- **SC-004**: The system creates exactly 1, 2 or 100 private Focuses for corresponding confirmed capacity, with no duplicates under retries or concurrent requests.
- **SC-005**: A request above confirmed capacity creates a checkout request for the exact increment but no additional active Focus until server-confirmed entitlement changes.
- **SC-006**: Pause/resume/remove/replace/reobserve semantics survive process restart; a failed replacement or reobservation preserves the previously successful portfolio/output.
- **SC-007**: Two Tenants can independently observe the same canonical Organization ID without cross-reading private portfolio state or duplicating the Organization.
- **SC-008**: No subscriber action changes canonical Organization or admitted economic truth; unresolved identity remains explicit and unknown.
- **SC-009**: ChatGPT sign-in is either backed by AXIGNAL's configured official SIWC client or shown unavailable; no API key or Codex session is accepted as subscriber login.

## Assumptions and Deferred Policy

- A subscriber registration creates one initial Principal/Tenant/membership. Additional Tenant creation, member roles, invitations and multi-member administration are outside v1.
- Billing separately confirms the capacity snapshot. Payer identity/cardinality and the mapping between payer and Tenant remain separate billing authority questions.
- If public information does not resolve a canonical Organization, the request remains pending and can direct governed research; it does not invent an Organization or negative evidence.
- Remove immediately withdraws private observation and active portfolio visibility. It does not define legal erasure or the retention period for minimum audit/history metadata.
- Durable SQLite in the configured runtime data directory proves local single-runtime persistence, not high availability, backup/restore, multi-host consistency or production operational readiness.
- API and frontend composition are provided by the existing runtime owner; this feature supplies application and persistence authorities without editing subscriber UI.

## Out of Scope

- Editing Organization facts, creating tenant-owned Organizations or direct canonical writes from user input.
- Membership roles, invitations, teams, multiple initial Tenants, payer inference, billing policy or entitlement grants on registration.
- Unverified provider claims, matching-email account linking, OpenAI API-key authentication, Codex identity, or a locally fabricated ChatGPT OAuth endpoint.
- Hard deletion/erasure policy, provider-independent legal retention policy, high-availability database design, backups/restore proof, production deployment or production-readiness declarations.
- Changes to `apps/web`, Admin/Customer Zero, economic reasoning implementation, billing implementation or MASTER doctrine.
