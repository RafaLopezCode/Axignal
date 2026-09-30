# ADR-0025 — AXIGNAL Prime cognitive control plane

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER Product Model §§56.13–56.20 and Engineering Constitution IX, X, XVII, XX.

## Context

AXIGNAL now has persistent Observation Memory, governed source acquisition, document representation, rich subject state and grounded semantic claim candidates. The MASTER also establishes Python as the control plane, structured evaluators as replaceable providers, and AXENT/LLM as adaptive intelligence rather than a universal observer.

The remaining risk is to encode one provider or one rigid germination pipeline as the Brain itself. The existing application/xeed_germination/semantic_flow.py is useful historical implementation evidence but represents a fixed retrieve→investigate→support→admit flow and MUST NOT define AXIGNAL Prime architecture.

## Decision

AXIGNAL Prime introduces a provider-neutral cognitive control plane with exactly three mechanism families:

1. DETERMINISTIC — exact mechanisms owned by Python/code.
2. STRUCTURED_EVALUATOR — bounded semantic judgments behind a replaceable provider boundary.
3. ADAPTIVE_RESEARCH — open-ended investigation/source discovery/ambiguity resolution performed by AXENT/cognitive providers.

Routing authority remains AXIGNAL-owned and deterministic. A model/evaluator MUST NOT decide which mechanism family owns its own work.
Every impacted semantic dimension requires an explicit, versioned DimensionRoutingPolicy. Missing policy fails closed. If the pre-provider Answerability Gate reports missing state, Prime routes the dimension to ADAPTIVE_RESEARCH and preserves the explicit missing requirements. An answerable dimension may route only to DETERMINISTIC or STRUCTURED_EVALUATOR.

The control plane does not select concrete providers. OpenAI Decisions, TypeSafe Jev, Luna structured output or future providers are adapters/policies outside this core and must be switchable without changing domain truth mechanics.

## Stable core versus intentionally open architecture

This ADR freezes the routing authority and mechanism families, but deliberately does **not** freeze the Xeed prospecting/germination strategy. In particular it does not decide:

- whether first bootstrap work is deterministic, adaptive or mixed;
- source-discovery ordering;
- when existing shared observation memory is sufficient;
- how aggressively to fan out initial observation;
- exact information-value/cost policy;
- provider choice or evaluator fallback/shadow strategy;
- learning-policy promotion.

Those questions require a separate Xeed germination architecture decision.

## Learning boundary

AXIGNAL learning is system-level, not provider memory. Observation outcomes, research yield, source economics, evaluator performance and later corrections may become governed learning inputs, but this ADR does not authorize self-modifying production policy.
Future learning machinery must be replayable, versioned, attributable and promoted through explicit governance.

MODEL LEARNING != AXIGNAL LEARNING

PROVIDER MEMORY != AXIGLAND MEMORY

PROMPT TUNING != GOVERNED LEARNING

## Consequences

- Prime routing is testable offline and independent of provider availability.
- NOT_ANSWERABLE cannot silently become a negative semantic result.
- A new evaluator can be introduced without changing the Prime control plane.
- Adaptive intelligence is reserved for missing state/ambiguity rather than becoming a mandatory first hop.
- The legacy germination runtime remains untouched until the separate architecture is resolved.
- No canonical write, EvidenceAdmission change, production model call, deployment or database migration is introduced by this slice.
