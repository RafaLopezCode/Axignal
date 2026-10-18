"""Common Crawl (spec 101): open-corpus capture, gently and off the read path."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.open_corpus import corpus_discoveries
from pipeline.open_corpus.common_crawl import CommonCrawlIndex, NotCaptured
from tools.runtime.common_crawl import CommonCrawlRunner, common_crawl_from_values

NOW = datetime(2026, 10, 19, 9, tzinfo=UTC)
CRAWLS = ["CC-MAIN-2026-39", "CC-MAIN-2026-34", "CC-MAIN-2026-30", "CC-MAIN-2026-25"]


def transport_for(captured: dict[str, list[str]], busy: set[str] = frozenset()):  # type: ignore[assignment]
    calls: list[str] = []

    def transport(url: str) -> bytes:
        calls.append(url)
        if url.endswith("collinfo.json"):
            return json.dumps([{"id": c} for c in CRAWLS]).encode()
        crawl = url.split("index.commoncrawl.org/")[1].split("-index")[0]
        if crawl in busy:
            raise urllib.error.HTTPError(url, 504, "busy", None, None)  # type: ignore[arg-type]
        statuses = captured.get(crawl)
        if not statuses:
            raise NotCaptured
        return "\n".join(json.dumps({"status": s}) for s in statuses).encode()

    return transport, calls


def test_index_counts_ok_captures_and_reads_404_as_none() -> None:
    transport, _ = transport_for({"CC-MAIN-2026-39": ["200", "200", "301"]})
    index = CommonCrawlIndex(transport=transport)
    assert index.crawls()[0] == "CC-MAIN-2026-39"
    found = index.captures("CC-MAIN-2026-39", "goiko.com")
    assert (found.captures, found.ok, found.capped) == (3, 2, False)
    assert index.captures("CC-MAIN-2026-34", "goiko.com").captures == 0


def test_runner_measures_three_crawls_off_the_read_path(tmp_path: Path) -> None:
    transport, calls = transport_for({"CC-MAIN-2026-39": ["200"] * 5, "CC-MAIN-2026-30": ["200"]})
    runner = CommonCrawlRunner(
        CommonCrawlIndex(transport=transport), tmp_path / "c.sqlite3", clock=lambda: NOW
    )
    runner.request("goiko.com")
    assert runner.measurement("goiko.com") is None and calls == []
    assert runner.run() == 1
    assert "limit=1000" in calls[1] and "limit=1" in calls[2] and len(calls) == 4  # 3 crawls + list
    found = corpus_discoveries(runner.measurement("goiko.com") or {}, observed_at="")
    assert [d["code"] for d in found] == ["OPEN_CORPUS_CAPTURED"]
    detail = found[0]["detail"]
    assert isinstance(detail, dict)
    assert detail["okCaptures"] == 5 and detail["capturedInPrevious"] == 1
    assert detail["conditions"]["crawl"] == "CC-MAIN-2026-39" and detail["uncertainty"]


def test_absent_from_the_latest_crawl_is_said_as_such(tmp_path: Path) -> None:
    transport, _ = transport_for({})
    runner = CommonCrawlRunner(
        CommonCrawlIndex(transport=transport), tmp_path / "c.sqlite3", clock=lambda: NOW
    )
    runner.request("biocultor.com")
    runner.run()
    found = corpus_discoveries(runner.measurement("biocultor.com") or {}, observed_at="")
    assert [(d["code"], d["epistemicState"]) for d in found] == [
        ("OPEN_CORPUS_NOT_CAPTURED", "OBSERVED")
    ]


def test_a_busy_index_is_unknown_never_absence(tmp_path: Path) -> None:
    clock = [NOW]
    transport, calls = transport_for({"CC-MAIN-2026-39": ["200"]}, busy={"CC-MAIN-2026-34"})
    runner = CommonCrawlRunner(
        CommonCrawlIndex(transport=transport), tmp_path / "c.sqlite3", clock=lambda: clock[0]
    )
    runner.request("huel.com")
    assert runner.run() == 0 and runner.measurement("huel.com") is None
    asked = len(calls)
    assert runner.run() == 0 and len(calls) == asked  # backing off
    clock[0] = NOW + timedelta(hours=4)
    with pytest.raises(AssertionError):
        assert runner.run() == 1  # still busy: stays unknown


def test_on_unless_turned_off(tmp_path: Path) -> None:
    assert common_crawl_from_values({}, tmp_path) is not None
    assert common_crawl_from_values({"AXIGNAL_COMMON_CRAWL_ENABLED": "false"}, tmp_path) is None
