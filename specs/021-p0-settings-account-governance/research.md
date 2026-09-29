# P0 Settings Authority Research

## Reentry and isolation evidence

- Canonical branch at reentry: `origin/main` =
  `26f298425d88c67551cd432ab35da99d975c6a7a`; new isolated branch is
  `codex/p0-settings-account-governance` at that base.
- The primary `D:\AXIGNAL\Axignal` checkout was already on PR #29's feature
  branch and had uncommitted changes in app, spec and test files. None were
  edited, staged, reset or committed.
- A different managed worktree contained unrelated dirty doctrine work; it was
  left untouched. The Design Director worktree/PR #30 was left untouched.
- GitHub reported PR #29 OPEN (`863b5db49c40b00c3854f8fb02d2e47670c6136a`) and
  PR #30 OPEN (`ce293bfed25c8a8b6a327731544e904a9e40ac67`), both based on the
  reentry main SHA and mergeable at inspection. No merge/deploy was performed.
- Graphify was rebuilt locally without LLM extraction. Its directed path query
  from `PrincipalTenantMembership` to `AuthorizedXeedReader` found no path;
  inspect the source protocols/tests for actual authority. Graphify is not truth
  authority.

## Authority map

| Authority | Evidence | Finding for Settings |
|---|---|---|
| MASTER §2.1 / §2.3 | `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` | AXIGNAL models the economic world; reevaluation, not company-profile editing. |
| MASTER §5 | Same file, epistemic neutrality and Epistemic Firewall | User input directs attention, never conclusions or direct canonical state. |
| MASTER §6.1 | Same file; diagram explicitly distinguishes User account/subscription/preferences from Organization identity/capabilities/products/markets/evidence/relationships | Account and Organization are distinct; the diagram does not create their schemas, writers or storage. |
| MASTER §6.3 / §7.3 | Same file | Private classifications/perspectives do not modify AXIGLAND; one Organization may be observed by many Xignals. |
| MASTER §15.1–15.4 | Same file | Claim is not write; FAXT truth and epistemic semantics remain governed. |
| Constitution V, VI, XIV, XIX–XXI | `.specify/memory/constitution.md` | XIGNAL is observation; admitted evidence alone changes canonical truth; private state and authorization scope remain separate. |
| ADR-0003, ADR-0004, ADR-0008 | `docs/adr/` | No direct profile editing, ownership/claiming or CRM/workflow drift. |
| ADR-0016 | `docs/adr/ADR-0016-human-first-cognitive-interface.md` | Human-facing meaning does not authorize UI, schema or persistence. |
| ADR-0017 | `docs/adr/ADR-0017-private-cognitive-continuity-and-context-boundaries.md` | Context, retention/deletion and tenant/client scopes are separate; no auth provider, database or UI is selected. |
| ADR-0018 | `docs/adr/ADR-0018-canonical-xeed-authority.md` | Tenant is private Xeed boundary; Principal–Tenant membership is access authority; Principal identity comes from a future adapter; production auth/persistence and Workspace authority absent. |
| ADR-0021 | `docs/adr/ADR-0021-authorized-xeed-organization-context-read.md` | Authorized Xeed can read its original global Organization; it does not authorize profile or reference mutation. |
| Subscriber spec §FR-015 and deferred items | `specs/003-subscriber-experience-interaction/spec.md` | Subscriber output is scoped; concrete storage, auth, retention and schemas deliberately remain unselected. |
| HFX-00 subscriber boundary | `specs/018-p0-hfx-00-golden-master-boundary/spec.md` | Test/dev in-memory authority exists; no production authentication, persistence or writer. Golden Master is presentation authority, not a settings schema. |
| Design System | `docs/design/DESIGN_SYSTEM.md` | Current web boundary has no product runtime/component framework; locale/layout guidance separates UI locale from knowledge/source language but selects no account locale store. |

## Current implementation inventory

- `domain/identity.py` defines `PrincipalId`, `TenantId`, `XeedId`, and
  `OrganizationId` as separate string-backed identities.
- `domain/tenancy/model.py` defines `Principal`, `Tenant`, and
  `PrincipalTenantMembership`. It defines no name, email, avatar, role, billing
  or user-preference fields.
- `application/xeed_access/reader.py` consumes a
  `TrustedRequestContext` that explicitly does not authenticate. It resolves a
  Principal, verifies membership, checks Xeed tenant ownership and returns
  `AuthorizedXeed`.
- `tests/support/xeed_authority.py` is deterministic in-memory test/dev
  authority. No application membership writer/store was found.
- `domain/xeed/model.py` contains `id`, `tenant_id`, `organization_id` and an
  optional presentation `label`. It is immutable; no production repository or
  settings update command exists.
- `domain/organizations/model.py` is global, has no account/tenant/owner
  fields, and says explicitly that observer identity is separate.
- `pyproject.toml` has no runtime dependencies. Repository source has no auth,
  billing, avatar/object-storage or database client. `apps/web/` on `main`
  contains design-system primitives and an isolated specimen, not a subscriber
  Settings app.
- The PR #29 branch contains an Account navigation label. In the dirty local
  HFX checkout, locale preview reads `navigator.languages` and a synthetic
  loopback `localStorage` key. That path is guarded as test/demo state and does
  not establish account preference persistence. The PR branch and its dirty
  checkout were not changed.
- Admin product documentation describes future observability of customers and
  billing, not a selected billing provider or subscriber mutation authority.

## Findings

1. The MASTER justifies keeping user/account/presentation distinct from global
   Organization, but does not specify account ownership, mutable fields or
   sources of truth.
2. The only present member boundary is a test/dev-backed binary
   Principal–Tenant membership contract. There is no verified actor adapter,
   role/capability model or mutation policy.
3. No candidate profile, locale, avatar, workspace, auth, billing, membership
   management, audit or deletion setting has a complete production source of
   truth, write authority, persistence and failure contract.
4. `Xeed.organization_id` is an existing global Organization reference read
   through `AuthorizedXeed`; it is not a subscriber-owned Organization profile
   or permission to rebind the Xeed.
5. Therefore no runtime vertical slice or contract test against Settings
   mutations is currently justified. A spec and matrices are the minimum
   truthful output; implementation waits for authority decisions.

