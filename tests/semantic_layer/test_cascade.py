"""Spec 062: memory before calls, one call per batch, budgets abstain, doubt escalates."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.economic_discovery.brain_contracts import SemanticPrimitive
from application.semantic_layer.cascade import CascadePolicy, Resolution, SemanticCascade
from application.semantic_layer.contracts import (
    JudgmentSource,
    SemanticAnswer,
    SemanticBatch,
    SemanticQuestion,
)
from application.semantic_layer.ledger import (
    JEV_1_13_PRICE,
    CostLedger,
    PricePolicy,
    SemanticBudget,
    monthly_system_one_usd,
)
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeReasoning, FakeSystemOne

NOW = datetime(2026, 10, 8, 12, tzinfo=UTC)
FIT = SemanticQuestion(
    "fit", "1", SemanticPrimitive.SCORE, "How close is `tender` to `capability`?",
    (("UNRELATED", "Different work."), ("ADJACENT", "Same sector."), ("CORE", "Same work.")),
)  # fmt: skip
ONSITE = SemanticQuestion(
    "onsite", "1", SemanticPrimitive.NOUL, "Must the work be done at the buyer's site?",
    (("true", "It is done at the buyer's site."), ("false", "It is not.")),
)  # fmt: skip


def batch(title: str = "Instalación fotovoltaica en edificios municipales") -> SemanticBatch:
    return SemanticBatch(
        "b:" + title[:12],
        {"tender": {"title": title}, "capability": {"label": "Solar photovoltaic installation"}},
        (FIT, ONSITE),
    )


def cascade(judge, *, memory=None, escalation=None, tokens=1_000_000, calls=0, escalable=()):
    return SemanticCascade(
        judge=judge,
        ledger=CostLedger(),
        budget=SemanticBudget(tokens, calls),
        policy=CascadePolicy(escalable=frozenset(escalable)),
        memory=memory,
        escalation=escalation,
    )


def test_every_question_of_a_batch_is_answered_in_one_call_and_costed() -> None:
    judge = FakeSystemOne(lambda b, q: ("CORE", 0.9) if q is FIT else ("true", 0.92))
    run = cascade(judge)
    outcome = run.run((batch(),), now=NOW)[batch().batch_id]
    assert len(judge.calls) == 1 and len(judge.calls[0].questions) == 2  # speculative fan-out
    assert outcome.judgment("fit").resolution is Resolution.DECIDED
    assert outcome.judgment("fit").answer.top == "CORE"
    assert outcome.judgment("onsite").resolution is Resolution.DECIDED
    line = run.ledger.lines[("typesafe-system-one", "jev-1.13.0")]
    assert line.calls == 1 and line.questions == 2 and line.input_tokens > 0
    assert line.usd == Decimal(line.input_tokens) * Decimal("0.042") / Decimal(1_000_000)
    assert not outcome.judgment("fit").answer.is_canonical_truth


def test_shared_memory_answers_the_same_world_state_without_a_second_call() -> None:
    judge = FakeSystemOne(lambda b, q: ("CORE", 0.9) if q is FIT else ("true", 0.9))
    memory = InMemoryJudgmentMemory()
    cascade(judge, memory=memory).run((batch(),), now=NOW)
    second = cascade(judge, memory=memory)  # e.g. another Focus meeting the same tender
    outcome = second.run((batch(),), now=NOW)[batch().batch_id]
    assert len(judge.calls) == 1
    assert second.ledger.memory_hits == 2 and not second.ledger.lines
    assert outcome.judgment("fit").from_memory


def test_a_new_question_version_or_state_is_judged_again() -> None:
    judge = FakeSystemOne(lambda b, q: ("CORE", 0.9) if q.question_id == "fit" else ("true", 0.9))
    memory = InMemoryJudgmentMemory()
    cascade(judge, memory=memory).run((batch(),), now=NOW)
    revised = SemanticQuestion("fit", "2", FIT.primitive, FIT.instructions, FIT.criteria)
    changed = SemanticBatch(batch().batch_id, batch().state, (revised, ONSITE))
    cascade(judge, memory=memory).run((changed,), now=NOW)
    assert len(judge.calls) == 2 and [q.question_id for q in judge.calls[1].questions] == ["fit"]
    cascade(judge, memory=memory).run((batch("Otra licitación distinta"),), now=NOW)
    assert len(judge.calls) == 3


def test_over_budget_questions_abstain_instead_of_guessing() -> None:
    judge = FakeSystemOne(lambda b, q: ("CORE", 0.9) if q is FIT else ("true", 0.9))
    outcome = cascade(judge, tokens=10).run((batch(),), now=NOW)[batch().batch_id]
    assert not judge.calls
    assert {j.resolution for j in outcome.judgments.values()} == {Resolution.ABSTAINED_BUDGET}
    assert not any(j.usable for j in outcome.judgments.values())


def test_provider_failure_is_unknown_for_that_batch_only() -> None:
    failing = FakeSystemOne(lambda b, q: ("CORE", 0.9), fail="RATE_LIMITED")
    outcome = cascade(failing).run((batch(),), now=NOW)[batch().batch_id]
    assert outcome.judgment("fit").resolution is Resolution.FAILED
    assert outcome.judgment("fit").reason == "RATE_LIMITED"


def test_uncertain_material_questions_escalate_once_within_the_call_budget() -> None:
    judge = FakeSystemOne(lambda b, q: ("ADJACENT", 0.41) if q is FIT else ("true", 0.5))
    luna = FakeReasoning(lambda q: "CORE" if q.question_id == "fit" else "UNKNOWN")
    run = cascade(judge, escalation=luna, calls=1, escalable=("fit", "onsite"))
    out = run.run((batch(), batch("Segunda licitación fotovoltaica")), now=NOW)
    first, second = out.values()
    assert len(luna.calls) == 1  # the call budget is one: the second batch stays uncertain
    assert first.judgment("fit").resolution is Resolution.ESCALATED
    assert first.judgment("fit").answer.selected == "CORE"
    assert first.judgment("fit").answer.distribution == ()  # no invented probabilities
    assert first.judgment("onsite").resolution is Resolution.UNCERTAIN  # Luna said UNKNOWN
    assert second.judgment("fit").resolution is Resolution.UNCERTAIN
    luna_line = run.ledger.lines[("luna-responses", "gpt-6-luna")]
    assert luna_line.calls == 1 and luna_line.unknown_cost_calls == 1  # price not configured


def test_questions_not_declared_escalable_never_reach_the_reasoning_model() -> None:
    judge = FakeSystemOne(lambda b, q: ("ADJACENT", 0.41) if q is FIT else ("true", 0.5))
    luna = FakeReasoning(lambda q: q.labels[0])
    cascade(judge, escalation=luna, calls=5).run((batch(),), now=NOW)
    assert not luna.calls


def test_oversized_state_is_refused_so_callers_filter_first() -> None:
    judge = FakeSystemOne(lambda b, q: ("CORE", 0.9))
    huge = SemanticBatch("big", {"tender": {"text": "x" * 120_000}}, (FIT,))
    outcome = cascade(judge, tokens=10**9).run((huge,), now=NOW)["big"]
    assert not judge.calls
    assert outcome.judgment("fit").reason == "STATE_TOO_LARGE_FILTER_FIRST"


def test_answers_cannot_select_outside_their_distribution_or_skip_both() -> None:
    with pytest.raises(ValueError):
        SemanticAnswer(
            "fit", SemanticPrimitive.SCORE, JudgmentSource.SYSTEM_ONE, "e", "m",
            distribution=(("CORE", 0.7), ("ADJACENT", 0.3)), selected="NOPE",
        )  # fmt: skip
    with pytest.raises(ValueError):
        SemanticAnswer("fit", SemanticPrimitive.SCORE, JudgmentSource.REASONING, "e", "m")


def test_planning_estimate_reflects_reuse_and_unknown_prices() -> None:
    # 200 candidate batches a day, ~700 tokens each, half reused across Foci.
    estimate = monthly_system_one_usd(batches_per_day=200, tokens_per_batch=700, reuse_ratio=0.5)
    assert estimate == Decimal(2_100_000) * Decimal("0.042") / Decimal(1_000_000)
    unpriced = PricePolicy("x", "e", "m", None, None, "none", "n/a")
    assert (
        monthly_system_one_usd(batches_per_day=1, tokens_per_batch=1, reuse_ratio=0, price=unpriced)
        is None
    )
    assert JEV_1_13_PRICE.cost(1_000_000, 10_000) == Decimal("0.042")  # output tokens are free
