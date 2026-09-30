# ADR-0036 — AXENT Context and Continuity Separation

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§5, 23, 25, 26, 55; ADR-0017, ADR-0018, ADR-0035.

## Context

AXENT remained visually available while AXIGLAND focus changed, but the synthetic
subscriber runtime stored one global transcript. A prior investigation could
therefore remain visible after focus changed and appear to describe the new
object. Clearing the transcript would hide the mismatch but destroy continuity.

## Decision

AXENT separates four concerns explicitly:

1. current AXIGLAND object/focus;
2. contextual actions bound to that exact Xeed/object scope;
3. prior investigation continuity, labeled with its original scope and time;
4. historical transcript, retained rather than silently deleted.

Every AXENT message carries Xeed id, object kind, canonical object id and
occurrence time. Current-focus messages are rendered as current conversation.
Messages from another focus are rendered only inside a visibly separate prior
investigation section. A prior investigation may be resumed only by resolving
its recorded scope back to an authorized object in the current Xeed.

`CURRENT FOCUS != PRIOR TRANSCRIPT`

`FOCUS CHANGE != TRANSCRIPT DELETION`

`TRANSCRIPT TEXT != STRUCTURED CONTINUITY AUTHORITY`

## Runtime boundary

FR-10 implements the subscriber presentation/runtime contract in the synthetic
loopback lab. It does not create the future persistence/context broker described
by ADR-0017 and does not grant new Xeed read authority. Scope resolution fails
closed if a recorded object cannot be resolved inside the current projection.

Contextual question actions carry the active Xeed, object kind and canonical
object id. New fixture interactions record scope and time at creation.

## Consequences

Changing focus can no longer present prior conversation as though it described
the current object. Previous work remains visible, dated and resumable without
silent deletion. Future production AXENT persistence can adopt the same scoped
contract behind the authorized Context Broker rather than relying on transcript
replay as authority.
