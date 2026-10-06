# Plan â€” TASK-050 Subscriber Brain Output E2E

**Plan status:** root architecture review approved; implementation slice in progress.

## Architecture

This is a narrow composition/read-model slice, not a second Brain or persistence system:

```text
Trusted request / verified subscriber identity
  â†’ existing AuthorizedXeed + TASK-049 OrganizationResolutionPort
       â”œâ”€ IdentityPending â†’ keep private pending locator/resource observation only
       â””â”€ canonical Organization resolved and revalidated
  â†’ authorize Observation Focus and private context
  â†’ read current evidence/memory + temporal MarketMap
  â†’ form the bounded observation plan (reuse MarketMap planner / Prime)
  â†’ preflight complete child fan-out with existing budget reservations
       â”œâ”€ stop + Learning Memory PARTIAL(COST_UNKNOWN) before work; or
       â””â”€ governed acquisition/research and existing EvidenceAdmission boundary
  â†’ deterministic EB-04 / EB-06 / EB-07 reasoning and DRI measurement compilation
  â†’ HumanOutput/EconomicHumanOutput + evidence-bound DRI gap when answerable
  â†’ existing RuntimeSignal / Today / subscriber projection
```

Canonical Organization and public AXIGLAND truth remain shared; subscriber context only authorizes private reads and projection. Private first-party data and private continuity never enter shared public output. An output's subject, state fingerprint, source/instrument lineage and temporal/currentness basis must match at every composition boundary. Partial/failure/unknown states are normal outputs and must survive through the product contract.

### Exact existing contracts to reuse

| Concern | Existing contract | Use in TASK-050 | Limit to preserve |
| --- | --- | --- | --- |
| Subscriber authorization | `application/xeed_access/reader.py`: `AuthorizedXeedReader`, `AuthorizedXeed`; `application/xeed_access/organization_reader.py`: `AuthorizedXeedOrganizationReader`, `AuthorizedXeedOrganization` | Require already-authorized context and canonical Organization before private or projected reads. Root-owned portfolio resolver supplies the bridge. | Trusted request context is not authentication; no new identity authority or tenant store. |
| Canonical Organization intake | TASK-049 `OrganizationResolutionPort.resolve(OrganizationLocator) -> ResolvedCanonicalOrganization | IdentityPending`; `pipeline/entity_resolution/resolver.py`: `ExactNameResolver`; `domain/identity_binding.py`; `EvidenceAdmission` | Name/URL only directs attention. Pending may retain private locator and separately authorized public resource observations, with unresolved subject. Only a resolved existing canonical Organization can enter Focus-bound Brain flow. | Current resolver finds governed existing candidates; it is not entity creation. Identity binding is not truth admission. Never use locator/name as OrganizationId or attach resource observation to Organization pre-resolution. |
| Market posture | `application/economic_discovery/market_entry.py`: `XeedMarketMap`, `MarketParticipation`, `MarketRelationship`, `ParticipationState`; `market_planning.py`: `plan_market_observation` | Consume existing temporal/evidence-backed map and materially adjust object types/questions. | No duplicate map/classifier. Unknown cannot fan out; B2C does not identify consumers. |
| Prime / ResearchValue | `prime.py`, `prime_execution.py`, `research_value.py`, `continuous_observation.py` | Reuse bounded observation plan, decision-bound adaptive route and durable shared intent/leases when authorized. | No second scheduler, no work unless ResearchValue/Prime permits, requester provenance remains separate from shared compute. |
| Evidence and economic output | `first_vertical_e2e.py` â†’ `FirstEconomicVerticalE2EResult`; `subscriber_projection/economic_output.py` â†’ `EconomicHumanOutput` | Compose actual EB-04 output and preserve `ExplainableBasis`, exact support, dimension state and uncertainty. | Evaluator is non-authoritative; admission remains independent; no client/lead/sale assertion. |
| Temporal memory | `observation_memory.py`, `temporal_currentness.py`, EB-06 contracts | Reconstruct/revalidate at explicit aware `as_of`, preserve history, invalidate declared downstream dependencies. | Stale/withdrawn/incompatible evidence cannot silently support current positive output. |
| DRI source access | `source_registry.py`, `application/source_acquisition/contracts.py`, `pipeline/source_acquisition/policy.py`, `HttpSourceSensor` | Only authorized, public, bounded HTTP instruments; retain rights/policy/source/surface/time/provenance. | One page fetch is only page representation. No new scraper, auth or anti-bot. No search/generative claim. |
| Cost and stop | `execution_budget.py`: `ExecutionBudgetPolicy`, `ExecutionBudgetState`, `ExecutionBudgetReservation`, `GovernedExecutionController`, `ExecutionStopReason`; ADR-0029 | Preflight all planned child source/research work (including currency/known cost policy) before any fan-out; reconcile actual use and record partial stop. | Unknown monetary cost is not zero; existing controller remains the authority. Need test atomicity/whole-fanout guarantee. |
| Learning lineage | `learning_memory.py`, `execution_learning.py` | Retain execution, attempt, policy, replay, failure, cost completeness and `COST_UNKNOWN`/partial outcome. | Learning event is operational evidence, not canonical fact or promotion. |
| Subscriber output | `subscriber_projection/economic_runtime.py`, `xignal.py`, `today.py`, `evidence_narrative.py` | Extend existing output compilation/attachment path and preserve Today/evidence paths. | Subject must match canonical Organization; no mutable source projection; no unsupported direct OBSERVED business Xignal. |
| Continuity | ADR-0017 and existing authorized contextual readers/checkpoints, if present | Read actual saved checkpoint only after scope authorization; show then-state/delta/open questions. | Do not invent origin or claim durability where no durable store exists; no model chooses scope. |

## Proposed new seams (subject to review)

1. `application/subscriber_projection/economic_runtime.py` â€” extend in place or add only narrowly required pure composition around existing `EconomicHumanOutput`. Add `SubscriberEconomicRuntime`/equivalent service only if an existing contract cannot express required dependencies. Keep tests at `tests/subscriber_projection/test_economic_runtime.py` if already present, otherwise use a new scoped test file only after review.
2. `application/economic_discovery/first_vertical_e2e.py` â€” only the root-approved retrocompatible cost schedule and maximum-fan-out preflight extension; preserve all evidence-admission and epistemic behavior. Other modules may be added only for narrowly typed composition, never to recreate market planning, budget, Prime, memory or generic source clients.
3. `tools/runtime/subscriber_economic.py` â€” factory reuses TASK-049 identity and portfolio readers plus the independent canonical Organization reader. `SubscriberEconomicRuntime.execute` accepts only an in-process server-owned `SubscriberEconomicExecutionPlan`, reauthorizes the focus, routes one MarketMap directive through an explicit plan catalogue, preflights the bounded EB-04 dispatch set, runs the existing EB-04 composition, persists public governed observations and an immutable output snapshot, then reads it back. No credentials, arbitrary source URL discovery, or fixture fallback exists in the runtime path.
4. Tests only in `tests/subscriber_projection/` and new files under `tests/economic_discovery/`: use fake ports at exact boundaries, assert dispatch counters, persisted stop event, same context and full evidence/temporal provenance. Do not edit concurrent spec 046-owned `first_vertical_e2e.py` tests or other tasksâ€™ tests.
5. `cognition/economic_evaluator_adapter.py` â€” provider-neutral `ModelRouter` adapter for EB-04's bounded structured judgment. The host must inject an exact registered provider and version; output is restricted to one declared choice and reports no fabricated distribution/confidence. No SDK/key detection or automatic live call is added.
6. `specs/050-subscriber-brain-output/` â€” only this new feature's Spec Kit artifacts during this phase. No `.specify/feature.json`, other roadmap or product/architecture document edits.

### Approved bounded EB-04 execution extension

Root approved a retrocompatible extension to `first_vertical_e2e.py` without changing its evidence-admission or epistemic rules. Production composition supplies a `FirstVerticalDispatchCosts` schedule whose source, semantic-extraction and evaluator entries each carry an amount, currency, and versioned cost-basis reference. The runner conservatively reserves the maximum seven dispatches (two public source acquisitions, two extraction calls, and up to three semantic judgments) in the existing `GovernedExecutionController` before the first call. The recorder consumes those pre-reservations; it does not reserve each child a second time. Any unknown/unversioned cost or failed aggregate reservation releases all held capacity, produces a PARTIAL Learning Memory stop, and dispatches no child. No capacity is assumed for arbitrary additional EB-06/EB-07 fan-out; that remains outside this bounded slice.

The route requires exactly one selected OBSERVED/POTENTIAL MarketMap directive and exactly one matching server-owned descriptor. If multiple market directives are active, the caller must select a relationship; if no descriptor matches, routing abstains. B2C descriptors can target only `DEMAND_ARCHETYPE`. The selected descriptor id/version/object type and rejected-route reasons are preserved in the output execution trace. This is a bounded plan router over the existing `plan_market_observation`, not a live universal source planner or a new market classifier.

Deployable server configuration must still supply registry-authorized source plans, extraction/representation ports, an evidence-backed MarketMap, a versioned cost basis, and a registered evaluator capability. The production adapter is available through the cognitive router, but this implementation does not configure a provider, inspect secrets, or claim an external provider call was authorized or run.

The root-owned authorized subscriber/portfolio â†’ `OrganizationResolutionPort` bridge is an input dependency, not part of this feature's edits. Until canonical identity independently resolves, retain an attention-only private `IdentityPending` request and optionally resource-level public observation through existing source policy; do not create a Focus, canonical subject, MarketMap or Brain output. Since existing EB-04 and subscriber-runtime contracts are reference/deterministic, this feature must not call fixture helpers or infer missing inputs into success. Runtime returns an explicit missing-prerequisite outcome until real authorized inputs exist.

## Implemented DRI measurement and remaining contract

The bounded implementation now uses the existing authorized public acquisition and `DocumentRepresentation` output to measure the canonical Organization name in one exact page title. The immutable wire record pins `axignal.public-page-representation@1.0.0`, page resource, source policy and rights/access/reuse/retention/robots references and statuses, representation and normalization versions, observation time, conditions, 1/1 page sample, currentness, field states, uncertainty and claim limits. Unobserved geography/device are `UNKNOWN`; declared page language is retained only when present. A missing phrase in the captured title emits an `INXIGHT_REPRESENTATION_GAP` with `cause=UNKNOWN` and explicit non-established search, generative, social, whole-Organization and SEO/GEO claims. No separate discovery measurement runs. No stored output yields `NOT_MEASURED`; reads reevaluate the measurementâ€™s currentness against the requested `as_of` and temporal policy.

When acquisition or representation fails, the execution response records a structured `NOT_MEASURED` attempt with the reason and a planned/acquired/informative sample count; it never emits a RepresentationGap for that attempt. A changed instrument version causes the current projection to report `NOT_MEASURED/INSTRUMENT_VERSION_MISMATCH`, while the immutable prior measurement remains available as recorded history. There is no cross-version comparison bridge or multi-page denominator. The page-title detector does not establish rendered-page visibility when the source representation reports unresolved visibility.

The first public measurement in scope is a deliberately narrow authorized resource/page representation. It records at least:

- `instrument_ref` and immutable `instrument_version`;
- family/surface exactly measured (for this slice, public web resource/page only);
- target subject resolution and the acquired canonical URL/resource reference;
- frozen detector/query set and expected eligible sample where a presence/absence comparison is claimed;
- geography, language, device/context only when the instrument actually controls/observes them; otherwise explicit UNKNOWN/NOT_APPLICABLE;
- observation time, acquisition method and policy/version, source/provenance/rights, retention and reuse scope;
- eligible sample count, informative denominator, failures/non-informative runs, coverage and uncertainty;
- a separate result state: PRESENT, MEASURED_ABSENCE_WITHIN_SCOPE, NOT_MEASURED, NON_INFORMATIVE, INACCESSIBLE, INSUFFICIENT_SAMPLE, UNKNOWN;
- currentness plus upstream state/instrument fingerprint.

A simple one-page fetch can emit only a page-level PRESENT or measured phrase/non-mention under its exact extraction contract. It has no search query/result set and cannot emit search-rank or web-wide absence. A gap output is allowed only when comparable, governed measures show a difference against evidence-backed Organization context; its description retains conditions and uncertainty, and it states that cause is unknown. No number/score is produced without separately approved deterministic metric formula, sample, denominator and uncertainty.

## Fan-out and cost protocol

1. Resolve authorized subscriber context. Resolve the input locator through TASK-049. If identity is pending, stop Organization-level composition and keep only authorized private pending state/resource observation; do not make a canonical output. For a resolved canonical subject, revalidate the returned Organization ID before loading only relevant state (no sources dispatched).
2. Derive the bounded work list from current MarketMap/Prime/ResearchValue and explicit user attention. UNKNOWN or blocked rights do not become source targets.
3. Bind a `PreflightBundle` conceptually to execution id, code/policy versions, exact state fingerprint, all child dispatch IDs, currency, reservation basis/upper bound, request/source count and deadline. The bundle is not a new authority; it groups `GovernedExecutionController` reservations and supports all-or-nothing preflight.
4. If any child has unknown/unverifiable cost and policy sets `stop_on_unknown_cost`, or aggregate planned reservations exceed any bound, persist PARTIAL stop/Learning Memory and dispatch none. No lease claim, source fetch, external provider call or hidden background work may occur before preflight.
5. After successful preflight only, dispatch each reserved item through current public source policy and Prime ports; reconcile every reservation with measured cost. If measured cost is unknown, preserve known lower bound and incompleteness, stop remaining work under the same policy, and retain completed work/evidence without calling it complete.
6. Current `ExecutionBudgetReservation`/controller supports individual reservations; tests must prove the composition reserves the entire child set before dispatch. If individual reservations cannot enforce all-or-nothing release/atomicity, root review must approve a minimal application coordinator that only composes the existing controller, not a second budget implementation.

## Verification and regression plan

Focused tests (planned, not yet run):

- runtime output is sourced from real `FirstEconomicVerticalE2EResult`, retains exact evidence and no fixture path;
- authorization and subject mismatch; one canonical Organization across 1/2/100 private contexts; same global public evidence cannot reveal private fields;
- MarketMap B2B/B2C/B2G/UNKNOWN plan changes and preserves OBSERVED vs POTENTIAL research intents;
- DRI condition/sample/denominator/instrument version and exact page-only scope; unmeasured vs measured absence; incompatible versions break comparison; rights/currentness fail closed;
- no Recommendation/cause inference from absence; output language never upgrades epistemic state;
- source/instrument change â†’ stale/downstream reevaluation; replay is deterministic and history remains append-only;
- unknown monetary cost among any fan-out member: zero fetches/leases/provider calls, `COST_UNKNOWN`, partial Learning Memory; known reservations sum and reject over budget before dispatch; lower bound and incomplete state survive unknown reconciliation;
- stop/failure/partial outcomes still compile into valid RuntimeSignal/Today without being treated as success;
- continuity origin unknown stays unknown; cross-tenant private context blocked;
- 1/2/100 controlled context integration and full applicable frontend/browser integration proof.

Repository validation is owned by root after the code freeze; this draft does not run or claim tests. Before integration, run focused tests and all prescribed deterministic gates from `AGENTS.md`, with Graphify update/query and diff/governance checks. No production deployment is authorized here.

## Risks and rollback

- **Economic overclaim:** prevent with page/surface family typing, sample/denominator and exact result-state gates; rollback by withholding positive derivation while preserving observations/history.
- **Cost leak before stop:** prove full-fanout preflight by observable zero-dispatch counters, no lease acquisition and a stop event. If the atomicity guarantee cannot be established, disable fan-out and return explicit blocked/unknown.
- **Stale or duplicate knowledge:** preserve observation id/lineage, instrument fingerprints, reuse policy, temporal policies and dedupe keys; invalidate only declared dependent outputs.
- **Subscriber isolation regression:** resolve authorized scope before any private read; test same Organization across distinct tenants and private input isolation.
- **Accidental duplicate architecture:** restrict changes to listed files and adapters; reuse existing contracts, no second truth/memory/market/budget authority.
- **Rollback:** revert this feature's new code/tests; retain append-only observations and prior outputs; no schema migration/provider/deployment in the proposed slice.
