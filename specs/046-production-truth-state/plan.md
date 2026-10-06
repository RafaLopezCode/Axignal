# Implementation Plan: Production Truth-State Preservation for EB-04

**Branch**: `codex/production-closure` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification in `specs/046-production-truth-state/spec.md`; audit finding BRAIN-01 / TASK-07.

**Plan state**: Root architecture review approved 2026-10-06. Root confirmed baseline `1341 passed`; tasks and bounded implementation are authorized.

## Summary

Preserve the epistemic meaning selected by a deterministic, governed EB-04 source-authority/predicate policy across canonical support and economic input state. Official-web capability/product claims remain `DECLARED`; exact admitted registry identity propositions are `OBSERVED` as registry propositions only; every other unruled pair fails closed. The change is scoped to the EB-04 materialization boundary and does not change `FAXT.create` defaults, evidence admission, Organization profile rules, or subscriber projections.

## Technical Context

**Language/Version**: Python 3.11+ (repository runtime; Python 3.12.11 in the available local venv)
**Primary Dependencies**: Existing AXIGNAL domain/application contracts; no new runtime dependency
**Storage**: None; no persistence/schema changes in scope
**Testing**: Focused pytest contracts for EB-04, economic state consistency, evidence admission, and representation surface
**Target Platform**: Existing deterministic Python application layer; no deployment work
**Project Type**: Layered Python application / domain model
**Performance Goals**: No measurable runtime-cost increase beyond deterministic classification; no new network/provider calls
**Constraints**: Preserve authority boundaries, exact evidence support, currentness, rights basis, and representation visibility. Unknown policy must fail closed, not default to observed.
**Scale/Scope**: One EB-04 field materialization path; no portfolio or production integration scope.

## Constitution Check

- **Epistemic neutrality / CLAIM â‰  WRITE**: Pass. EvidenceAdmission remains mandatory and unchanged; admission does not confer `OBSERVED` status (Constitution IV, VI, VIII; MASTER Â§Â§15.3â€“15.4).
- **Unknown preservation**: Pass. Unsupported or absent evidence stays unknown/absent-as-unknown; no false negative or FAXT with `UNKNOWN` (Constitution VIII).
- **One AXIGLAND / no tenant-owned truth**: Pass. No new canonical store or per-tenant truth is introduced (Constitution I, XVII).
- **Provider neutrality / deterministic truth mechanics**: Pass. Classification belongs to deterministic governed policy; evaluators and extractors cannot set canonical state (Constitution IX, X).
- **Reuse provenance/currentness**: Pass. Policy must preserve evidence, rights, state and currentness together (Constitution XVII).
- **Representation truth**: Pass. Representation surface/visibility is retained as its own axis; no extracted or unresolved surface is silently called human-visible (MASTER Â§54; Constitution XVIII).
- **No global default or policy weakening**: Pass. No change to `FAXT.create` global default, predicate-authority admission, architecture guard, or required gates.
- **Architecture decision reviewed and approved**: The current ADR-0073 permits Organization profile materialization only from `OBSERVED`/`CORROBORATED` FAXTs, while this feature preserves `DECLARED` canonical support for the EB-04 reasoning input. Root approved this distinction; the profile/projection boundary remains unchanged.

## Proposed Design

### Phase 0 â€” Research (complete)

Source-of-truth contracts, approved authority/predicate mappings, and boundaries are in [research.md](research.md). No vendor research or external provider is needed.

### Phase 1 â€” Data and behavioral contracts

- Keep evidence authority, epistemic state, currentness, representation surface, and visibility confidence separate.
- Define the transfer invariant: if an `EconomicObservation` has canonical support, `state`, `currentness`, field/predicate, value, observation time, and evidence reference agree with the exact FAXT.
- Define a deterministic, versioned application policy keyed by exact `(SourceAuthority, predicate)`. Existing admitted `OFFICIAL_WEB` capability/product predicates map to `DECLARED`. Existing admitted `REGISTRY` predicates `identity`, `legal_identity`, and `registration` map to `OBSERVED` for the exact proposition in the registry evidence.
- Every other authority/predicate pair without a policy rule has no `OBSERVED` fallback; canonical materialization fails closed. Do not add a generic direct-observation boolean or extractor/caller-supplied epistemic label.
- `UNKNOWN` is an economic input classification only and has no FAXT under the existing domain invariant.
- Preserve `TextSurface` and the exact span. An exact official-web declaration remains `DECLARED` when its surface is `EXTRACTED_TEXT`; unresolved visibility remains explicit and does not prove human-visible rendering.

Behavior contract: [contracts/epistemic-state-transfer.md](contracts/epistemic-state-transfer.md).
Conceptual model: [data-model.md](data-model.md).
Focused validation guide: [quickstart.md](quickstart.md).

### Approved source/test touchpoints

- `application/economic_discovery/first_vertical_e2e.py`: `EconomicFieldSpec`, `_canonical_support`, and `_materialize_source` are the scoped policy-transfer points.
- `application/economic_discovery/economic_state.py`: existing `EconomicObservation` consistency rule should remain the fail-closed invariant.
- `domain/faxt/model.py`: preserve its global default and UNKNOWN rejection; call-site must explicitly pass the governed state.
- `tests/economic_discovery/test_first_vertical_e2e.py`: replace the incorrect official-web capability assertion; add the declaration-with-unresolved-visibility and exact admitted registry-proposition cases.
- `tests/economic_discovery/test_first_vertical_e2e_adversarial.py`: prove unsupported authority/predicate pairs fail closed and existing evidence/identity mismatches remain rejected.
- Existing evidence-admission, FAXT, and representation contracts are verification targets only; this bounded task does not edit outside the authorized test glob.

## Project Structure

### Documentation (this feature)

```text
specs/046-production-truth-state/
â”œâ”€â”€ spec.md
â”œâ”€â”€ clarify.md
â”œâ”€â”€ plan.md
â”œâ”€â”€ research.md
â”œâ”€â”€ data-model.md
â”œâ”€â”€ quickstart.md
â”œâ”€â”€ tasks.md
â”œâ”€â”€ contracts/epistemic-state-transfer.md
â””â”€â”€ checklists/requirements.md
```

`tasks.md` records the approved implementation sequence.

### Source Code (repository root)

```text
application/economic_discovery/first_vertical_e2e.py
application/economic_discovery/economic_state.py (invariant review only)
tests/economic_discovery/test_first_vertical_e2e.py
tests/economic_discovery/test_first_vertical_e2e_adversarial.py
tests/contracts/test_evidence_admission.py
tests/source_representation/test_document_representation.py
```

**Structure Decision**: Reuse the existing application/domain layers and tests; no package, persistence layer, provider, API, or UI is proposed.

## Verification Plan

Run the red/green discriminative cases in `quickstart.md`, then the focused economic/admission regression set. Root owns full repository gates and final convergence. Root confirmed the pre-implementation baseline at 1341 passing tests and eight governance checks.

## Complexity Tracking

No constitution violations or new architectural components are proposed.
