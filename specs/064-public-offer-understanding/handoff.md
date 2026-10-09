# CTO handoff — Bidirectional public offer understanding

The missing second direction was independent understanding of the organization's public offering, rather than economic classification readiness. This slice adds a conditioned reading of offer, audience and outcome to the existing subscriber reading. A cited strength and a conditional clarification proposal have equally inspectable evidence; acquisition and instrument failures withhold company criticism. No economic fact is admitted from a model judgment.

## Delivery state

| Stage | Actual state |
| --- | --- |
| Implemented | Application measurement, purpose-specific rights, bounded acquisition, private persistence/history, temporal comparison, AXENT evidence retrieval and subscriber UI in six locales. |
| Tested | Deterministic adversarial, runtime HTTP, storage, security/isolation, frontend and engineering gates; exact results below. |
| Integrated | Composed and exercised on this feature branch from `06dd144`; not merged into canonical `main`. Existing spec 063/provider contracts reused without edits. |
| Deployed | No production deployment, migration, flag activation or cutover. Loopback review candidate only. Feature off by default. |
| Verified E2E | Real application/auth/job/store/projection/AXENT/Next paths with explicitly SYNTHETIC website, identity and evaluator ports. Desktop and 390px browser evidence. No live Google, real customer observation or live JEV/Luna quality verification. |

## Traceability and actual evidence

| Goal | Contract / implementation | Verification |
| --- | --- | --- |
| Environment discovery plus public comprehension | Existing First Observation economic activity/demand retained; separate optional `FirstProof.understanding`, never substituted by classification | `test_runtime_bidirectional_reobservation_is_private_durable_and_fresh`; subscriber renders both readings |
| Minimal “Manolo, zapatero” | Three bounded questions over exact offering quotations, no invented audience/outcome | `test_minimal_manolo_has_evidence_backed_offer_strength_and_conditional_omission`; browser minimal solar-offer fixture |
| Clear communication without forced criticism | Stable exact citation may produce a strength for every dimension | `test_clear_offer_audience_and_outcome_need_no_invented_critique`; browser clear reobservation |
| Acquisition failure does not blame company | Incomplete acquisition/representation withholds absence attribution | `test_incomplete_acquisition_never_turns_not_stated_into_a_gap`, runtime missing-page test; browser acquisition screenshot |
| Evaluator error does not become a business defect | Fixed positive/negative controls, invalid choices and failures produce instrument error; uncertainty remains unknown | Provider/control/invalid-choice/low-confidence tests; browser instrument-error screenshot |
| Contradictory sources | Unresolved state preserves both source bases and conditional human review | `test_conflicting_pages_remain_unresolved_with_both_exact_sources` |
| Comparable reobservation | Instrument/model/method/source-set/language/persona/sample compatibility; basis changes compare exact quotations, timestamps do not simulate change | Model/language/source drift, quote-basis and same-hour tests; browser before/after/history |
| Durable private history | Additive SQLite history under owned completion lease; tenant/target/exact subject filter; latest eight; earliest page rights expiry | Four history tests, restart and cross-tenant HTTP E2E |
| Inspectable AXENT explanation | Derived private evidence in PRESENCE/VALUE retrieval, historical cut excludes future reports, direct authorized report reference | Runtime AXENT HTTP retrieval; frontend route tests reject stale/private-invalid references; browser button focuses exact report heading and citations support keyboard navigation |
| Respect authority, rights, privacy, cost | Separate `publicOfferInput` permission; contact/identity minimization; no tenant/private attention in provider state; no reasoning escalation | Per-page grant/expiry, Person-schema/contact, private-state, budget and zero-reasoning tests; unchanged canonical MCP policy and regression coverage |

Acceptance is in `tests/first_observation/test_public_understanding.py` (20 cases including parametrization), `test_understanding_history.py` (4) and `test_understanding_e2e.py` (3). Frontend contract/render/reference/revision tests live in `public-understanding.test.ts` and `axent-grounded.test.ts`. Fixtures assert behavior; they do not establish real model accuracy.

## Engineering results

| Gate | Recorded final result |
| --- | --- |
| Full Python, including final expiration repair | `uv run --group semantic-layer-live pytest -q --basetemp D:/AXIGNAL/sol64-exact-closure-20261009`: **2006 passed, 5 skipped**, 552.97s. |
| Focused after expiration repair | `pytest tests/first_observation tests/axent tests/product_mcp`: **153 passed**, 99.73s. |
| Frontend | `npm run typecheck`; `npm run check:i18n`: 1530 entries, missing []; `npm test`: **159 passed**; `npm run build`: pass, 528 localized knowledge pages. |
| Python static and architecture | `ruff format --check .`: 1349 formatted; `ruff check .`: pass; `mypy`: 472 source files, no issues; `architecture-guard --root .`: no violations. |
| Governance | architecture, deps, docs, graphify, hygiene, no-generated-data, spec and terminology: PASS. |
| Graph maintenance | `graphify update . --no-cluster`: AST-only, 18756 nodes / 55387 edges; scoped post-update query succeeded. Generated graph excluded from PR. |
| Review candidate | Final backend restarted from this source; HTTP 200; loopback Next/gateway/runtime; no production environment loaded. |

An earlier full successful execution recorded 2006 passed / 5 skipped in 576.50s. A subsequent inspection found that expiration removed metadata required by the frontend; the store now retains non-content authority/execution/coverage metadata, and the runtime E2E test verifies that purge/restart still yields a readable report with no retained quotations. The focused and final full results above include that repair. Browser responsive overflow and the AXENT private evidence destination were also repaired and verified, rather than accepted from code inspection alone.

Earlier full runs exposed two intermittent assertions in unchanged concurrency tests: GLEIF duplicate creation state and an organization-attention worker still alive after a two-second join. The complete GLEIF file passed 34 tests; the complete attention file passed 18 tests. The earlier attention-failing full run was 2005 passed / 1 failed / 5 skipped. Retained logs record failures as well as repeats. No timeout, test selection or gate was weakened.

The five existing skips cover POSIX filesystem ownership/deployment on Windows. This session did not run those Linux-specific checks. The installed frozen optional SDK group validates TypeSafe question shape without making an API call. MCP remains read-only/canonical-authorized and does not consume this private perception report; the feature does not introduce Luna escalation for measurement.

## Browser evidence and remaining acceptance

All screenshots under `evidence/` use **SYNTHETIC** source/evaluator data. Reserved example-domain links deliberately do not claim live public-site availability. Exact source URLs, quotations, timestamps and rights references are rendered and can receive keyboard focus. Browser verification covered actual reobservation/comparison/history, Spanish and English, desktop and 390px, acquisition miss, instrument error and AXENT-to-report focus. Other supported locale strings were checked through catalog completeness and deterministic render tests, not six separate browser sessions.

The initial mobile test with instrument details expanded exposed long rights-reference overflow; the scoped report text-wrap fix was made and verified on the final build. No canonical navigation, funnel, public demo or shared CTA redesign is included.

Visual status: `IMPLEMENTED + AUTOMATED_QA_PASS + VISUAL_EVIDENCE_READY + HUMAN_VISUAL_ACCEPTANCE_PENDING`. The project Design Director skill states: “Automation may report defects, deltas and evidence. It MUST NOT declare a material AXIGNAL visual change accepted.” Human acceptance therefore remains CTO review, not an agent assertion. See `.agents/skills/axignal-design-director/SKILL.md`.

## Decisions and live-use boundary

The report is DERIVED_CONDITIONED, and controls only detect gross instrument/contract failure. A probability threshold and margin are versioned experimental interpretation policy, not calibrated perception truth. Provider-independent SemanticCascade and CognitiveProvider remain replaceable. No files under `application/semantic_layer`, `cognition/providers` or `experiments/decision_lab` were edited; dependency lockfiles and canonical product doctrine were not changed.

Rich offering excerpts require a separate reviewed purpose grant on every selected page. Public visibility, robots permission and the existing routing-vocabulary grant are insufficient. Email/telephone/URL excerpts, structured contact/identity fields and Person-schema pages are excluded. Deterministic minimization is not a general personal-data classifier; a live operator must authorize reviewed offering content and its provider-processing purpose/retention. That operational review is not performed by these synthetic tests.

The sample is bounded to selected own-site pages, 16 quotations, one conditioned execution or declared exact reuse, unknown market and no private reader context. Reports go stale after seven days, with permitted content lifetime potentially shorter; expiry removes quotations. No statement about search ranking, sales impact, reputation or all real observers follows from this sample.

Independent real-source/evaluator quality evaluation and CTO visual acceptance remain open (T013/T012). A reproducible synthetic candidate demonstrates the implementation path, not production-grade validity or goal-wide DONE. The candidate has no reasoning narrator configured: AXENT evidence retrieval and provenance are real; its response explicitly reports the extractive fallback. Production admission still belongs to Python/EvidenceAdmission.

## Review candidate and reproduction

`http://127.0.0.1:3841/__synthetic` establishes the test-only candidate session; `/account` is the subscriber entry. Next binds 3840, gateway 3841 and runtime 3842, all loopback. Data and logs are outside the checkout under `D:\AXIGNAL\bidirectional-candidate` and `D:\AXIGNAL\bidirectional-evidence`; no secrets or operational data are committed. Follow `quickstart.md` to reproduce with a new disposable directory.

Only the requested feature branch is submitted. No merge, main move/rebase, production deployment or production flag activation is authorized or performed.
