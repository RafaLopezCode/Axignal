"""Mozilla HTTP Observatory grade (spec 106): measured off the read path, failures unknown."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.web_quality import security_discoveries
from pipeline.web_quality.observatory import HttpObservatory
from tools.runtime.security_grade import SecurityGradeRunner, security_grade_from_values

NOW = datetime(2026, 10, 19, 9, tzinfo=UTC)
SCAN = {"grade": "D", "score": 35, "tests_passed": 9, "tests_failed": 3, "tests_quantity": 12,
        "scanned_at": "2026-10-19T08:21:27Z", "details_url": "https://developer.mozilla.org/en-US/observatory/analyze?host=biocultor.com",
        "error": None}  # fmt: skip


def test_the_scan_keeps_its_grade_score_checks_and_public_report() -> None:
    sent: list[str] = []

    def transport(url: str) -> bytes:
        sent.append(url)
        return json.dumps(SCAN).encode()

    scan = HttpObservatory(transport=transport).scan("www.biocultor.com")
    assert "host=www.biocultor.com" in sent[0]
    assert (scan["grade"], scan["score"], scan["testsPassed"], scan["testsQuantity"]) == (
        "D",
        35,
        9,
        12,
    )
    with pytest.raises(ValueError):
        HttpObservatory(transport=lambda _: json.dumps({"error": "site-down"}).encode()).scan(
            "x.es"
        )


class Fake:
    instrument = "fake-observatory"

    def __init__(self, fail: bool = False) -> None:
        self.fail, self.calls = fail, 0

    def scan(self, host: str) -> dict[str, object]:
        self.calls += 1
        if self.fail:
            raise ValueError("down")
        return HttpObservatory(transport=lambda _: json.dumps(SCAN).encode()).scan(host)


def test_runner_scans_off_the_read_path_shares_30_days_and_backs_off(tmp_path: Path) -> None:
    clock = [NOW]
    scanner = Fake()
    runner = SecurityGradeRunner(scanner, tmp_path / "s.sqlite3", clock=lambda: clock[0])
    runner.request("www.biocultor.com")
    assert runner.measurement("www.biocultor.com") is None and scanner.calls == 0
    assert runner.run() == 1
    found = security_discoveries(runner.measurement("www.biocultor.com") or {}, observed_at="")
    assert [(d["code"], d["statement"], d["epistemicState"]) for d in found] == [
        ("SECURITY_HEADERS_GRADE", "D", "OBSERVED")
    ]
    detail = found[0]["detail"]
    assert (
        isinstance(detail, dict) and detail["uncertainty"] and detail["notSearchPosition"] is True
    )
    clock[0] = NOW + timedelta(days=29)
    runner.request("www.biocultor.com")
    assert runner.run() == 0 and scanner.calls == 1
    down = Fake(fail=True)
    flaky = SecurityGradeRunner(down, tmp_path / "f.sqlite3", clock=lambda: clock[0])
    flaky.request("goiko.com")
    assert flaky.run() == 0 and flaky.run() == 0 and down.calls == 1
    assert flaky.measurement("goiko.com") is None


def test_on_unless_turned_off(tmp_path: Path) -> None:
    assert security_grade_from_values({}, tmp_path) is not None
    assert security_grade_from_values({"AXIGNAL_SECURITY_GRADE_ENABLED": "false"}, tmp_path) is None
