# AXIGNAL P0-JEV-01 Opportunity Map and Reconciliation

**Reviewed:** 2026-09-25
**Status:** Research/supporting evidence; no new domain authority.
**Baseline:** `43ac8eb2d29ce2358331dab07a4599574c4dfc2c`.

## Existing architecture reconstructed before the proposal

| Concern | Repository truth before P0-JEV-01 | Architectural implication |
|---|---|---|
| Canonical world and evidence | MASTER defines one AXIGLAND; `EvidenceAdmission` is the current gate for FAXT/observed relationships. | Evaluator output can only be a candidate input to AXIGNAL policy and evidence admission. |
| Epistemics and time | `EpistemicState`, `Currentness`, `Observability`, `truth_value()` and tests preserve UNKNOWN; relationship classes distinguish OBSERVED, POTENTIAL, HISTORICAL. | Do not collapse support/currentness/relationship class or add JEV output to canonical epistemic enums. |
| Cognitive providers | `CognitiveProvider`, `ModelRouter`, cognitive jobs and Echo form a small replaceable/provider-neutral skeleton. | Structured evaluation needs its own contract/adapter mapping; no domain SDK import or Jev hardwire. |
| Knowledge Frontier | Existing `KnowledgeFrontier` has unresolved questions, stale claims, candidate expansions and priority state. | Use it as the only AXIGNAL unresolved-knowledge representation; richer decision-gap projection may be specified without a parallel store. |
| Research Planner and acquisition | Brain/Atlas specify shared gap prioritization and targeted source acquisition; implementations remain partial/specification. ADR-0010 defines an AXIGNAL-owned source request/observation boundary; no selected runtime. | The evaluator may identify a dimension to investigate; only existing policy may prioritize and route acquisition. |
| Deterministic preparation | Partial normalization/entity-resolution, feature/evidence models and admission tests exist; no unified decision state builder/composer. | Python stages/state compiler are proposed boundaries, not claims of existing runtime. |
| V3/private | V3 product spec and V3.1 capability reconciliation require tenant-scoped private analysis and separation from public AXIGLAND. | Private state/evaluations remain authorized and tenant-scoped; private result cannot supply public FAXT. |
| Subscriber/Ask AXENT | Product and interaction specs make subscriber attention/disputes context, not control over canonical truth. | A dispute can trigger review/research; user assertion is not a label or truth. |
| V2/AEAP | Proposed V2 report product over canonical state; no runtime. | Structured judgments may eventually inform report analysis only through governed derived projections, not provider internals. |
| Admin | Proposed Admin observability excludes private content and does not own semantics. | Expose minimized metadata only after an owning runtime exists; Admin is not a decision engine. |
| Build/test architecture | Python 3.11+, uv, strict typing/lint/tests, deterministic architecture/governance gates; no JEV dependency. | Python is the proposed future adapter language. Production CI must remain offline and provider-independent. |

Graphify queries for decision/evidence/admission/Knowledge Frontier/Research
Planner and JEV/TypeSafe/confidence returned evidence clusters around
`domain/evidence/admission.py`, `domain/knowledge_frontier/model.py`, MASTER
§14/§15, the Brain/Xeed architecture and the P0-ARCH-01 gap ledger. Graphify
corroborates navigation only; source and deterministic tests establish
implementation status.

## Reconciliation against higher authority

- **MASTER:** No conflict. MASTER §§11, 14, 15, 19 and 20 define Knowledge
  Frontier, the AI/Python/JEV split, claim/write separation, separate internal
  dimensions and temporal meaning. Its example confidence values are internal
  and its product statement expressly forbids exposing raw JEV confidence as
  false precision. P0-JEV-01 preserves this distinction.
- **Constitution / ADRs:** No conflict. ADR-0006's provider boundary applies;
  ADR-0007's offline deterministic CI applies; ADR-0008 blocks CRM/workflow
  drift; ADR-0009 confirms graph semantics do not become renderer/provider
  semantics; ADR-0010 keeps Source Acquisition authority separate.
- **Atlas / Brain:** No conflict. The Atlas records JEV selection/API and a
  connected decision-state builder as open/unimplemented. Brain assigns JEV a
  bounded role and already describes Python, cognition, Knowledge Frontier,
  Research Planner and canonical policy responsibilities. This slice fills
  the missing decision-grammar/state/composition/lab architecture without
  claiming runtime completion.
- **AXIGLAND:** No conflict. One canonical economic world remains. No external
  graph/evaluator/provider type becomes AXIGLAND entity or truth.
- **V2 / V3.1 / Admin / interaction:** No conflict found. No report, private
  capability, access authorization, CRM, subscriber, or Admin authority is
  added or altered.
- **Source architecture:** No conflict. No adapter, crawler, Source Router,
  OAuth or acquisition path is changed.

No MASTER amendment, new ADR, or authority escalation is required for this
pre-implementation architecture. TypeSafe Jev is specified as the initial
replaceable evaluator implementation, not a production dependency or pinned
calibrated production model. A runtime, version pin, new persistence, private
data processing, production thresholds, or enforcement semantics require
follow-on review.

## Initial question opportunity map

| Family | Candidate atomic judgment dimensions | Keep deterministic / authority boundary |
|---|---|---|
| Entity alignment | same-entity semantic compatibility; name/domain/geography/business-description compatibility; identity contradiction | Exact canonical identifiers, normalization and candidate generation are Python. Jev cannot merge. Abstention is valid. |
| Claim ↔ evidence support | excerpt quote present; excerpt semantically supports exact candidate claim; material contradiction in context | Quote/provenance/reference checks are deterministic. Jev cannot invent evidence or promote Luna text. |
| Economic relationship | evidence supports a relationship; relationship type; direction; explicit/economic nature; observed-vs-inferred language; current-vs-historical language; representation-only alternative; contradiction | Identity, duplicate-source grouping, source authority, time math, rights and admission remain code/policy. Dimensions are separate and family state is bounded. |
| Capability evidence | explicitly offered; operationally evidenced; historical; marketing-only; third-party corroboration; representation-only; contradiction | Do not infer capability truth from marketing or a score. Candidate assessment is not a FAXT. |
| Representation/contradiction | which stated interpretation best fits an excerpt; whether an alternative representation is plausible; whether sources materially disagree | AXIGNAL preserves observable economic identity; surprise is not itself an error. Contradiction cannot be averaged away. |

The initial grammar is a candidate catalogue, not a final AXIGNAL ontology. Only
questions with a decision consumer and measurable label path should advance to
evaluation. The question must define when no option fits and when evidence is
insufficient; missing evidence never means false.

## Candidate routes and escalations

| Condition after composition | AXIGNAL route | Forbidden shortcut |
|---|---|---|
| Deterministic condition available | Python exact calculation/lookup/invariant | Paying an evaluator for date subtraction, count, unit conversion, or equality. |
| Narrow ambiguity with bounded output | StructuredEvaluator over family-specific state | Asking Jev to plan research, narrate a report, authorize, or mutate canonical state. |
| Open-ended interpretation / hypothesis | Existing cognitive provider/Luna policy | Converting Luna response to FAXT without admission. |
| Missing/weak/discriminating evidence | Structured gap requirement → Knowledge Frontier → existing Research Planner | Every low confidence or Noul near .5 triggers research. |
| Source/evaluator unavailable | Operational failure, bounded retry or review | Failure represented as a semantic negative. |
| Private requirement | Tenant-scoped V3.1 capability and authorization path if material and justified | Jev asks OAuth or private data automatically. |
| Sufficient structured evaluation | Candidate decision proceeds to independent AXIGNAL policy and canonical gate where applicable | `SUFFICIENT` treated as canonical. |

## Experimental design: no results claimed

The Decision Laboratory is specified as offline/replayable. The 38 adversarial
scenarios are defined in the P0-JEV-01 contract catalogue. They are synthetic
behavioral assertions, not TypeSafe calls, labeled production truth or proof of
calibration. Metrics must match a decision class and independently supported
labels. Compare one controlled variable at a time where practical; record
corpus/sampling, versions, changed state/question paths, outputs, policy,
review/outcome, failures, usage and missingness. Model and grammar promotion
must evaluate regressions in high-cost errors such as false entity merges, not
just aggregate accuracy. No targets or thresholds are invented.

The live endpoint was not called. Credential availability was not tested or
revealed. No API key was requested or stored. Production Jev/Luna integration,
real calibration and cost remain unproven.
