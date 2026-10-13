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
