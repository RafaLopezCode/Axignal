"""INXIGHTs: deterministic crossings, cited evidence, recomputed, never a fact."""

from __future__ import annotations

from typing import Any

from application.inxights import RULES_VERSION, apply_inxights, same_name


def _d(kind: str, code: str, statement: str = "", **detail: Any) -> dict[str, Any]:
    return {"kind": kind, "code": code, "statement": statement, "epistemicState": "POTENTIAL",
            "sourceUrl": f"https://source/{code}", "observedAt": "2026-10-01", "detail": detail}  # fmt: skip


def _view(*discoveries: dict[str, Any], scope: str = "EU/ES/ES3") -> dict[str, Any]:
    return {"discoveries": list(discoveries), "attentionScopes": [{"jurisdiction": scope}]}


def _codes(view: dict[str, Any]) -> list[str]:
    return [d["code"] for d in view["discoveries"] if d["kind"] == "INXIGHT"]


BUYER_A = _d("DEMAND", "RECURRING_PUBLIC_BUYER", "Ayuntamiento A", contractsInArea=4)
BUYER_B = _d("DEMAND", "RECURRING_PUBLIC_BUYER", "Ministerio B", contractsInArea=3)


def test_local_buyers_and_competitors_with_them_are_crossed_and_cited() -> None:
    rival = _d("COMPETITION", "WINS_IN_SAME_CODES", "Rival SA", buyers=["Ministerio B", "Otro"])
    view = apply_inxights(_view(BUYER_A, BUYER_B, rival))
    found = {d["code"]: d for d in view["discoveries"] if d["kind"] == "INXIGHT"}
    local = found["demand:LOCAL_BUYERS_NEVER_AWARDED"]
    assert local["epistemicState"] == "POTENTIAL"
    assert local["detail"]["values"] == {"buyers": 2, "contracts": 7, "where": "AREA"}
    assert [e["statement"] for e in local["detail"]["evidence"]] == [
        "Ayuntamiento A",
        "Ministerio B",
    ]
    assert local["detail"]["rulesVersion"] == RULES_VERSION
    rivals = found["relationships:COMPETITORS_WIN_WITH_ITS_BUYERS"]
    assert rivals["detail"]["values"] == {"competitors": ["Rival SA"], "buyers": ["Ministerio B"]}


def test_inxights_are_recomputed_never_stacked_and_vanish_with_their_evidence() -> None:
    view = apply_inxights(_view(BUYER_A, BUYER_B))
    view = apply_inxights(view)
    assert _codes(view) == ["demand:LOCAL_BUYERS_NEVER_AWARDED"]
    view["discoveries"] = [d for d in view["discoveries"] if d.get("statement") != "Ministerio B"]
    assert _codes(apply_inxights(view)) == []  # one buyer is not a pattern


def test_ai_naming_its_competitors_is_crossed_with_award_winners() -> None:
    geo = _d("GENERATIVE_VISIBILITY", "AI_NOT_NAMED_FOR_CATEGORY", "0/2",
             competitorsNamed=["Eulen Seguridad", "Securitas"])  # fmt: skip
    rival = _d("COMPETITION", "WINS_IN_SAME_CODES", "EULEN SEGURIDAD S.A.", buyers=[])
    other = _d("COMPETITION", "WINS_IN_SAME_CODES", "VASBE, S.L.", buyers=[])
    found = apply_inxights(_view(geo, rival, other))["discoveries"][0]
    assert found["code"] == "presence:AI_NAMES_COMPETITORS_NOT_IT"
    assert found["detail"]["values"]["competitors"] == ["EULEN SEGURIDAD S.A."]
    assert same_name("NVIDIA Corporation", "NVIDIA Corp") and not same_name("Eulen", "Clece")


def test_public_weight_and_concentration_from_awards_and_official_revenue() -> None:
    revenue = _d("ECONOMIC_FACT", "REGISTER:SIREN:revenue", fact="revenue", value=1_000_000,
                 unit="EUR", sourceKind="OFFICIAL_REGISTER")  # fmt: skip
    won = [
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Metro", amount=400_000.0, currency="EUR"),
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "ADIF", amount=50_000.0, currency="EUR"),
        _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "RTVE", amount=50_000.0, currency="EUR"),
    ]
    found = {d["code"]: d for d in apply_inxights(_view(revenue, *won))["discoveries"]
             if d["kind"] == "INXIGHT"}  # fmt: skip
    assert found["economics:PUBLIC_CONTRACTS_WEIGHT"]["detail"]["values"]["share"] == 0.5
    assert found["relationships:PUBLIC_CLIENT_CONCENTRATION"]["detail"]["values"]["share"] == 0.8


def test_more_than_its_revenue_is_said_without_a_misleading_percentage() -> None:
    revenue = _d("ECONOMIC_FACT", "R", fact="revenue", value=100_000, unit="EUR")
    won = _d("RELATIONSHIP", "PUBLIC_CONTRACTS_WON", "Metro", amount=900_000.0, currency="EUR")
    found = apply_inxights(_view(revenue, won))["discoveries"][0]
    assert "exceed" in found["statement"] and "%" not in found["statement"]


def test_open_demand_without_declared_offer_and_unwatched_group_countries() -> None:
    gap = _d("REPRESENTATION_GAP", "OFFER_NOT_MACHINE_READABLE")
    tender = _d("DEMAND", "TED:1", "Ventilation works")
    group = _d("DECLARED_LOCATION", "GROUP_ENTITIES_IN_COUNTRIES", "DE, FR, ES",
               countries={"DE": 3, "FR": 1, "ES": 2})  # fmt: skip
    view = _view(gap, tender, group, scope="EU/ES")
    view["demandMarkets"] = {"directed": ["EU/FR"]}
    found = {d["code"]: d for d in apply_inxights(view)["discoveries"] if d["kind"] == "INXIGHT"}
    assert found["demand:OPEN_DEMAND_OFFER_NOT_DECLARED"]["detail"]["values"]["openCalls"] == 1
    assert found["markets:GROUP_COUNTRIES_DEMAND_UNWATCHED"]["detail"]["values"]["countries"] == [
        "DE"
    ]


def test_sector_news_without_it_and_founding_year_disagreement() -> None:
    headlines = [_d("CONTEXT_SIGNAL", "SECTOR_HEADLINE", f"h{i}") for i in range(3)]
    official = _d("ECONOMIC_FACT", "REGISTER:SIREN:inception", fact="inception", value="2019",
                  sourceKind="OFFICIAL_REGISTER")  # fmt: skip
    community = _d("ECONOMIC_FACT", "WIKIDATA:inception", fact="inception", value="1998",
                   sourceKind="SECONDARY_COMMUNITY_EDITED")  # fmt: skip
    codes = _codes(apply_inxights(_view(*headlines, official, community)))
    assert "reputation:SECTOR_IN_NEWS_NOT_IT" in codes
    assert "organization:FOUNDING_YEAR_SOURCES_DISAGREE" in codes
    mention = _d("MENTION", "PRESS_MENTION", "It is quoted")
    assert "reputation:SECTOR_IN_NEWS_NOT_IT" not in _codes(
        apply_inxights(_view(*headlines, mention))
    )


def test_malformed_evidence_silences_only_that_rule() -> None:
    broken = _d("DEMAND", "RECURRING_PUBLIC_BUYER", "X", contractsInArea="many")
    view = apply_inxights(_view(broken, BUYER_A, BUYER_B))
    assert isinstance(view["discoveries"], list)
