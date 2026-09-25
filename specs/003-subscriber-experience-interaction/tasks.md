# Tasks: Subscriber Experience Interaction Contracts

**Input**: [Spec](spec.md), [plan](plan.md), [research](research.md),
[conceptual model](data-model.md), and [contract catalogue](contracts/interaction-contracts.md)

This bounded P0 slice is documentation/contract work only. The checkboxes
below track completion of the specification slice, not future product runtime.

## Phase 1: Authority and specification

- [x] T001 Reconcile candidate product specification against repository
  authorities and record no-conflict result in `research.md`.
- [x] T002 Preserve stable candidate path and proposed/pre-implementation
  metadata in `docs/product/AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md`.
- [x] T003 Normalize mutable GPT-6 Luna operational facts from official sources
  without changing architecture policy.
- [x] T004 Specify journeys, requirements, edge cases and measurable outcomes
  in `spec.md`.

## Phase 2: Contract design

- [x] T005 Define architecture boundaries and non-goals in `plan.md`.
- [x] T006 Define conceptual projection model without persistence schemas in
  `data-model.md`.
- [x] T007 Specify all 15 interaction contracts and failure/unknown behavior in
  `contracts/interaction-contracts.md`.
- [x] T008 Add documentation review walkthrough in `quickstart.md`.
- [x] T009 Add the subscriber specification and proposed contract reference to
  `docs/README.md`.

## Phase 3: Documentation-slice validation

- [x] T010 Review traceability from requirements to contracts and verify all
  authority/runtime non-goals remain explicit.
- [x] T011 Run repository deterministic validation and inspect final diff for
  runtime, dependency, schema, migration or out-of-scope changes.

## Deferred, requires separate authorization

- [ ] T012 Implement Subscriber Projection and germination read models.
- [ ] T013 Implement Today/materiality and Evolution temporal projections.
- [ ] T014 Implement Evidence, Graph/Map and PATHX subscriber surfaces.
- [ ] T015 Implement Ask AXENT context, response and research escalation.
- [ ] T016 Implement authorization enforcement, portable Xeed and Product MCP.
- [ ] T017 Implement provider-policy execution and cognitive/UX telemetry.
- [ ] T018 Build/prototype production UX and conduct UX validation.

No deferred task is part of this PR or authorized by the current phase.
