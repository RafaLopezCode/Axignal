# ADR-0015: Digital Measurements Are Instrument-Bound Reusable Observations

**Status:** Accepted measurement doctrine; pre-implementation.\
**Date:** 2026-09-26\
**Authority:** MASTER §§20, 46, 53 and 54; ADR-0014.

## Context

Search rank, generative answers, public conversation, platform ratings and
experience classifications vary by source, instrument, version, query, market,
time, sample and access method. Comparing unlike runs as a change in the
organization would mistake measurement drift for economic change. Repeated
acquisition per subscriber would waste compute and double-count evidence.

## Decision

Every digital measurement is bound to an identified and versioned instrument,
source/surface, conditions, time, sample, informative-run denominator,
uncertainty and permitted observation lineage. A material instrument change
creates a new comparison series unless a validated bridge exists. Non-informative
observations are not negative results; unknown is not zero.

```text
MEASUREMENT_INSTRUMENT_IS_VERSIONED
INSTRUMENT_VERSION_IS_PART_OF_RESULT
INSTRUMENT_DRIFT_BREAKS_NAIVE_COMPARISON
OBSERVATION_AMORTIZATION_IS_CORE
PUBLIC_OBSERVATION_CAN_ENRICH_MULTIPLE_XEEDS
PRIVATE_FIRST_PARTY_DATA_IS_ISOLATED
SAMPLE_SIZE_MUST_BE_VISIBLE
UNCERTAINTY_MUST_BE_PRESERVED
NONINFORMATIVE_OBSERVATION_IS_NOT_NEGATIVE_OBSERVATION
OFFICIAL_GOVERNED_ACCESS_PREFERRED
AUTHENTICATED_SCRAPING_NOT_AUTHORIZED_BY_DEFAULT
ANTI_BOT_EVASION_NOT_AUTHORIZED
SENSOR_ECONOMICS_PER_REUSABLE_OBSERVATION
REPUTATION_METRIC_IS_DETERMINISTIC
REPUTATION_METRIC_IS_VERSIONED
REPUTATION_METRIC_IS_TRACEABLE
CROSS_PLATFORM_RATINGS_NOT_NAIVELY_COMPARABLE
SAMPLE_SIZE_SURVIVES_AGGREGATION
CLASSIFICATION_VERSION_REQUIRED
METRIC_VERSION_REQUIRED
DELETION_PROPAGATES_TO_CURRENTNESS
DUPLICATES_MUST_NOT_DOUBLE_COUNT
```

Source-native ratings remain distinct. Cross-platform rating arithmetic,
source equality and population representativeness are not assumed. Any future
aggregate is a deterministic, versioned, inspectable and decomposable method
that preserves eligible sample, coverage, source, period, uncertainty and
currentness. An insufficient or incompatible sample withholds the metric.

Reviews and social observations are deduplicated before reuse; one experience
cannot become multiple evidence items merely through repeated, syndicated or
cross-posted acquisition. Public observations may be reused across relevant
Xignals only where rights and subject resolution permit. Private first-party
state remains tenant-only. Source removal propagates to currentness; historical
retention depends on source rights. Raw text retention is not automatic.

## Alternatives considered

- Compare by timestamp alone: rejected because the instrument and sample may
  have drifted.
- Average ratings and visibility across platforms: rejected because scales,
  populations, moderation and coverage differ.
- Reacquire separately for each Xignal: rejected because it duplicates cost
  and can double-count the same observation.
- Store all public content indefinitely: rejected because public visibility
  does not establish collection, retention or redistribution rights.
- Use a model-generated aggregate score: rejected because it is opaque,
  non-reproducible and confuses judgment with metric authority.

## Consequences

P0-DRI-01 must define minimum observation, instrument, deduplication, reuse,
currentness, rights and sensor-economics contracts before any provider or
acquisition implementation. Official/governed access is preferred; public
visibility alone is insufficient authority. No source, API, contract or
runtime is implemented by this decision.

## Risks and rollback

Provenance, retention and instrument comparability may be incomplete. Future
acquisition must fail closed when authority or rights are unknown; metrics
must be withheld when a valid comparison cannot be established. Amend through
a superseding ADR after an explicit MASTER change.
