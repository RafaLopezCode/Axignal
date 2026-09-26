# Feature Specification: Close Claim Evidence Answer Space

**Status:** Converged; additive experimental repair for CTO review.
**Authority:** MASTER Product Model, Constitution, ADR-0011; no production behavior authorized.
**Objective:** Close the direct-contradiction gap in `CLAIM_EVIDENCE_SUPPORT` while preserving V-next.1 byte-for-byte and keeping P0-JEV-04 paused.

## User Scenarios & Testing

### Story 1 — Interpret a supplied claim/evidence set without losing contradiction

As an experimental evaluator, I need the registered answer space to distinguish evidence that directly refutes a claim from evidence sources that conflict with each other, so that deterministic offline records preserve the intended epistemic state.

**Acceptance scenarios**

1. Given complete relevant evidence supporting every material claim assertion, the V-next.2 contract makes `SUPPORTED` eligible.
2. Given evidence supporting a material subset without refuting another assertion, it makes `PARTIAL` eligible.
3. Given relevant coherent evidence directly refuting a material assertion required by the claim, it makes `CONTRADICTED` representable.
4. Given relevant neutral evidence that neither supports nor refutes the claim, `NOT_SUPPORTED` remains distinct.
5. Given supplied passages but no relevant passage, `NO_EVIDENCE` remains distinct; zero passages fail the pre-provider information gate and cannot yield a judgment.
6. Given materially incompatible relevant evidence assertions about the same scope and time, `CONFLICTING` remains distinct from `CONTRADICTED`.
7. Given relevant information whose meaning, scope, or temporal referent prevents an unambiguous classification, `UNRESOLVED` remains available.

### Story 2 — Replay historical V-next.1 under its original semantics

As a maintainer, I need historical V-next.1 question identity, fingerprint, answer space, and grammar replay to remain unchanged when V-next.2 is added.

**Acceptance scenarios**

1. The V-next.1 grammar validates under the existing replay validator and still contains the same 12 questions.
2. The V-next.1 question fingerprint and six-option answer space remain unchanged.
3. Each version's provider binding rejects the other version's question and semantic drift fails closed.

## Functional Requirements

- **FR-001:** The V-next.1 grammar and registered question semantics remain unchanged.
- **FR-002:** A separately identified V-next.2 `CLAIM_EVIDENCE_SUPPORT` contract includes `CONTRADICTED` with a definition distinct from `CONFLICTING`.
- **FR-003:** V-next.2 declarations define mutually exclusive class meanings and explicit precedence for compound cases.
- **FR-004:** A minimum-one supplied evidence passage remains a structural answerability requirement. Relevance is not inferred by that gate.
- **FR-005:** `NO_EVIDENCE` means supplied evidence exists but no passage is relevant; zero passages remain `NOT_ANSWERABLE` before provider eligibility.
- **FR-006:** Provider question binding is version-exact and fingerprint-bound for both versions.
- **FR-007:** The repair adds deterministic contract tests only; it performs no Jev, OpenAI, DeepSeek, or other external model calls and accesses no TypeSafe key.
- **FR-008:** P0-JEV-04 remains paused, and the corpus assessment makes no claim that all six classes are present or that the experiment is eligible.

## Key Entities

- **Question definition:** Provider-visible semantics identified by question ID and question version.
- **DecisionContract:** AXIGNAL-owned binding among family, question version, state contract, primitive, answer space, fingerprint, and authority boundary.
- **Supplied evidence passage:** Non-empty semantic content plus provenance; its presence does not establish relevance or truth.
- **Historical replay:** Deterministic interpretation under the original V-next.1 definition and fingerprint.

## Assumptions

- V-next.2 can reuse the existing `claim-evidence.vNext.1` state shape because the repair adds an epistemic answer class, not new input fields.
- A new question ID avoids silently changing the existing registry identity and permits both versions to remain registered.
- This experimental contract provides no evidence admission, truth adjudication, production evaluator, or live experiment authorization.

## Out of Scope

Production inference, runtime/provider changes, executing P0-JEV-04, modifying the V-next.1 grammar, generating or adjudicating gold labels, creating an experimental corpus, broad V0.3 architecture work, or changing the P0-JEV-04 family.

## Success Criteria

- **SC-001:** One direct-contradiction case has exactly one eligible V-next.2 label, `CONTRADICTED`, and `CONFLICTING` is defined only for evidence-source disagreement.
- **SC-002:** All seven required conceptual states map to distinct V-next.2 labels, with empty evidence rejected before any judgment.
- **SC-003:** V-next.1 fingerprint, answer space, and 12-question grammar replay are unchanged.
- **SC-004:** Cross-version question binding and semantic drift are rejected deterministically.
- **SC-005:** The complete offline test and repository quality-gate results are recorded without any external model/provider call.

## Clarifications

- C-001: The literal no-passage case is an answerability failure, not `NO_EVIDENCE`; the answer-space label applies when passages are supplied but all are irrelevant.
- C-002: Where supplied relevant sources materially disagree about the same claim scope and time, classify `CONFLICTING` before evaluating a coherent direct contradiction.
- C-003: Where the evidence is coherent but directly refutes any material assertion required for the claim to be true, classify `CONTRADICTED`; this takes precedence over partial support in compound claims.

## Specification Quality Checklist

- [x] Scope, scenarios, requirements, edge conditions, and measurable criteria are explicit.
- [x] No clarification markers remain; all fixed semantics are captured above.
- [x] Production, provider, live experiment, and corpus-generation work is explicitly excluded.
- [x] MASTER/Constitution authority boundaries remain intact.
