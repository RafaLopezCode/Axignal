# AO-24A extension — persistent authorized organization attention

CURRENT_TASK = AO-24A

## Specify / clarify

Human authorization, 2026-10-04: develop adding organizations after onboarding;
Admin internal use requires no checkout. No second real organization is requested
now; verify controlled cases without seeding demo organizations in the real path.

Keep FR-30 acquisition/Prime/Basis/Xignal/Narrative/Today and its existing SQLite
read-model store. Add an internal attention inventory, not a second Brain or
canonical organization editor. Existing AXIGNAL self-observation remains valid.

An unknown submitted name/domain is attention only. Persist IDENTITY_UNRESOLVED;
do not create Organization, FAXT or Xignal from those inputs. Resolution consumes
already-canonical candidates and approved source bindings supplied by the server
catalog, never browser roles, IDs, plan counts or arbitrary target-policy grants.
The source catalog is configuration of existing authority, not identity evidence
admission. A catalog entry requires a canonical identity authority reference;
this feature does not create that referenced identity decision or automate it.

## Plan / constitution and architecture review

- Extend FirstProofStore in place with append-only attention attempts and private
  active-focus selection per authenticated Admin principal; no new database.
- Parameterize FR-30 by a resolved canonical target. Legacy plant stays allowlisted
  AXIGNAL. New add consumes exact server catalog name/domain binding; ambiguity
  stays unresolved. Existing resolver is reused. No URL-derived canonical IDs.
- Extend existing /api/xeeds for strict add/select/reobserve commands; add
  GET /api/organizations with XEEDS_READ. Commands require RESEARCH_OPERATE.
  Direct legacy standalone compatibility cannot access new internal commands.
- Inventory exposes approved selectable targets and human attempt states, not
  private operational data. Selection cannot access another workspace. Revoked
  catalog targets cannot be observed or selected anew. One internal workspace is
  FR-30's existing tenant, not a general commercial multi-tenant entitlement.
- GET /api/subscriber-context resolves persisted selection per principal.
  Reobservation appends evidence/projection; duplicates return the existing focus.
- Shared organization dialog performs add/change/retry using real contracts,
  holds pending/error states while retaining the current reading, and reloads
  persisted success. Remount Axent on scope revision and bind requests to Xeed;
  reject stale scope responses and clear transient conversation on focus change.

Constitution review: attention cannot provide conclusions; source gate/SSRF and
credential rules retained; no billing in internal flow; no tenant inference from
frontend; no canonical writer; reuse currentness/narrative unchanged. Graphify
query examined FirstProofService, Xeed authorization and CustomerZero composition.

## HTTP contract

GET /api/organizations returns accessMode INTERNAL_ADMIN, canObserve (runtime
grant), selectedId, organizations (request/focus id, canonical name only when
resolved, otherwise requestedLabel, targetUri, state, projectionContextId), and
available canonical targets (name,targetUri). Never return sessions or finance.

POST /api/xeeds accepts either legacy {label,targetUri}, or exactly:

- {action:"add",name,targetUri}: idempotent attention request; resolved target
  follows FR-30; unresolved identity202; insufficient evidence422 remains persisted.
- {action:"select",id}: persisted authorized selection; no acquisition.
- {action:"reobserve",id}: new run for selected/registered target, preserves history.

Reject extra fields, unsafe targets, arbitrary canonical IDs, billing/role inputs,
wrong methods and cross-origin browser writes. Failure does not erase active focus.
No completed charge or invoice is implied by any response.

## Tasks / acceptance

- [x] Store migration, catalog resolution and append-only focus inventory.
- [x] Existing runtime endpoints and per-principal persisted selection wired.
- [x] Shared organization dialog and evidence/Axent scope isolation.
- [x] Deterministic tests: add, duplicate, ambiguous/unresolved, insufficient
  evidence, authorization/revocation, persistence/restart, isolation and no billing.
- [x] Browser desktop/mobile, add/switch/retry with controlled governed runtime;
  default real runtime retains only AXIGNAL as requested by human.
- [x] Full gates, convergence evidence, roadmap/appendix/audit reconciled.

External commercial identity/onboarding/checkout and autonomous admission of new
canonical organization identities are separate contracts, not asserted complete
by this internal observation-inventory slice.
