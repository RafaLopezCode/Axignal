# ADR — TurboQuant as Derived Semantic Retrieval Infrastructure

**Status:** PROPOSED FOR VALIDATION  
**Date:** 2026-09-29  
**Authority:** AXIGNAL MASTER PRODUCT MODEL; Engineering Constitution

## Decision

AXIGNAL will evaluate and integrate TurboQuant behind a replaceable `SemanticIndex` port as **derived, non-canonical retrieval infrastructure**.

TurboQuant may accelerate:
1. Xeed germination candidate discovery;
2. reuse of already observed economic knowledge;
3. semantic demand clustering for governed public Knowledge acquisition;
4. geographic + locale-aware discovery when combined with deterministic filters;
5. DRI/GEO/AEO question-space and representation-gap candidate discovery.

TurboQuant MUST NOT become canonical knowledge, evidence authority, relationship authority, authorization authority, or publication authority.

## Non-negotiable invariants

- `SEMANTIC_REPRESENTATION != CANONICAL_KNOWLEDGE`
- `VECTOR_SIMILARITY != RELATIONSHIP`
- `NEAREST_NEIGHBOR != EVIDENCE`
- `RETRIEVED_CANDIDATE != OBSERVED_FACT`
- `KEYWORD != PAGE`
- `SEMANTIC_SIMILARITY != AUTHORIZATION`
- `CLAIM != WRITE`
- `OBSERVED != POTENTIAL`
- `UNKNOWN != FALSE`

The semantic index is disposable and reconstructable from authoritative sources. Deleting it MUST NOT delete canonical AXIGLAND knowledge.

## Placement

The domain owns only semantic meaning and invariants. It MUST NOT import TurboQuant or NumPy.

The application layer owns a provider-neutral retrieval port.

Concrete TurboQuant integration belongs outside the domain, behind that port. A future provider may replace TurboQuant without changing canonical domain semantics.

## Xeed germination contract

TurboQuant is allowed to answer only:

> Which already-known or externally discoverable candidates deserve investigation next?

It is not allowed to answer:

> What is true about this Xeed?

Pipeline:

```
Xeed
  -> identity resolution
  -> semantic probes
  -> SemanticIndex/TurboQuant candidate retrieval
  -> deterministic Python filters
  -> targeted investigation
  -> evidence interpretation / JEV where required
  -> EvidenceAdmission
  -> canonical AXIGLAND write
  -> admitted knowledge may seed another bounded retrieval expansion
```

Recursive germination MUST have deterministic budgets, cycle/duplicate suppression, canonical-ID normalization, temporal/currentness filtering, and explicit stopping criteria.

The optimization objective is high candidate recall. False positives may be filtered downstream; false negatives can hide economically relevant regions before investigation.

## Public Knowledge / SEO / GEO / AEO contract

TurboQuant may organize and retrieve **demand candidates**, not create indexable pages directly.

```
search / agent question / geographic demand
  -> semantic representation
  -> TurboQuant retrieval + clustering
  -> deterministic intent / locale / geography / duplication filters
  -> match against governed AXIGLAND knowledge
  -> evidence/currentness sufficiency gate
  -> distinct-information-value gate
  -> indexable-page candidate
  -> governed publication
```

Programmatic acquisition remains subject to the Public Landing / Knowledge contract. Thin pages, doorway pages, keyword permutations, fabricated evidence, and locale/geography pages without materially distinct information remain forbidden.

For geographic discovery, exact geography is structured metadata and a deterministic filter; it MUST NOT be inferred solely from vector proximity.

For GEO/AEO, agent-facing question representations are demand observations, not facts about the economy.

## Initial provider choice

The first validation target is the vector-search-oriented implementation:

- `Firmamento-Technologies/TurboQuant`
- evaluated commit: `2b6596093017419632abb03ae76e19bdcfb9a1e1`
- license reported by upstream: Apache-2.0
- upstream API includes brute-force `TurboQuantIndex` and `IVFTurboQuantIndex`

This is a validation target, not architectural authority. AXIGNAL MUST pin any adopted implementation to an exact reviewed version/commit and retain the provider abstraction.

## Accuracy policy

No bit width is canonized before AXIGNAL corpus benchmarks.

Initial benchmark candidates: FP32 baseline, 8-bit, 6-bit, 4-bit. 3-bit is excluded from initial production consideration for germination because candidate-loss risk dominates storage savings.

Promotion requires measuring at minimum:
- Recall@10 / @50 / @100 against exact FP32;
- **Germination Recall**: fraction of ultimately evidence-relevant candidates surviving retrieval;
- **Time-to-First-Useful-Xignal**;
- bytes/vector and total resident memory;
- index build/add latency;
- query p50/p95;
- candidate filtering cost;
- semantic drift across locales;
- geographic filter correctness;
- rebuild/recovery determinism.

No production germination path may depend exclusively on approximate retrieval until corpus evidence establishes an acceptable recall floor and a safe fallback.

## Publication safety

A semantic-demand hit cannot itself authorize a public page. Publication requires deterministic eligibility and governed source material. LLMs may render copy from governed inputs but may not manufacture material claims.

## Failure mode

If TurboQuant is unavailable, corrupted, or below the validated recall floor, AXIGNAL falls back to the configured exact/provider-neutral retrieval path. Canonical truth remains unaffected.

## Promotion gates

**EXPERIMENTAL -> SHADOW**
- adapter contract tests pass;
- deterministic reconstruction proven;
- no canonical writes from retrieval;
- AXIGNAL corpus benchmark exists.

**SHADOW -> ACTIVE CANDIDATE RETRIEVAL**
- Germination Recall threshold explicitly approved from measured corpus;
- fallback tested;
- latency/memory advantage demonstrated;
- locale/geography tests pass.

**ACTIVE -> DEFAULT**
- production telemetry confirms recall proxy, latency, resource use, and no epistemic-boundary violations.

TurboQuant is an optimization of where AXIGNAL looks, never of what AXIGNAL believes.
