# 063 — First Subscriber Observation Loop and Runtime Economics

- **Status:** Draft for CTO review
- **Date:** 2026-10-08
- **Base:** `origin/main` `19018f2` (PR #171 merged)
- **Authority:** MASTER §7 (Focus), §8 (demand-materialized graph, reuse, flywheel), §9
  (FIRST_MAP_WOW, construcción visible), §15.3 (source hierarchy per predicate), §15.4
  (UNKNOWN ≠ FALSE), §31.3 (200-subscription attack), §42 (COST_PER_FIRST_MAP,
  CROSS_XEED_REUSE), §53 (no universal score); Constitution I, III, V, VI, VIII–X, XI,
  XVI, XVII, XIX–XXII; ADR-0087, ADR-0088, ADR-0089, ADR-0090; specs 052, 054, 058, 059, 062.
- **Decision record:** ADR-0091.

## 1. Problem (verified in code at `19018f2`)

"Observe empresa.com" never reaches a useful result for an ordinary subscriber:

| # | Root cause | Evidence |
|---|---|---|
| R1 | Identity is the only gate to work. GLEIF answers only a bare LEI; a URL or a name is `IDENTITY_SOURCE_UNAVAILABLE`, and ADR-0087 §7 forbids any observation while pending. | `pipeline/entity_resolution/gleif_registry.py:231-237`; `application/subscriber_portfolio/service.py` `add()` |
| R2 | Nothing acquires the first public website observation. The T12 website entry point needs `attention.website`, which is read from an existing CURRENT website seed: a bootstrap deadlock. `run_once` does not even compose `PublicWebsiteAcquirer`. | `application/observation_runtime/tick.py:191`; `tools/runtime/observation_daily.py:attention_for`, `run_once` |
| R3 | The website acquirer stores observations under the Focus id (`subject_id=lead.xeed_id`), while every reader selects by Organization id: the observation is invisible and is repeated per Focus. | `application/observation_runtime/acquirers.py:110-118`; `subscriber_runtime._authorized_public_history` |
| R4 | Markets come only from an operator JSON (`AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE`, absent in production) or from schema.org `Service.areaServed` with NUTS identifiers (spec 058), which ordinary websites do not publish. | `tools/runtime/subscriber_observation.py`; `application/observation_runtime/materialization.py:explicit_public_scopes` |
| R5 | Capability discovery is a five-entry lexicon; any other business yields `[]` and no plan. | `application/observation_intelligence/catalog.py:CAPABILITY_LEXICON` |
| R6 | Observation runs synchronously inside the HTTP add/reobserve request. | `tools/runtime/subscriber_composition.py:_ObservationTrigger.trigger` |
| R7 | An empty result is indistinguishable from failure: the subscriber sees "identity unresolved" or `NOT_READY`, never why. | `apps/web/experience/components/subscriber-portfolio.tsx` |
| R8 | Public-world work is not shared: per-Focus website fetches (R3), per-Focus TED queries for identical capability × market questions. | as above; `pipeline/observation_intelligence/ted.py` |

Production (read-only check, 2026-10-08): `AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER=gleif`,
`AXIGNAL_OBSERVATION_RUNTIME_ENABLED=false`, `AXIGNAL_SEMANTIC_LAYER_ENABLED=false`, no
`AXIGNAL_SUBSCRIBER_OBSERVATION_PLAN_FILE`.

## 2. Outcome

```
subscriber adds locator
  → cheap synchronous validation (parse, entitlement, canonical index, registry port)
  → accepted attention target (Focus, or private pending attention)
  → durable First Observation job (bounded, idempotent, leased, resumable, budgeted)
  → First Proof: evidence-backed discoveries or grounded UNKNOWNs, with cost and value
  → reobservation through the existing T12 runtime (Focus) or due re-checks (pending)
```

Identity, observation and truth stay separate: attention starts observation; only a
registry admits identity (ADR-0087 unchanged); nothing in this spec writes FAXT.

## 3. Concepts

- **Attention target.** The private thing a subscriber pointed at: a Focus (canonical
  Organization resolved) or a pending attention entry. It carries the locator signals
  (website domain, name, LEI) and an `identityLink`: `REGISTRY_VERIFIED` when the canonical
  Organization's registry record attests that website, `SUBSCRIBER_DIRECTED` otherwise.
  It is never an Organization and never canonical.
- **Site reading (world level).** The deterministic reading of one public website origin:
  robots decision, fetched pages with fingerprints, title, description, languages,
  JSON-LD types, declared addresses, service areas, services, identifiers, ranked links.
  Keyed by origin, shared by every tenant (public world, provenance once, reuse many).
- **First Observation job.** Durable work item per (target, website fingerprint). States:
  `QUEUED → RUNNING → DONE | FAILED`; lease + attempt bound; replay of the same key is a no-op.
- **First Proof.** The first evidence-backed useful observation for a target (§7).

## 4. Cheapest-first cascade (implemented order)

| Level | Work | Spends | Runs when |
|---|---|---|---|
| L0 Memory | world site reading CURRENT; semantic judgment memory; world query cache (same source query, same UTC day) | nothing | always first |
| L1 Deterministic | locator normalization, robots.txt (cached per origin), HTML/JSON-LD parse, lexicon, schema.org types, addresses, languages, identifiers | 1 request per origin per robots TTL | no CURRENT reading |
| L2 Cheap public fetch | homepage; then at most 2 high-information pages (about / services / contact / locations) | ≤ 3 page requests | homepage always; extra pages only while activity or location is UNKNOWN |
| L3 Jev | one batch, one state, the routing-relevant questions only | System One tokens | semantic layer enabled and deterministic activity insufficient |
| L4 Demand research | existing strategy + routing + garden pruning → adopted sources | source requests (bounded 4) | capability codes × market have a routable adopted source |
| L5 Luna | none in First Observation (escalation budget 0 for its questions) | — | never here; AXENT keeps its own budget |
| L6 AXENT deep research | user-directed only (existing) | — | unchanged |

The **value policy** (`first-observation-value-policy.v1`, deterministic, versioned,
operational — not a score, not canonical) decides each optional step from the open
unknowns it can reduce (identity, activity, location, demand), its reuse level (world vs
tenant) and its marginal cost; every decision is recorded with a reason
(`FETCHED:ACTIVITY_UNKNOWN`, `SKIPPED:ACTIVITY_EVIDENCED`, `SKIPPED:NO_ROUTABLE_SOURCE`…).

## 5. Open capability discovery

Python reads; Jev classifies; Python validates and governs.

1. Lexicon (existing, codes attached) — DECLARED excerpt basis.
2. schema.org types the site declares about itself (e.g. `Electrician`, `School`) mapped to
   ISIC Rev.4 sections — governed vocabulary table, declared basis.
3. Semantic layer (when enabled): one `SemanticBatch` over the bounded public reading,
   questions selected by need: ISIC section (always), CPV division (only when an EU scope
   exists), NAICS sector (only when a US scope exists), customer type, delivery mode,
   operating-business check. Answers below the cascade policy stay UNKNOWN.

Every hypothesis is `POTENTIAL`, carries an exact page excerpt basis, its method
(`LEXICON | SCHEMA_ORG_TYPE | SEMANTIC_JUDGMENT`) and, for judgments, model and confidence.
Classification codes are routing indexes, never the organization's economic reality.

## 6. Market discovery

Three sets, never mixed:

- **Declared operating reach** — what the organization's own site states: postal
  addresses (`PREMISES`), `areaServed` (`STATED_SERVICE_AREA`). Epistemic state DECLARED
  (MASTER §15.4); not admitted reach.
- **Potential attention** — where AXIGNAL looks first, derived deterministically from the
  declared set: premises jurisdiction and declared service areas, coded into the existing
  jurisdiction tree (`EU/<NUTS CC>`, `US/US-<ST>`, `<ISO CC>`). POTENTIAL, attention only.
  Remote/digital delivery without a declared area stays UNKNOWN, never "global".
- **User-directed attention** — reserved (the subscriber may widen where to look later;
  never declares where the organization operates).

Spec 058's rule "no HQ/address inference" is refined, not dropped: an address never
becomes reach; it may only direct attention, and the spec 059 gate keeps unresolved reach
`UNRESOLVED_REACH`.

## 7. First Proof and subscriber states

Discovery kinds: `PUBLIC_PRESENCE`, `ACTIVITY`, `DECLARED_LOCATION`,
`DECLARED_SERVICE_AREA`, `LANGUAGES`, `IDENTITY_HINT` (identifier or legal name declared
by the site: never admitted), `DEMAND` (POTENTIAL opportunities), `SIGNIFICANT_UNKNOWN`.

First Proof is `READY` when at least one evidence-backed discovery exists. A grounded
unknown (site unreachable, robots disallow, no governed demand source) is shown as such.

Subscriber states (derived, never invented): `QUEUED`, `OBSERVING_PUBLIC_PRESENCE`,
`FIRST_PROOF_READY`, `NOT_ENOUGH_CAPABILITY_EVIDENCE`, `NO_PUBLIC_WEBSITE`,
`SOURCE_UNAVAILABLE`, `BUDGET_EXHAUSTED`, `OBSERVATION_DISABLED`; demand-level notes
`NO_GOVERNED_DEMAND_SOURCE:<jurisdiction>`, `NO_RELEVANT_DEMAND_FOUND`.
UNKNOWN ≠ failure; no result ≠ no opportunity; no source ≠ no market.

## 8. Reuse

| Work | Level | Mechanism |
|---|---|---|
| robots decision, page fetch, site reading | world (origin) | site reading store, TTL from the temporal policy |
| semantic judgment over public reading | world (state fingerprint) | existing judgment memory (spec 062) |
| identical source query on the same UTC day | world (source, query key, day) | world query cache |
| Focus seed observation | Organization subject | appended once per reading fingerprint; Focus readers unchanged |
| First Proof, ranking, demand fit | tenant | private result store |

## 9. Reobservation

Focus targets hand over to T12 (spec 058 materialization now accepts First Observation
scopes; the plan reader falls back to them when no operator file entry exists). Pending
targets get a due date: unchanged site → backoff ×2 (7 → 14 → 30 days), activity unknown →
7 days, changed → normal. `TemporalCurrentnessPolicy` decides currentness; no change is
invented when nothing was observed.

## 10. Cost accounting

Per job: HTTP requests and bytes (MEASURED), cache/memory hits and requests avoided
(MEASURED), Jev tokens (as reported by the provider, else ESTIMATED), Jev USD
(VENDOR_PUBLISHED price × tokens), Luna calls/USD (OPERATOR_CONFIGURED), source requests
(MEASURED) with paid amount from the source catalog (TED: 0, openly accessible per its
docs). Aggregates: `COST_PER_FIRST_PROOF`, `HTTP_REQUESTS_PER_USEFUL_RESULT`,
`COST_AVOIDED_BY_REUSE`, `JEV_ESCALATION_RATE`, `LUNA_ESCALATION_RATE`,
`COST_PER_USEFUL_OPPORTUNITY` (`tools/runtime/first_observation.py metrics`).
Estimated is never reported as measured.

## 11. Abuse and bounds

Pending targets consume observation only inside the tenant's current paid/pilot capacity
(active + paused Foci + observed pending targets ≤ capacity). Per-job and per-day request
budgets; robots honoured; no authenticated scraping; no anti-bot bypass.

## 12. Off by default

`AXIGNAL_FIRST_OBSERVATION_ENABLED=false` keeps today's behaviour exactly. Enabling it,
the semantic layer, or the T12 timer in production is a separate CTO step.

## 13. Out of scope (next tasks, defined in validation.md)

World-source TED ingestion (one feed, many Foci), USAspending/SAM.gov adapters, HTTP
conditional requests (ETag/Last-Modified) in the governed transport, persisted
operational learning across runs, user-directed market widening, Luna synthesis of the
First Proof narrative.
