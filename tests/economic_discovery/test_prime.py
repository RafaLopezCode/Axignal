from __future__ import annotations

import pytest

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    SemanticPrimitive,
    StateChange,
    TypingDimensionContract,
)
from application.economic_discovery.prime import (
    DimensionRoutingPolicy,
    PrimeRoute,
    build_initial_prime_control_plan,
    build_prime_control_plan,
)
from application.economic_discovery.research_value import (
    ResearchValueContext,
    ResearchValueDisposition,
    ResearchValuePolicy,
    ResearchValueSignal,
    decide_research_value,
)


def _contract(
    dimension_id: str,
    *,
    requirements: tuple[str, ...],
    dependencies: tuple[str, ...],
) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.CHOICE,
        question=f"Resolve {dimension_id}",
        state_requirements=requirements,
        dependencies=dependencies,
        mutually_exclusive=True,
        abstention_policy="preserve UNKNOWN",
    )


def _change(*fields: str) -> StateChange:
    return StateChange(
        subject_id="org:1",
        changed_fields=frozenset(fields),
        previous_fingerprint="before",
        current_fingerprint="after",
    )


def test_prime_routes_answerable_dimension_to_declared_mechanism() -> None:
    contract = _contract(
        "market_mode",
        requirements=("document.market",),
        dependencies=("document.market",),
    )

    plan = build_prime_control_plan(
        change=_change("document.market"),
        contracts=(contract,),
        available_state_fields=frozenset({"document.market"}),
        routing_policies=(
            DimensionRoutingPolicy(
                dimension_id="market_mode",
                version="routing-v1",
                answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
            ),
        ),
    )

    assert plan.subject_id == "org:1"
    assert plan.state_fingerprint == "after"
    assert len(plan.items) == 1
    item = plan.items[0]
    assert item.disposition is DimensionDisposition.ANSWERABLE
    assert item.route is PrimeRoute.STRUCTURED_EVALUATOR
    assert item.missing_requirements == ()


def test_prime_routes_missing_state_to_adaptive_research() -> None:
    contract = _contract(
        "capability",
        requirements=("document.capability", "source.currentness"),
        dependencies=("document.capability",),
    )

    decision = decide_research_value(
        context=ResearchValueContext(
            subject_id="org:1",
            state_fingerprint="after",
            dimension_id="capability",
            missing_requirements=("source.currentness",),
            value_signals=frozenset({ResearchValueSignal.MATERIALITY}),
            rights_permit=True,
            capability_available=True,
            budget_permits=True,
            known_source_available=False,
        ),
        policy=ResearchValuePolicy(
            policy_id="research-value",
            version="1",
            research_signals=frozenset({ResearchValueSignal.MATERIALITY}),
        ),
    )

    plan = build_prime_control_plan(
        change=_change("document.capability"),
        contracts=(contract,),
        available_state_fields=frozenset({"document.capability"}),
        routing_policies=(
            DimensionRoutingPolicy(
                dimension_id="capability",
                version="routing-v1",
                answerable_route=PrimeRoute.DETERMINISTIC,
            ),
        ),
        research_decisions=(decision,),
    )

    item = plan.items[0]
    assert item.disposition is DimensionDisposition.NOT_ANSWERABLE
    assert item.research_disposition is ResearchValueDisposition.RESEARCH_NOW
    assert item.route is PrimeRoute.ADAPTIVE_RESEARCH
    assert item.missing_requirements == ("source.currentness",)


def test_prime_fails_closed_when_impacted_dimension_has_no_policy() -> None:
    contract = _contract(
        "relationship",
        requirements=("document.relationship",),
        dependencies=("document.relationship",),
    )

    with pytest.raises(ValueError, match="missing Prime routing policy"):
        build_prime_control_plan(
            change=_change("document.relationship"),
            contracts=(contract,),
            available_state_fields=frozenset({"document.relationship"}),
            routing_policies=(),
        )


def test_prime_ignores_unaffected_dimensions() -> None:
    contract = _contract(
        "market_mode",
        requirements=("document.market",),
        dependencies=("document.market",),
    )

    plan = build_prime_control_plan(
        change=_change("document.title"),
        contracts=(contract,),
        available_state_fields=frozenset({"document.market", "document.title"}),
        routing_policies=(),
    )

    assert plan.items == ()


def test_answerable_policy_cannot_delegate_routing_to_adaptive_research() -> None:
    with pytest.raises(ValueError, match="answerable dimensions"):
        DimensionRoutingPolicy(
            dimension_id="market_mode",
            version="routing-v1",
            answerable_route=PrimeRoute.ADAPTIVE_RESEARCH,
        )


def test_initial_prime_plan_routes_only_answerable_dimensions() -> None:
    answerable = _contract(
        "market_mode",
        requirements=("document.market",),
        dependencies=("document.market",),
    )
    missing = _contract(
        "reputation",
        requirements=("document.reviews",),
        dependencies=("document.reviews",),
    )

    plan = build_initial_prime_control_plan(
        subject_id="org:1",
        state_fingerprint="state:1",
        contracts=(answerable, missing),
        available_state_fields=frozenset({"document.market"}),
        routing_policies=(
            DimensionRoutingPolicy(
                dimension_id="market_mode",
                version="routing-v1",
                answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
            ),
            DimensionRoutingPolicy(
                dimension_id="reputation",
                version="routing-v1",
                answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
            ),
        ),
    )

    assert [item.dimension_id for item in plan.items] == ["market_mode"]
    assert plan.items[0].disposition is DimensionDisposition.ANSWERABLE


def test_prime_fails_closed_when_gap_has_no_research_value_decision() -> None:
    contract = _contract(
        "capability",
        requirements=("document.capability", "source.currentness"),
        dependencies=("document.capability",),
    )

    with pytest.raises(ValueError, match="missing Research Value decision"):
        build_prime_control_plan(
            change=_change("document.capability"),
            contracts=(contract,),
            available_state_fields=frozenset({"document.capability"}),
            routing_policies=(
                DimensionRoutingPolicy(
                    dimension_id="capability",
                    version="routing-v1",
                    answerable_route=PrimeRoute.DETERMINISTIC,
                ),
            ),
        )


def test_prime_rejects_stale_research_value_decision() -> None:
    contract = _contract(
        "capability",
        requirements=("document.capability", "source.currentness"),
        dependencies=("document.capability",),
    )
    stale = decide_research_value(
        context=ResearchValueContext(
            subject_id="org:1",
            state_fingerprint="old-state",
            dimension_id="capability",
            missing_requirements=("source.currentness",),
            value_signals=frozenset({ResearchValueSignal.MATERIALITY}),
            rights_permit=True,
            capability_available=True,
            budget_permits=True,
            known_source_available=False,
        ),
        policy=ResearchValuePolicy(
            policy_id="research-value",
            version="1",
            research_signals=frozenset({ResearchValueSignal.MATERIALITY}),
        ),
    )

    with pytest.raises(ValueError, match="does not match current gap state"):
        build_prime_control_plan(
            change=_change("document.capability"),
            contracts=(contract,),
            available_state_fields=frozenset({"document.capability"}),
            routing_policies=(
                DimensionRoutingPolicy(
                    dimension_id="capability",
                    version="routing-v1",
                    answerable_route=PrimeRoute.DETERMINISTIC,
                ),
            ),
            research_decisions=(stale,),
        )
