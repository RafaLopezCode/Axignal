from __future__ import annotations

from datetime import UTC, datetime

from application.economic_discovery import (
    DimensionRoutingPolicy,
    LearningCost,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
    PrimeRoute,
    ResearchValueContext,
    ResearchValueDisposition,
    ResearchValuePolicy,
    ResearchValueSignal,
    SemanticPrimitive,
    TypingDimensionContract,
    decide_research_value,
)
from application.source_representation import RichStateDatum, compile_rich_subject_state
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination.bootstrap import (
    BootstrapDisposition,
    BootstrapPolicy,
    BootstrapSourceCandidate,
    build_bootstrap_plan,
)
from application.xeed_germination.learning import bootstrap_learning_event
from domain.organizations.model import Organization
from domain.tenancy.model import Principal
from domain.xeed.model import Xeed

NOW = datetime(2026, 9, 30, tzinfo=UTC)


class Principals:
    def get_principal(self, principal_id: str) -> Principal | None:
        return Principal(id=principal_id)


class Memberships:
    def has_membership(self, principal_id: str, tenant_id: str) -> bool:
        return True


class Xeeds:
    def get_xeed(self, xeed_id: str) -> Xeed | None:
        return Xeed(xeed_id, "tenant:1", "org:1")


class Organizations:
    def get_organization(self, organization_id: str) -> Organization | None:
        return Organization(organization_id, "Acme Industrial")


def _seed():
    xeed = AuthorizedXeedReader(Principals(), Memberships(), Xeeds()).read(
        TrustedRequestContext("principal:1", "tenant:1"),
        "xeed:1",
    )
    return AuthorizedXeedOrganizationReader(Organizations()).read(xeed)


def _rich_state(*fields: tuple[str, str]):
    return compile_rich_subject_state(
        subject_id="org:1",
        contributions=tuple(
            RichStateDatum(
                name=name,
                value=value,
                observation_id="obs:1",
                representation_id="repr:1",
                source_ref="https://acme.example/",
                observed_at=NOW,
            )
            for name, value in fields
        ),
    )


def _contract() -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id="market_mode",
        version="1",
        semantic_target="market relationship mode",
        primitive=SemanticPrimitive.CHOICE,
        question="Which market relationship mode is supported?",
        state_requirements=("document.home.visible_text",),
        dependencies=("document.home.visible_text",),
        mutually_exclusive=False,
        abstention_policy="preserve UNKNOWN",
    )


def _routing() -> tuple[DimensionRoutingPolicy, ...]:
    return (
        DimensionRoutingPolicy(
            dimension_id="market_mode",
            version="routing-v1",
            answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
        ),
    )


def _policy() -> BootstrapPolicy:
    return BootstrapPolicy(
        policy_id="xeed-bootstrap",
        version="2",
        max_known_sources=2,
    )


def _research_decision(
    rich_state,
    *,
    signals: frozenset[ResearchValueSignal] = frozenset({ResearchValueSignal.MATERIALITY}),
):
    return decide_research_value(
        context=ResearchValueContext(
            subject_id="org:1",
            state_fingerprint=rich_state.fingerprint,
            dimension_id="market_mode",
            missing_requirements=("document.home.visible_text",),
            value_signals=signals,
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


def test_bootstrap_reuses_memory_and_hands_off_immediately_to_prime() -> None:
    rich_state = _rich_state(("document.home.visible_text", "Industrial pump manufacturer."))

    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
    )

    assert plan.disposition is BootstrapDisposition.HANDOFF_TO_PRIME
    assert plan.reused_observation_count == 1
    assert plan.missing_requirements == ()
    assert plan.source_candidates == ()
    assert plan.prime_plan is not None
    assert plan.prime_plan.items[0].route is PrimeRoute.STRUCTURED_EVALUATOR


def test_bootstrap_uses_explicit_known_source_before_adaptive_research() -> None:
    source = BootstrapSourceCandidate(
        candidate_id="source:official-home",
        subject_id="org:1",
        observation_slot="home",
        source_ref="https://acme.example/",
        source_type="OFFICIAL_WEB",
        provides_fields=frozenset({"document.home.visible_text"}),
        priority=10,
    )

    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=_rich_state(),
        policy=_policy(),
        known_sources=(source,),
        contracts=(_contract(),),
        routing_policies=_routing(),
    )

    assert plan.disposition is BootstrapDisposition.ACQUIRE_KNOWN_SOURCES
    assert plan.source_candidates == (source,)
    assert plan.missing_requirements == ("document.home.visible_text",)
    assert plan.prime_plan is None


def test_bootstrap_escalates_only_when_research_value_gate_authorizes_it() -> None:
    rich_state = _rich_state()
    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
        research_decisions=(_research_decision(rich_state),),
    )

    assert plan.disposition is BootstrapDisposition.ADAPTIVE_RESEARCH
    assert plan.missing_requirements == ("document.home.visible_text",)
    assert plan.source_candidates == ()
    assert plan.prime_plan is None


def test_bootstrap_ignores_foreign_subject_sources() -> None:
    foreign = BootstrapSourceCandidate(
        candidate_id="source:foreign",
        subject_id="org:other",
        observation_slot="home",
        source_ref="https://other.example/",
        source_type="OFFICIAL_WEB",
        provides_fields=frozenset({"document.home.visible_text"}),
    )

    rich_state = _rich_state()
    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(foreign,),
        contracts=(_contract(),),
        routing_policies=_routing(),
        research_decisions=(_research_decision(rich_state),),
    )

    assert plan.disposition is BootstrapDisposition.ADAPTIVE_RESEARCH
    assert plan.source_candidates == ()


def test_bootstrap_source_selection_is_budgeted_and_deterministic() -> None:
    sources = tuple(
        BootstrapSourceCandidate(
            candidate_id=f"source:{name}",
            subject_id="org:1",
            observation_slot=name,
            source_ref=f"https://{name}.example/",
            source_type="PUBLIC_WEB",
            provides_fields=frozenset({"document.home.visible_text"}),
            priority=priority,
        )
        for name, priority in (("c", 20), ("b", 10), ("a", 10))
    )

    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=_rich_state(),
        policy=_policy(),
        known_sources=sources,
        contracts=(_contract(),),
        routing_policies=_routing(),
    )

    assert [item.candidate_id for item in plan.source_candidates] == ["source:a"]


def test_bootstrap_plan_is_replay_stable() -> None:
    rich_state = _rich_state(("document.home.visible_text", "Industrial pump manufacturer."))
    first = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
    )
    second = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
    )

    assert first.plan_fingerprint == second.plan_fingerprint


def test_bootstrap_policy_does_not_define_universal_minimum_state() -> None:
    policy = BootstrapPolicy(
        policy_id="xeed-bootstrap",
        version="2",
    )

    assert not hasattr(policy, "initial_state_requirements")


def test_bootstrap_outcome_can_be_recorded_without_granting_policy_authority() -> None:
    rich_state = _rich_state()
    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
        research_decisions=(_research_decision(rich_state),),
    )

    event = bootstrap_learning_event(
        event_id="learn:bootstrap:1",
        plan=plan,
        occurred_at=NOW,
        code_sha="abc123",
        outcome=LearningOutcome.COMPLETED,
        after_state_fingerprint="state:after",
        reason_code="ADAPTIVE_RESEARCH_FILLED_INITIAL_STATE",
        cost=LearningCost(amount_microunits=50, currency="USD", latency_ms=80),
        yield_=LearningYield(
            observations_added=2,
            state_fields_changed=1,
            dimensions_became_answerable=1,
        ),
        output_fingerprint="bootstrap-result:1",
    )

    assert event.kind is LearningEventKind.BOOTSTRAP
    assert event.mechanism is LearningMechanism.ADAPTIVE_RESEARCH
    assert event.activity_ref == plan.plan_fingerprint
    assert event.policy_id == plan.policy_id
    assert event.policy_version == plan.policy_version
    assert event.before_state_fingerprint == plan.state_fingerprint
    assert event.after_state_fingerprint == "state:after"
    assert not hasattr(event, "policy_update")


def test_bootstrap_hands_off_answerable_dimension_without_waiting_for_unrelated_gap() -> None:
    market = _contract()
    reputation = TypingDimensionContract(
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
    routing = (
        *_routing(),
        DimensionRoutingPolicy(
            dimension_id="reputation",
            version="routing-v1",
            answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
        ),
    )
    rich_state = _rich_state(("document.home.visible_text", "Industrial pump manufacturer."))
    reviews = BootstrapSourceCandidate(
        candidate_id="source:reviews",
        subject_id="org:1",
        observation_slot="reviews",
        source_ref="https://reviews.example/acme",
        source_type="PUBLIC_REVIEWS",
        provides_fields=frozenset({"document.reviews.visible_text"}),
    )

    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(reviews,),
        contracts=(market, reputation),
        routing_policies=routing,
    )

    assert plan.disposition is BootstrapDisposition.HANDOFF_TO_PRIME
    assert plan.prime_plan is not None
    assert [item.dimension_id for item in plan.prime_plan.items] == ["market_mode"]
    assert plan.dimension_gaps[0].dimension_id == "reputation"
    assert plan.dimension_gaps[0].missing_requirements == ("document.reviews.visible_text",)
    assert plan.missing_requirements == ("document.reviews.visible_text",)
    assert plan.source_candidates == (reviews,)


def test_bootstrap_can_retain_low_value_unknown_without_research() -> None:
    rich_state = _rich_state()
    decision = _research_decision(rich_state, signals=frozenset())

    plan = build_bootstrap_plan(
        seed=_seed(),
        rich_state=rich_state,
        policy=_policy(),
        known_sources=(),
        contracts=(_contract(),),
        routing_policies=_routing(),
        research_decisions=(decision,),
    )

    assert decision.disposition is ResearchValueDisposition.RETAIN_UNKNOWN
    assert plan.disposition is BootstrapDisposition.RETAIN_UNKNOWN
    assert plan.prime_plan is None
    assert plan.missing_requirements == ("document.home.visible_text",)
