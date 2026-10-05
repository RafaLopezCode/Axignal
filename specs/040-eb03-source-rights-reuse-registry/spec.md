# EB-03 — Source Rights & Reuse Registry

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER → Constitution → ADRs → Economic Brain Execution Roadmap
**Roadmap slice:** EB-03

## Purpose

Consolidate acquisition and reuse authorization into one versioned source/instrument registry so AXIGNAL cannot acquire a payload under one policy and later reuse it under independently invented rights, scope or currentness metadata.

## Requirements

1. Authorization is metadata-first and occurs before DNS/payload.
2. Every registered source binds source type, instrument, bounded target space, permitted purposes, rights status, access status and reuse scope.
3. Registry metadata includes versioned currentness, retention, rate and robots policy references plus an explicit reuse reason.
4. A successful authorization emits one coherent bundle: SourceRequest, SourceDispatchPolicy, ObservationReuseAuthority, TemporalCurrentnessPolicy, rate policy and retention policy.
5. Rights UNKNOWN/PROHIBITED, inaccessible sources, wrong purpose, wrong instrument and required robots without explicit permission fail closed.
6. Source policy id/version/fingerprint survive sensor envelope and ingestion.
7. Observation reuse authority persists exact registry id/version and policy references.
8. Registry authority grants observation/reuse permission only. It grants no canonical truth or EvidenceAdmission authority.
9. Historical observations lacking new registry metadata remain readable but do not gain new permission implicitly.
10. EB-03 does not authorize crawling, authenticated scraping, anti-bot bypass, broad scheduler execution or legal conclusions.

## Exit criteria

- Metadata authorization precedes payload access.
- Each new governed observation carries policy/version/scope lineage.
- Reuse cannot be authorized when rights or applicable purpose are absent.
- Production FirstProof derives dispatch and reuse authority from the same registry entry.
- Deterministic adversarial tests and repository gates pass.
