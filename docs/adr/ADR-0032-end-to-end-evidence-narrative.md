# ADR-0032 — End-to-End Evidence Narrative

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§4.4A, 15, 19, 20, 26; ADR-0030, ADR-0031.

## Context

FR-05 created an explainable subscriber-safe Xignal and a deterministic explanation trail, but the trail still carried references rather than proving that those references resolve against real persisted runtime lineage.

The Frontier audit requires the strongest UX pattern — `Show how AXIGNAL knows` — to be backed by stored observations, immutable artifacts, temporal context, contradictions and explicit unknowns rather than post-hoc prose.

## Decision

Introduce `application/subscriber_projection/evidence_narrative.py` as the product-grade evidence-narrative resolver.

The resolver consumes an authorized Xeed/Organization context, an explainable Xignal projection, its Explainable Basis, Observation Memory, artifact-integrity port and any canonical FAXTs claimed as support.

It resolves the subscriber-visible path:

`XIGNAL → CLAIM / RELATIONSHIP / PATHX → OBSERVATION → SOURCE → TIME → UNKNOWN`

Contradictory observations remain explicit in the same narrative.

## Runtime lineage

Every Basis datum must resolve uniquely to an actual `GovernedObservation` for the authorized canonical subject. Its source reference must match the stored observation source.

When the observation has an immutable artifact reference, an application-owned `ArtifactIntegrityPort` verifies that artifact through the concrete content-addressed store adapter. Failure to resolve or verify fails closed.

The artifact reference itself is not emitted to the subscriber projection.

## UI-safe narrative

`EvidenceNarrative` and `EvidenceNarrativeStep` expose only product-semantic fields:

- step kind and human label;
- deterministic parent relationship;
- public source reference where applicable;
- observed time;
- currentness where applicable;
- boolean artifact-integrity confirmation.

They do not expose:

- CAS references;
- filesystem paths;
- peer IP addresses;
- HTTP headers;
- transport/instrument internals;
- raw Observation Memory identifiers as presentation keys.

`UI NARRATIVE != INFRASTRUCTURE TRACE`

## Deterministic navigation

The Xignal is the narrative root. `focus_step_id` and `return_focus_step_id` resolve inside the narrative and deterministically return the user to the parent Xignal focus.

Step order is stable and derived only from governed lineage. No model is asked to invent an explanation after the fact.

`POST_HOC EXPLANATION != LINEAGE`

## Replay

Observation Memory remains append-only/idempotent. Exact replay of the same observations does not alter the reconstructed narrative. The same Xignal/Basis/runtime lineage therefore produces an equal `EvidenceNarrative`.

## Artifact semantics

The Observation Memory artifact reference may point to an immutable acquisition envelope while the observation content fingerprint may represent a different payload such as the response body. The integrity adapter therefore verifies the CAS artifact against its own content-addressed digest and does not incorrectly equate it with the observation content fingerprint.

## Non-goals

FR-06 does not redesign the browser UI, create canonical state, expose raw evidence bytes, or add a new truth authority. It provides the runtime-backed application object that the existing `Show how AXIGNAL knows` UX can consume.

## Consequences

The key epistemic UX interaction is now backed by real persisted lineage and survives replay. AXIGNAL can explain a visible Xignal by traversing stored observations and verified artifacts without leaking infrastructure or fabricating narrative.
