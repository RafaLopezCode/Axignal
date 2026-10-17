"""Jev reads what the organizations on a logo wall are to the site (spec 083, CTO 2026-10-17).

The vocabulary read roles from headings alone: "Partners" over press logos became partners,
and "Ils utilisent nos produits" or "Featured in" were never read. Each wall is a Choice
question over its heading and names; Python keeps the last word.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from application.first_observation.site import PageReading, read_page
from application.own_site import logo_walls
from application.own_site.wall_roles import interpret_walls, wall_batch, walls
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeSystemOne

NOW = datetime(2026, 10, 17, 9, tzinfo=UTC)
URL = "https://acme.example/"


def _page(body: str) -> PageReading:
    html = f"<html lang='fr'><head><title>Acme</title></head><body>{body}</body></html>"
    return read_page(
        url=URL, html=html, observed_at=NOW, content_fingerprint="f", artifact_ref=None
    )


PAGE = _page(
    "<h2>Ils utilisent nos produits</h2>"  # clients the vocabulary cannot read
    '<img alt="Carrefour"><img alt="Danone"><img alt="Michelin">'
    "<h2>Partners</h2>"  # press logos under a partners heading
    '<img alt="Le Monde"><img alt="Les Echos"><img alt="BFM Business">'
    "<h2>Nos partenaires</h2>"  # real partners: the evaluator is unsure
    '<img alt="Schneider Electric"><img alt="Legrand"><img alt="Hager">'
)


def _rule(batch, question):  # type: ignore[no-untyped-def]
    text = question.instructions
    if "Carrefour" in text:
        return ("CLIENTS", 0.92)
    if "Le Monde" in text:
        return ("PRESS", 0.95)
    return ("PARTNERS", 0.3)  # too uncertain to be usable


def _judged(page: PageReading) -> tuple[dict[tuple[str, str], str | None], FakeSystemOne]:
    candidates = walls([page])
    batch = wall_batch(candidates)
    assert batch is not None
    judge = FakeSystemOne(_rule)
    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-17")  # fmt: skip
    cascade = SemanticCascade(
        judge=judge, ledger=CostLedger(prices=(price,)), memory=InMemoryJudgmentMemory(),
        budget=SemanticBudget(max_system_one_input_tokens=50_000, max_reasoning_calls=0),
    )  # fmt: skip
    outcome = cascade.run([batch], now=NOW)[batch.batch_id]
    return interpret_walls(candidates, outcome), judge


def test_each_wall_is_one_question_over_its_heading_and_names() -> None:
    _judged_walls, judge = _judged(PAGE)
    (call,) = judge.calls
    assert len(call.questions) == 3
    assert all("Under the heading" in q.instructions for q in call.questions)


def test_the_evaluator_decides_the_role_and_uncertainty_keeps_the_vocabulary() -> None:
    judged, _judge = _judged(PAGE)
    read = {(d.code, d.statement): d for d in logo_walls([PAGE], judged=judged, model="jev-1.13.0")}
    # Read by the evaluator only: a POTENTIAL inference, never a declaration.
    client = read[("CLIENT_DECLARED", "Carrefour")]
    assert client.epistemic_state == "POTENTIAL" and client.detail["roleBy"] == "SEMANTIC_JUDGMENT"
    # Press under a "Partners" heading is no longer a partner.
    assert ("PARTNER_DECLARED", "Le Monde") not in read
    # Uncertain answer: the vocabulary's reading stands, as declared.
    partner = read[("PARTNER_DECLARED", "Schneider Electric")]
    assert partner.epistemic_state == "DECLARED" and partner.detail["roleBy"] == "VOCABULARY"


def test_without_judgments_the_reading_is_exactly_as_before() -> None:
    before = [(d.code, d.statement, d.epistemic_state) for d in logo_walls([PAGE])]
    assert ("PARTNER_DECLARED", "Le Monde", "DECLARED") in before
    assert not any(s == "Carrefour" for _c, s, _e in before)


def test_a_counterparty_role_needs_a_confident_answer_and_neither_does_not() -> None:
    from application.own_site.wall_roles import MIN_ROLE_CONFIDENCE

    page = _page(
        "<h2>Secure eCommerce</h2>"
        '<img alt="Solution 01"><img alt="Solution 02"><img alt="Disney">'
        "<h2>Menu</h2>"
        '<img alt="Submenu"><img alt="Search panel"><img alt="Language switch">'
    )
    candidates = walls([page])

    def rule(batch, question):  # type: ignore[no-untyped-def]
        if "Disney" in question.instructions:
            return ("CLIENTS", MIN_ROLE_CONFIDENCE - 0.07)
        return ("NOT_ORGANIZATIONS", 0.62)

    batch = wall_batch(candidates)
    assert batch is not None
    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-17")  # fmt: skip
    cascade = SemanticCascade(
        judge=FakeSystemOne(rule), ledger=CostLedger(prices=(price,)),
        memory=InMemoryJudgmentMemory(),
        budget=SemanticBudget(max_system_one_input_tokens=50_000, max_reasoning_calls=0),
    )  # fmt: skip
    judged = interpret_walls(candidates, cascade.run([batch], now=NOW)[batch.batch_id])
    assert (URL, "Secure eCommerce") not in judged  # unsure: unjudged, never a client
    assert judged[(URL, "Menu")] is None
