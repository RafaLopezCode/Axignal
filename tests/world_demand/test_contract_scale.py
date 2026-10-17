"""How big a call is, and the organization's lead activity first (spec 081, CTO 2026-10-17).

Found on the canary: biocultor.com, a small shop whose lead activity is fertiliser supply
and whose secondary service is garden care, was shown 97 calls mixed together, among them
one-year municipal green-area maintenance contracts. Whether a call is within reach is the
person's judgment; AXIGNAL shows what the source publishes about its size (value, lots,
the smallest lot, duration), never as a filter or a score, and lists the lead activity first.
"""

from __future__ import annotations

from datetime import timedelta

from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.findings import (
    ContractScale,
    ProcurementRecord,
    duration_months,
)
from application.world_demand.live import LiveDemandReader
from pipeline.observation_intelligence.ted import _scale as ted_scale
from tests.world_demand.test_live_demand import NOW, OPEN, SCOPES, Store

FERTILISER = {"capabilityId": "fertilisers-soil-amendments", "demandCodes": [["CPV", "24440000"]]}
GARDENS = {"capabilityId": "landscaping-gardening", "demandCodes": [["CPV", "77310000"]]}


def _call(
    rid: str, cpv: str, scale: ContractScale | None = None, days_ago: int = 3
) -> ProcurementRecord:
    return ProcurementRecord(
        record_id=rid, source_id="es-placsp", kind=OPEN, title=f"Contrato {rid}",
        buyer_name="Ayuntamiento", places=(TaxonomyCode("GEO", "EU/ES/ES4/ES42"),),
        demand_codes=(TaxonomyCode("CPV", cpv),), published_at=NOW - timedelta(days=days_ago),
        source_url=f"https://contrataciondelestado.es/{rid}", deadline="2026-11-01", scale=scale,
    )  # fmt: skip


def test_durations_are_read_in_whole_months_and_unknown_stays_unknown() -> None:
    assert duration_months("3", "ANN") == 36 and duration_months("1", "YEAR") == 12
    assert duration_months("33", "MONTH") == 33 and duration_months("45", "DAY") == 2
    assert duration_months(None, "MONTH") is None and duration_months("2", "FORTNIGHT") is None
    assert duration_months("0", "MONTH") is None and duration_months("x", "MONTH") is None


def test_ted_scale_reads_total_lots_smallest_lot_and_duration() -> None:
    scale = ted_scale({
        "estimated-value-proc": "564231.36", "estimated-value-cur-proc": "EUR",
        "estimated-value-lot": ["494266.67", "34982.35", "34982.34"], "estimated-value-cur-lot": ["EUR"],
        "duration-period-value-lot": ["1", "1", "1"], "duration-period-unit-lot": ["YEAR"] * 3,
    })  # fmt: skip
    assert scale == ContractScale(564231.36, "EUR", 3, 34982.34, 12)
    # Lots without a published total are summed; a single lot is not "lots".
    summed = ted_scale({"estimated-value-lot": ["100", "50"], "estimated-value-cur-lot": ["EUR"]})
    assert summed is not None and summed.estimated_value == 150 and summed.smallest_lot_value == 50
    single = ted_scale({"estimated-value-proc": "277200", "estimated-value-cur-proc": "EUR"})
    assert single is not None and single.lots is None
    assert ted_scale({}) is None  # nothing published: unknown, never zero


def test_the_scale_travels_with_each_call_and_survives_storage() -> None:
    scale = ContractScale(1_057_079.94, "EUR", None, None, 12)
    assert ContractScale.from_wire(scale.to_wire()) == scale
    assert ContractScale.from_wire(None) is None
    live = LiveDemandReader(Store([_call("parques", "77310000", scale)]), sources=("es-placsp",),
                            clock=lambda: NOW).read([GARDENS], SCOPES)  # type: ignore[arg-type]  # fmt: skip
    assert live is not None
    (call,) = live.candidates
    assert call["scale"] == scale.to_wire() and "_lead" not in call
    unknown = LiveDemandReader(Store([_call("x", "77310000")]), sources=("es-placsp",),
                               clock=lambda: NOW).read([GARDENS], SCOPES)  # type: ignore[arg-type]  # fmt: skip
    assert unknown is not None and unknown.candidates[0]["scale"] is None


def test_the_lead_activity_comes_first_and_nothing_is_hidden() -> None:
    calls = [_call("parques", "77310000", days_ago=1), _call("abono", "24440000", days_ago=9)]
    live = LiveDemandReader(Store(calls), sources=("es-placsp",),
                            clock=lambda: NOW).read([FERTILISER, GARDENS], SCOPES)  # type: ignore[arg-type]  # fmt: skip
    assert live is not None
    assert [c["title"] for c in live.candidates] == ["Contrato abono", "Contrato parques"]
    assert live.total == 2


def test_placsp_reads_the_estimated_value_and_planned_duration() -> None:
    import xml.etree.ElementTree as ET
    from pathlib import Path

    from pipeline.observation_intelligence.placsp import _local, parse_entry

    feed = (
        Path(__file__).parents[1]
        / "observation_intelligence"
        / "fixtures"
        / "placsp-feed-sample.atom"
    )
    entries = [e for e in ET.parse(feed).getroot() if _local(e.tag) == "entry"]
    scales = {r.title[:30]: r.scale for e in entries if (r := parse_entry(e)) is not None}
    assert ContractScale(657591.0, "EUR", None, None, 36) in scales.values()
    assert all(s is None or s.estimated_value for s in scales.values())
