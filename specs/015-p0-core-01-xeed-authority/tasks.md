# Tasks: P0-CORE-01 Canonical Xeed Authority

**Input**: spec.md, plan.md
**Prerequisites**: Reconciliation complete; CTO decisions in P0-CORE-01 resume order

## Phase 1: Contract Tests First

- [x] T001 [US1] Define identity and ownership acceptance matrix in spec/data model.
- [x] T002 [US1] Add tests for distinct IDs, Organization reference, same-world multi-Tenant Xeeds, label collision/mutation, and germination-state separation from authorization/truth.
- [x] T003 [US2] Add memory authority test fixture and authorized-read security matrix.
- [x] T004 [US2] Verify membership-before-Xeed lookup and non-enumerating external contract.

## Phase 2: Domain Authority

- [x] T005 [US1] Add distinct canonical ID types and type Organization.id as OrganizationId.
- [x] T006 [US1] Add minimal Principal, Tenant, membership and Xeed domain records.
- [x] T007 [US1] Add domain exports and identity validation.

## Phase 3: Application Authorized Read

- [x] T008 [US2] Add trusted request context, read ports, internal error codes and AuthorizedXeed result.
- [x] T009 [US2] Implement membership-first Xeed authorization and ownership check.
- [x] T010 [US2] Add application package to build/type-check configuration and enforce domain dependency direction.

## Phase 4: Architecture and Verification

- [x] T011 [US1, US2] Record implemented and explicitly absent authority in ADR-0018 and architecture overview.
- [ ] T012 [US1, US2] Run format, lint, types, all tests, architecture, governance, Graphify and secret scan.
- [ ] T013 [US1, US2] Review every diff path against CTO scope; commit/push and create an unmerged PR only if all required gates pass.

## Execution Order

T002–T004 precede implementation. T005–T007 establish domain authority.
T008–T009 consume that authority. T010–T011 enforce and document boundaries.
T012 is required before commit/PR. The PR remains unmerged.
