# P0 — TurboQuant Semantic Retrieval Validation

## Goal

Adopt TurboQuant only as a replaceable derived semantic retrieval accelerator and prove whether it improves two AXIGNAL workloads without weakening epistemic authority:

1. Xeed germination.
2. Governed Knowledge acquisition across SEO, geographic discovery, GEO/AEO and supported locales.

## Workload A — Xeed germination

Compare exact FP32 retrieval with TurboQuant 8/6/4-bit on a representative AXIGNAL corpus.

A candidate is useful only when later deterministic investigation/evidence processing establishes material relevance. The primary metric is **Germination Recall**, not generic cosine fidelity.

Required outputs:
- candidate IDs only; never canonical writes;
- typed retrieval reason / query family;
- similarity as retrieval metadata, never epistemic confidence;
- canonical-ID deduplication;
- structured locale/geography/time filters;
- deterministic expansion budget and cycle prevention.

Measure:
- Germination Recall;
- Time-to-First-Useful-Xignal;
- Recall@10/@50/@100;
- p50/p95 retrieval latency;
- bytes/vector / resident memory;
- add/index/rebuild time;
- downstream Python-filter reduction ratio;
- JEV calls avoided versus baseline.

## Workload B — Knowledge demand

Represent search queries, agent questions and public information intents as a separate derived demand corpus.

TurboQuant may discover semantic clusters and match demand to governed AXIGLAND knowledge. It MUST NOT decide publication.

Required deterministic publication gates:
- distinct intent;
- distinct information value;
- locale is explicit;
- geography is explicit structured metadata when applicable;
- sufficient governed source material;
- currentness/provenance requirements;
- no doorway/thin/permutation page;
- canonical URL decision;
- no material claim sourced from semantic proximity.

Measure:
- demand-cluster compression;
- duplicate-intent reduction;
- relevant AXIGLAND match recall;
- locale cross-talk;
- geographic false-positive rate;
- percentage of candidates rejected by publication governance.

## Architecture

Define a provider-neutral application port with operations equivalent to:
- add/upsert derived representations;
- remove by representation ID;
- search with k and structured filter context;
- stats;
- rebuild from authoritative source.

Concrete TurboQuant code must live outside `domain/`.

The port returns candidates, never FAXTs, Relationships, INXIGHTs or PATHX.

## Provider validation

First provider under evaluation:
`Firmamento-Technologies/TurboQuant@2b6596093017419632abb03ae76e19bdcfb9a1e1`.

Do not rely on upstream benchmark claims for promotion. Reproduce relevant measurements on AXIGNAL-shaped embeddings.

## Initial policy

- Default experiment: 8-bit.
- Challenger: 6-bit.
- 4-bit: benchmark only until Germination Recall proves acceptable.
- 3-bit: not eligible for germination default in this slice.
- exact FP32 remains benchmark truth for retrieval recall.
- TurboQuant failure cannot block canonical reads/writes.

## Definition of done

This slice is not DONE because an adapter imports successfully.

DONE requires:
- architecture/contract tests;
- deterministic benchmark fixture;
- exact baseline;
- TurboQuant variants;
- machine-readable benchmark result;
- explicit promotion decision based on measured thresholds;
- no Architecture Guard/governance regression;
- CI green.

Production activation is a separate decision after shadow evidence.
