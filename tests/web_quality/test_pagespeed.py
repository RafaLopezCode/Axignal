"""PageSpeed Insights (spec 100): Lighthouse lab runs, measured off the read path."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.web_quality import lighthouse_discoveries
from pipeline.web_quality.pagespeed import PageSpeedInsights, summarize
from tools.runtime.pagespeed import PageSpeedRunner, pagespeed_from_values

NOW = datetime(2026, 10, 19, 9, tzinfo=UTC)


def payload(seo: float = 0.83) -> dict[str, object]:
    return {
        "lighthouseResult": {
            "lighthouseVersion": "12.8.2",
            "fetchTime": "2026-10-19T09:00:00.000Z",
            "finalDisplayedUrl": "https://www.biocultor.com/",
            "configSettings": {"formFactor": "mobile", "throttlingMethod": "simulate"},
            "categories": {
                "seo": {"score": seo, "auditRefs": [
                    {"id": "meta-description", "weight": 1}, {"id": "document-title", "weight": 1},
                    {"id": "structured-data", "weight": 0},
                ]},
                "performance": {"score": 0.41, "auditRefs": [{"id": "largest-contentful-paint", "weight": 25}]},
                "accessibility": {"score": 0.9, "auditRefs": []},
                "best-practices": {"score": None, "auditRefs": []},
            },
            "audits": {
                "meta-description": {"title": "Document does not have a meta description", "score": 0},
                "document-title": {"title": "Document has a `<title>` element", "score": 1},
                "structured-data": {"title": "Structured data is valid", "score": None},
                "largest-contentful-paint": {"title": "Largest Contentful Paint", "score": 0.2},
            },
        }
    }  # fmt: skip


def test_summary_keeps_scores_conditions_and_failing_audits_only() -> None:
    summary = summarize(payload(), strategy="MOBILE")
    assert summary["scores"] == {
        "SEO": 83,
        "PERFORMANCE": 41,
        "ACCESSIBILITY": 90,
        "BEST_PRACTICES": None,
    }
    assert summary["failing"]["SEO"] == [  # type: ignore[index]
        {"id": "meta-description", "title": "Document does not have a meta description", "score": 0}
    ]
    assert summary["lighthouseVersion"] == "12.8.2" and summary["throttling"] == "simulate"


def test_adapter_sends_the_key_and_the_four_categories(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("AIza-test\n", encoding="utf-8")
    sent: list[str] = []

    def transport(url: str) -> bytes:
        sent.append(url)
        return json.dumps(payload()).encode()

    PageSpeedInsights(key, transport=transport).run(
        "https://www.biocultor.com/", strategy="DESKTOP"
    )
    assert "key=AIza-test" in sent[0] and "strategy=desktop" in sent[0]
    assert all(
        f"category={c}" in sent[0]
        for c in ("SEO", "PERFORMANCE", "ACCESSIBILITY", "BEST_PRACTICES")
    )


class FakeLighthouse:
    instrument = "fake-lighthouse"

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def run(self, url: str, *, strategy: str) -> dict[str, object]:
        self.calls.append((url, strategy))
        if self.fail:
            raise urllib.error.HTTPError(url, 403, "blocked", None, None)  # type: ignore[arg-type]
        return summarize(payload(), strategy=strategy)


def test_runner_measures_off_the_read_path_and_shares_for_14_days(tmp_path: Path) -> None:
    clock = [NOW]
    lighthouse = FakeLighthouse()
    runner = PageSpeedRunner(lighthouse, tmp_path / "p.sqlite3", clock=lambda: clock[0])
    origin = "https://www.biocultor.com/"
    runner.request(origin)
    assert runner.measurement(origin) is None and lighthouse.calls == []
    assert runner.run() == 1
    assert [s for _, s in lighthouse.calls] == ["MOBILE", "DESKTOP"]
    clock[0] = NOW + timedelta(days=13)
    runner.request(origin)
    assert runner.run() == 0  # still fresh
    found = lighthouse_discoveries(runner.measurement(origin) or {}, observed_at="")
    assert [d["code"] for d in found] == ["LIGHTHOUSE_AUDIT", "LIGHTHOUSE_AUDIT"]
    mobile = found[0]
    assert mobile["statement"] == "SEO 83 · PERFORMANCE 41 · ACCESSIBILITY 90"
    detail = mobile["detail"]
    assert isinstance(detail, dict)
    assert detail["conditions"]["strategy"] == "MOBILE" and detail["notSearchPosition"] is True
    assert detail["instrument"]["lighthouseVersion"] == "12.8.2" and detail["uncertainty"]


def test_a_refusal_is_retried_hours_later_not_in_a_loop(tmp_path: Path) -> None:
    clock = [NOW]
    lighthouse = FakeLighthouse(fail=True)
    runner = PageSpeedRunner(lighthouse, tmp_path / "p.sqlite3", clock=lambda: clock[0])
    runner.request("https://a.es/")
    assert runner.run() == 0 and len(lighthouse.calls) == 1
    assert runner.run() == 0 and len(lighthouse.calls) == 1  # backing off
    clock[0] = NOW + timedelta(hours=7)
    lighthouse.fail = False
    assert runner.run() == 1


def test_on_with_a_mounted_key_unless_turned_off(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("k", encoding="utf-8")
    assert pagespeed_from_values({"AXIGNAL_PAGESPEED_API_KEY_FILE": str(key)}, tmp_path) is not None
    off = {"AXIGNAL_PAGESPEED_API_KEY_FILE": str(key), "AXIGNAL_PAGESPEED_ENABLED": "false"}
    assert pagespeed_from_values(off, tmp_path) is None
    missing = {"AXIGNAL_PAGESPEED_API_KEY_FILE": str(tmp_path / "none")}
    assert pagespeed_from_values(missing, tmp_path) is None
