# AXIGNAL Digital Representation Intelligence Product Specification

**Status:** PROPOSED / PRE_IMPLEMENTATION  \\
**Authority:** MASTER Product Model §§22, 46 and 54; ADR-0014 and ADR-0015.  \\
**Scope:** Product semantics and measurement doctrine only. This document does
not establish implemented coverage, runtime behavior, source rights or provider
authorization.

## Product role

Digital Representation Intelligence (DRI) is AXIGNAL's independent observation
of how an organization is represented across digital discovery and public
experience surfaces, connected to the governed economic world. It is a core
observation capability of the AXIGNAL Economic Brain, not an SEO/GEO tool,
social manager, review-management platform, reputation-repair service or
standalone reputation SaaS.

```text
OBSERVABLE ECONOMY
+ DIGITAL REPRESENTATION
+ PUBLIC EXPERIENCE
+ DEMAND / PROJECTS / MARKETS
+ CAPABILITY-SPECIFIC REACH
+ TEMPORAL MEMORY
+ EXPLANATION
```

The four perceptive families are:

1. **Search Representation** — results observed for identified query, market,
   language, surface and time conditions.
2. **Generative Representation** — answers observed on a named product surface
   or API. Product UI and model API are different instruments.
3. **Social / Public Conversation Representation** — public mentions,
   citations, themes and conversation under source- and period-specific
   observation conditions.
4. **Public Reputation / Experience Representation** — structured and
   unstructured public experience signals associated with an organization,
   product, service or location from authorized sources.

Public Experience Intelligence is a capability within DRI, not a fifth product.
It may describe ratings, reviews, complaints, praise, recurring themes,
experience targets, company responses, changes, source-reported verification,
volume changes and anomalies without turning an individual opinion into
economic truth.

## Canonical semantics

`DigitalRepresentationObservation`, `MeasurementInstrument`,
`ReviewObservation`, `ExperienceTheme`, `ExperienceSignal`, `ReputationState`,
`ReputationChange`, `ReputationGap` and `RepresentationGap` are semantic
concepts only. They do not imply a Python class, schema, graph node, API,
database, sensor or production capability.

A future `ReviewObservation` can preserve source and source review ID, resolved
subject scope, source-native rating/scale, permitted review text or reference,
review and experience dates when explicitly supplied, observed-at time,
platform-reported verification, a separate company response and date,
currentness, source lineage and raw observation reference. Rights may require an
ID, fingerprint, excerpt or link instead of retaining raw text.

The following distinctions are mandatory:

```text
SURFACE REPRESENTATION != ECONOMIC REALITY
REVIEW != BUSINESS_TRUTH
REVIEWER_CLAIM != FAXT
PLATFORM_RATING != AXIGNAL_JUDGMENT
PLATFORM_VERIFICATION != AXIGNAL_AUTHENTICITY_JUDGMENT
MENTION != CITATION
CITATION != ENDORSEMENT
SENTIMENT != EXPERIENCE_FACT
ANOMALY != FRAUD
```

An observation records what an identified source displayed or a person
reported; it does not validate the underlying claim. A verified marker remains
source-reported. A response is a separate observation; response relevance does
not establish resolution. Organization, brand, product, service, location,
branch, seller and transaction are distinct subject scopes unless an explicit
resolution contract connects them.

`ExperienceTheme` is a versioned, inspectable and traceable derivation; the
examples delivery, support, quality, billing, installation, reliability,
value, documentation and onboarding do not freeze a taxonomy. `ExperienceSignal`
is a recurring, temporally bounded, evidence-backed pattern across multiple
public experience observations. A `ReputationState` is a derived, multidimensional
representation. A `ReputationChange` needs compatible temporal windows,
source coverage, subject resolution, eligibility and methodology. A
`ReputationGap` or `RepresentationGap` is derived INXIGHT, never FAXT or proof
that an observed capability is false.

Reviews are a sample, not the customer population. Percentages must identify
eligible observed reviews, period, sources, sample size, classification
version, coverage and uncertainty. Cross-platform ratings are not naively
comparable or automatically averaged. Source-native values stay identifiable.
Duplicate, syndicated, cross-posted or repeated ingestion must not multiply
one experience into independent evidence. Deletion changes currentness;
historical observation may remain only when rights permit. Removal does not
prove falsity and its cause stays unknown unless the source establishes it.

## Measurement and evaluator boundary

Every measurement result is bound to its instrument and version, observable
surface/source, conditions, observed-at time, sample/replicates, informative-run
denominator, raw observations or permitted references, and uncertainty. A
version or material instrument drift creates a discontinuity; do not claim a
company change from a method change. A non-informative run is not a negative
observation; unknown is not zero.

`MeasurementInstrument` is a versioned, inspectable specification of the
conditions for producing and comparing observations. Future contracts may
identify purpose and market/category; query and prompt families plus frozen
items; geography, language and any persona/context; surfaces and execution
mode; replicate policy; entity-detection, citation-extraction and
ranking/prominence semantics; informative-observation criteria; statistical
methodology version; and created/frozen times. A result without instrument ID
and version is not comparable. Material changes start a discontinuous series
unless a validated bridge is specified. A validated prompt/query family is
reusable measurement infrastructure, not disposable per-company prompt craft.

Repeated or stochastic metrics need an explicit method matched to the
measurement question, design, compatible instruments and adequate sample;
candidate methods for later contract selection include Wilson or bootstrap
intervals, Fisher exact, McNemar, Mann-Whitney, Wilcoxon, Cliff's Delta,
Jaccard, Kendall Tau, Rank-Biased Overlap and Fleiss Kappa. This list selects
no library or method and does not justify statistical claims by itself.

Future evaluator families may classify review polarity, topic, severity,
experience target, complaint/praise type, expectation failure or company
response relevance. These are future contract candidates; this slice freezes no
answer spaces. A replaceable structured evaluator may classify bounded
evidence after structured state and answerability checks. **Jev may classify
evidence. It must not hide evidence behind a number.** Jev is replaceable,
non-canonical and not live-authorized.

The candidate classification families are:

```text
REVIEW_EXPERIENCE_POLARITY
REVIEW_TOPIC_CLASSIFICATION
REVIEW_ISSUE_SEVERITY
REVIEW_EXPERIENCE_TARGET
REVIEW_COMPLAINT_TYPE
REVIEW_PRAISE_TYPE
REVIEW_EXPECTATION_FAILURE
REVIEW_COMPANY_RESPONSE_RELEVANCE
```

Each future classification preserves its method/version and input references;
response relevance is not evidence that the issue was resolved. These names
record semantic candidates only and freeze no executable answer space.

```text
CLASSIFICATION_VERSION_REQUIRED
METRIC_VERSION_REQUIRED
DELETION_PROPAGATES_TO_CURRENTNESS
DUPLICATES_MUST_NOT_DOUBLE_COUNT
```

Any future reputation metric must be deterministic, versioned, reproducible,
inspectable, source-aware, sample-aware, uncertainty-aware, currentness-aware,
traceable and decomposable. Any weight must be visible and contract-bound; a
LLM-generated score is forbidden. A methodology version change is not a
reputation change. Insufficient samples, incompatible source populations, low
classification coverage, instrument drift or unknown currentness withhold the
metric as not answerable. A displayed aggregate exposes method/version, period,
sample, sources, coverage, uncertainty and a trace down to permitted source
evidence.

## Reuse, rights, privacy and EOI

Observe a permitted public item once, resolve its subject, deduplicate it,
reuse it in relevant projections and preserve its history without double
counting. Public observations may enrich multiple Xignals when rights and
entity resolution permit. Private first-party analytics are classified by
acquisition channel and remain tenant-private; they do not silently enter
public AXIGLAND or cross-subscriber analysis.

For every future sensor, source identity, authority, rights, access method,
terms, database/content rights, privacy, retention, deletion, provider
transmission and currentness require review. Public visibility does not mean
authorized automated collection. Prefer official/governed access. Authenticated
scraping, cookie export, CAPTCHA bypass and anti-bot evasion are not authorized
by default. Minimize reviewer personal data; no cross-platform reviewer profile
graph. Raw review retention is never automatic; a source reference, review ID,
permitted excerpt, fingerprint or metadata may be the appropriate trace.

Future sensor selection and registry semantics should expose family/surface,
public/private channel, coverage, geography/language, method/auth requirements,
rights, cost, freshness, historical depth, raw-data retention, measurement
semantics, stochasticity and reuse potential. Compare coverage, quality,
rights, latency, freshness, stability, cost and reuse; prefer the cheapest
sufficient governed sensor for a shared information requirement. Evaluate
economics per legitimately reusable observation, not only per Xignal/Xeed.
No sensor router, executable registry or formula is defined here.

Public experience can surface an AXENT research objective or a possible market
pain signal. Reviews alone do not create a FAXT, `DemandSignal` or opportunity.
Repetition, scope, time, entity/product resolution and independent economic
evidence are needed before a demand conclusion. EOI may direct DRI measurement;
DRI/experience observations may trigger EOI reevaluation, with epistemic
boundaries preserved.

## Subscriber, agency and explanation value

Future Today, Explore, Evolution, Evidence and Ask AXENT projections may expose
what is represented, recurring praise/issues, experience anomalies, reputation
change and gaps alongside capabilities, markets, demand and opportunity. Each
claim should explain why it appears, its source/surface, instrument/version,
conditions, time, sample, what was observed or derived, deterministic method,
uncertainty and what remains unknown. AXENT may investigate and explain
persisted evidence; it cannot invent reviews, judge reviewer honesty, claim
fraud without evidence or rewrite observations.

Agency proposition: **You improve the company. AXIGNAL independently observes
what changed.** A comparison requires comparable instruments and conditions.
The moat is not more dashboards; it is connecting reusable digital
observations to a governed economic world.

## Out of scope

No crawler, review-platform adapter, scraping, browser automation, API, schema,
database, migration, runtime classes, jobs, cron, queue, evaluator contract,
LLM classification, production score, subscriber UI, provider, credential,
deployment or live measurement experiment. No review-source rights or global
coverage claim is made. P0-DRI-01 is not started by this specification.
