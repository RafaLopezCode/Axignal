"""Demand precision (spec 092): another activity under a CPV group, and doubtful calls first.

Found by the self-check (2026-10-17): a social-programme notice coded "social research"
(79315000, under "market research") reached an economic intelligence firm, and building
maintenance or works calls carrying a green-area code reached a landscaper unjudged.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.findings import (
    MAIN,
    ProcurementRecord,
    classified_as,
    cpv_other_activity,
)
from application.observation_intelligence.loop import code_within as loop_within
from application.world_demand.fit import doubt, open_pairs
from application.world_demand.index import code_within
from tests.world_demand.test_live_demand import NOW, OPEN


def cpv(code: str) -> TaxonomyCode:
    return TaxonomyCode("CPV", code)


RESEARCH = (cpv("79310000"),)
GREEN = (cpv("77310000"),)


def _call(
    rid: str, codes: tuple[str, ...], mains: tuple[str, ...] = (), days_ago: int = 3
) -> ProcurementRecord:
    return ProcurementRecord(
        record_id=rid, source_id="es-placsp", kind=OPEN, title=rid, buyer_name="B",
        places=(TaxonomyCode("GEO", "EU/ES"),), demand_codes=tuple(cpv(c) for c in codes),
        published_at=NOW - timedelta(days=days_ago), source_url=f"https://example.org/{rid}",
        deadline="2026-11-01", main_codes=tuple(cpv(c) for c in mains),
    )  # fmt: skip


def test_social_research_is_not_market_research_but_stays_askable() -> None:
    assert cpv_other_activity("79315000", "79310000")
    assert not cpv_other_activity("79311000", "79310000")
    for within in (code_within, loop_within):
        assert not within(cpv("79315000"), cpv("79310000"))
        assert within(cpv("79311400"), cpv("79310000"))
        assert within(cpv("79315000"), cpv("79315000"))  # asking for it still matches
    family = _call("familiaK", ("79315000", "85312400"), mains=("79315000", "85312400"))
    assert classified_as(family, RESEARCH) != MAIN


def test_doubtful_calls_are_judged_first() -> None:
    gardens = _call("parques", ("77310000",), days_ago=1)
    building = _call("edificio", ("50000000", "77311000"), days_ago=5)
    works = _call("obras", ("45112000", "77314000"), days_ago=9)
    declared = _call("canal", ("50000000", "77310000"), mains=("77310000",), days_ago=0)
    extra = _call("extra", ("90000000", "77310000"), mains=("90000000",), days_ago=0)
    assert [doubt(r, GREEN) for r in (building, works, gardens, declared, extra)] == [0, 0, 1, 2, 3]
    order = [r.record_id for r, _ in open_pairs(
        [gardens, building, works, declared, extra], [("landscaping", GREEN)], today="2026-10-17"
    )]  # fmt: skip
    assert order == ["edificio", "obras", "parques", "canal", "extra"]


def test_a_second_main_object_that_is_other_work_is_doubtful() -> None:
    two = _call("two", ("79311000", "85312400"), mains=("79311000", "85312400"))
    assert doubt(two, RESEARCH) == 0
    assert (
        doubt(
            replace(two, demand_codes=(cpv("79311000"),), main_codes=(cpv("79311000"),)), RESEARCH
        )
        == 2
    )
