from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from application.economic_discovery import (
    AttentionDisposition,
    DimensionDisposition,
    DimensionRoutingPolicy,
    PrimeControlPlan,
    PrimeRoute,
    PrimeWorkItem,
    ResearchValueDecision,
    ResearchValueDisposition,
    ResearchValueReason,
    SemanticPrimitive,
    StateChange,
    TypingDimensionContract,
    build_prime_control_plan,
)
from application.economic_discovery.continuous_observation import (
    ObservationWorkState,
    SharedObservationIntent,
    intents_from_prime_plan,
    schedule_prime_research,
)
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.opportunity import derive_economic_opportunity
from domain.xignal import XignalEpistemicState
from pipeline.continuous_observation import SqliteSharedObservationWorkMemory

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def _basis() -> ExplainableBasis:
    return ExplainableBasis(
        basis_id="basis:opportunity",
        subject_id="org:supplier",
        candidate_id="candidate:1",
        semantic_target="capability_need_opportunity",
        state_fingerprint="state:1",
        contract_fingerprint="contract:1",
        evaluated_at=NOW,
        data=(
            BasisDatum(
                datum_id="datum:1",
                observation_id="obs:1",
                source_ref="https://supplier.example/capability",
                source_type="OFFICIAL_WEB",
                observed_at=NOW,
                excerpt_or_summary="Supplier states CNC machining capability.",
                contribution=BasisContribution.SUPPORTS,
            ),
        ),
        interpretation="Potential functional relevance warrants attention.",
        uncertainty="Price and capacity remain unassessed.",
    )


def _reasoning_result(*, potential: bool = True):
    evaluations = (
        SimpleNamespace(dimension_id="functional_alignment", selected_option="YES"),
        SimpleNamespace(dimension_id="delivery_reach", selected_option="YES"),
        SimpleNamespace(dimension_id="timing", selected_option="YES"),
        SimpleNamespace(dimension_id="eligibility", selected_option="YES"),
    )
    interpretation = SimpleNamespace(
        epistemic_state=(
            XignalEpistemicState.POTENTIAL if potential else XignalEpistemicState.UNKNOWN
        ),
        attention=(
            AttentionDisposition.WARRANTED_ATTENTION
            if potential
            else AttentionDisposition.INVESTIGATE
        ),
        reason_codes=(
            ("ALIGNED_CAPABILITY_NEED_WITH_REACH_WINDOW_AND_ELIGIBILITY",)
            if potential
            else ("delivery_reach:REACH_UNVERIFIED:UNKNOWN",)
        ),
        policy_version="capability-announced-need:v1",
    )
    return SimpleNamespace(
        candidate=SimpleNamespace(
            candidate_id="candidate:1",
            subject=SimpleNamespace(state=SimpleNamespace(subject_id="org:supplier")),
            activity=SimpleNamespace(state=SimpleNamespace(subject_id="org:need")),
        ),
        vector=SimpleNamespace(
            state_fingerprint="state:1",
            evaluated_at=NOW,
            evaluations=evaluations,
        ),
        interpretation=interpretation,
        basis=_basis(),
    )


def _research_plan(*, fingerprint: str = "state:1") -> PrimeControlPlan:
    return PrimeControlPlan(
        subject_id="org:supplier",
        state_fingerprint=fingerprint,
        items=(
            PrimeWorkItem(
                dimension_id="commercial_access",
                disposition=DimensionDisposition.NOT_ANSWERABLE,
                route=PrimeRoute.ADAPTIVE_RESEARCH,
                policy_version="route:v1",
                missing_requirements=("activity.buyer_access",),
                research_disposition=ResearchValueDisposition.RESEARCH_NOW,
                research_policy_id="research:value",
                research_policy_version="1",
                research_context_fingerprint="context:1",
                research_reason_codes=("DECISION_IMPACT",),
            ),
            PrimeWorkItem(
                dimension_id="functional_alignment",
                disposition=DimensionDisposition.ANSWERABLE,
                route=PrimeRoute.STRUCTURED_EVALUATOR,
                policy_version="route:v1",
                missing_requirements=(),
            ),
        ),
    )


def test_potential_opportunity_preserves_explanation_and_explicit_missing_context() -> None:
    opportunity = derive_economic_opportunity(_reasoning_result())

    assert opportunity.epistemic_state is XignalEpistemicState.POTENTIAL
    assert opportunity.attention is AttentionDisposition.WARRANTED_ATTENTION
    assert opportunity.basis == _basis()
    assert opportunity.state_fingerprint == "state:1"
    assert opportunity.subject_id == "org:supplier"
    assert opportunity.activity_id == "org:need"
    assert set(opportunity.missing_context) >= {
        "commercial_access",
        "capacity",
        "incumbent",
        "price",
    }
    assert opportunity.opportunity_id.startswith("opportunity:")


def test_unknown_opportunity_never_promotes_to_observed_or_false() -> None:
    opportunity = derive_economic_opportunity(_reasoning_result(potential=False))

    assert opportunity.epistemic_state is XignalEpistemicState.UNKNOWN
    assert opportunity.epistemic_state is not XignalEpistemicState.OBSERVED
    assert opportunity.attention is AttentionDisposition.INVESTIGATE


def test_only_adaptive_research_becomes_shared_observation_work() -> None:
    intents = intents_from_prime_plan(_research_plan())

    assert len(intents) == 1
    assert intents[0].dimension_id == "commercial_access"
    assert intents[0].missing_requirements == ("activity.buyer_access",)


def test_same_governed_intent_is_shared_across_requesters_without_double_count(
    tmp_path,
) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    plan = _research_plan()

    first = schedule_prime_research(memory, plan=plan, requester_ref="focus:a")
    second = schedule_prime_research(memory, plan=plan, requester_ref="focus:b")

    assert first == second
    work = memory.get(first[0].work_key)
    assert work is not None
    assert work.state is ObservationWorkState.PENDING
    assert work.requester_refs == ("focus:a", "focus:b")
    assert memory.enqueue(first[0], "focus:a") is False


def test_shared_work_persists_and_lease_fencing_prevents_double_execution(tmp_path) -> None:
    database = tmp_path / "work.sqlite3"
    memory = SqliteSharedObservationWorkMemory(database)
    intent = intents_from_prime_plan(_research_plan())[0]
    assert memory.enqueue(intent, "focus:a") is True

    first = memory.claim(intent.work_key, now=NOW, lease_for=timedelta(minutes=1))
    assert first is not None
    assert (
        memory.claim(
            intent.work_key, now=NOW + timedelta(seconds=10), lease_for=timedelta(minutes=1)
        )
        is None
    )

    reopened = SqliteSharedObservationWorkMemory(database)
    second = reopened.claim(
        intent.work_key, now=NOW + timedelta(minutes=2), lease_for=timedelta(minutes=1)
    )
    assert second is not None
    assert second.lease_token != first.lease_token

    assert (
        reopened.complete(
            intent.work_key,
            first.lease_token,
            completed_at=NOW + timedelta(minutes=2, seconds=10),
        )
        is False
    )
    assert (
        reopened.complete(
            intent.work_key,
            second.lease_token,
            completed_at=NOW + timedelta(minutes=2, seconds=10),
        )
        is True
    )
    work = SqliteSharedObservationWorkMemory(database).get(intent.work_key)
    assert work is not None
    assert work.state is ObservationWorkState.COMPLETE
    assert work.completed_at == NOW + timedelta(minutes=2, seconds=10)


def test_state_change_creates_new_work_identity_without_overwriting_history(tmp_path) -> None:
    memory = SqliteSharedObservationWorkMemory(tmp_path / "work.sqlite3")
    first = intents_from_prime_plan(_research_plan(fingerprint="state:1"))[0]
    changed = intents_from_prime_plan(_research_plan(fingerprint="state:2"))[0]

    assert first.work_key != changed.work_key
    assert memory.enqueue(first, "focus:a") is True
    assert memory.enqueue(changed, "focus:a") is True
    assert memory.get(first.work_key) is not None
    assert memory.get(changed.work_key) is not None


def test_work_key_is_order_independent_for_missing_requirements() -> None:
    first = SharedObservationIntent(
        subject_id="org:x",
        state_fingerprint="state:x",
        dimension_id="gap",
        missing_requirements=("b", "a"),
        research_policy_id="p",
        research_policy_version="1",
        research_context_fingerprint="ctx",
    )
    second = SharedObservationIntent(
        subject_id="org:x",
        state_fingerprint="state:x",
        dimension_id="gap",
        missing_requirements=("a", "b"),
        research_policy_id="p",
        research_policy_version="1",
        research_context_fingerprint="ctx",
    )

    assert first == second
    assert first.work_key == second.work_key


def test_state_change_routes_only_impacted_research_into_shared_work(tmp_path) -> None:
    change = StateChange(
        subject_id="org:supplier",
        changed_fields=frozenset({"market_context"}),
        previous_fingerprint="state:1",
        current_fingerprint="state:2",
    )
    contracts = (
        TypingDimensionContract(
            dimension_id="commercial_access",
            version="1",
            semantic_target="commercial_access",
            primitive=SemanticPrimitive.CHOICE,
            question="Is buyer access known?",
            state_requirements=("buyer_access",),
            dependencies=("market_context",),
            mutually_exclusive=True,
            abstention_policy="Missing access remains UNKNOWN.",
        ),
        TypingDimensionContract(
            dimension_id="capability_fit",
            version="1",
            semantic_target="capability_fit",
            primitive=SemanticPrimitive.CHOICE,
            question="Is capability fit known?",
            state_requirements=("capability",),
            dependencies=("capability",),
            mutually_exclusive=True,
            abstention_policy="Missing capability remains UNKNOWN.",
        ),
    )
    policies = tuple(
        DimensionRoutingPolicy(
            dimension_id=contract.dimension_id,
            version="route:v1",
            answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
        )
        for contract in contracts
    )
    decision = ResearchValueDecision(
        subject_id="org:supplier",
        state_fingerprint="state:2",
        dimension_id="commercial_access",
        missing_requirements=("buyer_access",),
        disposition=ResearchValueDisposition.RESEARCH_NOW,
        policy_id="research:value",
        policy_version="1",
        context_fingerprint="context:changed-market",
        reason_codes=(ResearchValueReason.DECISION_IMPACT,),
    )
    plan = build_prime_control_plan(
        change=change,
        contracts=contracts,
        available_state_fields=frozenset(),
        routing_policies=policies,
        research_decisions=(decision,),
    )
    memory = SqliteSharedObservationWorkMemory(tmp_path / "change-work.sqlite3")

    intents = schedule_prime_research(memory, plan=plan, requester_ref="focus:a")

    assert tuple(item.dimension_id for item in plan.items) == ("commercial_access",)
    assert tuple(item.dimension_id for item in intents) == ("commercial_access",)
    assert memory.get(intents[0].work_key) is not None
