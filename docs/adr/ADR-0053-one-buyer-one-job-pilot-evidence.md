# ADR-0053 — One Buyer / One Job Pilot Evidence Contract

**Status:** ACCEPTED
**Date:** 2026-10-01
**Decision scope:** FR-27
**Upstream authority:** MASTER §§22, 27–28, 33, 49–50, 56.16; Constitution II, IV, VIII, XII, XV

## Context

AXIGNAL needs product evidence that goes beyond product thesis while preserving its epistemic model. FR-27 requires one concrete buyer/job pilot measuring decision advancement, evidence inspection/trust, return because something changed, willingness to pay and the value of additional Xeeds.

Commercial behavior cannot validate canonical truth. Usage cannot be silently converted into willingness to pay. A failed pilot must remain valid evidence.

## Decision

The first governed product-validation hypothesis is:

- buyer: an SEO/GEO/AEO agency responsible for an active client portfolio;
- job: detect a material externally observable change around one client, understand why it warrants attention, inspect its evidence, and decide whether further agency action or investigation is justified.

This is a pilot hypothesis only. It does not redefine AXIGNAL as an SEO/GEO/AEO product.

Pilot evidence is stored in a separate append-only evidence ledger and may reference Xeed, Xignal and LearningEvent identities. It cannot write AXIGLAND canonical truth.

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
```

## Completion rule

Implementation, protocol and persistence make FR-27 ready to execute. They do not make the empirical pilot complete.

FR-27 may be marked DONE only after a real buyer/job pilot has persisted all six required evidence dimensions plus matching FR-26 economics.

## Consequences

The repository can now run a falsifiable pilot without polluting AXIGLAND, overstating pricing evidence or discarding negative outcomes. A future audit can distinguish implemented measurement capability from actual market evidence.

## Rejected alternatives

- **Infer willingness-to-pay from engagement:** rejected as non-evidence.
- **Infer trust from evidence clicks:** rejected because inspection and trust are distinct.
- **Treat any return session as change-driven retention:** rejected because causality requires explicit evidence.
- **Mark FR-27 DONE from synthetic fixtures:** rejected because the Frontier closure explicitly requires real buyer/job evidence.
