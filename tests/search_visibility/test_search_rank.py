"""Search ranking measured: the activity's searches through a permitted API, never scraping."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from application.search_visibility import (
    SearchSubject,
    clean_terms,
    evaluate,
    google_url,
    keywords,
    language_for,
    search_discoveries,
    terms_from_activity,
)
from pipeline.search_visibility.brave import BraveSearch, search_language
from tools.runtime.search_rank import SearchRankRunner, search_rank_from_values

NOW = datetime(2026, 10, 17, 9, tzinfo=UTC)
BIOCULTOR = SearchSubject(
    name="biocultor.com",
    domain="biocultor.com",
    terms=("humus de lombriz", "abono orgánico"),
    country="ES",
    language="es",
)


def _results(*hosts: str) -> list[dict[str, object]]:
    return [
        {"position": i, "url": f"https://www.{h}/page", "title": h} for i, h in enumerate(hosts, 1)
    ]


def test_keywords_come_from_its_own_words_and_country_in_its_language() -> None:
    assert keywords(BIOCULTOR) == (
        "humus de lombriz",
        "humus de lombriz España",
        "abono orgánico",
    )
    # A site written in English for a Spanish company: no mixed-language query.
    english = SearchSubject("x", "x.com", ("worm castings",), "ES", "en")
    assert keywords(english) == ("worm castings",)


def test_terms_are_the_lexicon_terms_its_text_uses_in_order() -> None:
    excerpt = "Producimos Humus de Lombriz y vendemos abono orgánico certificado."
    found = terms_from_activity(excerpt, ("abono orgánico", "worm castings", "humus de lombriz"))
    assert found == ("humus de lombriz", "abono orgánico")
    assert clean_terms(["  humus  de lombriz ", "humus de lombriz", "eco"]) == ("humus de lombriz",)


def test_language_is_the_declared_one_else_the_country_one() -> None:
    assert language_for("ES", "en-GB") == "en"
    assert language_for("PT", None) == "pt"
    assert language_for("US", None) == "en"


def test_evaluation_finds_position_and_who_ranks_instead() -> None:
    found = [
        _results("amazon.es", "biocultor.com", "leroymerlin.es"),
        _results("amazon.es", "leroymerlin.es"),
        _results("shop.biocultor.com", "amazon.es"),
    ]
    result = evaluate(BIOCULTOR, found)
    rows = result["keywords"]
    assert [r["position"] for r in rows] == [2, None, 1]  # type: ignore[index]
    assert (result["ranked"], result["top10"], result["averagePosition"]) == (2, 2, 1.5)
    assert result["rankingInstead"][0] == ["amazon.es", 3]  # type: ignore[index]
    url = rows[0]["googleUrl"]  # type: ignore[index]
    assert parse_qs(urlsplit(str(url)).query) == {
        "q": ["humus de lombriz"],
        "hl": ["es"],
        "gl": ["es"],
    }
    assert google_url("x", BIOCULTOR).startswith("https://www.google.com/search?")


def test_discovery_is_a_declared_measurement_not_an_endorsement() -> None:
    result = evaluate(BIOCULTOR, [_results("biocultor.com"), [], []])
    found = search_discoveries(
        {"result": result, "instrument": {"name": "brave"}, "country": "ES", "language": "es",
         "measuredAt": NOW.isoformat()},
        observed_at="x",
    )  # fmt: skip
    (only,) = found
    assert (only["kind"], only["code"], only["statement"]) == (
        "SEARCH_VISIBILITY",
        "SEARCH_RANKS_MEASURED",
        "1/3",
    )
    detail = only["detail"]
    assert isinstance(detail, Mapping)
    assert detail["conditions"]["country"] == "ES"  # type: ignore[index]
    assert detail["uncertainty"] and detail["notEndorsement"] is True
    unranked = evaluate(BIOCULTOR, [[], [], []])
    assert (
        search_discoveries({"result": unranked}, observed_at="x")[0]["code"] == "SEARCH_NOT_RANKED"
    )
    assert search_discoveries({"result": {"keywordsMeasured": 0}}, observed_at="x") == []


def test_brave_client_sends_key_in_header_and_market_params(tmp_path: Path) -> None:
    key = tmp_path / "key"
    key.write_text("secret-test-key\n", encoding="utf-8")
    seen: list[tuple[str, Mapping[str, str]]] = []

    def transport(url: str, headers: Mapping[str, str]) -> bytes:
        seen.append((url, headers))
        return json.dumps(
            {"web": {"results": [{"url": "https://a.es", "title": "A"}, {"x": 1}]}}
        ).encode()

    results = BraveSearch(key, transport=transport).search("abono", country="CO", language="es")
    assert [(r.position, r.url) for r in results] == [(1, "https://a.es")]
    url, headers = seen[0]
    params = parse_qs(urlsplit(url).query)
    assert params["country"] == ["ALL"] and params["search_lang"] == ["es"]
    assert headers["X-Subscription-Token"] == "secret-test-key"
    assert "secret" not in url
    assert search_language("pt", "BR") == "pt-br" and search_language("pt", "PT") == "pt-pt"


def test_runner_queues_measures_once_and_respects_ttl_and_cap(tmp_path: Path) -> None:
    clock = [NOW]
    calls: list[str] = []

    def search(query: str, **_: object) -> list[object]:
        from pipeline.search_visibility.brave import SearchResult

        calls.append(query)
        return [SearchResult(1, "https://biocultor.com/", "Biocultor")]

    runner = SearchRankRunner(search, tmp_path / "s.sqlite3", clock=lambda: clock[0], max_per_day=1)
    assert runner.measurement(BIOCULTOR) is None
    runner.request(BIOCULTOR)
    runner.request(BIOCULTOR)  # already queued
    assert runner.run() == 1 and len(calls) == 3
    stored = runner.measurement(BIOCULTOR)
    assert stored is not None and stored["cost"] == {"queries": 3, "usd": 0.015}
    runner.request(BIOCULTOR)  # fresh: not queued again
    other = SearchSubject("o.es", "o.es", ("compost",), "ES", "es")
    runner.request(other)
    assert runner.run() == 0  # daily cap reached
    clock[0] = NOW + timedelta(days=1)
    assert runner.run() == 1


def test_runner_keeps_queued_when_the_api_fails(tmp_path: Path) -> None:
    def failing(query: str, **_: object) -> list[object]:
        raise OSError("unavailable")

    runner = SearchRankRunner(failing, tmp_path / "s.sqlite3", clock=lambda: NOW)
    runner.request(BIOCULTOR)
    assert runner.run() == 0 and runner.measurement(BIOCULTOR) is None


@pytest.mark.parametrize("value", ["", "relative/key", "/nonexistent/brave_key"])
def test_off_without_a_readable_key_file(tmp_path: Path, value: str) -> None:
    assert search_rank_from_values({"AXIGNAL_BRAVE_SEARCH_KEY_FILE": value}, tmp_path) is None


def test_on_with_a_readable_key_file(tmp_path: Path) -> None:
    key = tmp_path / "brave"
    key.write_text("k", encoding="utf-8")
    runner = search_rank_from_values({"AXIGNAL_BRAVE_SEARCH_KEY_FILE": str(key)}, tmp_path)
    assert isinstance(runner, SearchRankRunner)


def test_view_reads_terms_from_its_site_and_queues_without_searching(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from tools.runtime.first_observation import FirstObservationRuntime

    calls: list[str] = []

    def search(query: str, **_: object) -> list[object]:
        calls.append(query)
        return []

    runner = SearchRankRunner(search, tmp_path / "s.sqlite3", clock=lambda: NOW)
    view: dict[str, object] = {
        "target": {"website": "https://www.biocultor.com/"},
        "attentionScopes": [{"jurisdiction": "EU/ES"}],
        "publishedContact": {"language": "es"},
        "capabilities": [
            {"capabilityId": "fertilisers-soil-amendments",
             "basis": {"excerpt": "Fabricamos humus de lombriz y té de humus."}},
            {"capabilityId": "unknown-id", "basis": {"excerpt": "x"}},
        ],
        "discoveries": [],
    }  # fmt: skip
    host = SimpleNamespace(_search_rank=runner)
    out = FirstObservationRuntime._with_search_rank(host, dict(view))  # type: ignore[arg-type]
    assert out["discoveries"] == [] and calls == []  # queued, never searched inline
    assert runner.run() == 1
    assert calls == ["humus de lombriz", "humus de lombriz España"]
    shown = FirstObservationRuntime._with_search_rank(host, dict(view))  # type: ignore[arg-type]
    assert [d["code"] for d in shown["discoveries"]] == ["SEARCH_NOT_RANKED"]  # type: ignore[index, union-attr]
    # No country, no website or no activity in its words: nothing queued.
    bare = {**view, "attentionScopes": []}
    assert FirstObservationRuntime._with_search_rank(host, bare) is bare  # type: ignore[arg-type]
