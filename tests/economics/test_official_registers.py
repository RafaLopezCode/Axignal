"""Official registers: exact identifiers only, the register's own figures, honest attribution."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.economics import register_discoveries, same_organization_name
from application.first_observation.registry_ids import registry_identifiers
from application.first_observation.site import read_page
from pipeline.economics.registries import OfficialRegisters

NOW = datetime(2026, 10, 13, tzinfo=UTC)

FRANCE = {"results": [{
    "siren": "797666591", "nom_complet": "AGENCE WEB KEOPZ (KEOPZ)",
    "nom_raison_sociale": "AGENCE WEB KEOPZ", "date_creation": "2013-10-01",
    "tranche_effectif_salarie": "11", "annee_tranche_effectif_salarie": "2023",
    "categorie_entreprise": "PME", "annee_categorie_entreprise": "2023",
    "etat_administratif": "A", "activite_principale": "62.02A",
    "nombre_etablissements_ouverts": 1,
    "finances": {"2023": {"ca": 1200000, "resultat_net": 90000},
                 "2024": {"ca": 1450000, "resultat_net": 110000}},
}]}  # fmt: skip
SEC = {"entityName": "ACME CORP", "facts": {"us-gaap": {
    "Revenues": {"units": {"USD": [
        {"val": 900, "start": "2024-01-01", "end": "2024-12-31", "form": "10-K", "fy": 2024,
         "filed": "2025-02-01", "accn": "a1"},
        {"val": 300, "start": "2025-07-01", "end": "2025-09-30", "form": "10-K", "fy": 2025,
         "filed": "2026-02-01", "accn": "a2"},
        {"val": 1000, "start": "2025-01-01", "end": "2025-12-31", "form": "10-K", "fy": 2025,
         "filed": "2026-02-01", "accn": "a2"},
        {"val": 1100, "start": "2025-01-01", "end": "2025-12-31", "form": "10-Q", "fy": 2025},
    ]}},
}}}  # fmt: skip


def _registers(tmp_path: Path, calls: list[str], key: str | None = None) -> OfficialRegisters:
    def fetch(url: str, headers: Any) -> Any:
        calls.append(url)
        if "recherche-entreprises" in url:
            return FRANCE
        if "companyfacts" in url:
            return SEC
        if "company-information" in url:
            assert headers["Authorization"].startswith("Basic ")
            return {"company_number": "01234567", "company_name": "ACME LIMITED",
                    "date_of_creation": "2001-05-04", "company_status": "active",
                    "sic_codes": ["73110"],
                    "accounts": {"last_accounts": {"type": "small", "made_up_to": "2025-03-31"}}}  # fmt: skip
        raise AssertionError(url)

    return OfficialRegisters(tmp_path / "r.sqlite3", fetch=fetch, companies_house_key=key,
                             clock=lambda: NOW)  # fmt: skip


def test_only_labelled_numbers_with_valid_check_digits_are_register_identifiers() -> None:
    assert registry_identifiers("RCS Lyon B 797 666 591 — capital 10 000 €") == [
        ("SIREN", "797666591")
    ]
    assert registry_identifiers("SIREN 797 666 592") == []  # check digit fails
    assert registry_identifiers("Registered in England and Wales No. 1234567") == [
        ("COMPANIES_HOUSE", "01234567")
    ]
    assert registry_identifiers("Org.nr. 923 609 016 MVA") == [("ORGNR", "923609016")]
    assert registry_identifiers("Call 923 609 016 or order 01234567") == []


def test_the_site_reader_declares_them_as_identifiers() -> None:
    html = "<html><body><footer>KEOPZ SAS · RCS Lyon 797 666 591</footer></body></html>"
    page = read_page(url="https://keopz.fr/", html=html, observed_at=NOW,
                     content_fingerprint="f", artifact_ref=None)  # fmt: skip
    assert [(i.scheme, i.value) for i in page.identifiers] == [("SIREN", "797666591")]


def test_france_gives_latest_accounts_size_and_band_cached(tmp_path: Path) -> None:
    calls: list[str] = []
    registers = _registers(tmp_path, calls)
    record = registers.record("SIREN", "797666591")
    assert record is not None and record["name"] == "AGENCE WEB KEOPZ"
    facts = record["facts"]
    assert facts["revenue"] == {"value": 1450000, "year": "2024", "unit": "EUR"}
    assert facts["employeesBand"]["value"] == "10-19"
    assert facts["sizeCategory"]["value"] == "PME" and facts["status"]["value"] == "ACTIVE"
    registers.record("SIREN", "797666591")
    assert len(calls) == 1  # cached per identifier


def test_sec_reads_the_latest_annual_10k_not_a_quarter(tmp_path: Path) -> None:
    record = _registers(tmp_path, []).record("SEC_CIK", "1045810")
    assert record is not None
    assert record["facts"]["revenue"]["value"] == 1000
    assert record["facts"]["revenue"]["period"] == "2025-12-31"


def test_companies_house_needs_the_operators_key(tmp_path: Path) -> None:
    assert "COMPANIES_HOUSE" not in _registers(tmp_path, []).schemes
    assert _registers(tmp_path, []).record("COMPANIES_HOUSE", "01234567") is None
    record = _registers(tmp_path / "k", [], key="secret").record("COMPANIES_HOUSE", "01234567")
    assert record is not None and record["facts"]["accountsType"]["value"] == "small"


def test_names_must_match_for_an_observed_attribution(tmp_path: Path) -> None:
    assert same_organization_name("AGENCE WEB KEOPZ", ["Agence Web Keopz SAS"])
    assert same_organization_name("NVIDIA CORP", ["NVIDIA Corporation"])
    assert not same_organization_name("DANONE", ["Keopz"])
    record = _registers(tmp_path, []).record("SIREN", "797666591")
    assert record is not None
    observed = register_discoveries(record, attributed=True, via="REGISTER_ID_ON_WEBSITE",
                                    observed_at="x")  # fmt: skip
    assert observed[0]["code"] == "REGISTER:SIREN:revenue"
    assert observed[0]["epistemicState"] == "OBSERVED"
    assert observed[0]["detail"]["sourceKind"] == "OFFICIAL_REGISTER"
    potential = register_discoveries(record, attributed=False, via="REGISTER_ID_ON_WEBSITE",
                                     observed_at="x")  # fmt: skip
    assert {d["epistemicState"] for d in potential} == {"POTENTIAL"}
    assert potential[0]["detail"]["attributedBy"].endswith("_NAME_NOT_CONFIRMED")


def test_a_registered_name_starting_with_its_own_domain_name_matches() -> None:
    assert same_organization_name("VIPPS MOBILEPAY AS", ["vipps"])
    assert same_organization_name("ALAN", ["alan.com"])
    assert not same_organization_name("MOBILEPAY VIPPS AS", ["acme"])
