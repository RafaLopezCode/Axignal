# Jev failure taxonomy — 2026-09-25

Classify failures before assigning blame. The buckets below are AXIGNAL's operational taxonomy (AXIGNAL_DERIVATION), informed by official input, primitive, confidence, and weak-spot guidance (source ledger O2–O11).

| Class | Symptom | Diagnostic evidence | Control / experiment |
|---|---|---|---|
| State omission | Question lacks the fact or semantic content required | Inspect exact serialized state and question information requirements | Add the missing content; state ablation and sufficiency gate |
| Identifier-only state | IDs/URLs/reference keys supplied without retrieved semantics | State contains pointers but not the referenced passage/claim | Resolve deterministically, include exact relevant text and provenance |
| State ambiguity | Entities, time, scope or relation are unclear | Multiple interpretations fit state | Add named fields, identity/time metadata or explicit unknowns |
| Context dilution/noise | Relevant fact buried among irrelevant content | Compare full versus minimally sufficient state | Controlled state reduction; retain discriminating evidence |
| Contradictory state | Sources disagree without provenance/currentness | Conflicting values or claims in state | Preserve both claims, source/date/status and ask specific contradiction question |
| Missingness collapse | Absence of a field interpreted as negative evidence | Empty/omitted field conflated with false | Encode unknown/not-provided separately; test missing evidence |
| Question target ambiguity | Wording permits multiple readings | Annotator disagreement or sensitivity across equivalent wording | Define target, scope, exclusions and criteria; paired wording test |
| Candidate coverage failure | Correct label/value omitted | Gold answer is absent from Choice options/candidates | Deterministic candidate coverage check and explicit `none/other/review` |
| Primitive mismatch | Noul used for a single exclusive choice, Score for unordered labels, etc. | Output shape cannot represent the decision policy | Select by semantics; compare primitives on controlled examples |
| Calibration/confidence misuse | High confidence treated as correctness or universal action permission | Outcomes disagree despite concentrated answer distribution | Evaluate calibration by task, class, stakes and model version; use review bands |
| Correlated evidence/questions | Agreement counted as independent confirmation | Shared state, phrasing or model creates dependent judgments | Record dependence; avoid multiplying probabilities as independent evidence |
| Composition/policy defect | Good judgments produce bad action due to weights, thresholds or missing-case handling | Raw answers plausible; composed decision violates policy | Replay raw outputs under explicit policy; unit-test deterministic composition |
| Model capability limitation | Adequate state/question but repeatable domain error | Blinded labeled evaluation and controlled ablations | Estimate error by strata; use different primitive/model or avoid Jev |
| Provider/model drift | Result changes across alias, provider, SDK, or version | Request metadata differs or alias is mutable | Pin model/provider/SDK; retain request/response/version metadata |
| Transport/service failure | Timeout, malformed response, rate limit, auth, unavailable service | Provider logs/request IDs and typed transport error | Bounded retry per documented semantics; fail closed and distinguish from judgment |
| Exact-computation misuse | Jev asked to calculate dates, amounts, identity keys or exact equality | Error can be resolved by parser/comparator | Move exact operation to deterministic code; pass result as evidence if useful |
| Adversarial-input failure | Prompt injection, deceptive text, irrelevant instructions in source | Adversarial corpus changes answer | Treat source as untrusted data, isolate instructions, test attack classes, preserve policy gates |
| Evaluation leakage | Question/examples/threshold tuned on test cases | Test data influences prompt or selection | Separate development, calibration, held-out and temporal sets; log versions |
| Golden-data defect | Label is ambiguous, unsupported, stale or inconsistent | Independent annotators disagree or evidence missing | Adjudication, provenance, label confidence and `unanswerable` state |

## Attribution order

1. Verify experiment validity and gold label.
2. Verify provider response and exact model/version.
3. Verify the question is answerable from the serialized state.
4. Inspect primitive and answer-space coverage.
5. Inspect the raw judgment, then deterministic composition/policy.
6. Compare controlled ablations before labeling a residual error a model failure.

Never report end-task accuracy as Jev capability accuracy unless the state actually carried the target evidence and the evaluator tests the named semantic judgment.
