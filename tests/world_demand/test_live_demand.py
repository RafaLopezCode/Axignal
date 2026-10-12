"""Open demand is matched again at read time: open calls only, all of them, new ones marked."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from application.observation_intelligence.contracts import SourceCapability, TaxonomyCode
from application.observation_intelligence.findings import ProcurementRecord
from application.world_demand.index import DemandSlice, SliceState
from application.world_demand.live import LiveDemandReader, apply_live_demand

NOW = datetime(2026, 10, 12, 9, tzinfo=UTC)
OPEN = SourceCapability.PUBLIC_PROCUREMENT_OPPORTUNITIES
ENERGY = {"capabilityId": "energy-supply", "demandCodes": [["CPV", "09310000"]]}
SCOPES = ["EU/ES"]


def _record(
    rid: str, cpv: str, deadline: str | None, published_days_ago: int, place: str = "EU/ES/ES3/ES30"
) -> ProcurementRecord:
    return ProcurementRecord(
        record_id=rid, source_id="es-placsp", kind=OPEN, title=f"Suministro {rid}",
        buyer_name="Ayuntamiento", places=(TaxonomyCode("GEO", place),),
        demand_codes=(TaxonomyCode("CPV", cpv),),
        published_at=NOW - timedelta(days=published_days_ago),
        source_url=f"https://contrataciondelestado.es/{rid}", deadline=deadline,
    )  # fmt: skip


class Store:
    def __init__(
        self,
        records: list[ProcurementRecord],
        *,
        complete: bool = True,
        age: timedelta = timedelta(hours=3),
    ) -> None:
        self._records = tuple(records)
        self._complete = complete
        self._age = age
        self.reads = 0

    def state(self, item: DemandSlice) -> SliceState | None:
        if item.source_id != "es-placsp":
            return None
        return SliceState(
            item,
            NOW - self._age,
            NOW - timedelta(days=30),
            self._complete,
            1,
            len(self._records),
            NOW,
        )

    def records(self, item: DemandSlice) -> tuple[ProcurementRecord, ...]:
        self.reads += 1
        return self._records

    def demand(self, item: DemandSlice, *, now: datetime) -> None:
        return None


def _reader(store: Store) -> LiveDemandReader:
    return LiveDemandReader(store, sources=("ted-search-v3", "es-placsp"), clock=lambda: NOW)  # type: ignore[arg-type]


def test_only_open_matching_calls_in_the_market_are_returned_newest_first() -> None:
    store = Store([
        _record("open-old", "09310000", "2026-11-01", 20),
        _record("open-new", "09310000", "2026-10-20", 2),
        _record("closed", "09310000", "2026-10-01", 3),
        _record("no-deadline", "09310000", None, 1),
        _record("other-trade", "45000000", "2026-11-01", 1),
        _record("france", "09310000", "2026-11-01", 1, place="EU/FR"),
    ])  # fmt: skip
    live = _reader(store).read([ENERGY], SCOPES)
    assert live is not None
    assert [c["title"] for c in live.candidates] == ["Suministro open-new", "Suministro open-old"]
    assert (live.total, live.new) == (2, 1)
    assert all(c["epistemicState"] == "POTENTIAL" for c in live.candidates)


def test_an_incomplete_or_stale_slice_never_answers() -> None:
    for store in (Store([], complete=False), Store([], age=timedelta(days=3))):
        assert _reader(store).read([ENERGY], SCOPES) is None


def test_decoded_records_are_reused_until_the_slice_is_ingested_again() -> None:
    store = Store([_record("a", "09310000", "2026-11-01", 1)])
    reader = _reader(store)
    reader.read([ENERGY], SCOPES)
    reader.read([ENERGY], SCOPES)
    assert store.reads == 1


def _view(discoveries: list[dict[str, object]]) -> dict[str, object]:
    return {"discoveries": discoveries}


STORED = {
    "kind": "DEMAND", "code": "POTENTIAL_DEMAND", "statement": "Old", "epistemicState": "POTENTIAL",
    "sourceUrl": None, "excerpt": None, "observedAt": None, "detail": {"deadline": "2026-10-01"},
}  # fmt: skip
ACTIVITY = {"kind": "ACTIVITY", "code": "energy-supply", "detail": {}}
PROOF = {"capabilities": [ENERGY], "attentionScopes": [{"jurisdiction": "EU/ES"}]}


def test_the_view_replaces_frozen_demand_with_the_live_answer() -> None:
    store = Store([_record("open-new", "09310000", "2026-10-20", 2)])
    view = apply_live_demand(_view([ACTIVITY, STORED]), PROOF, _reader(store), now=NOW)
    demand = [d for d in view["discoveries"] if d["kind"] == "DEMAND"]  # type: ignore[union-attr,index]
    assert [d["statement"] for d in demand] == ["Suministro open-new"]
    assert view["demand"]["live"] is True and view["demand"]["new"] == 1  # type: ignore[index]


def test_without_a_live_answer_closed_calls_are_still_removed() -> None:
    view = apply_live_demand(_view([ACTIVITY, STORED]), PROOF, None, now=NOW)
    assert [d["kind"] for d in view["discoveries"]] == ["ACTIVITY"]  # type: ignore[union-attr,index]
    assert view["demand"] == {
        "live": False, "asOf": NOW.isoformat(), "total": 0, "new": 0, "preparing": False
    }  # fmt: skip


def test_an_observation_that_did_not_look_for_demand_is_left_as_it_is() -> None:
    store = Store([_record("open-new", "09310000", "2026-10-20", 2)])
    view = apply_live_demand(_view([ACTIVITY]), PROOF, _reader(store), now=NOW)
    assert view == {"discoveries": [ACTIVITY]}


def test_markets_the_subscriber_chose_direct_where_demand_is_looked_for() -> None:
    # No place was found by the observation (no demand discoveries), but the subscriber
    # chose Spain: the live answer is looked for there, and stays POTENTIAL.
    store = Store([_record("open-new", "09310000", "2026-10-20", 2)])
    proof = {"capabilities": [ENERGY], "attentionScopes": []}
    view = apply_live_demand(_view([ACTIVITY]), proof, _reader(store), now=NOW, directed=["EU/ES"])
    demand = [d for d in view["discoveries"] if d["kind"] == "DEMAND"]  # type: ignore[union-attr,index]
    assert [d["statement"] for d in demand] == ["Suministro open-new"]


class _Unprepared(Store):
    def __init__(self) -> None:
        super().__init__([])
        self.demanded: list[str] = []

    def state(self, item: DemandSlice) -> SliceState | None:
        return None

    def demand(self, item: DemandSlice, *, now: datetime) -> None:
        self.demanded.append(item.key)


def test_a_chosen_country_not_prepared_yet_is_demanded_and_said_to_be_preparing() -> None:
    store = _Unprepared()
    proof = {"capabilities": [ENERGY], "attentionScopes": []}
    view = apply_live_demand(_view([ACTIVITY]), proof, _reader(store), now=NOW, directed=["EU/PT"])  # type: ignore[arg-type]
    assert "es-placsp|EU/PT|PUBLIC_PROCUREMENT_OPPORTUNITIES" in store.demanded
    assert view["demand"]["preparing"] is True  # type: ignore[index]


def test_directed_markets_are_bounded_to_five_eu_member_states(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from types import SimpleNamespace

    import pytest

    from pipeline.first_observation.sqlite_store import SqliteFirstObservationStore
    from tools.runtime.first_observation import FirstObservationRuntime

    runtime = SimpleNamespace(
        store=SqliteFirstObservationStore(tmp_path / "fo.sqlite3"),
        _clock=SimpleNamespace(now=lambda: NOW),
    )
    context = SimpleNamespace(tenant_id="tenant-1")
    result = FirstObservationRuntime.set_demand_markets(
        runtime, context, "focus-1", ["EU/ES", "EU/PT", "EU/ES"]
    )  # type: ignore[arg-type]
    assert result == {"state": "success", "directed": ["EU/ES", "EU/PT"]}
    assert runtime.store.demand_markets("tenant-1", "focus-1") == ("EU/ES", "EU/PT")
    assert runtime.store.demand_markets("tenant-2", "focus-1") == ()  # never another tenant's
    for bad in (["US"], ["EU/XX"], [f"EU/{c}" for c in ("ES", "PT", "FR", "IT", "DE", "AT")]):
        with pytest.raises(ValueError):
            FirstObservationRuntime.set_demand_markets(runtime, context, "focus-1", bad)  # type: ignore[arg-type]
