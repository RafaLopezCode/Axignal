"""Selling a product is not doing what its buyers do with it (spec 080, CTO 2026-10-16).

Found on the canary: biocultor.com, a shop selling worm-humus tea (a fertiliser), was read
as landscaping, one of the many uses of what it sells, and offered 95 gardening tenders.
The CTO: "Debemos encontrar la forma de que esto no pase en ningún caso". So the rule is
structural, not a catalog patch: every judged activity and CPV division must agree with
the nature of what the organization sells (supplies, services or works), and CPV itself
says which nature each code has. Here the evaluator is made to answer wrongly on purpose.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from application.first_observation.activity import (
    CATALOG_ACTIVITY,
    CPV_DIVISION,
    OFFER_NATURE,
    deterministic_activity,
    interpret_activity,
    natures_disagree,
    plan_activity_batch,
)
from application.first_observation.site import read_page
from application.observation_intelligence.catalog import CAPABILITY_LEXICON, offer_natures
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeSystemOne

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)
#: A goods seller, worded so that only its buyers' activity is named (worst case).
SHOP = (
    "<html lang='es'><head><title>Tienda online | Ejemplo</title><meta name='description' "
    "content='Productos con envío a toda España. Añadir al carrito.'></head><body>"
    "<h1>Nuestros productos</h1><p>Catálogo de productos con envío en 24 horas.</p>"
    "</body></html>"
)
#: Activities whose catalog nature is a service: what a shop's buyers may do.
SERVICE_ACTIVITIES = [
    e.capability_id for e in CAPABILITY_LEXICON if offer_natures(e) == {"SERVICES"}
]


def _read(answers: dict[str, str]):  # type: ignore[no-untyped-def]
    page = read_page(url="https://shop.example.com/", html=SHOP, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    plan = plan_activity_batch("https://shop.example.com/", [page], known_scopes=(),
                               deterministic=())  # fmt: skip
    assert plan is not None

    def rule(batch, question):  # type: ignore[no-untyped-def]
        if question.question_id in answers:
            return (answers[question.question_id], 0.95)
        return ("UNCLEAR", 0.9) if "UNCLEAR" in question.labels else (question.labels[-1], 0.9)

    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-16")  # fmt: skip
    cascade = SemanticCascade(
        judge=FakeSystemOne(rule), ledger=CostLedger(prices=(price,)),
        memory=InMemoryJudgmentMemory(),
        budget=SemanticBudget(max_system_one_input_tokens=200_000, max_reasoning_calls=0),
    )  # fmt: skip
    outcome = cascade.run([plan.batch], now=NOW)[plan.batch.batch_id]
    return interpret_activity(plan, outcome, [page], model="jev-1.13.0")


def test_the_catalog_carries_a_nature_for_every_activity_it_routes_by_cpv() -> None:
    assert len(SERVICE_ACTIVITIES) >= 4  # landscaping, cleaning, security, catering...
    for entry in CAPABILITY_LEXICON:
        if any(c.scheme == "CPV" for c in entry.demand_codes):
            assert offer_natures(entry) <= {"SUPPLIES", "SERVICES", "WORKS"}, entry.capability_id
            assert offer_natures(entry), entry.capability_id


@pytest.mark.parametrize("activity", SERVICE_ACTIVITIES)
def test_a_goods_seller_never_takes_its_buyers_service_activity(activity: str) -> None:
    reading = _read({OFFER_NATURE.question_id: "SUPPLIES", CATALOG_ACTIVITY.question_id: activity})
    assert all(f.activity_id != activity for f in reading.findings)
    assert reading.judged["catalogActivityWithheld"] == "NATURE_CONFLICT"


def test_a_goods_seller_never_routes_by_a_service_division() -> None:
    reading = _read({OFFER_NATURE.question_id: "SUPPLIES", CPV_DIVISION.question_id: "77"})
    assert all(c.code != "77000000" for c in reading.codes)
    assert reading.judged["cpvDivisionWithheld"] == "NATURE_CONFLICT"
    kept = _read({OFFER_NATURE.question_id: "SUPPLIES", CPV_DIVISION.question_id: "24"})
    assert any(c.code == "24000000" for c in kept.codes)


def test_coherent_or_unknown_nature_keeps_the_judgment() -> None:
    supplier = _read({OFFER_NATURE.question_id: "SUPPLIES",
                      CATALOG_ACTIVITY.question_id: "fertilisers-soil-amendments"})  # fmt: skip
    assert supplier.findings[0].activity_id == "fertilisers-soil-amendments"
    gardener = _read({OFFER_NATURE.question_id: "SERVICES",
                      CATALOG_ACTIVITY.question_id: "landscaping-gardening"})  # fmt: skip
    assert gardener.findings[0].activity_id == "landscaping-gardening"
    # UNCLEAR and MIXED nature are unknown: they never withhold, never confirm.
    for nature in ("UNCLEAR", "MIXED"):
        reading = _read({OFFER_NATURE.question_id: nature,
                         CATALOG_ACTIVITY.question_id: "landscaping-gardening"})  # fmt: skip
        assert "catalogActivityWithheld" not in reading.judged


def test_the_question_tells_the_evaluator_what_each_activity_is_and_never_the_closest() -> None:
    labels = dict(CATALOG_ACTIVITY.criteria)
    assert "supplies goods" in labels["fertilisers-soil-amendments"]
    assert "performs services" in labels["landscaping-gardening"]
    assert "never the closest" in CATALOG_ACTIVITY.instructions
    reading = _read({OFFER_NATURE.question_id: "SUPPLIES", CATALOG_ACTIVITY.question_id: "NONE"})
    assert reading.judged["catalogGap"] == "NONE"


#: Measured after #290: the shop also read as landscaping from an article headline on its home.
SHOP_WITH_ARTICLE = (
    "<html lang='es'><head><title>Té de humus de lombriz | Ejemplo</title></head><body>"
    "<h1>Tienda especializada en té de humus de lombriz para huerto y jardín.</h1>"
    "<h2>Mantenimiento de jardines con bajo residuo visible: por qué importa en zonas premium</h2>"
    "</body></html>"
)


def _arbitrate(nature: str):  # type: ignore[no-untyped-def]
    page = read_page(url="https://shop.example.com/", html=SHOP_WITH_ARTICLE, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    found = deterministic_activity([page])
    assert {f.activity_id for f in found} >= {
        "fertilisers-soil-amendments",
        "landscaping-gardening",
    }
    plan = plan_activity_batch("https://shop.example.com/", [page], known_scopes=(),
                               deterministic=found)  # fmt: skip
    assert plan is not None and OFFER_NATURE in plan.batch.questions

    def rule(batch, question):  # type: ignore[no-untyped-def]
        if question.question_id == OFFER_NATURE.question_id:
            return (nature, 0.95)
        return ("UNCLEAR", 0.9) if "UNCLEAR" in question.labels else (question.labels[-1], 0.9)

    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-17")  # fmt: skip
    cascade = SemanticCascade(
        judge=FakeSystemOne(rule), ledger=CostLedger(prices=(price,)),
        memory=InMemoryJudgmentMemory(),
        budget=SemanticBudget(max_system_one_input_tokens=200_000, max_reasoning_calls=0),
    )  # fmt: skip
    outcome = cascade.run([plan.batch], now=NOW)[plan.batch.batch_id]
    return interpret_activity(plan, outcome, [page], model="jev-1.13.0")


def test_the_offer_nature_arbitrates_between_the_lexicons_own_readings() -> None:
    assert _arbitrate("SUPPLIES").withheld == ("landscaping-gardening",)
    assert _arbitrate("SERVICES").withheld == ("fertilisers-soil-amendments",)
    for unknown in ("MIXED", "UNCLEAR"):
        assert _arbitrate(unknown).withheld == ()
    # A nature none of its readings has never erases them all: unknown, not empty.
    assert _arbitrate("WORKS").withheld == ()


def test_readings_of_one_nature_never_ask() -> None:
    page = read_page(url="https://x.example.com/", html=SHOP, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    one = deterministic_activity([read_page(
        url="https://x.example.com/", observed_at=NOW, content_fingerprint="t", artifact_ref=None,
        html="<html><body><h1>Tienda de té de humus de lombriz y abono ecológico.</h1></body></html>",
    )])  # fmt: skip
    assert one and not natures_disagree(one)
    plan = plan_activity_batch("https://x.example.com/", [page], known_scopes=(), deterministic=one)
    assert plan is None or OFFER_NATURE not in plan.batch.questions


def test_a_declared_service_area_still_asks_where_the_organization_is() -> None:
    # Found on axignal.com (2026-10-17): "Worldwide" is where it sells, not where it is.
    html = ("<html><body><h1>Observatorio económico</h1><p>Empresa española con sede en Madrid, "
            "España, que observa organizaciones de todo el mundo.</p></body></html>")  # fmt: skip
    page = read_page(url="https://a.example.com/", html=html, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    from application.observation_intelligence.contracts import TaxonomyCode

    worldwide = (TaxonomyCode("GEO", "WORLD"),)
    asked = plan_activity_batch("https://a.example.com/", [page], known_scopes=worldwide,
                                deterministic=(), premises_known=False)  # fmt: skip
    assert asked is not None
    assert any(q.question_id == "fo_operating_location" for q in asked.batch.questions)
    known = plan_activity_batch("https://a.example.com/", [page], known_scopes=worldwide,
                                deterministic=(), premises_known=True)  # fmt: skip
    assert known is None or all(
        q.question_id != "fo_operating_location" for q in known.batch.questions
    )


def test_an_unclear_offer_nature_is_named_for_presence_and_mixed_is_not() -> None:
    # Spec 084, found on biocultor.com: MIXED 0.59 vs SUPPLIES 0.41, too uncertain to use.
    page = read_page(url="https://shop.example.com/", html=SHOP_WITH_ARTICLE, observed_at=NOW,
                     content_fingerprint="t", artifact_ref=None)  # fmt: skip
    found = deterministic_activity([page])
    plan = plan_activity_batch("https://shop.example.com/", [page], known_scopes=(),
                               deterministic=found)  # fmt: skip
    assert plan is not None

    def read(answer: tuple[str, float]):  # type: ignore[no-untyped-def]
        def rule(batch, question):  # type: ignore[no-untyped-def]
            if question.question_id == OFFER_NATURE.question_id:
                return answer
            return ("UNCLEAR", 0.9) if "UNCLEAR" in question.labels else (question.labels[-1], 0.9)

        price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                            Decimal("0"), "test", "2026-10-17")  # fmt: skip
        cascade = SemanticCascade(
            judge=FakeSystemOne(rule), ledger=CostLedger(prices=(price,)),
            memory=InMemoryJudgmentMemory(),
            budget=SemanticBudget(max_system_one_input_tokens=200_000, max_reasoning_calls=0),
        )  # fmt: skip
        outcome = cascade.run([plan.batch], now=NOW)[plan.batch.batch_id]
        return interpret_activity(plan, outcome, [page], model="jev-1.13.0")

    # A split answer reads a diversified organization, not an unclear website (self-check
    # 2026-10-17: Ferrovial and Iberdrola were wrongly told their website was unclear).
    assert "offerNatureUnclear" not in read(("MIXED", 0.59)).judged
    assert "offerNatureUnclear" not in read(("UNCLEAR", 0.5)).judged
    assert read(("UNCLEAR", 0.9)).judged["offerNatureUnclear"] == "UNCLEAR"
    assert "offerNatureUnclear" not in read(("MIXED", 0.9)).judged  # it does both, clearly
    assert "offerNatureUnclear" not in read(("SUPPLIES", 0.9)).judged
