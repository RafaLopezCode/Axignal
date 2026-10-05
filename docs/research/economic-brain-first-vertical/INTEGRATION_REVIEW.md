# Economic Brain first vertical — integration review

Date: 2026-10-05. Integration verdict: **READY**.

READY means safe integration of the internal, offline reference vertical onto
`main@b489156` in `codex/economic-brain-integration`. It does not mean production
readiness, live evaluator authorization, deployment or completion of the Economic
Brain product E2E milestone.

## Reviewed revisions and authority

- Target/base: `b4891561228a93b77a7605f2d45e998bba60d176`.
- Candidate: `a1c3519d8b403ac41edbf8b13bf2570fef68ffb3`, from
  `codex/economic-brain-e2e`.
- Common ancestor: `441b4d04bb7b27e81f66cef039d31662717b1bdb`.
- Inspected both commit summaries, candidate source/spec/test contents,
  main's admission/budget diff and tests, and `441b4d0..b489156` overlap.
- Authority: current MASTER §§14–21, 46, 53, 55–56; Constitution; accepted
  ADR-0012/0013/0047/0072/0074/0075/0076/0077; architecture Overview,
  Terminology, Atlas and current-state ledger; feature 038; unified Economic
  Brain execution roadmap. Architecture/Constitution review is recorded in
  `specs/038-economic-brain-first-vertical/architecture-review.md`.

The changed file sets of the two commits are disjoint. The candidate is
architecturally compatible and useful as the narrow EB-04 reference slice:
independently sourced capability and announced need become six independent
dimensions, deterministic interpretation, Explainable Basis and Human Output.
The semantic conflict was its older canonical fixture preparation, not a text
merge conflict. Production prerequisites and roadmap order remain in force.

## Accepted and rejected parts of a1c3519

| Part | Disposition and reason |
| --- | --- |
| `brain_contracts.py` extension | ACCEPTED. Optional selected choice/replay fields preserve existing callers and strengthen non-answerable metadata validation. |
| `economic_state.py` | ACCEPTED as internal read-only composition of already normalized, rights-cleared public inputs. Exact datum/basis bindings, existing FAXT matching, state completeness, contradictions and temporal validity are retained. It grants no acquisition, rights or truth authority. |
| `first_vertical.py` | ACCEPTED. Independent supplier/customer roles, bounded functional alignment, deterministic reach/window/qualification, answerability before evaluator dispatch, negative/UNKNOWN retention and versioned Python composition. Output cannot assert OBSERVED. |
| `economic_output.py` | ACCEPTED as an internal immutable read model. Meaning, independent states, limits, per-axis basis and source evidence survive. No subscriber route or permission is added. |
| Synthetic corpus and 29 original cases | ACCEPTED with the admission preparation corrected and six adversarial integration cases added. Assertions are retained; no tests are relaxed. |
| Feature spec/plan/tasks and implementation report | ACCEPTED with current-main integration annotations, architecture review and this report. Older counts remain clearly historical. |
| Canonical fixture lacking subject binding/GroundedClaim | REJECTED and replaced. Current admission must independently authorize the exact tuple and claim. |
| Older report as current integration evidence | REJECTED. All integration gate results below were rerun on this worktree. |
| Production/product E2E interpretation of this slice | NOT ACCEPTED. No live acquisition, product surface, durable orchestration, measured evaluator quality or deployment is demonstrated. |

The four application Python files are identical to the reviewed candidate.
Compatibility changes are confined to fixture preparation, added regressions and
governance/review documentation. Nothing from main's truth/cost hardening is
overwritten.

## Reconciliation with b489156

Applied `git cherry-pick --no-commit a1c3519` on the authorized integration
branch. No textual conflicts occurred. Kept EvidenceAdmission, execution-budget
policy/state/controller, main's existing tests, roadmap, MASTER, Constitution,
ADRs, dependency lock and gates unchanged.

Before correction, `uv run --offline pytest
tests/economic_discovery/test_first_vertical.py -x -q` failed at the first fixture:
**1 error in 0.61s**. Admission reported `canonical claim evidence has no
observation subject binding`. This is the correct fail-closed behavior.

The synthetic capability now includes its observation subject, literal subject
and predicate mentions, exact object/value and exact supporting excerpt in a
versioned GroundedClaim. It still uses `EvidenceAdmission.admit_claim` followed
by `FAXT.create` during input preparation only. Reasoning never calls either.

Six added cases establish that:

- wrong subject, predicate or object/value cannot be admitted from the same
  claim, and cannot reuse the original valid decision to materialize a FAXT;
- missing observation-subject binding or structured grounding fails closed;
- an admitted capability cannot be attached to another economic subject.

## Safety and semantic inspection

- **Canonical truth:** no writer/admission import or call in the reasoning or
  Human Output modules. OBSERVED/CORROBORATED inputs require matching existing
  FAXT; subject matching is checked by the state wrapper. The end-to-end test
  forbids admission, FAXT creation and observed-relationship creation after
  preparation. Final states are POTENTIAL/UNKNOWN; no relationship is created.
- **Uncertainty and attention:** missing, non-current or materially conflicting
  core context blocks positive interpretation before judgment. UNKNOWN remains
  null/UNKNOWN in output. Explicit negative judgments and closed windows retain
  candidates without manufacturing a false opportunity classification. Supplier
  and customer can coexist; absence of a role does not mean FALSE.
- **Confidence/commercial meaning:** no universal score, confidence threshold,
  lead or sale probability. Raw distributions/confidence are retained only when
  provided under the existing capability contract; they do not drive attention
  or appear as user confidence. Price, capacity, incumbent and commercial access
  remain unassessed even in a POTENTIAL output.
- **Tenant boundaries:** no tenant-owned Organization, private truth graph or
  persistence is introduced. The public-input precondition is an upstream
  requirement, not an authorization granted by a rights-reference string.
  Subscriber/private evidence consumption is not wired to this model.
- **Evaluator coupling:** existing StructuredEvaluatorPort/evaluate_structured
  validates capability profile, options and exact request fingerprints/replay.
  Choice-only and distribution-capable fake evaluators produce compatible
  interpretation. Failure, invalid provenance and malformed distributions
  degrade safely. No provider SDK/dependency or paid call is introduced.
- **Provenance/currentness:** every supplied datum retains source/evidence refs,
  time, representation fingerprint, epistemic/temporal state, rights reference
  and optional extraction fingerprint. Per-axis basis includes relevant
  contradictions; full basis preserves every supplied observation. Another
  consumption time requires reevaluation, preserving the original inputs.
  Exact synthetic replay is tested. Supplied hashes/references do not verify
  external source bytes or prove completeness beyond the supplied state.

## Validation actually run

Environment: Windows PowerShell, CPython 3.12.11, frozen development environment;
17 packages installed. All test/reasoning runs were offline and used fake
evaluators. No live model or source was called.

For `uv run --offline` commands, `UV_CACHE_DIR` was set to
`Join-Path $env:TEMP 'axignal-economic-brain-integration-uv'`. The first plain
`uv sync --frozen` attempt could not write the default uv cache. Rerunning the
same frozen install with approved cache access succeeded. The initial Git
index-lock permission failure was likewise retried with access to this
worktree's Git metadata. Neither retry modified dependencies or gates.

The initial concurrent governance run passed before mypy finished writing its
cache. A later pre-commit governance run failed with exit 1:
`FAIL hygiene — large file (>2MB) should not be committed: .mypy_cache/3.11/cache.4.db`.
The generated cache was moved with PowerShell `Move-Item` after verifying its
resolved source was exactly this worktree's `.mypy_cache`. Its new directory is
`C:\Users\usuario\AppData\Local\Temp\axignal-economic-brain-integration-mypy-96b3af5d5e604f3e9f7cd2039d0a669b`.
The final governance check below runs with that artifact outside the repository.
No ignore rule, file-size gate or code was changed to accommodate it. Future
mypy runs can use `--cache-dir` pointing outside the worktree.

| Command | Exact result |
| --- | --- |
| `uv sync --frozen` (successful retry) | PASS, exit 0; 17 packages installed. |
| `uv run --offline pytest tests/economic_discovery/test_first_vertical.py -q` | PASS, exit 0; **35 passed in 0.34s**. |
| `uv run --offline pytest tests/economic_discovery tests/contracts tests/source_representation -q` | PASS, exit 0; **731 passed in 56.18s**. Includes all vertical, shared dimension/evaluator, admission, budget, UNKNOWN/POTENTIAL and rich-state contracts. |
| `uv run --offline pytest tests/economic_discovery/test_first_vertical.py -k end_to_end -s -q` | PASS, exit 0; **1 passed, 34 deselected in 0.20s**; printed POTENTIAL/WARRANTED_ATTENTION with six exact per-axis evidence paths and commercial limits. |
| `uv run --offline pytest --basetemp $taskTestTempPath -q` | PASS, exit 0; **1095 passed in 86.42s (0:01:26)**. Includes affected subscriber narrative/projection, germination and architecture regressions. |
| `uv run --offline ruff format --check .` | PASS, exit 0; **852 files already formatted**; covers every changed Python file. |
| `uv run --offline ruff check .` | PASS, exit 0; **All checks passed!** |
| `uv run --offline mypy` | PASS, exit 0; **no issues found in 263 source files**. |
| `uv run --offline architecture-guard --root .` | PASS, exit 0; **Architecture Guard: OK (no violations)**. |
| `uv run --offline axignal-governance` (initial and final corrected runs) | PASS, exit 0; architecture, deps, docs, graphify, hygiene, no-generated-data, spec and terminology. Intermediate generated-cache failure and correction are recorded above. Graphify subcheck is a no-op when its CLI is absent. |
| `uv run --offline python docs/audits/brain-2026-10-04/reproduce_evidence_and_budget.py` | PASS, exit 0; wrong tuple rejected (`wrong_tuple_admitted=false`); cost sequence **7 → 7 incomplete → 8 incomplete**, `correct_total_is_unknown=true`; neither probe persisted data. |
| `git diff --check HEAD` | PASS, exit 0; no whitespace errors. |
| `git diff b489156 -- domain/evidence/admission.py application/economic_discovery/execution_budget.py tests/contracts/test_evidence_admission.py tests/economic_discovery/test_execution_budget.py` | Empty; main's firewalls and their tests retained byte-for-byte. All other b489156-changed files are outside the integration diff too. |
| `graphify query 'Economic vertical evidence admission and subscriber projection'` | UNAVAILABLE; executable not on PATH, no `graphify-out/graph.json`. Source/contract review performed. |
| `graphify update .` | UNAVAILABLE; command not found. No gate or Graphify configuration was changed. |

`$taskTestTempPath` for the full suite was the fresh external directory
`C:\Users\usuario\AppData\Local\Temp\axignal-economic-brain-integration-0213987867ab473ab2b0b57167ca4e4b`.
No deliberately invalid pytest fixtures were placed inside the repository.

Governance and whitespace checks also cover the finalized integration report
and spec annotations in the final pre-commit verification. No Python changed
after the successful gates above.

## Remaining production blockers

1. EB-01 governed run envelope: pre-dispatch reservations/budgets, monotonic
   deadlines, complete attempts, retries/cancellation/leases/idempotency and
   observable usage/cost reconciliation. This fake-only entry point is not a
   production provider-dispatch path.
2. EB-02/03 governed identity, normalization and exact representation/extraction
   spans; metadata-first source-rights, scope, retention and public reuse policy.
   Current wrappers validate supplied bindings, not independent external material.
3. Independently adjudicated rights-cleared economic corpus, failure/abstention
   quality, cost/latency measurements, and separately authorized provider pilot
   behind cognition ModelRouter/CognitiveProvider. Synthetic structural tests
   establish no real-world accuracy or commercial outcome.
4. Durable result/raw replay and Explainable Basis storage, considered-evidence
   ledger, capability/project identities beyond one pair of subjects, broader
   dimensions including relationship state, incremental dependency-selective
   reevaluation, absence/withdrawal/conflict history and shared observation
   scheduling without double counting.
5. Authorized subscriber consumption and exact narrative resolution before
   payload access; currentness refresh, Human First comprehension validation and
   real Panorama/Evidence/AXENT integration. No browser/Golden Master delta exists
   in this backend slice. Product E2E, measured economics, load/recovery/operability
   and any production deployment remain separate authorization and evidence.
6. Restore structural Graphify tooling and refresh the derived graph when
   available. Required Architecture Guard/governance have independently passed.

## Verdict and branch handling

**READY** to commit the reconciled internal reference implementation on
`codex/economic-brain-integration`. All deterministic gates run above pass;
current-main truth/cost authority is preserved. Production blockers remain
explicit and are not reclassified as completed roadmap work.

Only integration-owned files are staged for this commit. The supplied untracked
`CODEX_INTEGRATION_TASK.md` is excluded. No merge, push or deployment is performed;
`main` remains at `b489156` and the candidate branch remains at `a1c3519`.
