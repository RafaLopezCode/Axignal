# TASK-050 â€” Subscriber Brain Output E2E

**Status:** DRAFT â€” architecture review required before implementation
**Authority:** MASTER Â§Â§5â€“7, 53â€“55, 56.22 â†’ Constitution â†’ applicable ADRs/contracts â†’ this feature
**Roadmap:** EB-04/06/07 composition into EB-08; it does not replace or fork the Economic Brain roadmap.
**Scope:** A governed, subscriber-authorized read path from real economic/representation observations to a Human-First subscriber projection, with market-posture routing, currentness/continuity and cost fail-closed before fan-out.

## Product boundary

AXIGNAL is an OaaS that returns evidence-backed outputs about an Organization. A subscriber may register 1, 2 or 100 Organizations as observation contexts. Registration directs attention and creates no Organization truth, evidence, market participation, digital absence, opportunity or customer relationship. Customer Zero remains AXIGNAL's own internal use and is not subscriber onboarding.

An input Organization name/URL is only an attention locator. It must pass the subscriber identity/portfolio `OrganizationResolutionPort` boundary. If no existing canonical Organization is independently resolved, the request remains private `IdentityPending`: no canonical Organization ID, Observation Focus, Organization-level DRI claim, MarketMap, capability, Signal or economic output is created. A separately authorized public resource observation may be kept against the pending request/locator with unresolved subject status, but it may say only that the resource was observed and identity is unresolved. It cannot be attributed to an Organization or attached to a canonical output. After an independent identity decision resolves a global Organization, the server revalidates the canonical ID and exact evidence/identity bindings before output projection.

This feature reuses the single canonical Organization and existing authorized-Xeed/Observation Focus boundary. Subscriber context only authorizes a projection/retrieval; public observations remain governed by their existing source, evidence, reuse and admission contracts. Only explicit EvidenceAdmission may change canonical facts. Outputs are derived and explainable; opportunities remain POTENTIAL or UNKNOWN.

The output path must compose existing EB-04 economic reasoning, EB-06 temporal memory, EB-07 research/continuous-observation and EB-08 subscriber RuntimeSignal/Today contracts. It must produce a real result from governed runtime inputs or an explicit, inspectable `UNKNOWN`/partial outcome. Fixture-only economics, invented reasons, empty-state-as-negative inference and opaque universal scoring cannot be presented as Brain output.

Digital Representation Intelligence (DRI) may contribute a measured, condition-bound representation observation. One public website fetch only measures what that fetched resource represented under its captured conditions. It cannot establish search/generative/social presence or absence, whole-organization representation, SEO/GEO quality or the cause of a representation gap. `NOT_MEASURED`, inaccessible, insufficient sample, unknown surface, and measured absence are distinct states. A RepresentationGap is derived, scope-bound INXIGHT; recommendations are conditional investigation guidance and never SEO/GEO execution or reputation management.

## Users and scenarios

### US1 â€” Receive an evidence-backed Organization output

As a subscriber, I can register an Organization and receive the current Brain output that AXIGNAL can support, including what was observed, what may matter, what remains unknown, when it was measured and how to inspect the evidence.

**Acceptance scenarios**

1. Given an authorized Observation Focus and a real EB-04 result whose Organization matches the authorized canonical Organization, when the runtime projects it, then the existing RuntimeSignal contract contains the same POTENTIAL/UNKNOWN state, scope, basis, temporal state and evidence lineage.
2. Given an output for another Organization, when it is attached to the subscriber projection, then the operation fails closed and no content crosses contexts.
3. Given no qualifying observations, when the output is composed, then it says the matter is unknown/not measured and carries a reason; it does not imply no capabilities, no demand or poor digital representation.
4. Given an output whose material evidence is stale, withdrawn, rights-blocked or no longer reusable, when it is read, then the projection marks it stale/unknown or withholds the affected conclusion and preserves the historical output/lineage.

### US2 â€” Measure digital representation without overstating it

As a subscriber, I can inspect representation evidence under its actual instrument and conditions, and distinguish an observed surface result from business truth or a missing measurement.

**Acceptance scenarios**

1. Given a single public webpage acquired through the existing authorized HTTP/source policy, when compiled, then the only positive claim is about the exact page/resource and captured time/conditions; it does not become a search, generative, social or broad-web result.
2. Given no executed measurement instrument, when representation is projected, then status is `NOT_MEASURED`/`UNKNOWN`, never `ABSENT`.
3. Given an executed, versioned instrument with identified surface, frozen query/prompt set, geography, language, context/device where material, sample, informative denominator, time, source/provenance and uncertainty, when the measured set has no mention/citation, then AXIGNAL may describe absence only within that exact eligible set and window. It preserves coverage and cannot claim global absence.
4. Given incompatible instruments, versions, surfaces, samples or conditions, when two periods are compared, then no change/gap magnitude is asserted without a validated comparison bridge.
5. Given a measured representation gap, when guidance is emitted, then each recommendation is tied to the measured scope and observed Organization context, qualified as a possible investigation, with no causal claim about SEO, GEO, communications or marketing and no campaign/task execution.

### US3 â€” Let market posture change research

As a subscriber, I can see observation strategy that reflects the Brain's temporal B2B/B2C/B2G posture, while preserving observed participation separately from potential participation and unknown.

**Acceptance scenarios**

1. Given an existing `XeedMarketMap` with B2B `OBSERVED`, B2C `POTENTIAL` and B2G `UNKNOWN`, when an observation plan is composed, then it reuses `plan_market_observation`, confirms existing B2B participation, tests potential B2C aggregate Demand Archetypes without targeting persons, and creates no B2G target from UNKNOWN.
2. Given a new state fingerprint or relevant posture change, when the next assessment runs, then the plan is reevaluated and prior history is preserved; posture is not a permanent Organization identity.
3. Given no evidence-backed posture reader/input, then posture remains UNKNOWN and the composition reports the missing prerequisite rather than manufacturing a map from registration/profile input.

### US4 â€” Bound monetary exposure before work fan-out

As a subscriber and AXIGNAL operator, I can rely on research stopping before any source/research fan-out when monetary spend cannot be governed within the active policy.

**Acceptance scenarios**

1. Given a monetary policy with `stop_on_unknown_cost=True`, when the accumulated monetary state is incomplete or any planned child dispatch has no policy-backed cost reservation, then the controller returns `COST_UNKNOWN` before any child source fetch, provider call, durable lease or fan-out; a partial Learning Memory event is retained.
2. Given known same-currency reservations for a bounded fan-out, when preflight occurs, then the aggregate reservations fit the amount/request/source/deadline limits before any work begins; otherwise there is zero child dispatch.
3. Given actual cost later becomes unknown or differs from the reservation, when usage reconciles, then the known lower bound and incomplete flag survive, no later dispatch is authorized under stop-on-unknown, and all partial evidence/results remain inspectable.
4. Given a zero-cost instrument, then zero must be backed by an explicit versioned contractual source/evaluator cost policy; absence of a quoted charge is UNKNOWN, not zero.

### US5 â€” Resume a truthful investigation

As a subscriber, I can resume a prior Organization investigation and understand what was known then, what changed, and what remains open, without invented origin or cross-tenant/client leakage.

**Acceptance scenarios**

1. Given an existing stored checkpoint, when its authorized private scope and evidence versions are resolved, then the projection retains its actual origin/open questions/as-of state and shows subsequent deltas.
2. Given absent origin, missing checkpoint or expired access, then origin remains UNKNOWN and retrieval fails closed or returns the allowed partial state; it does not reconstruct rationale from current evidence.
3. Given a changed upstream observation or instrument, then downstream currentness/reasoning is invalidated according to declared dependencies while prior checkpoints remain immutable.
4. Given two tenants/contexts observing the same canonical Organization, then only rights-authorized public evidence can be reused; private observations and cognitive continuity remain isolated.

## Functional requirements

- **FR-001:** Resolve and authorize the subscriber context before reading any tenant-private Observation Focus, projection, continuity or first-party observation. Reuse the accepted authorized read contract; do not add a second identity/tenant authority.
- **FR-002:** Treat subscriber name/URL as an `OrganizationLocator`, never as canonical identity. Reuse TASK-049 `OrganizationResolutionPort.resolve(locator) -> ResolvedCanonicalOrganization | IdentityPending`. Only a separately governed resolved canonical Organization can have an Observation Focus, Organization-level Brain output or canonical subject projection. Pending public-resource observations remain attached to the pending request with unresolved subject; do not create/duplicate an Organization or accept subscriber input as canonical facts.
- **FR-003:** Consume real EB-04 output (`FirstEconomicVerticalE2EResult`/`EconomicHumanOutput`) and existing EB-06/EB-07 state when available. Fixture inputs are test-only. Missing runtime integration yields explicit UNKNOWN/partial, not a fabricated success.
- **FR-004:** Compile into the existing subscriber RuntimeSignal, evidence narrative and Today/read-model shapes. Preserve scope, epistemic/temporal status, uncertainty, exact basis and eligible evidence refs; reject subject mismatch.
- **FR-005:** Reuse `XeedMarketMap`, `MarketParticipation`, `plan_market_observation`, ResearchValue, Prime, existing shared work/leases and declared invalidation dependencies. Do not create a duplicate MarketMap, scheduler, memory, budget or evidence authority.
- **FR-006:** MarketMap is temporal and evidence-backed. OBSERVED and POTENTIAL have separate explainable basis and research intent. B2C targets aggregate Demand Archetypes, never named consumers. UNKNOWN remains explicit and is not made an observation target merely to complete a taxonomy.
- **FR-007:** DRI observations are bound to a versioned instrument, source/surface, exact conditions and time, sample and informative denominator, coverage, uncertainty, subject resolution, lineage, rights and currentness. Non-informative/inaccessible/unmeasured results are not negative observations.
- **FR-008:** A page-level HTTP observation proves only what the exact acquired page showed under that acquisition. It cannot be relabeled as search ranking, generative mention, public conversation, business truth or whole-web absence.
- **FR-009:** Any RepresentationGap is a derived INXIGHT, never FAXT. It exposes the observed-vs-expected comparison basis, scope, conditions, sample, uncertainty and currentness. It does not attribute cause to poor SEO/GEO/marketing or execute remediation.
- **FR-010:** Compare measurements only within compatible instrument/method versions and conditions, or a separately validated bridge; upstream changes create a new comparison series or invalidate downstream currentness without rewriting history.
- **FR-011:** Before fan-out, compute a bounded work set and preflight its requests, sources, deadlines and monetary reservations with the existing `GovernedExecutionController`. If amount/currency/policy-backed cost is unknown under `stop_on_unknown_cost`, stop before any child dispatch/lease/provider/source call, report `COST_UNKNOWN`, and retain a partial Learning Memory event.
- **FR-012:** Reconcile actual monetary use without turning UNKNOWN into zero or discarding a known lower bound. No cross-currency summation. A subsequent unit may run only after the same controller authorizes its reservation.
- **FR-013:** Preserve Observation/Learning Memory provenance, reuse rights, state fingerprints, replay IDs, execution attempts, failure/stop causes and no-change outcomes. Shared public observation reuse is deduplicated; private first-party inputs stay tenant-private.
- **FR-014:** Continuity stores/retrieves only authorized private context and real checkpoints. Missing origin stays UNKNOWN; model-generated text cannot choose scope or create retrospective provenance.
- **FR-015:** Deterministic Python composition and answerability gates run before structured evaluation. The approved provider-neutral `ModelRouter` adapter may be configured only with an exact registered provider and explicit version; provider output remains non-authoritative. Key presence never configures or authorizes a call, and missing evaluator capability remains unavailable/UNKNOWN.
- **FR-016:** Human wording uses canonical public vocabulary (â€œOrganizationâ€, â€œObservation Focusâ€, â€œSignalsâ€, â€œevidenceâ€), leads with meaning, and preserves direct evidence access and uncertainty. It makes no claim of validated cognitive benefit without representative user research.
- **FR-017:** Produce a real runtime proof for 1, 2 and 100 subscriber Organization contexts with context isolation; these are subscriber scale cases, not Customer Zero onboarding. Customer Zero remains an internal AXIGNAL test context.

## Explicit non-goals

- SEO/GEO execution, marketing or communication campaigns, reputation repair, social/review management, CRM, lead pipeline, customer relationship conclusions or sponsored ranking.
- Any new Organization/profile truth, tenant-owned canonical graph, role/invite model, or user-controlled truth editing.
- Global search/index/score from a single public website; universal digital score; claim of â€œpoor SEOâ€ from missing observations.
- Authenticated scraping, cookie/session use, anti-bot bypass, CAPTCHA, or unauthorized retention/republication.
- Provider-specific SDK integration, automatic key-based provider selection, general agent framework, crawler, vector/graph database, queue, scheduler or store.
- New parallel Memory, MarketMap, Prime, budget or subscriber-projection authority.
- Production deployment. Production requires separately authorized integration/browser E2E and external verification.

## Dependencies and known gaps

- **Identity/context:** reuse ADR-0018/0021 `AuthorizedXeed` / `AuthorizedXeedOrganization` and TASK-049 `OrganizationResolutionPort`. Production identity and durable persistence are not implied. If identity is pending, only private attention/pending-resource observation is allowed; Organization-level output waits for independent canonical resolution and server-side ID revalidation.
- **Canonical Organization intake:** current `ExactNameResolver` resolves among existing governed canonical candidates, not new entity creation; identity binding and EvidenceAdmission remain separate. A pending URL/name may direct public acquisition only under source policy and remains unassociated with an Organization until independently resolved. No URL+label shortcut.
- **EB-04:** reuses `run_first_economic_vertical_e2e` and output contracts. Its current source plan is explicit and reference-shaped; generic discovery for every registered Organization is not proven by this contract.
- **EB-06/07:** reuse temporal Observation Memory, ResearchValue, Prime, shared observation work and lease/fencing. A subscriber-facing read binding to durable economic outputs is not established by their unit contracts.
- **Market posture:** type and planner exist; a production reader/materialization source for evidence-backed temporal maps remains unverified. Until supplied, output is UNKNOWN and no posture-derived fan-out occurs.
- **DRI:** MASTER Â§54 establishes semantics and current authorization boundaries but not a complete measurement-instrument/source runtime. This feature proposes only the minimal public, condition-bound contract described here; architecture review must confirm it remains within public-source rights and deterministic contracts.
- **Cost preflight:** `GovernedExecutionController` supports pre-dispatch reservations and `COST_UNKNOWN`; acquisition/evaluator pricing estimates/upper-bound guarantees and complete fan-out reservation semantics must be proved by tests. Current unknown-price handling must fail closed before any child work.
- **Continuity:** ADR-0017 target persistence/broker remains unimplemented; this feature may compose existing authorized checkpoint/read paths only. It cannot claim durable continuity absent a real store.
- **User surface:** current fixture-only product proof does not demonstrate a live subscriber product integration. Exact web/backend integration owner and Browser E2E remain required before production.

## Success criteria

- **SC-001:** A live deterministic runtime invocation, with a supplied authorized context and real admitted/declared evidence, returns a subscriber projection whose meaning, basis, temporal state, uncertainty and evidence references are traceable to the same EB-04/06/07 output.
- **SC-002:** Missing or cross-context authorization, unresolved canonical identity, mismatch, stale/withdrawn evidence or source-rights failure never produces a positive unsupported conclusion or leaks private state.
- **SC-003:** DRI test cases prove the difference among NOT_MEASURED, inaccessible/insufficient sample, observed presence and measured absence within a frozen eligible sample; a website read never claims search/generative/global absence.
- **SC-004:** Market posture test cases prove B2B/B2C/B2G materially alter selected target kinds/questions and preserve OBSERVED/POTENTIAL/UNKNOWN.
- **SC-005:** Under stop-on-unknown monetary policy, an unknown cost anywhere in the planned fan-out yields zero child dispatches, zero leases and a replayable partial stop event. Known aggregate reservations are checked before any child starts.
- **SC-006:** Temporal tests prove same inputs reproduce the same projection; source/instrument changes preserve history and cause scoped reevaluation/staleness.
- **SC-007:** Private continuity and 1/2/100 Organization tests prove separation across subscriber contexts; Customer Zero is a separate internal fixture/context.
- **SC-008:** Meaningful focused tests plus applicable repository deterministic gates, architecture guard, governance, frontend type/build/browser proof and exact-candidate end-to-end integration pass before any integration/deploy proposal.
- **SC-009:** An unresolved locator cannot produce Organization-level output or create an Observation Focus. Any pending resource observation is explicitly unresolved and revalidated after independent identity resolution.
