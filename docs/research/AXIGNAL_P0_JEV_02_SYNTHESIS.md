# AXIGNAL P0-JEV-02 Decision Laboratory Synthesis

**Version:** 0.1.0
**Status:** EXPERIMENTAL TOOLING; LIVE EXPERIMENTS NOT RUN
**Reviewed:** 2026-09-25
**Authority:** Research evidence only. No production grammar, evaluator,
threshold, model or composition policy is promoted.

## Purpose and result boundary

P0-JEV-02 implements an offline-first laboratory under
`experiments/decision_lab/`. It contains a synthetic Golden Corpus V0.1 with 42
cases (14 each for claim/evidence support, entity alignment and economic
relationship), an executable and content-locked grammar, a minimal state
compiler, controlled experiment plans, typed judgment preservation,
descriptive metrics, comparison/report helpers, and create-only result files.
Recorded answers are contract fixtures explicitly labeled as not Jev output.

No live evaluator request was made. The credential-presence check returned
absent; there are no usage, latency, model-resolution, or invoice observations.
Therefore no pattern can be called better or worse, no AXIGNAL calibration
claim can be made, and all three planned experiments remain **INCONCLUSIVE /
NOT RUN**. A fixture replay proves only deterministic serialization and
contract behavior.

## Evidence categories

### OFFICIAL_VENDOR_GUIDANCE

Current TypeSafe guidance describes Choice for selection, Score for ordered
dimensions, and Noul for probability of a yes condition. Confidence is not an
overall workflow correctness or permission score; Noul has no separate
confidence field. Vendor materials also describe independent parallel
questions, self-consistency experiments, state minimization, and version
pinning. Those are experiment candidates, not AXIGNAL policy.

### AXIGNAL_HYPOTHESES

- Claim support wording with explicit partial, conflicting, wrong-entity and
  no-evidence outcomes may be more inspectable than a short binary wording.
- Temporal and provenance fields may help stale/duplicate/conflicting evidence
  cases; irrelevant context may distract.
- Relationship presence/type/time/contradiction decomposition may expose
  failure causes compared with a compound judgment, at a higher question cost.

### AXIGNAL_EXPERIMENTAL_RESULT

None. No live call or empirically scored candidate comparison exists in this
slice.

### AXIGNAL_VALIDATED_POLICY

None. No grammar candidate, threshold, state contract, model version, or
composition rule was promoted.

## Required research questions — present evidence

| Question | P0-JEV-02 finding |
|---|---|
| Which question patterns worked or failed? | Unknown; live experiments not run. |
| Which state fields helped or hurt? | Unknown; no observed variant comparison. |
| Was atomic decomposition useful? | Unknown; only a predeclared controlled plan exists. |
| Was speculative fan-out useful? | Unknown; no performance/quality/cost observation. |
| Where did Choice, Noul or Score work well? | Unknown; fixture coverage tests shape, not quality. |
| What uncertainty patterns were useful? | Unknown; no target-domain distributions observed. |
| What Jev jaggedness was observed/reproduced? | None observed or reproduced. Vendor-documented risks remain hypotheses to test. |
| What differed from expectation? | No live expectation comparison was possible. |
| What should Python own? | Exact identifiers, normalization, versioning, state compilation, budgets, comparison, deterministic rules and authority. This follows architecture and determinism, not a Jev bakeoff. |
| What should Jev own? | No validated allocation yet; only narrow semantic judgments are candidates for evaluation. |
| What should Luna own? | No P0-JEV-02 evidence. Open-ended reasoning remains outside this slice. |
| Which families are ready? | None are production-ready. The three synthetic families are ready for a bounded empirical pilot after review. |
| What should Python Intelligence consume? | Potentially the versioned corpus/grammar/result contracts and future measured failure taxonomy; no performance policy. |

## Controlled experiment plans

1. **claim-wording-ab** — Compare short and criteria-explicit Choice wording on
   identical synthetic claim cases.
2. **minimal-state-ablation** — Compare full and temporal/provenance-ablated
   states using the same question version.
3. **relationship-atomic-decomposition** — Compare a compound relationship
   Choice with independent presence/type/time/contradiction questions; preserve
   request/question counts in the declared budget.

They are predeclared hypotheses, not completed runs. Repetition, evaluator
version comparisons, primitive comparisons, fan-out economics and cost per
useful judgment remain future experimental dimensions. Grammar V0.1 is the
baseline; CES.SUPPORT.v2 is a wording candidate within the experimental
grammar. No grammar evolution loop was executed and no production promotion is
permitted.

## Operational and safety findings

- Default commands and all CI tests are offline. A live request requires the
  explicit `--live` flag, declared experiment, pinned `jev-1.13.0`, an
  environment credential, a passing preflight budget, sequential execution,
  and zero SDK retries.
- The official Python SDK is optional and lab-only. No dependency enters
  production dependencies or the product wheel. The official JS SDK was
  reviewed and not selected.
- Raw answer forms, distributions, defined confidence, resolved model when
  available, and usage are retained. Missing values remain missing. SDK
  exceptions are mapped to safe categories and never become semantic negatives.
- Results use create-only file writes and a manifest digest. There is no cache;
  cache key semantics are therefore not applicable. No automatic grammar or
  policy promotion exists.
- No private/customer data, production database, migration, deployment, source
  acquisition or production runtime was used or changed.
- Future Admin observability should be considered only through later governed
  work and should preserve evaluator/model version, grammar version, family,
  latency, usage, failure category, uncertainty, research escalation, cost and
  regression status. Raw/private evidence should not be exposed by default.

## Limitations and next authorized research

Synthetic cases test implementation invariants and deliberately known
construction. They cannot establish real-world semantic validity, accuracy,
calibration, language performance, repeatability, useful abstention, or cost.
Before a live pilot, review the PR and verify current credential/budget policy;
then run only a small predeclared synthetic smoke/pilot and preserve every
failure/inconclusive result. Any larger study needs a separate information-value
and power rationale. This report does not start that follow-on work.
