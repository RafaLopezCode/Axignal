# Architecture Review: P0-DRI-00 Digital Representation Intelligence

**Outcome:** APPROVED AS DOCUMENTATION/DOCTRINE ONLY\
**Date:** 2026-09-26\
**Authority:** MASTER §§5, 14, 20, 22, 23, 46, 53 and 54; Constitution;
ADR-0001–0015.

## Findings

AXIGNAL already separates public evidence discovery, normalization, evidence
admission, canonical FAXT/relationships, AXIGLAND, and derived projections.
Its provider boundary is replaceable and subscriber/private context is
separately governed. Digital representation and public experience fit as
observation families feeding those existing boundaries, not as authority or a
new execution product.

Surface outputs and reviews have distinct observation conditions and sources.
Search results depend on query and geography; generative product UI differs
from an API; public conversation and review populations are selected samples;
private first-party analytics may be channel-private. Source verification,
ratings and claims cannot be promoted directly to AXIGNAL truth.

## Decision and architecture boundary

Adopt four DRI perceptive families: search, generative, social/public
conversation and public reputation/experience. Public Experience Intelligence
is a capability within DRI. Keep instrument/version, conditions, time, sample,
uncertainty, rights, source lineage, subject resolution and currentness
conceptually explicit. `ReviewObservation`, `ExperienceSignal`,
`ReputationState`, `ReputationChange`, `ReputationGap` and `RepresentationGap`
are semantic terms only.

The future data path is conceptual:

```text
AUTHORIZED SOURCE OBSERVATION
    ↓ identity / rights / channel / source lineage
OBSERVATION AND INSTRUMENT CONTRACTS
    ↓ deterministic normalization / entity resolution / deduplication
STRUCTURED STATE AND ANSWERABILITY
    ↓ bounded replaceable classification where required
DETERMINISTIC COMPOSITION / METRIC
    ↓ source-aware projection and explanation trace
SUBSCRIBER / AXENT
```

Evidence admission remains independent. Reviews can support that a claim was
observed, not that its underlying event is FAXT. Evaluators cannot produce an
authoritative score. EOI can direct which DRI questions merit observation;
experience signals may trigger AXENT research, but reviews alone do not create
DemandSignal or opportunity. Private first-party state does not cross into
public AXIGLAND or other tenants.

Any future aggregate is deterministic, versioned, traceable, decomposable,
sample/coverage/uncertainty/currentness-aware and withheld when evidence is
insufficient or sources/methods are incompatible. Cross-platform values are
not naively averaged. Source removal affects currentness; history is retained
only as rights permit. Public observations are reusable only with authority,
rights, subject resolution and duplicate controls.

## Preserved invariants

One AXIGLAND; UNKNOWN is not FALSE; inference is not observation; FAXT is not
INXIGHT; claim is not write; subscriber attention does not set conclusions;
private state remains scoped; providers are replaceable; no CRM/workflow or
reputation repair drift.

## Risks and controls

Surface/population bias, classification drift, rights, retention, privacy,
defamatory collapse and duplicated reviews are material risks. The doctrine
requires explicit source/method/time/sample provenance, separate observation
and derivation, currentness/deletion, personal-data minimization and descriptive
language. An anomaly is not fraud. Product/location experience does not
generalize to the whole company without a contract.

## Scope decision

No runtime class, answer space, provider, source adapter, crawler, scraper,
schema, migration, job, queue, API, production score, subscriber UI, experiment
or deployment is approved. The next slice is P0-DRI-01 Digital Observation
Contracts & Sensor Economics; it should cover ReviewObservation,
ExperienceSignal, classification and metric-composition contracts,
cross-source comparability, source deletion/currentness, UGC rights/retention
and reputation sensor economics. It is not started here.
