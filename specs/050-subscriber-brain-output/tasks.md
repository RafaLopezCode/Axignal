# Tasks â€” TASK-050 Subscriber Brain Output E2E

**State:** bounded architecture slice approved by root; execution/read-model work implemented in part; remaining dependencies below stay open.

## Phase 0 â€” Architecture review (blocking)

- [x] T000 Root approved the bounded subscriber runtime, output snapshot, all-or-nothing EB-04 budget preflight, MarketMap routing, provider-neutral evaluator adapter, and one-page DRI contract.
- [x] T001 No MASTER doctrine change was required; TASK-050 preserves Â§54 measurement limits, non-authoritative evaluation, canonical Organization and UNKNOWN rules.
- [x] T002 File ownership was coordinated. Root explicitly assigned `application/economic_discovery/first_vertical_e2e.py` exclusively for the cost preflight extension.

## Phase 1 â€” Subscriber output composition

- [x] T010 [P1] Define typed execution/read protocols in `application/subscriber_projection/subscriber_runtime.py`, accept authorized context and real EB-04 output, and return the existing subscriber read-model shape. Focused tests: `tests/subscriber_projection/test_subscriber_runtime.py`, `test_subscriber_execution.py`.
- [x] T011 [P1] Reauthorize membership/Xeed and canonical Organization on read and publication; reject subject mismatch and propagate access failures.
- [ ] T014 [P1] Integrate only with TASK-049's `OrganizationResolutionPort`; test `IdentityPending` keeps the locator/resource observation private and unresolved, with no Focus/Organization output/MarketMap, and test resolved canonical ID is revalidated before read/projection.
- [x] T012 [P1] Compile and persist exact `EconomicHumanOutput` into RuntimeSignal/Today with evidence refs, scope, currentness, uncertainty and versioned execution trace; evidence freshness is revalidated at read.
- [x] T013 [P1] Tests exercise constructed EB-04 result, store idempotency, membership, subject binding, stale evidence, and controlled end-to-end run. The execution tests reuse synthetic fixtures only inside test scope.

## Phase 2 â€” MarketMap, continuity and temporal reuse

- [x] T020 [P1] Route the supplied evidence-backed `XeedMarketMap` through existing `plan_market_observation`; require exactly one selected matching server-owned descriptor.
- [ ] T021 [P1] Controlled routes cover B2B POTENTIAL/OBSERVED, B2C POTENTIAL, B2G POTENTIAL and UNKNOWN abstention; B2C is restricted to aggregate `DEMAND_ARCHETYPE`. B2C/B2G OBSERVED cases remain open.
- [ ] T022 [P1] Snapshot trace binds MarketMap fingerprint and EB-04 replay refs; read-time evidence currentness is reevaluated. EB-06 declared dependency invalidation and EB-07 shared-work/lease/fencing remain unconnected.
- [ ] T023 [P1] Immutable output snapshots persist in SQLite; actual private continuity origin, open-question checkpoint and delta reader remain unimplemented.
- [ ] T024 [P1] Membership recheck is tested; 1/2/100 context matrix, cross-context private isolation and Customer Zero separation still need integration E2E.

## Phase 3 â€” Condition-bound public DRI measurement

- [x] T030 [P1] Use the existing public source registry, HTTP policy and representation adapter for one authorized public page; no new source client/crawler/authentication.
- [x] T031 [P1] Define the immutable versioned page instrument record with exact resource, surface, sample, conditions, time, representation extractor versions, rights/access/reuse basis, currentness and uncertainty; no search/generative/social mapping.
- [x] T032 [P1] Derive a single-field RepresentationGap only for measured absence of the canonical Organization name in the exact captured page title; otherwise preserve the measured title state and exact scope.
- [x] T033 [P1] Emit descriptive page-level meaning; any context-required human guidance is limited to T035. Cause remains UNKNOWN and the output explicitly disclaims SEO/GEO quality, search/generative/social visibility and whole-Organization representation.
- [x] T034 [P1] Tests distinguish no plan, cost-blocked, inaccessible page and non-informative representation as structured NOT_MEASURED attempts with no gap; verify one-page title presence/absence, scope/rights/currentness and instrument-version mismatch retention/fail-closed projection.
- [x] T035 [P1] For an exact-page title gap only, include a typed `CONTEXT_REQUIRED` recommendation record. Keep page purpose and expected public brand unknown until confirmed; condition any title review on both, with human review only, no automatic SEO/GEO execution, and no performance claim. Preserve `cause=UNKNOWN` and the exact-page INXIGHT gap.

## Phase 4 â€” Cost preflight and stop-before-fan-out

- [x] T040 [P0] For this bounded EB-04 slice, compose a server-owned activity-plan route from an authorized selected MarketMap directive before dispatch; UNKNOWN/rights-blocked/unconfigured routes abstain. Prime/ResearchValue planning remains separate.
- [x] T041 [P0] Preflight the complete bounded EB-04 maximum (2 public sources + 2 extraction calls + up to 3 judgments) with existing `GovernedExecutionController`; the dispatch recorder consumes held reservations and does not reserve again.
- [x] T042 [P0] Unknown or unversioned per-dispatch cost and aggregate budget failure release held reservations, append a PARTIAL Learning Memory stop with exact reason, and produce zero dispatches. The existing `execution_stop_learning_event` marks stops non-replayable until its declared state payload retention gap is addressed.
- [ ] T043 [P0] The controller reconciles configured per-attempt amounts and completeness. Live metered/variable actual-cost reporting and retaining completed children after a later unknown actual cost are not implemented.
- [ ] T044 [P0] Focused counters prove unknown cost and known aggregate over-limit dispatch nothing and release capacity. Concurrent bundle races, lease counters and actual post-dispatch variable cost remain unverified.

## Phase 5 â€” Runtime integration and convergence

- [x] T050 [P1] Add the runtime factory using TASK-049 identity store (Principal+Membership), portfolio `XeedReader`, and separate canonical Organization reader. The execute call requires a server-owned plan; no fixtures are loaded in runtime.
- [ ] T051 [P1] Runtime emits the current backend projection shape. Root web route and frontend parser/browser wiring remain a separate integration.
- [ ] T052 [P1] Focused suites passed; root still owns adversarial cross-task review and full deterministic repository gates.
- [ ] T053 [P1] Graphify AST update/queries and root governance/architecture guard/diff check remain pending after code freeze.
- [ ] T054 [P1] Controlled one-Organization fixture E2E passed. Real candidate and 1/2/100 product/browser E2E and persistence/provider limits review remain; no deployment.

## Dependency map

- T010â€“014 depend on T000â€“002 and root's authorized identity/portfolio â†’ `OrganizationResolutionPort` bridge. Resolved identity is mandatory for Organization output; pending identity permits only private unresolved request/resource observation.
- T020â€“024 consume an injected evidence-backed temporal MarketMap; its live read source, full routing coverage and broader EB-06/07 integration remain dependencies.
- T030â€“035 use the existing authorized page acquisition and representation path; only the one-page condition-bound instrument and context-required human-review prompt are implemented. Recommendation context is not inferred or defaulted. Unavailable/non-informative attempts are structured, and a version mismatch hides the old derived gap from the current projection while retaining the immutable recorded measurement. No cross-version comparison bridge exists.
- T040â€“044 use the existing `GovernedExecutionController` for one bounded EB-04 max-seven set. Cost basis is required/versioned before dispatch; broader fan-out, concurrency and live variable-cost reconciliation remain open.
- T050â€“054 depend on all core phases plus current projection ownership and browser harness availability. Production remains excluded.
