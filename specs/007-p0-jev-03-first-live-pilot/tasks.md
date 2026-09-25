# Tasks: P0-JEV-03 First Live Jev Empirical Pilot

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/pilot-run.md](contracts/pilot-run.md), [quickstart.md](quickstart.md)

## Phase 1: Foundation and contract

- [x] T001 [P] [US1] Create the sequential P0-JEV-03 Spec Kit feature and verify exact base in `specs/007-p0-jev-03-first-live-pilot/`.
- [x] T002 [P] [US1] Refresh official SDK, response, model, retry, and pricing facts in `specs/007-p0-jev-03-first-live-pilot/research.md`.
- [x] T003 [US1] Pin smoke selection and explicit safe local credential loading in `experiments/decision_lab/pilot.py`.

## Phase 2: Smoke boundary (US1, Priority P1)

- [x] T004 [US1] Add typed answer whitelist to the experimental adapter in `experiments/decision_lab/providers/typesafe.py`.
- [x] T005 [US1] Implement one-request smoke artifact and digest-gated eligibility in `experiments/decision_lab/pilot.py`.
- [x] T006 [US1] Execute exactly one live smoke request and inspect the result and offline replay in `docs/research/p0-jev-03/`.
- [x] T007 [US1] Create a smoke gate record only if every required smoke condition passes in `docs/research/p0-jev-03/smoke-gate.json`.

## Phase 3: Controlled experiment (US2, Priority P2)

- [x] T008 [US2] Preflight the unchanged complete experiment and execute it once after the passing smoke gate using `experiments/decision_lab/pilot.py`.
- [x] T009 [US2] Store the complete immutable live result at `docs/research/p0-jev-03/claim-wording-ab-result.json`.
- [x] T010 [US2] Preserve typed source fields and avoid synthesizing provider-reported usage in `experiments/decision_lab/providers/typesafe.py`.

## Phase 4: Offline replay and reporting (US3, Priority P3)

- [x] T011 [US3] Recompute deterministic composition, supported metrics, critical regressions, and predeclared outcome in `experiments/decision_lab/cli.py` during offline replay.
- [x] T012 [US3] Replay the smoke and controlled artifacts without credential or network access into `docs/research/p0-jev-03/`.
- [x] T013 [US3] Complete the evidence-labeled report in `docs/research/p0-jev-03/empirical-report.md`.
- [ ] T014 [US3] Run required offline and repository gates; verify secret, production, CI, migration, and canonical-write exclusions.
- [ ] T015 [US3] Open a new unmerged PR for CTO review and provide the required evidence ledger.

## Dependency Order

`T001-T005` → `T006` → `T007` only when the smoke passes → `T008-T009` → `T012-T015`.
If smoke fails, record and report it, leave the controlled experiment unrun, and stop for CTO review.
