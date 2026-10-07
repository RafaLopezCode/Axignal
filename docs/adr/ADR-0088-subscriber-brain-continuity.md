# ADR-0088: Subscriber Brain continuity over EB-06, EB-07 and the T12 runtime

- **Status:** Accepted for review (CTO)
- **Date:** 2026-10-07
- **Authority:** MASTER §14, §15.1, §15.4, §20; Constitution; ADR-0049, ADR-0072, ADR-0077 (currentness at consumption); EB-06 (spec 043), EB-07 (spec 044), TASK-050 T022–T024, TASK-054 T10–T12.
- **Scope:** closing the seams between immutable Subscriber Brain snapshots, the temporal authority, recomputation and shared work. No new temporal store, scheduler, queue or lease system.

## Context

Brain snapshots were immutable and read-time currentness was reevaluated, but no snapshot declared what it depended on, nothing invalidated selectively when that changed, there was no private continuity (origin, open questions, delta), and EB-07 shared work and the T12 recomputation queue were not connected to the Brain's state.

## Decision

1. **Continuity is governed economic state, not conversation.** A checkpoint per Focus records: items (opportunities, EB-04 dimensions) with epistemic state, currentness and a semantic value fingerprint; deterministic open questions (missing context, UNKNOWN dimensions, non-current support, unobserved family, unmeasured representation); declared dependencies; and the trace (MarketMap fingerprint, EB-04 replay refs, plan, instruments).
2. **Origin.** `previous_checkpoint_id + organization + snapshot refs + temporal cut + dependency fingerprint`. The checkpoint id derives from lineage and meaning, so a replay never forks history; a Focus retargeted to another Organization starts a new lineage.
3. **Append-only, meaning-deduplicated.** A new checkpoint is written only after a new snapshot and only if the semantic fingerprint differs (clocks, ordering and serialization never count). History is never updated.
4. **Temporal authority stays EB-06.** Dependencies are evaluated with `compile_observation_state(as_of)`, reuse selection and the currentness policy: CURRENT, REFRESHED (same meaning, re-observed), STALE (revalidate; not false), REPLACED and WITHDRAWN (recompute), RIGHTS_BLOCKED and MISSING (UNKNOWN). Precedence is fixed and each subject is compiled once.
5. **Recomputation stays T12.** RECOMPUTE debt is persisted per checkpoint and family, then owed into the T12 `aor_recompute` queue with `owe_recompute`, fenced by the same condition as `claim_tick`: while a tick is live nothing is written and the debt stays undelivered for the next reconciliation (never lost, delivered once). The daily run reconciles enrolled Foci before the tick; the tick drains the debt through the existing `RecomputationPort`.
6. **Shared work stays EB-07.** Shared research writes its result into global Observation Memory. Only a completion that still owns its lease calls `on_subject_changed`, which fans out to dependent Foci through `subscriber_continuity_dependents` (subject → Focus index). Requester refs in the shared ledger must be opaque (`opaque_requester_ref`); raw `focus_`/`tenant:`/`principal:` identifiers are refused.
7. **Two leases, two levels.** The T12 tick lease owns *the daily run* (one worker per day); the EB-07 lease owns *one shared work item*. They never fence each other; continuity only reads the tick lease to avoid writing while a tick runs.
8. **Isolation.** Continuity is keyed by the authorized Tenant and Focus; reads re-authorize membership and Focus before loading anything. Canonical identity and evidence remain global; Customer Zero has no subscriber continuity.

## Consequences

- `select_reusable_observations` now ignores observations made after the context's cut. Evaluating their currentness raised and broke every historical subscriber read once newer evidence existed (regression test added).
- EB-04 dimensions have no T12 family: their invalidation is recorded and shown, but recomputing them still requires a server-owned execution plan (TASK-050 T051–T054).
- Retention: checkpoints, invalidations and debt are append-only at pilot scale; pruning is a later, governed decision.
