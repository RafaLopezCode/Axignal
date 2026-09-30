# P0 — Grounded Semantic Claim Candidates

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER §§14, 15.1, 56.1–56.8; Engineering Constitution; Document Representation runtime.

## Objective

Introduce the governed boundary by which a replaceable cognitive provider may propose economic semantic claims from a represented source without gaining authority over provenance, identity, evidence admission, or canonical truth.

## Required behavior

- AXIGNAL owns SemanticExtractionContract, allowed semantic targets, candidate budget and candidate identity.
- A semantic-extraction job is deterministically bound to the exact DocumentRepresentation and contract fingerprints.
- The provider receives represented content, not authority to mutate Observation Memory or AXIGLAND.
- Every accepted proposal requires a non-empty statement and an excerpt grounded in represented visible text or normalized structured data.
- Targets outside the declared contract fail closed.
- Candidate counts above the declared budget fail closed.
- Duplicate semantic candidates fail closed.
- Provider-supplied candidate identifiers have no authority; AXIGNAL derives candidate IDs deterministically.
- Provider identity/version and result fingerprint are preserved for replay and audit.

## Authority boundaries

- MODEL OUTPUT != EVIDENCE.
- ECONOMIC CLAIM CANDIDATE != FAXT.
- GROUNDED EXCERPT != TRUE INTERPRETATION.
- PROVIDER CONFIDENCE != TRUTH CONFIDENCE.
- CLAIM != WRITE.
- Candidate output cannot invoke EvidenceAdmission or canonical writers.

## P0 scope

This slice defines provider-neutral job construction and fail-closed result normalization. It does not add a live foundation-model provider, JEV evaluation, EvidenceAdmission, Xignal interpretation, scheduling, or production deployment.