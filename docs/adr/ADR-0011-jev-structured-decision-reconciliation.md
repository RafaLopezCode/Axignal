# ADR-0011 — Reconcile Jev structured decision architecture

**Status:** Accepted for experimental architecture and deterministic validation; no production evaluator integration authorized.
**Date:** 2026-09-26
**Supersedes/amends:** `AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md` for future evaluation-contract design only. Historical records remain unchanged.

## Context

The accepted MASTER and Constitution keep deterministic truth mechanics, AXIGNAL-owned policy, evidence admission and canonical authority outside a model provider. P0-JEV-01/V3 and P0-JEV-02 established a replaceable structured-evaluation boundary and deterministic lab foundations. P0-JEV-03 captured one authenticated provider smoke request and a bounded wording experiment; these provider and replay paths were operationally validated.

The forensic P0-JEV-03 record and P0-JEV-DEEP-RECON (PR #15) establish that the live claim-support request contained a candidate identifier and evidence identifiers but no explicit claim proposition or semantic evidence passage. The separate corpus evidence array was not sent. The unchanged fingerprint reconstruction matches the recorded artifacts. The observed `0.20` is accuracy under that recorded insufficient request state; `JEV_CLAIM_EVIDENCE_ACCURACY=NOT_ESTABLISHED`.

## Decision

1. A successful serialization or syntactic state check is not a semantic answerability check.
2. Every future structured evaluation is governed by a versioned AXIGNAL `DecisionContract`, family-specific `StateContract`, explicit information requirements, answer-space/primitive contract and deterministic pre-provider `AnswerabilityGate`.
3. State assembly, normalization, state-contract validation, canonical serialization and fingerprinting are separate operations. Referenced evidence is resolved explicitly. An unresolved reference fails closed; an identifier never substitutes for semantic content.
4. Answerability means only that declared minimum information is present. It does not predict correctness, evidence truth or canonical validity. Unanswerable cases are excluded from model-quality metrics.
5. Deterministic composition preserves primitive-specific raw judgment and uncertainty. Composition policy is versioned; no universal confidence threshold is introduced.
6. The Decision Laboratory remains experimental and offline-first. Historical versions remain replayable under their original contracts. V-next fixtures and code do not rewrite P0-JEV-03 artifacts or promote grammar/policy.
7. Canonical admission remains an independent AXIGNAL authority. Jev/model output and the lab have no canonical write capability.
8. The generic V0.1 live lab and one-off P0-JEV-03 smoke/experiment entrypoints are replay-only; the experimental provider adapter independently requires a registered V-next DecisionContract and answerability pass before SDK import/call.

## Previous model, new evidence, and disposition

| Item | Disposition |
|---|---|
| Provider compatibility, live typed judgment capture, offline replay | Preserved as validated for the bounded P0-JEV-03 run and recorded SDK/model version. |
| V0.1 generic serialized state as sufficient evaluation input | Superseded for future evaluation by versioned, family-specific information contracts. |
| P0-JEV-03 `0.20` result | Preserved exactly as historical observed accuracy under its recorded state. |
| Claim-evidence capability conclusion from P0-JEV-03 | Not supported; claim-evidence accuracy remains not established. |
| AXIGNAL authority, provider replacement, unknown/missing distinction, deterministic composition, evidence admission | Preserved. |
| Minimum sufficient state, best primitive, calibration, thresholds, domain performance | Requires future independent controlled experiments; remains unknown. |

## Consequences

The experimental implementation is isolated under `experiments/decision_lab/`; V0.1 files and historical result artifacts remain byte-for-byte untouched. The new corpus is synthetic structural evidence only. Its small development/held-out split does not establish statistical or real-world performance. The preregistered information-ladder experiment is not run, is not eligible for live execution until independent golden provenance is valid, and is not authorized by this ADR.

## Alternatives considered

- Treat successful JSON compilation as answerability: rejected because it allows missing proposition/evidence information to masquerade as a valid semantic request.
- Patch the historical live state/result in place: rejected because that would rewrite evidence.
- Add a production Jev adapter or canonical-write path: rejected because neither is necessary for deterministic contract validation and both exceed this slice.
- Use one universal state or confidence score: rejected because semantic information needs and primitive uncertainty differ by family.

## Risks and rollback

V-next is additive and experimental. Rollback is removal of the V-next code/docs while retaining all existing V0.1 history. No data migration, production configuration, provider call or production behavior change is part of the decision.
