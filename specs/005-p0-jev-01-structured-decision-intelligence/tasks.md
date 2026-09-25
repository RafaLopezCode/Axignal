# Tasks: P0-JEV-01 Structured Decision Intelligence

**Input**: [spec](spec.md), [plan](plan.md), [research](research.md),
[data model](data-model.md), and [contracts](contracts/decision-contracts.md).

Checked items track this architecture/specification slice, not production
implementation.

## Phase 1: Baseline and evidence

- [x] T001 Verify exact baseline, clean worktree and create dedicated branch
  before editing.
- [x] T002 Review official current TypeSafe docs, Skill, APIs, SDKs, cookbooks,
  models, version guidance and Jev 1.13 jaggedness; distinguish facts from
  unproven assumptions.
- [x] T003 Inspect official Python/JS SDK, official adapter and Skill source;
  record reviewed main SHAs and do not vendor source.
- [x] T004 Inspect selected non-authoritative community patterns without
  installing them or adopting their performance/threshold claims.
- [x] T005 Reconstruct AXIGNAL source and authority boundaries before designing.
- [x] T006 Run focused Graphify queries and reconcile source/test evidence.

## Phase 2: Architecture and contracts

- [x] T007 Install official TypeSafe Skill project-locally and confirm it is
  tooling, not a runtime dependency.
- [x] T008 Specify replaceable structured-evaluator architecture and roles for
  Python, Luna, state compiler, Jev, composer, Knowledge Frontier, Research
  Planner and canonical admission.
- [x] T009 Specify Decision Grammar V0.1, atomic question/primitive/fan-out
  policy, candidate families and version lifecycle.
- [x] T010 Specify minimal state compilation, raw judgment preservation,
  deterministic composition and structured uncertainty boundaries.
- [x] T011 Specify offline Decision Laboratory, metric applicability, controlled
  experiments, replay and explicit grammar promotion.
- [x] T012 Specify all 38 synthetic adversarial case expectations and private,
  security, Admin and failure boundaries.
- [x] T013 Add feature Spec Kit and documentation-map references.

## Phase 3: Deterministic validation and PR

- [ ] T014 Run applicable deterministic gates, Graphify update, docs/reference
  integrity, secret scan and build; record exact results.
- [ ] T015 Review final diff/status for only P0-JEV-01 architecture, research,
  Spec Kit and authorized Skill tooling.
- [ ] T016 Commit, push the dedicated branch and open a PR for CTO review; do
  not merge.

## Deferred; separate authorization required

- [ ] T017 Add a production Jev adapter/SDK, API call, credentials or runtime.
- [ ] T018 Build a persistent Decision Ledger, schema/database, queue,
  Knowledge Frontier integration runtime or production Research Planner.
- [ ] T019 Add live calibration, thresholds, model auto-upgrade or grammar
  self-modification/promotion.
- [ ] T020 Process private/customer data or use a live TypeSafe API experiment.
- [ ] T021 Start follow-on Brain/Luna, Source Router, V3, Admin, subscriber, V2
  or any implementation slice.

Deferred tasks are not part of this PR or P0-JEV-01 architecture completion.
