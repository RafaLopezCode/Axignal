"""Wikipedia notoriety: identified by official website, never by name; stored, then read."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.reputation import notoriety_discoveries
from pipeline.reputation.notoriety import WikipediaNotoriety

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _entity(website: str, *langs: str) -> dict[str, Any]:
    return {
        "claims": {"P856": [{"mainsnak": {"datavalue": {"value": website}}}]},
        "sitelinks": {f"{lang}wiki": {"title": "Wise (company)"} for lang in langs},
    }


class Web:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, url: str) -> Any:
        self.calls.append(url)
        if "list=search" in url:
            return {"query": {"search": []}}
        if "wbsearchentities" in url:
            return {"search": [{"id": "Q1"}, {"id": "Q2"}, {"id": "Q3"}]}
        if "wbgetentities" in url:
            return {"entities": {
                "Q1": _entity("https://www.wise.example/", "en", "de", "fr"),  # the company
                "Q2": _entity("https://wisdom.example/", "en", "de", "fr", "es", "it"),  # homonym
                "Q3": {"claims": {}, "sitelinks": {"enwiki": {"title": "Wise"}}},  # a word
            }}  # fmt: skip
        if "/en.wikipedia/" in url:
            return {
                "items": [{"timestamp": f"2026{m:02d}0100", "views": 100 * m} for m in range(1, 10)]
            }
        if "/de.wikipedia/" in url:
            return {"items": [{"timestamp": "2026090100", "views": 50}]}
        raise OSError("404")  # an article with no views


def test_the_item_is_the_one_whose_official_website_is_its_brand(tmp_path: Path) -> None:
    web = Web()
    store = WikipediaNotoriety(tmp_path / "n.sqlite3", fetch=web, clock=lambda: NOW)
    store.request("wise.example", "Wise")
    assert store.latest("wise.example") is None  # nothing read on the subscriber path
    assert store.run() == 1
    result = store.latest("www.wise.example")
    assert result is not None and result["item"] == "Q1"  # never the richer homonym
    assert result["monthly"]["2026-09"] == 950 and result["byLanguage"]["de"] == 50
    assert store.run() == 0  # weekly, not on every tick


def test_findings_are_observed_attention_with_trend_not_opinion(tmp_path: Path) -> None:
    store = WikipediaNotoriety(tmp_path / "n.sqlite3", fetch=Web(), clock=lambda: NOW)
    store.request("wise.example", "Wise")
    store.run()
    (found,) = notoriety_discoveries(store.latest("wise.example"))
    assert found["code"] == "WIKIPEDIA_NOTORIETY" and found["epistemicState"] == "OBSERVED"
    assert found["detail"]["views"] == 950 and found["detail"]["trend"] == round(2450 / 1500 - 1, 3)
    assert "not opinion" in str(found["detail"]["limitation"])
    assert notoriety_discoveries({"item": None}) == []


def test_no_official_website_match_means_no_finding(tmp_path: Path) -> None:
    web = Web()
    store = WikipediaNotoriety(tmp_path / "n.sqlite3", fetch=web, clock=lambda: NOW)
    store.request("unknown-brand.example", "Wise")
    store.run()
    assert notoriety_discoveries(store.latest("unknown-brand.example")) == []
