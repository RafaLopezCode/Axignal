# ADR-0044 — Replay Reference Completeness

**Status:** Accepted
**Date:** 2026-10-01
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0024, ADR-0027, ADR-0030, ADR-0043.

## Context

FR-17 made Learning Memory reflect real execution. It still did not guarantee that a recorded event was reproducible. Several events had only fingerprints or partial provenance. A fingerprint can prove identity/stability, but it cannot reconstruct missing inputs, provider configuration or compiler/policy versions.

FR-18 requires each Learning Event to carry one of two explicit states:

1. exact replay references sufficient for the supported replay boundary; or
2. an explicit non-replayable classification with the exact missing-boundary reason.

## Decision

Introduce LearningReplayReference on every Learning Event.

It carries ReplayDisposition.REPLAYABLE or ReplayDisposition.NON_REPLAYABLE, a deterministic set of named references, and an explicit reason code for non-replayable events.

A replayable reference must contain at least one concrete reference and cannot carry a failure reason. A non-replayable reference must carry a reason.

LearningReplayReference.require(name, expected) fails closed when a required reference is absent or when the recorded version/value differs from the expected one. Version mismatch is therefore detectable and cannot be silently treated as replay.

## Runtime replay boundaries

### Source acquisition

Successful captured source acquisition is replayable from the immutable captured artifact for downstream reconstruction. Its replay references include immutable artifact ref, source policy id and fingerprint, source observation fingerprint and code SHA.

This does not claim the external network can be made to produce the same response again. It replays the captured observation boundary.

### Observation ingestion

Observation ingestion is replayable from immutable acquisition artifact, governed observation id/fingerprint, source policy id/fingerprint and code SHA. Before/after Observation State fingerprints remain on the Learning Event.

### Document representation

Representation is replayable from immutable source artifact, immutable representation artifact, representation id, representation version, normalization version, source observation fingerprint, source policy fingerprint and code SHA.

A caller that attempts replay with a different compiler/normalization version receives an explicit mismatch failure.

### Semantic extraction and provider-bound work

The current semantic extraction contract records provider and provider version but does not yet retain exact model and harness identities. Therefore structured semantic extraction is explicitly NON_REPLAYABLE: PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE.

The event still retains all available references, including representation artifact/version, semantic contract fingerprint, provider/provider-version, result fingerprint and code SHA.

Likewise structured-evaluator and adaptive-research Prime work are explicitly non-replayable until the concrete executor supplies exact provider/model/harness replay identity.

Deterministic Prime work is replayable from its state fingerprint, routing-policy version, route and code SHA.

### Bootstrap

Bootstrap currently retains the exact plan fingerprint, policy identity/version, state fingerprint and code SHA but not the complete governed plan payload. It is explicitly NON_REPLAYABLE: BOOTSTRAP_PLAN_PAYLOAD_NOT_RETAINED.

### Budget stops

Budget stops retain exact policy/state fingerprints and stop reason but not the complete controller state/policy payload. They are explicitly NON_REPLAYABLE: EXECUTION_BUDGET_STATE_PAYLOAD_NOT_RETAINED.

## Persistence and compatibility

SQLite persists replay disposition, references and reason code inside the append-only event payload.

Events written before ADR-0044 remain readable. Missing replay metadata is normalized to NON_REPLAYABLE: REPLAY_REFERENCE_NOT_RECORDED.

This is intentionally not promoted to replayable from fingerprints.

## Invariants

FINGERPRINT != REPLAY

REPLAYABLE => CONCRETE_REPLAY_REFERENCES

NON_REPLAYABLE => EXPLICIT_REASON

VERSION_MISMATCH => FAIL_CLOSED

CAPTURED_ARTIFACT_REPLAY != EXTERNAL_NETWORK_REEXECUTION

PROVIDER_NAME != COMPLETE_PROVIDER_REPLAY_IDENTITY

MISSING_MODEL_OR_HARNESS != REPLAYABLE

LEARNING_MEMORY != CANONICAL_TRUTH

REPLAY_REFERENCE != AUTHORITY_TO_WRITE_AXIGLAND

## Privacy, rights and retention

Replay metadata stores references and versions, not duplicated raw private payloads. Artifact access remains subject to the existing storage, rights, retention and privacy boundaries. A reference being present does not grant access to an artifact after retention expiry or rights revocation.

## Consequences

Learning Memory can now distinguish a genuinely replayable captured execution boundary from a stable fingerprint with missing inputs. Audits and future policy experiments can fail closed on missing references and version drift instead of silently overstating reproducibility.

FR-19 can now build replay/shadow policy comparison on top of an explicit replayability contract.

## Non-goals

This ADR does not make every provider-bound event replayable, retain secrets/provider payloads indefinitely, re-run external websites deterministically, change EvidenceAdmission, or authorize automatic policy promotion.
