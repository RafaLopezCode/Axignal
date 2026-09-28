# Feature Specification: P0 Settings / Account Governance Authority

**Feature Branch**: `codex/p0-settings-account-governance`  
**Created**: 2026-09-28  
**Status**: Draft — authority audit complete; runtime implementation blocked  
**Input**: AXIGNAL P0 Settings / Account Governance Authority request

## Scope and authority

Establish the minimum authority boundary for a future Settings surface before
adding account controls. This spec is subordinate to the MASTER Product Model,
Engineering Constitution and accepted ADRs. It records which authorities
actually exist and leaves unsupported account behavior absent.

**Settings is a presentation aggregation surface, not a domain aggregate.** It
may compose separately authorized identity, tenant, membership, presentation,
security, billing and Xeed capabilities only when those authorities exist.
Settings must never write AXIGLAND or make a subscriber claim canonical truth.

The canonical `main` checkout has no product Settings runtime. PR #29 contains
an Account navigation affordance, and the uncommitted local HFX synthetic lab
contains loopback-only locale preview state. Neither is production account
authority. The local HFX checkout is not changed by this slice.

## Problem

Account-like labels can collapse distinct identities: authenticated Principal,
Tenant, Xeed, a future subscriber/workspace, billing identity and global
Organization. The repository has canonical Principal, Tenant,
PrincipalTenantMembership, Xeed and Organization contracts, but no actual
authentication adapter, user profile, Workspace/Subscriber authority, role
model, production persistence, billing provider or Settings application. A UI
control alone cannot authorize a write or make one persistent.

## User scenarios and acceptance

### US1 — Distinguish settings from economic truth (Priority: P1)

A subscriber-facing surface must never suggest that changing an account or
workspace display value edits the Organization AXIGNAL observes.

**Independent Test**: Review every setting's authority row and show that no
subscriber/account mutation can reach Organization, FAXT, Relationship,
AXIGLAND or EvidenceAdmission.

**Acceptance Scenarios**:

1. Given a future permitted user presentation change, when it is saved, then
   Organization identity/name, FAXTs, relationships and AXIGLAND remain
   unchanged and EvidenceAdmission is not invoked.
2. Given a user assertion that canonical Organization data is wrong, when it is
   submitted, then no direct canonical update occurs; any future review path
   must trigger independent reevaluation and evidence admission.

### US2 — Use only implemented account authorities (Priority: P1)

A person opening Settings sees only controls backed by a real source of truth,
server-side authorization and persistence appropriate to the setting.

**Independent Test**: Every rendered control maps to one authority matrix row
with owner, authorized actor, source of truth, write semantics and failure
behavior.

**Acceptance Scenarios**:

1. Given a setting without an implemented authority, when the Settings surface
   is built, then that control is absent or explicitly unavailable; it does not
   save synthetic values or claim success.
2. Given a supplied `user_id`, tenant ID, hidden field or disabled control,
   when a future mutation is requested, then authorization is derived and
   checked server-side from authenticated actor and owned scope.

### US3 — Keep private context references separate from ownership (Priority: P1)

A future subscriber may be able to direct attention toward a canonical
Organization without acquiring that Organization or changing its truth.

**Independent Test**: Rebind/association contracts prove reference semantics,
scope authorization and unchanged shared Organization identity.

**Acceptance Scenarios**:

1. Given a Xeed that references Organization X, when the reference is read
   through an authorized Xeed, then the original global Organization is
   returned without copying it into Tenant state.
2. Given a user saying “my organization is X,” when that input is recorded in
   any future authorized private context, then it implies neither ownership,
   control nor canonical truth; this spec does not authorize changing
   `Xeed.organization_id`.

## Invariants

- `Settings != domain`: Settings is a presentation/application aggregation
  surface, not a domain aggregate.
- `Tenant != Workspace`: Tenant is the current private Xeed isolation and
  ownership boundary; no Workspace authority or alias is established.
- `Account != Tenant` unless future explicit product authority establishes that
  identity. No such authority currently exists.
- `Account != Organization`; `Subscriber identity != canonical Organization`;
  `Billing identity != canonical Organization`; `User profile != canonical
  Organization`.
- `Xeed reference != ownership`: `Xeed.organization_id` references the global
  Organization and grants no ownership, claim or write authority.
- `Settings != domain`: Settings is a presentation/application aggregation
  surface, not a domain aggregate.
- `Tenant != Workspace`: Tenant is the current private Xeed isolation and
  ownership boundary; no Workspace authority or alias is established.
- `Account != Tenant` unless future explicit product authority establishes that
  identity. No such authority currently exists.
- `Account != Organization`; `Subscriber identity != canonical Organization`;
  `Billing identity != canonical Organization`; `User profile != canonical
  Organization`.
- `Xeed reference != ownership`: `Xeed.organization_id` references the global
  Organization and grants no ownership, claim or write authority.
- `USER_CONFIG != CANONICAL_TRUTH`; `ACCOUNT_PROFILE != ORGANIZATION`;
  `WORKSPACE != ORGANIZATION`; `BILLING_IDENTITY != ORGANIZATION`;
  `XEED != ORGANIZATION`; `CLAIM != WRITE`.
- `Organization` remains global and observer-independent. Subscriber input may
  direct attention; only independently investigated evidence admitted through
  `EvidenceAdmission` may alter canonical truth.
- A canonical reference does not confer ownership or truth authority.
- `Settings` aggregates use cases in presentation/application layers; it is not
  a god domain package, arbitrary PATCH endpoint or direct access to domain
  writers.
- The existing Principal–Tenant membership contract grants only its defined
  tenant access semantics. It does not imply `OWNER`, `ADMIN`, or `MEMBER`
  roles, nor authority to change profile, billing or security settings.
- UI locale, knowledge presentation language, source language, canonical IDs,
  predicates, epistemic state and stored truth are separate. Locale changes
  never alter canonical identity or truth.
- User settings do not produce fake AXENT conversation, research events,
  evidence, or “Saved” UI without successful persistence.

## Authority matrix

See [`authority-matrix.md`](authority-matrix.md). It covers identity, account,
workspace, membership, presentation, security, billing, Xeed context and
canonical-world boundaries. All proposed settings currently lack a complete
production write authority; unsupported controls remain absent.

## Locale resolution contract

The presentation target is deterministic:

```text
supported explicit user preference
    > supported browser preference
    > product fallback locale
```

Current code does not provide a production locale authority or durable user
override. Browser detection and `localStorage` in the local synthetic HFX lab
are preview mechanics only. No account persistence, supported locale catalog,
or product fallback locale is selected by this spec. Persist a user override
only after authenticated user scope and a real preference store exist.

## Avatar contract boundary

No avatar field, upload service or object storage exists. This spec authorizes
no upload. If a later authority review permits avatars, they remain user-owned
presentation data, never evidence. That slice must define MIME allowlist, byte
and dimension limits, safe decode/re-encode, generated storage keys, owner
authorization, replacement/deletion, deterministic fallback, alt semantics
and tenant isolation where storage requires it. Do not accept arbitrary SVG
uploads without a reviewed policy.

## Display-name contract boundary

No Principal display-name field or writer exists. If one is later authorized,
it is mutable user presentation data: normalize Unicode, select reasonable
length bounds before implementation, do not require uniqueness, and never use
the value as an identifier or authorization key. It must not alias a Tenant,
Workspace, subscriber organization claim or canonical Organization name.

## Mutation contract

No Settings mutation is implemented. Any later permitted mutation must name its
actor, target, authority, validation/normalization, concurrency behavior where
material, single source of truth, persistence, minimized audit record, side
effects and fail-closed outcomes. Mutations are semantically bounded commands;
unknown fields are rejected. Authorization is server-side. Settings never
exposes an arbitrary object patch. Unknown actor/target, denied scope, invalid
input, unavailable persistence and provider failure must return a truthful
failure without partial or substituted values and without success feedback.
Consequential security, membership, billing and destructive commands require a
version/concurrency policy from their authoritative provider. No optimistic
concurrency policy is selected for nonexistent low-risk preference writes.

## Security, audit and deletion

- Do not store passwords, tokens, MFA secrets or recovery codes in Settings.
  Account-security controls belong to a verified identity provider's secure
  flows if one is adopted.
- No auth or billing provider is selected or implemented. Do not mirror
  provider-owned secrets, payment credentials or sensitive billing state.
- Do not send routine setting changes to AXENT or research. A research hint
  must cross an explicit private-context/attention boundary and cannot bypass
  independent observation or EvidenceAdmission.
- Deletion operations are distinct: clear an avatar, clear locale override,
  leave Tenant, remove membership, delete Principal/account, delete Tenant,
  cancel a subscription, unlink an Organization reference and delete a Xeed.
  No deletion UI is authorized until object/retention/billing/authorization
  consequences are specified. Policy and statutory retention are unresolved.
- Deleting a subscriber/account cannot delete independently admitted AXIGLAND
  knowledge. User/Tenant/private-context deletion and retention remain separate
  policy decisions.
- Sensitive audit records, if later introduced, identify actor/action/target,
  timestamp, request correlation and outcome without copying secret or
  unnecessary personal payloads. No audit store currently exists.

## Required demonstration cases

- **A — Avatar**: If a future user-owned avatar write is authorized, it changes
  only presentation; AXIGLAND, Organization, Xeed truth, FAXT and research stay
  unchanged; EvidenceAdmission is not invoked.
- **B — Workspace display name**: No Workspace name field currently exists.
  If a future field is authorized, it is private/account presentation and
  cannot change canonical Organization name, FAXTs, relationships or AXIGLAND.
- **C — Linked Organization**: `Xeed.organization_id` currently references a
  global Organization. It is not an editable “my company” relation or proof
  that the subscriber owns/controls the Organization.
- **D — Canonical correction**: A challenge never directly edits canonical
  data. Any later correction flow requests independent reevaluation and
  EvidenceAdmission.

These are specification invariants, not tests against nonexistent Settings
mutations.

## Minimum information architecture

Settings remains a secondary presentation surface. It may have a low-emphasis
entry in the account area, consistent with the separately authorized visual
direction, but this slice defines no page/component. Do not render empty
Personal, Workspace, Members, Security, Billing or Xeed sections. Only show a
family when at least one permitted setting exists. The exact visual placement
and icon remain governed by the active canonical Design System and accepted
Golden Master; this slice does not modify either.

## Out of scope

No runtime/UI, authentication provider, profile, avatar upload/storage,
Workspace/Subscriber aggregate, RBAC, invitation/member management, locale
catalog or persistence, billing integration, security console, settings API,
audit store, deletion flow, Organization link writer, Xeed writer,
EvidenceAdmission change, database, migration, deployment, PR #29 or PR #30.

## Doctrine gaps

`DOCTRINE_GAP`: product doctrine does not select or define account/profile
ownership; provider; user/workspace/subscriber identity and cardinality;
workspace naming/branding; member roles; write authority for `Xeed.label` or
`Xeed.organization_id`; locale catalog/fallback and durable owner; avatar
storage/retention; billing provider/identity; account security provider; audit
requirements; deletion, offboarding, retention and legal policy. This spec
does not invent these decisions. CTO review/authority is required before a
runtime slice.

## Success criteria

- Settings is explicitly documented as a presentation/application aggregator,
  never a domain authority.
- Every proposed setting is assigned current status, owner/scope, source/write/
  read authority, persistence, sensitivity, audit, side effects, deletion and
  unknown behavior in the authority matrix.
- Unsupported fields have no runtime write path, fake persistence or success
  state.
- The four demonstration cases preserve the canonical/private boundary.
- No Organization, FAXT, Relationship, EvidenceAdmission or Golden Master
  semantics change.
