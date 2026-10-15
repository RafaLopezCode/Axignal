"""The excellence harness measures families deterministically and flags regressions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.evaluation.excellence import main, markdown, regressions, report, sample

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _d(kind: str, code: str, state: str = "OBSERVED", url: str = "https://s/") -> dict[str, Any]:
    return {"kind": kind, "code": code, "statement": code, "epistemicState": state,
            "sourceUrl": url, "observedAt": "2026-10-13", "detail": {}}  # fmt: skip


ROWS = [
    {"domain": "a.example", "country": "ES", "view": {"state": "READY", "discoveries": [
        _d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED"), _d("LANGUAGES", "LANGUAGES_PUBLISHED"),
        _d("GENERATIVE_VISIBILITY", "AI_NAMED"), _d("CREDENTIAL", "CERTIFICATION_CLAIMED", "DECLARED"),
        _d("SIGNIFICANT_UNKNOWN", "NO_PRESS_MENTION_FOUND", "UNKNOWN", url=""),
    ]}},
    {"domain": "b.example", "country": "DE", "view": None},
]  # fmt: skip


def test_report_measures_coverage_observability_and_states_per_family() -> None:
    out = report(ROWS, now=NOW)
    presence, value, reputation = (out["families"][f] for f in ("presence", "value", "reputation"))
    assert presence["coverage_pct"] == 50.0 and presence["observability"] == {
        "STRONG": 1,
        "UNKNOWN": 1,
    }
    assert value["by_state"] == {"DECLARED": 1}
    assert reputation["coverage_pct"] == 0.0 and reputation["observability"]["LIMITED"] == 1
    assert out["countries"]["DE"]["family_coverage_pct"] == 0.0
    assert "| presence | 50.0% |" in markdown(out)


def test_regressions_are_flagged_and_fail_the_command(tmp_path: Path) -> None:
    baseline = report(ROWS, now=NOW)
    baseline["families"]["value"]["coverage_pct"] = 90.0
    assert regressions(report(ROWS, now=NOW), baseline) == ["value: 90.0 -> 50.0"]
    views, base = tmp_path / "v.json", tmp_path / "b.json"
    views.write_text(json.dumps(ROWS), encoding="utf-8")
    base.write_text(json.dumps(baseline), encoding="utf-8")
    assert main(["report", str(views), "--baseline", str(base)]) == 1
    assert main(["report", str(views)]) == 0


def test_sample_is_reproducible_for_human_precision_review() -> None:
    first = sample(ROWS, "presence", 2)
    assert first == sample(ROWS, "presence", 2) and len(first) == 2
    assert all(item["verdict"] is None for item in first)


def test_buyers_report_routes_coverage_and_why_none() -> None:
    def buyer(*signals: tuple[str, str]) -> dict[str, Any]:
        return {"kind": "DEMAND", "code": "POTENTIAL_BUYER", "statement": "X",
                "epistemicState": "POTENTIAL", "sourceUrl": None, "observedAt": "t",
                "detail": {"signalTypes": sorted({t for t, _ in signals}),
                           "signals": [{"type": t, "basis": b} for t, b in signals]}}  # fmt: skip

    unknown = _d("SIGNIFICANT_UNKNOWN", "NO_BUYER_SIGNALS", "UNKNOWN")
    unknown["detail"] = {"hasCustomerProfile": False}
    rows = [
        {"domain": "a", "country": "ES", "view": {"discoveries": [
            buyer(("CUSTOMER_OF_COMPETITOR", "Shown as a client on the website of P"),
                  ("SIMILAR_TO_CUSTOMERS", "Wikidata places it")),
            buyer(("PUBLIC_BUYER_OF_CATEGORY", "Awarded 4 public contracts")),
        ]}},
        {"domain": "b", "country": "US", "view": {"discoveries": [unknown]}},
    ]  # fmt: skip
    out = report(rows, now=NOW)["buyers"]
    assert out["organizations_with_buyers"] == 1 and out["coverage_pct"] == 50.0
    assert out["organizations_by_route"] == {
        "CUSTOMER_OF_COMPETITOR:PORTFOLIO_PEER_WEBSITE": 1,
        "PUBLIC_BUYER_OF_CATEGORY": 1,
        "SIMILAR_TO_CUSTOMERS": 1,
    }
    assert out["with_multi_signal_candidates"] == 1 and out["median_candidates"] == 2
    assert out["unknown_reasons"] == {"NO_CUSTOMER_PROFILE": 1, "CUSTOMERS_WITHOUT_ROUTE": 0}
    assert "| US | 0/1 |" in markdown(report(rows, now=NOW))


def test_self_check_flags_false_positives_negatives_and_unrelated_demand() -> None:
    from tools.evaluation.self_check import TRUTH, evaluate

    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    reading = {"discoveries": [
        _d("PUBLIC_PRESENCE", "PUBLIC_WEBSITE_OBSERVED"),
        {"kind": "LANGUAGES", "code": "LANGUAGES_PUBLISHED", "statement": "de, en, es, fr, it, pt, x-default", "detail": {}},
        {"kind": "RELATIONSHIP", "code": "CLIENT_DECLARED", "statement": "Google Partner", "detail": {}},
        {"kind": "DEMAND", "code": "POTENTIAL_DEMAND", "statement": "x",
         "detail": {"title": "Servicio de campañas de publicidad", "codes": ["CPV:79341400"]}},
        {"kind": "DEMAND", "code": "POTENTIAL_DEMAND", "statement": "y",
         "detail": {"title": "Servicios de análisis de mercado", "codes": ["CPV:79310000"]}},
    ]}  # fmt: skip
    report = evaluate(reading, truth)
    by_id = {v["id"]: v for v in report["verdicts"]}
    assert by_id["presence.languages"]["status"] == "PASS"
    assert by_id["relationships.no_declared_clients"]["defect"] == "FALSE_POSITIVE"
    assert by_id["organization.identity_unverified"]["defect"] == "FALSE_NEGATIVE"
    demand = by_id["demand.relevant_to_its_activity"]
    assert demand["status"] == "FAIL" and len(demand["detail"]["unrelated"]) == 1
    assert by_id["value.industry"]["status"] == "NOT_MEASURED"  # nothing to judge it with
    assert report["accuracy"] is not None and 0 < report["accuracy"] < 100


def test_known_capabilities_read_the_catalogs_current_codes() -> None:
    from application.observation_intelligence.catalog import with_current_codes

    stored = {"capabilityId": "market-research", "demandCodes": [["CPV", "79300000"]]}
    codes = [c for _s, c in with_current_codes(stored)["demandCodes"]]  # type: ignore[union-attr]
    assert "79300000" not in codes and "79310000" in codes  # advertising (7934) no longer matches
    unknown = {"capabilityId": "something-else", "demandCodes": [["CPV", "1"]]}
    assert with_current_codes(unknown) is unknown
