"""Its sector's economy in its markets, from official statistics (spec 095)."""

from __future__ import annotations

from application.inxights import size_in_sector
from application.sector_economy import (
    apply_sector_economy,
    division_key,
    markets_of,
    sector_figures,
    sector_market_discoveries,
    size_class_of,
    table,
)


def test_the_table_is_official_and_covers_europe() -> None:
    data = table()
    assert "Eurostat" in data["source"] and data["licence"] == "Eurostat, CC BY 4.0"
    assert {"ES", "FR", "DE", "IT", "PT", "NL", "SE", "NO"} <= set(data["countries"])
    assert division_key(62) == "J62" and division_key(20) == "C20" and division_key(4) is None


def test_figures_sum_divisions_and_keep_unknown_unknown() -> None:
    one = sector_figures("FR", [62])
    two = sector_figures("FR", [62, 63])
    assert one is not None and two is not None
    assert two["enterprises"] > one["enterprises"] > 0
    assert two["turnoverPerPersonTeur"] == round(
        two["turnoverMeur"] * 1000 / two["personsEmployed"], 1
    )
    assert sector_figures("FR", [4]) is None  # no such division: unknown, never zero
    assert sector_figures("ZZ", [62]) is None
    greece = sector_figures("GR", [62])  # Eurostat writes Greece EL
    assert greece is not None and greece["enterprises"] == sector_figures("EL", [62])["enterprises"]  # type: ignore[index]


def test_markets_are_its_country_then_the_ones_it_looks_at() -> None:
    view = {"attentionScopes": [{"jurisdiction": "EU/ES/ES5"}, {"jurisdiction": "EU/FR"}]}
    assert markets_of(view, ["EU/PT", "EU/ES"]) == ["ES", "FR", "PT"]


def test_sector_market_is_about_the_sector_and_states_how_the_sector_was_read() -> None:
    (fact,) = sector_market_discoveries("J62_63", "REGISTER_ACTIVITY_CODE", ["FR"], observed_at="x")
    detail = fact["detail"]
    assert fact["kind"] == "ECONOMIC_FACT" and fact["code"] == "SECTOR_MARKET:FR"
    assert fact["epistemicState"] == "DECLARED"
    assert detail["aboutSector"] and detail["notAboutThisOrganization"]  # type: ignore[index]
    assert detail["fact"] == "sectorMarket" and detail["divisions"] == ["J62", "J63"]  # type: ignore[index]
    (read,) = sector_market_discoveries("J62_63", "WEBSITE_ACTIVITY", ["FR"], observed_at="x")
    assert read["epistemicState"] == "POTENTIAL"


def test_applied_from_the_same_industry_every_family_reads() -> None:
    view = {
        "attentionScopes": [{"jurisdiction": "EU/FR"}],
        "discoveries": [{"kind": "ECONOMIC_FACT", "code": "REGISTER:activity",
                         "detail": {"fact": "activity", "value": "NAF 62.02A"}}],
    }  # fmt: skip
    out = apply_sector_economy(view, {"capabilities": []})
    codes = [d["code"] for d in out["discoveries"]]
    assert "SECTOR_MARKET:FR" in codes


def _sector(**figures: object) -> dict[str, object]:
    return {"kind": "ECONOMIC_FACT", "code": "SECTOR_MARKET:FR", "observedAt": "2026-10-18",
            "detail": {"fact": "sectorMarket", "country": "FR", "year": "2024", **figures}}  # fmt: skip


SECTOR = _sector(
    enterprises=1000, turnoverMeur=500,
    bySize={"0-9": {"enterprises": 900, "turnoverMeur": 100}, "10-19": {"enterprises": 50, "turnoverMeur": 50},
            "20-49": {"enterprises": 30, "turnoverMeur": 100}, "50-249": {"enterprises": 15, "turnoverMeur": 150},
            "GE250": {"enterprises": 5, "turnoverMeur": 100}},
)  # fmt: skip


def test_size_in_sector_compares_with_its_size_class_and_the_whole_sector() -> None:
    revenue = {
        "kind": "ECONOMIC_FACT",
        "code": "REGISTER:revenue",
        "detail": {"fact": "revenue", "value": 20_000_000, "unit": "EUR", "year": "2023"},
    }
    band = {"kind": "ECONOMIC_FACT", "code": "REGISTER:employeesBand",
            "detail": {"fact": "employeesBand", "value": "50-99"}}  # fmt: skip
    (found,) = size_in_sector({"discoveries": [SECTOR, revenue, band]})
    values = found["detail"]["values"]  # type: ignore[index]
    assert found["code"] == "economics:SIZE_IN_SECTOR" and found["epistemicState"] == "POTENTIAL"
    assert values["timesSectorAverage"] == 40.0  # 20M against 0.5M
    assert values["timesSizeClassAverage"] == 2.0  # 20M against 10M
    assert values["shareAtLeastItsSize"] == 0.02  # 15 + 5 of 1000


def test_without_its_own_figures_there_is_no_comparison() -> None:
    assert size_in_sector({"discoveries": [SECTOR]}) == []
    assert size_class_of(None, "50-99") == "50-249" and size_class_of(300, None) == "GE250"
    assert size_class_of(None, None) is None
