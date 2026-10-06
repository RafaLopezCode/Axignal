# Architecture Review â€” TASK-050 Subscriber Brain Output E2E

**Review status:** pending root approval; no implementation authorization yet.
**Reviewed in read-only mode:** source and contracts at repository HEAD `016235736db002038f8063f3abd311ba5dca110c`; shared worktree has concurrent TASK-046/047/048/049 changes outside this feature.
**Scope reviewed:** subscriber projection, EB-04/06/07 composition, market posture, DRI measurement boundary, identity-pending intake, continuity and cost preflight.

## Proposed decision

Approve TASK-050 as a bounded application composition/read-model feature using current AXIGNAL authorities. It introduces no second truth, memory, market map, budget, scheduler, tenant, Organization or provider authority. Runtime source data is passed from existing governed ports and must be independently verified. The proposed subscriber runtime projects real EB-04/06/07 outputs or returns explicit partial/UNKNOWN. Public DRI is a distinct condition-bound observation and must not be synthesized from registration, a lone URL locator or missing acquisition.

Do not begin implementation until root reviews the exact ports and approves the task boundary. The root-owned TASK-049 organization resolver/portfolio bridge is a prerequisite. No change to MASTER is proposed: the feature implements the observation semantics in MASTER Â§54 and does not promote DRI into SEO/GEO execution or an authoritative score.

## Authority and product-semantics check

- **MASTER Â§Â§5â€“7, 53:** user input directs attention; canonical Organization/evidence authority remains independent; derived opportunity defaults POTENTIAL; temporal knowledge is reused only with provenance/currentness; evaluator output is replaceable/non-authoritative.
- **MASTER Â§54 and ADR-0014/0015:** DRI is one Brain observation capability, not a marketing suite. Every digital measurement binds instrument/version, surface, conditions, sample, time, uncertainty, rights and lineage. Public surface output is not business truth. A gap is derived; it cannot assert poor SEO/GEO cause. Public visibility alone grants no acquisition rights.
- **MASTER Â§55 and ADR-0016/0017:** meaning precedes metrics; epistemic/temporal/context scope and proof remain visible. Continuity must preserve recorded origin and then-state; unknown origin stays unknown. Private context is resolved/authorized before retrieval; no model selects scope.
- **MASTER Â§56.22:** temporal market posture materially selects sensors, vocabulary, candidate types and questions. OBSERVED confirmation differs from POTENTIAL investigation; UNKNOWN remains explicit. B2C observes aggregate Demand Archetypes, never individual consumers.
- **ADR-0021:** only an `AuthorizedXeed` can resolve its global Organization. A subscriber locator, raw Focus ID or Organization ID does not grant read authority.
- **ADR-0024â€“0030:** deterministic control plane, Prime/ResearchValue, learning and execution budgets are reused. Every external unit of work needs pre-dispatch authorization. Unknown cost is not zero; stop-on-unknown produces a replayable partial stop.
- **No C0 substitution:** TASK-049's subscriber journey is 1/2/100 Organization contexts. Customer Zero is AXIGNAL internal self-use, in a separate authority plane.

## Identity resolution seam

The source review did not find an authorized â€œsubscriber URL + display name â†’ new canonical Organizationâ€ path. It found:

- `pipeline/entity_resolution/resolver.py` `ExactNameResolver.resolve_identity`: exact unique canonical/alias resolution among existing governed candidates; verified external identifiers take precedence; ambiguity/unresolved are explicit.
- `ExactNameResolver.bind_mention`: produces an exact-span governed identity binding only when an existing canonical identity is RESOLVED. A binding is not itself canonical truth.
- `application/identity_resolution/governance.py`: append-only merge/split/reversal across Organization IDs, not arbitrary entity creation.
- `domain/evidence/admission.py`: canonical identity/legal-identity/registration propositions require Registry authority; subscriber signal is attention-only.
- TASK-049 draft: `OrganizationResolutionPort.resolve(OrganizationLocator) -> ResolvedCanonicalOrganization | IdentityPending` is the intended intake seam.

**Required integration behavior:**

1. Authenticate and authorize subscriber context first; resolve the locator through TASK-049.
2. For `IdentityPending`, retain a private pending request only. If an allowed public source is independently acquired under the existing registry/policy, store the result as resource-level observation linked to the pending request, with subject resolution UNKNOWN/UNRESOLVED. It may report â€œthis resource was observed; Organization identity is unresolved.â€ No Organization-level Signal, Focus, capability, market posture, RepresentationGap or Brain result may be emitted.
3. Once a separate identity authority returns a canonical Organization, the server rechecks that ID against the resolved canonical Organization reader and binds exact source mentions/representations. EvidenceAdmission independently decides if any proposition enters AXIGLAND.
4. Any identity mismatch, ambiguity, change/merge redirect or stale decision stops projection and requires re-resolution. Never retrofit pending resource data to a canonical Organization solely from the original URL/name.

This keeps subscriber experience useful while a target is pending: the UI may show resolution status and permitted resource observation metadata, but it cannot phrase those as an Organization fact. Creation of a durable `IdentityPending` request/store is owned by TASK-049; TASK-050 consumes the result and does not implement another identity or portfolio store.

## DRI and Human Output boundary

Existing `EconomicHumanOutput` compiles EB-04 result dimensions, exact evidence/source/span refs, state fingerprint, currentness and uncertainty. Existing `economic_runtime.py` maps it to `RuntimeSignal` and attaches it only when the subject matches the projection Organization. This is a good adapter seam; it is currently a pure mapping/composition boundary and tests do not establish durable live subscriber Brain inputs.

The minimum DRI addition is a typed, versioned measurement record through the existing public source policy/representation adapter:

```text
instrument_id + instrument_version
measured_family/surface + exact resource/query/prompt set
canonical_subject_ref OR unresolved_pending_ref (mutually exclusive authority)
conditions + geography/language/device where measured (otherwise UNKNOWN/NOT_APPLICABLE)
observed_at + source/policy/provenance/rights/reuse/currentness
sample_count + informative_denominator + coverage + uncertainty
result = PRESENT | MEASURED_ABSENCE_IN_SCOPE | NOT_MEASURED |
         NON_INFORMATIVE | INACCESSIBLE | INSUFFICIENT_SAMPLE | UNKNOWN
```

With the source acquisition currently known, a plain public HTTP page only supports a page/resource-level observation. It has no frozen external search result set, generative product/API instrument, social conversation sample or public-reputation sample. Therefore it cannot say that an Organization has or lacks those representations. It also cannot establish that the Organization has â€œalmost no presenceâ€ across the web. `NOT_MEASURED` is not `MEASURED_ABSENCE_IN_SCOPE`. An absence is eligible only within a previously specified eligible sample and informative denominator and requires the instrument to show that the sample itself ran. Incompatible versions/conditions create separate series unless a validated bridge exists.

Deterministic wording may state the exact measured scope and a bounded next investigation (e.g. inspect whether the observed page explains the independently evidenced capability). It cannot attribute cause, promise growth, execute recommendations, generate an ungrounded capability/market, or invent a causal narrative. No score is authorized.

## Cost-before-fan-out protocol

`GovernedExecutionController` supports pre-dispatch reservations, aggregate projection across active reservations, explicit currency, `COST_UNKNOWN`, and reconciliation where known amount can coexist with incomplete cost. `ExecutionBudgetPolicy` supports `stop_on_unknown_cost`; individual `execute_prime_source_slice` source work is reserved before acquisition. These are useful foundations but do not yet prove atomic preflight of every child in a new bounded subscriber fan-out.

Required application protocol:

1. Resolve authorization, canonical Organization, current state and posture without external dispatch.
2. Compute a bounded child plan from existing MarketMap/Prime/ResearchValue; rights-blocked and UNKNOWN items remain non-executable.
3. Pre-reserve all child source/research work against one existing `GovernedExecutionController`. The bundle must be bound to execution, policy/code version, canonical subject, state fingerprint, exact child IDs, currency, amount basis, request/source counts and deadline.
4. If any child price is unknown under stop-on-unknown, any reservation fails, or aggregate limits exceed policy, release every successful reservation, persist one replayable PARTIAL stop, and perform **zero** child source fetches/provider calls/durable lease claims. There must be no background fan-out before this step.
5. Only then may already-authorized ports run; each dispatch is still tied to its reservation and reconciles measured usage. If actual cost becomes unknown, preserve its known lower bound/incomplete state and stop subsequent units.

If the existing controller cannot release/claim the reservation bundle with the required all-or-nothing pre-dispatch guarantee, root should approve a minimal orchestration wrapper around that controller, not a competing budget implementation. A missing price/cap is UNKNOWN. `0` requires an explicit, versioned contractual price rule; free-to-use public access does not prove AXIGNAL acquisition cost is zero.

## Files and ownership

Current TASK-050 draft may modify only these feature docs before review:

- `specs/050-subscriber-brain-output/spec.md`
- `specs/050-subscriber-brain-output/clarify.md`
- `specs/050-subscriber-brain-output/plan.md`
- `specs/050-subscriber-brain-output/tasks.md`
- `specs/050-subscriber-brain-output/checklists/requirements.md`
- this `architecture-review.md`

After approval, proposed implementation paths are:

- `application/subscriber_projection/economic_runtime.py` (extend only if existing adapter is insufficient; no editing root-owned bridge);
- new narrowly named `application/economic_discovery/` measurement/preflight composition module(s), without touching spec-046-owned `first_vertical_e2e.py` and without duplicating `market_entry.py`, `market_planning.py`, `execution_budget.py`, `prime_execution.py`, memory or source registry;
- `tools/runtime/subscriber_economic.py` as thin injection/composition entrypoint, only if an existing runtime cannot wire it;
- new tests under `tests/subscriber_projection/` and `tests/economic_discovery/`, avoiding existing/concurrent TASK-046, 047 and 048 paths;
- TASK-050 Spec Kit docs only.

TASK-049 owns subscriber identity/portfolio/pending locator and canonical Organization resolution. Root owns existing canonical resolver bridge. No `.specify/feature.json`, database choice, schema migration, frontend path, provider or deployment is included in this authorization request.

## Graphify and evidence used

Graphify first yielded the relevant subgraph, then targeted `explain`/`affected` confirmed references. Source was cross-checked in the listed files.

- `graphify query "How does EB-04 economic discovery connect evidence admission, subscriber projections, DRI, MarketMap and human-first output?"` â€” surfaced `EconomicHumanOutput`, EB-04, existing `economic_runtime.py`, `XeedMarketMap`, `GovernedExecutionController`, currentness, Observation/Learning Memory and AuthorizedXeed.
- `graphify explain EconomicHumanOutput` â€” confirmed current runtime adapter attachment, subject result, existing `test_economic_runtime.py`, and EB-04 producer imports.
- `graphify affected application/subscriber_projection/economic_output.py` â€” confirmed integration fan-in: EB-04 producer, subscriber runtime, existing runtime tests and EB-08 QA harness; verified that editing the output contract may affect these exact boundaries.
- `graphify query "What existing contracts implement budgeted source fan-out and unknown-cost fail-closed behavior?"` and `graphify explain GovernedExecutionController` â€” confirmed reservation/attempt/Prime/testing dependents; source code reviewed for whole-fan-out atomicity gap.
- `graphify explain XeedMarketMap` â€” confirmed one existing map/planner and market-entry tests; no duplicate map proposed.
- Direct source review: `pipeline/entity_resolution/resolver.py`, `application/identity_resolution/governance.py`, `domain/identity_binding.py`, `domain/evidence/admission.py`, TASK-049 draft and ADR-0018/0021.

Graph evidence is navigational, not authority. Direct source and tests govern this proposal.

## Test and implementation status

- Current repository baseline: root reports 1,404 deterministic tests passing before this slice; this agent did not rerun or claim that result.
- Existing test contracts to preserve: `tests/subscriber_projection/test_economic_runtime.py` (attachment, UNKNOWN, Organization mismatch); `tests/economic_discovery/test_market_entry_demand.py` and `test_market_planning.py`; `test_execution_budget.py`, `test_prime_execution.py`, `test_first_vertical_e2e_adversarial.py`, `test_observation_reuse.py`, and `test_continuous_observation.py`.
- The available EB-08 load/backup proof uses synthetic economics; it is not this task's real subscriber Brain proof.
- No TASK-050 code or tests have been implemented/run. All acceptance and adversarial cases in `tasks.md` remain pending.

## Review decision requested from root

1. Approve/adjust the pending-identity rule: resource-level public observations can be shown only against `IdentityPending`; they are not Organization-level output until independent resolution.
2. Approve the DRI first-slice measurement family and the strict one-page scope; no Search/Generative/Social result is claimed without its own instrument.
3. Approve all-or-nothing reservation bundle requirement and confirm the existing controller can support it without a second budget authority.
4. Approve implementation ownership/path split, including whether runtime is new file or an extension of `economic_runtime.py`.
5. Confirm TASK-049 and backend/app identity wiring prerequisite; exact product/browser E2E remains downstream and deployment remains out of scope.
