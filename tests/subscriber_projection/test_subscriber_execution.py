from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    GovernedExecutionController,
)
from application.economic_discovery.explanation import (
    BasisContribution,
    BasisDatum,
    ExplainableBasis,
)
from application.economic_discovery.first_vertical_e2e import (
    EconomicFieldSpec,
    FirstVerticalDispatchCosts,
    FirstVerticalSourcePlan,
)
from application.economic_discovery.governed_dispatch import DispatchCost
from application.economic_discovery.market_entry import (
    MarketParticipation,
    MarketRelationship,
    ParticipationState,
    XeedMarketMap,
)
from application.economic_discovery.market_planning import (
    MarketResearchIntent,
    ObservationObjectType,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.source_registry import StaticSourceRegistry
from application.subscriber_projection.dri_measurement import (
    PageMeasureState,
    measure_public_page_representation,
)
from application.subscriber_projection.subscriber_runtime import (
    MarketActivityPlanDescriptor,
    SubscriberEconomicExecutionPlan,
    SubscriberExecutionOutcome,
    SubscriberRuntimeStatus,
    route_market_activity_plan,
)
from domain.identity import OrganizationId
from domain.organizations.model import Organization
from pipeline.learning_memory.sqlite_store import SqliteLearningMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PublicSourcePolicyGate,
)
from pipeline.source_representation import HtmlDocumentRepresentationAdapter
from tests.economic_discovery.test_first_vertical_e2e import (
    CORPUS,
    OBSERVED_AT,
    AlwaysYesEvaluator,
    FixtureIdentityBindingPort,
    FixtureSemanticExtractor,
    FixtureTransport,
    _contract,
    _entry,
    _public_dns,
    _run_fixture,
)
from tests.subscriber_projection.test_subscriber_runtime import _runtime


def _market_map(xeed_id: str, organization_id: str, at) -> XeedMarketMap:
    datum = BasisDatum(
        datum_id="market-basis",
        observation_id="market-observation",
        source_ref="https://arbor-cooling.example/markets",
        source_type="OFFICIAL_WEB",
        observed_at=at,
        excerpt_or_summary="Source-backed test evidence for potential B2B participation.",
        contribution=BasisContribution.SUPPORTS,
        evidence_ref="market-evidence",
    )
    basis = ExplainableBasis(
        basis_id="market-basis-id",
        subject_id=xeed_id,
        candidate_id="market-candidate",
        semantic_target="market_participation",
        state_fingerprint="market-state",
        contract_fingerprint="market-contract",
        evaluated_at=at,
        data=(datum,),
        interpretation="Potential B2B participation is supported for this controlled test.",
        uncertainty="Test input only.",
    )
    return XeedMarketMap(
        xeed_id=xeed_id,
        state_fingerprint="market-map-state",
        classified_at=at,
        participations=(
            MarketParticipation(MarketRelationship.B2B, ParticipationState.POTENTIAL, 0.5, basis),
            MarketParticipation(MarketRelationship.B2C, ParticipationState.UNKNOWN, None, None),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.UNKNOWN, None, None),
        ),
    )


def _plan(
    *,
    result: Any,
    transport: FixtureTransport,
    tmp_path: Path,
    unknown_cost: bool = False,
    max_cost: int = 100,
) -> SubscriberEconomicExecutionPlan:
    docs = CORPUS["documents"]
    subject, activity = docs[0], docs[1]
    purpose = ReusePurpose.HISTORICAL_REFERENCE
    entries = tuple(
        replace(
            _entry(doc, transport.instrument_ref),
            allowed_purposes=(ReusePurpose.CURRENT_STATE, purpose),
        )
        for doc in (subject, activity)
    )
    registry = StaticSourceRegistry(entries)
    authorizations = tuple(
        registry.authorize(
            source_id=str(doc["id"]),
            request_id=f"subscriber-test:{doc['id']}",
            subject_id=str(doc["subject_id"]),
            observation_slot="economic-source",
            target_uri=str(doc["source_ref"]),
            source_type=str(doc["source_type"]),
            purpose=purpose,
            instrument_ref=transport.instrument_ref,
        )
        for doc in (subject, activity)
    )
    plans = tuple(
        FirstVerticalSourcePlan(
            authorization=authorization,
            extraction_contract=_contract(f"subscriber-{doc['id']}", dict(doc["fields"])),
            subject_mention=str(doc.get("subject_mention", "Harbor Storage")),
            fields=tuple(
                EconomicFieldSpec(semantic_target=name, field_name=name)
                for name in dict(doc["fields"])
            ),
        )
        for doc, authorization in zip((subject, activity), authorizations, strict=True)
    )
    artifacts = ContentAddressedArtifactStore(tmp_path / "execution-artifacts")
    acquirer = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=transport,
        artifacts=artifacts,
        clock=lambda: OBSERVED_AT,
    )
    extractor = FixtureSemanticExtractor(
        {str(doc["subject_id"]): dict(doc["fields"]) for doc in (subject, activity)}
    )
    controller = GovernedExecutionController(
        ExecutionBudgetPolicy(
            policy_id="subscriber-controlled-test-budget",
            version="1",
            currency="EUR",
            max_amount_microunits=max_cost,
            max_requests=7,
            max_sources=2,
            max_elapsed_ms=10_000,
            max_loops=3,
            stop_on_unknown_cost=True,
        ),
        state=ExecutionBudgetState(amount_microunits=0, currency="EUR", cost_complete=True),
    )
    costs = FirstVerticalDispatchCosts(
        source=(
            DispatchCost() if unknown_cost else DispatchCost(1, "EUR", "test-source-tariff", "1")
        ),
        semantic_extraction=DispatchCost(1, "EUR", "test-extraction-tariff", "1"),
        evaluator=DispatchCost(1, "EUR", "test-evaluator-tariff", "1"),
    )
    organization_id = str(result.human_output.to_wire()["subject_ref"])
    assert organization_id == str(subject["subject_id"])
    market_map = _market_map(
        "xeed:subscriber:1", organization_id, result.reasoning.vector.evaluated_at
    )
    return SubscriberEconomicExecutionPlan(
        market_map=market_map,
        market_catalogue=(
            MarketActivityPlanDescriptor(
                descriptor_id="b2b-organization-v1",
                version="1",
                relationship=MarketRelationship.B2B,
                participation_state=ParticipationState.POTENTIAL,
                object_type=ObservationObjectType.ORGANIZATION,
                plan=plans[1],
            ),
        ),
        subject_plan=plans[0],
        selected_relationship=MarketRelationship.B2B,
        source_acquirer=acquirer,
        representation_port=HtmlDocumentRepresentationAdapter(artifacts),
        semantic_extractor=extractor,
        binding_port=FixtureIdentityBindingPort(),
        evaluator=AlwaysYesEvaluator(),
        execution_controller=controller,
        dispatch_costs=costs,
        learning_memory=SqliteLearningMemory(tmp_path / "learning.sqlite3"),
        as_of=result.reasoning.vector.evaluated_at + timedelta(minutes=1),
    )


def _base_runtime(tmp_path: Path, result: Any):
    runtime, context, xeed = _runtime(tmp_path, result)
    return runtime, context, xeed


def test_configured_runner_executes_governed_eb04_and_persists_memory_and_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path / "seed"
    )
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)

    outcome = runtime.execute(context, xeed.id, plan)

    assert isinstance(outcome, SubscriberExecutionOutcome)
    assert outcome.state == "COMPLETED"
    assert outcome.market_targets == ("B2B",)
    assert transport.calls[-2:] == ["arbor-cooling.example", "harbor-storage.example"]
    assert outcome.read is not None
    assert outcome.read.status is SubscriberRuntimeStatus.SUCCESS
    signal = outcome.read.projection["nodes"][0]
    assert isinstance(signal, dict)
    assert signal["executionTrace"]["budget"]["costComplete"] is True
    assert signal["executionTrace"]["marketMap"]["directives"][0]["relationship"] == "B2B"
    assert (
        signal["executionTrace"]["marketPlanRouting"]["selectedDescriptorId"]
        == "b2b-organization-v1"
    )
    assert outcome.read.projection["economicOutput"]["evidence"]
    dri = outcome.read.projection["digitalRepresentation"]
    assert dri["kind"] == "DRI_PUBLIC_PAGE_REPRESENTATION"
    assert dri["instrument"] == {
        "ref": "axignal.public-page-representation",
        "version": "1.0.0",
    }
    assert dri["surface"] == "PUBLIC_WEB_PAGE"
    assert dri["sample"] == {"eligible": 1, "informative": 1}
    assert dri["conditions"] == {
        "geography": "UNKNOWN",
        "language": "UNKNOWN",
        "deviceContext": "UNKNOWN",
    }
    assert dri["source"]["rightsStatus"] == "PERMITTED"
    assert dri["source"]["policyVersion"] == "1"
    assert dri["observedAt"] == "2026-10-01T12:00:00+00:00"
    assert "One authorized public page only" in dri["scopeLimit"]
    assert dri["representationGap"]["type"] == "INXIGHT_REPRESENTATION_GAP"
    assert dri["representationGap"]["cause"] == "UNKNOWN"
    assert "search visibility" in dri["representationGap"]["notEstablished"]
    gap = dri["representationGap"]
    assert isinstance(gap, dict)
    recommendation = gap["contextRecommendation"]
    assert isinstance(recommendation, dict)
    assert recommendation.get("state") == "CONTEXT_REQUIRED"
    assert recommendation.get("requiredContext") == {
        "pagePurpose": "UNKNOWN",
        "expectedPublicBrandName": "UNKNOWN",
    }
    assert recommendation.get("actionMode") == "HUMAN_REVIEW_ONLY"
    assert recommendation.get("performanceBenefit") == "NOT_ESTABLISHED"
    recommended_action = recommendation.get("recommendedAction")
    assert isinstance(recommended_action, str)
    assert "responsible team" in recommended_action


def test_unknown_dispatch_cost_blocks_before_any_public_fetch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path / "seed"
    )
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path, unknown_cost=True)
    before = len(transport.calls)

    outcome = runtime.execute(context, xeed.id, plan)

    assert outcome.state == "BLOCKED_COST_UNKNOWN"
    assert len(transport.calls) == before
    assert outcome.read is None
    events = plan.learning_memory.for_xeed(str(xeed.id))
    assert len(events) == 1
    assert events[0].outcome.value == "PARTIAL"
    assert events[0].reason_code == "COST_UNKNOWN"
    attempt = outcome.to_wire()["digitalRepresentationAttempt"]
    assert attempt["state"] == "NOT_MEASURED"
    assert attempt["reason"]["code"] == "COST_PREFLIGHT_BLOCKED"


def test_missing_execution_plan_reports_not_ready_and_not_measured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, *_ = _run_fixture(monkeypatch, tmp_path / "seed")
    runtime, context, xeed = _base_runtime(tmp_path, result)

    outcome = runtime.execute(context, xeed.id, None)

    assert outcome.state == "NOT_READY"
    attempt = outcome.to_wire()["digitalRepresentationAttempt"]
    assert attempt["state"] == "NOT_MEASURED"
    assert attempt["reason"]["code"] == "EXECUTION_PLAN_UNAVAILABLE"


def test_inaccessible_public_page_is_structured_not_measured_without_a_gap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, *_ = _run_fixture(monkeypatch, tmp_path / "seed")
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)

    monkeypatch.setattr(
        plan.source_acquirer,
        "observe",
        lambda *_args: SimpleNamespace(failure_state="http_503"),
    )
    outcome = runtime.execute(context, xeed.id, plan)

    assert outcome.state == "PARTIAL"
    attempt = outcome.to_wire()["digitalRepresentationAttempt"]
    assert attempt["state"] == "NOT_MEASURED"
    assert attempt["reason"]["code"] == "SOURCE_ACQUISITION_FAILED"
    assert attempt["sampleAttempt"] == {
        "planned": 1,
        "acquired": 0,
        "informative": 0,
        "resultState": "INACCESSIBLE",
    }
    assert "representationGap" not in attempt


def test_non_informative_page_is_structured_not_measured_without_a_gap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, *_ = _run_fixture(monkeypatch, tmp_path / "seed")
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)

    def reject_page_representation(**_kwargs: object) -> None:
        raise ValueError("unresolved document")

    monkeypatch.setattr(
        plan.representation_port,
        "represent",
        reject_page_representation,
    )

    outcome = runtime.execute(context, xeed.id, plan)

    attempt = outcome.to_wire()["digitalRepresentationAttempt"]
    assert attempt["state"] == "NOT_MEASURED"
    assert attempt["reason"]["code"] == "PAGE_REPRESENTATION_UNAVAILABLE"
    assert attempt["sampleAttempt"] == {
        "planned": 1,
        "acquired": 1,
        "informative": 0,
        "resultState": "NON_INFORMATIVE",
    }
    assert "representationGap" not in attempt


def test_page_measurement_currentness_is_recomputed_at_read_time(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path / "seed"
    )
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)

    outcome = runtime.execute(context, xeed.id, plan)
    assert outcome.read is not None
    later = runtime.read(context, xeed.id, plan.as_of + timedelta(days=8))

    assert later.projection["digitalRepresentation"]["currentness"] == "STALE"
    assert later.projection["digitalRepresentation"]["currentnessEvaluation"]["policyRef"] == (
        "subscriber-currentness@1"
    )


def test_instrument_version_change_hides_current_gap_but_retains_recorded_measurement(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, *_ = _run_fixture(monkeypatch, tmp_path / "seed")
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)
    outcome = runtime.execute(context, xeed.id, plan)
    assert outcome.read is not None

    monkeypatch.setattr(
        "application.subscriber_projection.subscriber_runtime.DRI_INSTRUMENT_VERSION",
        "2.0.0",
    )
    read = runtime.read(context, xeed.id, plan.as_of)

    dri = read.projection["digitalRepresentation"]
    assert dri["state"] == "NOT_MEASURED"
    assert dri["reason"]["code"] == "INSTRUMENT_VERSION_MISMATCH"
    assert "representationGap" in dri["recordedMeasurement"]
    assert dri["recordedMeasurement"]["instrument"]["version"] == "1.0.0"


def test_page_title_measure_does_not_promote_unresolved_body_visibility(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, *_ = _run_fixture(monkeypatch, tmp_path, unresolved_visibility=True)
    representation = result.subject_source.representation
    source = replace(
        result.subject_source,
        representation=replace(
            representation,
            title="Arbor Cooling | Capabilities",
            visibility_resolved=False,
            extracted_text=representation.document_text,
            extracted_text_fingerprint=representation.document_text_fingerprint,
        ),
    )
    organization = Organization(
        id=OrganizationId(str(result.human_output.to_wire()["subject_ref"])),
        canonical_name="Arbor Cooling",
    )

    measurement = measure_public_page_representation(source=source, organization=organization)

    fields = {name: state for name, state, _value in measurement.fields}
    assert fields["canonical_organization_name_in_page_title"] is PageMeasureState.PRESENT
    assert fields["visible_text"] is PageMeasureState.NOT_MEASURED
    assert measurement.gap is None
    assert "one page only" in measurement.human_meaning


def test_known_fanout_over_budget_releases_partial_reservations_before_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path / "seed"
    )
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path, max_cost=6)
    before = len(transport.calls)

    outcome = runtime.execute(context, xeed.id, plan)

    assert outcome.state == "BLOCKED_BUDGET"
    assert len(transport.calls) == before
    assert plan.execution_controller.active_reservation_ids == ()
    events = plan.learning_memory.for_xeed(str(xeed.id))
    assert len(events) == 1
    assert events[0].outcome.value == "PARTIAL"
    assert events[0].reason_code == "MONETARY_BUDGET_EXHAUSTED"


def test_market_router_changes_typed_plan_by_posture_and_abstains_on_unknown(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("socket.getaddrinfo", _public_dns)
    result, transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch, tmp_path / "seed"
    )
    runtime, context, xeed = _base_runtime(tmp_path, result)
    plan = _plan(result=result, transport=transport, tmp_path=tmp_path)
    b2c_descriptor = MarketActivityPlanDescriptor(
        descriptor_id="b2c-demand-archetype-v1",
        version="1",
        relationship=MarketRelationship.B2C,
        participation_state=ParticipationState.POTENTIAL,
        object_type=ObservationObjectType.DEMAND_ARCHETYPE,
        plan=plan.market_catalogue[0].plan,
    )
    b2b = route_market_activity_plan(
        market_map=plan.market_map,
        catalogue=(*plan.market_catalogue, b2c_descriptor),
        selected_relationship=MarketRelationship.B2B,
    )
    b2c_map = XeedMarketMap(
        xeed_id=plan.market_map.xeed_id,
        state_fingerprint="market-map-b2c",
        classified_at=plan.market_map.classified_at,
        participations=(
            MarketParticipation(MarketRelationship.B2B, ParticipationState.UNKNOWN, None, None),
            MarketParticipation(
                MarketRelationship.B2C,
                ParticipationState.POTENTIAL,
                0.5,
                plan.market_map.participations[0].basis,
            ),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.UNKNOWN, None, None),
        ),
    )
    b2c = route_market_activity_plan(
        market_map=b2c_map,
        catalogue=(*plan.market_catalogue, b2c_descriptor),
        selected_relationship=MarketRelationship.B2C,
    )
    unknown_map = XeedMarketMap(
        xeed_id=plan.market_map.xeed_id,
        state_fingerprint="market-map-unknown",
        classified_at=plan.market_map.classified_at,
        participations=tuple(
            MarketParticipation(relationship, ParticipationState.UNKNOWN, None, None)
            for relationship in MarketRelationship
        ),
    )
    unknown = route_market_activity_plan(
        market_map=unknown_map,
        catalogue=(*plan.market_catalogue, b2c_descriptor),
        selected_relationship=None,
    )

    assert b2b.descriptor is not None and b2b.descriptor.descriptor_id == "b2b-organization-v1"
    assert b2b.descriptor.object_type is ObservationObjectType.ORGANIZATION
    assert b2c.descriptor is not None and b2c.descriptor.descriptor_id == "b2c-demand-archetype-v1"
    assert b2c.descriptor.object_type is ObservationObjectType.DEMAND_ARCHETYPE
    assert b2b.directive is not None
    assert b2b.directive.research_intent is MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
    assert b2c.directive is not None
    assert b2c.directive.research_intent is MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
    assert unknown.descriptor is None
    assert unknown.rejected == ("NO_OBSERVED_OR_POTENTIAL_MARKET_TARGET",)

    basis = plan.market_map.participations[0].basis
    assert basis is not None
    observed_b2b_map = XeedMarketMap(
        xeed_id=plan.market_map.xeed_id,
        state_fingerprint="market-map-b2b-observed",
        classified_at=plan.market_map.classified_at,
        participations=(
            MarketParticipation(MarketRelationship.B2B, ParticipationState.OBSERVED, 0.5, basis),
            MarketParticipation(MarketRelationship.B2C, ParticipationState.UNKNOWN, None, None),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.UNKNOWN, None, None),
        ),
    )
    observed_b2b_descriptor = MarketActivityPlanDescriptor(
        descriptor_id="b2b-organization-observed-v1",
        version="1",
        relationship=MarketRelationship.B2B,
        participation_state=ParticipationState.OBSERVED,
        object_type=ObservationObjectType.ORGANIZATION,
        plan=plan.market_catalogue[0].plan,
    )
    observed_b2b = route_market_activity_plan(
        market_map=observed_b2b_map,
        catalogue=(observed_b2b_descriptor,),
        selected_relationship=MarketRelationship.B2B,
    )
    b2g_map = XeedMarketMap(
        xeed_id=plan.market_map.xeed_id,
        state_fingerprint="market-map-b2g-potential",
        classified_at=plan.market_map.classified_at,
        participations=(
            MarketParticipation(MarketRelationship.B2B, ParticipationState.UNKNOWN, None, None),
            MarketParticipation(MarketRelationship.B2C, ParticipationState.UNKNOWN, None, None),
            MarketParticipation(MarketRelationship.B2G, ParticipationState.POTENTIAL, 0.5, basis),
        ),
    )
    b2g_descriptor = MarketActivityPlanDescriptor(
        descriptor_id="b2g-public-body-v1",
        version="1",
        relationship=MarketRelationship.B2G,
        participation_state=ParticipationState.POTENTIAL,
        object_type=ObservationObjectType.PUBLIC_BODY,
        plan=plan.market_catalogue[0].plan,
    )
    b2g = route_market_activity_plan(
        market_map=b2g_map,
        catalogue=(b2g_descriptor,),
        selected_relationship=MarketRelationship.B2G,
    )
    assert observed_b2b.descriptor is not None
    assert observed_b2b.directive is not None
    assert (
        observed_b2b.directive.research_intent is MarketResearchIntent.CONFIRM_CURRENT_PARTICIPATION
    )
    assert b2g.descriptor is not None
    assert b2g.descriptor.object_type is ObservationObjectType.PUBLIC_BODY
    assert b2g.directive is not None
    assert b2g.directive.research_intent is MarketResearchIntent.TEST_POTENTIAL_PARTICIPATION
    before = len(transport.calls)
    unknown_outcome = runtime.execute(
        context,
        xeed.id,
        replace(plan, market_map=unknown_map, selected_relationship=None),
    )
    assert unknown_outcome.state == "INSUFFICIENT_EVIDENCE"
    assert len(transport.calls) == before
