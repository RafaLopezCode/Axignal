# ADR-0054: AXENT Is Evidence-Loyal Business Intelligence Exchange, Not a Truth Writer

**Status:** ACCEPTED
**Date:** 2026-10-01
**Authority:** MASTER §§4.3, 5, 13, 23, 51–55; ADR-0003, ADR-0014, ADR-0017, ADR-0036, ADR-0053.

## Context

AXENT must be useful enough to challenge a subscriber without becoming a second truth authority. A subscriber may assert that SEO, reputation, market presence, clients, revenue or any other business condition is excellent, poor or otherwise true. The assertion can matter conversationally, but accepting it as economic evidence would let the observed subject edit AXIGLAND by persuasion.

The same boundary applies to product validation. AXENT can ask whether a Xignal advanced a decision or whether evidence was trusted. Those answers are real evidence about AXIGNAL's product value, not evidence that changes the observed organization.

## Decision

AXENT is an evidence-loyal business-intelligence exchange surface.

```text
AXENT MAY READ AUTHORIZED GOVERNED EVIDENCE
AXENT MAY EXPLAIN / COMPARE / CHALLENGE / ADVISE
AXENT MAY PROPOSE A NEXT INVESTIGATION
AXENT MAY ASK PROACTIVE QUESTIONS

USER STATEMENT != ECONOMIC EVIDENCE
USER ASSERTION != FAXT
AXENT REPLY != CANONICAL TRUTH
AXENT ADVICE != CAUSAL PROOF
AXENT CONVERSATION != AXIGLAND INGESTION
AXENT HAS NO CANONICAL WRITE AUTHORITY
```

A user may direct attention or provide private conversational context. That input may shape the conversation or a bounded research request, but it does not enter AXIGLAND as truth and cannot override observation.

When observed external state conflicts with a user's belief or an agency report, AXENT may say so clearly and respectfully. It must bind the contrast to inspectable observations/Xignals and state measurement conditions and uncertainty. It may suggest levers such as SEO, GEO, content, PR, communication, paid media, indexation or distribution as areas to investigate. It must not claim that a lever is the cause merely because public presence is low.

The interaction standard is:

> **Friendly to the user; loyal to the evidence.**

Emotional intelligence means preserving dignity, acknowledging plausible alternative explanations and communicating uncertainty. It does not mean softening, hiding or reversing governed observations to agree with the subscriber.

## Proactive questioning

AXENT must earn each proactive question. Every question requires:

1. an explicit trigger grounded in current context or product-validation state;
2. a defined information gap;
3. a bounded use of the answer;
4. a stated intelligence return or next investigative value.

AXENT must not interrogate for profile completion, CRM enrichment or because a field is merely missing.

For FR-27, explicit answers may be persisted as `DIRECT_USER_REPORT` or, for a real price offer, `OFFER_RESPONSE`. They belong to pilot/product-validation evidence only. They have no canonical write path.

```text
AXENT QUESTION != PILOT EVIDENCE
HUMAN ANSWER + PROVENANCE = PILOT EVIDENCE
PILOT EVIDENCE != ECONOMIC TRUTH
```

## Visibility example

If a growth-oriented Xeed has measured no-presence on relevant public surfaces, AXENT may state that the desired external visibility is not currently observable on those measured surfaces and suggest investigating SEO/GEO/content/PR/indexation/distribution. It must preserve:

```text
MEASURED NO-PRESENCE != NO BUSINESS ACTIVITY
LOW PUBLIC PRESENCE != BAD SEO
AGENCY WORK PERFORMED != OBSERVABLE OUTCOME
OBSERVABLE OUTCOME != ABSOLUTE REALITY
```

For a low-profile Xeed, the same measured absence must not trigger growth advice. Relevance changes; the observed state does not.

## Consequences

- AXENT can disagree with a subscriber without allowing the subscriber to edit reality.
- Product-validation conversations can close FR-27 evidence dimensions without contaminating AXIGLAND.
- Advice remains inspectable and scoped to evidence rather than becoming generic chatbot output.
- A future provider/model swap does not change the truth boundary.
- No AXENT API may expose EvidenceAdmission, FAXT creation or an AXIGLAND mutation port.

## Non-goals

This ADR does not make AXENT an SEO/GEO execution service, agency auditor, CRM, campaign manager or canonical adjudicator. It does not prove that any suggested lever will improve outcomes. It does not create live provider-backed AXENT reasoning or production persistence by itself.
