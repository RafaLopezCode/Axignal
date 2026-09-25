# P0-JEV-02 Research Notes

## Official documentation refresh (2026-09-25)

The installed official Skill remains at `typesafe-ai/skills` commit `65a39f393687675ce170e6094757de20370365b9` (v0.5.7), matching the current official main at inspection. Python SDK current main is `0ffd094c72ed9445223060b24ffd7a56aa781fb4` (0.7.1); JavaScript SDK is `66880ccded6cb642dc1809620c2b108c33730214` (0.6.0). No SDK release change from P0-JEV-01 was found.

### Material documentation delta

- Current docs index exposes separate self-consistency Cookbooks for Noul and Choice and a full RetryPolicy reference. These sharpen the experiment design but are vendor examples, not AXIGNAL results.
- The Noul cookbook reports 15 repeated Jev calls and includes a fresh `uid` field per call. The page itself cautions that this cannot distinguish sensitivity to the changing field from natural repeat variation. AXIGNAL repeatability experiments therefore keep semantic state and question versions identical, with no UID perturbation.
- Current models docs explicitly list Jev 1.13 (`jev-1.13.0`) at USD 0.042 per million input tokens and zero output-token charge, while warning rate limits can change. This is a dated vendor price source for bounded preflight estimates, not proof of AXIGNAL account billing.
- Current Python SDK retry policy defaults to two retries and can retry 408/429/5xx and connection/timeout conditions. Live lab calls set zero retries so one declared request cannot multiply silently.
- SDK docs/source state authorization headers are redacted but request/response bodies are not. The adapter therefore avoids SDK verbose logging, never serializes exception bodies, and stores only normalized responses and safe error categories.
- The docs index lists current `jev-latest` → `jev-1.13.0`; the lab pins `jev-1.13.0` for experiment identity and records any resolved response model.

No contradiction to P0-JEV-01 architecture was found. These findings do not update that accepted architecture or authorize production integration.

## SDK decision

**SDK_SELECTED**: Official Python `typesafe-sdk==0.7.1`, optional `decision-lab-live` group only.
**WHY**: AXIGNAL's core and deterministic processing are Python. The SDK exposes typed questions/answers, model and usage metadata, and typed operational failures.
**ALTERNATIVE_REJECTED**: Official JavaScript `@typesafe-ai/sdk` 0.6.0; reviewed, but AXIGNAL has no JavaScript backend or lab runtime, while adding a second runtime would increase packaging and operational surface.
**ISOLATION_BOUNDARY**: Lazy import in `experiments/decision_lab/providers/typesafe.py`; lab folder is excluded from built wheel; no production code imports the lab; optional dependency is absent from default and production dependency sets.

## Research classification

| Classification | Finding |
|---|---|
| OFFICIAL_VENDOR_GUIDANCE | Repeated calls can be studied for stability; keep the actual Noul/Choice values and model/usage metadata visible. |
| AXIGNAL_HYPOTHESIS | For claim support, explicit support/partial/contradiction/no-support criteria may improve diagnostic quality over an underspecified prompt. |
| AXIGNAL_HYPOTHESIS | Minimal evidence state may reduce distraction while preserving identity, provenance, temporal fields, and contradictions. |
| AXIGNAL_HYPOTHESIS | Separating relationship presence/type/time/contradiction may improve failure localization, though may increase question count. |
| AXIGNAL_EXPERIMENTAL_RESULT | None yet. No live Jev credential was present and no model calls were made. |
| AXIGNAL_VALIDATED_POLICY | None. A small synthetic corpus or recorded fixture cannot establish model quality, calibration, or production thresholds. |

## Current limits and unproven items

- AXIGNAL-specific accuracy, repeatability, calibration, and cost per useful judgment remain unknown.
- Current vendor input pricing may not equal account invoice terms and can change.
- Model alias resolution and SDK behavior must be recorded per response; no alternate current stable Jev version was available for a live version comparison during this slice.
- The official self-consistency cookbook's dataset, prices, repeated-call results, and thresholds do not transfer to AXIGNAL.
- P0-JEV-01's review-time TypeSafe facts remain historical evidence; this refresh is dated and does not silently rewrite that artifact.
