# Implementation Plan: P0-JEV Reconciliation

## Objective

Add an additive, deterministic V-next experimental contract path following ADR-0011. Preserve all V0.1 and P0-JEV-03 history. No provider or canonical authority integration.

## Affected systems

- `experiments/decision_lab/`: contracts, compiler stages, answerability, composition, audit records and experiment validity.
- `experiments/decision_lab/grammar/vnext/`, `corpus/vnext/`, and `experiments/vnext/`: immutable proposal artifacts.
- `tests/experiments/`: offline contract and boundary tests.
- `docs/adr/`, `docs/architecture/`, `specs/008-p0-jev-reconciliation/`: decision and implementation contract.

## Sequence

1. Preserve historical PR #14 and #15 as merge commits; verify the Phase-A hash and merge ancestry.
2. Add typed family contracts and split state assembly, normalization, validation, serialization and hashing.
3. Add deterministic answerability, primitive validation, uncertainty-preserving composition and record/quality eligibility rules.
4. Add V-next grammar and synthetic evidence-bearing corpus with evaluator-only targets.
5. Lock the development/held-out state-sufficiency preregistration and implement a fail-closed validity gate.
6. Validate deterministic tests, typing, format/lint, Architecture Guard, governance, Graphify, references and secret boundary.
7. Open one reconciliation PR and leave it unmerged for CTO review.

## Risks and rollback

The major risk is overclaiming synthetic or structurally answerable fixtures as model-quality evidence. Document the limits, exclude unanswerable/no-target cases, and keep `LIVE_EXPERIMENT_ELIGIBLE=NO` until independent golden provenance exists. Roll back by removing the additive V-next files/docs; do not touch historical artifacts.

## Validation checklist

- [x] Family contracts and answerability negative fixtures are deterministic.
- [x] V0.1/P0-JEV-03 history and Phase-A hash remain unchanged.
- [x] No provider or canonical-writer dependency is reachable from V-next modules.
- [x] Development and held-out IDs are disjoint and locked.
- [x] Full repository deterministic gates recorded in the PR evidence.
