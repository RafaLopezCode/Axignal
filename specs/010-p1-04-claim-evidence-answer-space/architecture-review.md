# Architecture Review: P1-04 Claim Evidence Answer Space

**Review outcome:** APPROVED WITHIN EXPERIMENTAL SCOPE
**Date:** 2026-09-26
**Authority:** MASTER §4.5, §5, §15.1–15.4, §20, §46; Constitution IV, VI, VIII, IX, X; ADR-0011; V0.2.

## Finding

The current V-next.1 claim/evidence option meanings declare `NOT_SUPPORTED` only when relevant evidence neither supports nor contradicts the proposition. None of the remaining options denotes one coherent relevant evidence set directly refuting a material claim assertion. `UNRESOLVED` is a fallback for genuine ambiguity, not a semantically valid encoding of a clear contradiction. The declared `EXHAUSTIVE_WITH_UNRESOLVED` coverage is therefore mechanically valid but semantically incomplete.

## Evidence and conceptual closure table

| Claim ↔ supplied evidence state | V-next.1 mapping | Closure result | V-next.2 mapping |
|---|---|---|---|
| FULL_SUPPORT | `SUPPORTED` | Representable | `SUPPORTED` |
| PARTIAL_SUPPORT without refutation | `PARTIAL` | Representable | `PARTIAL` |
| DIRECT_CONTRADICTION in coherent relevant evidence | None semantically valid | **Missing** | `CONTRADICTED` |
| RELEVANT_NON_SUPPORT; neutral to claim | `NOT_SUPPORTED` | Representable | `NOT_SUPPORTED` |
| No relevant passage among one or more supplied passages | `NO_EVIDENCE` | Representable | `NO_EVIDENCE` |
| Materially incompatible evidence assertions about same scope/time | `CONFLICTING` | Representable, definition underspecified | `CONFLICTING` |
| Relevant evidence but scope/meaning/time prevents a unique answer | `UNRESOLVED` | Representable | `UNRESOLVED` |

**V-next.1 closure:** `ANSWER_SPACE_EXHAUSTIVE=NO`.
**Missing:** direct coherent refutation (`CONTRADICTED`).
**Overlaps/underspecification:** `UNRESOLVED` is broad enough to swallow cases with distinct intended classes; it must be restricted to genuine indeterminacy. `CONFLICTING` needs source-source disagreement semantics.
**Unreachable:** literal zero supplied passages cannot reach any provider judgment under the min-cardinality-one `StateContract`; `NO_EVIDENCE` remains reachable when supplied passages exist but none is relevant. The gate validates structural content and provenance only, not relevance.

## Decision and risks

Register a new V-next.2 question ID and fingerprint; never mutate V-next.1. Reuse the existing state shape. A new option introduces no new canonical authority and does not assert evidence truth. Tests validate representation and binding, not provider accuracy or truth adjudication.

## Non-functional checks

- No production evaluator or provider runtime changes.
- No provider SDK import/call, network experiment, or credential access.
- No rewrite of V-next.1, P0-JEV-03, or PR #16 evidence.
- No expansion into V0.3 architecture.
