# ADR-0026 — Temporal Xeed Bootstrap Controller

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§4.4, 7, 56.14, 56.18, 56.20; ADR-0025.

## Context

A planted Xeed must begin useful observation quickly without creating a second Brain or hard-coding an LLM-first pipeline. Existing architecture already has shared Observation Memory, governed source acquisition, rich state, market-entry semantics and the Prime control plane. The legacy semantic germination runtime remains historical implementation evidence but must not define Prime.

The unresolved problem is only the temporary transition from PLANTED to the normal event-driven Prime loop.

## Decision

Introduce a short-lived Xeed Bootstrap Controller in application space. Its sole objective is to reach the minimum governed state required for Prime as quickly and cheaply as possible, then disappear from the execution path.

Bootstrap follows this authority order:

1. Reuse governed shared Observation Memory for the canonical Organization.
2. If declared minimum bootstrap state is incomplete, select only explicit known source candidates capable of filling missing requirements.
3. Source candidates are planning hints only; they do not authorize network dispatch. Existing source policy/TLS/DNS controls remain mandatory.
4. If no known source can close the missing state, request ADAPTIVE_RESEARCH with the exact unresolved requirements.
5. As soon as minimum state is present, hand off to PrimeControlPlan. Prime owns all subsequent deterministic/evaluator/research routing.

## Selection and economics

Known-source selection is deterministic, budgeted and coverage-oriented. For each step it prefers the candidate that covers the largest number of still-missing bootstrap requirements; ties use explicit priority then stable candidate identity. Selection stops as soon as requirements are covered or the source budget is exhausted.

This is not a universal source-quality score and does not claim expected information gain. Future learning may replace the source-selection policy only through a new versioned, replayable policy.

BOOTSTRAP != BRAIN

KNOWN SOURCE != AUTHORIZED DISPATCH

SOURCE PROMISE != OBSERVATION

ADAPTIVE RESEARCH != CANONICAL TRUTH

## Replay and learning boundary

Every bootstrap plan carries a deterministic fingerprint over Xeed, subject, policy version, current state, disposition, selected sources and Prime handoff items. This gives the future Learning Engine a stable join key for source yield, cost, information gain, correction and downstream usefulness without allowing runtime self-modification.

Bootstrap policy is versioned and declares minimum initial state explicitly. Learning may propose better policy versions; production promotion remains governed and replayable.

## Non-goals

This ADR does not choose OpenAI Decisions, TypeSafe Jev or Luna. It does not implement provider adapters, market-classification grammar, source discovery, network dispatch, EvidenceAdmission, FAXT writes, Xignal presentation or autonomous policy mutation.

It also does not require a mandatory LLM call when a Xeed is planted. Adaptive intelligence is used when deterministic reuse and explicit known sources cannot establish the minimum state needed by Prime.

## Consequences

- Xeed-specific orchestration is temporary instead of becoming a permanent parallel pipeline.
- Existing public observations can make a new Xeed cheap to germinate.
- A never-seen organization can begin with governed known sources and escalate only when genuinely necessary.
- Missing information remains explicit and becomes research work rather than FALSE.
- Provider changes do not affect bootstrap semantics.
- Future learning has replayable bootstrap evidence but no authority to rewrite policy automatically.

## 2026-09-30 amendment — FR-01 dimensional handoff

The original V0 wording required a universal `minimum initial state` before Prime handoff. That requirement is superseded.

Bootstrap now assesses every declared `TypingDimensionContract` independently against the current `RichSubjectState`.

For each dimension:

- requirements satisfied → the dimension is answerable and may be handed to Prime now;
- requirements missing → the dimension remains an explicit bootstrap gap with the exact missing requirements.

An unrelated gap MUST NOT block useful work in another answerable dimension.

`BOOTSTRAP_COMPLETENESS != DIMENSION_ANSWERABILITY`

`DIMENSION_A_UNKNOWN != DIMENSION_B_BLOCKED`

`PARTIAL_STATE != FAILED_BOOTSTRAP`

Prime receives only currently answerable bootstrap dimensions. Missing dimensions remain outside executable Prime work until a later policy determines what to do with them. FR-01 does not define that later research-value decision; FR-02 owns it.

Explicit known source candidates may be selected for unresolved dimension requirements while answerable dimensions are already handed to Prime. Therefore source completion and useful partial work are no longer mutually exclusive phases.

If no dimension is answerable, Bootstrap may still use explicit known sources. The current fallback to adaptive research when neither answerable work nor known sources exist is transitional and is intentionally subject to FR-02 Research Value Gate.

The `BootstrapPolicy` no longer declares a universal set of `initial_state_requirements`. It remains versioned and currently governs bounded known source selection.

This amendment preserves all previous authority boundaries:

- Bootstrap is temporary application orchestration, not the Brain.
- Known source candidate != authorized dispatch.
- Missing information remains UNKNOWN.
- Prime owns mechanism routing for executable dimensions.
- Provider/model output has no truth authority.
- EvidenceAdmission remains the canonical write firewall.
