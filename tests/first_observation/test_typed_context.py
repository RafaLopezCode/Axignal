"""Jev reads the public text it needs (spec 079, ADR-0090 amendment 2026-10-16).

Found on the canary: biocultor.com says "Comprar té de humus y servicios para jardines" in its
title, yet no activity was established, because the evaluator only received AXIGNAL's
vocabulary. With typed public text, the catalog question reads it, and Python turns the
answer into a catalog activity with its demand codes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from application.first_observation.activity import (
    CATALOG_ACTIVITY,
    interpret_activity,
    plan_activity_batch,
)
from application.first_observation.site import read_page
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeSystemOne

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)
HOME = (
    "<html lang='es'><head><title>Comprar té de humus y servicios para jardines | Biocultor"
    "</title><meta name='description' content='Té de humus de lombriz para huerto urbano y "
    "jardín. Fertilizante ecológico con envío a toda España.'></head><body>"
    "<h1>Té de humus de lombriz</h1><p>Usuarios de huerto urbano, autoconsumo y jardinería "
    "doméstica. Escríbenos a hola@biocultor.example.com o llama al 600 000 000.</p>"
    "<p>Fundada por Rafael en Toledo.</p></body></html>"
)


def _cascade(judge: FakeSystemOne) -> SemanticCascade:
    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-16")  # fmt: skip
    return SemanticCascade(
        judge=judge, ledger=CostLedger(prices=(price,)), memory=InMemoryJudgmentMemory(),
        budget=SemanticBudget(max_system_one_input_tokens=200_000, max_reasoning_calls=0),
    )  # fmt: skip


def test_a_site_the_lexicon_cannot_read_gets_its_catalog_activity_from_public_text() -> None:
    page = read_page(url="https://biocultor.example.com/", html=HOME, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    plan = plan_activity_batch("https://biocultor.example.com/", [page], known_scopes=(),
                               deterministic=())  # fmt: skip
    assert plan is not None and CATALOG_ACTIVITY in plan.batch.questions
    state = plan.batch.state
    title = state["pages"][0]["title"]  # type: ignore[index]
    assert "té de humus" in title.casefold()  # the evaluator reads what the site says
    raw = str(state)
    assert "hola@" not in raw and "600 000 000" not in raw and "Fundada por" not in raw

    def rule(batch, question):  # type: ignore[no-untyped-def]
        if question.question_id == CATALOG_ACTIVITY.question_id:
            return ("agriculture", 0.9)
        return (
            ("UNCLEAR", 0.9)
            if question.labels and "UNCLEAR" in question.labels
            else (question.labels[0], 0.9)
        )

    outcome = _cascade(FakeSystemOne(rule)).run([plan.batch], now=NOW)[plan.batch.batch_id]
    reading = interpret_activity(plan, outcome, [page], model="jev-1.13.0")
    (finding,) = [f for f in reading.findings if f.activity_id == "agriculture"]
    assert finding.demand_codes  # routes demand like any catalog activity
    assert reading.judged["catalogActivity"] == "agriculture"


def test_none_and_unclear_establish_nothing() -> None:
    page = read_page(url="https://x.example.com/", html=HOME, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    plan = plan_activity_batch("https://x.example.com/", [page], known_scopes=(), deterministic=())
    assert plan is not None
    for label in ("NONE", "UNCLEAR"):

        def rule(batch, question, label=label):  # type: ignore[no-untyped-def]
            return (label, 0.9) if label in question.labels else (question.labels[-1], 0.9)

        outcome = _cascade(FakeSystemOne(rule)).run([plan.batch], now=NOW)[plan.batch.batch_id]
        reading = interpret_activity(plan, outcome, [page], model="jev-1.13.0")
        assert "catalogActivity" not in reading.judged
