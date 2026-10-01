# FR-27 — One Buyer / One Job Pilot Protocol

**Status:** READY FOR REAL PILOT
**Pilot ID:** `fr27-agency-external-change-v1`
**Date prepared:** 2026-10-01

## Purpose

Run one falsifiable product-validation pilot without redefining AXIGNAL and without allowing commercial outcomes to alter canonical truth.

## Buyer hypothesis

**SEO/GEO/AEO agency responsible for an active client portfolio.**

This is a pilot hypothesis, not AXIGNAL's canonical market definition. AXIGNAL remains a general observing economic brain.

## Job to be done

> Detect a material externally observable change around one client, understand why it warrants attention, inspect the evidence, and decide whether further agency action or investigation is justified.

The pilot does not ask whether AXIGNAL can perform SEO/GEO/AEO work. It asks whether independent observation and explanation advance a real agency decision.

## Primary Xeed

The pilot uses one client Xeed as the unit of observation. The runtime identifier is assigned when the real pilot is created; the contract placeholder is `pilot:xeed:client-1`.

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
- a commercial win/loss may not establish or falsify epistemic truth.

## FR-26 linkage

The pilot report must attach the exact FR-26 `UnitEconomicsReport` for the same Xeed. This provides cost, reuse, first-value and contribution-margin inputs without mixing them with user-validation evidence.

## Execution sequence

1. Select one real agency and one real client decision context.
2. Create the pilot Xeed and record its exact identifier.
3. Let AXIGNAL surface a real, evidence-backed Xignal.
4. Present the Xignal in the normal subscriber flow.
5. Observe evidence inspection through telemetry.
6. Ask the buyer whether the Xignal advanced the actual decision.
7. Ask explicitly whether the evidence was sufficiently trustworthy for that decision.
8. After a genuine externally observed change and subsequent return, ask why they returned.
9. Present the pricing hypothesis explicitly and record stated/accepted/declined/paid evidence.
10. Ask whether an additional Xeed at the additional-Xeed price has concrete value and for what target.
11. Generate the pilot report from persisted evidence + the matching FR-26 economics report.
12. Preserve failure, contradiction and UNKNOWN without rewriting the hypothesis after the fact.

## Completion rule

FR-27 is **not DONE** merely because this protocol, code, tests and persistence exist.

It may move to DONE only when:

- one real buyer has participated;
- one real job context has been observed;
- all six observation dimensions have evidence;
- the evidence is persisted with provenance;
- the matching FR-26 economics report exists;
- the result is documented even if negative or inconclusive.

## Non-goals

The pilot does not validate canonical truth, prove general product-market fit, prove agency causality, justify a pricing change, or establish that agencies are AXIGNAL's only/best market.
