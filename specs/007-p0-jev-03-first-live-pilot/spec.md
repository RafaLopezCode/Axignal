# Feature Specification: P0-JEV-03 First Live Jev Empirical Pilot

**Feature Branch**: `experiment/p0-jev-03-first-live-pilot`
**Created**: 2026-09-25
**Status**: Draft
**Input**: CTO order for one bounded live provider smoke test followed, only after a passing smoke gate, by the single predeclared `claim-wording-ab` experiment.

## User Scenarios & Testing

### User Story 1 - Verify the Live Provider Boundary (Priority: P1)

An AXIGNAL experiment operator performs one live request using one existing synthetic Golden case and one existing versioned Choice question. The run captures only the minimum safe metadata and typed judgment needed to decide whether the provider boundary matches the approved laboratory contract.

**Why this priority**: The first live request is the safety and compatibility gate for any empirical experiment.

**Independent Test**: Offline checks prove the selected case, question, state variant, model, retry policy, byte budget, secret handling, and create-only artifact path. The live operation is then limited to one request and one question.

**Acceptance Scenarios**:

1. **Given** the pinned SDK, ignored local credential file, and approved synthetic assets, **When** the smoke run is invoked, **Then** it sends one request for `CES-01-clear-positive` and `CES.SUPPORT.v1` with model `jev-1.13.0`, one concurrency, and zero SDK retries.
2. **Given** a provider response or a provider failure, **When** the request completes, **Then** the run records a safe immutable artifact with present metadata, typed judgment or safe failure category, and no credential or raw request/response body.
3. **Given** a failed or unsafe smoke result, **When** the smoke gate is evaluated, **Then** the controlled experiment does not run and no automatic semantic retry occurs.

### User Story 2 - Run the Predeclared Controlled Experiment (Priority: P2)

After a smoke result passes every stated gate, an operator runs the complete smallest valid predeclared `claim-wording-ab` comparison over its five specified synthetic cases, two wording variants, and one repetition.

**Why this priority**: This produces the first bounded comparison while retaining the already reviewed sample and controlled dimensions.

**Independent Test**: Offline contract validation proves the exact locked experiment definition yields 10 requests and 10 questions, one at a time, with no retries and the pinned model. The live result is checked against that definition.

**Acceptance Scenarios**:

1. **Given** a passing smoke gate, **When** `claim-wording-ab` runs, **Then** it uses all five declared cases, both declared question variants, the unchanged minimal state, grammar, policy, criteria, and model.
2. **Given** live judgments, **When** evaluation completes, **Then** raw typed answers, distributions, uncertainty, provider usage, failures, descriptive metrics, and the predeclared formal outcome remain separately identifiable.
3. **Given** any missing provider metadata or usage, **When** the result is reported, **Then** it remains `UNKNOWN` and is not converted to zero or inferred.

### User Story 3 - Reproduce and Report the Evidence (Priority: P3)

An AXIGNAL reviewer can inspect the dated report and replay the recorded non-secret result offline without a credential or another provider call.

**Why this priority**: The evidence must be auditable and reproducible before it can inform any later governed decision.

**Independent Test**: Replay from the immutable recorded artifact reproduces its normalization, composition, supported metrics, formal outcome, and digest validation without reading `.env` or making a network request.

**Acceptance Scenarios**:

1. **Given** a recorded result artifact, **When** offline replay runs, **Then** the result digest verifies and deterministic derived outputs match the source artifact.
2. **Given** the research report, **When** a reviewer reads it, **Then** vendor facts, configuration, observations, derived metrics, interpretations, unknowns, and unevaluated claims are clearly distinguished.
3. **Given** synthetic corpus observations, **When** conclusions are presented, **Then** the report disclaims real-world accuracy and makes no production, canonical, grammar, model, or threshold promotion.

### Edge Cases

- Missing, duplicate, malformed, or empty local credential configuration prevents the live request before network access.
- Authentication, request, timeout, network, provider, or response-shape failures are captured as safe categories and do not trigger retries.
- Missing resolved model, distribution, confidence, usage, or timing subfields remain explicitly unknown where the source does not provide them.
- Existing result paths cannot be overwritten; an artifact path collision aborts the write.
- A smoke answer that is missing, malformed, unsafe to serialize, or incompatible with the selected primitive fails the smoke gate.
- Any experiment definition, lock, corpus, grammar, policy, case, or question drift from the P0-JEV-02 predeclared material invalidates the run before live access.

## Requirements

### Functional Requirements

- **FR-001**: The slice MUST remain an experimental research activity and MUST NOT grant Jev canonical or production authority.
- **FR-002**: The smoke operation MUST make exactly one request containing exactly one existing synthetic Golden case and one existing versioned `CLAIM_EVIDENCE_SUPPORT` Choice question.
- **FR-003**: The smoke operation MUST use the existing compiler, TypeSafe adapter, judgment normalization, pinned `jev-1.13.0` model, one concurrency, and zero SDK retries.
- **FR-004**: Credential loading MUST be explicit, process-local, and confined to the experimental boundary; secret values MUST NOT be printed, serialized, logged, committed, or persisted.
- **FR-005**: The smoke record MUST retain the timestamp, identifiers and versions, state fingerprint, model information when exposed, primitive, normalized judgment, replay-sufficient answer fields, provider-reported usage when present, local latency, retry count, adapter and SDK versions, source revision, and safe failure category when present.
- **FR-006**: A smoke result MUST pass all authentication, contract, serialization, model, typed semantic, uncertainty, usage, latency, replay, and authority-isolation checks before the controlled experiment is eligible to run.
- **FR-007**: After a passing smoke gate, the slice MUST execute only the unchanged, complete `claim-wording-ab@0.1.0` definition with five cases, two variants, one repetition, 10 maximum requests, sequential execution, and zero retries.
- **FR-008**: The run MUST preserve raw typed judgments and distributions before normalization, composition, Golden comparison, metrics, and predeclared outcome evaluation.
- **FR-009**: Provider omissions and unavailable billing evidence MUST remain unknown; the slice MUST NOT invent token counts, resolved models, confidence, cost, or other metadata.
- **FR-010**: The formal outcome MUST use the existing evaluator and its unchanged criteria; no post-hoc hypothesis, threshold, sample, case, wording, state, model, policy, or label changes are permitted.
- **FR-011**: Successful live observations MUST be stored as create-only, digest-verified, non-secret artifacts that support offline replay without credentials or network access.
- **FR-012**: The report MUST distinguish vendor facts, experiment configuration, live observations, derived metrics, interpretation, unknowns, and unevaluated claims, and prominently disclaim real-world accuracy and all forms of promotion or canonical authority.
- **FR-013**: Deterministic CI MUST remain independent of provider credentials, availability, live requests, and model behavior.
- **FR-014**: The slice MUST make no AXIGLAND, FAXT, INXIGHT, PATHX, Knowledge Frontier, production research, private-access, production policy, or production runtime writes.
- **FR-015**: The slice MUST leave `claim-wording-ab` outcome status as the existing evaluator determines and MUST NOT promote a grammar, model, threshold, or policy.

### Key Entities

- **Smoke Observation**: One request's identifiers, immutable state identity, model metadata, typed response or safe failure, usage and latency metadata, source revision, and artifact digest.
- **Controlled Run**: The immutable predeclared experiment definition and the complete set of case-by-variant observations.
- **Replay Artifact**: A non-secret recorded result used to reproduce deterministic transformations and evaluation offline.
- **Empirical Report**: A dated account separating observed facts from configuration, derivation, interpretation, unknowns, and unevaluated questions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Smoke request and question counts are each exactly one, with the approved case, question, model, one concurrency, and zero retries recorded.
- **SC-002**: The controlled experiment, if eligible, contains exactly five cases, two variants, one repetition, and at most 10 requests and 10 questions.
- **SC-003**: Every persisted observation can be digest-validated and replayed offline without a provider credential or network request.
- **SC-004**: No live-call secret appears in repository files, result artifacts, logs, Git changes, or pull-request content.
- **SC-005**: Required deterministic repository checks pass without provider credentials or network access to TypeSafe.
- **SC-006**: The report records outcome and limitations without changing Golden labels or promoting canonical truth, grammar, thresholds, models, production policy, or runtime.

## Assumptions

- The canonical branch base and ignored local `.env` credential are available and pass the forensic gates.
- The approved TypeSafe Python SDK remains pinned to version `0.7.1`, and current official documentation remains compatible with the existing adapter.
- The existing five-case experiment, wording variants, Golden labels, policy, and thresholds remain immutable during this slice.
- Live output artifacts contain only explicitly selected safe answer fields and metadata; HTTP bodies, credentials, and unreviewed provider objects are excluded.
- This is synthetic laboratory evidence and cannot establish real-world AXIGNAL accuracy.
