# Tasks: P0-ADMIN-01 Observability Contracts

**Input**: [Spec](spec.md), [plan](plan.md), [research](research.md),
[conceptual model](data-model.md), and
[contract catalogue](contracts/observability-contracts.md).

This bounded slice specifies observability before runtime. Checked items track
completion of this documentation slice only; they do not track or claim product
implementation.

## Phase 1: Authority and repository evidence

- [x] T001 Verify the approved baseline, clean worktree, branch and remote main
  before editing.
- [x] T002 Reconcile the Admin proposal against MASTER, Constitution, all
  accepted ADRs, Atlas, Brain, source, subscriber, V2/V3 and communication
  authorities; record status evidence in `research.md`.
- [x] T003 Inspect source and deterministic-test evidence and distinguish
  implemented/partial/specification/accepted/open states.

## Phase 2: Proposed contract architecture

- [x] T004 Reconcile Admin product status, AXENT naming, V2/V3 observability,
  Admin MCP, metric lineage and private-content boundaries.
- [x] T005 Specify the Admin observability architecture reference without
  selecting transport, persistence, vendor or runtime.
- [x] T006 Specify all 26 observability contracts and first-runtime emission
  classes in `contracts/observability-contracts.md`.
- [x] T007 Define conceptual data meanings without adding storage schemas,
  migrations or API wire formats.
- [x] T008 Integrate architecture and feature references into the documentation
  map.

## Phase 3: Documentation-slice validation

- [ ] T009 Run repository deterministic validation, Graphify checks, broken
  reference checks and secret scan; inspect the final change boundary.
- [ ] T010 Commit only authorized P0-ADMIN-01 documentation, push the dedicated
  branch and open a PR for CTO review.

## Deferred; requires separate authorization

- [ ] T011 Implement Admin event/observation ingestion, metric computation or
  Admin read models.
- [ ] T012 Implement Admin UI, API, exports, Admin MCP or operational commands.
- [ ] T013 Implement telemetry, event transport, storage, queues, dashboards or
  provider/billing integrations.
- [ ] T014 Implement Brain, JEV, GPT-6 Luna, source acquisition, Xeed
  germination, V2, V3, private connectors or report generation.

No deferred item is part of this PR or authorized by P0-ADMIN-01.
