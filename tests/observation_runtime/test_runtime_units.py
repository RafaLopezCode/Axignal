from __future__ import annotations

import ast
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.observation_intelligence import SourceCapability, geo
from application.observation_runtime import (
    FAMILY_POLICIES,
    LEAD_CAPABILITY,
    Acquisition,
    AcquisitionRequest,
    BudgetScope,
    BudgetUsage,
    DailyObservationBudget,
    LeadKind,
    LeadOutcome,
    LeadTier,
    LeaseLost,
    ObservationFamily,
    ResearchLead,
    TickStatus,
    TickStopReason,
    explain,
    lead_id,
    run_daily_tick,
)
from application.observation_runtime.budget import reserve
from application.observation_runtime.ports import AcquisitionPort
from tests.observation_runtime.harness import ATTENTION, DAY_1, SITE, XEED, World, world


def _lead(**overrides: object) -> ResearchLead:
    base = ResearchLead(
        lead_id=lead_id(XEED, ObservationFamily.DEMAND, LeadKind.OPEN_DEMAND, "EU/ES", "EU/ES"),
        xeed_id=XEED,
        family=ObservationFamily.DEMAND,
        kind=LeadKind.OPEN_DEMAND,
        target="EU/ES",
        geography=geo("EU/ES"),
        question="compatible-public-tenders",
        reduces_unknown="demand UNKNOWN",
        depth=0,
        parent_lead_id=None,
        origin_evidence=(),
        reasons=("ENTRY",),
        next_due_at=DAY_1,
        tier=LeadTier.FIRST_OBSERVATION,
        scheduling_reason="ENTRY_POINT_NEVER_OBSERVED",
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def _run(w: World, *, acquirers: dict[str, AcquisitionPort] | None = None, **kwargs: object):  # type: ignore[no-untyped-def]
    return run_daily_tick(
        store=w.store(),
        now=w.clock(),
        attention=ATTENTION,
        acquirers=acquirers or w.acquirers(),
        recompute=w.downstream,
        **kwargs,  # type: ignore[arg-type]
    )


def test_every_canonical_family_has_an_explicit_non_generic_policy() -> None:
    assert set(FAMILY_POLICIES) == set(ObservationFamily) and len(ObservationFamily) == 10
    for policy in FAMILY_POLICIES.values():
        assert policy.economic_questions and policy.entry_points and policy.stop_conditions
        assert policy.currentness.stale_after < policy.currentness.historical_after
    # SEO and GEO live in Presence; opportunities live in Demand.
    presence = {r.to_kind for r in FAMILY_POLICIES[ObservationFamily.PRESENCE].follow_ups}
    assert {LeadKind.SEARCH_VISIBILITY, LeadKind.GENERATIVE_VISIBILITY} <= presence
    demand = FAMILY_POLICIES[ObservationFamily.DEMAND]
    assert (
        LEAD_CAPABILITY[demand.entry_points[0].kind]
        is SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
    )
    # Cadences differ by family: one generic policy would make these equal.
    intervals = {p.base_interval for p in FAMILY_POLICIES.values()}
    assert len(intervals) >= 4


def test_leads_are_content_addressed_and_merging_never_resets_a_schedule() -> None:
    with pytest.raises(ValueError, match="content-addressed"):
        _lead(lead_id="lead:forged")
    with pytest.raises(ValueError, match="evidence that opened it"):
        _lead(depth=1, parent_lead_id="lead:parent")
    later = _lead(next_due_at=DAY_1 + timedelta(days=5), origin_evidence=())
    merged = later.merged_with(_lead(reasons=("ANOTHER_PATH",)))
    assert merged.next_due_at == later.next_due_at
    assert merged.reasons == ("ENTRY", "ANOTHER_PATH")


def test_why_spend_here_is_answerable_without_a_model() -> None:
    lines = explain(_lead())
    assert lines[0] == "TIER:FIRST_OBSERVATION:ENTRY_POINT_NEVER_OBSERVED"
    assert "NEEDS:PUBLIC_PROCUREMENT_OPPORTUNITIES" in lines
    assert "GEOGRAPHY:EU/ES" in lines and "REDUCES_UNKNOWN:demand UNKNOWN" in lines


def test_global_limits_stop_while_scoped_limits_only_skip() -> None:
    budget = DailyObservationBudget(max_http_requests=10, max_runs_per_xeed=1)
    policy = FAMILY_POLICIES[ObservationFamily.DEMAND]
    usage = BudgetUsage(day="2026-10-06")

    def ask(requests: int = 1, depth: int = 0):  # type: ignore[no-untyped-def]
        return reserve(
            budget, usage, xeed_id=XEED, family=policy, source_id="ted-search-v3",
            depth=depth, requests=requests, cost_per_request_microunits=0, elapsed_seconds=0.0,
        )  # fmt: skip

    assert ask() is None
    assert ask(requests=11).scope is BudgetScope.GLOBAL  # type: ignore[union-attr]
    assert ask(depth=4).scope is BudgetScope.DEPTH  # type: ignore[union-attr]
    usage.xeed_actions[XEED] = 1
    denial = ask()
    assert denial is not None and denial.scope is BudgetScope.XEED and not denial.stops_tick
    paid = reserve(
        DailyObservationBudget(), BudgetUsage(day="d"), xeed_id=XEED, family=policy,
        source_id="paid", depth=0, requests=1, cost_per_request_microunits=5, elapsed_seconds=0.0,
    )  # fmt: skip
    assert paid is not None and paid.limit == "max_paid_cost_microunits"


def test_exhausted_budget_stops_and_leaves_work_due_for_tomorrow(tmp_path: Path) -> None:
    w = world(tmp_path)
    report = _run(w, budget=DailyObservationBudget(max_http_requests=3))
    assert report.stop_reason is TickStopReason.BUDGET_EXHAUSTED
    assert report.requests <= 3
    due = [lead for lead in w.store().leads() if lead.next_due_at <= w.clock()]
    assert due, "unexecuted work stays due; nothing is extended past the budget"
    w.clock.at_day(2)
    tomorrow = _run(w)
    assert {e.lead_id for e in tomorrow.executed} >= {lead.lead_id for lead in due}


class _Crash(RuntimeError):
    pass


class _CrashAfter:
    """Delegates to real acquirers, then dies mid-tick like a killed process."""

    def __init__(self, inner: AcquisitionPort, budget: list[int]) -> None:
        self._inner, self._budget = inner, budget

    def acquisition_key(self, request: AcquisitionRequest) -> str:
        return self._inner.acquisition_key(request)

    def worst_case_requests(self, request: AcquisitionRequest) -> int:
        return self._inner.worst_case_requests(request)

    def acquire(self, request: AcquisitionRequest) -> Acquisition:
        if self._budget[0] <= 0:
            raise _Crash("killed")
        self._budget[0] -= 1
        return self._inner.acquire(request)


def test_interrupted_tick_is_fenced_then_resumed_without_repeating_work(tmp_path: Path) -> None:
    w = world(tmp_path)
    remaining = [2]
    crashing = {k: _CrashAfter(v, remaining) for k, v in w.acquirers().items()}
    with pytest.raises(_Crash):
        _run(w, acquirers=crashing)
    done_before = {lead.lead_id for lead in w.store().leads() if lead.attempts}
    usage_before = w.store().budget_usage("2026-10-06")
    assert len(done_before) >= 2 and usage_before.actions == 2

    # A second worker while the lease is live does nothing.
    held = _run(w)
    assert held.status is TickStatus.LEASE_HELD and not held.executed

    # After the lease expires the same day is resumed, not restarted.
    w.clock.now = DAY_1 + timedelta(hours=1, minutes=1)
    resumed = _run(w)
    assert resumed.status is TickStatus.COMPLETED and resumed.resumed
    assert not done_before & {
        e.lead_id for e in resumed.executed if e.outcome is not LeadOutcome.BLOCKED
    }
    # The in-memory share cache dies with the process: a lead of another family may
    # fetch the same page once more after a crash. No lead is repeated.
    assert w.web.requests[SITE] <= 2
    assert w.store().budget_usage("2026-10-06").actions > usage_before.actions
    assert _run(w).status is TickStatus.ALREADY_COMPLETED


def test_a_worker_that_lost_its_lease_cannot_write(tmp_path: Path) -> None:
    w = world(tmp_path)
    store = w.store()
    first = store.claim_tick("2026-10-06", now=DAY_1, lease_seconds=60)
    assert first is not None and store.claim_tick("2026-10-06", now=DAY_1, lease_seconds=60) is None
    second = store.claim_tick("2026-10-06", now=DAY_1 + timedelta(seconds=61), lease_seconds=60)
    assert second is not None and second.resumed
    with pytest.raises(LeaseLost):
        store.commit(
            first, now=DAY_1, leads=(), evidence=(), candidates=(),
            usage=BudgetUsage(day="2026-10-06"), learning=store.learning(), recompute=(),
        )  # fmt: skip


def test_failing_source_backs_off_and_trips_its_daily_circuit(tmp_path: Path) -> None:
    w = world(tmp_path)
    w.web.down.add(SITE)
    d1 = _run(w)
    failed = [e for e in d1.executed if e.outcome is LeadOutcome.FAILED]
    assert failed and all(e.source_id == "official-public-website" for e in failed)
    assert w.web.requests[SITE] == 1, "one failed fetch is shared, not retried per family"
    website = next(lead for lead in w.store().leads() if lead.kind is LeadKind.WEBSITE)
    assert website.failures == 1 and website.next_due_at == w.clock() + timedelta(days=1)
    w.clock.at_day(2)
    _run(w)
    website = next(lead for lead in w.store().leads() if lead.kind is LeadKind.WEBSITE)
    assert website.failures == 2 and website.next_due_at == w.clock() + timedelta(days=2)
    # Operational learning records the failures; it never turns them into a claim.
    stats = w.store().learning().for_source("official-public-website")
    assert stats.failures == 2 and stats.hit_rate == 0.0


def test_cyclic_rediscovery_merges_into_the_existing_lead(tmp_path: Path) -> None:
    w = world(tmp_path)
    _run(w)
    leads = w.store().leads()
    identities = [(lead.xeed_id, lead.family, lead.kind, lead.target) for lead in leads]
    assert len(identities) == len(set(identities))
    assert max(lead.depth for lead in leads) <= max(p.max_depth for p in FAMILY_POLICIES.values())


def test_control_loop_imports_no_model_or_evaluator() -> None:
    root = Path(__file__).resolve().parents[2] / "application" / "observation_runtime"
    forbidden = ("cognition", "semantic_judgment", "semantic_extraction", "luna", "jev", "axent")
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                assert not any(part in name.lower().split(".") for part in forbidden), (path, name)
