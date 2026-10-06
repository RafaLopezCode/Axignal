# Clarification Record: Production Truth-State Preservation for EB-04

**Date:** 2026-10-06
**Feature:** [spec.md](spec.md)
**Status:** No critical user clarification required; root architecture review resolved the policy questions on 2026-10-06.

## Clarification pass

No critical ambiguity was raised to the user. The requested scope already fixes the target path (`EconomicFieldSpec` â†’ `EconomicObservation` / FAXT), the product authority (MASTER Â§Â§15.3â€“15.4), the forbidden change (do not alter the global `FAXT.create` default), and the required outcomes (preserve `DECLARED`, allow separately justified `OBSERVED`, preserve `UNKNOWN`).

## Decisions grounded in repository authority

- Source authority answers whether evidence may support a predicate; it does not determine whether the proposition is `DECLARED`, `OBSERVED`, or another epistemic state (MASTER Â§15.3; ADR-0072).
- Exact evidence admission is necessary for canonical materialization but does not itself imply `OBSERVED` (ADR-0072; Constitution VI and VIII).
- FAXT and `EconomicObservation` must agree on epistemic state and currentness; the economic-state contract already enforces this when canonical support is present.
- An unresolved representation surface remains explicit and must not be treated as a human-visible page (the extracted-text representation contract and MASTER Â§54).
- Unknown evidence must remain unknown, and `FAXT.create` cannot materialize `UNKNOWN` under its current contract.

## Architecture-review decisions (approved by root)

1. Implement a deterministic, versioned policy under `application/economic_discovery`, keyed by exact `SourceAuthority` and predicate. A helper in `first_vertical_e2e.py` is acceptable.
2. Existing `OFFICIAL_WEB` capability/product predicates accepted by `EvidenceAdmission` map to `DECLARED`.
3. Existing `REGISTRY` predicates `identity`, `legal_identity`, and `registration`, with exact evidence and identity/source-authority admission, map to `OBSERVED` for the exact registry proposition only. This does not assert an underlying economic capability.
4. Every other authority/predicate pair without a rule has no `OBSERVED` fallback; reject canonical materialization fail-closed. Do not add a generic direct-observation boolean or permit extractor/caller-selected epistemic labels.
5. For an exact official-web declaration represented as `EXTRACTED_TEXT` with unresolved visual visibility, retain `DECLARED` and preserve the visibility uncertainty. It is not evidence of human-visible rendering or an independently observed capability.
6. Preserve the noncanonical absence/unknown path. Pass the selected state explicitly to FAXT and EconomicObservation. Leave global FAXT defaults, EvidenceAdmission, Organization profile materialization, and subscriber projections intact.

Architecture review approved the distinction between canonical `DECLARED` FAXT support for EB-04 inputs and the `OBSERVED`/`CORROBORATED` restriction on `Organization.from_admitted_faxts` in ADR-0073. The restriction remains unchanged. Root confirmed the 1341-test baseline and authorized the bounded implementation.
