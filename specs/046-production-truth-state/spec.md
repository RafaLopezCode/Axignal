# Feature Specification: Production Truth-State Preservation for EB-04

**Feature Branch**: `codex/production-closure`

**Created**: 2026-10-06

**Status**: Implemented, reviewed and locally converged on 2026-10-06; full deterministic gates passed. See `docs/audits/production-readiness-2026-10-06/closure-verification.md`. No deployment claim.

**Input**: Close audit finding BRAIN-01 / TASK-07 by preserving the epistemic meaning of economic claims as they move from source evidence into EB-04 economic observations and canonical support.

## User Scenarios & Testing

### User Story 1 â€” Understand what an Organization declares (Priority: P1)

As a subscriber reviewing an Organizationâ€™s capability evidence, I need a statement from its official website to remain a declaration by that Organization, so I can distinguish its published claims from independently observed economic facts.

**Why this priority**: The first vertical currently materializes official-site capability claims as `OBSERVED` because FAXT creation inherits a default. This changes what the evidence means and undermines the trust contract of every downstream output.

**Independent Test**: Run the EB-04 materialization path over an exact, admitted official-site capability statement and inspect both its `EconomicObservation` and `FAXT` support.

**Acceptance Scenarios**:

1. **Given** an exact capability claim extracted from an Organizationâ€™s official website, **When** EB-04 admits and materializes it, **Then** both the economic observation and its FAXT support carry `DECLARED`.
2. **Given** that the claim is admitted and has exact source support, **When** a reviewer opens its evidence basis, **Then** the exact source, representation surface, span, time, currentness, and rights basis remain reachable without presenting the declaration as an independently observed fact.

### User Story 2 â€” Preserve a genuinely observed fact (Priority: P1)

As a subscriber, I need a fact supported by a governed observation rule to retain `OBSERVED`, so that correcting the declaration bug does not erase valid observations or collapse every state to `DECLARED`.

**Why this priority**: AXIGNAL must retain distinctions between declarations and observations in both directions; a blanket downgrade would be as semantically wrong as the current blanket promotion.

**Independent Test**: Exercise a field policy that explicitly qualifies an admitted claim as an observed fact and verify state equality between the economic observation and canonical support.

**Acceptance Scenarios**:

1. **Given** a predicate-specific policy and evidence class that authorize an observed fact, **When** the exact evidence is admitted, **Then** the economic observation and its FAXT support both carry `OBSERVED`.
2. **Given** evidence that is merely a sourceâ€™s declaration, **When** the observed-fact path is attempted without a qualifying policy, **Then** it is rejected or remains non-observed; source authority or successful admission alone cannot promote it.

### User Story 3 â€” Keep uncertainty explicit (Priority: P1)

As a subscriber, I need missing or insufficient evidence to remain unknown, so absence of a qualifying claim is not reported as proof that the Organization lacks a capability.

**Why this priority**: The product doctrine prohibits turning `UNKNOWN` into `FALSE`; this feature must not replace one epistemic error with another.

**Independent Test**: Exercise a missing/ambiguous/unsupported claim and inspect downstream state, canonical materialization, and output semantics.

**Acceptance Scenarios**:

1. **Given** no qualifying evidence or an unresolved epistemic policy, **When** EB-04 evaluates the field, **Then** the field remains `UNKNOWN` or absent-as-unknown and no false claim or `UNKNOWN` FAXT is created.
2. **Given** a representation whose visible surface is unresolved, **When** its extracted text is retained for analysis, **Then** the representation remains marked as extracted/visibility-unresolved and does not gain `OBSERVED` status from that fact.

## Edge Cases

- Exact admission succeeds but no epistemic policy matches the predicate, claim class, and source authority: fail closed for canonical materialization or preserve the state as unknown; never fall back to `OBSERVED`.
- A declaration is present in extracted text while visual visibility is unresolved: preserve exact support and surface metadata, but do not claim that a human-visible page or underlying business fact was observed.
- A policy marks a claim observed while its supporting authority is attention-only or unauthorized for the predicate: evidence admission still rejects it.
- An `EconomicObservation` and its `FAXT` disagree on epistemic state or currentness: reject the inconsistent pair.
- Independent corroboration is not established by repeated extraction, duplicate sources, or a model verdict; this feature does not invent corroboration.
- Existing callers that rely on the global `FAXT.create` default must not change behavior as a side effect of this feature.

## Requirements

### Functional Requirements

- **FR-001**: System MUST resolve canonical epistemic state through a deterministic, versioned application policy keyed by the exact `SourceAuthority` and predicate; an extractor, evaluator, or caller MUST NOT supply an arbitrary epistemic label.
- **FR-002**: System MUST preserve the policy-resolved state in both `EconomicObservation` and any canonical `FAXT` support.
- **FR-003**: System MUST treat source authority as permission to support a predicate, not as a universal epistemic state.
- **FR-004**: An admitted `OFFICIAL_WEB` capability/product predicate MUST be classified as `DECLARED`, including when exact source support uses `EXTRACTED_TEXT` with unresolved visual visibility.
- **FR-005**: An admitted `REGISTRY` predicate in the existing `identity`, `legal_identity`, or `registration` family MUST be classified as `OBSERVED` only for the exact proposition present in the admitted registry evidence. This status means the registry proposition was observed; it does not establish an economic capability or separate underlying fact.
- **FR-006**: Any canonical authority/predicate pair without an explicit policy rule MUST fail closed; it MUST NOT fall back to `OBSERVED`.
- **FR-007**: System MUST preserve `UNKNOWN` when evidence is absent or insufficient; it MUST NOT turn absence, unresolved visibility, or admission failure into `FALSE` or `OBSERVED`.
- **FR-008**: System MUST NOT create a canonical `FAXT` with `UNKNOWN`; an unknown economic observation MUST have no canonical support under the current domain contract.
- **FR-009**: System MUST preserve exact evidence identity, proposition, representation surface, span, observation time, currentness, and reuse-rights provenance through state transfer.
- **FR-010**: System MUST keep representation surface/visibility and epistemic state as distinct dimensions. `EXTRACTED_TEXT` or unresolved visibility MUST NOT be represented as visible-page confirmation.
- **FR-011**: System MUST retain the existing `EvidenceAdmission` source-authority, proposition-binding, identity-grounding, and exact-support checks.
- **FR-012**: This feature MUST NOT change the global default of `FAXT.create`, broaden source-authority policy, modify `Organization.from_admitted_faxts`, or promote declarations into subscriber `OBSERVED` projections.
- **FR-013**: The noncanonical/absence path MUST remain noncanonical and preserve current unknown/absence behavior; no `UNKNOWN` FAXT is introduced.
- **FR-014**: The feature MUST preserve deterministic behavior and remain provider-neutral.

### Key Entities

- **Economic field policy**: Governed rule for interpreting one field/predicate from a specified evidence class and source authority; establishes the allowed epistemic classification or explicit unknown behavior.
- **Economic observation**: Evidence-bound input to rich economic state, with its own epistemic state, currentness, rights basis, representation, and optional canonical support.
- **FAXT**: Canonical evidence-backed proposition whose epistemic state and currentness must match the economic observation that references it.
- **Evidence representation**: Exact source text and span, including the representation surface (visible, structured, or extracted) and the certainty of visual visibility.
- **Epistemic classification**: `DECLARED`, `OBSERVED`, `CORROBORATED`, `INFERRED`, `CONTRADICTED`, `STALE`, or `UNKNOWN`; this feature does not conflate it with source authority or currentness.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The official-web capability regression produces `DECLARED` on both `EconomicObservation` and FAXT support, with exact evidence linkage.
- **SC-002**: An exact registry `identity`, `legal_identity`, or `registration` proposition produces `OBSERVED` on both objects; no test depends on FAXTâ€™s default argument.
- **SC-003**: Missing, unsupported, ambiguous, or visibility-unresolved evidence cannot produce an `OBSERVED` claim or a `FALSE` negative; `UNKNOWN` remains explicit where a state is represented.
- **SC-004**: Tests prove mismatched epistemic state/currentness between an economic observation and its FAXT support is rejected.
- **SC-005**: Existing proposition-bound admission, source-authority, exact-span, and attention-only rejection contracts continue to pass without policy or gate weakening.
- **SC-006**: The global FAXT default and unrelated FAXT callers remain unchanged.

## Assumptions

- The feature is a bounded correction to EB-04 truth-state transfer, not a redesign of `EvidenceAdmission` or the global epistemic model.
- The versioned application policy is keyed by exact `SourceAuthority` and predicate, and does not accept a generic `direct_observation` boolean or an extractor/caller-supplied epistemic state.
- `OFFICIAL_WEB` predicates admitted by the existing capability/product policy map to `DECLARED`; `REGISTRY` predicates `identity`, `legal_identity`, and `registration` map to `OBSERVED` for the exact registry proposition. Other authority/predicate pairs have no observed fallback and fail closed as canonical requests.
- Official-web capability text is evidence that the Organization declares a capability; it is not by itself proof that the capability has been independently observed in operation. Unresolved visual visibility remains explicit and qualifies the representation, not the truth state.
- `UNKNOWN` may be represented in `EconomicObservation` but cannot be materialized as a FAXT under the current domain contract.
- `Organization.from_admitted_faxts` retains its accepted `OBSERVED`/`CORROBORATED` profile boundary under ADR-0073; this feature does not change that policy.

## Out of Scope

- Changing FAXTâ€™s global default, canonical admission rules, predicate/source authority table, Organization materialization, or subscriber projection policy.
- Implementing new source integrations, corroboration pipelines, source visibility resolution, or provider-based semantic judgments.
- Adding new database schemas, persistence, deployment, APIs, UI, or production claims.
- Changing files outside `application/economic_discovery/first_vertical_e2e.py` and `tests/economic_discovery/test_first_vertical_e2e*.py` during bounded implementation.
