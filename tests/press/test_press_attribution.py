"""Is a headline that names it about this organization? Jev decides, Python keeps the last word.

Spec 085 (Reputation, CTO 2026-10-17): homonyms (another company, a person, a place)
reached an organization's reputation as "not verified" mentions. The read path recalls
remembered judgments only; the background runner judges what is missing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from application.press.attribution import ATTRIBUTION, PressAttribution
from application.press.contracts import PressItem
from application.press.mentions import press_discoveries
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from tests.semantic_layer.fakes import FakeSystemOne

NOW = datetime(2026, 10, 17, 9, tzinfo=UTC)
ABOUT = "Zitron suministra la ventilación del nuevo túnel de Madrid"
HOMONYM = "La cantante Zitron presenta su nuevo disco"
DOUBT = "Zitron, en el foco"


class Store:
    def __init__(self, items: list[PressItem]) -> None:
        self.items = items

    def items_matching(self, terms, *, since, limit=500):  # type: ignore[no-untyped-def]
        return tuple(self.items)

    def coverage(self):  # type: ignore[no-untyped-def]
        return NOW, len(self.items), 3


def _item(title: str, n: int) -> PressItem:
    return PressItem("f", "Diario", title, f"https://d.example/{n}", NOW, "es", "EU/ES")


def _rule(batch, question):  # type: ignore[no-untyped-def]
    headline = str(batch.state["headline"])
    if headline == HOMONYM:
        return ("ANOTHER_ENTITY", 0.94)
    if headline == ABOUT:
        return ("ABOUT_IT", 0.91)
    return ("ABOUT_IT", 0.3)  # too uncertain to use


def _attribution(judge: FakeSystemOne) -> PressAttribution:
    memory = InMemoryJudgmentMemory()
    price = PricePolicy("t.v1", "typesafe-system-one", "jev-1.13.0", Decimal("0.042"),
                        Decimal("0"), "test", "2026-10-17")  # fmt: skip

    def factory() -> SemanticCascade:
        return SemanticCascade(
            judge=judge, ledger=CostLedger(prices=(price,)), memory=memory,
            budget=SemanticBudget(max_system_one_input_tokens=60_000, max_reasoning_calls=0),
        )  # fmt: skip

    return PressAttribution(factory)


VIEW = {"target": {"name": "Zitron"}, "discoveries": []}


def _read(attribution: PressAttribution) -> list[dict[str, object]]:
    store = Store([_item(ABOUT, 1), _item(HOMONYM, 2), _item(DOUBT, 3)])
    check = attribution.recall("Zitron", "zitron.com", "Industrial ventilation")
    return press_discoveries(VIEW, store, now=NOW, own_domain="zitron.com", attribution=check)


def test_the_read_path_never_calls_a_provider_and_unknown_stays_as_before() -> None:
    judge = FakeSystemOne(_rule)
    attribution = _attribution(judge)
    first = _read(attribution)
    assert judge.calls == []  # recall only
    assert {str(d["statement"]) for d in first} == {ABOUT, HOMONYM, DOUBT}
    assert all("not verified" in str(d["detail"]["attribution"]) for d in first)  # type: ignore[index]


def test_judged_in_the_background_then_homonyms_are_withheld_and_doubt_is_untouched() -> None:
    judge = FakeSystemOne(_rule)
    attribution = _attribution(judge)
    _read(attribution)  # queues the three headlines
    assert attribution.run(NOW) == 3
    assert all(q.question_id == ATTRIBUTION.question_id for c in judge.calls for q in c.questions)
    shown = {str(d["statement"]): d for d in _read(attribution)}
    assert HOMONYM not in shown
    about = shown[ABOUT]["detail"]
    assert (
        about["attributionBy"] == "jev-1.13.0" and "judged to be about it" in about["attribution"]
    )  # type: ignore[index]
    assert shown[ABOUT]["epistemicState"] == "POTENTIAL" and about["notEndorsement"] is True  # type: ignore[index]
    assert "not verified" in str(shown[DOUBT]["detail"]["attribution"])  # type: ignore[index]
    assert about["withheldAsAnotherEntity"] == 1  # type: ignore[index]
    assert attribution.run(NOW) == 0  # nothing left to judge
