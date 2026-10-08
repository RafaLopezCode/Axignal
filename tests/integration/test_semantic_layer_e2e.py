"""Spec 062 end to end through the real subscriber runtime (no network).

Deterministic code finds TED demand by codes and places; one System One call per
(tender, capability class) judges fit and delivery mode; the Economic Relevance Gate
uses that delivery mode; confidently unrelated demand is counted, not shown; doubtful
fit escalates to the reasoning model within its budget; a second Focus meeting the
same tenders reuses the judgments without new calls.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.observation_intelligence.semantic_screen import SemanticDemandScreen
from application.semantic_layer.cascade import CascadePolicy, SemanticCascade
from application.semantic_layer.ledger import CostLedger, SemanticBudget
from application.semantic_layer.memory import InMemoryJudgmentMemory
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId
from tests.integration.test_economic_garden_e2e import _Clock, _subscriber, world  # noqa: F401
from tests.semantic_layer.fakes import FakeReasoning, FakeSystemOne
from tools.runtime.observation_daily import build_economic_runtime
from tools.runtime.semantic_layer import semantic_screen_from_env
from tools.runtime.subscriber_observation import (
    ConfiguredSubscriberObservationPlanReader,
    load_observation_attention,
)


def _title(batch) -> str:
    return str(batch.state["tender"]["title"]).lower()


def _screen(judge, *, memory=None, reasoning=None, calls=0) -> SemanticDemandScreen:
    memory = memory if memory is not None else InMemoryJudgmentMemory()
    return SemanticDemandScreen(
        lambda: SemanticCascade(
            judge=judge,
            ledger=CostLedger(),
            budget=SemanticBudget(1_000_000, calls),
            policy=CascadePolicy(escalable=frozenset({"tender_capability_fit"})),
            memory=memory,
            escalation=reasoning,
        )
    )


def _observe(tmp_path: Path, facade: Any, plan: Path, name: str, screen) -> dict[str, Any]:
    token, focus = _subscriber(facade, tmp_path, f"subject:{name}", f"add:{name}")
    member = facade.identity.authenticate(token)
    context = TrustedRequestContext(member.principal_id, member.tenant_id)
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    economic.semantic_screen = screen
    clock = _Clock(datetime.now(UTC) + timedelta(minutes=5))
    reader = ConfiguredSubscriberObservationPlanReader(
        economic=economic, clock=clock, attention=load_observation_attention(plan)
    )
    execution = reader.observation_plan_for(context, XeedId(focus))  # type: ignore[arg-type]
    assert execution is not None
    economic.execute_observation_loop(
        context, XeedId(focus), observation_context=execution.observation_context,
        strategy=execution.strategy, adapters=execution.adapters, coverage=execution.coverage,
        learning=execution.learning, registry=execution.registry,
    )  # fmt: skip
    projection = economic.read(context, XeedId(focus), clock.now()).projection
    return dict(projection.get("cognition") or {})


def _core_onsite(batch, question):
    if question.question_id == "tender_capability_fit":
        return ("CORE", 0.91) if "fotovolt" in _title(batch) else ("UNRELATED", 0.93)
    return ("CUSTOMER_SITE", 0.9)


def test_jev_judges_fit_and_delivery_and_the_gate_uses_it(tmp_path: Path, world) -> None:  # noqa: F811
    facade, plan = world
    judge = FakeSystemOne(_core_onsite)
    cognition = _observe(tmp_path, facade, plan, "screen", _screen(judge))
    (getafe,) = [o for o in cognition["opportunities"] if "Getafe" in str(o["buyer"])]
    screen = getafe["semanticScreen"]
    assert screen["fit"] == "CORE" and screen["requiredModes"] == ["CUSTOMER_SITE"]
    assert screen["nonAuthoritative"] is True and getafe["epistemic"] in {"POTENTIAL", "UNKNOWN"}
    assert getafe["relevance"]["scope"] == "OPERATING_REACH"  # on-site work inside its reach
    layer = cognition["semanticLayer"]
    (line,) = layer["usage"]["lines"]
    assert line["evaluator"] == "typesafe-system-one" and line["calls"] == len(judge.calls)
    assert all(len(batch.questions) == 2 for batch in judge.calls)  # fit + delivery per call
    assert layer["judgments"]["DECIDED"] >= 2


def test_confidently_unrelated_demand_is_counted_not_shown(tmp_path: Path, world) -> None:  # noqa: F811
    facade, plan = world

    def depuradoras_unrelated(batch, question):
        if question.question_id == "tender_capability_fit" and "depuradora" in _title(batch):
            return ("UNRELATED", 0.95)
        return _core_onsite(batch, question)

    cognition = _observe(
        tmp_path, facade, plan, "unrelated", _screen(FakeSystemOne(depuradoras_unrelated))
    )
    assert cognition["relevanceFiltered"].get("SEMANTIC_UNRELATED", 0) >= 1
    assert not any("depuradora" in str(o["title"]).lower() for o in cognition["opportunities"])
    assert any("Getafe" in str(o["buyer"]) for o in cognition["opportunities"])


def test_doubtful_fit_escalates_to_luna_within_its_budget(tmp_path: Path, world) -> None:  # noqa: F811
    facade, plan = world

    def doubtful(batch, question):
        if question.question_id == "tender_capability_fit":
            return ("ADJACENT", 0.42)
        return ("CUSTOMER_SITE", 0.9)

    luna = FakeReasoning(lambda q: "CORE")
    cognition = _observe(
        tmp_path,
        facade,
        plan,
        "escalate",
        _screen(FakeSystemOne(doubtful), reasoning=luna, calls=1),
    )
    assert len(luna.calls) == 1
    escalated = [
        item
        for o in cognition["opportunities"]
        for item in o["semanticScreen"]["fitByCapability"].values()
        if item["resolution"] == "ESCALATED"
    ]
    assert escalated and escalated[0]["answer"]["source"] == "REASONING"
    lines = {line["evaluator"]: line for line in cognition["semanticLayer"]["usage"]["lines"]}
    assert lines["luna-responses"]["calls"] == 1


def test_a_second_focus_reuses_the_same_world_judgments(tmp_path: Path, world) -> None:  # noqa: F811
    facade, plan = world
    judge = FakeSystemOne(_core_onsite)
    memory = InMemoryJudgmentMemory()
    _observe(tmp_path, facade, plan, "first", _screen(judge, memory=memory))
    calls = len(judge.calls)
    second = _observe(tmp_path, facade, plan, "second", _screen(judge, memory=memory))
    assert len(judge.calls) == calls  # no new System One call: shared world, shared judgment
    assert second["semanticLayer"]["usage"]["memoryHits"] >= 2
    assert second["semanticLayer"]["usage"]["lines"] == []


def test_a_delivery_mode_the_channel_lacks_downgrades_reach_without_inventing_a_no(
    tmp_path: Path,
    world,  # noqa: F811
) -> None:
    facade, plan = world

    def remote(batch, question):
        if question.question_id == "tender_capability_fit":
            return ("CORE", 0.9)
        return ("REMOTE_OR_DIGITAL", 0.9)

    cognition = _observe(tmp_path, facade, plan, "remote", _screen(FakeSystemOne(remote)))
    (getafe,) = [o for o in cognition["opportunities"] if "Getafe" in str(o["buyer"])]
    # The installer only evidences on-site work. Remote delivery is not evidenced, which
    # is not evidence that it cannot: reach becomes UNRESOLVED, never OPERATING (spec 059).
    assert getafe["semanticScreen"]["requiredModes"] == ["DIGITAL", "REMOTE"]
    assert getafe["relevance"]["scope"] == "UNRESOLVED_REACH"
    assert [c["mode"] for c in getafe["relevance"]["channels"]] == [None]


def test_composition_is_off_unless_fully_configured(tmp_path: Path) -> None:
    assert semantic_screen_from_env({}, data_dir=tmp_path) is None
    assert (
        semantic_screen_from_env({"AXIGNAL_SEMANTIC_LAYER_ENABLED": "true"}, data_dir=tmp_path)
        is None
    )
    key = tmp_path / "typesafe_api_key"
    key.write_text("not-a-real-key", encoding="utf-8")
    enabled = {
        "AXIGNAL_SEMANTIC_LAYER_ENABLED": "true",
        "AXIGNAL_TYPESAFE_API_KEY_FILE": str(key.resolve()),
    }
    assert isinstance(semantic_screen_from_env(enabled, data_dir=tmp_path), SemanticDemandScreen)
    assert (
        semantic_screen_from_env(
            {**enabled, "AXIGNAL_SEMANTIC_RUN_TOKEN_BUDGET": "0"}, data_dir=tmp_path
        )
        is None
    )
    assert (
        semantic_screen_from_env(
            {**enabled, "AXIGNAL_TYPESAFE_API_KEY_FILE": "relative"}, data_dir=tmp_path
        )
        is None
    )


def test_only_demand_that_passed_provenance_and_rights_is_sent_to_jev(
    tmp_path: Path,
    world,  # noqa: F811
    monkeypatch,
) -> None:
    # MCA §5: provider eligibility never widens Input rights. A notice whose provenance
    # fails the display gate (here: its URL is not a safe public link) is never judged.
    import application.observation_intelligence.subscriber_projection as projection

    original = projection._safe_public_url
    monkeypatch.setattr(
        projection, "_safe_public_url", lambda url: "700102" not in url and original(url)
    )
    facade, plan = world
    judge = FakeSystemOne(_core_onsite)
    cognition = _observe(tmp_path, facade, plan, "rights", _screen(judge))
    sent = " ".join(_title(batch) for batch in judge.calls)
    assert "depuradoras" not in sent and "getafe" not in sent  # buyer is not in the title
    assert any("autoconsumo" in _title(batch) for batch in judge.calls)
    assert any("Getafe" in str(o["buyer"]) for o in cognition["opportunities"])
