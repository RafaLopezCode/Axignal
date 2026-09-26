# ADR-0014: Digital Representation Intelligence Is a Core AXIGNAL Observation Capability

**Status:** Accepted product doctrine; pre-implementation.\
**Date:** 2026-09-26\
**Authority:** MASTER §§22, 46 and 54.

## Context

AXIGNAL observes the economy independently of subscriber or agency
configuration. Digital discovery and public experience surfaces affect how an
organization is found, represented and discussed. Treating their outputs as
reality would leak surface bias, private tenant information or evaluator
judgment into canonical economic knowledge. Treating public reviews as facts
would exceed their evidence authority and risk unsupported claims.

## Decision

DRI is a core, source-neutral observation capability with four families:
search; generative; social/public conversation; and public reputation/experience.
Public Experience Intelligence belongs within DRI, not as a separate product.
DRI connects condition-bound observations with economic capabilities, markets,
demand, reach, competitors, opportunities and time while keeping observation,
derivation and canonical truth distinct.

The following are binding:

```text
DRI_IS_CORE=YES
DRI_IS_SEO_TOOL=NO
DRI_IS_GEO_TOOL=NO
DRI_IS_SOCIAL_MANAGER=NO
REPRESENTATION_IS_NOT_REALITY
DIGITAL_OBSERVATION_IS_CONDITION_BOUND
MENTION_IS_NOT_CITATION
CITATION_IS_NOT_ENDORSEMENT
GENERATIVE_OUTPUT_IS_NOT_BUSINESS_TRUTH
SOCIAL_VOLUME_IS_NOT_DEMAND
REVIEW_IS_NOT_BUSINESS_TRUTH
REVIEWER_CLAIM_IS_NOT_FAXT
PLATFORM_RATING_IS_NOT_AXIGNAL_JUDGMENT
PLATFORM_VERIFICATION_IS_NOT_AXIGNAL_AUTHENTICITY
SENTIMENT_IS_DERIVED
REPUTATION_GAP_IS_DERIVED
DRI_MAY_FEED_EOI
EOI_MAY_FEED_DRI
NO_UNIVERSAL_DIGITAL_SCORE
```

An experience pattern needs multiple observations, scope and a temporal
window. A representation/reputation gap is an explainable INXIGHT, not a FAXT
or proof of capability failure. Reviews may create research objectives but do
not automatically create demand or opportunity. Product, location and
organization experience are distinct subjects. Anomaly is not fraud.

## Alternatives considered

- A standalone SEO/GEO/reputation product: rejected because it fragments the
  economic brain and encourages surface-only optimization.
- A review-management or reputation-repair tool: rejected because AXIGNAL
  observes; it does not execute campaigns, responses or review disputes.
- Treating reviews, platform marks or generated answers as business facts:
  rejected because source-reported claims do not meet AXIGLAND truth admission.
- Omitting public experience: rejected because it can be a useful, distinct
  perception of product/service outcomes and an AXENT research trigger.

## Consequences

Search, generative, public conversation and public experience remain separate
instrument-bound observation families. Subscriber projections can expose their
intersections with capabilities and opportunity only with provenance, temporal
context, uncertainty and scope. Private first-party analytics remain isolated.
Future evaluators may classify bounded evidence but do not determine truth or
final scores. No implementation is authorized by this ADR.

## Risks and rollback

Surface, sample and selection bias may create false certainty or defamatory
overreach. Future designs must be descriptive, scope-bound and traceable. If
this doctrine conflicts with source rights or a higher authority, fail closed;
revise through the MASTER and a superseding ADR rather than silently changing
data semantics.
