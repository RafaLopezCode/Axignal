# P0-JEV-02 TypeSafe Documentation Refresh

**Reviewed:** 2026-09-25
**Classification:** OFFICIAL_VENDOR_GUIDANCE / RESEARCH_EVIDENCE
**Authority:** Supporting evidence only; subordinate to the MASTER,
Constitution, accepted ADRs, Atlas, and P0-JEV-01. This record does not change
the accepted production architecture.

## Sources and versions

- [TypeSafe documentation index](https://docs.typesafe.ai/llms.txt),
  [System One](https://docs.typesafe.ai/concepts/system-one),
  [State](https://docs.typesafe.ai/concepts/state),
  [Choice](https://docs.typesafe.ai/primitives/choice),
  [Score](https://docs.typesafe.ai/primitives/score),
  [Noul](https://docs.typesafe.ai/primitives/noul), and
  [confidence](https://docs.typesafe.ai/confidence).
- [Models and pricing](https://docs.typesafe.ai/models),
  [HTTP API](https://docs.typesafe.ai/api),
  [Python SDK](https://docs.typesafe.ai/sdk/python),
  [Python RetryPolicy](https://docs.typesafe.ai/sdk/python/api/retries),
  [Noul self-consistency cookbook](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook),
  [Choice self-consistency cookbook](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook),
  [speculative fan-out](https://docs.typesafe.ai/patterns/fan-out),
  [composite scoring](https://docs.typesafe.ai/patterns/composite-scoring),
  [entity alignment](https://docs.typesafe.ai/cookbooks/entity_alignment),
  [citation checking](https://docs.typesafe.ai/cookbooks/citation_check), and
  [feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).
- Official source reviewed: Python SDK `typesafe-ai/typesafe-sdk-python`,
  version 0.7.1, source commit
  `0ffd094c72ed9445223060b24ffd7a56aa781fb4`; JavaScript SDK 0.6.0, source
  commit `66880ccded6cb642dc1809620c2b108c33730214`; official Skill 0.5.7,
  source commit `65a39f393687675ce170e6094757de20370365b9`.

## Current findings

### OFFICIAL_VENDOR_GUIDANCE / SDK FACT

- The official Python package is `typesafe-sdk`, imported as `typesafe_sdk`;
  its documented client evaluates typed Choice, Score and Noul questions and
  exposes typed answers, resolved model and usage. `TYPESAFE_API_KEY` is the
  documented environment credential.
- Jev 1.13 is identified as `jev-1.13.0`. The model page reviewed on this date
  listed USD 0.042 per million input tokens and zero output-token charge. This
  is a dated public price reference, not account invoice evidence.
- Python SDK transient retries default to two. The lab sets retry count to
  zero and uses a 30-second attempt timeout; its sequential runner separately
  enforces request/question/state-size and encoded request-byte limits before
  calls. Bytes are not token counts and are never converted to cost.
- SDK authorization headers are redacted but request and response bodies are
  not safe for verbose logging. The adapter retains normalized answers and
  safe metadata only; exception text and response bodies are discarded.
- The Noul self-consistency cookbook demonstrates repeated calls but changes
  a `uid` field between them and cautions that state variation is confounded
  with natural answer variation. The lab's predeclared repeat protocol keeps
  state and question identities fixed.
- TypeSafe describes questions in a batched request as independent judgments
  over the same state. Additional questions still contribute input cost.

### Material delta from P0-JEV-01

The documentation index now exposes separate Noul and Choice self-consistency
recipes and a detailed Python retry reference. The model page lists the Jev
1.13 input-token price. The lab stores that reviewed price in an explicit
versioned policy and applies it only to provider-reported input-token usage;
preflight request bytes do not estimate tokens or cost. The source provides no
invoice evidence and no AXIGNAL-labeled observations and does not contradict or
supersede P0-JEV-01.

### SDK decision

**SDK_SELECTED:** official Python `typesafe-sdk==0.7.1`, only in the optional
`decision-lab-live` dependency group.
**WHY:** the deterministic lab and AXIGNAL core are Python; the official SDK
preserves typed response and usage information.
**ALTERNATIVE_REVIEWED:** official TypeScript/JavaScript SDK 0.6.0. It was not
selected because this repository has no JavaScript application or lab runtime;
a second language runtime would add unrelated packaging and CI surface.
**ISOLATION_BOUNDARY:** `experiments/decision_lab/providers/typesafe.py` is the
only SDK import; the lab is excluded from the product wheel, production core
cannot import it, and it cannot import `domain`, `pipeline`, or `cognition`.
No production dependency or provider route is changed.

## AXIGNAL classifications

| Classification | Finding |
|---|---|
| OFFICIAL_VENDOR_GUIDANCE | Test narrow semantic judgments, state representations, and repeatability while preserving typed distributions and usage. |
| AXIGNAL_HYPOTHESIS | Explicit support criteria and preserved provenance/temporal state may make claim review more diagnostic. |
| AXIGNAL_HYPOTHESIS | Atomic economic-relationship judgments may localize failures but add questions and cost. |
| AXIGNAL_EXPERIMENTAL_RESULT | None. Live Jev was not run because no credential was present. |
| AXIGNAL_VALIDATED_POLICY | None. |

The hypotheses are registered in experiment definitions. No vendor benchmark,
cookbook threshold, or synthetic fixture is reported as AXIGNAL model quality.
