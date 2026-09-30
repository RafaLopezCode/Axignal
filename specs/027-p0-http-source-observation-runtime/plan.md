# Implementation Plan

1. Define provider-neutral SourceRequest, SourceObservation, target rule and dispatch policy contracts.
2. Bind requests to exact policy fingerprints.
3. Implement fail-closed public target validation and DNS resolution.
4. Implement direct HTTP(S) transport pinned to validated addresses with hard response/time budgets.
5. Re-authorize every redirect.
6. Implement immutable content-addressed raw artifact storage.
7. Build a SourceObservation envelope retaining policy, instrument and network provenance.
8. Translate SourceObservation into GovernedObservation without semantic/truth authority.
9. Ingest it through Observation Memory and reuse the existing Brain planner.
10. Prove security, transport and E2E behavior with deterministic tests; attempt one harmless public smoke without making it a CI dependency.
