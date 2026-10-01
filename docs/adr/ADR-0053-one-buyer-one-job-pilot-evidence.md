# ADR-0053 — One Buyer / One Job Pilot Evidence Contract

**Status:** ACCEPTED
**Date:** 2026-10-01
**Decision scope:** FR-27
**Upstream authority:** MASTER §§22, 27–28, 33, 49–50, 54, 56.16; Constitution II, IV, VIII, XII, XV

## Context

AXIGNAL needs product evidence that goes beyond product thesis while preserving its epistemic model. FR-27 requires one concrete buyer/job pilot measuring decision advancement, evidence inspection/trust, return because something changed, willingness to pay and the value of additional Xeeds.

Commercial behavior cannot validate canonical truth. Usage cannot be silently converted into willingness to pay. A failed pilot must remain valid evidence.

FR-27 must also respect AXIGNAL's external-observability boundary. A buyer may know private facts that AXIGNAL cannot independently observe. Conversely, a measured absence of public presence can itself be useful information when the observation surface and provenance are explicit.

## Decision

The first governed product-validation hypothesis is:

- buyer: an SEO/GEO/AEO agency responsible for an active client portfolio;
- job: detect a material externally observable change around one client, understand why it warrants attention, inspect its evidence, and decide whether further agency action or investigation is justified.

This is a pilot hypothesis only. It does not redefine AXIGNAL as an SEO/GEO/AEO product.

Pilot evidence is stored in a separate append-only evidence ledger and may reference Xeed, Xignal and LearningEvent identities. It cannot write AXIGLAND canonical truth.

Before discovery quality is interpreted, the pilot persists a `PilotObservabilityAssessment` distinguishing publicly observable, partially observable, private/non-observable and unknown territory. Per-surface results distinguish presence, measured absence, not observed, source unavailable and outside-public-scope state.

`NO_PRESENCE_OBSERVED` is valid only when a defined public surface was actually measured and provenance exists. It means that no qualifying presence was observed on that measured surface; it does not mean that the organization has no economic activity, poor marketing, no demand or deliberate low-profile intent.

A Xeed may privately carry `GROW_VISIBILITY`, `MONITOR_VISIBILITY`, `LOW_PROFILE` or `UNKNOWN` attention posture. This changes relevance projection only and cannot create FAXT or organization truth. The same measured absence may therefore become a visibility-gap candidate for a growth-oriented Xeed or low-exposure evidence for a low-profile Xeed; observed presence may become an exposure candidate for a low-profile Xeed.

## Required evidence dimensions

The pilot preserves evidence independently for:

1. decision advancement;
2. evidence inspection;
3. explicit evidence-trust report;
4. explicit return-because-change report;
5. willingness-to-pay evidence;
6. additional-Xeed value.

YES, NO and UNKNOWN are all valid observations. Missing evidence is not NO.

## Pricing

The current €9.95 first-Xeed and €4.95 additional-Xeed figures remain hypotheses.

Willingness-to-pay requires explicit evidence such as stated maximum, accepted offer, declined offer or payment. Product telemetry cannot establish willingness to pay.

## FR-26 linkage

A pilot report must attach the matching FR-26 UnitEconomicsReport for the same primary Xeed. Product-validation evidence and unit economics are combined for inspection but retain separate authority.

## Invariants

```text
PILOT HYPOTHESIS != PRODUCT DEFINITION
USAGE != WILLINGNESS TO PAY
EVIDENCE INSPECTION != EVIDENCE TRUST
RETURN VISIT != RETURN BECAUSE CHANGE
COMMERCIAL OUTCOME != EPISTEMIC VALIDITY
PILOT EVIDENCE != CANONICAL TRUTH
NO != FAILURE OF EPISTEMOLOGY
UNKNOWN != NO
MISSING EVIDENCE != NEGATIVE EVIDENCE
NOT OBSERVED != ABSENT
NOT PUBLIC != FALSE
PRIVATE UNKNOWN != DISCOVERY FAILURE
LOW PUBLIC PRESENCE != POOR MARKETING
LOW PUBLIC PRESENCE != LOW-PROFILE INTENT
XEED ATTENTION POSTURE != ORGANIZATION TRUTH
OBSERVATION IS SHARED != RELEVANCE IS SHARED
```

## Completion rule

Implementation, protocol and persistence make FR-27 ready to execute. They do not make the empirical pilot complete.

FR-27 may be marked DONE only after a real buyer/job pilot has persisted a real observability assessment, distinguished measured public presence/absence from private/out-of-scope territory, captured all six required evidence dimensions, and attached matching FR-26 economics.

## Consequences

The repository can now run a falsifiable pilot without polluting AXIGLAND, overstating pricing evidence, discarding negative outcomes or misclassifying non-public information as product failure.

Low public presence can be useful evidence for a growth-oriented Xeed while the same observation can be useful confirmation for a low-profile monitoring Xeed. Conversely, a public mention can be an exposure candidate for a low-profile Xeed. The underlying public observation remains unchanged.

A future audit can distinguish source/coverage failure, legitimate non-observability, measured low public presence, Xeed-private relevance and actual decision value.

## Rejected alternatives

- **Infer willingness-to-pay from engagement:** rejected as non-evidence.
- **Infer trust from evidence clicks:** rejected because inspection and trust are distinct.
- **Treat any return session as change-driven retention:** rejected because causality requires explicit evidence.
- **Treat private/non-observable facts as discovery failures:** rejected because AXIGNAL must fail closed to UNKNOWN outside its public-economic boundary.
- **Treat low public presence as proof of poor marketing:** rejected because intent and private reality are not established by absence.
- **Write the Xeed visibility posture into organization truth:** rejected because user attention does not configure canonical state.
- **Mark FR-27 DONE from synthetic fixtures:** rejected because the Frontier closure explicitly requires real buyer/job evidence.
