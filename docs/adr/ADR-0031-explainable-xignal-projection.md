# ADR-0031 — Explainable Xignal Projection

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§4.4A, 7.3, 15, 19, 20, 26; ADR-0023, ADR-0025 through ADR-0030.

## Context

FR-04 proved that the governed Brain organs execute through one Prime composition root. AXIGNAL still lacked a concrete subscriber-safe Xignal payload and a deterministic explanation path from visible signal back to admitted support and observations.

## Decision

Introduce a concrete `domain.xignal.Xignal` payload and a subscriber projection owned by `application/subscriber_projection/xignal.py`.

A Xignal remains non-canonical by construction:

`XIGNAL != FAXT`

`XIGNAL != CANONICAL WRITE`

`XIGNAL != PROVIDER CONFIDENCE`

`XIGNAL != SALE PROBABILITY`

The projection separates the private `xeed_id` that receives the signal from the canonical `subject_id` being observed.

## Epistemic states

Subscriber-visible Xignal state is explicit:

- `OBSERVED` — requires already-admitted canonical support;
- `POTENTIAL` — explainable economic possibility, never displayed as observed;
- `UNKNOWN` — an explicit unresolved knowledge state with named unknowns.

`OBSERVED != POTENTIAL`

`UNKNOWN != FALSE`

## EvidenceAdmission boundary

An `OBSERVED` Xignal requires a canonical FAXT already created through `EvidenceAdmission`. The Explainable Basis must contain at least one supporting datum whose `evidence_ref` is one of that FAXT's admitted evidence references.

This requirement does not make the Xignal itself canonical. It prevents a model proposal, unadmitted claim or provider probability from being relabeled as an observed subscriber truth.

POTENTIAL and UNKNOWN Xignals may be emitted without canonical FAXT support, but their state remains explicit and their Explainable Basis remains mandatory.

## Subscriber-safe payload

The projection carries at minimum:

- why attention is warranted;
- OBSERVED / POTENTIAL / UNKNOWN state;
- semantic target and interpretation;
- currentness;
- source refs and source types;
- first and last observation time;
- contradictions;
- explicit unknowns;
- optional relationship and PATHX references;
- Explainable Basis reference;
- canonical support references when state is OBSERVED;
- policy version.

No provider confidence or sale probability is exposed as truth.

## Show how AXIGNAL knows

`XignalExplanationTrail` is the deterministic epistemic journey used by `Show how AXIGNAL knows`.

The trail order is stable:

1. Xignal;
2. canonical admitted support refs, sorted deterministically;
3. supporting Basis data;
4. contradictory Basis data;
5. contextual Basis data;
6. explicit unknowns.

Basis data are ordered by contribution, observation time and stable datum id. Each step preserves source reference/type and observation time when applicable.

## Basis evidence binding

`BasisDatum` gains an optional `evidence_ref`. Existing non-canonical explainability use cases do not require it. An OBSERVED Xignal does.

## Non-goals

FR-05 does not admit new FAXTs, relationships or PATHX. It does not infer sale probability, choose business actions or create canonical state. It also does not yet wire the Xignal into the complete AXIGLAND visual projection; later roadmap slices own that UX integration.

## Consequences

AXIGNAL now has a real subscriber-safe signal object that can explain why it exists and distinguish observed fact-supported attention from potential opportunity and unresolved uncertainty without weakening EvidenceAdmission.
