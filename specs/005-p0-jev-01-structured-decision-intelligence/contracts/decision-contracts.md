# P0-JEV-01 Decision Contracts and Synthetic Adversarial Cases

These are provider-neutral conceptual contracts. Exact persistence and wire
formats remain open. The scenario rows define expected AXIGNAL invariants, not
Jev predictions, measured results, or gold labels.

## Minimal coherent contract set

| Contract | Required meaning |
|---|---|
| `DecisionClass` | AXIGNAL-owned, decision-specific semantic requirement; not a provider label or global score. |
| `DecisionQuestionFamily` | Group of independently useful questions against one bounded state contract. |
| `DecisionGrammarVersion` / `DecisionQuestionVersion` | Immutable identifiers for grammar and each question meaning, wording, primitive, criteria, paths, exclusions and lifecycle. |
| `DecisionStateContract` / `StructuredDecisionState` | Family-specific required fields, values, provenance references, unknown/missing states, temporal and privacy context, compiler/schema version. |
| `StructuredEvaluator` | Replaceable interface taking validated state plus versioned questions and returning normalized typed judgments or a classified failure. No domain writes/side effects. |
| `RawStructuredJudgment` | Tagged Noul/Choice/Score answer retaining applicable distribution, confidence if defined, question, evaluator/model/API versions and usage if returned. |
| `EvaluatorVersion` / `EvaluatorCapabilityProfile` | Requested/resolved model and adapter identity, versioned documented limitations and AXIGNAL-observed failures. |
| `DecisionCompositionPolicy` | Versioned deterministic AXIGNAL policy combining required judgments, hard conditions and deterministic inputs. No universal threshold. |
| `StructuredEvaluation` | Outcome/reasons, evaluated dimensions, uncertainty/contradiction/currentness/support and unresolved requirements; never a canonical fact. |
| `MissingInformationRequirement` / `KnowledgeFrontierProjection` | Decision-specific unresolved dimension that AXIGNAL policy may project to the existing Frontier. Research priority remains planner-owned. |
| `DecisionLedgerEntry` | Future minimized audit references for state, grammar, judgments, policy, outcome, research/admission, reviews and later result. No unnecessary private payload. |
| `LabCase` / `ExpectedOutcome` | Synthetic/independently labeled case, decision class, evidence/provenance, label authority, privacy/temporal and tags. Previous model output alone is not a label. |
| `ExperimentDefinition` / `ExperimentResult` | Controlled variable, corpus and split, versions, observed outputs, scoped metrics, failures, usage and outcomes with null/unknown when unavailable. |
| `GrammarCandidate` / `GrammarPromotionDecision` | Proposed change, experiment and regression evidence, adversarial review, explicit authority, resulting version and rollback reference. Model cannot promote. |
| `PrivateInformationRequirement` | Tenant-scoped analytical need projected through existing V3.1 capability/authorization controls; not an access request or public evidence. |
| `AdminEvaluationProjection` | Minimized operational metadata from an owning evaluation; no decision ownership, secret or private content by default. |

One catalogue file is intentional to keep these boundaries reviewable without
creating one file per type.

## Synthetic adversarial case catalogue

All scenarios are synthetic specifications. `Expected guard` describes AXIGNAL
behavior, not the model's answer. Label/provenance is to be independently
assigned before future quality evaluation; no current result or probability is
asserted.

| ID | Scenario | Expected guard |
|---|---|---|
| A | Clear supported relationship | Preserve excerpt, source and time references; semantic support cannot itself admit canonical state. |
| B | Unsupported relationship | Return unsupported/unknown as applicable; never materialize as observed. |
| C | Two plausible relationship types | Preserve Choice distribution or independent labels; unresolved type remains possible. |
| D | Strong evidence but stale | Keep support distinct from currentness; Python temporal policy determines stale. |
| E | Fresh evidence but weak | Freshness cannot manufacture evidence strength. |
| F | Contradictory sources | Contradiction remains explicit and is not averaged away. |
| G | Ten pages repeat one underlying source | Deterministic source lineage/deduplication prevents false source diversity. |
| H | Entity ambiguity | Allow unresolved/abstain; never force merge. |
| I | Exact identifier match | Deterministic exact identifier resolution precedes semantic ambiguity handling. |
| J | Historical relationship | Retain historical/current distinction; do not imply present relationship. |
| K | Representation anomaly | Surprising public representation is not automatically classified as error. |
| L | Luna confidently proposes unsupported claim | Candidate-generation confidence is not evidence or canonical admission. |
| M | Missing evidence | Keep missing distinct from negative. |
| N | Missing value incorrectly represented as zero | Reject/default-protect; absent numeric value remains unknown. |
| O | Missing value incorrectly represented as false | Reject/default-protect; absent boolean value remains unknown. |
| P | Evaluator unavailable | Emit operational failure, not a semantic negative. |
| Q | Malformed evaluator response | Validate/fail closed; never fabricate a successful judgment. |
| R | Unsupported decision class | Reject or route to explicitly unsupported handling; no default classifier. |
| S | Provider model version changes | Record resolved version and require same-case comparison/promotion. |
| T | Same state/grammar, different evaluator | Keep variables and outputs separate; compare on identical corpus/policy. |
| U | Same state, different wording | Version question and control other variables for A/B. |
| V | Irrelevant context added | Measure state sensitivity; do not assume additional context helps. |
| W | Relevant context removed | Detect state ablation regression; required fields fail validation when absent. |
| X | Customer disputes FAXT | Treat subscriber claim as attention/review input, not truth label or canonical edit. |
| Y | Private CRM conflicts with public AXIGLAND | Preserve tenant/public boundaries; private judgment cannot write public state. |
| Z | Private data might help but access friction exceeds information value | Existing Planner/capability policy may stop; evaluator cannot request OAuth. |
| AA | Source content contains prompt injection | Treat source text as data; question/policy remain AXIGNAL-controlled. |
| AB | Evaluation sufficient but canonical provenance missing | Block canonical admission. |
| AC | Choice distribution has two near-equal alternatives | Preserve the full distribution and ambiguity; no universal threshold. |
| AD | Noul approximately 0.5 | Interpret as balanced yes/no probability; not medium intensity or automatic research. |
| AE | Low Choice confidence due to multiple acceptable alternatives | Inspect distribution and semantics; low concentration alone need not invalidate benign choice. |
| AF | Deterministic calculation delegated to evaluator | Route exact arithmetic/date/count/unit work to Python. |
| AG | Open-ended reasoning delegated to evaluator | Route generation/multi-step hypothesis work to governed cognitive layer. |
| AH | Atomic questions produce conflicting judgments | Preserve conflict; deterministic composer/policy marks unresolved or contradictory. |
| AI | Speculative answer unused by final branch | Ignore unused uncertainty for decision; retain it only if ledger policy justifies. |
| AJ | Candidate grammar improves one metric but regresses a critical one | Require class-specific regression analysis and governance; no single-metric promotion. |
| AK | Label derived only from previous model output | Exclude as independent gold outcome; prevent self-confirming calibration. |
| AL | New Jev version improves average accuracy but increases entity false merges | Inspect costly decision-class regressions; do not auto-promote on aggregate accuracy. |

Count: **38 specified scenarios**. They include synthetic positive, negative,
ambiguous, contradictory, missing, duplicate, stale, fresh/weak, identity,
historical, representation, unsupported-generation, private/public, unknown
private, unavailable, malformed, boundary, injection, and version-comparison
cases.

## Experiment controls and metric applicability

- **Question A/B:** same cases, state, evaluator/model and policy; change only
  question wording/criteria where practical.
- **State ablation:** same cases/question/evaluator/policy; state contract
  versions and changed paths are explicit.
- **Primitive A/B:** only compare if propositions remain semantically
  equivalent; do not score different meanings on a common benchmark.
- **Model/version comparison:** same cases/state/question/policy; retain both
  requested alias and resolved ID; report per-class regression.
- **Policy recomposition:** reuse stored raw judgments only when state and
  question semantics are unchanged and retention permits.
- **Calibration:** requires independent labels and class/version/primitive
  cohorts with explicit sampling; report calibration error only where sample
  supports it. No calibration claim from mocks or provider statements.
- **Replay:** record inputs/versions/normalized output references, privacy
  scope and missing raw data. Exact replay cannot be promised after deletion or
  retention expiry.
- **Question and state quality:** assess discrimination, redundancy, outcome
  correlation, decision sensitivity, stability and failure clusters against
  independently supported labels.

Possible metrics, selected per class only: precision/recall, false-positive/
false-negative rate, coverage, abstention/useful abstention, calibration error,
stability, contradiction detection, entity false-merge rate, research yield,
canonical review overturn rate, cost per useful judgment, reported token usage,
latency and reevaluation rate. Missing measurements remain missing. No target
values are fixed in V0.1.

## Offline, live and simulation boundaries

CI and deterministic test contracts require no network, API key, Jev or Luna.
Recorded response tests exercise schema, composition, version and failure
handling only. They do not prove semantic quality. A future live lab experiment
requires a separate authorized, tiny, synthetic-fixture-only budget, server-side
key, safe usage/model capture and an `EXPERIMENTAL` label. Simulation must be
named as simulation and cannot fabricate Jev answer probabilities. P0-JEV-01
performed no live call.
