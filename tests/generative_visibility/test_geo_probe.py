"""GEO measured: fixed questions to the routed assistant, declared as a measurement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from application.generative_visibility.probe import (
    ProbeSubject,
    evaluate,
    geo_discoveries,
    questions,
)
from cognition.jobs.model import JobKind
from tools.runtime.generative_probe import GenerativeProbeRunner

NOW = datetime(2026, 10, 13, 9, tzinfo=UTC)
ZITRON = ProbeSubject("Talleres Zitrón", "zitron.com", "ventilation systems", "Spain", "en")


def test_questions_are_fixed_and_localized() -> None:
    assert questions(ZITRON) == (
        "Which companies do you recommend for ventilation systems in Spain?",
        "Who are the main providers of ventilation systems in Spain?",
        "What do you know about the company Talleres Zitrón?",
    )
    spanish = ProbeSubject("Holaluz", None, "energía", "España", "es")
    assert questions(spanish)[0] == "¿Qué empresas recomiendas para energía en España?"


def test_evaluation_separates_named_cited_competitors_and_brand_knowledge() -> None:
    answers = [
        {"answer": "Talleres Zitrón (zitron.com) and Soler & Palau lead.", "organizations_named": ["Talleres Zitrón", "Soler & Palau"], "websites_cited": ["https://zitron.com"]},
        {"answer": "Soler & Palau and Systemair.", "organizations_named": ["Soler & Palau", "Systemair"], "websites_cited": []},
        {"answer": "A Spanish maker of tunnel fans.", "organizations_named": ["Talleres Zitrón"], "websites_cited": [], "recognizes_subject": True},
    ]  # fmt: skip
    result = evaluate(ZITRON, answers)
    assert (result["namedInCategory"], result["citedInCategory"], result["brandKnown"]) == (
        1,
        1,
        True,
    )
    found = geo_discoveries(
        {
            "result": result,
            "instrument": {"model": "m"},
            "measuredAt": NOW.isoformat(),
            "language": "en",
        },
        observed_at="x",
    )
    category = found[0]
    assert category["code"] == "AI_NAMED_FOR_CATEGORY" and category["statement"] == "1/2"
    assert category["detail"]["competitorsNamed"] == ["Soler & Palau", "Systemair"]  # type: ignore[index]
    assert category["detail"]["conditions"]["liveWebSearch"] is False  # type: ignore[index]
    assert found[1]["code"] == "AI_KNOWS_BRAND"


def _model(calls: list[str], *, fail: bool = False):  # type: ignore[no-untyped-def]
    def complete(job):  # type: ignore[no-untyped-def]
        assert job.kind is JobKind.GENERATIVE_PROBE
        calls.append(str(job.context["user"]))
        if fail:
            raise RuntimeError("provider unavailable")
        return SimpleNamespace(payload={"answer": {"answer": "Systemair.", "organizations_named": ["Systemair"],
                                                   "websites_cited": [], "recognizes_subject": False},
                                        "input_tokens": 100, "output_tokens": 200})  # fmt: skip

    return complete


def test_the_runner_measures_once_per_period_off_the_read_path(tmp_path: Path) -> None:
    from decimal import Decimal

    calls: list[str] = []
    clock = [NOW]
    runner = GenerativeProbeRunner(_model(calls), "luna-test", tmp_path / "g.sqlite3",
                                   rates=(Decimal("0.125"), Decimal("0.5")), clock=lambda: clock[0])  # fmt: skip
    assert runner.measurement(ZITRON) is None
    runner.request(ZITRON)
    runner.request(ZITRON)  # already queued
    assert calls == []  # requesting never asks the model
    assert runner.run() == 1 and len(calls) == 3
    measurement = runner.measurement(ZITRON)
    assert measurement is not None and measurement["cost"]["usd"] == 0.000338  # type: ignore[index]
    runner.request(ZITRON)
    assert runner.run() == 0  # fresh for 30 days
    clock[0] = NOW + timedelta(days=31)
    runner.request(ZITRON)
    assert runner.run() == 1


def test_a_daily_cap_and_provider_failures_never_invent_a_result(tmp_path: Path) -> None:
    calls: list[str] = []
    runner = GenerativeProbeRunner(
        _model(calls, fail=True), "m", tmp_path / "g.sqlite3", clock=lambda: NOW, max_per_day=1
    )
    runner.request(ZITRON)
    assert runner.run() == 0 and runner.measurement(ZITRON) is None  # stays queued
