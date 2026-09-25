# P0-ADMIN-01 Contract Catalogue

**Status**: PROPOSED / PRE_IMPLEMENTATION\
**Authority**: Subordinate to MASTER, Constitution, accepted ADRs, Atlas and
accepted domain architectures.\
**Interpretation**: Semantic responsibilities only; not executable interfaces,
database schemas, APIs, event sourcing, storage choices or runtime evidence.

## Shared envelope and rules

Every contract uses only applicable fields from this conceptual envelope:

```text
record_id, record_type, schema_version, producer/owning_domain,
subject_refs[], occurred_at?, observed_at?, effective_at?, recorded_at,
correlation_refs[]?, causation_ref?, policy_refs[]?, outcome_state,
completeness, unknown_reason?, provenance_refs[]?, privacy_class/scope
```

Time, scope, provenance, policy version, outcome and completeness must be
preserved when they affect interpretation. IDs are references, not authority.
No contract requires copying raw source payloads, private documents, full model
prompts/responses, hidden reasoning, credentials or unrelated subscriber data.
`UNKNOWN`/missing is not zero, false, empty or free. Operational failures,
epistemic insufficiency, policy denial, security denial and expected unknown
remain distinct. Correlation alone is not causation.

## C01 — Admin Projection Contract

- **Producer / consumer**: Authorized projection layer / human Admin, export
  surfaces and future internal Admin MCP.
- **Must convey**: projection/schema version, scope, generated/as-of time,
  completeness, filters, key operational state, metric definitions/observations,
  attention reasons and inspectable lineage references.
- **Invariant**: projection is a read model over domain-owned sources, not a
  source of truth; human and agent projections preserve the same semantics.
- **Failure / unknown**: partial/unavailable/denied state and omitted scope are
  explicit; do not fabricate zero metrics or readiness.

## C02 — Operational Event Contract

- **Producer / consumer**: Owning service / bounded operational projections.
- **Must convey**: typed event, event/schema version, owner, subject references,
  applicable time, outcome, failure class and correlation/causation links where
  known.
- **Invariant**: an operational event is distinct from a log line, metric,
  canonical domain event, AXIGLAND `TemporalEvent` and canonical FAXT. It is an
  AXIGLAND `TemporalEvent` only when its canonical domain owner explicitly
  records a canonical entity transition with its own state/evidence references
  under the applicable admission rules. No event-sourcing platform is implied.
- **Failure / unknown**: incomplete emission or unknown outcome is represented;
  retries and duplicate delivery must not be mistaken for multiple domain
  transitions.

## C03 — Correlation / Causality Contract

- **Producer / consumer**: Participating services / cross-system trace view.
- **Must convey**: optional typed references such as account, Xeed, research
  run, question, job, source request/observation, cognitive task, decision,
  canonicalization, report or connection; distinguish correlation from direct
  causation and identify the causal edge when established.
- **Invariant**: a record need not contain every identifier; matching IDs or
  time proximity do not prove cause.
- **Failure / unknown**: missing/unavailable IDs remain absent/unknown, not
  synthesized.

## C04 — Temporal Observation Contract

- **Producer / consumer**: Every event/observation producer / temporal Admin
  projections and metric calculations.
- **Must convey**: applicable `occurred_at`, `observed_at`, `effective_at`,
  `recorded_at`, `started_at`, `completed_at`, time zone/precision where
  meaningful, and policy/projection version for historical reconstruction.
- **Invariant**: these meanings are not collapsed into `created_at`; later
  knowledge does not silently rewrite what was known earlier.
- **Failure / unknown**: missing or incomparable time is surfaced, not
  interpolated as observed fact.

## C05 — Xeed Lifecycle Observability Contract

- **Producer / consumer**: Xeed/germination owner / Command Center and Xeed
  Observatory.
- **Must convey**: lifecycle state/transition, trigger, stage, start/finish,
  blocker, readiness evaluation/reference, cancellation/retirement when
  applicable, and real supporting events.
- **Invariant**: Admin projects actual state; no fake percentage, synthetic
  progress, `DONE` state or readiness claim.
- **Failure / unknown**: queued, active, partial, blocked, stalled, failed,
  cancelled and unavailable are distinct where known.

## C06 — Knowledge Frontier Observability Contract

- **Producer / consumer**: Knowledge Frontier/research owner / AXIGLAND quality
  and Command Center projections.
- **Must convey**: gap/question reference, domain, materiality rationale,
  expected information-gain estimate if available, currentness need, attempts,
  contradiction links, exhausted/stopping reason, unknown-private/not-observable
  class and resolution transition.
- **Invariant**: distinguish unresearched, researched-but-insufficient,
  private/unobservable, contradictory, stale and resolved; Admin does not
  promote a gap to a fact.
- **Failure / unknown**: unknown estimates remain unknown; no universal frontier
  or knowledge score.

## C07 — Research Run Observability Contract

- **Producer / consumer**: Research orchestrator / AXENT-Research and
  operational diagnosis.
- **Must convey**: trigger taxonomy/reference, objective/question, planner and
  source-policy references, Xeed/job scope, attempts, stage outcomes, next
  action, stop reason, latency, cost and knowledge/reuse references where
  available.
- **Invariant**: trigger allocates attention only and has no canonical write
  authority; structured operational reasoning is exposed without hidden
  chain-of-thought.
- **Failure / unknown**: provider failure, policy denial, security denial,
  epistemic insufficiency, contradiction, budget exhaustion and expected unknown
  remain distinct.

## C08 — Source Acquisition Observability Contract

- **Producer / consumer**: AXIGNAL source policy/router/adapters / source
  observatory and research run projection.
- **Must convey**: AXIGNAL `SourceRequest`/`SourceObservation` references,
  capability, selected adapter, HTTP/browser path, policy/escalation reason,
  source identity, observation time, response/denial/rate-limit state,
  provenance, latency, cost reference and reuse where relevant.
- **Invariant**: sources provide observations, not truth or instruction
  authority; respect ADR-0010 and its deferred engine selection.
- **Failure / unknown**: blocked/denied, timeout, unavailable and empty result
  are not fabricated evidence; no stealth escalation is implied.

## C09 — Cognitive Usage Observation Contract

- **Producer / consumer**: `CognitiveProvider`/`ModelRouter` adapters / provider,
  cost and research projections.
- **Must convey**: cognitive-task and model-policy version references, provider
  and model when available, operation class/mode, measurable usage fields and
  their known/unknown state, latency, retries/outcome, cost reference and
  authorized Xeed/report correlation.
- **Invariant**: provider/model is policy, not domain authority; context and
  output content are not copied for convenience. Luna is not hard-wired in
  Admin.
- **Failure / unknown**: missing tokens or price are unknown, not zero; provider
  failure does not change epistemic truth.

## C10 — JEV Decision Observation Contract

- **Producer / consumer**: Future bounded JEV owner / research and governance
  projections.
- **Must convey**: decision class, structured input reference, result class,
  structured uncertainty/missing-information/contradiction references,
  decision-policy version, latency/cost where observed and next-action
  implication.
- **Invariant**: no JEV implementation is assumed; no universal confidence
  threshold, hidden reasoning or direct canonical write is specified.
- **Failure / unknown**: unavailable, unresolved, ambiguous, insufficient and
  policy-denied are distinct.

## C11 — Canonicalization Observation Contract

- **Producer / consumer**: Evidence admission/canonicalization owner / audit
  and AXIGLAND observability projection.
- **Must convey**: candidate/decision/admission references, policy version,
  supporting evidence/provenance refs, result, canonical object refs, prior and
  resulting revision refs, effective time and unresolved contradictions.
- **Invariant**: Admin observes but does not execute canonicalization; a trigger,
  provider or JEV result alone is not authority. Existing evidence-admission
  rules remain controlling.
- **Failure / unknown**: rejected, deferred, unresolved and admitted outcomes
  are explicit; no claim is inferred from a missing write.

## C12 — Epistemic Transition / Lineage Contract

- **Producer / consumer**: Canonical domain owner / quality observatory.
- **Must convey**: domain object reference, prior/new epistemic and currentness
  state, effective/observed time, derivation and evidence/source references,
  transition policy and contradiction links.
- **Invariant**: Admin references a domain-owned transition; it does not create
  epistemic state. Maintain FAXT/INXIGHT/PATHX/relationship separation.
- **Failure / unknown**: incomplete lineage and unknown currentness remain
  visible; no `UNKNOWN` → `FALSE` coercion.

## C13 — Cost Observation Contract

- **Producer / consumer**: Provider, billing, compute or domain operation / unit
  economics projection.
- **Must convey**: observation ID/time, category, provider/service/operation
  class where known, usage quantity/unit, amount/currency if authoritative,
  pricing authority/version/effective time, related Xeed/account/job/report/
  connection refs, and unknown reason.
- **Invariant**: usage, monetary amount and authority may be independently
  known/unknown. Preserve `TRIGGERED_COST`, `ATTRIBUTED_COST`, `SHARED_COST` and
  keep `AVOIDED_RECOMPUTE` as a reuse observation, not negative spend.
  `COST_PER_ACTIVE_XEED_MONTH` and MASTER's `COST_PER_LIVE_XIGNAL` are distinct
  metrics with distinct denominators; no conversion or substitution is implied.
- **Failure / unknown**: no known amount defaults to zero or free; no invented
  historical prices.

## C14 — Cost Attribution Contract

- **Producer / consumer**: Versioned attribution calculation / cost metrics.
- **Must convey**: source CostObservation refs, target scope, attribution class,
  allocation basis/weights, included/excluded cost, shared-cost policy/version,
  time window, output amount/currency and completeness/uncertainty.
- **Invariant**: an attribution is derived, not extra spend; do not silently
  distribute shared fixed cost or double-count triggered plus attributed cost.
- **Failure / unknown**: unavailable allocation basis remains unknown/partial;
  assumptions and exclusions are inspectable.

## C15 — Knowledge Gain Observation Contract

- **Producer / consumer**: Domain/research outcome producer / knowledge
  economics projection.
- **Must convey**: decomposed result references such as newly admitted or
  corroborated FAXTs, resolved gaps/contradictions, verified relationships,
  renewed currentness, reusable evidence or material updates, plus time and
  research/cost references where available.
- **Invariant**: only domain owners establish canonical outcomes; one opaque
  universal score and unsupported causal claim are prohibited.
- **Failure / unknown**: not measured/unavailable is not “no knowledge gained.”

## C16 — Reuse / Avoided-Recompute Contract

- **Producer / consumer**: Reuse-aware research/cost attribution / economics.
- **Must convey**: reused evidence vs reused canonical knowledge vs new
  computation vs refresh/currentness work, source refs, consuming run/Xeed,
  deduplication identity, avoided action and valuation method/version if any.
- **Invariant**: reused knowledge is not counted as newly created; avoided
  compute is counterfactual and not negative monetary cost unless a declared
  measurement method supports a separate derived saving.
- **Failure / unknown**: absent counterfactual evidence means avoided value is
  unknown, not zero or proven savings.

## C17 — Admin Metric Definition and Lineage Contract

- **Producer / consumer**: Versioned metric definition/calculator / Command
  Center, exports and explanation layer.
- **Must convey**: stable metric ID/version, purpose, unit, formula semantics,
  numerator/denominator, source event/observation types, attribution and
  aggregation method, time window, filters/exclusions, freshness, completeness,
  unknown handling, policy refs and lineage refs.
- **Invariant**: no material Admin metric without lineage; arithmetic is not
  opaque; metric is not source evidence or domain truth.
- **Failure / unknown**: partial input produces explicitly partial/unknown value
  and disclosed exclusions; never silently replace a missing value by zero.

## C18 — Provider Health Observation Contract

- **Producer / consumer**: Provider/adapter health probes or request outcomes /
  System & Providers projection.
- **Must convey**: provider capability, health state, observed time, latency,
  error/retry/backlog/rate-limit and relevant operation/policy references.
- **Invariant**: health observation describes service behavior, not economic
  truth or provider authority over AXIGNAL.
- **Failure / unknown**: no probe or stale probe is unavailable/unknown, not
  healthy.

## C19 — Customer Operations Observation Contract

- **Producer / consumer**: AXIGNAL account, subscription, billing, support or
  product-use owner / Business & Customer Operations projection.
- **Must convey**: AXIGNAL account/user scope, subscription/payment/product
  lifecycle, support/claim-review/export/Product MCP use and time/provenance
  appropriate to first-party operations.
- **Invariant**: first-party AXIGNAL service state only (ADR-0008); no leads,
  pipeline, customer CRM objects, outreach, sales tasks or workflow engine.
- **Failure / unknown**: source-of-record uncertainty or missing lifecycle
  state remains explicit; this contract does not infer economic truth about an
  observed organization.

## C20 — Claim Review Observability Contract

- **Producer / consumer**: Claim Review/research owner / quality and governance
  projections.
- **Must convey**: request ID/requester scope/reason, challenged claim and
  evidence refs, investigation state, new/contradictory evidence refs, decision
  policy, outcome (`UPHELD`, `REVISED`, `RETIRED`, `UNRESOLVED`) and times.
- **Invariant**: request triggers independent reinvestigation, not editing;
  Admin does not adjudicate truth.
- **Failure / unknown**: unresolved and disputed are not false; missing review
  progress is not closure.

## C21 — V2 Analytical Observability Contract

- **Producer / consumer**: Future V2 report/AEAP runtime / report operations and
  economics projection.
- **Must convey**: report lifecycle/readiness, Xeed/projection/AEAP versions,
  question/branch counts and stopping reasons, synthesis/contradiction and
  alternative-explanation references, Red Team outcomes, finding support state,
  evidence coverage, research/cognitive escalation, latency/cost and reuse.
- **Invariant**: V2 remains a projection; findings and narrative do not become
  canonical FAXTs. Proposed/pre-implementation status stays explicit until
  runtime evidence proves otherwise.
- **Failure / unknown**: incomplete analysis, partial support and unknown cost
  remain distinct; do not expose fabricated finding counts.

## C22 — V3 Private Operational Observability Contract

- **Producer / consumer**: Future private capability/connector/report owners /
  authorized Admin metadata projection.
- **Must convey**: tenant-scoped connection/adapter health, capability request
  and authorization state, scope reference, access mode, cost, normalization,
  private report lifecycle, revocation/retention/deletion and security-event
  references.
- **Invariant**: operational metadata is not private-content access. Exclude
  payloads, CRM opportunities, documents, strategy, prompts, context and Private
  Findings by default. No Admin-to-AXIGLAND private write.
- **Failure / unknown**: authorization, revocation, deletion and retention
  outcomes must be observable without showing secrets/content; missing state is
  not proof that access stopped.

## C23 — Security / Governance Event Contract

- **Producer / consumer**: Authorization, policy, security, export and Admin
  operation owners / governance audit.
- **Must convey**: event type, actor/service reference, subject/scope, decision,
  policy version, time, target operation, outcome, severity/impact class and
  audit correlation. Secret values are prohibited.
- **Invariant**: append-oriented/auditable where required by authority; do not
  place credentials, tokens, raw private payloads or prompt content into event
  fields.
- **Failure / unknown**: denied, suspicious, failed-to-audit and unavailable
  are explicit; no security success is inferred from absent events.

## C24 — Admin Authorization Boundary Contract

- **Producer / consumer**: Future identity/authorization owner / Admin read,
  export and command surfaces.
- **Must convey**: actor class, capability/scope, resource/tenant scope,
  purpose, decision, policy version and audit reference; sensitive commands
  identify the owning domain service that executes them.
- **Invariant**: authenticated internal access, least privilege, separate
  subscriber/Product MCP/Admin MCP credentials and authorization, no default
  private-content access, and no direct canonical mutation.
- **Failure / unknown**: deny-by-default for unknown scope; denied is not empty
  data and not permission to broaden access.

## C25 — Admin MCP Read Contract

- **Producer / consumer**: Future Admin Projection / separately authorized
  internal agent.
- **Must convey**: bounded read/query result, projection/schema version, scope,
  completeness, metric/event lineage references and pagination/cursor semantics
  when later specified.
- **Invariant**: internal, read-only by default, least privilege, no canonical
  write authority, separate from Product MCP, no private-content access by
  default; human-readable comprehension does not depend on an agent.
- **Failure / unknown**: denied, partial, unsupported and unavailable are
  explicit; tools cannot turn arbitrary query text into authority.

## C26 — Retention / Minimization Contract

- **Producer / consumer**: Data owner, privacy/security policy / event,
  projection and export lifecycle.
- **Must convey**: data class (operational, economic, provider usage, audit,
  security, private metadata or private-content reference), purpose, scope,
  minimization rule, retention-policy version, deletion/revocation state and
  audit references.
- **Invariant**: metadata-first; no arbitrary forever-retention; prompts,
  responses, raw source/private payloads and credentials are not retained merely
  for debugging; exact periods are governed later.
- **Failure / unknown**: unknown retention/deletion state is surfaced; absence
  of a deletion event is not proof of deletion.

## Instrumentation priority

### MUST_EMIT_FROM_FIRST_RUNTIME

- Shared identity/version/owner/scope/completeness/time semantics for every
  material event/observation.
- Correlation and causal reference when known; domain policy/version and stable
  provenance references when relevant.
- Xeed, research, source request/observation, cognitive task, JEV decision,
  canonicalization result and epistemic transition metadata as each respective
  runtime is introduced.
- Usage and cost observations, including unknown/partial state and cost
  authority; cost attribution policy for any reported attributed metric.
- Security/authorization/governance decisions, exports and privileged Admin
  actions without secrets or unrestricted content.
- First-party customer/product lifecycle metadata needed for service operation.
- V2 report/AEAP and V3 private-operation metadata when those products are
  separately implemented; V3 content remains excluded by default.

### SHOULD_EMIT

- Decomposed knowledge-gain, evidence reuse and avoided-recompute observations
  where the system can substantiate them.
- Provider latency/retry/capability outcomes, currentness/freshness and
  explanation-coverage dimensions that materially support diagnosis.
- Human-interpretable failure stage, impact and next-action references.

### OPTIONAL_LATER

- Additional anomaly analytics, cohort comparisons, advanced visual summaries
  or derived metrics that have a defined decision purpose and approved lineage.
- No vanity score, speculative event inventory or raw-content retention is
  required by this class.
