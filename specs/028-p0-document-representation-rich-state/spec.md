# P0 — Document Representation and Rich Subject State

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER §§14, 56.1–56.5; Engineering Constitution; existing Observation Memory and source-acquisition contracts.

## Objective

Implement AXIGNAL's first deterministic REPRESENT stage over acquired HTML documents. The stage preserves exact source lineage, produces a reconstructible normalized document representation, compiles semantically useful rich state, and triggers dependency-aware answerability without granting evidence or truth authority.

## Required behavior

- Representation consumes an existing authorized SourceRequest + SourceObservation; it performs no network dispatch.
- The representation binds to the exact Observation Memory observation id and retains original source_type, source/content fingerprints and time.
- HTML visible body text is normalized deterministically; title, language, description, canonical URI and valid JSON-LD are preserved separately.
- Script/style/template/noscript/svg content does not enter visible text.
- Representation output is content-addressed and reconstructible from the immutable source artifact.
- RichSubjectState retains field-level observation/representation/source/time provenance.
- Representation changes produce deterministic StateChange objects so only affected typing dimensions are reconsidered.
- Missing semantic state remains NOT_ANSWERABLE/researchable; no missing value becomes FALSE.

## Authority boundaries

- REPRESENTATION != OBSERVATION MEMORY.
- REPRESENTATION != EVIDENCE.
- REPRESENTATION != CLAIM.
- REPRESENTATION != CANONICAL TRUTH.
- JSON-LD DECLARATION != VERIFIED BUSINESS FACT.
- VISIBLE TEXT != ECONOMIC INTERPRETATION.
- Rich state compilation may assemble available context but may not invent missing facts.

## P0 scope

This slice supports deterministic text/html and application/xhtml+xml representation only. It does not add semantic claim extraction, JEV, crawler/browser rendering, PDF parsing, EvidenceAdmission, FAXT/Relationship writes, production scheduling or deployment.