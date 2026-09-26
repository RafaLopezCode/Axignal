# Tasks: P1-04 Claim Evidence Answer Space

## Phase 1: Specification and clarification

- [x] T001 Specify the claim/evidence answer-space closure slice and out-of-scope boundaries.
- [x] T002 Clarify empty evidence reachability, class boundaries, compound-case precedence, and version identity.

## Phase 2: Plan and architecture review

- [x] T003 Plan additive V-next.2 registration with unchanged V-next.1 and shared state shape.
- [x] T004 Review MASTER, Constitution, ADR-0011, V0.2 and graph dependencies; approve bounded repair.

## Phase 3: Implementation

- [x] T005 Add standalone V-next.2 question and distinct DecisionContract/fingerprint.
- [x] T006 Add offline V-next.1 preservation, V-next.2 semantic mapping, answerability, and version-binding tests.
- [x] T007 Assess public business-corpus candidates and record license, domain fit, textual evidence, label independence, and natural/procedural separation without creating gold.

## Phase 4: Verification and convergence

- [x] T008 Run full deterministic repository gates, graph maintenance, no-provider audit, and diff audit. `pytest=154 passed`; Ruff, mypy, Architecture Guard and diff check pass. Governance reports only the pre-existing local ignored `.env` hygiene/no-generated-data violation; it was not read, staged, moved, or removed.
- [x] T009 Converge against specification, plan, tasks, and doctrine; open an unmerged repair PR only if all blocking gates pass. PR #17 remains open and unmerged; remote CI run 36232517361 passed for head `e2a94162a74b6bed2b2687309a978001aeb7c5e6`.

## Phase 5: Convergence

- [x] No additional implementation gaps found during final convergence beyond verification evidence and PR creation tracked in T008–T009.
