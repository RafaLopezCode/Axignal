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


def test_osm_confirmation_rules_are_fixed_in_advance() -> None:
    from tools.evaluation.osm_confirm import RULES, eligible, person_like

    assert RULES == ("WEBSITE_REQUIRED", "PERSON_FILTER")
    assert person_like("Maître Élodie Grisel", "M69_70") and person_like(
        "Alexandrina FERREIRA", "M69_70"
    )
    assert not person_like("Basman and Smith LLP", "M69_70") and not person_like("PwC", "M69_70")
    assert not person_like("Tischlerei Liebel", "F")  # the filter is for professional names only
    assert not eligible({"name": "Shop", "sector": "G47", "website": None})
    assert eligible({"name": "Shop", "sector": "G47", "website": "https://shop.example"})
