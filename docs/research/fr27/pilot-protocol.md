# FR-27 — One Buyer / One Job Pilot Protocol

**Status:** READY FOR REAL PILOT
**Pilot ID:** `fr27-agency-external-change-v1`
**Date prepared:** 2026-10-01

## Purpose

Run one falsifiable product-validation pilot without redefining AXIGNAL, without allowing commercial outcomes to alter canonical truth, and without treating non-public information as a discovery failure.

## Buyer hypothesis

**SEO/GEO/AEO agency responsible for an active client portfolio.**

This is a pilot hypothesis, not AXIGNAL's canonical market definition. AXIGNAL remains a general observing economic brain.

## Job to be done

> Detect a material externally observable change around one client, understand why it warrants attention, inspect the evidence, and decide whether further agency action or investigation is justified.

The pilot does not ask whether AXIGNAL can perform SEO/GEO/AEO work. It asks whether independent observation and explanation advance a real agency decision.

## Primary Xeed

The pilot uses one client Xeed as the unit of observation. The runtime identifier is assigned when the real pilot is created; the contract placeholder is `pilot:xeed:client-1`.

## Observability boundary before value judgment

FR-27 must classify the pilot job before discovery quality is interpreted:

- `PUBLICLY_OBSERVABLE`
- `PARTIALLY_OBSERVABLE`
- `PRIVATE_OR_NON_OBSERVABLE`
- `UNKNOWN`

The assessment is time-bound and persisted with provenance.

A public surface can record:

- `PRESENCE_OBSERVED`
- `NO_PRESENCE_OBSERVED`
- `NOT_OBSERVED`
- `SOURCE_UNAVAILABLE`
- `OUTSIDE_PUBLIC_SCOPE`

`NO_PRESENCE_OBSERVED` is a positive observation only when a defined surface/instrument was actually measured and provenance exists. It never means that the organization has no economic activity.

Private or non-observable facts — CRM state, pipeline, margins, internal priorities, private contracts and similar information — are not scored as AXIGNAL discovery failures.

## Xeed-private attention posture

The subscriber may privately state why public representation matters to this Xeed:

- `GROW_VISIBILITY`
- `MONITOR_VISIBILITY`
- `LOW_PROFILE`
- `UNKNOWN`

This preference changes only relevance projection. It never changes canonical organization state.

The same public observation can therefore have different Xeed-private relevance:

```text
NO_PRESENCE_OBSERVED + GROW_VISIBILITY
→ VISIBILITY_GAP_CANDIDATE

NO_PRESENCE_OBSERVED + LOW_PROFILE
→ LOW_EXPOSURE_OBSERVED

PRESENCE_OBSERVED + LOW_PROFILE
→ UNEXPECTED_EXPOSURE_CANDIDATE
```

These are attention projections, not FAXTs and not automatic recommendations to perform SEO, GEO, PR or reputation work.

## Pricing hypothesis under test

- first Xeed / subscription hypothesis: **€9.95/month**
- each additional Xeed hypothesis: **€4.95/month**

These remain hypotheses until observed willingness-to-pay evidence exists.

Usage, session duration, evidence inspection, return visits, Xignal count and feature engagement MUST NOT be transformed into willingness-to-pay.

## Required observation dimensions

The real pilot must capture all six dimensions, preserving YES, NO and UNKNOWN:

1. **Decision advancement** — did the surfaced Xignal materially advance a real decision?
2. **Evidence inspection** — did the user inspect the supporting evidence?
3. **Evidence trust report** — did the user explicitly report that the evidence was sufficiently trustworthy for the decision?
4. **Return because change occurred** — did the user explicitly report returning because AXIGNAL detected/reported a meaningful change?
5. **Willingness to pay** — stated maximum, accepted offer, declined offer or actual payment, with amount and currency.
6. **Additional-Xeed value** — did the user explicitly report value in monitoring another client/competitor/target with an additional Xeed?

A negative answer is valid evidence. UNKNOWN is valid evidence. Missing evidence is not converted to NO.

## Evidence sources

Allowed provenance:

- product telemetry;
- direct user report;
- interview record;
- offer response;
- payment record.

Restrictions:

- telemetry may prove an evidence view occurred, but not that evidence was trusted;
- telemetry may prove a return occurred, but not that the return was caused by a detected change;
- telemetry may not establish willingness to pay;
- a commercial win/loss may not establish or falsify epistemic truth;
- low public presence may be useful evidence, but does not prove poor marketing;
- public exposure may matter to a low-profile Xeed, but does not prove harm.

## FR-26 linkage

The pilot report must attach the exact FR-26 `UnitEconomicsReport` for the same Xeed. This provides cost, reuse, first-value and contribution-margin inputs without mixing them with user-validation evidence.

## Execution sequence

1. Select one real agency and one real client decision context.
2. Create the pilot Xeed and record its exact identifier.
3. Record the Xeed-private attention posture.
4. Define the public surfaces that are legitimate and relevant to observe.
5. Persist a `PilotObservabilityAssessment` before interpreting discovery quality.
6. Let AXIGNAL surface real evidence-backed observations/Xignals.
7. Record presence, measured absence, unavailable sources and out-of-scope private territory separately.
8. Present the result in the normal subscriber flow.
9. Observe evidence inspection through telemetry.
10. Ask the buyer whether the result advanced the actual decision.
11. Ask explicitly whether the evidence was sufficiently trustworthy for that decision.
12. After a genuine externally observed change and subsequent return, ask why they returned.
13. Present the pricing hypothesis explicitly and record stated/accepted/declined/paid evidence.
14. Ask whether an additional Xeed at the additional-Xeed price has concrete value and for what target.
15. Generate the pilot report from persisted observability + pilot evidence + matching FR-26 economics.
16. Preserve failure, contradiction, UNKNOWN and non-observable territory without rewriting the hypothesis after the fact.

## Completion rule

FR-27 is **not DONE** merely because this protocol, code, tests and persistence exist.

It may move to DONE only when:

- one real buyer has participated;
- one real job context has been observed;
- a real observability assessment is persisted;
- measured public presence/absence and out-of-scope private territory are distinguished;
- all six observation dimensions have evidence;
- the evidence is persisted with provenance;
- the matching FR-26 economics report exists;
- the result is documented even if negative or inconclusive.

## Non-goals

The pilot does not validate canonical truth, prove general product-market fit, prove agency causality, justify a pricing change, establish that agencies are AXIGNAL's only/best market, infer poor marketing from low public presence, or infer low exposure intent from low public presence.
