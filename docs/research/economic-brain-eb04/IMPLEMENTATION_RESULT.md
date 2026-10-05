# EB-04 — First Economic Vertical E2E implementation result

**Base:** main@5535b14  
**Branch:** cto/eb04-first-economic-vertical  
**Status:** IMPLEMENTED / focused validation complete; full repository validation pending at document creation time.

## Implemented

A reproducible rights-cleared synthetic run now composes:

```
Source Registry
→ governed source acquisition
→ visible HTML representation
→ grounded semantic extraction
→ governed identity binding
→ EvidenceAdmission for canonical capability
→ evidence-backed RichSubjectState
→ multi-axis TypedJudgmentVector
→ deterministic Python interpretation
→ Explainable Basis
→ Human Output with exact support spans
```

The same run also composes EB-01 around every costly/provider-like dispatch:

```
reserve before dispatch
→ execute
→ monotonic elapsed measurement
→ reconcile success/failure
→ preserve known/UNKNOWN cost
→ release reservation
```

The reference aligned case yields:

- capability: OBSERVED with FAXT support;
- independent event/need: DECLARED;
- opportunity state: POTENTIAL;
- attention: WARRANTED_ATTENTION;
- no observed relationship;
- no sale probability;
- exact evidence/source/representation/span refs in Human Output.

## Safe degradation proven

Deterministic tests cover:

- missing material context → UNKNOWN / INVESTIGATE;
- evaluator outage → NOT_ANSWERABLE / UNKNOWN with evidence preserved;
- material contradiction → no positive presentation;
- source budget exhausted → blocked before second fetch;
- ambiguous identity/excerpt → fail closed;
- rights UNKNOWN/PROHIBITED → acquisition authorization rejected;
- unknown cost preserves known lower bound and never becomes zero;
- same authorized inputs → same semantic output and replay refs.

## Composition fixes

EB-04 exposed a real EB-01 issue: reaching a source-specific limit blocked later work that consumed zero sources. `GovernedExecutionController.reserve()` now distinguishes global exhausted constraints from resource-specific reservation limits.

EB-04 also strengthens:

- semantically extracted EconomicObservation must retain verifiable representation/span;
- material supplier contradiction blocks positive opportunity attention;
- Human Output exports exact support span metadata.

## Deliberately not implemented

- No live JEV/Luna calls. EB-05 owns provider comparison and real usage/cost.
- No production crawling or scheduler.
- No continuous reobservation worker.
- No subscriber UI/browser integration.
- No production deployment.
- No graph/vector database or agent framework.
- No CRM/lead scoring/sale probability.

## Validation so far

- Core EB-04 + execution budget + governed dispatch: **53 passed**.
- Two E2E suites after reconciliation: **24 passed**.
- Focused Ruff: PASS.
- Focused mypy for the new dispatch/orchestrator modules: PASS.

## Final branch validation

- Full repository pytest: **1226 passed in 92.89s** with basetemp outside the repository.
- Focused EB-04 / governed-dispatch / execution-budget suite: **53 passed**.
- Reconciled E2E suites: **24 passed**.
- Ruff check: PASS.
- Mypy: **Success, no issues found in 268 source files**.
- Architecture Guard: PASS, no violations.
- AXIGNAL Governance: PASS for architecture, deps, docs, Graphify, hygiene, generated-data, spec and terminology.
- Graphify structural graph refreshed after code changes: **11,971 nodes / 30,204 edges**.
- Graphify freshness check: PASS.
- git diff --check: PASS.

A final exact-state format/check/gate pass is executed after this evidence update and immediately before commit. Integration, GitHub push and CI remain E4-19.
