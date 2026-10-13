# ADR-0095: Subscriber MCP: the organization panorama, its evidence and its history

**Status:** Proposed (needs CTO acceptance before integration).
**Date:** 2026-10-13
**Authority:** MASTER §1.1 (human vocabulary; no `Xeed` in new public APIs), §10 (LIVE, "since your last visit"), §11 (knowledge frontier), §18 (INXIGHT explicable to its evidence), §19 (no magic percentage), §20 (temporality), §21 (observability states, not a score), §30.2 (cost advantage is not a moat by itself), §31 (extraction attacks), §38 (thin integration primitives); Constitution; ADR-0014/0015 (measurement claims carry instrument and version); ADR-0086 (subscriber product MCP); spec 052 First Observation.
**Amends:** ADR-0086 §6, the tool list. Every other ADR-0086 decision stands unchanged: OAuth, per-call authorization, read-only, no model on reads, audit and revocation.

## Context

ADR-0086 gave a subscriber's own assistant the **economic reading** of an observed organization. It did not give it what the subscriber sees in the web product: the First Observation across the ten families, the crossings between them (INXIGHT), the changes between readings and the recorded history.

As a result, an assistant asked to *write a value report about Acme* had to research the organization again on its own. That costs the subscriber far more than reading what AXIGNAL already holds, and the result is worse: no governed states, no history, no evidence trail.

The subscriber pays for persistent observation. The assistant must be able to **interpret everything AXIGNAL read and holds** about that organization, and to report on its evolution, not only on today's photo.

## Decision

Four read-only tools are added, with public vocabulary only (§1.1). The existing `*_xeed_*` tools stay for compatibility as migration debt.

1. `list_organizations`: the organizations this subscriber may read now. This is the same authorization as `list_xeeds`.
2. `get_organization_panorama(organization_id)`: the starting point. It returns:
   - **Families:** each of the ten families with:
     - **observability** (§21): `STRONG`, `PARTIAL`, `LIMITED`, `UNKNOWN`, `CONFLICTING` or `STALE`, from deterministic rules stated in the response. It is never a number. Low observability is never presented as a bad organization.
     - the top known findings;
     - its **knowledge frontier** (§11), the questions still open.
   - **Signals:**
     - crossings, each traced to the findings that support it through `supported_by` finding ids (§18);
     - changes against a reading at least a week old, regressions first.
   - **Public understanding:** the report and its comparison.
   - **The record behind it:** sources read per family, instruments and versions, and days recorded.
   - **A report guide:** how to turn all of this into a value report without changing any state.
3. `get_organization_findings(organization_id, family, cursor)`: every finding of one family, paged. Each finding has a **stable finding id** (derived from kind, code, claim and source), its state, source, time, instrument, limitation and compact detail. Raw payloads are never returned.
4. `get_organization_history(organization_id, family?, since?)`: the recorded evolution (§20):
   - **dated events:** which supplier, client, partner, certification, buyer, market or rule appeared or disappeared, and on which day;
   - **numeric series** per metric;
   - **a per-family summary.**

   With `since=YYYY-MM-DD` it returns only what is new after that day, the "since your last report" of §10. Each series keeps its last reading before `since` as its starting point. A day without a value was not measured: it is unknown, never zero.

The MCP reading now includes the First Observation view through the same runtime call the web product makes, after the same portfolio re-authorization. As on the web, a read records that day's compact family metrics (ADR timeline, `fo_family_snapshots`) and may queue the bounded judgments the view already queues. Nothing else is written. Nothing admits evidence and nothing calls a model on the read path.

## Consequences

- A subscriber's assistant can write a governed value report from one panorama call plus targeted follow-ups. Its cost is a deterministic read, not a re-investigation.
- History is answerable as §20 asks: when something appeared, when it stopped being observed, how a metric moved.
- Temporal storage is a bounded **compact metric digest per day**, not a full periodic snapshot of the organization (§20 prefers event history). Events are derived from consecutive digests at read time.
- §31: the responses expose findings, their states, sources, instruments and versions, which is what a measurement claim requires. They do not expose rules' internal thresholds, budgets, prompts or scores.
- **200-subscription test:** today's findings are largely reconstructible from public sources. The history is not: it exists only because AXIGNAL kept observing the organization over time. It is exposed per observed organization, inside entitlement.
- An event-history store (current state plus events) can replace the daily digest later without changing these tool contracts.
