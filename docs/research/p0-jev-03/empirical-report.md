# P0-JEV-03 First Live Jev Empirical Pilot

> **THIS IS SYNTHETIC-LAB EVIDENCE.** It does not establish real-world AXIGNAL accuracy. It does not promote Jev to production. It does not promote a decision grammar. It does not grant canonical authority.

## Evidence Labels

- **OFFICIAL_VENDOR_FACT** — sourced current TypeSafe documentation or release facts.
- **AXIGNAL_EXPERIMENT_CONFIGURATION** — the unchanged P0-JEV-02 predeclared setup and this slice's fixed execution limits.
- **AXIGNAL_LIVE_OBSERVATION** — values returned by the provider and recorded by this run.
- **AXIGNAL_DERIVED_METRIC** — deterministic result from preserved observations and Golden labels.
- **AXIGNAL_INTERPRETATION** — bounded explanation of this synthetic sample only.
- **UNKNOWN** — provider or billing metadata not available in the artifact.
- **NOT_EVALUATED** — outside the stated experiment.

## Run Identity

- **Smoke response timestamp (UTC)**: `2026-09-25T18:05:23.970703+00:00`.
- **Smoke artifact created (UTC)**: `2026-09-25T18:05:24.0228078Z`.
- **Controlled result artifact created (UTC)**: `2026-09-25T18:08:14.4872987Z`. Per-request times were not separately stored; the exact experiment start/end wall times are **UNKNOWN**.
- **Git HEAD recorded by the runner**: `551ba1a2e78d2768089b45a9e764403174a14755`.
- **Execution source state**: the working tree contained the P0-JEV-03 implementation as uncommitted changes when the live calls ran. The immutable result manifest records the base Git HEAD, not a commit containing the runner and adapter changes. The request-path function hashes below identify the source functions used; this remains a manifest limitation for exact commit-level provenance.
- **Smoke result ID**: `b56a860609bbb391490fcae782a6133b75cf954d5519ad5bb95eb0a6565c95fc`.
- **Smoke gate ID**: `908a8cacc6f4285c301c18086fade0438b498802b311a73511ff213cccb150cc`.
- **Controlled result ID**: `8f5317065c62df629e63689ef21701c5fd4a8d9500aaa17f4621340f925e7960`.
- **Controlled replay source ID**: same as controlled result ID.

Artifacts are create-only. The first offline smoke replay (`smoke-replay.json`) was written with an empty experiment definition and then rejected by the reader's manifest consistency check. It is preserved unchanged. A corrected offline replay (`smoke-replay-validated.json`) passes digest and composition checks; no provider call was repeated. The complete controlled replay is `replay-result.json`.

## OFFICIAL_VENDOR_FACT

Official sources reviewed on 2026-09-25:

- TypeSafe [Python SDK guide](https://docs.typesafe.ai/sdk/python) and [synchronous client reference](https://docs.typesafe.ai/sdk/python/api/clients/sync): explicit client key, timeout, `system_one` model selection, and retry policy.
- TypeSafe [response types](https://docs.typesafe.ai/sdk/python/api/types/responses), [Choice primitive](https://docs.typesafe.ai/primitives/choice), and [confidence semantics](https://docs.typesafe.ai/confidence): Choice provides a selected value, probabilities and derived confidence; usage/model metadata may be absent.
- TypeSafe [retry policy](https://docs.typesafe.ai/sdk/python/api/retries): `max_retries=0` disables SDK retries.
- TypeSafe [model catalog and public prices](https://docs.typesafe.ai/models): Jev 1.13 model ID is `jev-1.13.0`; listed input price is `$0.042 per 1,000,000 input tokens`. The mutable `jev-latest` alias was not used.
- Official Python SDK [v0.7.1 release](https://github.com/typesafe-ai/typesafe-sdk-python/releases). Installed and pinned version: `0.7.1`.

The refreshed contract agrees with the adapter behavior relevant to this run. The adapter explicitly passes the pinned model and zero-retry policy, and preserves the selected Choice, returned probability distribution, confidence, resolved model, and usage fields actually reported. No SDK response object, HTTP body, exception text, request header, or credential is stored.

## AXIGNAL_EXPERIMENT_CONFIGURATION

### Smoke

- Case: `CES-01-clear-positive`, synthetic Golden label `SUPPORTED`.
- Question: `CES.SUPPORT.v1` version `v1`, `CLAIM_EVIDENCE_SUPPORT`, primitive `CHOICE`.
- State: existing compiler, `minimal@0.1.0`; requested model `jev-1.13.0`.
- Requests/questions: exactly `1` / `1`; concurrency `1`; SDK retries `0`.
- Request bytes: `960`; token and monetary preflight: **UNKNOWN**.

### Controlled experiment

- Definition: unchanged `claim-wording-ab@0.1.0`; five predeclared cases; variants `v1` and `v2`; one repetition.
- Requests/questions: exactly `10` / `10`; concurrency `1`; SDK retries `0`.
- Preflight bytes: maximum request `1,082`, aggregate `10,192`; limits `20,000` and `150,000` respectively.
- Preflight provider-input-token budget: **UNKNOWN**.
- Preflight maximum monetary exposure: **UNKNOWN**; request bytes were not treated as tokens.
- Pricing policy: `typesafe-jev-1.13-input-price.v0.1`; input price `$0.042 / 1M tokens`; effective date not stated by vendor.

## AXIGNAL_LIVE_OBSERVATION

### Smoke

- Authentication/provider request: succeeded; no operational failure category.
- Requested/resolved model: `jev-1.13.0` / `jev-1.13.0`.
- Selected answer: `NO_EVIDENCE`; confidence `0.79`.
- Returned distribution: `CONFLICTING=0.00`, `NOT_SUPPORTED=0.14`, `NO_EVIDENCE=0.83`, `PARTIAL=0.01`, `SUPPORTED=0.02`.
- Provider usage: `391` input and `70` output tokens; `total_tokens` was not reported.
- Local latency: `1.3455206` seconds; retries: `0`.
- The output disagrees with the independent synthetic `SUPPORTED` Golden label. This is retained as a quality observation and did not invalidate the provider compatibility gate.

### Controlled run

All ten calls answered, returned distributions, resolved to `jev-1.13.0`, and reported `input_tokens` and `output_tokens`. There were no provider failures, missing answers, malformed judgments, or critical regressions. Every selected Choice was `NO_EVIDENCE`.

| Case | Golden label | v1 Choice | v1 confidence | v1 P(NO_EVIDENCE) | v2 Choice | v2 confidence | v2 P(NO_EVIDENCE) |
|---|---|---:|---:|---:|---:|---:|---:|
| CES-01-clear-positive | SUPPORTED | NO_EVIDENCE | 0.77 | 0.81 | NO_EVIDENCE | 0.84 | 0.88 |
| CES-02-clear-negative | NOT_SUPPORTED | NO_EVIDENCE | 0.74 | 0.80 | NO_EVIDENCE | 0.80 | 0.83 |
| CES-03-partial-support | PARTIAL | NO_EVIDENCE | 0.75 | 0.79 | NO_EVIDENCE | 0.78 | 0.82 |
| CES-04-wrong-entity | NOT_SUPPORTED | NO_EVIDENCE | 0.76 | 0.80 | NO_EVIDENCE | 0.81 | 0.84 |
| CES-07-missing-evidence | NO_EVIDENCE | NO_EVIDENCE | 0.98 | 0.99 | NO_EVIDENCE | 0.99 | 1.00 |

Provider-reported usage summed across the ten calls: `4,043` input tokens and `700` output tokens. The provider did not report `total_tokens`; aggregate total-token usage is **UNKNOWN**. Summed local per-call latency: `6.1736513` seconds; observed range: `0.5853913`–`0.7035691` seconds.

Wrong answers: `4/5` for each variant. The eight wrong rows reported confidence from `0.74` to `0.84`; this is a concerning confidence observation, but calibration and formal overconfidence are **NOT VALIDATED**. The one correct case per variant reported `0.98` and `0.99`; there is no low-confidence correct answer in this sample. No distribution was flat or malformed; the selected `NO_EVIDENCE` probabilities ranged from `0.79` to `1.00`. No SDK schema mismatch, model-resolution mismatch, or unexpected exception occurred. The absent `total_tokens` field is retained as unknown.

## AXIGNAL_DERIVED_METRIC

- **v1 exact outcome accuracy**: `1/5 = 0.20`; confusion matrix rows are Golden labels and the only predicted column is `NO_EVIDENCE` (`SUPPORTED→NO_EVIDENCE: 1`, `NOT_SUPPORTED→NO_EVIDENCE: 2`, `PARTIAL→NO_EVIDENCE: 1`, `NO_EVIDENCE→NO_EVIDENCE: 1`).
- **v2 exact outcome accuracy**: `1/5 = 0.20`; identical confusion matrix.
- **Difference**: no top-choice change and no accuracy difference. v2 increased `P(NO_EVIDENCE)` on all five cases by `0.01`–`0.07`; this descriptive movement does not establish a benefit.
- **Critical regressions**: `0` under the existing evaluator.
- **Provider operational failures**: `0`.
- **Estimated public input-price cost**: `4,043 × $0.042 / 1,000,000 = $0.000169806 USD`.
- **Invoice cost**: **UNKNOWN**; no billing evidence was available.
- **Brier score**: not evaluated. Existing supported calibration helper is binary; the current run uses a five-class Choice distribution and no approved categorical Brier calculation.
- **Calibration validated**: `NO`.

## Formal Outcome

- **FORMAL_OUTCOME**: `INCONCLUSIVE`.
- **FORMAL_OUTCOME_REASON**: `NO_PREDECLARED_MINIMUM_EFFECT`.
- This is the unchanged P0-JEV-02 evaluator result. The result is not upgraded by the equal descriptive accuracy or observed distribution movement.
- The first smoke replay write had a local manifest-shape defect. Its file remains unchanged; corrected replay and controlled replay both pass digest verification. The live observation and controlled result were not rerun.

## Replay and Reproducibility

- Smoke replay result ID: `1b112dfb0d079e1601510144eaa9d9ce4d215aed5624109fafeefdcc1ff809ce` (reader rejected its empty-definition/source-manifest pairing; retained for audit).
- Validated smoke replay: `smoke-replay-validated.json`; source ID and normalized judgment/composition match the live smoke result.
- Controlled replay: `replay-result.json`; source digest, all ten judgments and compositions, both variant metrics, critical regressions, and formal outcome/reason match `claim-wording-ab-result.json`.
- The result and replay artifacts pass `read_result` content-digest validation. Replay reads only recorded data and needs no credential or network.
- **Reproducibility manifest completeness**: **PARTIAL**. The source `git_revision` is the clean base commit because changes were uncommitted during execution. Result definition/assets and provider outputs are digested/preserved; current provider/run function SHA-256 values are listed below, and the controlled-run implementation files have not changed since the calls. A commit-level source SHA for the executed dirty tree was unavailable at call time.

| Execution function | SHA-256 of source function |
|---|---|
| `pilot.py::run_smoke` | `efe17ef3db92c1fd2b9ba5aad66030e4353d0f0a408d861d8a5b90df3a118a7d` |
| `pilot.py::run_experiment` | `2c810c5366f618f71b96ffb8a648f77a3b1bdf1f4c24d5be5960f3e78bbe7dc2` |
| `providers/typesafe.py::TypeSafeLabEvaluator.evaluate` | `167484c2635517a83d485ce9cb950fb45d2cd6c6082924319e3ff3fe83ada496` |
| `cli.py::_run_live` | `ca4792be851c0bac3a589f780e5d16f35a0b9d0c9f05f6f08d38f6b4c7bf5a94` |
| `cli.py::_run_result_replay` | `5efe8fffd0a524c88e41a1bd736a007e4d3d405528e121e1afbac3ac3762c737` |

Configuration/corpus SHA-256:

| Input | SHA-256 |
|---|---|
| `experiments/v0.1/claim-wording-ab.json` | `e03a63f21a58446f507c815934aeb87d7f5be4a697a3f8e7721c30ffe598bc9c` |
| `corpus/v0.1/cases.json` | `25d4c5980579ea094d0300a1fe9b97208c2f20c4c3736c06e5db3e1094fa852d` |
| `grammar/v0.1/grammar.json` | `411729ede1a0cc49a5b7a219d5ecb6b8af548a400c150ae39bde690da84206b2` |
| `grammar/v0.1/question-lock.json` | `28a6614f98dbe326e837dea94c4aa6efa851356d0feb4faf32b5511d2d7d262` |
| `pricing/v0.1/typesafe-jev-1.13.json` | `77046587356a1b9b2be8bc887010943aeeafd1e3a59806f06cebf0c9fe73affe` |

The replay function hash reflects the offline replay fix made after the smoke request; it did not participate in either live provider call. The smoke request and experiment request functions, TypeSafe evaluator, corpus, grammar, question lock, experiment definition, and price policy hashes reflect the source used for the controlled run. The smoke-specific request function and TypeSafe evaluator were unchanged after the smoke call.

## AXIGNAL_INTERPRETATION

On this five-case synthetic sample, both wording variants returned the same top choice for every case and achieved the same descriptive accuracy. The provider repeatedly favored `NO_EVIDENCE`, including where the independent Golden label was positive, negative, or partial. The criteria-explicit wording shifted more probability toward `NO_EVIDENCE`, but did not change the selected answer or measured accuracy. The sample and unvalidated calibration do not support a quality or generalization claim.

`GRAMMAR_EVOLUTION_CANDIDATE=NO`: no wording candidate is supported by the formal outcome or descriptive accuracy. No grammar was promoted.

## UNKNOWN

- Total tokens, because the provider returned no `total_tokens` field.
- Exact controlled-run request-sequence start/end timestamps; only result artifact creation time and per-call durations were captured.
- Invoice cost and any account-specific discount/fees.
- Real-economy accuracy and generalization.
- Provider metadata not exposed in the recorded typed response.

## NOT_EVALUATED

Calibration validation, other experiments, other models/providers, production routing, canonical admission, real-world accuracy, and any grammar/model/threshold promotion.

## Authority and Safety

Jev output is a typed provider judgment only. Golden labels remain independent and unchanged. No AXIGLAND, FAXT, INXIGHT, PATHX, Knowledge Frontier, production research, private-access request, production policy, grammar, model, or runtime was changed by this pilot.
