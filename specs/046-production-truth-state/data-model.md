# Data Model: Production Truth-State Preservation for EB-04

This model describes semantic responsibilities; it does not authorize a new canonical store or schema.

## Entities and relationships

### Versioned economic epistemic policy

An application-owned deterministic table maps exact source authority and predicate to the epistemic state appropriate to that evidence proposition. It is not a label accepted from a caller or semantic extractor.

- **Key**: exact `SourceAuthority` and predicate.
- **Policy identity/version**: stable evidence that makes deterministic replay explainable.
- **Approved mapping 1**: existing admitted `OFFICIAL_WEB` capability/product predicates â†’ `DECLARED`.
- **Approved mapping 2**: existing admitted `REGISTRY` predicates `identity`, `legal_identity`, and `registration` â†’ `OBSERVED` of the exact registral proposition.
- **No rule**: every other authority/predicate pair has no observed fallback and fails closed for a canonical request.

Source authority remains the independent permission gate in `EvidenceAdmission`. These state mappings do not expand its allowlist.

### Economic observation

An admitted/considered economic input, already represented by `EconomicObservation`.

- `datum`: normalized value and exact observation/source/time/span references.
- `basis`: evidence identity, source type, rights basis and extraction/representation fingerprints.
- `epistemic_state`: state selected by policy.
- `currentness`: independent temporal status.
- `representation`: exact text representation and surface (`VISIBLE_TEXT`, `STRUCTURED_DATA`, or `EXTRACTED_TEXT`).
- `canonical_support`: optional FAXT. Required for `OBSERVED`/`CORROBORATED` by the current invariant; absent for `UNKNOWN`.

### Canonical FAXT support

Evidence-backed proposition created through proposition-bound `EvidenceAdmission`.

- Same subject/predicate/value, evidence identity/time, epistemic state, and currentness as the associated economic observation.
- Preserves `DECLARED` for an exact official-web capability/product proposition.
- Preserves `OBSERVED` for an exact admitted registry proposition in the approved identity predicate family; it does not assert an economic capability.
- Cannot carry `UNKNOWN` under the current `FAXT.create` contract.

### Evidence representation

Immutable exact source text and spans with explicit surface and provenance. Its surface/visibility is orthogonal to claim epistemic state. A retrieved extracted string does not prove a rendered page was visible to a human.

## State table

| Evidence condition | Economic observation | Canonical FAXT | Allowed interpretation |
|---|---|---|---|
| Official website literally states an Organization capability/product; exact predicate/source authority are admitted | `DECLARED` | `DECLARED` | The Organization declares the capability; not independent proof of operation |
| Exact registry evidence supports an admitted identity/legal_identity/registration proposition and identity/source-authority checks pass | `OBSERVED` | `OBSERVED` | The exact registral proposition was observed; this is not an economic capability observation |
| Independent corroboration threshold is not implemented or not met | Preserve known component state or `UNKNOWN`; never invent `CORROBORATED` | No corroborated support unless the explicit rule is met | Explain limitation/abstain |
| Other authority/predicate pair with no rule, or disallowed source authority | Existing noncanonical/absence path or rejected canonical request | None | Fail closed; no `OBSERVED` fallback |
| Evidence absent, ambiguous, or insufficient | Existing noncanonical/absence path | None | No false negative; preserve unknown/absence behavior |
| Exact official-web declaration is represented as extracted text with unresolved visibility | `DECLARED` | `DECLARED` if exact admission succeeds | Retain extracted-surface qualification; do not assert human-visible rendering |

## Invariants

1. `SourceAuthority` and `EpistemicState` are distinct.
2. Evidence admission is necessary for canonical FAXT but does not select its epistemic state.
3. If FAXT support exists, its state and currentness equal those on `EconomicObservation`.
4. `UNKNOWN` is neither false nor a canonical FAXT.
5. No subscriber/user/agency or evaluator supplies canonical state.
6. Representation surface, rights, provenance, exact span, observed time, and currentness remain inspectable.
7. Policy version is deterministic and exact authority/predicate pairs without rules cannot produce `OBSERVED`.
