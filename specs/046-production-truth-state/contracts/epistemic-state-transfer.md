# Contract: EB-04 Epistemic-State Transfer

## Inputs

- Exact `EconomicClaimCandidate` grounded in a `TextRepresentation` and supporting span.
- Versioned application-owned policy keyed by exact `SourceAuthority` and predicate. No caller-supplied epistemic result.
- Existing reuse-rights authorization and currentness decision.
- Existing proposition-bound `EvidenceAdmission` request and decision.

No state supplied by subscriber input, semantic extractor output, evaluator output, or constructor default is authoritative.

## Required behavior

1. Resolve canonical state through the exact authority/predicate table; do not add a generic direct-observation boolean or extractor/caller-supplied epistemic label.
2. Apply existing source-authority and exact-proposition admission without broadening it.
3. Pass the resolved, explicit state to canonical FAXT materialization and assign the same state to the corresponding economic observation.
4. If support exists, require agreement on subject, predicate, value, evidence reference, observed time, state, and currentness.
5. Existing admitted `OFFICIAL_WEB` capability/product predicates map to `DECLARED`.
6. Existing admitted `REGISTRY` predicates `identity`, `legal_identity`, and `registration`, with exact evidence and identity/source-authority admission, map to `OBSERVED` for that registral proposition only.
7. Every other authority/predicate pair without a rule fails closed for canonical materialization; passing admission alone is insufficient for `OBSERVED`.
8. Preserve the noncanonical/absence path and do not assert `FALSE` or create an `UNKNOWN` FAXT.
9. Preserve representation surface and visibility certainty. An exact official-web declaration supported by `EXTRACTED_TEXT` may remain `DECLARED`; it does not prove human-visible rendering.
10. Do not change FAXTâ€™s global default, Organization profile admission, or subscriber projection policy.

## Rejection / abstention behavior

- Unsupported authority/predicate pair: reject a canonical request fail-closed before any `OBSERVED` fallback.
- Unsupported source authority under existing admission: existing `EvidenceAdmission` rejection remains authoritative.
- State mismatch between FAXT and `EconomicObservation`: reject construction/materialization.
- Attempt to create a FAXT with `UNKNOWN`: retain the existing domain rejection.
- User/provider/extractor attempts to force `OBSERVED`: there is no input field that grants this state; no canonical mutation occurs.

## Replay and determinism

The same exact candidate, evidence/representation, policy version, and temporal inputs produce the same epistemic result. The successful EB-04 result records `epistemic_policy_version`; the pipeline version is bumped for the behavior change. A policy-version change must be visible to replay/re-evaluation and must not silently rewrite historical evidence.
