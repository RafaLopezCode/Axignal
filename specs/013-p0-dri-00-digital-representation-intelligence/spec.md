# Feature Specification: P0-DRI-00 Digital Representation Intelligence

**Status:** Converged product doctrine; documentation-only, pre-implementation.\
**Authority:** MASTER §§22, 46 and 54; ADR-0014 and ADR-0015.\
**Objective:** Canonize four condition-bound digital representation observation
families and their relationship to the governed economic world, including
public experience, without creating runtime or source acquisition.

## User scenarios and acceptance

### Story 1 — Understand digital representation

As a subscriber, I need AXIGNAL to distinguish how search, generative and
public-conversation surfaces represent an organization from what AXIGNAL
independently observes about its capabilities, markets and demand.

1. Search results retain query, language, geography, surface, time, instrument
   version and informative sample; no global context-free rank is claimed.
2. A product UI and a model API are different generative instruments. Their
   outputs are observations of a surface, not business facts.
3. Mention, citation and endorsement remain distinct. Social volume is not
   demand. RepresentationGap is a derived INXIGHT, not FAXT.
4. Before/after claims require comparable instruments, conditions, period,
   subject and coverage; material drift is not company change.

### Story 2 — Understand public experience without overstating it

As a subscriber, I need recurring praise, complaints, themes, responses and
changes to remain traceable to public observations so that a review sample is
not presented as the experience of all customers or as canonical truth.

1. A ReviewObservation preserves source-native content/metadata or a permitted
   reference and distinguishes review, subject, dates, response, verification,
   currentness and lineage.
2. REVIEW != BUSINESS_TRUTH; reviewer claims do not become FAXT. Platform
   ratings and verification remain source-reported; sentiment is derived.
3. ExperienceSignal requires repeated, scoped, time-bounded observations.
   Organization, product and location reputations do not collapse.
4. Anomaly does not prove fraud or review bombing; removed does not mean false.
5. Duplicate, syndicated and cross-posted observations do not become multiple
   independent evidence items.

### Story 3 — Inspect a future metric

As a subscriber, I need any future reputation metric to show how it was
calculated and what it excludes so that a scalar never hides sample, source,
coverage, method or uncertainty.

1. Any future metric is deterministic, versioned, reproducible, source-aware,
   sample-aware, uncertainty/currentness-aware, traceable and decomposable.
2. Cross-platform ratings are not naively averaged; insufficient or
   incomparable evidence withholds the metric.
3. A structured evaluator may classify bounded evidence but does not create a
   final reputation score or canonical truth. Jev remains replaceable,
   non-authoritative and not live-authorized.

### Story 4 — Protect rights and privacy

As a future sensor owner, I need source-specific rights, acquisition channel,
privacy, retention, deletion and provider-transmission conditions before any
collection or reuse.

1. Public visibility does not imply authorization for automated collection.
2. Private first-party analytics remain tenant-private and never silently
   enter canonical public AXIGLAND or cross-subscriber analyses.
3. Authenticated scraping, cookie export, CAPTCHA bypass and anti-bot evasion
   are not authorized by default. Reviewer profiles are out of scope.
4. Raw review text is not retained by default; deletion/currentness and rights
   bound permitted historical retention.

## Functional requirements

- **FR-001:** One MASTER canonizes four DRI families; no fifth product or
  competing authority is created.
- **FR-002:** DRI observes surfaces and conditions; it is not SEO/GEO execution,
  social management, review management or reputation repair.
- **FR-003:** MeasurementInstrument and version, conditions, time, sample,
  informative denominator and uncertainty bind a measurement claim.
- **FR-004:** Review, reviewer claim, source rating and source verification do
  not establish business truth, FAXT, AXIGNAL judgment or authenticity.
- **FR-005:** ExperienceTheme, ExperienceSignal, ReputationState, temporal
  change and RepresentationGap are explicit, inspectable derivations.
- **FR-006:** Any future aggregate reputation metric is deterministic,
  versioned, decomposable and traceable; unsupported metrics are withheld.
- **FR-007:** Public observation reuse is rights-bound, entity-resolved and
  deduplicated; private first-party data remains tenant-scoped.
- **FR-008:** Public experience may trigger AXENT/EOI research but reviews alone
  do not create DemandSignal, FAXT or opportunity.
- **FR-009:** UX and communication remain descriptive, sample-aware,
  uncertainty-aware and subordinate to product doctrine.
- **FR-010:** No runtime, source integration, scraping, API, schema, migration,
  dependency, provider, score implementation, UI or deployment is introduced.
- **FR-011:** No live Jev, TypeSafe credential, AXIGNAL model or external sensor
  call occurs in this slice.

## Acceptance examples (original DRI instrument tests)

| Case | Observation | Required interpretation |
|---|---|---|
| A — Reality vs representation | AXIGLAND has corroborated capability X; search/AI rarely surfaces the organization for X. | Keep capability and business state unchanged; a possible derived RepresentationGap may be surfaced. |
| B — Generative hallucination | A generative surface says the company makes quantum batteries; independent evidence is absent. | Record the surface response; do not create a business FAXT. |
| C — Cited but not named | Answer cites `company-a.com/document` but never names Company A. | `MENTION=NO`, `CITATION=YES`. |
| D — Private GSC | Subscriber connects private Search Console data with impressions. | Keep it tenant-private; no canonical public AXIGLAND update absent independent public evidence. |
| E — Shared SERP | One public SERP contains three organizations. | One authorized observation may be reused for all three after rights and resolution; no three independent acquisitions required. |
| F — Non-informative run | A generative run has no target names or citations and gives a generic answer. | Mark non-informative; do not infer negative visibility. |
| G — Instrument drift | A later period materially changes prompts, geography or surfaces. | Create a new instrument version; prohibit naive trend comparison. |
| H — Social signal | Public discussion increasingly associates a product with a use case. | Record a public signal; do not confirm demand or opportunity; AXENT research may follow. |
| I — Agency | An agency improves a website and comparable later observations show greater representation. | Report observed change; do not attribute causality without causal evidence. |
| J — Score | A system proposes `DIGITAL SCORE=84`. | Reject universal opaque scoring; prefer inspectable, source-aware dimensions. |

## Acceptance examples (public experience addendum)

| Case | Observation | Required interpretation |
|---|---|---|
| A — Review claim | Review says a product broke in 48 hours. | `REVIEW_OBSERVED=YES`; do not create product-failure FAXT. |
| B — Platform verification | Platform marks a review verified. | Preserve source-reported marker; do not claim AXIGNAL proved authenticity. |
| C — Evaluator classification | Future evaluator classifies delivery theme/polarity. | Classification is derived; no direct reputation score from evaluator. |
| D — Deterministic metric | Eligible observations are classified. | Classifications feed a deterministic versioned formula, never LLM → score. |
| E — Cross-source ratings | Sources use unlike scales and populations. | Naive mean is prohibited. |
| F — Review removal | Review is present at T1 and removed at T2. | Current projection is not present; historical observation survives only if rights permit. |
| G — Volume spike | Negative-review volume rises suddenly. | Pattern anomaly may be investigated; fraud/review bombing is not proven. |
| H — Market pain | Independent reviews repeat integration difficulty. | Possible ExperienceSignal/research objective; no automatic DemandSignal. |
| I — Product scope | Reviews address one product line. | Do not project automatically to the full organization. |
| J — Metric trace | User asks why an index equals 72. | Trace metric/version → formula/dimensions → classifications → observations → permitted source references. |

## Assumptions

- MASTER §54 is the single authority; ADRs, product spec and this Spec Kit
  derive from it.
- Sensor coverage, source rights, customer representativeness and production
  performance are not established by documentation.
- Reviews can inform investigation but do not bypass evidence admission.
- Product/UI and measurement contracts are future work; specification is not
  implementation evidence.

## Out of scope

Review crawlers/adapters/APIs; Trustpilot, Google, G2, Capterra or forum data
collection; browser automation; source accounts/credentials; database/schema,
migrations, runtime classes, jobs, queues, cron; Jev contracts/calls; LLM
classification; production or cross-source reputation score; CRM, workflow,
review response automation, reviewer profiles, UI implementation, deployment,
EOI-01 and DRI-01 implementation.

## Success criteria

- **SC-001:** The four families and Public Experience Intelligence converge
  across MASTER, ADRs, product spec, architecture, UX, communication and
  operational guidance.
- **SC-002:** Review, rating, verification, sentiment, anomaly and derived-gap
  epistemic boundaries are explicit.
- **SC-003:** Measurement conditions, version drift, sample size, coverage,
  uncertainty, source populations and currentness remain inspectable.
- **SC-004:** Rights, privacy, deletion, private/public separation and
  observation deduplication constrain future source reuse.
- **SC-005:** Future score authority is deterministic and decomposable; no
  evaluator creates the score or canonical truth.
- **SC-006:** EOI/DRI intersections permit research while preserving independent
  evidence admission and preventing reviews from automatically creating
  demand/opportunity.
- **SC-007:** Full deterministic gates and Graphify checks are recorded, one
  documentation-only commit is pushed to this branch, one unmerged PR is opened
  against updated `main`, and PR #18 remains unchanged.
