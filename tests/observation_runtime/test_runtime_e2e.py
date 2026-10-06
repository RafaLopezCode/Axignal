"""Multi-day E2E: daily ticks on a controlled clock, each one a fresh process.

Every tick opens new store and adapter handles on the same files, so each day
is also a restart. The scenario follows one Xeed across 40 days: first
observation, unchanged reuse, aging without fetch, new public demand found by
fractal expansion, no-gain backoff and idempotent reruns.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from application.observation_runtime import (
    DailyObservationBudget,
    LeadOutcome,
    LeadStatus,
    LeadTier,
    ObservationFamily,
    RecomputeTrigger,
    TickReport,
    TickStatus,
    TickStopReason,
    observation_digest,
    run_daily_tick,
)
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState
from tests.observation_runtime.harness import ATTENTION, NEW_CALL, SITE, XEED, World, world


def _tick(w: World, day: int, budget: DailyObservationBudget | None = None) -> TickReport:
    now = w.clock.at_day(day)
    return run_daily_tick(
        store=w.store(),
        now=now,
        attention=ATTENTION,
        acquirers=w.acquirers(),
        recompute=w.downstream,
        budget=budget,
    )


def _families(report: TickReport) -> set[str]:
    return {e.family for e in report.executed}


def test_autonomous_runtime_over_forty_days(tmp_path: Path) -> None:
    w = world(tmp_path)

    # DAY 1: due Xeed, first observation of every family, evidence, frontier, persistence.
    d1 = _tick(w, 1)
    assert d1.status is TickStatus.COMPLETED
    assert d1.stop_reason is TickStopReason.DUE_WORK_DONE
    assert _families(d1) == {f.value for f in ObservationFamily}
    assert d1.candidates_total == 3 and d1.scheduler_model_calls == 0
    assert w.web.requests[SITE] == 1, "presence, value and organization share one fetch"
    assert d1.shared_acquisitions >= 3
    assert d1.frontier_max_depth >= 1 and any(e.opened for e in d1.executed)
    # Families with no adopted source stay UNKNOWN with the reason, spending nothing.
    blocked = dict(d1.blocked)
    assert any("NO_KNOWN_SOURCE:PUBLIC_REVIEWS_AND_MENTIONS" in r for r in blocked.values())
    assert any("NO_ADOPTED_SOURCE:PUBLIC_FUNDING" in r for r in blocked.values())
    assert all(e.requests == 0 for e in d1.executed if e.outcome is LeadOutcome.BLOCKED)
    # Every spend is explainable without a model.
    for e in d1.executed:
        assert any(line.startswith("TIER:") for line in e.why)
        assert any(line.startswith("REDUCES_UNKNOWN:") for line in e.why)
        assert any(line.startswith(("ROUTED:", "NO_")) for line in e.why)
    store = w.store()
    assert all(
        c.candidate.epistemic_state is XignalEpistemicState.POTENTIAL
        for c in store.candidates(XEED)
    )
    # Fractal frontier: awards -> recurring buyer (Relationships) -> its open demand (Demand),
    # each step naming the evidence that opened it.
    leads = {lead.lead_id: lead for lead in store.leads()}
    deepest = max(leads.values(), key=lambda lead: (lead.depth, lead.lead_id))
    chain = [deepest]
    while chain[-1].parent_lead_id is not None:
        chain.append(leads[chain[-1].parent_lead_id])
    assert [(lead.family.value, lead.kind.value) for lead in chain] == [
        ("demand", "BUYER_OPEN_DEMAND"),
        ("relationships", "RECURRING_BUYER"),
        ("relationships", "AWARD_COAPPEARANCE"),
    ]
    assert all(lead.origin_evidence for lead in chain[:-1])
    digest_1 = observation_digest(store, XEED, as_of=w.clock())
    readings = {f.family: f for f in digest_1.families}
    assert readings["economics"].currentness == "UNKNOWN"
    assert readings["economics"].unknown_because
    assert readings["demand"].currentness == "CURRENT"

    # Same day again: idempotent, nothing re-run.
    ted_before = len(w.ted.bodies)
    again = _tick(w, 1)
    assert again.status is TickStatus.ALREADY_COMPLETED and not again.executed
    assert len(w.ted.bodies) == ted_before

    # DAY 2: unchanged content is reused; no recomputation; only daily-cadence leads run.
    extractions = w.downstream.semantic_extractions
    d2 = _tick(w, 2)
    assert _families(d2) == {"demand"}
    assert all(e.outcome is LeadOutcome.UNCHANGED for e in d2.executed)
    assert d2.recomputations == () and d2.recomputations_avoided == len(ObservationFamily)
    assert d2.duplicate_evidence > 0 and d2.candidates_new == 0
    assert w.web.requests[SITE] == 1
    assert w.downstream.semantic_extractions == extractions

    for day in range(3, 17):
        _tick(w, day)

    # DAY 17: new compatible demand is published; nothing is due to look at it yet.
    w.ted.publish(NEW_CALL)
    _tick(w, 17)

    # DAY 18 (aging): presence evidence turns STALE with no fetch; budget is zero today.
    site_requests = w.web.requests[SITE]
    d18 = _tick(w, 18, DailyObservationBudget(max_http_requests=0))
    assert d18.stop_reason is TickStopReason.BUDGET_EXHAUSTED and d18.requests == 0
    assert ("presence", "CURRENT", "STALE") in {(t[1], t[3], t[4]) for t in d18.transitions}
    assert (XEED, "presence", RecomputeTrigger.CURRENTNESS_TRANSITION.value) in d18.recomputations
    assert all(
        trigger != RecomputeTrigger.MATERIAL_CHANGE.value for *_, trigger in d18.recomputations
    )
    assert w.web.requests[SITE] == site_requests
    stale = [
        e
        for e in w.store().evidence()
        if e.family is ObservationFamily.PRESENCE and e.key == f"web:{SITE}"
    ]
    assert stale[0].currentness is Currentness.STALE
    assert stale[0].observed_at < w.clock(), "aging never fakes an observation time"
    presence_18 = {
        f.family: f for f in observation_digest(w.store(), XEED, as_of=w.clock()).families
    }
    assert presence_18["presence"].currentness == "STALE"

    # NEXT TICK (day 19): the aged lead and due sources run again. The website is
    # re-observed (refresh, not re-extraction) and the new public demand is found.
    digest_18 = observation_digest(w.store(), XEED, as_of=w.clock())
    evaluations, extractions = (
        w.downstream.structured_evaluations,
        w.downstream.semantic_extractions,
    )
    d19 = _tick(w, 19)
    website = next(e for e in d19.executed if e.kind == "WEBSITE")
    assert any(line.startswith(f"TIER:{LeadTier.STALE_EVIDENCE.name}") for line in website.why)
    assert website.outcome is LeadOutcome.UNCHANGED
    assert w.web.requests[SITE] == site_requests + 1
    assert (XEED, "presence", RecomputeTrigger.CURRENTNESS_TRANSITION.value) in d19.recomputations
    assert w.downstream.semantic_extractions == extractions, "refresh is not re-extraction"
    assert w.downstream.structured_evaluations > evaluations
    assert d19.candidates_new == 1
    found = next(e for e in d19.executed if e.new_candidates)
    assert found.family == "demand" and found.outcome is LeadOutcome.MATERIAL_CHANGE
    assert (XEED, "demand", RecomputeTrigger.MATERIAL_CHANGE.value) in d19.recomputations
    # Selective: families with neither new evidence nor a currentness change are untouched.
    assert {family for _, family, _ in d19.recomputations} == {"presence", "demand"}
    store = w.store()
    new = next(
        c for c in store.candidates(XEED) if c.candidate.record.record_id == "ted:720301-2026"
    )
    assert new.candidate.epistemic_state is XignalEpistemicState.POTENTIAL
    assert new.candidate.record.source_url and new.candidate.missing_context
    assert new.lead_id == found.lead_id
    assert any(r.startswith("ACTION:") for r in new.candidate.why_looked)
    digest_19 = observation_digest(store, XEED, as_of=w.clock())
    assert digest_19.fingerprint != digest_18.fingerprint
    assert any(
        o.title == new.candidate.record.title and o.open_on_as_of for o in digest_19.opportunities
    )

    # FOLLOWING TICKS: duplicates only, backoff, lower priority, bounded work, STOP each day.
    reports = [_tick(w, day) for day in range(20, 41)]
    assert all(r.candidates_new == 0 for r in reports)
    assert all(
        r.stop_reason in {TickStopReason.DUE_WORK_DONE, TickStopReason.NOTHING_DUE} for r in reports
    )
    assert sum(r.stop_reason is TickStopReason.NOTHING_DUE for r in reports) >= 5
    assert max(len(r.executed) for r in reports) <= 12
    final = {lead.lead_id: lead for lead in w.store().leads()}
    demand = [
        lead
        for lead in final.values()
        if lead.family is ObservationFamily.DEMAND and lead.status is LeadStatus.ACTIVE
    ]
    assert any(lead.tier is LeadTier.LOW_YIELD and lead.no_gain_streak >= 2 for lead in demand)
    assert all(
        lead.next_due_at - lead.last_attempt_at <= timedelta(days=3)
        for lead in demand
        if lead.last_attempt_at
    )
    assert reports[-1].frontier_size == d1.frontier_size, "duplicates never grow the frontier"
