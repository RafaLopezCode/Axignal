"""One reading of an organization's own industry, shared by every consumer (golden set,
2026-10-14: head offices, legal pages and a missing Wikidata step misread six of thirty)."""

from __future__ import annotations

from typing import Any

from application.value_chain import LEGAL_PAGE, company_industry, non_operating


def _d(
    kind: str, code: str, statement: str = "", url: str = "https://x.example/", **detail: Any
) -> dict[str, Any]:
    return {"kind": kind, "code": code, "statement": statement, "sourceUrl": url, "detail": detail}


def _nace(qid: str) -> list[str]:
    return {"Q_HEAD_OFFICE": ["70.10"], "Q_GLASS": ["23.1"], "Q_SOFTWARE": ["62"]}.get(qid, [])


def test_a_head_office_register_code_never_decides_the_industry() -> None:
    view = {"discoveries": [
        _d("ECONOMIC_FACT", "REGISTER:SIREN:activity", value="NAF 70.10Z"),
        _d("ECONOMIC_FACT", "WIKIDATA:industry", value="Q_GLASS"),
    ]}  # fmt: skip
    assert non_operating("NAF 70.10Z") and non_operating("64.20") and not non_operating("62.01")
    assert company_industry(view, [], nace_of=_nace) == ("C23", "WIKIDATA_INDUSTRY")


def test_wikidata_comes_before_the_website_and_head_offices_are_skipped_there_too() -> None:
    web = _d("ACTIVITY", "web-design", routingCodes=["CPV:72413000"])
    view = {"discoveries": [_d("ECONOMIC_FACT", "WIKIDATA:industry", value="Q_SOFTWARE"), web]}
    assert company_industry(view, [], nace_of=_nace) == ("J62_63", "WIKIDATA_INDUSTRY")
    holding = {
        "discoveries": [_d("ECONOMIC_FACT", "WIKIDATA:industry", value="Q_HEAD_OFFICE"), web]
    }
    assert company_industry(holding, [], nace_of=_nace) == ("J62_63", "WEBSITE_ACTIVITY")


def test_legal_pages_do_not_vote_and_each_activity_votes_once() -> None:
    view = {"discoveries": [
        _d("ACTIVITY", "web-design", routingCodes=["CPV:72413000", "CPV:72212224"]),
        _d("ACTIVITY", "marketing-advertising", url="https://x.example/legal/",
           routingCodes=["CPV:79340000", "CPV:79341000", "CPV:79342000"]),
    ]}  # fmt: skip
    assert company_industry(view, [], nace_of=_nace) == ("J62_63", "WEBSITE_ACTIVITY")
    for path in ("/legal/", "/terms-of-service", "/aviso-legal", "/impressum", "/privacy-policy"):
        assert LEGAL_PAGE.search(path), path
    for path in ("/services/", "/legalTech", "/products/terminal"):
        assert not LEGAL_PAGE.search(path), path


def test_without_view_activities_the_stored_codes_still_answer() -> None:
    assert company_industry({"discoveries": []}, ["45000000"]) == ("F", "ACTIVITY_CPV_CODES")
    assert company_industry({"discoveries": []}, []) is None


def test_real_estate_reads_as_its_services_never_as_imputed_rents() -> None:
    from application.value_chain import industry_of_code, industry_of_nace

    assert industry_of_nace("68.20") == "L68B" and industry_of_code("68") == "L68B"
