"""World demand index: ingest a public slice once, answer many Foci locally (spec 063)."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from application.observation_intelligence.contracts import (
    QuerySpec,
    SourceCapability,
    TaxonomyCode,
    geo,
)
from application.world_demand.index import (
    DemandIndexPort,
    DemandSlice,
    WorldDemandIngestor,
    code_within,
    per_focus_requests,
    world_slice_requests,
)
from pipeline.world_demand.sqlite_store import SqliteWorldDemandIndex
from tests.first_observation import harness
from tests.first_observation.harness import NOW, SOLAR_ES, TENDERS, TedWorld, World, build, runtime
from tests.first_observation.test_first_observation_e2e import (
    _attend,
    _ledger,
    _pending_id,
    _view,
    discoveries,
)

SECOND_SOLAR = "https://sol-levante.example.com/"
_OPEN = SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES


def test_cpv_hierarchy_is_matched_by_significant_prefix() -> None:
    assert code_within(TaxonomyCode("CPV", "45261215"), TaxonomyCode("CPV", "45000000"))
    assert code_within(TaxonomyCode("CPV", "09332000"), TaxonomyCode("CPV", "09332000"))
    assert not code_within(TaxonomyCode("CPV", "45261215"), TaxonomyCode("CPV", "09332000"))
    assert not code_within(TaxonomyCode("NAICS", "61"), TaxonomyCode("CPV", "61000000"))


def test_second_focus_in_the_same_country_is_answered_from_the_world_index(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setitem(
        harness.PAGES,
        SECOND_SOLAR,
        harness.PAGES[SOLAR_ES].replace("Solaria Norte", "Sol Levante"),
    )
    world = World()
    facade = build(tmp_path, world)
    _attend(facade, tmp_path, "subject:first-es", SOLAR_ES)
    runtime(facade).drain()
    live_queries = len(world.ted.queries)
    assert live_queries >= 1  # nothing indexed yet: the live adapter answered
    # The covering slice was demanded by that question; ingestion runs off the
    # First Proof path and pages through every Spanish notice of each window once.
    assert runtime(facade).ingest_demanded() == 2  # open notices and awards
    assert world.ted.pages == [("EU/ES", 1), ("EU/ES", 1)]

    token, _ = _attend(facade, tmp_path, "subject:second-es", SECOND_SOLAR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert len(world.ted.queries) == live_queries  # no new per-Focus source request
    assert _ledger(view, "sourceRequests") == 0 and _ledger(view, "sourceCacheHits") >= 1
    (demand,) = discoveries(view, "DEMAND")
    assert demand["detail"]["title"] == TENDERS[0].title
    assert demand["sourceUrl"] == TENDERS[0].source_url  # original evidence, one click away


def test_an_incomplete_slice_never_answers(tmp_path: Path) -> None:
    many = tuple(
        replace(TENDERS[0], record_id=f"9{i:05d}-2026", title=f"Notice {i}") for i in range(150)
    )
    ted = TedWorld(extra=many)
    store = SqliteWorldDemandIndex(tmp_path / "index.sqlite3")
    item = DemandSlice("ted-search-v3", "EU/ES", _OPEN)
    store.demand(item, now=NOW)
    ingestor = WorldDemandIngestor(
        feeds={"ted-search-v3": ted}, store=store, clock=lambda: NOW, max_pages=1
    )
    (report,) = ingestor.run()
    assert (report.pages, report.complete) == (1, False)
    port = DemandIndexPort(store, None, clock=lambda: NOW)
    query = QuerySpec(
        demand_codes=(TaxonomyCode("CPV", "09332000"),),
        geographies=(geo("EU/ES"),),
        capabilities=frozenset({_OPEN}),
        published_since=NOW - timedelta(days=60),
    )
    assert port.covered("ted-search-v3", query) is None  # fail closed: fall back to live
    complete = WorldDemandIngestor(feeds={"ted-search-v3": ted}, store=store, clock=lambda: NOW)
    assert complete.ingest(item).complete is True
    assert port.covered("ted-search-v3", query) is not None


def test_slice_ingestion_is_orders_of_magnitude_cheaper_at_scale() -> None:
    # ESTIMATED model, inputs labelled: 1,000 Foci, 2 capabilities, 1 market, 2 demand
    # questions, daily DEMAND cadence vs 10 country slices x 2 notice kinds with an
    # ESTIMATED 300 new notices per slice per day at 100 per page.
    pull = per_focus_requests(foci=1000, capabilities=2, markets=1, questions=2, cadence_days=1)
    slices = world_slice_requests(slices=20, daily_notices_per_slice=300, page_size=100)
    assert (pull, slices) == (4000, 60)
    assert pull / slices > 60
