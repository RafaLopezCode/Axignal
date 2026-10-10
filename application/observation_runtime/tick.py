"""The daily tick: due work → budget → frontier → acquisition → delta/aging →
bounded expansion → selective recomputation → persist → next_due → STOP.

Deterministic and model-free: nothing in this module calls a model, and every
spend decision is explainable from the lead's tier, family policy, evidence
and budget. One tick per UTC day; a second call the same day is a no-op, and a
tick interrupted mid-way resumes from what it already persisted.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.temporal_currentness import evaluate_effective_currentness
from application.observation_intelligence.contracts import SourceDescriptor, TaxonomyCode
from application.observation_intelligence.learning import OperationalLearning
from application.observation_intelligence.registry import SourceRegistry
from application.observation_runtime.budget import (
    BudgetUsage,
    DailyObservationBudget,
    charge,
    global_denial,
    reserve,
    settle_acquisition,
)
from application.observation_runtime.families import (
    FAMILY_POLICIES,
    FAMILY_POLICY_VERSION,
    EntryTarget,
    FamilyObservationPolicy,
    ObservationFamily,
)
from application.observation_runtime.frontier import (
    LeadOutcome,
    LeadStatus,
    LeadTier,
    ResearchLead,
    explain,
    lead_id,
    lead_order,
)
from application.observation_runtime.ports import (
    Acquisition,
    AcquisitionPort,
    AcquisitionRequest,
    EvidenceState,
    LeadHint,
    ObservationRuntimeStore,
    PendingRecompute,
    RecomputationPort,
    RecomputationRequest,
    RecomputeTrigger,
    StoredCandidate,
    TickClaim,
    XeedAttention,
)
from domain.evidence.epistemics import Currentness

TICK_POLICY_VERSION = "aor-tick-2026-10-07.1"
_ANYWHERE = TaxonomyCode("GLOBAL", "ANY")
#: Backoff doubles at most this many times before the family ceiling applies.
_MAX_DOUBLINGS = 16


class TickStatus(StrEnum):
    COMPLETED = "COMPLETED"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    LEASE_HELD = "LEASE_HELD"


class TickStopReason(StrEnum):
    NOTHING_DUE = "NOTHING_DUE"
    DUE_WORK_DONE = "DUE_WORK_DONE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    LEASE_HELD = "LEASE_HELD"


@dataclass(frozen=True, slots=True)
class ExecutedLead:
    lead_id: str
    xeed_id: str
    family: str
    kind: str
    source_id: str | None
    outcome: LeadOutcome
    requests: int
    paid_cost_microunits: int
    new_evidence: int
    new_candidates: int
    opened: tuple[str, ...]
    #: The acquisition was already made today for another lead (no new request).
    shared: bool
    why: tuple[str, ...]
    next_due_at: str


@dataclass(frozen=True, slots=True)
class TickReport:
    day: str
    status: TickStatus
    stop_reason: TickStopReason
    stop_detail: str
    resumed: bool = False
    executed: tuple[ExecutedLead, ...] = ()
    deferred: tuple[tuple[str, str], ...] = ()
    transitions: tuple[tuple[str, str, str, str, str], ...] = ()
    recomputations: tuple[tuple[str, str, str], ...] = ()
    recomputations_avoided: int = 0
    shared_acquisitions: int = 0
    duplicate_evidence: int = 0
    rejected_hints: int = 0
    requests: int = 0
    paid_cost_microunits: int = 0
    candidates_total: int = 0
    candidates_new: int = 0
    frontier_size: int = 0
    frontier_max_depth: int = 0
    frontier_by_tier: tuple[tuple[str, int], ...] = ()
    blocked: tuple[tuple[str, str], ...] = ()
    next_due_at: str | None = None
    wall_seconds: float = 0.0
    #: The control loop never calls a model; downstream recompute is counted apart.
    scheduler_model_calls: int = 0

    def to_payload(self) -> dict[str, object]:
        return {
            "day": self.day,
            "status": self.status.value,
            "stop_reason": self.stop_reason.value,
            "stop_detail": self.stop_detail,
            "resumed": self.resumed,
            "executed": [
                {
                    "lead_id": e.lead_id,
                    "xeed_id": e.xeed_id,
                    "family": e.family,
                    "kind": e.kind,
                    "source_id": e.source_id,
                    "outcome": e.outcome.value,
                    "requests": e.requests,
                    "paid_cost_microunits": e.paid_cost_microunits,
                    "new_evidence": e.new_evidence,
                    "new_candidates": e.new_candidates,
                    "opened": list(e.opened),
                    "shared": e.shared,
                    "why": list(e.why),
                    "next_due_at": e.next_due_at,
                }
                for e in self.executed
            ],
            "deferred": [list(item) for item in self.deferred],
            "transitions": [list(item) for item in self.transitions],
            "recomputations": [list(item) for item in self.recomputations],
            "recomputations_avoided": self.recomputations_avoided,
            "shared_acquisitions": self.shared_acquisitions,
            "duplicate_evidence": self.duplicate_evidence,
            "rejected_hints": self.rejected_hints,
            "requests": self.requests,
            "paid_cost_microunits": self.paid_cost_microunits,
            "candidates_total": self.candidates_total,
            "candidates_new": self.candidates_new,
            "frontier_size": self.frontier_size,
            "frontier_max_depth": self.frontier_max_depth,
            "frontier_by_tier": dict(self.frontier_by_tier),
            "blocked": [list(item) for item in self.blocked],
            "next_due_at": self.next_due_at,
            "wall_seconds": self.wall_seconds,
            "scheduler_model_calls": self.scheduler_model_calls,
        }


class AttentionLifecycle(Protocol):
    def prepare(
        self, claim: TickClaim, now: datetime, leads: tuple[ResearchLead, ...]
    ) -> frozenset[tuple[str, str]]: ...

    def finish(self, claim: TickClaim, now: datetime, report: TickReport) -> None: ...


def _entry_leads(
    attention: XeedAttention, policy: FamilyObservationPolicy, now: datetime
) -> list[ResearchLead]:
    leads: list[ResearchLead] = []
    for entry in policy.entry_points:
        anchors: list[tuple[str, TaxonomyCode | None]]
        if entry.target is EntryTarget.WEBSITE:
            anchors = [] if attention.website is None else [(attention.website, None)]
        elif entry.target is EntryTarget.ORGANIZATION:
            anchors = [(attention.organization_name, None)]
        else:
            anchors = [(m.geography.code, m.geography) for m in attention.markets]
        for target, geography in anchors:
            leads.append(
                ResearchLead(
                    lead_id=lead_id(
                        attention.xeed_id,
                        policy.family,
                        entry.kind,
                        target,
                        None if geography is None else geography.code,
                    ),
                    xeed_id=attention.xeed_id,
                    family=policy.family,
                    kind=entry.kind,
                    target=target,
                    geography=geography,
                    question=entry.question,
                    reduces_unknown=f"{policy.family.value} of {attention.xeed_id} is UNKNOWN",
                    depth=0,
                    parent_lead_id=None,
                    origin_evidence=(),
                    reasons=(f"ENTRY_POINT:{FAMILY_POLICY_VERSION}",),
                    next_due_at=now,
                    tier=LeadTier.FIRST_OBSERVATION,
                    scheduling_reason="ENTRY_POINT_NEVER_OBSERVED",
                )
            )
    return leads


def _route(
    lead: ResearchLead,
    registry: SourceRegistry,
    acquirers: Mapping[str, AcquisitionPort],
    learning: OperationalLearning,
) -> tuple[SourceDescriptor | None, str]:
    """Abstract capability + geography → the best routable source with an adapter."""

    resolution = registry.resolve(lead.capability, lead.geography or _ANYWHERE)
    ranked = sorted(
        resolution.routable,
        key=lambda s: (
            -learning.adjusted_quality(
                s.source_id, min(s.reliability, s.precision, s.provenance_quality)
            )[0],
            s.cost_per_request_microunits or 0,
            s.source_id,
        ),
    )
    for source in ranked:
        if source.source_id in acquirers:
            return source, f"ROUTED:{lead.capability.value}->{source.source_id}"
    where = (lead.geography or _ANYWHERE).code
    if ranked:
        return None, "NO_ADAPTER:" + ",".join(s.source_id for s in ranked)
    if resolution.pending:
        pending = ";".join(f"{sid}:{'+'.join(why)}" for sid, why in resolution.pending)
        return None, f"NO_ADOPTED_SOURCE:{lead.capability.value}@{where}:{pending}"
    return None, f"NO_KNOWN_SOURCE:{lead.capability.value}@{where}"


def _scheduled(
    lead: ResearchLead,
    policy: FamilyObservationPolicy,
    outcome: LeadOutcome,
    now: datetime,
    *,
    new_to_lead: bool = False,
) -> ResearchLead:
    """Cadence after an attempt: yield keeps the base rhythm, no gain and failure back off."""

    if outcome is LeadOutcome.FAILED:
        failures = lead.failures + 1
        wait = min(
            policy.failure_backoff * 2 ** min(failures - 1, _MAX_DOUBLINGS), policy.max_interval
        )
        return replace(
            lead,
            failures=failures,
            next_due_at=now + wait,
            tier=LeadTier.SCHEDULED_REFRESH,
            scheduling_reason=f"FAILURE_BACKOFF:{failures}",
        )
    if outcome is LeadOutcome.MATERIAL_CHANGE:
        return replace(
            lead,
            failures=0,
            no_gain_streak=0,
            next_due_at=now + policy.base_interval,
            tier=LeadTier.SCHEDULED_REFRESH,
            scheduling_reason="CADENCE_AFTER_MATERIAL_CHANGE",
            last_material_change_at=now,
        )
    if new_to_lead:
        # Known to the family but new to this lead (a follow-up's first look): not a no-gain.
        return replace(
            lead,
            failures=0,
            no_gain_streak=0,
            next_due_at=now + policy.base_interval,
            tier=LeadTier.SCHEDULED_REFRESH,
            scheduling_reason="CADENCE_AFTER_EVIDENCE_NEW_TO_LEAD",
        )
    streak = lead.no_gain_streak + 1
    wait = min(policy.base_interval * 2 ** min(streak, _MAX_DOUBLINGS), policy.max_interval)
    low = streak >= policy.low_yield_after
    return replace(
        lead,
        failures=0,
        no_gain_streak=streak,
        next_due_at=now + wait,
        tier=LeadTier.LOW_YIELD if low else LeadTier.SCHEDULED_REFRESH,
        scheduling_reason=f"NO_GAIN_BACKOFF:{streak}",
    )


def _insert_ordered(queue: list[ResearchLead], lead: ResearchLead) -> None:
    key = lead_order(lead)
    index = next((i for i, item in enumerate(queue) if lead_order(item) > key), len(queue))
    queue.insert(index, lead)


@dataclass
class _Tick:
    leads: dict[str, ResearchLead]
    evidence: dict[tuple[str, str, str], EvidenceState]
    usage: BudgetUsage
    learning: OperationalLearning
    known_candidates: dict[str, set[str]]
    dirty: dict[tuple[str, str], tuple[RecomputeTrigger, set[str]]]

    def mark(
        self, xeed_id: str, family: ObservationFamily, trigger: RecomputeTrigger, key: str
    ) -> None:
        current = self.dirty.get((xeed_id, family.value))
        if current is None:
            self.dirty[(xeed_id, family.value)] = (trigger, {key})
            return
        # A material change supersedes a currentness-only transition.
        stronger = (
            RecomputeTrigger.MATERIAL_CHANGE
            if RecomputeTrigger.MATERIAL_CHANGE in (trigger, current[0])
            else trigger
        )
        self.dirty[(xeed_id, family.value)] = (stronger, current[1] | {key})

    def pending(self) -> tuple[PendingRecompute, ...]:
        return tuple(
            PendingRecompute(xeed_id, ObservationFamily(family), trigger, tuple(sorted(keys)))
            for (xeed_id, family), (trigger, keys) in sorted(self.dirty.items())
        )


def run_daily_tick(
    *,
    store: ObservationRuntimeStore,
    now: datetime,
    attention: tuple[XeedAttention, ...],
    acquirers: Mapping[str, AcquisitionPort],
    recompute: RecomputationPort,
    budget: DailyObservationBudget | None = None,
    registry: SourceRegistry | None = None,
    policies: Mapping[ObservationFamily, FamilyObservationPolicy] = FAMILY_POLICIES,
    lease_seconds: int = 3600,
    monotonic: Callable[[], float] = time.monotonic,
    research: AttentionLifecycle | None = None,
) -> TickReport:
    if now.tzinfo is None:
        raise ValueError("the daily tick needs a timezone-aware time")
    budget = budget or DailyObservationBudget()
    registry = registry or SourceRegistry()
    started = monotonic()
    day = now.astimezone(UTC).date().isoformat()
    claim = store.claim_tick(day, now=now, lease_seconds=lease_seconds)
    if claim is None:
        finished = store.tick_report(day) is not None
        status = TickStatus.ALREADY_COMPLETED if finished else TickStatus.LEASE_HELD
        reason = TickStopReason.ALREADY_COMPLETED if finished else TickStopReason.LEASE_HELD
        return TickReport(day, status, reason, "idempotent: this day's tick is not ours to run")

    def lease_now() -> datetime:
        # Evidence retains the tick's as-of; lease authority follows elapsed time.
        return now + timedelta(seconds=max(monotonic() - started, 0.0))

    xeeds = {item.xeed_id: item for item in attention}
    state = _Tick(
        leads={lead.lead_id: lead for lead in store.leads()},
        evidence={(e.xeed_id, e.family.value, e.key): e for e in store.evidence()},
        usage=store.budget_usage(day),
        learning=store.learning(),
        known_candidates={
            xeed_id: {c.candidate.candidate_id for c in store.candidates(xeed_id)}
            for xeed_id in xeeds
        },
        dirty={
            (item.xeed_id, item.family.value): (item.trigger, set(item.evidence_keys))
            for item in store.pending_recompute()
            if item.xeed_id in xeeds
        },
    )
    changed_leads: dict[str, ResearchLead] = {}

    # 1. Entry points: a family never looked at is UNKNOWN and due now.
    for xeed in attention:
        for policy in policies.values():
            for entry in _entry_leads(xeed, policy, now):
                if entry.lead_id not in state.leads:
                    state.leads[entry.lead_id] = changed_leads[entry.lead_id] = entry

    # 2. Aging without fetching: currentness moves with time, observed_at does not.
    at_start = {key: row.currentness for key, row in state.evidence.items()}
    transitions: list[tuple[str, str, str, str, str]] = []
    changed_evidence: dict[tuple[str, str, str], EvidenceState] = {}
    for evidence_key, row in sorted(state.evidence.items()):
        if row.xeed_id not in xeeds:
            continue
        policy = policies[row.family]
        decision = evaluate_effective_currentness(
            observation_id=row.key,
            observed_at=row.observed_at,
            previous=row.currentness,
            as_of=now,
            policy=policy.currentness,
        )
        if not decision.changed:
            continue
        aged = replace(row, currentness=decision.current)
        state.evidence[evidence_key] = changed_evidence[evidence_key] = aged
        transitions.append(
            (row.xeed_id, row.family.value, row.key, row.currentness.value, decision.current.value)
        )
        if policy.freshness_dependent:
            state.mark(row.xeed_id, row.family, RecomputeTrigger.CURRENTNESS_TRANSITION, row.key)
        owner = state.leads.get(row.lead_id)
        if owner is not None and owner.status is LeadStatus.ACTIVE and owner.next_due_at > now:
            # Aged evidence is selective replanning: only its own lead moves forward.
            state.leads[owner.lead_id] = changed_leads[owner.lead_id] = replace(
                owner,
                next_due_at=now,
                tier=min(owner.tier, LeadTier.STALE_EVIDENCE),
                scheduling_reason=f"EVIDENCE_{decision.current.value}:{row.key}",
            )

    receipts: list[tuple[str, Acquisition]] = []

    def commit(candidates: tuple[StoredCandidate, ...] = ()) -> None:
        store.commit(
            claim,
            now=lease_now(),
            leads=tuple(changed_leads.values()),
            evidence=tuple(changed_evidence.values()),
            candidates=candidates,
            usage=state.usage,
            learning=state.learning,
            recompute=state.pending(),
            receipts=tuple(receipts),
        )
        changed_leads.clear()
        changed_evidence.clear()
        receipts.clear()

    commit()

    waiting_shared = (
        frozenset()
        if research is None
        else research.prepare(claim, lease_now(), tuple(state.leads.values()))
    )

    # 3. Due work in deterministic tier order; blocked leads are re-routed when due.
    queue = sorted(
        (
            lead
            for lead in state.leads.values()
            if lead.xeed_id in xeeds
            and (lead.xeed_id, lead.family.value) not in waiting_shared
            and lead.due(now)
            and lead.depth <= policies[lead.family].max_depth
        ),
        key=lead_order,
    )
    executed: list[ExecutedLead] = []
    deferred: list[tuple[str, str]] = []
    done: set[str] = set()
    # Today's acquisition receipts: after a crash, a fetch already made is reused, not repeated.
    acquired: dict[str, Acquisition] = dict(store.receipts(day))
    stop: tuple[TickStopReason, str] | None = None
    shared_count = duplicates = rejected = new_candidates_total = 0

    while queue:
        store.assert_claim(claim, now=lease_now())
        lead = queue.pop(0)
        if (lead.xeed_id, lead.family.value) in waiting_shared:
            continue
        if lead.lead_id in done:
            continue
        done.add(lead.lead_id)
        policy = policies[lead.family]
        why = explain(lead)
        source, route = _route(lead, registry, acquirers, state.learning)
        if source is None:
            blocked = replace(
                lead,
                status=LeadStatus.BLOCKED,
                blocked_reason=route,
                last_outcome=LeadOutcome.BLOCKED,
                next_due_at=now + policy.blocked_recheck,
                scheduling_reason="BLOCKED_RECHECK",
            )
            state.leads[lead.lead_id] = changed_leads[lead.lead_id] = blocked
            executed.append(
                ExecutedLead(
                    lead.lead_id, lead.xeed_id, lead.family.value, lead.kind.value, None,
                    LeadOutcome.BLOCKED, 0, 0, 0, 0, (), False, (*why, route),
                    blocked.next_due_at.isoformat(),
                )
            )  # fmt: skip
            commit()
            continue

        cost = source.cost_per_request_microunits
        if cost is None:
            stop = (TickStopReason.BUDGET_EXHAUSTED, "COST_UNKNOWN")
            break
        allowance = min(
            budget.max_http_requests - state.usage.requests,
            policy.max_requests_per_tick - state.usage.family_requests.get(lead.family.value, 0),
        )
        cap = budget.source_cap(source.source_id)
        if cap is not None:
            allowance = min(allowance, cap - state.usage.source_requests.get(source.source_id, 0))
        if cost:
            allowance = min(
                allowance,
                (budget.max_paid_cost_microunits - state.usage.paid_cost_microunits) // cost,
            )
        acquirer = acquirers[source.source_id]
        request = AcquisitionRequest(
            lead=lead,
            source=source,
            attention=xeeds[lead.xeed_id],
            as_of=now,
            max_requests=0,
            known_evidence=frozenset(key for (x, _, key) in state.evidence if x == lead.xeed_id),
        )
        worst = acquirer.worst_case_requests(request)
        request = replace(request, max_requests=max(min(allowance, worst), 0))
        acquisition_key = acquirer.acquisition_key(request)
        shared = acquisition_key in acquired
        if shared:
            acquisition = acquired[acquisition_key]
            shared_count += 1
        elif acquisition_key in state.usage.pending_acquisitions:
            # No receipt survived: the call may have executed. Never infer zero spend
            # or fabricate an observation, and never redispatch this key today.
            acquisition = Acquisition(0, 0, 0, blocked="ACQUISITION_OUTCOME_UNKNOWN")
        else:
            denial = reserve(
                budget,
                state.usage,
                xeed_id=lead.xeed_id,
                family=policy,
                source_id=source.source_id,
                depth=lead.depth,
                requests=worst,
                cost_per_request_microunits=cost,
                elapsed_seconds=monotonic() - started,
            )
            if denial is not None:
                if denial.stops_tick:
                    stop = (TickStopReason.BUDGET_EXHAUSTED, str(denial))
                    break
                # A scoped limit skips this lead; it stays due for the next tick.
                deferred.append((lead.lead_id, str(denial)))
                continue
            # Durable upper bound BEFORE child work: a hard kill between dispatch
            # and receipt must not reset the daily budget on the next lease.
            charge(
                state.usage,
                xeed_id=lead.xeed_id,
                family=lead.family,
                source_id=source.source_id,
                requests=request.max_requests,
                paid_cost_microunits=request.max_requests * cost,
                failed=False,
            )
            state.usage.pending_acquisitions[acquisition_key] = {
                "requests": request.max_requests,
                "paid_cost_microunits": request.max_requests * cost,
            }
            commit()
            began = monotonic()
            store.assert_claim(claim, now=lease_now())
            acquisition = acquirer.acquire(request)
            state.usage.runtime_seconds += monotonic() - began
            settle_acquisition(
                state.usage,
                acquisition_key=acquisition_key,
                family=lead.family,
                source_id=source.source_id,
                requests=acquisition.requests,
                paid_cost_microunits=acquisition.paid_cost_microunits,
                failed=acquisition.failure is not None,
            )
            acquired[acquisition_key] = acquisition
            receipts.append((acquisition_key, acquisition))
            stats = state.learning.for_source(source.source_id)
            stats.attempts += 1
            stats.requests += acquisition.requests
            stats.latency_ms += acquisition.latency_ms or 0
            stats.amount_microunits += acquisition.paid_cost_microunits
            if acquisition.failure is not None:
                stats.failures += 1

        if acquisition.blocked is not None:
            parked = replace(
                lead,
                status=LeadStatus.BLOCKED,
                blocked_reason=acquisition.blocked,
                last_outcome=LeadOutcome.BLOCKED,
                next_due_at=now + policy.blocked_recheck,
                scheduling_reason="BLOCKED_RECHECK",
            )
            state.leads[lead.lead_id] = changed_leads[lead.lead_id] = parked
            executed.append(
                ExecutedLead(
                    lead.lead_id, lead.xeed_id, lead.family.value, lead.kind.value,
                    source.source_id, LeadOutcome.BLOCKED, 0 if shared else acquisition.requests,
                    0, 0, 0, (), shared, (*why, route, acquisition.blocked),
                    parked.next_due_at.isoformat(),
                )
            )  # fmt: skip
            commit()
            continue
        attempted = replace(
            lead,
            status=LeadStatus.ACTIVE,
            blocked_reason=None,
            attempts=lead.attempts + 1,
            last_attempt_at=now,
        )
        opened: list[str] = []
        new_keys: set[str] = set()
        new_to_lead: set[str] = set()
        fresh: list[StoredCandidate] = []
        if acquisition.failure is not None:
            outcome = LeadOutcome.FAILED
        else:
            for found in acquisition.evidence:
                key3 = (lead.xeed_id, lead.family.value, found.key)
                prior = state.evidence.get(key3)
                if prior is None or prior.fingerprint != found.fingerprint:
                    new_keys.add(found.key)
                    updated = EvidenceState(
                        xeed_id=lead.xeed_id,
                        family=lead.family,
                        key=found.key,
                        fingerprint=found.fingerprint,
                        source_id=source.source_id,
                        provenance_ref=found.provenance_ref,
                        lead_id=lead.lead_id,
                        first_observed_at=found.observed_at
                        if prior is None
                        else prior.first_observed_at,
                        observed_at=found.observed_at,
                        changed_at=found.observed_at,
                        currentness=Currentness.CURRENT,
                    )
                else:
                    duplicates += 1
                    # Same content really re-observed: a temporal refresh, not new evidence.
                    updated = replace(
                        prior, observed_at=found.observed_at, currentness=Currentness.CURRENT
                    )
                    if prior.currentness is not Currentness.CURRENT:
                        transitions.append(
                            (
                                lead.xeed_id,
                                lead.family.value,
                                found.key,
                                prior.currentness.value,
                                "CURRENT",
                            )
                        )
                        if policy.freshness_dependent:
                            state.mark(
                                lead.xeed_id,
                                lead.family,
                                RecomputeTrigger.CURRENTNESS_TRANSITION,
                                found.key,
                            )
                state.evidence[key3] = changed_evidence[key3] = updated
            known = state.known_candidates.setdefault(lead.xeed_id, set())
            for candidate in acquisition.candidates:
                if candidate.candidate_id not in known:
                    known.add(candidate.candidate_id)
                    fresh.append(StoredCandidate(candidate, lead.lead_id, now))
            if new_keys or fresh:
                outcome = LeadOutcome.MATERIAL_CHANGE
                for marked in sorted(new_keys) or [fresh[0].candidate.candidate_id]:
                    state.mark(lead.xeed_id, lead.family, RecomputeTrigger.MATERIAL_CHANGE, marked)
            else:
                outcome = LeadOutcome.UNCHANGED if acquisition.evidence else LeadOutcome.NO_EVIDENCE
            attempted = replace(
                attempted,
                last_success_at=now,
                evidence_keys=tuple(
                    sorted({*attempted.evidence_keys, *(i.key for i in acquisition.evidence)})
                ),
            )
            # 4. Bounded, fractal expansion: only evidence new to this lead opens questions;
            # re-reading what it already saw (a duplicate) never expands the frontier again.
            new_to_lead = {i.key for i in acquisition.evidence} - set(lead.evidence_keys)
            for hint in acquisition.hints:
                if not new_to_lead & set(hint.evidence_keys):
                    continue
                child = _child(lead, hint, policies[hint.family or lead.family], budget, now, state)
                if child is None:
                    rejected += 1
                    continue
                existing = state.leads.get(child.lead_id)
                if existing is not None:
                    state.leads[child.lead_id] = changed_leads[child.lead_id] = (
                        existing.merged_with(child)
                    )
                    continue
                state.leads[child.lead_id] = changed_leads[child.lead_id] = child
                opened.append(child.lead_id)
                _insert_ordered(queue, child)
            if not shared:
                stats = state.learning.for_source(source.source_id)
                stats.records += len(acquisition.evidence)
                stats.new_records += len(new_keys)
                stats.duplicates += len(acquisition.evidence) - len(new_keys)
                stats.candidates += len(fresh)
                stats.follow_ups += len(opened)
        scheduled = _scheduled(
            attempted,
            policy,
            outcome,
            now,
            new_to_lead=outcome is LeadOutcome.UNCHANGED and bool(new_to_lead),
        )
        scheduled = replace(scheduled, last_outcome=outcome)
        state.leads[lead.lead_id] = changed_leads[lead.lead_id] = scheduled
        new_candidates_total += len(fresh)
        executed.append(
            ExecutedLead(
                lead.lead_id, lead.xeed_id, lead.family.value, lead.kind.value, source.source_id,
                outcome, 0 if shared else acquisition.requests,
                0 if shared else acquisition.paid_cost_microunits,
                len(new_keys), len(fresh), tuple(opened), shared, (*why, route),
                scheduled.next_due_at.isoformat(),
            )
        )  # fmt: skip
        commit(tuple(fresh))

    if stop is None:
        stop = (
            (
                TickStopReason.DUE_WORK_DONE,
                f"{len(executed)} leads executed; frontier has no due lead",
            )
            if executed
            else (TickStopReason.NOTHING_DUE, "no lead due and no evidence aged into replanning")
        )
    if stop[0] is TickStopReason.BUDGET_EXHAUSTED:
        stop_detail = stop[1]
    else:
        late = global_denial(budget, state.usage, elapsed_seconds=0)
        stop_detail = stop[1] if late is None else f"{stop[1]}; budget reached {late}"

    # 5. Selective recomputation: only families whose evidence or currentness moved.
    # Evidence that aged and was really re-observed in this same tick ends where it began:
    # no freshness-dependent work is owed for it (a material change is never dropped).
    for (xeed_id, family), (trigger, keys) in list(state.dirty.items()):
        if trigger is RecomputeTrigger.CURRENTNESS_TRANSITION and all(
            (held := state.evidence.get((xeed_id, family, key))) is not None
            and at_start.get((xeed_id, family, key)) is held.currentness
            for key in keys
        ):
            del state.dirty[(xeed_id, family)]
            store.clear_recompute(
                claim, now=lease_now(), xeed_id=xeed_id, family=ObservationFamily(family)
            )
    # Owed work survives a crash: it is persisted with every step and cleared only after it ran.
    commit()
    recomputations: list[tuple[str, str, str]] = []
    for owed in state.pending():
        store.assert_claim(claim, now=lease_now())
        recompute.recompute(
            RecomputationRequest(owed.xeed_id, owed.family, owed.trigger, owed.evidence_keys, now)
        )
        store.clear_recompute(claim, now=lease_now(), xeed_id=owed.xeed_id, family=owed.family)
        recomputations.append((owed.xeed_id, owed.family.value, owed.trigger.value))
    avoided = len(xeeds) * len(policies) - len(recomputations)

    active = [
        lead
        for lead in state.leads.values()
        if lead.xeed_id in xeeds and lead.status is LeadStatus.ACTIVE
    ]
    tiers: dict[str, int] = {}
    for lead in active:
        tiers[lead.tier.name] = tiers.get(lead.tier.name, 0) + 1
    upcoming = min(
        (lead.next_due_at for lead in state.leads.values() if lead.xeed_id in xeeds), default=None
    )
    report = TickReport(
        day=day,
        status=TickStatus.COMPLETED,
        stop_reason=stop[0],
        stop_detail=stop_detail,
        resumed=claim.resumed,
        executed=tuple(executed),
        deferred=tuple(deferred),
        transitions=tuple(transitions),
        recomputations=tuple(recomputations),
        recomputations_avoided=avoided,
        shared_acquisitions=shared_count,
        duplicate_evidence=duplicates,
        rejected_hints=rejected,
        requests=sum(e.requests for e in executed),
        paid_cost_microunits=sum(e.paid_cost_microunits for e in executed),
        candidates_total=sum(len(v) for v in state.known_candidates.values()),
        candidates_new=new_candidates_total,
        frontier_size=len(active),
        frontier_max_depth=max((lead.depth for lead in active), default=0),
        frontier_by_tier=tuple(sorted(tiers.items())),
        blocked=tuple(
            sorted(
                (lead.lead_id, lead.blocked_reason or "")
                for lead in state.leads.values()
                if lead.xeed_id in xeeds and lead.status is LeadStatus.BLOCKED
            )
        ),
        next_due_at=None if upcoming is None else upcoming.isoformat(),
        wall_seconds=round(monotonic() - started, 6),
    )
    if research is not None:
        research.finish(claim, lease_now(), report)
    store.complete_tick(claim, completed_at=lease_now(), report=report.to_payload())
    return report


def _child(
    parent: ResearchLead,
    hint: LeadHint,
    policy: FamilyObservationPolicy,
    budget: DailyObservationBudget,
    now: datetime,
    state: _Tick,
) -> ResearchLead | None:
    """A follow-up lead only when its family allows it, within depth and frontier caps."""

    family = policy.family
    rule = policy.allows(parent.kind, hint.kind)
    depth = parent.depth + 1
    if rule is None or depth > min(policy.max_depth, budget.max_follow_up_depth):
        return None
    child_id = lead_id(
        parent.xeed_id,
        family,
        hint.kind,
        hint.target,
        None if hint.geography is None else hint.geography.code,
    )
    family_leads = sum(
        1
        for lead in state.leads.values()
        if lead.xeed_id == parent.xeed_id and lead.family is family
    )
    if child_id not in state.leads and family_leads >= policy.max_leads_per_xeed:
        return None
    return ResearchLead(
        lead_id=child_id,
        xeed_id=parent.xeed_id,
        family=family,
        kind=hint.kind,
        target=hint.target,
        geography=hint.geography,
        question=rule.question,
        reduces_unknown=rule.reduces_unknown,
        depth=depth,
        parent_lead_id=parent.lead_id,
        origin_evidence=tuple(sorted(hint.evidence_keys)),
        reasons=(
            hint.reason,
            f"RULE:{FAMILY_POLICY_VERSION}:{parent.kind.value}->{hint.kind.value}",
            *hint.detail,
        ),
        next_due_at=now,
        tier=LeadTier.FOLLOW_UP,
        scheduling_reason=f"OPENED_BY:{parent.lead_id}",
    )
