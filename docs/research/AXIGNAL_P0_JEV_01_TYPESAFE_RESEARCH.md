# P0-JEV-01 TypeSafe / Jev Research Record

**Reviewed:** 2026-09-25
**Research class:** Vendor documentation and public-source code inspection.
**Authority:** Supporting evidence only; subordinate to AXIGNAL's MASTER,
Constitution, accepted ADRs, Atlas and the P0-JEV-01 architecture.
**Currentness:** TypeSafe docs and main-branch code may change. Recheck them
before implementation.

This record separates **OFFICIAL FACT**, **AXIGNAL INFERENCE**, **DESIGN
DECISION**, and **UNPROVEN ASSUMPTION**. Vendor benchmarks and model capability
claims are not AXIGNAL evaluation results.

## Sources reviewed

Official TypeSafe documentation index: [docs.typesafe.ai/llms.txt](https://docs.typesafe.ai/llms.txt).
Targeted pages reviewed:

- [System One](https://docs.typesafe.ai/concepts/system-one),
  [State](https://docs.typesafe.ai/concepts/state),
  [Primitives](https://docs.typesafe.ai/primitives),
  [Choice](https://docs.typesafe.ai/primitives/choice),
  [Score](https://docs.typesafe.ai/primitives/score),
  [Noul](https://docs.typesafe.ai/primitives/noul),
  [Confidence](https://docs.typesafe.ai/confidence), and
  [How to build with TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one).
- [Speculative fan-out](https://docs.typesafe.ai/patterns/fan-out),
  [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring),
  [Entity alignment cookbook](https://docs.typesafe.ai/cookbooks/entity_alignment),
  [Citation verification cookbook](https://docs.typesafe.ai/cookbooks/citation_check),
  [Autoresearch feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery),
  [Function calling cookbook](https://docs.typesafe.ai/cookbooks/function_calling),
  and [Parallel questions cookbook](https://docs.typesafe.ai/cookbooks/parallel_questions).
- [Models and aliases](https://docs.typesafe.ai/models),
  [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13),
  [HTTP API](https://docs.typesafe.ai/api),
  [Python SDK](https://docs.typesafe.ai/sdk/python),
  [Python response types](https://docs.typesafe.ai/sdk/python/api/types/responses),
  [Python exceptions](https://docs.typesafe.ai/sdk/python/api/exceptions), and
  [JavaScript SDK](https://docs.typesafe.ai/sdk/javascript).
- Official public repositories (main HEAD captured with `git ls-remote` and
  inspected from temporary shallow clones; no repository was added or vendored):

| Repository | Main SHA reviewed | Code examined | Finding |
|---|---|---|---|
| [typesafe-ai/skills](https://github.com/typesafe-ai/skills) | `65a39f393687675ce170e6094757de20370365b9` | `skills/typesafe-ai/SKILL.md` | Directs agents to current docs, typed questions, minimal named state, independent fan-out and empirical validation. |
| [typesafe-ai/typesafe-sdk-python](https://github.com/typesafe-ai/typesafe-sdk-python) | `0ffd094c72ed9445223060b24ffd7a56aa781fb4` | question, response, endpoint, error and retry modules; package metadata | Python public models validate typed questions/answers, expose typed views and usage, resolve configured model, and define bounded retry/error behavior. Main package version was 0.7.1. |
| [typesafe-ai/typesafe-sdk-js](https://github.com/typesafe-ai/typesafe-sdk-js) | `66880ccded6cb642dc1809620c2b108c33730214` | `src/types.ts`, `client.ts`, `retry.ts`, `errors.ts` | Typed result interfaces preserve per-question output; client has explicit timeout/retry, status error classes and usage/model metadata. Main package version was 0.6.0 (Node.js >=20). |
| [typesafe-ai/system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python) | `e1d4cc938204b22fc5a3c3aca7044072fe3f712d` | README, response extension and provider/schema modules | Compatibility interface can compare hosted Jev with generative-model providers. It synthesizes a System One-like contract and is not Jev, not an official Jev substitute, and not evidence of equivalent calibration. |

The official Skill was installed project-locally from
`typesafe-ai/skills/skills/typesafe-ai` at the captured main commit above. It
resides at `.agents/skills/typesafe-ai/`, includes its `LICENSE`, and is
Codex-discoverable through the shared project agent-skills path. No Python/JS
runtime manifest was changed; the Skill is not a product dependency.

## System One and Jev semantics

### OFFICIAL FACT

- Jev is documented as TypeSafe's first System One model: it evaluates a
  supplied state against typed questions and returns typed answers and
  probabilities rather than generated explanations or free-form text.
- Current model docs list `jev-1.13.0` / Jev 1.13. `jev-latest` is a mutable
  alias; the response includes the resolved model ID. `jev-preview` may move
  independently. TypeSafe says to pin a version when behavior was calibrated
  against a version. This is vendor guidance, not a production pin for AXIGNAL.
- Current docs say text-only input: string, JSON object, or arrays of text;
  no image/audio/video. English is the primary training language; the docs
  report lower accuracy for other languages, including CJK. This is a vendor
  statement and has not been measured against AXIGNAL's language mix.
- Current model page documents a 64k request input context with a 32k limit
  over state plus the longest single question. Rate limits are explicitly
  described as subject to change. Treat both as point-in-time vendor limits,
  not AXIGNAL budgets.
- The API is `POST https://api.typesafe.ai/v1/systemone` with `state`, `model`,
  and question map. It returns a resolved `model`, answers keyed by the
  question IDs, and usage token counts. Question IDs identify outputs and are
  not sent as semantic content to the model.
- Choice returns selected option, full probability map, and confidence. Score
  returns probability-weighted ordered position, rubric/legend, probability
  map and confidence. Noul returns probability of yes; it has no separate
  confidence field.
- Choice confidence summarizes distribution concentration; Score confidence
  summarizes its level distribution. Neither is an overall workflow-correctness
  probability or authorization signal. A Noul near .5 means the model assigns
  similar probability to yes and no; it is not “medium.” Multiple acceptable
  choices can spread distribution. Uncertainty on an unused branch can be
  ignored by application code.
- A call's questions see the same state and are evaluated independently. One
  answer cannot condition another question in the same request. Independent
  speculative questions can be batched; code ignores unused branches. A second
  call is meaningful when an earlier answer is needed to acquire/build the next
  state or determine its options. Additional questions consume input tokens;
  end-to-end cost and latency should be measured.
- State can be a string, JSON object or array. Official guidance recommends
  named fields when context contains multiple parts, explicit paths in
  instructions, enough relevant context, complete candidate coverage and a
  no-match option where valid. Code should own exact rules/calculations.
- The Jev 1.13 jaggedness page (reviewed 2026-09-17) warns about overly literal
  interpretation, numeric precision, date/time comparisons, indirection,
  large irrelevant state, adversarial content, inconsistent criteria, common
  structural invariants, and generation. It recommends precise questions,
  code for arithmetic/time/invariants, minimized state, and a generative model
  for generation. This is explicitly version-scoped vendor guidance.
- TypeSafe's docs call Jev calibrated; the docs also state calibration is
  measured across groups and does not guarantee an individual answer. AXIGNAL
  has no target-domain calibration evidence and must not infer it from a typed
  response or vendor statement.
- Official recipes illustrate claim-to-evidence verification, entity
  alignment, batching and feature discovery. Recipe scores, thresholds, cost,
  quality, and speed are not AXIGNAL results and are not adopted as policy.

### OFFICIAL SDK/API code facts

- Current Python SDK source is typed and Pydantic-based. It normalizes typed
  Choice/Score/Noul question objects or mappings, validates response shapes,
  exposes answers and typed convenience maps, model ID and usage. Its response
  model retains a raw HTTP response at its lower response base layer; AXIGNAL
  does not need to persist provider raw bodies.
- Python source defines separate API, auth, permission, invalid-request,
  not-found, rate-limit, server, connection, timeout and response-validation
  errors. Its retry policy can retry timeout/connection, 408, 429 and 5xx,
  honors retry-after headers, and has bounded attempts/backoff/budget. These
  are SDK implementation details, not a permanent API guarantee.
- Current JavaScript SDK defines corresponding typed question/response types,
  answer type inference, resolved model and usage, timeout/cancellation,
  configurable retry/backoff and typed API errors. It is designed for Node.js
  20 or newer. A JS web runtime is absent from AXIGNAL's current backend/core.
- Both SDKs keep credentials in environment/client configuration and call the
  same HTTP endpoint. A client retry policy can cause repeated paid input; any
  future AXIGNAL retry/budget policy must account for this explicitly.
- `system-one-adapter-python` is a separate TypeSafe-owned open-source
  compatibility/testing project that asks other LLM providers to emulate the
  typed interface and may derive probabilities. It should only be considered
  as an experimental comparison arm. Its output is not real Jev output and
  cannot validate the hosted Jev model's accuracy or calibration.

## Closest official cookbooks and transfer limits

| Source/pattern | OFFICIAL FACT / demonstrated pattern | AXIGNAL INFERENCE | DESIGN DECISION / transfer limit |
|---|---|---|---|
| Speculative fan-out and parallel questions | Multiple independent judgments over identical state can be requested together; answers do not share context. Docs' cost/speed comparisons are their sample workloads. | Economic relationship state may support parallel presence/type/currentness/contradiction judgments. | Use only independent questions; state each premise, preserve unused raw judgment, measure input and end-to-end cost. No assumption of free questions or unchanged AXIGNAL latency. |
| Composite scoring | Separate semantic dimensions can be combined with code-owned weights/policy. | Some AXIGNAL decisions may need multiple dimensions. | Do not make a weighted global truth score. Compensating score is invalid where contradiction or admission is a hard condition. Keep decision-class rules explicit. |
| Entity alignment | Cookbook uses a candidate pair, one Score plus companion Nouls to expose field disagreement, and warns that an incorrect merge is costly. | Candidate identity ambiguity can use narrow semantic judgments after deterministic identifiers. | Candidate generation and exact IDs stay in Python; semantic evaluator cannot merge or authorize. False merge rate is a critical class-specific lab metric. Cookbook data/output is not AXIGNAL calibration. |
| Citation checking | Exact quote presence is checked in code, then a Choice judges whether surrounding context supports the claim; uncertain outputs can route for review. | Candidate claim support can be decomposed into provenance/exact-match plus semantic support. | Jev may assess relation of supplied excerpt to claim; cannot manufacture evidence or provenance, nor canonicalize. |
| Feature discovery / AutoResearch | A loop proposes questions/features, evaluates them on labeled rows, and uses held-out model errors to revise candidates. | Could propose grammar candidates from failure clusters later. | Reuse only as offline proposal/evaluation technique. AXIGNAL requires provenance-bearing independent labels, holdout/regression/red-team checks and human governance; the cookbook's CatBoost and reported metrics are not AXIGNAL targets. |
| Function calling / intent routing | Typed choices can select bounded code paths while code retains control flow. | Could inform later decision routing. | Choice never grants access or authority. Source Router, OAuth, private-access broker and canonical writer stay behind AXIGNAL policy. |

## SDK choice for a future adapter

### AXIGNAL INFERENCE

Current packages, domain, pipeline, cognition and tests are Python; repository
package metadata requires Python 3.11+, and no JavaScript application/runtime
has source code. A future TypeSafe adapter is therefore most coherent in Python,
under `cognition/providers/` or a separately reviewed adapter boundary, and
reachable only through an AXIGNAL-owned evaluator interface. The official
Python client offers sync/async clients and typed request/response models. A
future adapter should be selected after integration tests and deployment
constraints are authorized.

### DESIGN DECISION

Use Python as the *proposed future adapter language*; do not add either SDK or
any lab-only dependency in P0-JEV-01. The JavaScript SDK remains relevant only
if a separately governed application-side use case is later demonstrated; no
browser must ever receive the API key. Neither official SDK's existence is a
reason to make it a dependency now.

## Version selection, errors, budgets and privacy

### OFFICIAL FACT

An alias can resolve to a different version without caller changes. The
resolved response model identifies which model answered. The docs currently
list Jev 1.13 and dynamic rate limits, and the response reports token usage.
The SDKs describe retry-after handling and typed request/auth/rate/server/
timeout/connection/response-validation failures. The public docs index did not
surface a migration-to-v1 guide; a direct attempted page was unavailable in
the web reader, so migration-specific facts remain unverified.

### AXIGNAL INFERENCE

An alias change is a potential semantic change. It needs an experiment on the
same labeled cases and explicit AXIGNAL promotion before any calibrated
production policy adopts it. Failed calls must remain operational failures;
retry exhaustion cannot be represented as an answer. Token usage is known
only when returned. Cost requires a versioned price source and attribution
policy; unknown usage/cost is not zero.

### UNPROVEN ASSUMPTIONS

- No AXIGNAL-labeled corpus yet proves accuracy, calibration, abstention
  utility, language performance, question discrimination, latency or cost.
- No guarantee is assumed for provider-side data retention, account-specific
  rate limits, stable alias cadence, API SLA, response fields outside current
  docs/SDK, or behavior after SDK/API upgrades.
- The API endpoint's use is external processing. Any production or private
  evaluation needs a later security/privacy/contract review and explicit
  authorization; this slice sends no data.

## Implications for AXIGNAL

The research supports a replaceable typed semantic evaluator, atomic question
grammar, compact family-specific state, raw judgment preservation, deterministic
composition, explicit failure states, and offline replay experiments. It does
not prove a Jev runtime belongs in production, select an exact production
model pin, justify thresholds, or replace evidence admission, Knowledge
Frontier, Research Planner, AXIGNAL epistemic classes, Luna or Brain. See the
[P0-JEV-01 architecture](../architecture/AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md)
for AXIGNAL's design decisions and [community research](AXIGNAL_P0_JEV_01_COMMUNITY_PATTERNS.md)
for non-authoritative evidence.
