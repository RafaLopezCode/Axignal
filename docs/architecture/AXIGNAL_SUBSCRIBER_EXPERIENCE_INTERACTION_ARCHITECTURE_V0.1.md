# AXIGNAL Subscriber Experience Interaction Architecture V0.1

**Version:** 0.1\
**Status:** PROPOSED\
**Implementation status:** PRE_IMPLEMENTATION\
**Classification:** PROPOSED_INTERACTION_ARCHITECTURE\
**Feature:** P0-INTERACTION-01 (`specs/003-subscriber-experience-interaction/`)

This document specifies future interaction contracts. It is subordinate to
the MASTER Product Model, Engineering Constitution, accepted ADRs and Logical
Architecture Atlas. It creates no new accepted architectural authority and is
not evidence that a runtime exists.

## Boundary

```text
Canonical AXIGLAND
        ↓
AXIGNAL authorized subscriber projection
        ├── Human-first UI projections
        ├── Ask AXENT — by AXIGNAL (contextual cognitive projection)
        ├── Portable Xeed (Markdown / JSON projection)
        └── Product MCP (authorized read/query projection)
```

There is one canonical AXIGLAND. Subscriber UI, model response, export and
Product MCP are not canonical authority. Subscriber Experience is distinct
from AXIGNAL Internal Admin in purpose, authorization and projection. AXIGNAL
owns semantic meaning; a renderer draws its projection. Ask AXENT extends
understanding and does not compensate for poor deterministic information
design.

## Human-first interaction model

Default comprehension follows: What is happening? → What matters? → What
changed? → Why? → What supports this? → What else should I examine? Basic
comprehension does not require prompting. Progressive disclosure reveals
complexity without erasing it. Cognitive-question-to-representation mapping
includes feed/discoveries, economic map, graph, timeline, evidence/derivation,
PATHX, corporate structure, knowledge/observability and representation
anomalies. Graph is not the universal UI; graph hairball is not success.

Germination is a projection of actual state, never a cosmetic timer. First Map
reveal presents evidence-backed “What AXIGNAL learned”, “What AXIGNAL found”
and “What AXIGNAL did not expect” before or with “Explore your economic world”.
Today prioritizes explainable material changes since the prior visit. No opaque
WOW or universal materiality score is allowed.

## Canonical contract catalogue

The normative proposed definitions are maintained in
[`contracts/interaction-contracts.md`](../../specs/003-subscriber-experience-interaction/contracts/interaction-contracts.md):

1. Subscriber Projection
2. Germination Projection
3. Today / Attention / Material Change
4. Evolution / Temporal Projection
5. Evidence Drill-down
6. Graph / Map Projection
7. PATHX Presentation
8. Ask AXENT Context
9. Ask AXENT Response
10. Ask AXENT Research Escalation
11. Subscriber Authorization
12. Portable Xeed
13. Product MCP Read
14. Cognitive Provider Policy
15. Subscriber Cognitive Telemetry

All 15 preserve the same authority boundary and specify producer/consumer,
required meaning, hard invariants and failure/unknown semantics. Concrete wire
schemas, endpoints, storage, event names, authorization mechanism and UI
components remain deferred.

## V3 contextual private capability interaction

The V3 product specification owns private analytical questions, required
capabilities, access need and continuation. Subscriber Interaction owns only
the authorized projection of a V3 `PrivateCapabilityRequest` into the existing
Ask AXENT experience. An explicit V3 request may enter Ask AXENT directly;
private connection is optional at entry. AXENT first investigates with
available authorized context and requests access only when a material question
requires missing private evidence.

The request is presented as a contextual inline Card carrying the question,
reason, minimum requested and unnecessary scope, read-only default, decline
path and analytical continuation. Subscriber intent approval is not provider
authorization. Provider verification and granted scope determine capability
availability. Decline or access failure pauses or resolves only the affected
branch; successful availability resumes its original question. A secondary
Connections surface may expose access metadata and revoke/reconnect controls;
it is not mandatory onboarding. Modals/popups are reserved for provider,
legal, payment or security-sensitive transitions, not the default request
surface. A renderer such as AI Elements cannot own these semantics. See C16
in the interaction contract catalogue and V3 §44 for the domain contract.

This is an additive, subordinate reconciliation. It does not change the
human-first model, existing Ask AXENT authority, authorization boundary,
Admin boundary or pre-implementation status. No subscriber UI, Card,
connector, authorization or runtime is implemented or authorized.

## Cognitive policy and provider boundary

MASTER §53 supersedes the former proposed OpenAI/GPT-6 Luna/Batch and
Standard Responses defaults recorded in the historical research for this
interaction architecture. No provider or model is canonized here. AXIGNAL's
brain is its complete governed system, not a model. Deterministic computation
comes first; a replaceable structured evaluator is used only for bounded
judgment after answerability is established; missing context routes to AXENT
research or remains unknown/abstained. Model output never directs AXIGNAL or
becomes canonical truth. Any provider live use needs separate authorization,
rights and evaluation.

Context is the smallest useful authorized structured projection. Provider
identifiers, capability, context limits and pricing are mutable operational
facts, not product semantics. Missing cost is unknown, not zero.

## Claim review, portability and agent boundary

A subscriber may challenge a claim, which triggers independent reinvestigation
and policy evaluation; it does not edit canonical truth. Users may direct
attention, never conclusions. Xeed.md and Xeed.json are scoped temporal
projections, not authority. Product MCP is an explicitly authorized query
surface; no write authority is specified. External agents cannot mutate
AXIGLAND.

## Security, privacy and telemetry

All requests, context, responses, exports and MCP reads are account/Xeed
scoped. Authorization is enforced at retrieval and release boundaries.
Unrelated subscriber data, secrets and unnecessary PII do not enter model
context or telemetry. Private subscriber state does not silently become public
AXIGLAND truth. Telemetry is minimized, protected and lineage-aware. UX/cost
metrics are interpretable observations; no causal conclusion is encoded
without evidence.

## Non-goals and status

This document authorizes no production subscriber UI, Ask AXENT runtime, model
API call, Batch job, Brain, research loop, JEV, Source Router, Product MCP,
Xeed export runtime, Admin, Customer Operations, production dependency, schema
or migration. Follow-on implementation requires review/authorization of this
proposed contract and separate governed slices.

**Specified != implemented. Documented architecture != runtime evidence.**
