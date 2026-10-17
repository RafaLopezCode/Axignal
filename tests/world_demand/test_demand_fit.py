"""Jev judges the fit of open demand off the read path; live demand only recalls it (spec 075).

Found on the truth set (2026-10-15): a fan maker (Zitron) was offered building ventilation
works, and AXIGNAL a foster-family service, because codes match work that is not theirs.
The narrow fit judgment exists since spec 062 but never reached the list subscribers read.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from application.observation_intelligence.contracts import TaxonomyCode
from application.observation_intelligence.findings import ProcurementRecord
from application.observation_intelligence.semantic_screen import FIT, FitRecall
from application.semantic_layer.cascade import SemanticCascade
from application.semantic_layer.ledger import CostLedger, PricePolicy, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from application.world_demand.fit import catalog_capabilities, judge_pairs, open_pairs
from application.world_demand.live import LiveDemandReader, apply_live_demand
from tests.semantic_layer.fakes import FakeSystemOne
from tests.world_demand.test_live_demand import NOW, OPEN, SCOPES, Store

RESEARCH = {"capabilityId": "market-research", "demandCodes": [["CPV", "79310000"]]}
FITS = {"survey": ("CORE", 0.9), "foster": ("UNRELATED", 0.9), "stats": ("ADJACENT", 0.8),
        "doubt": ("UNRELATED", 0.4), "maybe": ("CORE", 0.4)}  # fmt: skip


def _call(rid: str, days_ago: int = 3, cpv: str = "79311000") -> ProcurementRecord:
    return ProcurementRecord(
        record_id=rid, source_id="es-placsp", kind=OPEN, title=f"Servicio {rid}",
        buyer_name=f"Comprador {rid}", places=(TaxonomyCode("GEO", "EU/ES/ES3/ES30"),),
        demand_codes=(TaxonomyCode("CPV", cpv),), published_at=NOW - timedelta(days=days_ago),
        source_url=f"https://contrataciondelestado.es/{rid}", deadline="2026-11-01",
    )  # fmt: skip


def _judge() -> FakeSystemOne:
    def rule(batch, question):  # type: ignore[no-untyped-def]
        rid = str(batch.state["tender"]["title"]).split()[-1]
        if question.question_id == FIT.question_id:
            return FITS.get(rid, ("CORE", 0.9))
        return ("UNCLEAR", 0.9)

    return FakeSystemOne(rule)


def _cascade(judge: FakeSystemOne, memory: InMemoryJudgmentMemory) -> SemanticCascade:
    price = PricePolicy(
        "test.v1",
        "typesafe-system-one",
        "jev-1.13.0",
        Decimal("0.042"),
        Decimal("0"),
        "test",
        "2026-10-15",
    )
    return SemanticCascade(
        judge=judge, ledger=CostLedger(prices=(price,)), memory=memory,
        budget=SemanticBudget(max_system_one_input_tokens=200_000, max_reasoning_calls=0),
    )  # fmt: skip


def _judged(calls: list[ProcurementRecord]) -> FitRecall:
    memory = InMemoryJudgmentMemory()
    judge = _judge()
    pairs = open_pairs(calls, catalog_capabilities(["market-research"]), today="2026-10-12")
    run = judge_pairs(pairs, _cascade(judge, memory), now=NOW)
    assert run.pairs == len(calls) and len(judge.calls) == len(calls)
    # Judged once: a second run is served from memory, without a provider call.
    again = judge_pairs(pairs, _cascade(judge, memory), now=NOW)
    assert again.from_memory == len(calls) and len(judge.calls) == len(calls)
    return FitRecall(memory=memory, evaluators=(("typesafe-system-one", "jev-1.13.0"),))


def test_unrelated_calls_are_set_aside_listed_and_the_rest_ordered_by_fit() -> None:
    calls = [_call("survey", 20), _call("foster", 1), _call("stats", 1), _call("doubt", 1),
             _call("unjudged", 2)]  # fmt: skip
    recall = _judged(calls[:4])  # "unjudged" is published after the run: no judgment yet
    live = LiveDemandReader(
        Store(calls),
        sources=("es-placsp",),
        clock=lambda: NOW,
        fit=recall,  # type: ignore[arg-type]
    ).read([RESEARCH], SCOPES)
    assert live is not None
    shown = [(c["title"], c["fit"]) for c in live.candidates]
    # CORE first, then not judged, then in doubt (spec 092: an uncertain judgment is neither
    # its label nor set aside), then ADJACENT.
    assert shown == [("Servicio survey", "CORE"), ("Servicio unjudged", None),
                     ("Servicio doubt", "UNCERTAIN"), ("Servicio stats", "ADJACENT")]  # fmt: skip
    doubt = next(c for c in live.candidates if c["fit"] == "UNCERTAIN")
    assert doubt["focus"] == "OTHER" and "UNCERTAIN_FIT" in doubt["otherReasons"]  # type: ignore[operator]
    assert doubt["fitBy"]["leaning"] == "UNRELATED"  # type: ignore[index]
    assert [s["title"] for s in live.set_aside] == ["Servicio foster"] and live.set_aside_total == 1
    assert live.total == 4  # set aside, never counted as an opportunity nor deleted
    view = apply_live_demand(
        {"discoveries": [{"kind": "DEMAND", "code": "POTENTIAL_DEMAND"}]},
        {"capabilities": [RESEARCH], "attentionScopes": [{"jurisdiction": "EU/ES"}]},
        LiveDemandReader(Store(calls), sources=("es-placsp",), clock=lambda: NOW, fit=recall),  # type: ignore[arg-type]
        now=NOW,
    )
    demand = view["demand"]
    assert demand["setAsideByFit"] == 1 and demand["setAside"][0]["fitBy"]["model"] == "jev-1.13.0"  # type: ignore[index]


def test_without_judgments_live_demand_is_exactly_as_before() -> None:
    calls = [_call("survey", 20), _call("foster", 1)]
    plain = LiveDemandReader(Store(calls), sources=("es-placsp",), clock=lambda: NOW)  # type: ignore[arg-type]
    empty = FitRecall(
        memory=InMemoryJudgmentMemory(), evaluators=(("typesafe-system-one", "jev-1.13.0"),)
    )
    recalled = LiveDemandReader(Store(calls), sources=("es-placsp",), clock=lambda: NOW, fit=empty)  # type: ignore[arg-type]
    a, b = plain.read([RESEARCH], SCOPES), recalled.read([RESEARCH], SCOPES)
    assert a is not None and b is not None
    assert [c["title"] for c in a.candidates] == [c["title"] for c in b.candidates]
    assert b.set_aside == () and all(c["fit"] is None for c in b.candidates)


def test_a_judgment_by_another_model_is_never_reused() -> None:
    recall = _judged([_call("foster")])
    other = FitRecall(memory=recall.memory, evaluators=(("typesafe-system-one", "jev-2.0.0"),))
    assert recall(_call("foster"), "market-research")["fit"] == "UNRELATED"  # type: ignore[index]
    assert other(_call("foster"), "market-research") is None


def test_only_open_calls_matching_by_code_are_paired_newest_first() -> None:
    closed = ProcurementRecord(
        record_id="old", source_id="es-placsp", kind=OPEN, title="Servicio old", buyer_name=None,
        places=(), demand_codes=(TaxonomyCode("CPV", "79311000"),), published_at=NOW,
        source_url="https://contrataciondelestado.es/old", deadline="2026-10-01",
    )  # fmt: skip
    pairs = open_pairs(
        [_call("a", 5), _call("b", 1), _call("works", 1, cpv="45000000"), closed],
        catalog_capabilities(["market-research"]),
        today="2026-10-12",
    )
    assert [(r.record_id, c) for r, c in pairs] == [
        ("b", "market-research"),
        ("a", "market-research"),
    ]


def test_the_fit_budget_is_bounded_and_off_without_the_layer(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from tools.runtime.demand_fit import run_demand_fit
    from tools.runtime.semantic_layer import fit_cascade_factory_from_env

    key = tmp_path / "key"
    key.write_text("x", encoding="utf-8")
    base = {"AXIGNAL_SEMANTIC_LAYER_ENABLED": "true", "AXIGNAL_TYPESAFE_API_KEY_FILE": str(key),
            "AXIGNAL_SEMANTIC_RUN_TOKEN_BUDGET": "12000"}  # fmt: skip
    default = fit_cascade_factory_from_env(base, data_dir=tmp_path)
    assert default is not None and default().budget.max_system_one_input_tokens == 500_000
    capped = fit_cascade_factory_from_env(
        {**base, "AXIGNAL_SEMANTIC_FIT_TOKEN_BUDGET": "9000000"}, data_dir=tmp_path
    )
    assert capped is not None and capped().budget.max_system_one_input_tokens == 2_000_000
    assert (
        fit_cascade_factory_from_env(
            {**base, "AXIGNAL_SEMANTIC_FIT_TOKEN_BUDGET": "0"}, data_dir=tmp_path
        )
        is None
    )
    assert run_demand_fit(tmp_path, values={}) == {"state": "LAYER_DISABLED"}


def test_a_doubtful_judgment_leaning_core_stays_unjudged() -> None:
    calls = [_call("maybe", 1)]
    recall = _judged(calls)
    assert recall(calls[0], "market-research") is None  # never promoted, never demoted
