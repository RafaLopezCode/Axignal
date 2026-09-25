# Jev source ledger — 2026-09-25

Access/review date for mutable sources: 2026-09-25. This ledger separates official evidence from independent observation. Mutable docs and `main` links should be rechecked before implementation; versioned release/tag links are reproducible snapshots where noted.

## Tier 1 — primary TypeSafe authority

| ID | Source | Type | Version / freshness | Claims used |
|---|---|---|---|---|
| O1 | [Documentation index](https://docs.typesafe.ai/llms.txt) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Current doc map, concepts, primitives, cookbooks |
| O2 | [State](https://docs.typesafe.ai/concepts/state) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | State is the content evaluated; accepted textual/JSON forms; shared state/questions |
| O3 | [Choice](https://docs.typesafe.ai/primitives/choice) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Fixed option set, selected value and distribution, confidence, option cap |
| O4 | [Score](https://docs.typesafe.ai/primitives/score) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Ordered levels, distribution, expected position, confidence |
| O5 | [Noul](https://docs.typesafe.ai/primitives/noul) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Proposition/yes probability, no separate confidence |
| O6 | [Confidence](https://docs.typesafe.ai/confidence) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Distribution concentration, uncertainty handling, thresholds are domain/stake dependent |
| O7 | [Fan-out](https://docs.typesafe.ai/patterns/fan-out) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Independent questions over one state; answers cannot see each other |
| O8 | [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Independent measures composed with application-defined weights |
| O9 | [Building with System One](https://docs.typesafe.ai/concepts/how-to-build-with-system-one) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | Model supplies narrow judgments; code owns workflow and deterministic work |
| O10 | [Models](https://docs.typesafe.ai/models) | OFFICIAL_DOC | Mutable; accessed 2026-09-25 | `jev-1.13.0`, mutable `jev-latest`, published context and price figures |
| O11 | [Jev 1.13 known weak spots](https://docs.typesafe.ai/model-jaggedness/jev-1.13) | OFFICIAL_DOC | Mutable; page says last reviewed 2026-09-17 | Literal interpretation, numeric/date weakness, context and adversarial guidance |
| O12 | [Citation checking cookbook](https://docs.typesafe.ai/cookbooks/citation_check) | OFFICIAL_COOKBOOK | Mutable; example reports Jev 1.12 on 2026-08-16 | Exact retrieval in code then semantic judgment with claim and section together |
| O13 | [Entity alignment cookbook](https://docs.typesafe.ai/cookbooks/entity_alignment) | OFFICIAL_COOKBOOK | Mutable; example reports Jev 1.12 | Candidate pair state; same/related/different plus field judgments; author-reported evaluation |
| O14 | [Autoresearch feature discovery cookbook](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) | OFFICIAL_COOKBOOK | Mutable; accessed 2026-09-25 | Jev feature proposal evaluated by external supervised ML objective |
| O15 | [TypeSafe Python SDK releases](https://github.com/typesafe-ai/typesafe-sdk-python/releases) | OFFICIAL_SDK | v0.7.1 released 2026-09-21, commit `0ffd094` (short hash shown by GitHub) | Current release; API key exception handling fix; v0.7.0 serializer breaking change; v0.6 Score criteria migration |
| O16 | [TypeSafe Agent Skills repository](https://github.com/typesafe-ai/skills) | OFFICIAL_SKILL | Mutable `main`, accessed 2026-09-25; repository page showed 2 commits, no exact current head SHA surfaced in accessible view | Skill is first-party developer guidance for docs/cookbooks and code-composed typed judgments |
| O17 | [Official Python SDK constants on main](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/src/typesafe_sdk/constants.py) | OFFICIAL_SDK | Mutable `main`, accessed 2026-09-25 | SDK defaults include `jev-latest`, direct API base URL and 10 second operation timeout |

The installed project skill `.agents/skills/typesafe-ai/SKILL.md` was read only to identify and interpret the official guidance. It directs users to live docs as the version-sensitive source of truth, recommends sufficient named state, narrow typed questions, application-owned composition, and domain evaluation. Its local installed copy is not treated as proof of current release metadata.

## Tier 2 — official implementation evidence

| ID | Source | Type | Version / freshness | Claims used / limit |
|---|---|---|---|---|
| I1 | [Python SDK v0.7.1 release](https://github.com/typesafe-ai/typesafe-sdk-python/releases/tag/v0.7.1) | OFFICIAL_SDK | Versioned tag; release page reports commit prefix `0ffd094` | Exact release date and described changes. Release notes do not establish model accuracy or all transport semantics. |
| I2 | [Python SDK constants.py](https://github.com/typesafe-ai/typesafe-sdk-python/blob/main/src/typesafe_sdk/constants.py) | OFFICIAL_SDK | Mutable `main` | Direct API defaults shown in source; not a promise for all gateways or deployments. |

The current docs index links to API and SDK guides, but this review did not retrieve the complete retry/usage schema pages or an immutable SDK source tree. Retryable statuses, backoff details, request-ID guarantees, and exact usage accounting beyond docs' displayed figures therefore remain **UNKNOWN** here. Do not infer them from third-party clients.

## Tier 3/4 — independent ecosystem observations

| ID | Project | Type | Reviewed material | Observation and limitation |
|---|---|---|---|---|
| E1 | [nexibeo/jev-cookbook](https://github.com/nexibeo/jev-cookbook) | COMMUNITY_PATTERN | README, recipe result summary; mutable `main`, accessed 2026-09-25 | Small labeled samples, code-built state, parallel questions, review bands, deterministic candidate extraction. README reports live OpenRouter runs from 2026-09-19 against Jev 1.13; author explicitly says samples are not benchmarks. Results are not independently reproduced. |
| E2 | [agencyenterprise/jev-recipes](https://github.com/agencyenterprise/jev-recipes) | COMMUNITY_PATTERN | Repository README; mutable `main`, accessed 2026-09-25 | 88 composable TS recipes claim input/result validation, confidence policy and offline fixtures. Its docs distinguish fixture demos from live calls. No production effectiveness inference. |
| E3 | [chr-kelly/jev-cookbook](https://github.com/chr-kelly/jev-cookbook) | COMMUNITY_PATTERN | Repository README/search-indexed contents; mutable `main`, accessed 2026-09-25 | Reports a CLINC150 evaluation harness, request-shape linter, version/provider comparison and recipe patterns. The search-accessible page exposes author claims, not independent validation; exact quantitative artifacts not fully audited. |
| E4 | [rajivkuriakose/typesafe-jev-examples](https://github.com/rajivkuriakose/typesafe-jev-examples) | COMMUNITY_PATTERN | Repository README; mutable `main`, accessed 2026-09-25 | Documents provider-separated configuration and author-reported OpenRouter path; direct API path explicitly unrun in README. This is useful precisely as a provider provenance caveat. |
| E5 | [realbogart/jev](https://github.com/realbogart/jev) | COMMUNITY_PATTERN | Repository README; mutable `main`, accessed 2026-09-25 | Haskell client shows explicit configuration, timeout and typed API surface; independent implementation, not TypeSafe API authority. |

The following are not promoted to primary evidence: gateways, mirrors, unofficial clients, social posts, and project result tables. Gateway model aliases, request accounting, latency, availability, and model snapshots can differ from TypeSafe direct service. No community score is cited as a Jev guarantee.

## Tier 5 — AXIGNAL derivations and open questions

| ID | Type | Derivation / status |
|---|---|---|
| D1 | AXIGNAL_DERIVATION | Require a machine-checkable link from each question to the state fields needed to answer it. Official material motivates adequate relevant state but does not name a universal `answerability` API or guarantee. |
| D2 | AXIGNAL_DERIVATION | A runtime should preserve state, question, primitive, model/version, raw output, composition, policy, and observed outcome as distinct experiment records. This supports attribution; it is not a vendor requirement. |
| D3 | AXIGNAL_DERIVATION | Deterministic evidence retrieval, identifier validation, date/number checks, authority admission, and side effects belong in ordinary code/domain policy where exact rules exist. |
| U1 | UNKNOWN | Exact calibration guarantees, dataset scope, metric definition, and statistical uncertainty behind current marketing statements were not established by the accessible primary sources. |
| U2 | UNKNOWN | Exact retry defaults, idempotency semantics, billing on transport retry, and full API usage schema need version-pinned source review. |
| U3 | REQUIRES_EXPERIMENT | Target-domain error, calibration, repeatability, and review-routing utility for any AXIGNAL task. |

## Conflict and freshness notes

- The mutable model page reports the current model identifier `jev-1.13.0`; the Python SDK defaults to mutable `jev-latest`. A moving alias is not a reproducible experiment identifier.
- Community repositories report alternate gateway model names and outcomes. These are ecosystem observations, not evidence that direct TypeSafe behavior, billing, latency, or version resolution is identical.
- SDK release history shows serialized-type and criteria-shape changes within days in September 2026. Implementations must pin and test an SDK version and preserve raw request/response schema alongside experiments.
- Official recipes are worked patterns with reported results. Their patterns may be reusable; their scores, thresholds, and sample performance are not portable without local evaluation.
