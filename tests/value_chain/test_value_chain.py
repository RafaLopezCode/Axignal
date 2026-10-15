"""Value chain: the sector's buyers and suppliers (EU-27 table), and companies nearby."""

from __future__ import annotations

from datetime import date

from application.observation_intelligence.contracts import TaxonomyCode
from application.value_chain import (
    apply_value_chain,
    chain_organizations,
    company_industry,
    flows,
    industry_of_cpv,
    industry_of_nace,
    table,
)
from application.world_demand.awards import AwardRecord, is_company, normalized_name


def test_the_table_is_complete_and_sourced() -> None:
    data = table()
    assert data["source"].startswith("Eurostat naio_10_cp1750") and len(data["industries"]) == 64
    for entry in data["industries"].values():
        shares = [s for _k, s in entry["buyers"]]
        assert shares == sorted(shares, reverse=True) and sum(shares) <= 1.0001


def test_codes_resolve_to_industries() -> None:
    assert industry_of_nace("62.02A") == "J62_63"
    assert industry_of_nace("80.10Z") == "N80-82"
    assert industry_of_nace("06.100") == "B"
    assert industry_of_cpv("79710000") == "N80-82"
    assert industry_of_cpv("72000000") == "J62_63"
    assert industry_of_cpv("45000000") == "F"
    # Found on hamilton-medical.com (truth set): medical equipment is not pharmacy.
    assert industry_of_cpv("33100000") == "C31_32" and industry_of_cpv("33600000") == "C21"
    assert industry_of_cpv("") is None


def test_the_register_activity_code_wins_over_what_the_site_says() -> None:
    view = {"discoveries": [{"kind": "ECONOMIC_FACT", "code": "REGISTER:SIREN:activity",
                             "detail": {"value": "NAF 71.12B"}}]}  # fmt: skip
    assert company_industry(view, ["72000000"]) == ("M71", "REGISTER_ACTIVITY_CODE")
    assert company_industry({"discoveries": []}, ["72000000", "72200000", "45000000"]) == (
        "J62_63",
        "ACTIVITY_CPV_CODES",
    )


def test_sector_buyers_and_suppliers_are_potential_and_exclude_itself() -> None:
    proof = {"capabilities": [{"demandCodes": [["CPV", "79710000"]]}]}
    view = apply_value_chain({"observedAt": "x", "discoveries": []}, proof)
    by_code = {d["code"]: d for d in view["discoveries"]}
    buyers = by_code["VALUE_CHAIN_BUYERS"]
    assert buyers["epistemicState"] == "POTENTIAL" and buyers["kind"] == "DEMAND"
    sectors = [s["code"] for s in buyers["detail"]["sectors"]]
    assert "N80-82" not in sectors and "HOUSEHOLDS" in sectors
    assert by_code["VALUE_CHAIN_SUPPLIERS"]["kind"] == "RELATIONSHIP"


def _award(winner: str, tax: str | None, cpv: str, place: str = "EU/ES/ES3") -> AwardRecord:
    return AwardRecord(
        source_id="es-placsp", record_id=f"r-{winner}-{cpv}", lot="1", title="t",
        buyer_name="B", winner_name=winner, winner_id=tax, amount=1000.0, currency="EUR",
        awarded_on=date(2026, 9, 1), offers_received=2,
        demand_codes=(TaxonomyCode("CPV", cpv),), places=(TaxonomyCode("GEO", place),),
        source_url="https://contrataciondelestado.es/x",
    )  # fmt: skip


def test_companies_nearby_never_individuals_public_sectors_or_twice() -> None:
    industry = "N80-82"
    supplier_sector = next(s for s, _x in flows(industry, "suppliers") if s == "J62_63")
    assert supplier_sector == "J62_63"
    awards = [
        _award("Construcciones Norte SA", "A11111111", "45000000"),  # F buys from N80-82
        _award("Construcciones Norte SA", "A11111111", "45000000"),
        _award("Software Sur SL", "B22222222", "72000000"),  # J62_63 sells to N80-82
        _award("Juan Pérez García", "12345678Z", "72000000"),  # an individual: never
        _award("Abogados Lejos SLP", "B33333333", "79110000", place="EU/ES/ES7"),  # elsewhere
        _award("Asistencia Técnica SL", "B44444444", "75000000"),  # sells to the State
    ]
    area = [TaxonomyCode("GEO", "EU/ES/ES3")]
    found = chain_organizations(
        awards, industry,
        in_area=lambda a: any(p.within(z) for p in a.places for z in area),
        own_ids=set(), own_names=set(), normalize=normalized_name, observed_at="x",
    )  # fmt: skip
    names = {(d["code"], d["statement"]) for d in found}
    assert ("POTENTIAL_PRIVATE_CUSTOMER", "Construcciones Norte SA") in names
    assert ("POTENTIAL_SUPPLIER", "Software Sur SL") in names
    assert not any(n in {"Juan Pérez García", "Abogados Lejos SLP", "Asistencia Técnica SL"}
                   for _c, n in names)  # fmt: skip
    assert all(d["epistemicState"] == "POTENTIAL" for d in found)


def test_individuals_are_told_apart_from_companies() -> None:
    assert is_company("ACME SERVICIOS SL", "B12345674")
    assert not is_company("Juan Pérez García", "12345678Z")
    assert not is_company("John Smith", "X1234567L")
    assert is_company("Talleres Zitrón, S.A.", None)
    assert not is_company("María López", None)


def test_truth_set_findings_on_industries_and_legal_pages() -> None:
    # Found on securitas.com and ferrovial.com (truth set, 2026-10-15).
    from application.value_chain import (
        LEGAL_PAGE,
        wikidata_industry_classifies,
        wikidata_industry_nace,
    )

    assert LEGAL_PAGE.search("/en/about-us/securitas-digital-services--legal-documents/")
    assert LEGAL_PAGE.search("/privacy/") and not LEGAL_PAGE.search("/en/services/guarding/")
    # "Transport" (land, air or sea?) never names one organization's industry...
    assert not wikidata_industry_classifies("Q7590") and wikidata_industry_nace("Q7590") == "49"
    assert wikidata_industry_classifies("Q1116826") and wikidata_industry_nace("Q1116826") == "80"
    view = {"discoveries": [{"code": "WIKIDATA:industry", "detail": {"value": "Q7590"}}]}
    # ... so it falls through to what the website or its codes establish (here: nothing).
    assert company_industry(view, [], nace_of=lambda q: [wikidata_industry_nace(q) or ""]) is None
