"""Website history from the Internet Archive (spec 102)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from application.web_history import history_discoveries, summarize
from pipeline.web_history.wayback import WaybackIndex
from tools.runtime.wayback import WaybackRunner, wayback_from_values

NOW = datetime(2026, 10, 19, 9, tzinfo=UTC)
CAPTURES = [
    ("20021101120000", "200", "A"),
    ("20150301120000", "200", "A"),
    ("20251101120000", "200", "B"),
    ("20260201120000", "200", "B"),
    ("20260501120000", "200", "C"),
    ("20260901120000", "301", "-"),
]


def test_summary_is_a_lower_bound_and_counts_home_page_versions() -> None:
    summary = summarize(CAPTURES, today=date(2026, 10, 19))
    assert summary["firstCapture"] == "2002-11-01" and summary["lastCapture"] == "2026-09-01"
    assert summary["homeVersions"] == 3  # A, B, C among successful captures
    assert summary["homeVersionsLast12Months"] == 2  # B (Nov 2025) and C (May 2026)
    assert summarize([], today=date(2026, 10, 19)) == {"captures": 0}
    redirecting = [("20150301120000", "200", "A"), ("20260901120000", "301", "-")]
    assert summarize(redirecting, today=date(2026, 10, 19))["homeVersionsLast12Months"] is None


def test_index_reads_the_cdx_rows_after_the_header() -> None:
    calls: list[str] = []

    def transport(url: str) -> bytes:
        calls.append(url)
        return json.dumps(
            [["timestamp", "statuscode", "digest"], *[list(c) for c in CAPTURES]]
        ).encode()

    rows = WaybackIndex(transport=transport).monthly_captures("goiko.com")
    assert rows[0] == CAPTURES[0] and len(rows) == 6
    assert "collapse=timestamp%3A6" in calls[0] and "url=goiko.com" in calls[0]


class FakeArchive:
    instrument = "fake-archive"

    def __init__(self, captures: list[tuple[str, str, str]] | None, fail: bool = False) -> None:
        self.captures = captures or []
        self.fail = fail
        self.calls = 0

    def monthly_captures(self, host: str) -> list[tuple[str, str, str]]:
        self.calls += 1
        if self.fail:
            raise OSError("archive unavailable")
        return self.captures


def test_runner_measures_off_the_read_path_and_finds_history(tmp_path: Path) -> None:
    archive = FakeArchive(CAPTURES)
    runner = WaybackRunner(archive, tmp_path / "w.sqlite3", clock=lambda: NOW)
    runner.request("goiko.com")
    assert runner.measurement("goiko.com") is None and archive.calls == 0
    assert runner.run() == 1
    found = history_discoveries(runner.measurement("goiko.com") or {}, observed_at="")
    assert [(d["kind"], d["code"], d["statement"]) for d in found] == [
        ("OPERATING_SIGNAL", "WEBSITE_HISTORY", "2002-11-01")
    ]
    detail = found[0]["detail"]
    assert isinstance(detail, dict) and detail["uncertainty"] and detail["homeVersions"] == 3


def test_no_captures_is_said_and_an_outage_is_unknown(tmp_path: Path) -> None:
    runner = WaybackRunner(FakeArchive([]), tmp_path / "a.sqlite3", clock=lambda: NOW)
    runner.request("biocultor.com")
    runner.run()
    found = history_discoveries(runner.measurement("biocultor.com") or {}, observed_at="")
    assert [d["code"] for d in found] == ["WEBSITE_NOT_ARCHIVED"]
    clock = [NOW]
    down = FakeArchive(None, fail=True)
    flaky = WaybackRunner(down, tmp_path / "b.sqlite3", clock=lambda: clock[0])
    flaky.request("huel.com")
    assert flaky.run() == 0 and flaky.measurement("huel.com") is None
    assert flaky.run() == 0 and down.calls == 1  # backing off
    clock[0] = NOW + timedelta(hours=4)
    down.fail = False
    assert flaky.run() == 1


def test_on_unless_turned_off(tmp_path: Path) -> None:
    assert wayback_from_values({}, tmp_path) is not None
    assert wayback_from_values({"AXIGNAL_WAYBACK_ENABLED": "false"}, tmp_path) is None
