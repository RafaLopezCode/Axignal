# Tasks: P0-JEV-02 Decision Laboratory

**Input**: Design documents in `specs/006-p0-jev-02-decision-laboratory/`
**Tests**: Required by the CTO order; all tests deterministic and offline.

## Phase 1: Setup and research

- [x] T001 Record current TypeSafe documentation delta and SDK decision in `docs/research/AXIGNAL_P0_JEV_02_TYPESAFE_REFRESH.md`.
- [x] T002 Create lab package and synthetic corpus/grammar/experiment data paths under `experiments/decision_lab/`.
- [x] T003 Add the official SDK only to the optional `decision-lab-live` dependency group and update `uv.lock`.

## Phase 2: Foundational contracts

- [x] T004 [P] Implement corpus, grammar, experiment, result, label, and failure validation in `experiments/decision_lab/validation.py`.
- [x] T005 [P] Implement normalized typed judgments and evaluator protocol in `experiments/decision_lab/models.py` and `judgments.py`.
- [x] T006 Implement deterministic state compiler and fingerprint in `experiments/decision_lab/state.py`.
- [x] T007 Add narrow Architecture Guard rules/tests for the lab-only SDK adapter, lab-to-production imports, and production-to-lab imports.

## Phase 3: User Story 1 — Corpus and grammar (P1)

- [x] T008 Build the 42-case provenance-aware synthetic corpus in `experiments/decision_lab/corpus/v0.1/cases.json`.
- [x] T009 Add immutable grammar V0.1 and claim wording candidates in `experiments/decision_lab/grammar/v0.1/grammar.json`.
- [x] T010 Add experiment definitions for claim wording A/B, state ablation, and atomic decomposition with declared budgets.
- [x] T011 Add corpus/grammar/budget validation CLI commands in `experiments/decision_lab/cli.py`.
- [x] T012 [P] Add deterministic corpus, invalid-label, grammar identity, and question-version tests under `tests/experiments/`.

## Phase 4: User Story 2 — Offline evaluator, replay, metrics, and reports (P1)

- [x] T013 Implement recorded-response evaluator and fixture parsing without any fake Jev-success fallback.
- [x] T014 Implement versioned deterministic experimental composition; never import/call canonical admission.
- [x] T015 Implement class-specific metrics, confusion matrices, calibration infrastructure flags, error taxonomy, and critical regression detection.
- [x] T016 Implement immutable result manifests, create-only writes, replay, comparisons, and human-readable reports.
- [x] T017 Add focused unit tests for state fingerprints, missing/false/zero, typed judgment normalization, failure mapping, replay, budget, metrics, regression, immutability, and no-write boundaries.
- [x] T018 Add fixture-only recorded responses and label them explicitly as contract fixtures, not observed Jev outputs.

## Phase 5: User Story 3 — Explicit live TypeSafe evaluator (P2)

- [x] T019 Implement the isolated official SDK adapter under `experiments/decision_lab/providers/typesafe.py` with lazy import, safe error classification, zero retries, and no body logging.
- [x] T020 Implement explicit `--live` opt-in, environment-key presence validation, model pin, request/question/byte/cost preflight, sequential calls, and safe usage capture.
- [x] T021 Add mocked SDK transport tests proving no network in offline modes, one-attempt behavior, metadata preservation, and no exception/credential serialization.
- [x] T022 Inspect credential presence without displaying its value. It was absent; no live call was made (`NOT_RUN_CREDENTIAL_UNAVAILABLE`).

## Phase 6: Synthesis, verification, and review

- [x] T023 Produce `docs/research/AXIGNAL_P0_JEV_02_SYNTHESIS.md`, separating vendor facts, hypotheses, observed results, and validated policy.
- [x] T024 Run repository/lab gates, Graphify, and build. Local `gitleaks` was unavailable; the existing GitHub secret-scan job remains enabled for PR CI.
- [x] T025 Verify changed-file scope, optional-only dependency placement, no migrations/runtime side effects, and clean worktree before commit.
- [x] T026 Commit only P0-JEV-02 scope, push `experiment/p0-jev-02-decision-lab`, and open a PR without merging.
