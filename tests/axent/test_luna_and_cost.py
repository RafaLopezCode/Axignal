from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from application.axent.grounded import CostRates, ReasoningRequest, turn_cost
from application.axent.grounded.answer import ANSWER_SCHEMA, verify
from application.axent.grounded.corpus import EvidenceItem, EvidenceKind
from application.axent.grounded.cost import avoided_cost, projections
from cognition.axent_reasoner import CognitiveGroundedReasoner
from cognition.providers.luna_responses import LunaResponsesProvider
from cognition.router.router import ModelRouter
from tests.axent.benchmark import NaiveScripted, run
from tests.axent.benchmark import main as benchmark_main
from tests.axent.fixtures import FOCUS_A, TENANT_A, ScriptedLuna
from tests.axent.test_grounded_axent import _world


class _FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text='{"claims":[{"text":"x","refs":["E1"]}],"unknowns":[],"insufficient_evidence":false}',
            usage=SimpleNamespace(input_tokens=321, output_tokens=45),
        )


def test_luna_call_has_no_tools_no_storage_and_strict_schema() -> None:
    fake = _FakeResponses()
    provider = LunaResponsesProvider(client=SimpleNamespace(responses=fake))
    reasoner = CognitiveGroundedReasoner(ModelRouter([provider]), model="gpt-6-luna")
    result = reasoner.reason(
        ReasoningRequest("r1", "SYSTEM", "<evidence>..</evidence>", ANSWER_SCHEMA, 300)
    )
    call = fake.calls[0]
    assert call["model"] == "gpt-6-luna" and "tools" not in call and call["store"] is False
    assert call["text"]["format"]["strict"] is True and call["max_output_tokens"] == 300
    assert result.input_tokens == 321 and result.output_tokens == 45 and result.payload["claims"]


def test_provider_failure_degrades_to_evidence_not_an_answer() -> None:
    class Broken:
        def create(self, **kwargs: Any) -> Any:
            raise ConnectionError("down")

    reasoner = CognitiveGroundedReasoner(
        ModelRouter([LunaResponsesProvider(client=SimpleNamespace(responses=Broken()))]),
        model="gpt-6-luna",
    )
    service, _, _ = _world()
    service.reasoner = reasoner
    turn = service.ask(TENANT_A, FOCUS_A, "¿Qué oportunidades hay?")
    assert (
        turn.answer.route.value == "EXTRACTIVE" and turn.answer.evidence and not turn.answer.claims
    )


def test_partial_pack_is_declared_and_refs_never_reach_the_text() -> None:
    service, _, luna = _world()
    service.ask(TENANT_A, FOCUS_A, "¿Qué oportunidades hay?")
    assert "shown=" in luna.requests[0].user and "in_scope=" in luna.requests[0].user
    item = EvidenceItem(
        "o", EvidenceKind.OPPORTUNITY, frozenset(), "t", "POTENTIAL", "CURRENT", None, "u", None
    )
    claims, *_ = verify({"claims": [{"text": "Hay demanda (E1).", "refs": ["E1"]}]}, {"E1": item})
    assert claims[0].text == "Hay demanda."


def test_cost_model_uses_configured_rates_only() -> None:
    rates = CostRates(Decimal("2.00"), Decimal("8.00"), "EUR")
    assert turn_cost(1_000_000, 0, rates) == Decimal("2.00")
    assert turn_cost(500, 100, rates) == Decimal("0.0018")
    assert avoided_cost(1_000_000, rates) == Decimal("2.00")
    month = projections(
        input_tokens=250, output_tokens=140, rates=rates, turns_per_subscriber_month=200
    )
    assert month["currency"] == "EUR" and Decimal(month["per_subscriber_month"]) > 0


def test_offline_benchmark_shows_material_reduction(capsys: Any) -> None:
    result = run(ScriptedLuna(), NaiveScripted())
    before = sum(r["before"]["input_tokens"] for r in result["rows"])
    after = sum(r["after"]["input_tokens"] for r in result["rows"])
    assert after * 5 < before
    assert sum(r["after"]["model_calls"] for r in result["rows"]) < len(result["rows"])
    cross = next(r for r in result["rows"] if r["query"] == "G_cross_tenant")["after"]
    assert cross["route"] == "ABSTAINED" and cross["model_calls"] == 0
    benchmark_main([])
    assert '"input_tokens_avoided"' in capsys.readouterr().out
