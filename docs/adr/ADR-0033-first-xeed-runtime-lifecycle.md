# ADR-0033 — First-Xeed Runtime Lifecycle

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§2, 10, 14, 56.18; ADR-0026 through ADR-0032.

## Context

AXIGNAL already had `XeedGerminationState`, but it only distinguished GERMINATING from LIVE. That was too coarse to execute a truthful first-Xeed product loop and made partial/insufficient/blocked outcomes invisible.

FR-07 evolves the existing authority rather than creating a parallel lifecycle model.

## Decision

`domain.xeed.germination.XeedGerminationStatus` is the single runtime lifecycle authority for a planted Xeed.

The explicit statuses are:

- PLANTED
- RESOLVING
- OBSERVING
- PARTIAL_READY
- FIRST_XIGNAL_READY
- LIVE
- INSUFFICIENT_EVIDENCE
- FAILED
- BLOCKED

`LIVE != DONE`

`PARTIAL_READY != FAILURE`

`INSUFFICIENT_EVIDENCE != FALSE`

`BLOCKED != INSUFFICIENT_EVIDENCE`

## Transition authority

The domain model owns legal transitions and rejects illegal jumps such as PLANTED → LIVE. Each transition records exact from/to status, timezone-aware occurrence time and explicit reason code.

The application runtime consumes only already-governed artifacts:

- AuthorizedXeedOrganization;
- BootstrapPlan;
- PrimeExecutionTrace;
- ExplainableXignalProjection;
- externally produced readiness decision.

No timer, UI progress bar, model confidence or synthetic node count can advance lifecycle state.

## Runtime semantics

An authorized Xeed starts at PLANTED and may enter RESOLVING.

Bootstrap outcomes map truthfully:

- executable/source/research work → OBSERVING;
- RETAIN_UNKNOWN or DEFER → INSUFFICIENT_EVIDENCE;
- rights/budget block → BLOCKED.

A real Prime trace records observation progress and can move OBSERVING → PARTIAL_READY without claiming that a Xignal exists.

A real explainable Xignal moves OBSERVING/PARTIAL_READY → FIRST_XIGNAL_READY and permanently records the first Xignal identity.

LIVE promotion consumes a typed readiness decision but FR-07 does not own the policy that produces that decision. FR-08 owns FIRST_MAP readiness evaluation.

## Readiness decision binding

To prevent stale/cross-Xeed promotion, a readiness decision is bound to:

- xeed_id;
- first_xignal_id;
- observation_depth;
- lifecycle revision (transition count);
- policy id/version;
- explicit reason codes.

`READINESS DECISION FOR STATE A != AUTHORITY FOR STATE B`

## Recovery

PARTIAL_READY is recoverable. A later governed readiness decision may promote it back through FIRST_XIGNAL_READY and then LIVE without fabricating a second first Xignal.

INSUFFICIENT_EVIDENCE, BLOCKED and FAILED are explicit states and may re-enter resolving/observing through legal transitions when conditions change.

## Non-goals

FR-07 does not define FIRST_MAP readiness criteria, persistence/API/UI wiring, billing state or canonical truth. It does not infer progress from elapsed time or arbitrary node counts.

## Consequences

Future runtime can execute a first-Xeed lifecycle honestly, expose useful partial states, distinguish epistemic insufficiency from operational failure/blocking, and reserve LIVE for an explicit governed readiness authority.
