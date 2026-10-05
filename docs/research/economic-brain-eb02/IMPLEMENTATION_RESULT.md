# EB-02 — Identity & Representation Fidelity implementation result

Date: 2026-10-05. Branch: `codex/eb02-identity-representation`.
Base: `main@23a6453`. Scope authority: the explicit EB-02 implementation task,
MASTER §§5, 14, 15, 20, 23, 36, 54, 56, Constitution and accepted ADR-0049,
ADR-0072 and ADR-0079. Feature artifacts: `specs/039-eb02-identity-representation/`.

## Result

Deterministic identity resolution, representation support and canonical admission
now connect without treating a model proposal or identity receipt as truth.

Exact identity keys use Unicode NFC, casefold and whitespace normalization;
diacritics, non-Latin scripts and punctuation survive. Homonyms and casefold
collisions remain explicitly AMBIGUOUS. Verified identifiers are namespaced by
scheme and authority; values preserve case except the explicitly case-insensitive
LEI scheme. All supplied keys must be known and agree. No first match, approximate
name, subscriber preference or provider result selects an Organization.

Immutable governed alias/rebrand records retain actor, decision, evidence,
authority and half-open validity intervals. Resolution of history requires an
aware as-of time. Records never overwrite canonical names or Organization IDs.
The resolver's mention-binding bridge refuses unresolved/ambiguous identity and
retains relevant naming-decision/evidence references in the binding receipt.
Existing merge/split/reversal topology storage is unchanged.

HTML document representation is versioned `html-document/0.2` with normalization
`visible-text/0.2`. It verifies source-byte fingerprints and preserves both raw
body and raw observation artifact references. Hidden ancestry, script/style,
template/noscript/SVG, hidden/ARIA-hidden attributes, explicit invisible inline
styles, simple hidden stylesheet selectors, closed details/dialog and fallback
embedded content cannot supply visible text. Duplicate attributes follow the
first-attribute HTML rule. Unknown CSS/layout and malformed hidden ancestry fail
closed. Metadata and structured declarations remain separate surfaces.

`RepresentationSpan` binds half-open Unicode code-point offsets to a complete
immutable `TextRepresentation` fingerprint. Extraction accepts exact validated
provider offsets or derives offsets only for a unique exact excerpt. It rejects
invalid ranges, boolean offsets, mismatched excerpts, foreign representations,
explicit null spans and ambiguous repeated excerpts. Candidate identity includes
the span. Exact excerpt whitespace survives. Provider output remains a proposal.

New canonical claim admission requires `grounded-claim:v2`, the representation,
an exact support span and source/subject/type/time consistency. Non-literal
subject/object mentions require authentic governed identity receipts scoped to
the exact mention inside that support. Hand-built/copied/foreign receipts fail.
Admission independently enforces the existing predicate-specific source authority
and exact tuple. Representation, span and binding provenance enter admission and
ledger fingerprints. A binding or evidence-only decision cannot create a FAXT or
ObservedRelationship; the positive test creates a relationship only after exact
proposition admission and retains UNKNOWN currentness.

Rich-state visible text retains a support span; state fingerprints include it.
Economic observations carrying spans require their exact representation, source,
time and basis fingerprint. Cross-subject representations fail closed. Existing
epistemic state, currentness and validity checks remain independent and unchanged.

## Exit criteria evidence

`tests/contracts/test_eb02_identity_representation.py` contains 70 deterministic
adversarial cases. The fixtures are synthetic, offline and provider neutral.

| Exit criterion | Deterministic proof |
| --- | --- |
| 1. Homonyms never silently merge | Normalized homonyms, reversed candidate order, canonical/alias collisions; AMBIGUOUS and no selected candidate |
| 2. Rebrand/alias history preserves identity | Governed history, expiry boundary, as-of requirement, rejected ungoverned authority/evidence, canonical name unchanged |
| 3. Unicode normalization preserves distinctions | Composed/decomposed café, diacritic distinctions, Japanese/Chinese names, punctuation, case-sensitive identifiers and multiple verified keys |
| 4. Hidden text is not visible support | Hidden nested/void content, script/style/template, inline visibility, closed disclosures, unknown stylesheet/layout and malformed hidden tree |
| 5. Exact source support | Immutable source artifacts → document → Unicode offset → representation span → scoped identity binding → proposition admission → observed relationship |
| 6. Invalid support fails closed | Fabricated, misaligned, out-of-range, missing, unsupported-version and foreign spans; invalid provider offsets and replay rejection |
| 7. Ambiguity stays explicit | AMBIGUOUS/UNRESOLVED outputs and refusal to issue a binding for colliding identities |
| 8. Non-literal entity grounding is governed | Missing, forged, copied, wrong-entity, wrong-mention and foreign-representation receipts are rejected |
| 9. Provenance/time/currentness survive | Raw body/observation refs, versions, fingerprints, observation currentness dependency, UNKNOWN economic currentness, source/time mutation rejection |
| 10. Provider output has no authority | Candidates remain non-canonical, provider authority strings are rejected, binding alone/evidence-only admission cannot materialize observed truth |

## Exact files changed

Implementation:

- `application/economic_discovery/economic_state.py`
- `application/semantic_extraction/contracts.py`
- `application/semantic_extraction/runtime.py`
- `application/source_representation/contracts.py`
- `application/source_representation/runtime.py`
- `domain/evidence/admission.py`
- `domain/identity.py`
- `domain/identity_binding.py` (new)
- `domain/representation.py` (new)
- `pipeline/entity_resolution/resolver.py`
- `pipeline/normalization/text.py`
- `pipeline/source_representation/html_document.py`

Adversarial tests, explicit synthetic representation fixtures and compatibility:

- `tests/contracts/test_eb02_identity_representation.py` (new)
- `tests/support/grounding.py` (new; synthetic-only helper)
- `tests/contracts/test_evidence_admission.py`
- `tests/contracts/test_faxt_requires_admission.py`
- `tests/contracts/test_observed_vs_potential.py`
- `tests/contracts/test_organization_canonical.py`
- `tests/contracts/test_subscriber_projection.py`
- `tests/contracts/test_xeed_knowledge_binding.py`
- `tests/economic_discovery/test_first_vertical.py`
- `tests/economic_discovery/test_prime_execution.py`
- `tests/semantic_extraction/test_semantic_claim_candidates.py`
- `tests/subscriber_projection/test_evidence_narrative.py`
- `tests/subscriber_projection/test_explainable_xignal.py`
- `tests/support/hfx01_demo.py`
- `tests/support/hfx01_ux_lab.py`
- `tests/unit/test_normalization.py`
- `tests/xeed_germination/test_semantic_flow.py`
- `tests/xeed_germination/test_turboquant_germination_integration.py`

Governance and evidence:

- `specs/039-eb02-identity-representation/spec.md` (new)
- `specs/039-eb02-identity-representation/plan.md` (new)
- `specs/039-eb02-identity-representation/tasks.md` (new)
- `docs/research/economic-brain-eb02/IMPLEMENTATION_RESULT.md` (this file)

No MASTER, Constitution, ADR, gate, dependency/lockfile, EB-03 implementation or
EB-01 budget/deadline/lease/attention file changed. The pre-existing untracked
`CODEX_EB02_TASK.md` is preserved and is not part of the implementation commit.

## Validation actually run

All commands ran in this worktree using Python 3.12.11 and the frozen lockfile.
`UV_CACHE_DIR` was set to `%TEMP%/axignal-eb02-uv-cache`. Mypy cache and pytest
basetemps were placed outside the repository. No provider calls were required.

| Command/check | Result |
| --- | --- |
| `uv sync --frozen` | PASS after authorized dependency installation; initial default-cache access and sandbox network attempts failed, then resolved using temp cache and escalation |
| Final focused pytest across EB-02, entity resolution, normalization, admission, representation, extraction, ledger, Prime execution and legacy semantic flow | PASS: 136 tests, 2.25 seconds |
| `uv run ruff format --check .` | PASS: 860 files formatted |
| `uv run ruff check .` | PASS |
| `uv run mypy --cache-dir %TEMP%/axignal-eb02-mypy-cache` | PASS: 265 source files |
| `uv run pytest --basetemp %TEMP%/axignal-eb02-full-complete` | PASS: 1,175 tests, 78.79 seconds |
| `uv run architecture-guard --root .` | PASS, no violations |
| `uv run axignal-governance` | PASS: architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology |
| `git diff --check` | PASS; Git emits existing CRLF→LF normalization notices for migrated fixtures |
| Spec Kit setup-plan and check-prerequisites, with feature directory 039 | PASS; constitution check and scoped architecture review recorded in plan |
| `graphify --version`, `graphify update .` | Unavailable: executable not on PATH; graphify-out/graph.json also absent. No structural graph was updated |

Iteration failures were fixed without changing a gate: one expected exception
message; replay assertions pinned to 0.1; and a changed-time replay fixture that
needed an explicit new synthetic representation before exercising ledger conflict.
The preceding full run passed 1,173 tests in 79.13 seconds; final review added
two conservative CSS cases and verified the existing observed factory boundary.

## Accepted limitations and blockers

- Static HTML is not a browser/CSS engine. Only a bounded declarative visibility
  subset is accepted. External stylesheets, unsupported declarations/selectors,
  computed layout/visibility and malformed hidden ancestry return an error,
  preserving absence of support. Closed details summaries and other uncertain
  fallback surfaces may be conservatively omitted. No renderer, JS execution,
  pixel-visibility or full browser fidelity claim is made.
- Offsets are in normalized representation text, not raw HTML bytes. The exact
  text, versions, fingerprints and immutable raw/representation artifacts make
  those offsets independently verifiable. Structured JSON-LD is labelled as a
  declaration surface and never relabelled visible content or verified truth.
- Governed naming history is immutable input to the existing resolver; this
  slice adds no persistence infrastructure. Existing plain `aliases` remain the
  pre-governed static catalog contract of ADR-0049. New temporal alias/rebrand
  decisions use explicit governed history. Neither path edits canonical truth.
- Identity-binding and admission tokens have the existing Python language-level
  integrity posture. They do not claim hostile-process security. Provider result
  parsing has no binding issuance path; trusted identity governance supplies the
  closed authority, actor, evidence and decision inputs separately.
- `grounded-claim:v1` without verifiable representation support no longer
  authorizes new canonical materialization or factory replay. Historical records
  are not rewritten. Old callers must supply independently sourced v2 support
  and governed non-literal bindings. The fixture helper is synthetic-only and
  must never be used to upgrade real provider output or real historical evidence.
- Currentness remains an upstream observation dependency and existing economic
  temporal policy; a stable representation/binding never implies current truth.
  EB-03 source registry/rights/reuse and EB-06 temporal-memory work remain outside
  this slice. No product deployment or external end-to-end milestone is claimed.
- The two optional Brain audit files named in the task are absent at this base.
  Graphify tooling is unavailable; this is the only tooling blocker. All required
  deterministic gates run independently and remain unchanged.

## Convergence and delivery

Spec Kit intent inventory FR-001–006 / SC-001–002 and all ten task exit criteria
map to implementation and deterministic evidence above. Convergence found no
remaining buildable requirement in scope, so no additional task phase was needed.
All tasks and required deterministic gates are complete. Delivery is a commit
on the requested branch containing the implementation, tests and this report.
No merge, push to main or deployment is part of this delivery.
