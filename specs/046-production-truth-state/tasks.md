# Tasks: Production Truth-State Preservation for EB-04

**Input**: Approved design documents in `specs/046-production-truth-state/`
**Architecture review**: Root approved exact source-authority/predicate mappings on 2026-10-06.
**Baseline**: Root confirmed 1341 passed before implementation.
**Scope**: Production edit only in `application/economic_discovery/first_vertical_e2e.py`; test edits only in `tests/economic_discovery/test_first_vertical_e2e*.py`.

## Phase 1: Setup

**Purpose**: Freeze the approved boundary before implementation.

- [x] T001 Confirm the root baseline is recorded as 1341 passed and no production edits precede the baseline.

## Phase 2: User Story 1 â€” Preserve official-web declarations (Priority: P1)

**Goal**: A capability/product stated on an official website remains `DECLARED` through exact canonical support, including an extracted representation with unresolved visibility.

**Independent Test**: The official-web EB-04 case proves both `EconomicObservation` and its exact FAXT carry `DECLARED`, preserve evidence/span/currentness/rights, and retain `TextSurface.EXTRACTED_TEXT` when visibility is unresolved.

- [x] T002 [US1] Add a failing EB-04 regression for an exact official-web capability declaration with unresolved visual visibility in `tests/economic_discovery/test_first_vertical_e2e.py`; assert both states are `DECLARED` and exact source support/surface remain intact.
- [x] T003 [US1] Implement the versioned exact `(SourceAuthority.OFFICIAL_WEB, predicate)` mapping for the existing EvidenceAdmission-approved capability/product predicate family in `application/economic_discovery/first_vertical_e2e.py`; pass the resolved state explicitly to FAXT and `EconomicObservation` without changing global defaults.

## Phase 3: User Story 2 â€” Preserve a registry observation and reject unsupported pairs (Priority: P1)

**Goal**: Registry evidence can support an observed legal-identity proposition, while all unapproved authority/predicate pairs fail closed without an `OBSERVED` fallback.

**Independent Test**: Exact admitted registry evidence for `identity`, `legal_identity`, or `registration` yields the same `OBSERVED` state on FAXT and economic observation; mismatched and unsupported pairs cannot materialize canonical support.

- [x] T004 [US2] Add failing cases for exact admitted `REGISTRY` legal-identity evidence and unsupported authority/predicate combinations in `tests/economic_discovery/test_first_vertical_e2e.py`.
- [x] T005 [US2] Add the versioned exact `(SourceAuthority.REGISTRY, identity|legal_identity|registration)` mapping to `application/economic_discovery/first_vertical_e2e.py`; fail canonical requests closed where no approved pair exists, while retaining existing `EvidenceAdmission` checks.

## Phase 4: User Story 3 â€” Preserve the existing uncertainty and mismatch boundary (Priority: P1)

**Goal**: Missing/unsupported evidence remains noncanonical and unknown/absent-as-unknown, and existing exact evidence mismatches cannot be promoted by the new policy.

**Independent Test**: Missing candidates remain absent-as-unknown; state/currentness/evidence/identity mismatch tests still reject; focused EB-04 and evidence contracts pass.

- [x] T006 [US3] Reuse existing exact-evidence/identity/state-transfer adversarial regressions and verify missing material stays unknown without FAXT.
- [x] T007 [US3] Run the focused economic discovery suite and existing evidence, FAXT, identity/representation contracts; record pass/fail output and confirm the global `FAXT.create` default and Organization/subscriber materialization files are untouched.

## Phase 5: Polish & cross-cutting validation

**Purpose**: Confirm deterministic quality before rootâ€™s full-gate convergence.

- [x] T008 Run `ruff format --check`, `ruff check`, and `mypy` with the approved cache location; run `git diff --check`; report the exact changed-file set to root for full repository gates.

## Dependencies & Execution Order

- T001 is complete and is the baseline prerequisite.
- T002 â†’ T003 form the official-web declaration red/green slice.
- T004 â†’ T005 form the registry/unsupported-pair red/green slice; they reuse T003â€™s policy transfer but must remain independently discriminative.
- T006 depends on T003/T005; T007 depends on all story tests. T008 follows focused regression.
- No tasks may edit outside the approved production file and `test_first_vertical_e2e*.py` test glob. Root owns full gates and final convergence.

## Parallel Opportunities

- No implementation tasks are parallelizable: the production policy and the focused fixture tests share the same behavioral boundary.
- T002 and T004 may be authored concurrently only if separate agents own distinct test files; do not run concurrent code writers.

## Implementation Strategy

1. Complete the official-web test first and observe its failure.
2. Implement the exact declared mapping and explicit state transfer; verify green.
3. Add and verify the registry and unsupported-pair cases; extend only the same deterministic policy.
4. Run existing mismatch and missing-context cases, then the full focused economic/evidence regression set.
5. Stop for rootâ€™s full gates and review; do not deploy or commit.

## Task-format validation

All eight tasks have checkboxes, sequential IDs, precise paths, and story labels for story work. All eight are complete. Root reviewed the implementation and ran the final repository gates: 1,404 tests passed. Convergence found no additional gap within this bounded feature; no tasks were appended. Deployment and subscriber runtime remain outside scope.
