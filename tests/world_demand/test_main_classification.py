"""A call is matched by any of its codes, but it is said whether it is mainly about the activity.

Found on AXIGNAL itself (flywheel, 2026-10-15): an electricity supply listing "survey
services" as an additional code was shown to a market-research firm as its opportunity.
The rule holds for every organization and every source that publishes the main object.
"""

from __future__ import annotations

import json
from datetime import timedelta

from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.findings import (
    ADDITIONAL,
    MAIN,
    ProcurementRecord,
    classified_as,
)
from application.world_demand.live import apply_live_demand
from pipeline.observation_intelligence import parse_notices
from pipeline.observation_intelligence.placsp import parse_feed
from pipeline.world_demand.sqlite_store import _decode, _encode
from tests.observation_intelligence.test_placsp import FIXTURE
from tests.world_demand.test_live_demand import NOW, OPEN, SCOPES, Store, _reader

SURVEYS = (TaxonomyCode("CPV", "79310000"), TaxonomyCode("CPV", "79320000"))
#: TED prefixes "Country, en dash, main category, en dash" to its titles.
DASH = f" {chr(0x2013)} "
RESEARCH = {"capabilityId": "market-research", "demandCodes": [["CPV", "79310000"]]}


def _call(
    rid: str,
    codes: tuple[str, ...],
    *,
    main: tuple[str, ...] = (),
    nature: str | None = None,
    source: str = "es-placsp",
    title: str | None = None,
    days_ago: int = 3,
) -> ProcurementRecord:
    return ProcurementRecord(
        record_id=rid, source_id=source, kind=OPEN, title=title or f"Contrato {rid}",
        buyer_name="Ayuntamiento", places=(TaxonomyCode("GEO", "EU/ES/ES3/ES30"),),
        demand_codes=tuple(TaxonomyCode("CPV", c) for c in codes),
        published_at=NOW - timedelta(days=days_ago),
        source_url=f"https://contrataciondelestado.es/{rid}", deadline="2026-11-01",
        main_codes=tuple(TaxonomyCode("CPV", c) for c in main), contract_nature=nature,
    )  # fmt: skip


def test_the_main_object_decides_main_or_additional_and_unknown_stays_unknown() -> None:
    electricity = _call("e", ("09310000", "79311000"), main=("09310000",))
    assert classified_as(electricity, SURVEYS) == ADDITIONAL
    assert classified_as(_call("s", ("79311000",), main=("79311000",)), SURVEYS) == MAIN
    # A parent group ("market and economic research") is about the activity ...
    assert classified_as(_call("g", ("79311000",), main=("79300000",)), SURVEYS) == MAIN
    # ... a whole division ("business services") is too broad to say either way.
    assert classified_as(_call("d", ("79311000",), main=("79000000",)), SURVEYS) is None
    # ... unless a specific main object names something else (foster-family services).
    social = _call("f", ("79311000", "85312000"), main=("79000000", "85312000"))
    assert classified_as(social, SURVEYS) == ADDITIONAL
    # Without a main code, a declared nature the activity cannot have says it too.
    assert classified_as(_call("n", ("79311000",), nature="SUPPLIES"), SURVEYS) == ADDITIONAL
    assert classified_as(_call("v", ("79311000",), nature="SERVICES"), SURVEYS) is None
    assert classified_as(_call("u", ("79311000",)), SURVEYS) is None  # unknown, never ADDITIONAL
    assert classified_as(electricity, (TaxonomyCode("NAICS", "541910"),)) is None


def test_ted_publishes_the_main_object_and_nature_per_procedure_and_lot() -> None:
    notice = {
        "publication-number": "1-2026", "notice-type": "cn-standard", "notice-title": {"spa": "x"},
        "classification-cpv": ["09310000", "79311000"], "publication-date": "2026-10-01+02:00",
        "main-classification-proc": ["09310000"], "main-classification-lot": ["09310000", "79311000"],
        "contract-nature": ["supplies", "supplies"],
    }  # fmt: skip
    (record,) = parse_notices({"notices": [notice]})
    assert [c.code for c in record.main_codes] == ["09310000", "79311000"]
    assert record.contract_nature == "SUPPLIES"
    # A lot mainly about surveys is an opportunity mainly about surveys.
    assert classified_as(record, SURVEYS) == MAIN
    (mixed,) = parse_notices({"notices": [{**notice, "contract-nature": ["supplies", "works"]}]})
    assert mixed.contract_nature is None


def test_placsp_declares_the_contract_nature() -> None:
    records, _next, _oldest = parse_feed(FIXTURE.read_bytes())
    assert {r.contract_nature for r in records} <= {"SUPPLIES", "SERVICES", "WORKS", None}
    assert any(r.contract_nature is not None for r in records)


def test_calls_about_something_else_are_said_so_and_shown_last() -> None:
    store = Store([
        _call("electricity", ("09310000", "79311000"), main=("09310000",), days_ago=1),
        _call("survey", ("79311000",), main=("79311000",), days_ago=20),
        _call("unknown", ("79311000",), days_ago=20),
    ])  # fmt: skip
    live = _reader(store).read([RESEARCH], SCOPES)
    assert live is not None
    order = [(c["title"], c["classifiedAs"]) for c in live.candidates]
    # Newest first still holds, but never above a call mainly about the activity.
    assert order[-1] == ("Contrato electricity", ADDITIONAL)
    assert {o[1] for o in order[:2]} == {MAIN, None}
    assert live.additional == 1 and live.total == 3

    view: dict[str, object] = {"discoveries": [{"kind": "DEMAND", "code": "POTENTIAL_DEMAND"}]}
    view = apply_live_demand(
        view,
        {"capabilities": [RESEARCH], "attentionScopes": [{"jurisdiction": "EU/ES"}]},
        _reader(store),
        now=NOW,
    )
    assert view["demand"]["additional"] == 1  # type: ignore[index]


def test_the_national_entry_keeps_what_ted_says_about_the_main_object() -> None:
    title = "Contratación del suministro de energía eléctrica"
    store = Store([
        _call("ted:1", ("09310000", "79311000"), main=("09310000",), source="ted-search-v3",
              title=f"España{DASH}Electricidad{DASH}{title}"),
        _call("placsp:1", ("09310000", "79311000"), title=title),
    ])  # fmt: skip
    live = _reader(store).read([RESEARCH], SCOPES)
    assert live is not None
    (kept,) = live.candidates
    assert kept["source"] == "es-placsp" and kept["classifiedAs"] == ADDITIONAL


def test_stored_records_keep_the_main_object_and_older_ones_read_as_unknown() -> None:
    record = _call("e", ("09310000", "79311000"), main=("09310000",), nature="SUPPLIES")
    assert _decode(json.loads(_encode(record))) == record
    older = json.loads(_encode(record))
    del older["main_codes"], older["contract_nature"]
    restored = _decode(older)
    assert restored.main_codes == () and restored.contract_nature is None
    assert classified_as(restored, SURVEYS) is None


def test_the_contract_nature_is_validated() -> None:
    try:
        _call("x", ("79311000",), nature="LEASE")
    except ValueError:
        return
    raise AssertionError("an unknown contract nature must be rejected")


def test_one_call_titled_differently_by_each_source_is_shown_once() -> None:
    # Found on AXIGNAL: TED and the national platform titled the same call differently
    # ("Compra Pública de Tecnología Innovadora..." vs "gestión inteligente de las
    # emergencias"); its eleven codes and deadline are the same.
    codes = ("72000000", "72224000", "79311000", "79411000")
    store = Store([
        _call("ted:2", codes, main=("72224000",), source="ted-search-v3",
              title=f"España{DASH}Consultoría{DASH}Compra Pública de Tecnología Innovadora"),
        _call("placsp:2", codes, title="gestión inteligente de las emergencias"),
        _call("placsp:3", (*codes[:2], "79311000"), title="otra licitación con otros códigos"),
    ])  # fmt: skip
    live = _reader(store).read([RESEARCH], SCOPES)
    assert live is not None
    titles = {c["title"]: c["classifiedAs"] for c in live.candidates}
    assert titles == {
        "gestión inteligente de las emergencias": ADDITIONAL,
        "otra licitación con otros códigos": None,
    }
    assert all("_allCodes" not in c for c in live.candidates)
