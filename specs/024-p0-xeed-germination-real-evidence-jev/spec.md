# Feature Specification: P0 Xeed Germination Real Evidence + Jev

**Feature Branch**: `feature/p0-real-corpus-jev-germination`
**Created**: 2026-09-30
**Status**: Implementation slice; live Jev execution blocked by missing local credential.
**Authority**: MASTER §§14–15 and §53.1; Constitution; existing P0-JEV contracts; subordinate to canonical evidence authority.

## Objective

Connect the first evidence-labeled, real-public-source claim-support path to Xeed germination without allowing semantic retrieval, Jev, a source, or an LLM to become truth authority.

The governing path is:

```text
Authorized Xeed
→ semantic retrieval candidate
→ deterministic eligibility filters
→ bounded investigation
→ explicit atomic claim + exact evidence passage + provenance
→ AnswerabilityGate
→ replaceable structured evaluator (Jev candidate)
→ deterministic semantic policy
→ EvidenceAdmission
→ evidence ledger
→ canonical FAXT writer
```

## Jev precision contract

Jev receives semantic content, not IDs standing in for content. Every claim-support request MUST contain:
- one explicit atomic claim proposition;
- one or more bounded evidence passages;
- source reference/provenance;
- the frozen `CES.SUPPORT.vNext.2` answer space;
- a pinned model identifier when Jev is used.

Gold labels, evaluator notes, expected outcomes, downstream policy and canonical state MUST NOT be provider-visible.

`NO_EVIDENCE != NOT_SUPPORTED != CONTRADICTED != CONFLICTING != UNRESOLVED`.

Operational/provider failure MUST NOT be converted into a semantic class. Missing/unanswerable state MUST be rejected before a provider call.

For this first atomic-FAXT slice, only `SUPPORTED` may continue toward EvidenceAdmission. `PARTIAL` indicates the proposed FAXT is too broad or evidence is insufficient and therefore fails closed rather than being silently narrowed by the evaluator.

## Real evidence corpus V0.1

The first corpus uses bounded excerpts from current official Carrier and Daikin public product/cold-chain pages observed 2026-09-30. It contains 12 independently labeled claim/evidence pairs spanning SUPPORTED, CONTRADICTED and NO_EVIDENCE.

This corpus is evidence-labeled but small and intentionally non-representative. It has `promotion_authority=false`. It can expose request/state/answer-space defects and obvious Jev failure modes; it cannot establish production calibration, global economic-domain accuracy or a deployment threshold.

## Acceptance

1. Every corpus case passes the existing V-next AnswerabilityGate.
2. Gold labels never cross the provider boundary.
3. The Jev adapter receives exact claim/evidence semantics plus provenance.
4. Provider failure fails closed and remains operational failure.
5. Raw provider-neutral judgment provenance (class, distribution when available, confidence when available, model, state/question fingerprints and replay reference) is retained independently of canonical evidence.
6. Germination cannot reach EvidenceAdmission unless semantic support is explicitly SUPPORTED.
7. EvidenceAdmission remains independently necessary after semantic support.
8. No Jev confidence/probability is treated as truth or exposed as a product score.
9. The live runner refuses to fabricate results when `TYPESAFE_API_KEY` is absent.
10. Full deterministic CI remains green.

## Explicit non-goals

- No source-acquisition provider is promoted.
- No production Jev dependency is created.
- No automatic retry policy is introduced.
- No confidence threshold is invented.
- No Xignal payload is fabricated.
- No canonical write is authorized by this spec merely because Jev returns SUPPORTED.

## Promotion blockers

Before SHADOW:
- execute this corpus live against pinned Jev and preserve immutable result metadata;
- expand to a representative evidence-labeled germination corpus with hard negatives, partials, conflicts, temporal ambiguity, multilingual cases and adversarial source content;
- establish task-specific selective-risk/error-cost policy;
- implement/approve the source-acquisition boundary;
- implement canonical persistence adapters;
- prove provider/model swap behavior;
- decide production authorization separately.

## Current execution truth

At slice start, `TYPESAFE_API_KEY` is absent from process, User and Machine environment scopes. The locked `typesafe-sdk==0.7.1` dependency group is installable, but absence of credentials means no live Jev result may be claimed.
