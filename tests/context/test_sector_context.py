"""Sector context: lexicon prefilter, then a non-authoritative relevance judgment."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from application.context.sector import context_discoveries, mentions_keyword, sector_keywords
from application.press.contracts import PressItem
from cognition.jobs.model import JobKind
from pipeline.press.sqlite_store import SqlitePressIndex
from tools.runtime.sector_context import SectorContextRunner

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)


def _item(title: str, country: str = "EU/ES") -> PressItem:
    return PressItem(
        "f", "Diario", title, f"https://d.example/{abs(hash(title))}", NOW, "es", country
    )


def test_sector_keywords_come_from_the_lexicon_without_generic_words() -> None:
    keywords = sector_keywords("security-guarding")
    assert "privada" in keywords and "servicios" not in keywords
    assert mentions_keyword("La seguridad privada crece", keywords)
    assert sector_keywords("unknown-activity") == ()


def test_only_judged_headlines_in_its_country_are_shown(tmp_path: Path) -> None:
    store = SqlitePressIndex(tmp_path / "p.sqlite3")
    store.upsert([
        _item("Las empresas de seguridad privada piden más vigilantes"),
        _item("La Seguridad Social cambia la jubilación"),
        _item("Private security guarding grows", country="US"),
    ])  # fmt: skip
    seen: list[str] = []

    def complete(job):  # type: ignore[no-untyped-def]
        assert job.kind is JobKind.SEMANTIC_DECISION
        seen.append(str(job.context["user"]))
        titles = [line.split(". ", 1)[1] for line in str(job.context["user"]).splitlines()[2:]]
        relevant = [i for i, t in enumerate(titles) if "privada" in t]
        return SimpleNamespace(payload={"answer": {"relevant": relevant}})

    runner = SectorContextRunner(complete, "m", store, tmp_path / "c.sqlite3", clock=lambda: NOW)
    runner.request("security-guarding", "EU/ES")
    runner.request("security-guarding", "EU/ES")  # once per activity, country and day
    assert runner.run() == 1 and len(seen) == 1
    assert "guarding grows" not in seen[0]  # its country only
    result = runner.latest("security-guarding", "EU/ES")
    found = context_discoveries(
        result or {}, capability_id="security-guarding", country="EU/ES", observed_at="x"
    )
    assert [d["statement"] for d in found] == [
        "Las empresas de seguridad privada piden más vigilantes"
    ]
    assert found[0]["epistemicState"] == "POTENTIAL" and found[0]["kind"] == "CONTEXT_SIGNAL"


def test_an_unavailable_assistant_leaves_it_queued(tmp_path: Path) -> None:
    store = SqlitePressIndex(tmp_path / "p.sqlite3")
    store.upsert([_item("Las empresas de seguridad privada piden más vigilantes")])

    def failing(job):  # type: ignore[no-untyped-def]
        raise RuntimeError("down")

    runner = SectorContextRunner(failing, "m", store, tmp_path / "c.sqlite3", clock=lambda: NOW)
    runner.request("security-guarding", "EU/ES")
    assert runner.run() == 0 and runner.latest("security-guarding", "EU/ES") is None
