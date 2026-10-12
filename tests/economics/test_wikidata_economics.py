"""Economic magnitudes from Wikidata, resolved by LEI and shown as what the source states."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.economics import economic_discoveries
from pipeline.economics.wikidata import WikidataEconomics

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
LEI = "W38RGI023J3WT1HWRP32"


def _quantity(amount: str, unit: str, when: str, rank: str = "normal") -> dict[str, Any]:
    return {"rank": rank, "mainsnak": {"datavalue": {"value": {"amount": amount, "unit": f"http://www.wikidata.org/entity/{unit}"}}},
            "qualifiers": {"P585": [{"datavalue": {"value": {"time": when}}}]}}  # fmt: skip


ENTITIES = {
    "Q81230": {"labels": {"en": {"value": "Siemens"}}, "claims": {
        "P2139": [_quantity("+75636000000", "Q4916", "+2015-00-00T00:00:00Z"),
                  _quantity("+77769000000", "Q4916", "+2023-00-00T00:00:00Z")],
        "P2226": [_quantity("+111760000", "Q4916", "+2021-05-07T00:00:00Z"),
                  _quantity("+139800000000", "Q4917", "+2021-08-24T00:00:00Z")],
        "P1128": [_quantity("+999999", "1", "+2030-01-01T00:00:00Z", rank="deprecated"),
                  _quantity("+320000", "1", "+2023-09-30T00:00:00Z")],
        "P414": [{"rank": "normal", "mainsnak": {"datavalue": {"value": {"id": "Q151139"}}}}],
    }},
    "Q16984598": {"labels": {"en": {"value": "Siemens AG"}}, "claims": {}},
    "Q151139": {"labels": {"en": {"value": "Frankfurt Stock Exchange"}}},
}  # fmt: skip


def fetch(params: dict[str, str]) -> dict[str, Any]:
    if params["action"] == "query":
        lei = params["srsearch"].split("=", 1)[1]
        return {
            "query": {"search": [{"title": "Q81230"}, {"title": "Q16984598"}] if lei == LEI else []}
        }
    return {"entities": {q: ENTITIES[q] for q in params["ids"].split("|") if q in ENTITIES}}


def test_the_richest_item_is_read_latest_exact_date_wins_and_deprecated_is_ignored(
    tmp_path: Path,
) -> None:
    facts = WikidataEconomics(tmp_path / "w.sqlite3", fetch=fetch, clock=lambda: NOW).facts(LEI)
    assert facts["item"] == "Q81230" and facts["alsoCarryingLei"] == ["Q16984598"]
    values = facts["facts"]
    assert values["revenue"] == {
        "value": 77769000000.0,
        "unit": "Q4916",
        "year": "2023",
        "unitLabel": "EUR",
    }  # type: ignore[index]
    assert values["marketCapitalization"]["unitLabel"] == "USD"  # type: ignore[index]  # 2021-08 over 2021-05
    assert values["employees"]["value"] == 320000.0  # type: ignore[index]
    assert values["stockExchange"]["valueLabel"] == "Frankfurt Stock Exchange"  # type: ignore[index]


def test_an_lei_not_in_wikidata_gives_nothing(tmp_path: Path) -> None:
    facts = WikidataEconomics(tmp_path / "w.sqlite3", fetch=fetch, clock=lambda: NOW).facts(
        "9598008X362A8R6PTW48"
    )
    assert (
        facts["item"] is None and economic_discoveries(facts, verified=True, observed_at="x") == []
    )


def test_discoveries_state_their_source_year_and_attribution(tmp_path: Path) -> None:
    facts = WikidataEconomics(tmp_path / "w.sqlite3", fetch=fetch, clock=lambda: NOW).facts(LEI)
    found = economic_discoveries(facts, verified=False, observed_at=NOW.isoformat())
    revenue = next(d for d in found if d["code"] == "WIKIDATA:revenue")
    assert revenue["epistemicState"] == "POTENTIAL"  # LEI only declared on the website
    assert revenue["detail"]["sourceKind"] == "SECONDARY_COMMUNITY_EDITED"  # type: ignore[index]
    assert revenue["sourceUrl"] == "https://www.wikidata.org/wiki/Q81230"
