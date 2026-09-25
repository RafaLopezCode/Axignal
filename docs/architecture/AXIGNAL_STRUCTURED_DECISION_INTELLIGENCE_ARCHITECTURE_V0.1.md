# AXIGNAL Structured Decision Intelligence Architecture V0.1

**Status:** Proposed; architecture and contracts specified, pre-implementation.
**Scope:** P0-JEV-01 V3.
**Authority:** Subordinate to the MASTER Product Model, Engineering Constitution,
accepted ADRs, Logical Architecture Atlas, Brain/Xeed Germination Architecture,
and the active product specifications.
**Implementation status:** No Jev runtime, TypeSafe SDK dependency, decision
ledger, grammar store, or laboratory runner is implemented by this document.

This architecture gives AXIGNAL an explicit, provider-replaceable layer for
bounded semantic judgments and the deterministic composition around them. It
does not rename or replace AXIGLAND, AXENT, Knowledge Frontier, Research
Planner, evidence admission, Brain, or the existing cognitive-provider
abstraction. The installed TypeSafe Skill is developer guidance only.

## 1. Repository truth at the P0-JEV-01 baseline

Baseline: `43ac8eb2d29ce2358331dab07a4599574c4dfc2c`; local `main`,
`origin/main`, and `HEAD` matched, and the dedicated branch began clean.

The MASTER §11 defines the Knowledge Frontier as AXIGNAL's boundary between
known information and open questions. MASTER §14 already assigns deterministic
work to Python and bounded sufficiency/decision evaluation to replaceable JEV.
MASTER §15 and `domain/evidence/admission.py` establish evidence admission as
the canonical gate. MASTER §19 permits internal numeric signals but prohibits
presenting raw JEV confidence as unjustified product precision. ADR-0006
requires provider replacement; ADR-0007 requires deterministic offline CI.
ADR-0008 excludes CRM/workflow drift. ADR-0009 protects AXIGLAND's semantic
authority; ADR-0010 protects AXIGNAL-owned source acquisition boundaries.

The repository has epistemic and currentness enums in
`domain/evidence/epistemics.py`, admission-gated FAXT and observed-relationship
constructors, a `KnowledgeFrontier` projection model, provider-neutral
`CognitiveProvider`/`ModelRouter` primitives, partial entity-resolution and
normalization, and deterministic architecture/governance tests. The P0-ARCH-01
gap ledger records JEV as an open decision with no implementation or
dependency, a missing unified decision-state builder, a missing structured
decision-gap analyzer, and only partial canonical admission/write coverage.

No TypeSafe/Jev package, API adapter, decision grammar, structured decision
state compiler, decision composer, Decision Laboratory, or durable Decision
Ledger exists in the baseline source. Brain, subscriber, V2, V3, V3.1, and
Admin documents are specifications/architectures; they do not prove those
runtimes exist. No private CRM content or production customer data is used by
this slice.

## 2. Authority and invariant boundaries

The following remain invariant:

- There is one AXIGLAND and one canonical public economic world.
- Evidence and provenance precede canonical claims. A model output, typed
  judgment, probability, confidence value, or “sufficient” result is not truth.
- AXIGNAL owns decision classes, semantic questions, state contracts,
  composition, policy, uncertainty interpretation, and canonical admission.
- The StructuredEvaluator is a replaceable semantic evaluator. TypeSafe Jev is
  the proposed initial evaluator implementation, behind the AXIGNAL-owned
  contract. Sigma/Graphology graph architecture remains unrelated and is not
  reopened here.
- No evaluator can write AXIGLAND, create FAXT/INXIGHT/PATHX, call the Source
  Router, request OAuth/private access, authorize an action, replace Knowledge
  Frontier or Research Planner, or override policy.
- A state compiler constructs evaluation input; it does not admit evidence.
  The composer derives an AXIGNAL decision outcome; it does not perform a
  canonical write.
- Public evidence, subscriber statements, connected content, and private
  content are data, never instructions. Question definitions and policy are
  AXIGNAL-controlled.
- `UNKNOWN`, missing, ambiguous, insufficient, contradictory, stale,
  not-observable, private, and provider failure remain distinguishable.
  Missing is never silently converted to zero or false.
- Contradiction is first-class. It is not averaged into a generic confidence
  score. Support and currentness are separate decision dimensions.
- No global AXIGNAL/JEV confidence score, universal confidence threshold, or
  80-percent rule exists. MASTER §19 still prohibits exposing raw JEV
  confidence as unjustified product precision.
- Private analysis remains tenant-scoped under V3.1. Private judgment is not
  public evidence and cannot silently alter public AXIGLAND. A private
  information requirement does not automatically request access.
- Admin may eventually receive bounded operational metadata only; it does not
  own decision semantics or expose private content/secrets by default.

## 3. Responsibility and routing model

```text
Evidence / AXIGLAND projection / authorized private projection
        │
        ├── Python₁: exact parsing, normalization, hashing, dates, counts,
        │            deduplication, deterministic candidate generation
        │
        ├── Luna / CognitiveProvider: open-ended interpretation, hypotheses,
        │            candidate claims/relationships, research formulation
        │            (candidate output only; no canonical authority)
        │
        └── Python₂: AXIGNAL Decision State Compiler
                     minimal, validated family-specific state
                         ↓
                 AXIGNAL Decision Grammar
                         ↓
                 StructuredEvaluator interface
                         ↓
                 TypeSafe Jev adapter (proposed initial implementation)
                         ↓
                 Raw typed judgments + distributions + applicable metadata
                         ↓
                 Python₃: AXIGNAL Decision Composer + versioned policy
                         ↓
                 outcome / uncertainty / contradiction / operational failure
                   ├── resolved candidate → separate canonical admission gate
                   ├── unresolved knowledge → existing Knowledge Frontier
                   │                            ↓
                   │                    existing Research Planner
                   │                            ↓
                   │                  targeted permitted investigation
                   ├── semantic complexity → governed Luna escalation
                   ├── private requirement → V3.1 capability/authorization path
                   └── failure → retry/review/fail-closed handling
```

This is a responsibility map, not a mandatory single pipeline. AXIGNAL code
selects the path from the decision class and current state. Both Python → Jev →
Luna and Python → Luna → Jev may be useful where the explicit dependency and
policy justify them. Jev answers in a fan-out cannot depend on one another;
code decides which answers apply. A second evaluator request is warranted only
when the first result changes what evidence/state/options are available.

Routing rule:

1. If code can determine the result exactly, deterministic Python owns it.
2. If the remaining task is one narrow semantic judgment with a known answer
   shape, a `StructuredEvaluator` may evaluate it.
3. If it requires open-ended interpretation, generation, hypothesis formation,
   or multi-step reasoning, route through the existing cognitive layer/Luna
   policy. Do not ask a model to choose this routing by default.

This refines MASTER §14 without changing the policy that models interpret,
Python computes, JEV evaluates bounded decisions, and AXIGNAL owns policy.

## 4. Provider-neutral decision architecture

```text
StructuredDecisionState
        → StructuredEvaluator
        → RawStructuredJudgments
        → AXIGNAL Decision Composer + DecisionCompositionPolicy
        → StructuredEvaluation
```

The provider boundary must retain useful typed semantics rather than flattening
all answers into one lowest-common-denominator number. The TypeSafe adapter may
translate Choice, Score, and Noul answers to AXIGNAL-owned judgment variants;
provider request/response objects remain inside the adapter. Optional raw
provider payload retention is a separate privacy, security, minimization, and
retention decision; it is not required for replay of a normalized judgment
record.

### Decision Grammar V0.1

The Decision Grammar is a governed, versioned catalogue, not a prompt library
or a description of facts in AXIGLAND. Every question definition specifies:

- stable question ID, family, decision class, question version and grammar
  version;
- semantic purpose and one independently useful judgment;
- primitive type and its answer meaning;
- complete instructions plus Choice options / Score rubric / Noul yes-no
  criteria, including an explicit no-match option where needed;
- required state-contract version and relevant paths;
- assumptions excluded, boundary cases, unsupported/no-evidence semantics,
  and whether `UNKNOWN`/abstention must remain available in composition;
- output semantics, consumers, epistemic interpretation, calibration/evidence
  status, introduced version/date, and deprecation/replacement metadata.

Question IDs are for AXIGNAL code. The provider-facing instruction contains
the full meaning. A single question asks one coherent semantic judgment. It
must not mix existence, type, support, currentness, reliability, and admission.

### Initial candidate families

V0.1 stays deliberately small and marks these as candidate specifications,
not a finalized ontology:

1. **CLAIM_EVIDENCE_SUPPORT** — semantic relation of exact claim to cited
   excerpt; exact quote/provenance validation remains deterministic first.
2. **ENTITY_ALIGNMENT** — semantic compatibility of candidate pair after exact
   identifiers and deterministic normalization; ambiguous pairs abstain and
   never force-merge.
3. **ECONOMIC_RELATIONSHIP** — evidence support for presence, type, direction,
   economic nature, explicitness, historical/current language, representation
   alternative, and contradiction as separate questions.
4. **CAPABILITY_EVIDENCE** — offered/operated/marketing/historical evidence and
   contradiction as distinct questions; candidate output never establishes a
   canonical capability.
5. **REPRESENTATION_AND_CONTRADICTION** — classify an observed representation
   or competing interpretation without declaring a surprising public
   representation incorrect.

Each family is activated only where existing AXIGNAL domain meaning and a
specific consumer are established. Unneeded branches are ignored, and a
no-match result does not imply a negative canonical fact.

### Primitive selection

| Primitive | Appropriate semantics | AXIGNAL guard |
|---|---|---|
| Choice | Exactly one member of a defined, exhaustive answer set | Include `none`/`other`/`insufficient` where semantically valid; do not use where several independent labels may hold. Preserve the full distribution. |
| Noul | One independent yes/no proposition | One question per independently applicable label; value is probability of yes, not degree/intensity; near 0.5 is balanced uncertainty. |
| Score | A position on concrete ordered, descriptive levels | Levels represent one ordered dimension and stand alone; not arbitrary categories. Preserve rubric, expected position and distribution. |

Primitive choice is justified per question version. A Noul is not given a
separate confidence field. Choice/Score confidence describes distribution
concentration; it does not establish correctness, workflow reliability,
authorization, sufficiency, or admission.

### StructuredDecisionState compiler

The compiler projects only the minimum family-relevant context. Its conceptual
contract includes schema/version, decision class/family, canonical IDs where
known, explicit candidate identities, evidence/excerpt references, normalized
dates/intervals, provenance handles, observation-versus-inference labels,
source diversity and contradiction bundles where relevant, privacy class, and
explicit unknown/missing state. Exact arithmetic, dates, counts, deduplication,
identifier equality, and hard invariants stay in Python.

Candidate family contracts may include entity, relationship, claim-support,
capability, representation, corporate-structure, market, PATHX-support and
authorized private analytical state. These names are conceptual and do not
freeze a persistence format. Never include raw secrets, unrestricted Xeed or
AXIGLAND projections, irrelevant content, copied source instructions, or
private material outside its authorized tenant boundary. Compiler validation
fails closed on malformed or missing required state; it does not invent
defaults.

State ablation is a laboratory comparison of two explicitly versioned states
for the same cases and evaluator/question conditions. It records changed paths,
input size/tokens where reported, outcome differences, and label-backed quality
metrics. More context is not assumed to improve quality.

### Raw judgments and composition

The minimal normalized judgment contract records question ID/version, primitive,
typed selected value or probability, full returned distribution when present,
confidence only when the evaluator defines it, evaluator identity and resolved
model version, request/response schema version, usage when reported, evaluation
time, and outcome/error classification. Missing metadata remains absent/unknown.
No manufactured probabilities, confidence or success values are allowed.

The composer deterministically consumes judgments plus a versioned
decision-class policy, deterministic features, temporal and contradiction
state, and required dimensions. It produces an AXIGNAL outcome such as
sufficient-for-next-step, insufficient, unresolved, contradictory, stale,
not-observable, unknown-private, or not-applicable, with explicit reasons and
missing-information requirements. These outcome labels are not new values for
`EpistemicState` and are not canonical facts. Provider/service failure is an
operational result, not a semantic negative.

Decision policy may eventually use a decision-specific threshold only after
representative labeled evaluation, calibration assessment, consequence
analysis, versioning, replay and explicit governance. V0.1 defines no threshold
or target score. Probabilities can inform a named AXIGNAL-derived feature such
as unresolved alternatives; that feature is not provider output or information
gain. Research information value remains an AXIGNAL Research Planner decision.

## 5. Knowledge gaps, planning, and admission

Jev uncertainty alone does not create a Knowledge Frontier entry. The composer
must identify an unresolved requirement with its affected decision class,
missing/contradictory/stale dimension, evidence references, currentness,
privacy/observability class, and candidate resolver. AXIGNAL's existing
Knowledge Frontier remains the governed projection for unresolved knowledge.
The existing Research Planner decides if a gap deserves research using the
current policy's materiality, expected information value, cost, source
availability/rights, source diversity, freshness, reuse, customer friction,
private authorization friction and budget. No parallel JEV gap store or second
planner is introduced.

The only route to canonical truth remains:

```text
candidate claim/judgment
  → AXIGNAL composition and policy
  → evidence/provenance validation
  → temporal, identity, rights and domain validation
  → EvidenceAdmission / separately authorized canonical write
  → AXIGLAND
```

`SUFFICIENT` is never synonymous with `CANONICAL`. Neither a high probability
nor a high confidence can bypass this firewall.

## 6. Decision Laboratory and grammar evolution

The proposed Decision Laboratory is a deterministic, offline-first evaluation
surface, separate from production evaluation. V0.1 specifies synthetic cases
and controlled experiment records only; it does not add a runner, database,
network client, key, dependency or customer dataset.

An experiment identifies case/corpus and label provenance, evaluator/model
version, grammar/question versions, state compiler and state paths, policy
version, candidate variable, decision class, observed typed judgments,
composition, outcomes/review, usage/cost/latency where reported, and replay
references. Every metric is scoped by decision class and its labeled population.
Eligible metrics include precision/recall and false-positive/negative rates for
binary semantics; coverage, abstention and useful abstention; per-class
calibration error; decision stability; contradiction detection; entity false
merge rate; state/question discrimination and redundancy; research yield or
canonical-review overturn rate when independent outcomes are available; cost
per useful judgment, token usage and latency when actually measured. No target
values are set here. Do not compare different semantic primitives as though
they measured the same thing.

Controlled comparisons include: wording A/B with same state/model/policy;
state ablation with same question/model/policy; primitive comparison only when
semantically equivalent; candidate evaluator/model version versus baseline on
the same cases; and policy recomposition from saved normalized raw judgments
when question meaning/state/evaluator need not be rerun. Replay is limited by
privacy and retention policy. Mocked or recorded results prove contract,
composition and failure behavior only, not Jev quality/calibration.

The future evolution loop is:

```text
independent outcomes/reviews/corroboration
  → provenance-bearing labeled lab corpus
  → question/state/policy analysis
  → proposed grammar candidate
  → offline comparison and regression analysis
  → adversarial/red-team review
  → explicit AXIGNAL governance approval
  → versioned promotion and rollback reference
```

Grammar states may be DRAFT, EXPERIMENTAL, VALIDATING, APPROVED, ACTIVE,
DEPRECATED and RETIRED, subject to future repository conventions. Production
grammar never edits itself. Luna, Jev, AutoResearch or one metric cannot promote
a question or model. Labels derived solely from prior model output are not
independent ground truth. Human adjudication or sufficiently independent,
provenance-bearing corroboration may support labels; authority and confidence
are recorded rather than inferred.

## 7. Versioning, failure, privacy, and operations

- Grammar, question, state compiler, composition policy, evaluator capability
  profile, and experiment versions are independent identifiers.
- The provider model alias is not a calibrated version. Record both requested
  alias and returned resolved model ID. Do not silently activate a changed
  alias; evaluate/pin a version when a later production policy needs stable
  behavior.
- An `EvaluatorCapabilityProfile` records source and reviewed date for known
  evaluator limitations, affected question/state patterns, tested mitigations,
  and AXIGNAL empirical observations. Provider documentation is versioned
  evidence, not eternal truth.
- Timeout, authentication/permission, rate limit, invalid request, malformed
  response, unavailable evaluator, and successful empty/unknown semantic
  judgment are distinct outcomes. Retry is bounded and respects request budget;
  a retry must not turn a service error into an answer.
- Credentials remain server-side. State, logs, fixtures, ledger and Admin
  projection exclude API keys, OAuth/refresh tokens, private provider
  credentials, unnecessary raw private content and hidden chain-of-thought.
- A Decision Ledger is a future logical audit record, not a selected database.
  It should reference state/grammar/question/evaluator/policy versions,
  normalized raw judgments, composition, downstream research/canonical effect,
  review and later outcome without forcing unnecessary content retention.
- Future Admin observability may expose bounded counts, decision class,
  grammar/compiler/policy/evaluator versions, latency/usage/cost when known,
  uncertainty/contradiction/abstention rates and escalation/promotion status.
  Missing metrics are not zero; no private content or secret is included.

## 8. Enforcement candidates and implementation status

Future Architecture Guard rules are candidates only if a later runtime makes
them enforceable at import/call boundaries: provider SDK imports only in
provider adapter packages; no evaluator-to-canonical-writer, Source Router or
Authorization Broker path; no private-to-public write; no missing-to-false/zero
coercion; no global confidence policy; no production grammar self-mutation;
and explicit model-version promotion. This slice does not add speculative guard
machinery or change existing suppressions/gates.

No production Jev runtime or Luna runtime is implemented. No SDK or runtime
dependency, database migration, provider adapter, model call, Admin, subscriber,
V2/V3, Source Router, Knowledge Frontier, Research Planner or canonical-writer
runtime is added by this architecture. A later implementation needs its own
authorization and contract tests.

## 9. Open decisions

The following remain open: production evaluator version and alias policy;
calibration requirements and per-decision thresholds; grammar storage and
distribution; state and judgment retention/redaction; raw provider payload
retention; end-to-end idempotency and request budgets; concrete adapter and
resilience configuration; human review/label authority mechanics; actual
representative labels; empirical Jev versus Luna/code comparisons; information
value methodology; exact Knowledge Frontier projection mapping; security review
for private evaluation; runtime observability instrumentation; and whether a
future architecture enforcement rule belongs in Architecture Guard.

None of these open decisions blocks this pre-implementation architecture slice.
