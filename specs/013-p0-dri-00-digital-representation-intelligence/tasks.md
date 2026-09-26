# Tasks: P0-DRI-00 Digital Representation Intelligence

## Specification and clarifications

- [x] T001 Read original CTO order and addendum; preserve branch, base, PR #18,
  no-runtime and no-provider constraints.
- [x] T002 Freeze four DRI families and public experience/review epistemic
  boundaries.
- [x] T003 Freeze measurement, score, temporal, privacy, rights, deletion,
  deduplication and EOI interaction clarifications.

## Plan and architecture review

- [x] T004 Inspect Graphify and relevant MASTER, Constitution, ADR,
  architecture, UX and communication boundaries.
- [x] T005 Review condition-bound instruments, public/private channel split,
  platform/source authority and currentness requirements.
- [x] T006 Approve documentation-only future architecture and record P0-DRI-01
  contract/sensor-economics scope without starting it.

## Documentation convergence

- [x] T007 Extend the single MASTER in place and update its pinned hash.
- [x] T008 Create ADR-0014/0015 and update ADR and product indexes.
- [x] T009 Update Constitution, AGENTS, architecture terminology/overview,
  subscriber experience, communication and graph-design guidance.
- [x] T010 Create the product spec and integrated product-slice README.
- [x] T011 Create spec, clarifications, plan, architecture review, tasks,
  requirements checklist and prior-art record.
- [x] T012 Document candidate sources and prior art without code copying,
  vendor lock-in or unverified rights claims.
- [x] T013 Run cross-document doctrine, privacy, score, rights, epistemic and
  scope consistency audit; fix findings.
- [x] T018 Canonize public reputation as the fourth DRI family and Public
  Experience Intelligence as an internal DRI capability, not another product.
- [x] T019 Define ReviewObservation, ExperienceTheme, ExperienceSignal,
  ReputationState, ReputationChange and derived ReputationGap semantics.
- [x] T020 Preserve reviewer-claim, platform-rating, verification, sentiment,
  response and evaluator boundaries; Jev does not create a final score.
- [x] T021 Require deterministic, versioned, reproducible, decomposable and
  traceable reputation metrics with visible sample, coverage and uncertainty.
- [x] T022 Prohibit naive cross-platform rating comparability and preserve
  source populations and source-native metrics.
- [x] T023 Propagate source deletion/removal to currentness and prevent
  duplicate or syndicated observations from double counting.
- [x] T024 Permit public experience to initiate AXENT/EOI research without
  automatically creating a FAXT, DemandSignal or opportunity.
- [x] T025 Preserve rights, privacy, reviewer minimization, tenant isolation,
  currentness and nonautomatic raw-text retention.
- [x] T026 Record review/reputation candidate sensor families without
  unverified rights claims, provider integration or downloaded data.
- [x] T027 Add the required review acceptance cases and Ask AXENT/product
  experience semantics to the existing P0-DRI-00 slice.

## Quality gates and delivery

- [x] T014 Run frozen sync, Ruff, mypy, full pytest, Architecture Guard,
  governance, diff check and Graphify refresh/diagnostics; record exceptions.
  `uv sync --frozen`, Ruff format/check, mypy, pytest (154), Architecture Guard,
  diff check and Graphify update/diagnose passed. Governance passed architecture,
  deps, docs, graphify, spec and terminology; hygiene and no-generated-data were
  blocked only by the already-present local `.env`, which was not read or
  touched.
- [x] T015 Verify documentation-only scope, PR #18 exact state/head, main base,
  no runtime/provider/sensor calls and no `.env` access. Origin main is
  `77958603792af600cb9f16bc1c12e118dc3a73cf` and contains PR #19 head
  `438a85aa97715927c10ae7958ca66921c9a494ad`; PR #18 remains open at
  `e877547f27a17f945df40ae546533fa68cf3ee79`. Scope audit found only the
  authorized documentation, doctrine and Spec Kit paths; no runtime, provider,
  sensor, dependency, migration or deployment changes/calls occurred.
- [x] T016 Commit the slice on the authorized branch, push, open one PR against
  `main` without merging, and verify remote CI for that head. PR #20 is open at
  `https://github.com/RafaLopezCode/Axignal/pull/20`; the published doctrine
  head `a33b7ca1e2f5b7129739b47e39efef524c1c5b9a` passed remote run
  `36244274408` (deterministic validation, Graphify structural checks and
  secret scanning all successful; Sourcery review skipped). The final
  task-ledger closeout remains subject to CI on its pushed head.
- [x] T017 Return the complete original and addendum CTO ledgers in the final
  task response; stop before P0-DRI-01.
