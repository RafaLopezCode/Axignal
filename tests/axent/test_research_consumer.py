"""Durable attention consumes the existing tick, never a model/source side channel."""

import sqlite3
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from application.axent.grounded.answer import ResearchRequest
from application.axent.grounded.corpus import corpus_from_reading
from application.axent.research import ResearchConsumer
from application.economic_discovery.batch_research import (
    claim_research_batch,
    complete_research_batch,
)
from application.economic_discovery.continuous_observation import (
    PrimeResearchAuthority,
    SharedObservationIntent,
    opaque_requester_ref,
)
from application.observation_intelligence import SourceRegistry
from application.observation_intelligence.catalog import SOURCES
from application.observation_runtime import (
    DailyObservationBudget,
    ObservationFamily,
    run_daily_tick,
)
from application.observation_runtime.families import FAMILY_POLICIES
from application.observation_runtime.ports import Acquisition, LeaseLost
from pipeline.axent import SqliteResearchRequestLedger
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory
from tests.axent.fixtures import reading
from tests.observation_runtime.harness import ATTENTION, DAY_1, XEED, world
from tools.runtime.observation_research import compatible_shared_key, shared_scope


def setup(tmp_path: Path, family: ObservationFamily = ObservationFamily.DEMAND):
    w = world(tmp_path)
    ledger = SqliteResearchRequestLedger(
        tmp_path / "research.sqlite3", runtime_path=w.store()._path
    )
    corpus = corpus_from_reading(
        tenant_id="tenant:a", projection=reading(xeed=XEED, organization="Solartec"), as_of=DAY_1
    )
    item = ResearchRequest(
        "req:a",
        "tenant:a",
        XEED,
        family,
        (),
        "NO_AUTHORIZED_EVIDENCE",
        "OVERVIEW",
        DAY_1,
        corpus.organization_id,
        corpus.dependency_fingerprint,
    )
    assert ledger.request(item)
    return w, ledger, item, corpus


def tick(w, consumer, *, now=DAY_1, budget=None):
    return run_daily_tick(
        store=w.store(),
        now=now,
        attention=ATTENTION,
        acquirers=w.acquirers(),
        recompute=w.downstream,
        research=consumer,
        budget=budget,
    )


def state(ledger):
    return ledger.states(tenant_id="tenant:a", xeed_id=XEED)[0]


def test_happy_path_durable_completion_and_replay(tmp_path: Path):
    w, ledger, item, corpus = setup(tmp_path)
    consumer = ResearchConsumer(ledger, lambda *_: corpus)
    report = tick(w, consumer)
    result = state(ledger)
    assert result.status == "OBSERVATION_COMPLETED" and result.attempts == 1
    assert result.work_ids and result.last_attempt and report.scheduler_model_calls == 0
    spent = len(w.ted.bodies)
    assert not ledger.request(item)
    tick(w, consumer)
    assert len(w.ted.bodies) == spent
    restarted = SqliteResearchRequestLedger(
        tmp_path / "research.sqlite3", runtime_path=w.store()._path
    )
    assert state(restarted) == result
    assert restarted.states(tenant_id="tenant:b", xeed_id=XEED) == ()
    with sqlite3.connect(tmp_path / "research.sqlite3") as db:
        transitions = db.execute(
            "SELECT status FROM axent_research_transitions ORDER BY sequence"
        ).fetchall()
    assert transitions == [("PENDING",), ("CLAIMED",), ("OBSERVATION_COMPLETED",)]


@pytest.mark.parametrize(
    "budget", [DailyObservationBudget(max_http_requests=0), DailyObservationBudget(max_actions=0)]
)
def test_budget_blocks_child_calls_without_counting_attempt(tmp_path: Path, budget):
    w, ledger, _, corpus = setup(tmp_path)
    tick(w, ResearchConsumer(ledger, lambda *_: corpus), budget=budget)
    assert state(ledger).outcome == "BUDGET_BLOCKED" and state(ledger).attempts == 0
    assert not w.ted.bodies and not w.web.requests


@pytest.mark.parametrize(
    "failure", ["STOPPED_AUTHORIZATION", "STOPPED_EXPIRED", "STOPPED_UNSUPPORTED_SCOPE", "OBSOLETE"]
)
def test_invalid_or_obsolete_attention_never_creates_new_work(tmp_path: Path, failure):
    w, ledger, item, corpus = setup(tmp_path)
    now = DAY_1 + timedelta(days=8) if failure == "STOPPED_EXPIRED" else DAY_1

    def callback(request, _):
        if failure == "STOPPED_AUTHORIZATION":
            return None
        if failure == "OBSOLETE":
            return replace(corpus, items=())
        if failure == "STOPPED_UNSUPPORTED_SCOPE":
            return replace(corpus, organization_id=request.organization_id)
        return corpus

    if failure == "STOPPED_UNSUPPORTED_SCOPE":
        # A legacy row cannot acquire subject authority by migration.
        other = replace(item, request_id="legacy", organization_id="", dependency_fingerprint="")
        ledger.request(other)
    claim = w.store().claim_tick(now.date().isoformat(), now=now, lease_seconds=3600)
    assert claim
    ResearchConsumer(ledger, callback).prepare(claim, now, ())
    rows = ledger.states(tenant_id="tenant:a", xeed_id=XEED)
    assert any(r.outcome == failure for r in rows)
    assert not w.ted.bodies and not w.web.requests and w.store().leads() == ()


def test_restart_reclaims_with_existing_tick_and_stale_worker_cannot_write(tmp_path: Path):
    w, ledger, _, corpus = setup(tmp_path)
    stale = w.store().claim_tick(DAY_1.date().isoformat(), now=DAY_1, lease_seconds=60)
    assert stale
    assert w.store().claim_tick(DAY_1.date().isoformat(), now=DAY_1, lease_seconds=60) is None
    later = DAY_1 + timedelta(seconds=61)
    current = w.store().claim_tick(DAY_1.date().isoformat(), now=later, lease_seconds=3600)
    assert current and current.token != stale.token
    with pytest.raises(LeaseLost):
        ledger.save(replace(state(ledger), status="OBSERVATION_COMPLETED"), stale, now=later)
    # A recovered run resumes the original day and the persisted request.
    tick(w, ResearchConsumer(ledger, lambda *_: corpus), now=later + timedelta(hours=2))
    assert state(ledger).status == "OBSERVATION_COMPLETED"


def test_unknown_source_stops_without_false_or_loop(tmp_path: Path):
    w, ledger, item, corpus = setup(tmp_path, ObservationFamily.ECONOMICS)
    consumer = ResearchConsumer(ledger, lambda *_: corpus)
    tick(w, consumer)
    initial = state(ledger)
    assert initial.status == "STOPPED" and initial.outcome == "STOPPED_SOURCE"
    assert not ledger.request(item)
    assert initial.attempts == 1
    assert "FALSE" not in str(initial)
    assert consumer.ledger.eligible(DAY_1 + timedelta(days=1)) == ()


@pytest.mark.parametrize("failed", [False, True])
def test_no_evidence_and_failure_have_distinct_bounded_lifecycles(tmp_path: Path, failed: bool):
    w, ledger, item, corpus = setup(tmp_path)
    inner = w.acquirers()["ted-search-v3"]

    class Controlled:
        calls = 0

        def acquisition_key(self, request):
            return inner.acquisition_key(request)

        def worst_case_requests(self, request):
            return 1

        def acquire(self, request):
            self.calls += 1
            return Acquisition(1, 0, 0, failure="UNAVAILABLE" if failed else None)

    adapter = Controlled()
    consumer = ResearchConsumer(ledger, lambda *_: corpus)

    def run(day):
        return run_daily_tick(
            store=w.store(),
            now=DAY_1 + timedelta(days=day),
            attention=ATTENTION,
            acquirers={"ted-search-v3": adapter},
            recompute=w.downstream,
            research=consumer,
            policies={ObservationFamily.DEMAND: FAMILY_POLICIES[ObservationFamily.DEMAND]},
        )

    run(0)
    assert state(ledger).status == ("FAILED_RETRYABLE" if failed else "UNRESOLVED")
    assert state(ledger).outcome == ("UNAVAILABLE" if failed else "NO_NEW_EVIDENCE")
    assert not ledger.request(item)
    run(0)
    assert adapter.calls == 1
    if failed:
        for day in range(1, 7):
            run(day)
        assert state(ledger).attempts <= 3
        assert state(ledger).status == "STOPPED"
    else:
        assert consumer.ledger.eligible(DAY_1 + timedelta(days=1)) == ()
    assert not w.store().evidence() and not w.store().candidates(XEED)


def test_unknown_cost_means_zero_child_work(tmp_path: Path):
    w, ledger, _, corpus = setup(tmp_path)
    registry = SourceRegistry(
        tuple(
            replace(s, cost_per_request_microunits=None) if s.source_id == "ted-search-v3" else s
            for s in SOURCES
        )
    )
    run_daily_tick(
        store=w.store(),
        now=DAY_1,
        attention=ATTENTION,
        acquirers=w.acquirers(),
        recompute=w.downstream,
        research=ResearchConsumer(ledger, lambda *_: corpus),
        registry=registry,
        policies={ObservationFamily.DEMAND: FAMILY_POLICIES[ObservationFamily.DEMAND]},
    )
    assert state(ledger).outcome == "BUDGET_BLOCKED" and state(ledger).attempts == 0
    assert not w.ted.bodies


def test_two_private_requests_attach_only_to_eligible_existing_eb07_authority(tmp_path: Path):
    w, ledger, item, corpus = setup(tmp_path)
    other = replace(item, request_id="req:b", tenant_id="tenant:b", xeed_id="focus:b")
    ledger.request(other)
    shared = SqliteSharedObservationWorkMemory(tmp_path / "shared.sqlite3")
    intent = SharedObservationIntent(
        item.organization_id,
        "public-state:1",
        "demand",
        ("public-evidence",),
        "existing-policy",
        "1",
        shared_scope(item),
    )
    shared.enqueue(intent, opaque_requester_ref("server", "existing-owner"))
    shared.replace_prime_authority(
        PrimeResearchAuthority(
            item.organization_id,
            "public-state:1",
            frozenset({intent.work_key}),
            DAY_1 - timedelta(minutes=1),
            "obs:public",
            DAY_1 + timedelta(days=3),
            "temporal",
            "1",
        )
    )
    consumer = ResearchConsumer(
        ledger,
        lambda request, _: replace(corpus, tenant_id=request.tenant_id, xeed_id=request.xeed_id),
        shared=shared,
        shared_key_for=lambda request: compatible_shared_key(shared, request),
    )
    attention = (*ATTENTION, replace(ATTENTION[0], xeed_id="focus:b"))
    report = run_daily_tick(
        store=w.store(),
        now=DAY_1,
        attention=attention,
        acquirers=w.acquirers(),
        recompute=w.downstream,
        research=consumer,
    )
    assert not any(e.family == "demand" for e in report.executed), (
        "pending EB-07 authority suppresses redundant public demand work"
    )
    for request in (item, other):
        row = ledger.states(tenant_id=request.tenant_id, xeed_id=request.xeed_id)[0]
        assert (
            row.outcome == "WAITING_EXISTING_SHARED_WORK" and row.shared_work_key == intent.work_key
        )
    work = shared.get(intent.work_key)
    assert work and len(work.requester_refs) == 3
    assert all("tenant:" not in ref and "focus:" not in ref for ref in work.requester_refs)
    owner = claim_research_batch(
        shared,
        work_keys=(intent.work_key,),
        now=DAY_1,
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    assert len(owner) == 1
    assert not claim_research_batch(
        shared,
        work_keys=(intent.work_key,),
        now=DAY_1,
        lease_for=timedelta(minutes=5),
        max_batch_size=1,
    )
    assert complete_research_batch(
        shared, claimed=owner, completed_at=DAY_1 + timedelta(minutes=1)
    ) == (intent.work_key,)
    assert not complete_research_batch(
        shared, claimed=owner, completed_at=DAY_1 + timedelta(minutes=2)
    )


def test_shared_work_with_incompatible_context_is_not_attached(tmp_path: Path):
    _, _, item, _ = setup(tmp_path)
    shared = SqliteSharedObservationWorkMemory(tmp_path / "shared.sqlite3")
    intent = SharedObservationIntent(
        item.organization_id,
        "s:1",
        "demand",
        ("public-evidence",),
        "policy",
        "1",
        "different-source-scope",
    )
    shared.enqueue(intent, opaque_requester_ref("server", "owner"))
    shared.replace_prime_authority(
        PrimeResearchAuthority(
            item.organization_id,
            "s:1",
            frozenset({intent.work_key}),
            DAY_1 - timedelta(minutes=1),
            "obs:public",
            DAY_1 + timedelta(days=3),
            "temporal",
            "1",
        )
    )
    assert compatible_shared_key(shared, item) is None
