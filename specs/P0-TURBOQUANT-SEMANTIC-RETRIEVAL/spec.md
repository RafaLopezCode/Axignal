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

## Execution evidence — 2026-09-30

Implemented on the first germination slice:
- provider-neutral index now supports rebuild, upsert, remove, search and stats;
- deterministic structured filtering occurs after retrieval and before investigation;
- candidate canonical-organization deduplication and self/stale/locale/geography rejection are fail-closed;
- investigation findings must bind to the retrieved candidate subject;
- admitted evidence is appended before the canonical FAXT writer is invoked;
- a real TurboQuant adapter participates in the integration contract from AuthorizedXeed through EvidenceAdmission to FAXT write.

The deterministic AXIGNAL-shaped V0 corpus contains 576 candidate representations, 72 Xeed queries, 12 economic archetypes, six locales and six geographies at 384 dimensions. It is explicitly synthetic and has **no promotion authority**. Its purpose is to expose quantization loss and retrieval/filter behavior before spending money or authority on a live embedding/evidence corpus.

Latest V0 benchmark evidence is stored at `experiments/semantic_retrieval/results/axignal_corpus_latest.json`. The result must not be interpreted as production Germination Recall because relevance is synthetic and the vectors are deterministic facet representations, not production embeddings.

### Newly exposed blockers

Deep execution exposed four missing production authorities that were not visible at adapter level:
1. no production semantic encoder/provider contract is implemented;
2. no production candidate investigator/source-acquisition adapter exists;
3. no production canonical Evidence/FAXT persistence writer exists;
4. the concrete Xignal payload/provenance contract remains intentionally deferred, so this slice may admit FAXTs but MUST NOT fabricate a Xignal object.

Therefore the slice remains **SHADOW-INELIGIBLE** despite green adapter/flow tests. The next corpus must be evidence-labeled and use the selected production embedding path before any recall threshold can be approved.

### Defects exposed and repaired by deep integration

The integration pass also exposed pre-existing inconsistencies outside TurboQuant itself. They were repaired rather than bypassed: the Engineering Constitution and landing execution order still described the superseded Xignal-based pricing/attention model; EvidenceAdmission could admit evidence with missing identity/source metadata; FAXT creation accepted an empty subject/value; the TurboQuant port lacked the upsert/remove/stats operations required by this spec; and the HFX synthetic lab encoded an empty canonical FAXT value to exercise a presentation edge case. The lab fixture now preserves the presentation intent without constructing canonically invalid knowledge.
