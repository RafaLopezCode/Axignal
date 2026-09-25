# AXIGNAL Jev reconciliation plan — 2026-09-25

**Status:** Research recommendation only. Nothing below is implemented or authorized. The dependency order corrects experimental validity before broad grammar/policy claims and retains MASTER/ADR authority. Old accepted decisions remain historical; a new ADR/spec records `OLD DECISION → NEW EVIDENCE → RECONCILIATION → NEW DECISION`.

## Proposed dependency graph

```text
R0 historical evidence/report semantics
  ↓
R1 reconciliation ADR + amended structured-decision spec
  ↓
R2 question information requirements and state contracts
  ↓
R3 state compiler implementation proposal
  ↓
R4 answerability/preflight validity gate
  ├───────────────┐
  ↓               ↓
R5 grammar review  R6 lab/evaluator attribution controls
  └───────┬───────┘
          ↓
R7 evidence-bearing corpus + adjudication protocol
          ↓
R8 deterministic validation/replay and release invalidation rules
          ↓
R9 controlled state-sufficiency experiment design
          ↓ (only after a separate CTO live-call authorization)
R10 live state/wording/primitive experiment
          ↓
R11 broader target-domain validation and policy assessment
          ↓
R12 separate architecture/runtime decision (no automatic promotion)
```

## Ordered remediation units

The units specify needed future work, not a request to start it. “Files/components” are likely touch points to verify at authorization time; this audit does not prescribe their exact implementation.

| ID | Why | Dependencies | Likely files/components | Architectural risk | Migration risk | Experiment required | Live calls required | Production impact | Acceptance gate |
|---|---|---|---|---|---|---|---|---|---|
| R0 — Preserve P0-JEV-03 as historical, limited result | Correctly label `0.20` as accuracy under the recorded insufficient state, not claim-evidence accuracy | None; PR #14 remains separately governed | P0-JEV-03 report/run manifest and PR #14 review context | Low if historical data is append-only; high if rewritten | None | No | No | None | Exact request/replay fingerprints retained; claim accuracy remains `NOT_ESTABLISHED`; PR #14 decision made only by CTO |
| R1 — Reconciliation authority record | Preserve P0-JEV-01/02 accepted history while changing future design basis explicitly | R0, this research accepted by CTO | New ADR and structured decision architecture spec/status | Medium: must not conflict with MASTER/accepted ADRs | Low, documentary | No | No | None | CTO accepts findings; ADR resolves supersession/amendment and preserves lineage |
| R2 — Question information requirements + state contracts | Current shared contract cannot express question-specific semantic evidence needed | R1 | Grammar/question contracts, conceptual data model, contract docs | Medium: avoid over-general schema | Medium: existing grammar contract hashes change only in new version | No | No | None | Every question declares semantic fields, provenance/time constraints, missingness and no-match semantics; review against MASTER |
| R3 — State compiler reconciliation | Compiler validates JSON safety/canonical bytes but not meaning/required information | R2 | `experiments/decision_lab/state.py` first; production boundary remains unselected | Medium: compiler must remain adapter-neutral and non-authoritative | Medium: fingerprints/version changes invalidate experiment comparability | Yes, compiler contract cases | No | None until separately authorized | Deterministically rejects absent required semantic fields, preserves evidence content/provenance, differentiates absent from explicit unknown; old hashes remain reproducible |
| R4 — Answerability validity gate | Prevent structurally invalid arms from being scored as model-quality evidence | R2/R3 | experiment validation/preflight, result schema, evaluator gate | High if gate is only another heuristic or can be bypassed | Medium: legacy runs classified retrospectively without deletion | Yes, false pass/fail adjudication | No | Research-only | Unanswerable/ambiguous/golden-invalid outcomes invalidate quality metrics or are reported in separate denominators; cannot call provider |
| R5 — Grammar V-next review | All 12 current questions have incomplete semantics, criteria, or actual state mismatch | R2/R4 | `grammar/v0.1` frozen; new grammar version and locks | Medium: avoid silent mutation and conflating candidate tasks | Medium: explicit version migration and crosswalk | Yes | No before R9 | None | Each prompt has valid state contract, complete criteria/candidate coverage, primitive fit, uncertainty behavior, independent estimand, and status; no production promotion |
| R6 — Laboratory attribution repair | Current lab tracks many variables, but not answerability, golden validity, or all failure causes as separate dimensions | R4; parallel with R5 | `validation.py`, experiment/result/outcome/evaluator/replay/metrics modules and tests | Medium: preserve provider-neutral CI | Medium: schema/replay compatibility for old fixture results | Yes, deterministic fixtures and invalidation cases | No | Research-only | Lab distinguishes state/question/primitive/model/composition/golden/provider; quality metric cannot issue for invalid arm; replay is offline |
| R7 — Evidence-bearing corpus and annotation | Existing 42 cases put evidence text beside state; synthetic construction cannot establish target performance | R2/R5/R6 | corpus schema/cases, independent label provenance, evidence fixtures | High: privacy/provenance and label authority | Medium: corpus format and hashes | Human adjudication; synthetic and real/public split | No for synthetic; live provider not needed | None | Every answerable case serializes relevant claim/evidence; evidence links resolve; independent label protocol/agreement; ambiguous cases explicit; no customer/private content |
| R8 — Offline validation and reproducibility gate | Ensure prior cases and new controls are reproducible without provider access | R6/R7 | deterministic tests, governance/architecture checks, manifests/replay | Low-to-medium | Low | Offline contract tests | No | None | Required CI stays deterministic/provider-independent; historical raw artifacts are immutable and replay behavior versioned |
| R9 — State-sufficiency experiment preregistration | Identify minimum sufficient state empirically rather than inventing it from docs | R5–R8 | new experiment definition, corpus split and protocol only | Medium: prevent confounding; include state disclosure/privacy review | None | Required by purpose | Not until explicit approval | None | Locked arms: candidate/IDs, explicit claim, semantic passage, provenance, time, contradictory/negative evidence as relevant; answerability adjudicated; power/sample plan and outcome/metrics frozen |
| R10 — Controlled live state/wording/primitive pilot | Measure Jev only on answerable state and attribute differences correctly | R9 plus separate CTO authorization | bounded lab invocation and append-only artifacts | Medium: avoid overclaim and alias drift | None | Yes | Yes, only after separate authorization | None | Pinned resolved model/provider/SDK; held-out labels; declared budget; no production path; answerable denominator, confidence/calibration and failure strata reported |
| R11 — Broader domain validation | Establish repeatability, calibration, class coverage, cost and policy utility beyond a tiny synthetic run | R10 | evaluation program, permitted evidence dataset | High: selection/leakage and domain shift | None | Required | Likely, separately authorized | None | Independent samples across source/time/subgroups, uncertainty intervals, cost and review load, false-positive/negative consequences, explicit pass/fail policy |
| R12 — Separate future architecture/runtime decision | Evidence does not authorize production Jev, Luna, or policy thresholds | R11 plus relevant CTO order | new spec/ADR, runtime only after approval | High | Potentially high | Depends on intended use | Possibly, separately authorized | None now | Explicit decision authority, security/privacy review, rollback, observability, admission firewall, model replacement and staged validation |

## Python / Jev / Luna / policy responsibility matrix

This refines the MASTER heuristic. `Python` means deterministic application logic; `Jev` is a candidate bounded judgment, never presumed beneficial; `Luna` denotes the separately governed open-ended cognitive/generative role described in architecture docs, not a runtime implemented here; `AXIGNAL policy` owns domain rules and authority.

| Work | Python | Jev | Luna | AXIGNAL policy / hybrid |
|---|---|---|---|---|
| Exact computation | Own calculations, dates, counts, canonicalization, equality | N/A | N/A | Policy supplies constants/meaning if needed |
| Normalization | Own deterministic schema/Unicode/unit mapping where defined | Candidate only for genuinely semantic normalization | Candidate for novel explanation | Policy defines accepted forms; hybrid only for ambiguous meanings |
| Entity identity | Exact IDs, registries, pair construction, deterministic blockers | Candidate pairwise semantic judgment with both records present | Open-ended research on ambiguous corporate history | Policy handles review/merge authority; hybrid |
| Semantic alignment | Retrieve and construct state; validate shapes | Candidate for narrow comparison over explicit text | Open-ended interpretation when bounded labels fail | Policy defines taxonomy and downstream meaning; hybrid |
| Evidence support | Retrieve exact passages, maintain provenance and labels | Candidate claim-to-passage semantic judgment | Synthesize complex multi-source explanations | Admission is evidence/policy controlled; hybrid |
| Classification | Rules first for exact categories; format validation | Candidate bounded exclusive Choice or independent Nouls | Open-set taxonomy discovery / explanation | Policy defines category and action; hybrid |
| Ranking | Compute deterministic filters/eligible candidates | Candidate dimension Scores over complete relevant candidates | Synthesize criteria or open-ended qualitative tradeoffs | Policy defines weights, eligibility and ties; hybrid |
| Routing | Enforce permissions, availability and explicit rules | Candidate bounded semantic route among legal candidates | Decompose unfamiliar request | Policy authorizes queue/route; hybrid |
| Research planning | Maintain state, budget, dependencies and stop conditions | Candidate bounded gap/next-step judgments only if useful | Propose research plan and hypotheses | Research Planner owns priority and whether to act; hybrid |
| Source selection | Enforce source registry, rights, reliability metadata | Candidate relevance judgment among permitted supplied sources | Formulate novel search strategies | Policy owns permission/risk and acquisition; hybrid |
| Context compaction | Exact budgets, preserve source IDs/quotes/hash | Candidate item retention/relevance judgments | Coherent summary/generative compression | Policy chooses loss tolerance; require recall experiment; hybrid |
| Open-ended interpretation | Structure inputs and validate outputs | Poor fit when no bounded answer space | Candidate for open-ended synthesis | Domain constraints and evidence authority remain AXIGNAL; hybrid |
| Hypothesis generation | Store candidates, dedupe and test constraints | Not the generation authority | Candidate generator | Hypotheses remain unproven until evidence and admission; hybrid |
| Canonical admission | Execute admission checks and transactions | Never authorize or commit | Never authorize or commit | AXIGNAL domain admission authority; Jev/Luna N/A as authority |
| Action execution | Validate and execute idempotently after authorization | May rank/select candidate only | May propose/plan only | AXIGNAL policy and domain controls authorize; Jev/Luna N/A as authority |

**Status:** routing heuristic remains useful as a first triage only. Add “is the exact target deterministic?”, “does the input contain the semantic information?”, “is the answer space appropriate?”, “who owns action authority?”, and “has target-domain utility been measured?” before choosing a model. No Luna call or implementation is part of this plan.

## PR #14 decision boundary

`PR14_RECOMMENDATION=MERGE_AS_HISTORICAL_EXPERIMENT`, subject to CTO review. This research does not change PR #14 or authorize its merge. No P0-JEV-03 artifact should be rewritten; any future report should append a reconciliation reference rather than alter the original run.

## Next live experiment recommendation (not authorization)

`NEXT_LIVE_EXPERIMENT_RECOMMENDED=YES, AFTER R2–R9 AND SEPARATE CTO ORDER`. Purpose: estimate how explicit claim plus semantic source passage, provenance/source independence and temporal context affect a narrowly named evidence-support judgment, under answerability-adjudicated cases and locked held-out evaluation. Do not infer a global minimum state from one task. Include negative, partial, no-evidence, duplicate, contradictory and wrong-entity cases. Keep production admission out of scope. `NEXT_LIVE_EXPERIMENT_AUTHORIZED=NO`.
