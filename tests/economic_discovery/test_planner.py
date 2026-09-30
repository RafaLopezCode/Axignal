from application.economic_discovery import (
    DimensionDisposition,
    ObservationIngress,
    ObservationMode,
    SemanticPrimitive,
    StateChange,
    TypingDimensionContract,
    assess_dimension_work,
    build_work_plan,
    route_retrieval,
)


def _contract(
    dimension_id: str,
    requirements: tuple[str, ...],
    dependencies: tuple[str, ...],
) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.NOUL,
        question=f"Does {dimension_id} apply?",
        state_requirements=requirements,
        dependencies=dependencies,
        mutually_exclusive=False,
        abstention_policy="NOT_ANSWERABLE",
    )


def test_bound_direct_observation_bypasses_turboquant() -> None:
    ingress = ObservationIngress("obs:1", ObservationMode.DIRECT_EVENT, "org:b", True)
    assert route_retrieval(ingress) is False


def test_unbound_universe_discovery_requires_retrieval() -> None:
    ingress = ObservationIngress("obs:2", ObservationMode.DETERMINISTIC_SENSOR, None, True)
    assert route_retrieval(ingress) is True


def test_plan_only_re_evaluates_impacted_dimensions_and_researches_missing_state() -> None:
    ingress = ObservationIngress("obs:3", ObservationMode.DIRECT_EVENT, "org:b", False)
    change = StateChange(
        subject_id="org:b",
        changed_fields=frozenset({"tenders"}),
        previous_fingerprint="s1",
        current_fingerprint="s2",
    )
    contracts = (
        _contract("CUSTOMER_ROLE", ("candidate_context", "current_demand"), ("tenders",)),
        _contract("SUPPLIER_ROLE", ("candidate_context",), ("supply_evidence",)),
        _contract("NEED_CLASS", ("candidate_context",), ("tenders",)),
    )
    plan = build_work_plan(
        ingress=ingress,
        change=change,
        contracts=contracts,
        available_state_fields=frozenset({"candidate_context"}),
    )

    assert plan.retrieval_required is False
    assert plan.state_mutation_required is True
    assert [item.dimension_id for item in plan.evaluation] == ["CUSTOMER_ROLE", "NEED_CLASS"]
    assert plan.evaluation[0].disposition is DimensionDisposition.NOT_ANSWERABLE
    assert plan.evaluation[1].disposition is DimensionDisposition.ANSWERABLE
    assert plan.research_dimensions == ("CUSTOMER_ROLE",)


def test_initial_dimension_assessment_includes_completely_missing_dimensions() -> None:
    contract = TypingDimensionContract(
        dimension_id="reputation",
        version="1",
        semantic_target="public reputation",
        primitive=SemanticPrimitive.CHOICE,
        question="What public reputation state is supported?",
        state_requirements=("document.reviews.visible_text",),
        dependencies=("document.reviews.visible_text",),
        mutually_exclusive=False,
        abstention_policy="preserve UNKNOWN",
    )

    work = assess_dimension_work(
        contracts=(contract,),
        available_state_fields=frozenset(),
    )

    assert len(work) == 1
    assert work[0].dimension_id == "reputation"
    assert work[0].disposition is DimensionDisposition.NOT_ANSWERABLE
    assert work[0].missing_requirements == ("document.reviews.visible_text",)
