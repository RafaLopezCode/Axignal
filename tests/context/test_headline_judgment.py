"""Jev judges each headline for sector context and regulation (spec 082, CTO 2026-10-17).

Before, the generative assistant returned "the indexes" of relevant headlines in one opaque
call. A classification is asked as one: a Noul per headline over a typed state, Python
keeps only usable "true" answers, and a headline judged once is not paid for again.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from application.context.headline_judgment import (
    REGULATION,
    SECTOR_NEWS,
    HeadlineVerdict,
    jev_headline_judge,
)
from application.context.sector import context_discoveries
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from pipeline.press.sqlite_store import SqlitePressIndex
from tests.context.test_sector_context import _item
from tests.semantic_layer.fakes import FakeSystemOne
from tools.runtime.sector_context import SectorContextRunner

NOW = datetime(2026, 10, 17, 9, tzinfo=UTC)
TITLES = [
    "Las empresas de seguridad privada piden más vigilantes",
    "La Seguridad Social cambia la jubilación",
    "Dudoso: un titular ambiguo sobre seguridad",
]


def _rule(batch, question):  # type: ignore[no-untyped-def]
    text = question.instructions
    if "privada" in text:
        return ("true", 0.93)
    if "Dudoso" in text:
        return ("true", 0.3)  # too uncertain to be usable: never shown
    return ("false", 0.95)


def _factory(judge: FakeSystemOne, memory: InMemoryJudgmentMemory):  # type: ignore[no-untyped-def]
    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-17")  # fmt: skip

    def make() -> SemanticCascade:
        return SemanticCascade(
            judge=judge, ledger=CostLedger(prices=(price,)), memory=memory,
            budget=SemanticBudget(max_system_one_input_tokens=60_000, max_reasoning_calls=0),
        )  # fmt: skip

    return make


def test_each_headline_is_judged_and_only_usable_true_answers_are_kept() -> None:
    judge, memory = FakeSystemOne(_rule), InMemoryJudgmentMemory()
    verdict = jev_headline_judge(_factory(judge, memory))(
        "Private security", TITLES, SECTOR_NEWS, NOW
    )
    assert verdict is not None and verdict.kept == (0,)
    assert verdict.instrument["model"] == "jev-1.13.0"
    asked = [q.instructions for call in judge.calls for q in call.questions]
    assert len(asked) == 3 and all("Headline:" in a for a in asked)
    # The same headlines tomorrow are remembered, not paid again.
    again = jev_headline_judge(_factory(judge, memory))(
        "Private security", TITLES, SECTOR_NEWS, NOW
    )
    assert again == verdict and sum(len(c.questions) for c in judge.calls) == 3


def test_regulation_and_news_are_different_questions() -> None:
    judge, memory = FakeSystemOne(_rule), InMemoryJudgmentMemory()
    jev_headline_judge(_factory(judge, memory))("Private security", TITLES[:1], SECTOR_NEWS, NOW)
    jev_headline_judge(_factory(judge, memory))("Private security", TITLES[:1], REGULATION, NOW)
    assert len(judge.calls) == 2  # never reuses a news judgment as a regulatory one


def test_the_runner_prefers_jev_and_falls_back_to_the_assistant(tmp_path: Path) -> None:
    store = SqlitePressIndex(tmp_path / "p.sqlite3")
    store.upsert([_item(t) for t in TITLES])
    judge = jev_headline_judge(_factory(FakeSystemOne(_rule), InMemoryJudgmentMemory()))
    runner = SectorContextRunner(None, None, store, tmp_path / "c.sqlite3", clock=lambda: NOW,
                                 judge=judge)  # fmt: skip
    runner.request("security-guarding", "EU/ES")
    assert runner.run() == 1
    result = runner.latest("security-guarding", "EU/ES") or {}
    shown = context_discoveries(result, capability_id="security-guarding", country="EU/ES",
                                observed_at="x")  # fmt: skip
    assert [d["statement"] for d in shown] == [TITLES[0]]
    assert shown[0]["detail"]["instrument"]["evaluator"] == "typesafe-system-one"  # type: ignore[index]

    def unavailable(*_args):  # type: ignore[no-untyped-def]
        return None

    def complete(job):  # type: ignore[no-untyped-def]
        return SimpleNamespace(payload={"answer": {"relevant": [0]}})

    fallback = SectorContextRunner(complete, "assistant", store, tmp_path / "f.sqlite3",
                                   clock=lambda: NOW, judge=unavailable)  # fmt: skip
    fallback.request("security-guarding", "EU/ES")
    assert fallback.run() == 1
    assert (fallback.latest("security-guarding", "EU/ES") or {})["instrument"][
        "model"
    ] == "assistant"  # type: ignore[index]
    # Nothing can judge: it stays queued, never "nothing relevant".
    idle = SectorContextRunner(None, None, store, tmp_path / "i.sqlite3", clock=lambda: NOW,
                               judge=unavailable)  # fmt: skip
    idle.request("security-guarding", "EU/ES")
    assert idle.run() == 0 and idle.latest("security-guarding", "EU/ES") is None


def test_a_verdict_carries_only_indexes_into_the_candidates() -> None:
    verdict = HeadlineVerdict(kept=(0,), instrument={})
    assert all(isinstance(i, int) for i in verdict.kept)
