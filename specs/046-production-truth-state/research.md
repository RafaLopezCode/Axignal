# Research: Production Truth-State Preservation for EB-04

**Date**: 2026-10-06
**Snapshot**: `016235736db002038f8063f3abd311ba5dca110c` (`codex/production-closure`)
**Scope**: Read-only source and contract inspection; no provider calls or production probes.

## Findings and decisions

### 1. Authority is not epistemic state

- **Evidence**: MASTER Â§15.3 says source hierarchy is predicate-specific and describes official web as support for *declared* products/capabilities; Â§15.4 defines distinct `OBSERVED`, `DECLARED`, `INFERRED`, `CORROBORATED`, `CONTRADICTED`, `STALE`, and `UNKNOWN` states.
- **Current implementation**: `SourceAuthority` and `_PREDICATE_AUTHORITY_POLICY` authorize a source for a predicate in `domain/evidence/admission.py`; this proves neither that a claim is true nor that it is observed.
- **Approved decision**: A deterministic, versioned policy in `application/economic_discovery` is keyed by exact `SourceAuthority` and predicate. Existing `OFFICIAL_WEB` capability/product predicates approved by EvidenceAdmission map to `DECLARED`. Existing `REGISTRY` identity/legal_identity/registration predicates map to `OBSERVED` for the exact registry proposition after exact evidence and identity/source-authority admission. Other combinations have no `OBSERVED` fallback and fail closed as canonical requests.

### 2. Defect is at the EB-04 transfer boundary

- **Evidence**: `EconomicFieldSpec` has source authority and exact predicate mention but no epistemic classification (`application/economic_discovery/first_vertical_e2e.py`, lines 85â€“103). `_canonical_support` calls `FAXT.create` without `epistemic_state` (lines 152â€“216); `FAXT.create` defaults to `OBSERVED` (`domain/faxt/model.py`, lines 71â€“80). `_materialize_source` starts as `DECLARED` but changes any canonical-authority field to `OBSERVED` (lines 279â€“313). The test asserts an official-web capability is `OBSERVED` (`tests/economic_discovery/test_first_vertical_e2e.py`, around lines 545â€“548).
- **Approved decision**: Correct only this EB-04 policy/transfer path. Pass the state explicitly into FAXT and EconomicObservation. Do not alter the global `FAXT.create` default; unrelated callers must keep current API behavior. Do not add caller/extractor state labels or a generic direct-observation boolean.

### 3. Support integrity already has useful guards

- **Evidence**: `EvidenceAdmission.admit_claim` enforces exact grounded evidence and predicate-authority policy (`domain/evidence/admission.py`). `EconomicObservation.__post_init__` requires observed/corroborated observations to have canonical support and checks state/currentness/value/time/evidence alignment when support exists (`application/economic_discovery/economic_state.py`, lines 35â€“115).
- **Decision**: Reuse these invariants. Do not relax source-authority, proposition binding, identity binding, admission tokens, or representation span checks.

### 4. Unknown and surface are separate axes

- **Evidence**: `FAXT.create` rejects `UNKNOWN` (`domain/faxt/model.py`); `EconomicObservation` can carry `UNKNOWN` without observed/corroborated canonical support (`application/economic_discovery/economic_state.py`). `TextRepresentation` carries an explicit `TextSurface`; source representation uses `EXTRACTED_TEXT` when visibility is unresolved (`domain/representation.py`, `application/source_representation/contracts.py`).
- **Approved decision**: Preserve the existing noncanonical absence/unknown path with no FAXT; do not synthesize `FALSE`. An exact official-web declaration can remain `DECLARED` when supported by extracted text, while `EXTRACTED_TEXT`/unresolved visibility remains explicit. That surface does not establish human-visible rendering or promote the capability to `OBSERVED`.

### 5. Keep Organization profile and subscriber presentation boundaries

- **Evidence**: ADR-0073 says `Organization.from_admitted_faxts` accepts `OBSERVED`/`CORROBORATED` FAXTs only and subscriber OBSERVED projection must not upgrade `DECLARED`/`INFERRED` (`docs/adr/ADR-0073-canonical-materialization-relationship-admission.md`). ADR-0072 keeps admission proposition-bound.
- **Decision**: This feature does not change Organization profile materialization or subscriber `OBSERVED` projection. Preserve an official-web declaration as a declaration in the EB-04 reasoning input and explainable basis; no claim is made that the Organization observed-profile API should consume it.
- **Approved architecture review**: Retaining an admitted `DECLARED` FAXT as an EB-04 reasoning input is compatible with the accepted profile boundary. `Organization.from_admitted_faxts` remains restricted to `OBSERVED`/`CORROBORATED`; subscriber OBSERVED projection remains unchanged.

## Alternatives considered

- **Remove `epistemic_state` from all FAXT defaults or globally default to `DECLARED`**: rejected; this is an EB-04 call-site/policy defect and a global change could silently alter unrelated callers.
- **Set every field to `DECLARED`**: rejected; it would erase genuinely observed facts and collapse epistemic distinctions.
- **Treat successful `EvidenceAdmission` or `SourceAuthority` as `OBSERVED`**: rejected; admission proves eligibility/proposition binding, not semantic truth status.
- **Map extracted-text visibility uncertainty directly to `UNKNOWN` for every claim**: deferred to the visibility/classification policy; observation surface and proposition state are different axes. It must never become `OBSERVED` solely from extraction.
- **Use model/extractor labels for epistemic state**: rejected; evaluators are non-authoritative and canonical conclusions are deterministic-policy governed.

## Remaining implementation verification

No product-semantics question remains open in this phase. Tests must prove the exact official-web DECLARED case with unresolved visibility, the registry OBSERVED proposition case, fail-closed behavior for unsupported authority/predicate pairs, and existing exact-evidence mismatch rejection. No evidence supports broadening the policy beyond those approved mappings.
