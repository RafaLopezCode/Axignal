"""Wikidata through the item its official website identifies (blocked or LEI-less sites)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.economics import economic_discoveries
from pipeline.economics.wikidata import WikidataEconomics

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _claim(value: Any) -> dict[str, Any]:
    return {"rank": "normal", "mainsnak": {"datavalue": {"value": value}}}


def test_an_item_identified_by_website_yields_magnitudes_lei_and_registers(tmp_path: Path) -> None:
    calls: list[dict[str, str]] = []

    def fetch(params: dict[str, str]) -> dict[str, Any]:
        calls.append(params)
        assert params["action"] != "query"  # no LEI search: the item is already known
        if params.get("props") == "labels":
            return {"entities": {}}
        return {"entities": {"Q1": {"labels": {"en": {"value": "Acme"}}, "claims": {
            "P1128": [_claim({"amount": "+1800", "unit": "1"})],
            "P1278": [_claim("969500BPSLCSC039UV67")],
            "P1616": [_claim("794598813")],
        }}}}  # fmt: skip

    store = WikidataEconomics(tmp_path / "w.sqlite3", fetch=fetch, clock=lambda: NOW)
    facts = store.facts_for_item("Q1")
    assert facts["item"] == "Q1" and facts["lei"] == "969500BPSLCSC039UV67"
    assert facts["registers"] == {"SIREN": "794598813"}
    assert store.facts_for_item("Q1") == facts and len(calls) == 1  # cached
    (employees,) = economic_discoveries(facts, verified=False, observed_at="2026-10-13",
                                        attributed_by="OFFICIAL_WEBSITE_IN_WIKIDATA")  # fmt: skip
    assert employees["epistemicState"] == "POTENTIAL"
    assert employees["detail"]["attributedBy"] == "OFFICIAL_WEBSITE_IN_WIKIDATA"


def test_the_stated_industry_answers_value_only_when_nothing_else_does() -> None:
    from application.economics import stated_industry
    from application.regulation.sectors import route_of, section_of_label

    industry = {"kind": "ECONOMIC_FACT", "code": "WIKIDATA:industry", "statement": "software industry",
                "sourceUrl": "https://www.wikidata.org/wiki/Q1", "detail": {"fact": "industry"}}  # fmt: skip
    unknown = {"kind": "SIGNIFICANT_UNKNOWN", "code": "ACTIVITY_NOT_ESTABLISHED"}
    out = stated_industry([unknown, industry])
    activity = out[-1]
    assert activity["code"] == "STATED_INDUSTRY" and activity["epistemicState"] == "POTENTIAL"
    assert route_of(activity) == "isic-J" and unknown not in out
    website = {"kind": "ACTIVITY", "code": "isic-K"}
    assert stated_industry([website, industry]) == [website, industry]
    assert section_of_label("mechanical engineering") == "C"
    assert section_of_label("financial services") == "K"
    assert (
        stated_industry([{**industry, "statement": "Q112166002"}])[-1]["code"] != "STATED_INDUSTRY"
    )
