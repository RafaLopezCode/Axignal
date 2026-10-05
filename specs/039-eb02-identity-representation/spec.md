# EB-02 — Identity & Representation Fidelity

Status: implementation authorized on codex/eb02-identity-representation.
Authority: MASTER §§5, 14, 15, 20, 23, 36, 54, 56; Constitution VI–X,
XVII–XVIII; ADR-0049, ADR-0072, ADR-0079; accepted specs 028/029/038;
Economic Brain Execution Roadmap 2026-10-05, EB-02.

## Requirements and acceptance

- FR-001: Exact Unicode NFC/case normalization preserves diacritics, scripts,
  punctuation and identity collisions. Names never merge Organizations. All
  supplied verified keys must agree; unknown keys never cause name fallback.
- FR-002: Alias/rebrand records retain governed authority, actor, evidence and
  temporal history. A rebrand never overwrites the canonical identity. Temporal
  aliases require explicit as-of context; homonyms remain AMBIGUOUS/UNRESOLVED.
- FR-003: HTML representation excludes script/style/template and hidden content
  including hidden ancestors and inline visibility rules. Unknown stylesheet
  visibility fails closed rather than claiming browser visibility.
- FR-004: Extracted support has exact half-open Unicode code-point offsets in
  an identified, fingerprinted representation surface. Invalid, mismatched,
  out-of-range and cross-representation spans fail closed. Duplicate occurrences
  require an explicit span rather than a convenient first match.
- FR-005: Canonical GroundedClaim requires verifiable representation support.
  Non-literal entity/object mentions require an authentic governed identity
  binding scoped to that mention and representation. Binding alone never grants
  truth: independent predicate-specific EvidenceAdmission remains required.
- FR-006: Source/artifact refs, observation time, representation/normalization
  versions, fingerprints and currentness dependencies survive extraction and
  admission digests. Provider outputs remain proposals, never identity authority.

SC-001: Deterministic adversarial tests prove every FR and the ten task exit
criteria, with an acquisition-artifact → representation → span → binding →
admission integration example and negative mutations.
SC-002: Existing deterministic gates pass without changing gates or doctrine.

## Clarifications

Offsets refer to normalized representation text, not raw HTML byte offsets.
Visible text and structured declarations are distinct surfaces. Static HTML is
not a browser renderer; unresolved CSS is explicitly unavailable for visible
support. Governed identity binding is a language-level integrity boundary like
EvidenceAdmission, not protection against hostile Python introspection.
Legacy grounding without a representation may be read as history but cannot
authorize a new canonical claim. Synthetic tests supply explicit text artifacts.

## Exclusions

No EB-03 registry/rights/robots/rate/retention/reuse policy, EB-01 budget/lease
changes, infrastructure, provider SDK, UI, production deployment, merge or push.
