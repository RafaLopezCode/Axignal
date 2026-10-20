# Convergence

Mode EXPLORE. Independent commercial presentation in the isolated lab; existing subscriber capabilities, evidence semantics and commercial price book retained. Current source `4b2a7fbc7937d01f81efa8820315b6755ab9f8dc`; integration through #355. Own feature specification renumbered 108 to preserve upstream 107.

Visual evidence: complete current old/new desktop/mobile comparison; discovery, relationships, reasoning, sources, temporal change, UNKNOWN, Observer, GSAP replay/reduced motion, pricing, newsletter and mobile menu. Eighteen responsive cases in six languages. Native anchor back-to-top reaches zero and restores H1 focus. Expanded newsletter consent contrast corrected after screenshot inspection. No Golden Master overwritten or declared accepted.

Validation: frontend 413 PASS, zero skipped; Python 2723 PASS and seven explicit Windows/optional-SDK skips (see verification.md); Ruff, mypy, architecture, i18n, production build and initial HTML verified. All eight governance checks PASS after evidence staging (architecture, deps, docs, graphify, hygiene, no-generated-data, spec, terminology). AST graph updated without API costs. No gate, CSP or epistemic invariant weakened.

Lighthouse: three serial cold mobile samples and one desktop. All raw samples retained; mobile selected by median LCP. No field INP or field CWV assertion. Mobile LCP retains margin against 2.5 seconds; this is explicitly reported, not called perfect.

Merged PR review includes #341–#355. Two inherited #347 limits and one inherited #351 future-tense extraction defect remain separately documented; the read-only synthetic landing does not call those paths.

Status: IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING. Draft PR #350 remains the review vehicle. No merge, public homepage replacement or production deployment authorized.
