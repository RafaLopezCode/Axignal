# Phase 0 Research: P0-JEV-03 First Live Jev Empirical Pilot

**Date**: 2026-09-25
**Branch base**: `551ba1a2e78d2768089b45a9e764403174a14755`

## Official TypeSafe Contract Review

Sources reviewed on 2026-09-25:

- [TypeSafe documentation index](https://docs.typesafe.ai/llms.txt)
- [Python SDK guide](https://docs.typesafe.ai/sdk/python)
- [Synchronous client reference](https://docs.typesafe.ai/sdk/python/api/clients/sync)
- [Response type reference](https://docs.typesafe.ai/sdk/python/api/types/responses)
- [Choice primitive](https://docs.typesafe.ai/primitives/choice)
- [Confidence semantics](https://docs.typesafe.ai/confidence)
- [Retry policy reference](https://docs.typesafe.ai/sdk/python/api/retries)
- [Model catalog and pricing](https://docs.typesafe.ai/models)
- [Official Python SDK release v0.7.1](https://github.com/typesafe-ai/typesafe-sdk-python/releases)
- Installed AXIGNAL TypeSafe skill: `.agents/skills/typesafe-ai/SKILL.md`

**Official vendor facts**: The Python client accepts an explicit API key and timeout; `system_one` accepts `state`, `questions`, `model`, and a retry policy. Choice responses expose a selected choice, probabilities, and derived confidence. Response metadata includes a model and usage object; individual usage fields may be absent. Retry policy supports `max_retries=0`. The pinned immutable Jev model ID is `jev-1.13.0`; `jev-latest` is mutable and excluded. The official model page lists Jev 1.13 input price at `$0.042 / 1M tokens`; the approved public policy remains unchanged and invoices remain unknown without billing evidence.

**SDK version**: Repository lock and optional dependency group pin `typesafe-sdk==0.7.1`. Installed version was verified as `0.7.1` after syncing that group. **Version match: yes.**

**Contract comparison**: No material contradiction was found. The existing adapter passes a selected model and a zero-retry policy, supplies an explicit key and timeout, extracts typed Choice answer fields, preserves distributions/confidence, and treats missing usage/model metadata as absent. This slice adds a whitelist of source answer fields to the experimental artifact for replay; it will not serialize the SDK response object or request/response body.

**Failure contract**: SDK exceptions are classified into a safe category by the current adapter. Exception messages and response bodies are not suitable for artifacts. An unclassified error remains `UNKNOWN`.

## Decisions

1. Use `CES-01-clear-positive`, `CES.SUPPORT.v1`, `minimal@0.1.0`, and `jev-1.13.0` for one smoke request.
2. Use only the existing locked `claim-wording-ab@0.1.0` definition for phase B, with its exact five cases, variants, grammar, criteria, and state policy.
3. Keep local usage/cost unknown unless supported by the returned provider fields and unchanged public pricing policy. Preflight token count and monetary cost are unknown because P0-JEV-02 explicitly provides no reliable token estimator before usage.
4. Store artifacts under the new `docs/research/p0-jev-03/` path through create-only writes.
5. No vendor contract mismatch or dependency change authorizes changing the experiment or promoting any provider judgment.

## Resolved Questions

- **Does the SDK automatically load the repository `.env`?** No such behavior is assumed. A lab-only explicit loader will read only the named key into the current process; no dotenv dependency is added.
- **May experiment size be reduced?** No. The declared five-case/two-variant design is the smallest valid predeclared comparison and remains 10 requests/10 questions.
- **Can preflight cost be stated?** No. Without a defensible provider-input-token upper bound, both preflight tokens and monetary exposure remain `UNKNOWN`.
- **May a response alter labels or the grammar?** No. Labels and grammar locks remain unchanged and have no promotion path in this slice.
