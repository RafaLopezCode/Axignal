# Jev evaluation methodology — 2026-09-25

This is a proposed research protocol derived from the official recommendation to evaluate System One performance in the target domain (O6/O9/O11). It is not a TypeSafe-required benchmark.

## 1. Freeze the estimand

Name the semantic judgment being evaluated (not the downstream workflow label alone), the population, decision unit, intended use, error costs, and the observation window. State whether the target is primitive answer quality, calibrated probability, composition quality, or end-to-end policy utility.

## 2. Validate answerability before scoring

For every case, record the gold answer, its evidence location, required state fields, and whether the serialized request actually includes discriminating semantic evidence. Label cases `answerable`, `partially_answerable`, `unanswerable`, or `ambiguous` through a documented human/adjudication protocol. Do not count structurally unanswerable cases as model mistakes or as evidence of model quality. Keep their count and reasons visible.

## 3. Data and annotation

- Use representative, provenance-bearing examples; include positive, negative, boundary, missing, contradictory, adversarial and hard-negative cases.
- Establish annotation instructions and independent labels; report disagreement and adjudication.
- Split by source/entity/time so near-duplicates cannot leak across development, calibration and held-out sets.
- Keep synthetic demonstrations separate from real-world validation.
- Pre-register the primary metric and decision costs before looking at held-out outcomes.

## 4. Controlled request specification

Version the exact UTF-8 state payload, question instructions, criteria/options/rubric, primitive, model identifier resolved at call time, provider/endpoint, SDK version, and relevant headers without secrets. Record response schema, request ID, usage fields when available, timestamps, retry/transport outcome, and raw typed answers. Never assume `jev-latest` is immutable.

## 5. Ablation and comparison matrix

Change one factor at a time where feasible:

| Factor | Controlled comparison |
|---|---|
| State | identifier-only vs retrieved semantic content; full vs minimally sufficient; with/without provenance, time, contradictions, negative evidence |
| Question | original vs precise target/exclusions; one complex vs independent atomic questions |
| Primitive | Choice vs per-label Noul vs Score where semantics permit |
| Candidates | complete vs deliberately omitted candidate; explicit none/review outcome |
| Provider/model | pin and compare provider/version with all other inputs fixed |
| Repeatability | repeated requests under same pinned configuration; report variability, not just mean |
| Composition | preserve raw outputs and replay alternative deterministic policies offline |

Do not run an ablation whose arms change multiple semantic factors without calling it a bundled comparison.

## 6. Metrics

Report confusion matrix and per-class precision/recall/F1; exact accuracy only with class balance context; coverage and selective risk by abstention/review rate; Brier/log loss and calibration plots for probabilistic outputs where the output semantics support them; latency and usage/cost per resolved item; end-to-end utility under explicit false-positive/false-negative costs. Include uncertainty intervals and subgroup/source/time breakdowns. A Choice distribution or Score distribution is not automatically calibrated for the AXIGNAL population.

For Noul, treat the returned value as the probability assigned to the proposition. Do not invent a second confidence number. For Choice/Score, confidence is a distribution-shape statistic; measure probability quality against labels independently.

## 7. Decision threshold selection

Choose action thresholds using a development/calibration set and explicit costs, then lock them before held-out evaluation. Include an abstain/review region when the cost of automatic error justifies it. Thresholds are task-, class-, and action-specific; no universal threshold is supported by O6. Evaluate workload and harm as well as predictive metrics.

## 8. Failure attribution

For every error, preserve case ID, state, question, candidate set, primitive, model/provider, raw output, composition, policy action, gold label, evidence, and adjudication. Apply [failure taxonomy](JEV_FAILURE_TAXONOMY_2026-09-25.md). Report errors by state/question/model/policy class rather than attributing all of them to Jev.

## 9. Reproducibility and release gate

Store immutable corpus and configuration hashes, source provenance, SDK lockfile, resolved model version, code revision, evaluator version, and run manifest. Re-run deterministic evaluator and replay composition separately from live inference. Require independent held-out validation, acceptable subgroup performance, calibrated review burden, and explicit domain-owner acceptance before operational use. Live experiments require separate authorization; this document authorizes none.

## Interpretation guardrails

- Cookbook or community sample results are technique illustrations, not representative benchmarks.
- Model output format validity is not semantic accuracy.
- Repeated agreement is not independent evidence by itself.
- Cost optimization is downstream of proving the request can answer the target question.
- UNKNOWN remains distinct from false; missing evidence is not negative evidence.
