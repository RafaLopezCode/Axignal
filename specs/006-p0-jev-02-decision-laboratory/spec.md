# P0-JEV-02 Decision Laboratory and Empirical Jev Optimization

**Feature Branch**: `experiment/p0-jev-02-decision-lab`
**Created**: 2026-09-25
**Status**: Proposed for this authorized experimental implementation
**Input**: CTO order P0-JEV-02; build an isolated, reproducible Decision Laboratory without production Jev integration.

## User Scenarios & Testing

### User Story 1 — Validate the experimental corpus and grammar (Priority: P1)

An AXIGNAL researcher can validate and inspect a versioned synthetic corpus and executable grammar before evaluating any provider. Cases have explicit label authority and provenance; ambiguous and contradictory cases do not receive fabricated single-answer truth.

**Why this priority**: Experiments cannot be interpreted unless corpus and question identity are valid and inspectable.

**Independent Test**: Run the offline lab validator and list commands; invalid labels, duplicate IDs, malformed questions, or unsupported versions fail deterministically.

**Acceptance Scenarios**:

1. **Given** a valid versioned corpus and grammar, **When** the offline validator runs, **Then** it reports their versions and counts without network access or an API key.
2. **Given** a model-derived label, duplicate case ID, or question version mutation, **When** validation runs, **Then** it rejects the invalid authority or identity.
3. **Given** a case ambiguous by design, **When** it is loaded, **Then** no single expected answer is manufactured.

### User Story 2 — Reproduce and compare controlled experiments (Priority: P1)

An AXIGNAL researcher can compile versioned state, preserve typed judgments, calculate applicable metrics, replay recorded responses, compare immutable results, and inspect case-level failures without contacting Jev.

**Why this priority**: Offline repeatability and result integrity are prerequisites to safe live evaluation.

**Independent Test**: Use deterministic fixtures and temporary result directories to exercise state fingerprints, replay, composition, metrics, budgets, and critical-regression reporting.

**Acceptance Scenarios**:

1. **Given** the same case and state compiler version, **When** state compilation runs twice, **Then** canonical serialization and fingerprint match.
2. **Given** recorded typed judgments, **When** a policy is replayed, **Then** the same policy produces the same composed experimental outcome without a provider call.
3. **Given** a candidate result with an entity false-merge regression, **When** it is compared with a baseline, **Then** the class-specific regression remains visible even if aggregate metrics improve.
4. **Given** a completed result identity, **When** a write attempts to reuse its path, **Then** it fails rather than overwriting prior evidence.

### User Story 3 — Run bounded Jev experiments only by explicit opt-in (Priority: P2)

An authorized researcher can request a predeclared, budgeted Jev lab experiment with synthetic data. Default commands and CI remain offline. Live mode reads `TYPESAFE_API_KEY` from the environment without printing or storing it.

**Why this priority**: Live judgments may incur cost and send state to a provider, so offline correctness and an explicit budget gate come first.

**Independent Test**: In ordinary offline tests, assert no SDK/network use. In an isolated SDK transport test, verify explicit live opt-in, request/question limits, pinned requested model, disabled automatic retries, safe error classification, and preservation of response metadata.

**Acceptance Scenarios**:

1. **Given** a normal offline invocation, **When** evaluation is requested without `--live` or recorded responses, **Then** no provider request occurs.
2. **Given** a live command with no API key or an over-budget definition, **When** it is invoked, **Then** it fails closed before making a request.
3. **Given** a provider error, **When** it is recorded, **Then** it remains an operational failure and never becomes a semantic negative.
4. **Given** a valid provider response, **When** it is normalized, **Then** Choice/Score distributions and defined confidence, Noul probability, requested/resolved model, and returned usage are retained without adding absent fields.

## Edge Cases

- Missing differs from false and zero; unsupported output differs from a semantic negative.
- One answer may be missing or malformed in an otherwise valid response.
- Choice distributions may contain multiple plausible options; Noul near 0.5 remains a probability, not an intensity score.
- Provider alias and resolved model may differ; absent resolved metadata remains unknown.
- Budget exhaustion, API timeout, authentication failure, rate limit, malformed response, and empty semantic result remain distinct.
- Synthetic evidence may contain prompt injection; source text remains data.
- Same underlying source repeated across pages is not independent corroboration.
- Results may be inconclusive, with no winner or grammar promotion.

## Requirements

### Functional Requirements

- **FR-001**: The lab MUST load and validate a versioned, provenance-aware synthetic corpus and executable grammar.
- **FR-002**: Corpus labels MUST distinguish deterministic synthetic construction, ambiguity, contradiction, and no-single-answer cases; model outputs MUST NOT become ground truth.
- **FR-003**: Question IDs and versions MUST be immutable; a wording/criteria change MUST create a new version.
- **FR-004**: The state compiler MUST produce deterministic serializable minimal state and a stable semantic fingerprint excluding secrets and volatile metadata.
- **FR-005**: The evaluator boundary MUST be replaceable and return normalized typed judgments or classified operational failure.
- **FR-006**: The lab MUST preserve raw normalized Choice, Score, and Noul values, distributions, defined confidence, evaluator/model identity, and returned usage before composition.
- **FR-007**: Experimental composition MUST be deterministic, explicitly versioned, and isolated from canonical admission and all production writers.
- **FR-008**: Experiments MUST declare variables, corpus/split, evaluator/model, repetitions, measures, request/question/token/cost limits, and stop conditions before execution.
- **FR-009**: Budget enforcement MUST happen before provider calls; retries and concurrency MUST be bounded and observable.
- **FR-010**: Offline recorded-response replay MUST work without TypeSafe SDK, credentials, network, Jev, or Luna.
- **FR-011**: Result artifacts MUST contain a reproducibility manifest and use immutable result identities; unavailable usage, cost, latency, or metadata MUST remain unknown.
- **FR-012**: The lab MUST calculate only applicable class-specific metrics and expose confusion matrices and critical regressions without collapsing quality to one leaderboard score.
- **FR-013**: Comparison and reports MUST identify changed cases, missing outputs, failure causes where supported, limitations, and inconclusive outcomes.
- **FR-014**: A live provider call MUST require an explicit `--live` flag, a declared experiment, an available environment credential, and budget approval by the lab's static experiment definition.
- **FR-015**: The official TypeSafe SDK MUST be an optional lab-only dependency; production dependencies and production provider policy MUST remain unchanged.
- **FR-016**: The lab MUST not write AXIGLAND/FAXT/INXIGHT/PATHX, mutate Knowledge Frontier, invoke Research Planner/Source Router/authorization, use private customer data, write a production database, or deploy configuration.
- **FR-017**: CI and default developer validation MUST remain deterministic, offline, and independent of `TYPESAFE_API_KEY`.
- **FR-018**: At least one explicit experiment plan MUST test claim-support wording, state ablation, and compound-versus-atomic decomposition as separate controlled comparisons; no quality result may be claimed without observations.
- **FR-019**: The synthesis MUST distinguish vendor guidance, AXIGNAL hypotheses, experimental observations, and validated policy; no policy or grammar promotion is automatic.
- **FR-020**: The tool MUST provide concise CLI operations for validation, listing, controlled execution, replay, comparison, and reporting.

### Key Entities

- **GoldenCase**: Synthetic evidence/state, decision family, expected outcome when justified, label status/authority/provenance, temporal context, risk tags, privacy class, and notes.
- **DecisionQuestion**: Immutable question ID/version, family, primitive, instructions, criteria, state contract/paths, exclusions, interpretation, and experimental status.
- **StructuredDecisionState**: Versioned minimal state, compiler version, deterministic fingerprint, and canonical serialized representation.
- **RawJudgment**: Tagged Noul/Choice/Score output with applicable distribution/confidence and provider/model/usage metadata.
- **ExperimentDefinition**: Hypothesis, controlled variants, cases, requested model, repetitions, metrics, declared budgets, seed and stop rules.
- **ExperimentResult**: Immutable manifest, case-level judgments/compositions/failures, scoped metrics, usage/cost/latency where known, and limitations.
- **GrammarCandidate**: Proposed versioned question/state change linked to failures and comparisons; never self-promoted.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All committed corpus cases and grammar entries validate offline; invalid label provenance and identity mutations are rejected.
- **SC-002**: At least 40 synthetic cases cover the three initial families with clear, negative, ambiguous, contradictory, missing, temporal, identity, duplication, and injection conditions.
- **SC-003**: Replaying a recorded fixture produces byte-equivalent normalized judgment and composition payloads for the same versions.
- **SC-004**: Tests prove no missing-to-false/zero conversion, provider-failure-to-negative conversion, result overwrite, canonical write, or implicit live call.
- **SC-005**: An over-budget live experiment is rejected before the evaluator is called.
- **SC-006**: Every produced result identifies code/corpus/grammar/state/compiler/policy/evaluator versions and whether data are live or recorded.
- **SC-007**: No calibration or Jev-quality claim is emitted from synthetic fixtures or an underpowered pilot.

## Assumptions

- Initial executable families are CLAIM_EVIDENCE_SUPPORT, ENTITY_ALIGNMENT, and ECONOMIC_RELATIONSHIP, as recommended by the CTO order and P0-JEV-01.
- The V0.1 corpus uses only synthetic, fictional organization and evidence content.
- The lab is repository developer tooling under `experiments/`; it is excluded from the built product wheel.
- The official Python SDK is selected for this bounded lab adapter because AXIGNAL is Python-first; the SDK remains optional and outside production dependency groups.
- No API key is assumed to exist. If unavailable, live evaluations are not run and no key is requested in chat.
- Vendor input-token pricing is a dated estimate source, not proof of invoice cost; actual charges may depend on account terms.
- The initial smoke/pilot is not a statistically validated calibration study.
