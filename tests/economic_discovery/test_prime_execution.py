from __future__ import annotations

import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.economic_discovery import (
    ObservationAccessStatus,
    ObservationReuseAuthority,
    ObservationReusePolicy,
    ObservationReuseScope,
    ObservationRightsStatus,
    ReusePurpose,
)
from application.economic_discovery.brain_contracts import (
    SemanticPrimitive,
    TypingDimensionContract,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionBudgetState,
    GovernedExecutionController,
)
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEventKind,
    LearningOutcome,
    ReplayDisposition,
)
from application.economic_discovery.prime import DimensionRoutingPolicy, PrimeRoute
from application.economic_discovery.prime_execution import (
    PrimeExecutionPorts,
    PrimeMechanismResult,
    execute_prime_source_slice,
)
from application.economic_discovery.research_value import (
    ResearchValueContext,
    ResearchValuePolicy,
    ResearchValueSignal,
    decide_research_value,
)
from application.semantic_extraction import (
    SemanticExtractionContract,
    SemanticTarget,
)
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
    SourceTargetRule,
    ingest_source_observation,
)
from application.source_representation import (
    compile_rich_subject_state,
    representation_state_data,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganizationReader
from application.xeed_access.reader import AuthorizedXeedReader, TrustedRequestContext
from application.xeed_germination import (
    BootstrapPolicy,
    BootstrapSourceCandidate,
    apply_bootstrap_plan,
    begin_resolution,
    build_bootstrap_plan,
    plant_xeed_runtime,
)
from cognition.jobs.model import StructuredResult
from cognition.router.router import ModelRouter
from cognition.semantic_extraction_adapter import CognitiveSemanticExtractionAdapter
from domain.evidence.epistemics import Currentness
from domain.identity import OrganizationId, PrincipalId, TenantId, XeedId
from domain.organizations.model import Organization
from domain.tenancy.model import Principal, PrincipalTenantMembership, Tenant
from domain.xeed.model import Xeed
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PublicSourcePolicyGate,
    RawHttpResponse,
    ResolvedTarget,
)
from pipeline.source_representation import HtmlDocumentRepresentationAdapter
from tests.support.xeed_authority import InMemoryXeedAuthority

NOW = datetime(2026, 9, 30, 18, 30, tzinfo=UTC)


def _reuse_authority() -> ObservationReuseAuthority:
    return ObservationReuseAuthority(
        rights_status=ObservationRightsStatus.PERMITTED,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        scope=ObservationReuseScope.GLOBAL_PUBLIC,
        provenance_ref="provenance:prime-fixture",
        currentness=Currentness.CURRENT,
        applicable_subject_ids=("org:acme",),
        applicable_purposes=(ReusePurpose.CURRENT_STATE.value,),
    )


def _reuse_policy() -> ObservationReusePolicy:
    return ObservationReusePolicy("observation-reuse", "1")


def _public_dns(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("8.8.8.8", 443),
        )
    ]


class _Transport:
    instrument_ref = "prime-fixture-http/1"

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        assert timeout_ms == 1_500
        body = (
            b"<html lang='en'><head><title>ACME Pumps</title></head>"
            b"<body>ACME manufactures industrial pumps for food factories.</body></html>"
        )
        assert len(body) < max_response_bytes
        return RawHttpResponse(
            status=200,
            headers=(("Content-Type", "text/html; charset=utf-8"),),
            body=body,
            peer_ip=target.addresses[0],
        )


class _Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization

    def get_organization(self, organization_id: OrganizationId) -> Organization | None:
        return self.organization if organization_id == self.organization.id else None


def _authorized_seed():
    authority = InMemoryXeedAuthority()
    authority.add_principal(Principal(PrincipalId("principal:1")))
    authority.add_tenant(Tenant(TenantId("tenant:1")))
    authority.add_membership(
        PrincipalTenantMembership(PrincipalId("principal:1"), TenantId("tenant:1"))
    )
    authority.add_xeed(Xeed(XeedId("xeed:1"), TenantId("tenant:1"), OrganizationId("org:acme")))
    authorized = AuthorizedXeedReader(authority, authority, authority).read(
        TrustedRequestContext(PrincipalId("principal:1"), TenantId("tenant:1")),
        XeedId("xeed:1"),
    )
    organization = Organization(OrganizationId("org:acme"), "ACME")
    return AuthorizedXeedOrganizationReader(_Organizations(organization)).read(authorized)


def _source_policy() -> SourceDispatchPolicy:
    return SourceDispatchPolicy(
        policy_id="source:web:v1",
        disposition=DispatchDisposition.ALLOW,
        decision_basis="authorized public corporate homepage",
        targets=(SourceTargetRule("example.test", "/company", ("https",)),),
        timeout_ms=1_500,
        max_redirects=1,
    )


def _request(policy: SourceDispatchPolicy) -> SourceRequest:
    return SourceRequest(
        request_id="request:acme:home:1",
        subject_id="org:acme",
        observation_slot="website",
        target_uri="https://example.test/company",
        source_type="OFFICIAL_WEB",
        policy_id=policy.policy_id,
        policy_fingerprint=policy.fingerprint,
    )


def _sensor(tmp_path: Path) -> tuple[HttpSourceSensor, ContentAddressedArtifactStore]:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    return (
        HttpSourceSensor(
            policy_gate=PublicSourcePolicyGate(),
            transport=_Transport(),  # type: ignore[arg-type]
            artifacts=artifacts,
            clock=lambda: NOW,
        ),
        artifacts,
    )


def _contract(dimension_id: str) -> TypingDimensionContract:
    return TypingDimensionContract(
        dimension_id=dimension_id,
        version="1",
        semantic_target=dimension_id,
        primitive=SemanticPrimitive.CHOICE,
        question=f"What is {dimension_id}?",
        state_requirements=("document.website.visible_text",),
        dependencies=("document.website.visible_text",),
        mutually_exclusive=True,
        abstention_policy="preserve UNKNOWN",
    )


class _Executor:
    def __init__(self, label: str, *, progress: bool = True) -> None:
        self.label = label
        self.progress = progress
        self.calls: list[str] = []

    def execute(self, *, item, state, semantic_candidates):
        self.calls.append(item.dimension_id)
        if item.route is PrimeRoute.STRUCTURED_EVALUATOR:
            assert semantic_candidates is not None
            assert semantic_candidates.candidates
        return PrimeMechanismResult(
            output_fingerprint=f"{self.label}:{item.dimension_id}:{state.fingerprint}",
            made_progress=self.progress,
            cost=LearningCost(
                amount_microunits=5,
                currency="USD",
                latency_ms=7,
            ),
            requests=1,
            semantic_judgments_produced=(1 if item.route is PrimeRoute.STRUCTURED_EVALUATOR else 0),
        )


class _SemanticProvider:
    name = "fixture-semantic"

    def complete(self, job):
        text = str(job.context["visible_text"])
        excerpt = "ACME manufactures industrial pumps for food factories."
        assert excerpt in text
        return StructuredResult(
            job_id=job.id,
            provider=self.name,
            payload={
                "provider_version": "1",
                "candidates": [
                    {
                        "semantic_target": "market-mode",
                        "statement": "ACME manufactures industrial pumps.",
                        "excerpt": excerpt,
                        "grounding_surface": "VISIBLE_TEXT",
                    }
                ],
            },
        )


def _budget(max_loops: int = 10) -> GovernedExecutionController:
    return GovernedExecutionController(
        policy=ExecutionBudgetPolicy(
            policy_id="prime-execution-budget",
            version="1",
            currency="USD",
            max_amount_microunits=100,
            max_requests=10,
            max_sources=10,
            max_elapsed_ms=10_000,
            max_retries=2,
            max_loops=max_loops,
            max_no_progress_streak=2,
        ),
        state=ExecutionBudgetState(amount_microunits=0, currency="USD"),
    )


def test_real_source_to_prime_composition_with_semantic_extraction(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    policy = _source_policy()
    request = _request(policy)
    sensor, artifacts = _sensor(tmp_path)
    observation_memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    learning_memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    structured = _Executor("structured")
    ports = PrimeExecutionPorts(
        deterministic=_Executor("deterministic"),
        structured_evaluator=structured,
        adaptive_research=_Executor("adaptive"),
    )
    contract = _contract("market-mode")
    extraction_contract = SemanticExtractionContract(
        contract_id="semantic:market-mode",
        version="1",
        targets=(SemanticTarget("market-mode", "economic market mode"),),
    )
    semantic_adapter = CognitiveSemanticExtractionAdapter(ModelRouter((_SemanticProvider(),)))

    trace = execute_prime_source_slice(
        execution_id="run:1",
        seed=seed,
        code_sha="abc123",
        occurred_at=NOW,
        observation_memory=observation_memory,
        learning_memory=learning_memory,
        request=request,
        source_policy=policy,
        source_acquirer=sensor,
        representation_port=HtmlDocumentRepresentationAdapter(artifacts),
        prior_rich_state=compile_rich_subject_state(
            subject_id="org:acme",
            contributions=(),
        ),
        contracts=(contract,),
        routing_policies=(
            DimensionRoutingPolicy(
                dimension_id="market-mode",
                version="routing-v1",
                answerable_route=PrimeRoute.STRUCTURED_EVALUATOR,
            ),
        ),
        research_decisions=(),
        execution_controller=_budget(),
        ports=ports,
        semantic_extractor=semantic_adapter,
        semantic_contract=extraction_contract,
    )

    assert trace.prime_plan is not None
    assert trace.prime_plan.items[0].route is PrimeRoute.STRUCTURED_EVALUATOR
    assert structured.calls == ["market-mode"]
    assert trace.semantic_extraction_id is not None
    assert trace.source_artifact_ref.startswith("cas:sha256:")
    assert len(trace.learning_event_ids) == 5
    history = {event.event_id: event for event in learning_memory.for_xeed("xeed:1")}
    assert [history[event_id].kind.value for event_id in trace.learning_event_ids] == [
        "SOURCE_ACQUISITION",
        "OBSERVATION_INGESTION",
        "REPRESENTATION",
        "SEMANTIC_EXTRACTION",
        "STRUCTURED_EVALUATION",
    ]
    semantic_event = history[trace.learning_event_ids[3]]
    structured_event = history[trace.learning_event_ids[4]]
    assert semantic_event.replay.disposition is ReplayDisposition.NON_REPLAYABLE
    assert semantic_event.replay.reason_code == "PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE"
    assert semantic_event.replay.require("provider") == "fixture-semantic"
    assert semantic_event.replay.require("provider_version") == "1"
    assert structured_event.replay.disposition is ReplayDisposition.NON_REPLAYABLE
    assert structured_event.replay.reason_code == "PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE"


def test_budget_stop_blocks_second_prime_work_and_records_partial_learning(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    policy = _source_policy()
    request = _request(policy)
    sensor, artifacts = _sensor(tmp_path)
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    deterministic = _Executor("deterministic")
    ports = PrimeExecutionPorts(
        deterministic=deterministic,
        structured_evaluator=_Executor("structured"),
        adaptive_research=_Executor("adaptive"),
    )

    trace = execute_prime_source_slice(
        execution_id="run:budget",
        seed=seed,
        code_sha="abc123",
        occurred_at=NOW,
        observation_memory=SqliteObservationMemory(tmp_path / "observations.sqlite3"),
        learning_memory=learning,
        request=request,
        source_policy=policy,
        source_acquirer=sensor,
        representation_port=HtmlDocumentRepresentationAdapter(artifacts),
        prior_rich_state=compile_rich_subject_state(subject_id="org:acme", contributions=()),
        contracts=(_contract("market-a"), _contract("market-b")),
        routing_policies=(
            DimensionRoutingPolicy("market-a", "routing-v1", PrimeRoute.DETERMINISTIC),
            DimensionRoutingPolicy("market-b", "routing-v1", PrimeRoute.DETERMINISTIC),
        ),
        research_decisions=(),
        execution_controller=_budget(max_loops=1),
        ports=ports,
    )

    assert deterministic.calls == ["market-a"]
    assert trace.budget_stop_reason == "LOOP_LIMIT_REACHED"
    history = learning.for_xeed("xeed:1")
    assert history[-1].outcome is LearningOutcome.PARTIAL
    assert history[-1].reason_code == "LOOP_LIMIT_REACHED"


def test_exact_replay_no_change_does_not_execute_prime_again(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    policy = _source_policy()
    request = _request(policy)
    sensor, artifacts = _sensor(tmp_path)
    representation_adapter = HtmlDocumentRepresentationAdapter(artifacts)
    observation = sensor.observe(request, policy)
    representation = representation_adapter.represent(request=request, observation=observation)
    memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    ingest_source_observation(
        memory=memory,
        request=request,
        observation=observation,
        contracts=(_contract("market-mode"),),
        reuse_authority=_reuse_authority(),
    )
    prior = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=representation_state_data(
            representation,
            observation_slot="website",
        ),
    )
    deterministic = _Executor("deterministic")
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")

    trace = execute_prime_source_slice(
        execution_id="run:replay",
        seed=seed,
        code_sha="abc123",
        occurred_at=NOW,
        observation_memory=memory,
        learning_memory=learning,
        request=request,
        source_policy=policy,
        source_acquirer=sensor,
        representation_port=representation_adapter,
        prior_rich_state=prior,
        contracts=(_contract("market-mode"),),
        routing_policies=(
            DimensionRoutingPolicy(
                "market-mode",
                "routing-v1",
                PrimeRoute.DETERMINISTIC,
            ),
        ),
        research_decisions=(),
        execution_controller=_budget(),
        ports=PrimeExecutionPorts(
            deterministic=deterministic,
            structured_evaluator=_Executor("structured"),
            adaptive_research=_Executor("adaptive"),
        ),
        reuse_policy=_reuse_policy(),
    )

    assert trace.prime_plan is None
    assert deterministic.calls == []
    history = learning.for_xeed("xeed:1")
    assert history[0].outcome is LearningOutcome.COMPLETED
    assert history[1].outcome is LearningOutcome.NO_CHANGE
    assert history[2].outcome is LearningOutcome.NO_CHANGE


class _FailingExecutor:
    def execute(self, *, item, state, semantic_candidates):
        raise RuntimeError("fixture execution failure")


def test_prime_executor_failure_is_recorded_before_reraise(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    policy = _source_policy()
    request = _request(policy)
    sensor, artifacts = _sensor(tmp_path)
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")

    import pytest

    with pytest.raises(RuntimeError, match="fixture execution failure"):
        execute_prime_source_slice(
            execution_id="run:failure",
            seed=seed,
            code_sha="abc123",
            occurred_at=NOW,
            observation_memory=SqliteObservationMemory(tmp_path / "observations.sqlite3"),
            learning_memory=learning,
            request=request,
            source_policy=policy,
            source_acquirer=sensor,
            representation_port=HtmlDocumentRepresentationAdapter(artifacts),
            prior_rich_state=compile_rich_subject_state(
                subject_id="org:acme",
                contributions=(),
            ),
            contracts=(_contract("market-mode"),),
            routing_policies=(
                DimensionRoutingPolicy(
                    "market-mode",
                    "routing-v1",
                    PrimeRoute.DETERMINISTIC,
                ),
            ),
            research_decisions=(),
            execution_controller=_budget(),
            ports=PrimeExecutionPorts(
                deterministic=_FailingExecutor(),
                structured_evaluator=_Executor("structured"),
                adaptive_research=_Executor("adaptive"),
            ),
        )

    failures = [
        event for event in learning.for_xeed("xeed:1") if event.outcome is LearningOutcome.FAILED
    ]
    assert len(failures) == 1
    assert failures[0].reason_code == "PRIME_EXECUTION_FAILED:RuntimeError"


def test_one_execution_reconstructs_bootstrap_to_prime_learning_sequence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    source_policy = _source_policy()
    request = _request(source_policy)
    sensor, artifacts = _sensor(tmp_path)
    observation_memory = SqliteObservationMemory(tmp_path / "observations.sqlite3")
    learning_memory = SqliteLearningMemory(tmp_path / "learning.sqlite3")
    prior = compile_rich_subject_state(subject_id="org:acme", contributions=())
    contract = _contract("market-mode")
    routing = (
        DimensionRoutingPolicy(
            "market-mode",
            "routing-v1",
            PrimeRoute.DETERMINISTIC,
        ),
    )
    bootstrap_plan = build_bootstrap_plan(
        seed=seed,
        rich_state=prior,
        policy=BootstrapPolicy(
            policy_id="xeed-bootstrap",
            version="fr17-v1",
            max_known_sources=1,
        ),
        known_sources=(
            BootstrapSourceCandidate(
                candidate_id="source:website",
                subject_id="org:acme",
                observation_slot="website",
                source_ref=request.target_uri,
                source_type=request.source_type,
                provides_fields=frozenset({"document.website.visible_text"}),
                priority=1,
            ),
        ),
        contracts=(contract,),
        routing_policies=routing,
    )
    lifecycle = plant_xeed_runtime(
        seed=seed,
        initiated_by="principal:1",
        created_at=NOW,
    )
    begin_resolution(seed=seed, state=lifecycle, occurred_at=NOW)
    apply_bootstrap_plan(
        seed=seed,
        state=lifecycle,
        plan=bootstrap_plan,
        occurred_at=NOW,
        learning_memory=learning_memory,
        execution_id="run:learning-e2e",
        code_sha="abc123",
    )

    trace = execute_prime_source_slice(
        execution_id="run:learning-e2e",
        seed=seed,
        code_sha="abc123",
        occurred_at=NOW,
        observation_memory=observation_memory,
        learning_memory=learning_memory,
        request=request,
        source_policy=source_policy,
        source_acquirer=sensor,
        representation_port=HtmlDocumentRepresentationAdapter(artifacts),
        prior_rich_state=prior,
        contracts=(contract,),
        routing_policies=routing,
        research_decisions=(),
        execution_controller=_budget(),
        ports=PrimeExecutionPorts(
            deterministic=_Executor("deterministic"),
            structured_evaluator=_Executor("structured"),
            adaptive_research=_Executor("adaptive"),
        ),
    )

    history = learning_memory.for_xeed("xeed:1")
    assert [event.kind for event in history] == [
        LearningEventKind.BOOTSTRAP,
        LearningEventKind.SOURCE_ACQUISITION,
        LearningEventKind.OBSERVATION_INGESTION,
        LearningEventKind.REPRESENTATION,
        LearningEventKind.DETERMINISTIC_EVALUATION,
    ]
    assert ":00-bootstrap:" in history[0].event_id
    assert ":01-source:" in history[1].event_id
    assert ":02-ingestion:" in history[2].event_id
    assert ":03-representation:" in history[3].event_id
    assert ":05-prime:0000:" in history[4].event_id
    assert tuple(event.event_id for event in history[1:]) == trace.learning_event_ids
    assert all(event.code_sha == "abc123" for event in history)
    assert history[0].policy_id == "xeed-bootstrap"
    assert history[1].policy_id == source_policy.policy_id
    assert history[1].activity_ref.startswith("cas:sha256:")
    assert history[2].yield_.observations_added == 1
    assert history[3].yield_.dimensions_became_answerable == 1
    assert history[0].cost.amount_microunits is None
    assert history[1].cost.amount_microunits is None
    assert history[4].cost.amount_microunits == 5

    assert history[0].replay.disposition is ReplayDisposition.NON_REPLAYABLE
    assert history[0].replay.reason_code == "BOOTSTRAP_PLAN_PAYLOAD_NOT_RETAINED"
    assert history[1].replay.disposition is ReplayDisposition.REPLAYABLE
    assert history[1].replay.require("artifact_ref") == history[1].activity_ref
    assert history[1].replay.require("source_policy_fingerprint") == source_policy.fingerprint
    assert history[2].replay.disposition is ReplayDisposition.REPLAYABLE
    assert history[3].replay.disposition is ReplayDisposition.REPLAYABLE
    assert history[3].replay.require("representation_version") == "html-document/0.1"
    assert history[3].replay.require("normalization_version") == "visible-text/0.1"
    assert history[4].replay.disposition is ReplayDisposition.REPLAYABLE
    assert history[4].replay.require("routing_policy_version") == "routing-v1"
    with pytest.raises(ValueError, match="version/value mismatch"):
        history[3].replay.require("representation_version", "html-document/999")


def test_adaptive_research_learning_yield_is_derived_from_real_work_item(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    seed = _authorized_seed()
    source_policy = _source_policy()
    request = _request(source_policy)
    sensor, artifacts = _sensor(tmp_path)
    representation_port = HtmlDocumentRepresentationAdapter(artifacts)
    prior = compile_rich_subject_state(subject_id="org:acme", contributions=())

    preview_observation = sensor.observe(request, source_policy)
    preview_representation = representation_port.represent(
        request=request,
        observation=preview_observation,
    )
    expected_state = compile_rich_subject_state(
        subject_id="org:acme",
        contributions=representation_state_data(
            preview_representation,
            observation_slot="website",
        ),
    )
    contract = TypingDimensionContract(
        dimension_id="reputation",
        version="1",
        semantic_target="public reputation state",
        primitive=SemanticPrimitive.CHOICE,
        question="What reputation state is supported?",
        state_requirements=("document.reviews.visible_text",),
        dependencies=("document.website.visible_text",),
        mutually_exclusive=False,
        abstention_policy="preserve UNKNOWN",
    )
    research_decision = decide_research_value(
        context=ResearchValueContext(
            subject_id="org:acme",
            state_fingerprint=expected_state.fingerprint,
            dimension_id="reputation",
            missing_requirements=("document.reviews.visible_text",),
            value_signals=frozenset({ResearchValueSignal.MATERIALITY}),
            rights_permit=True,
            capability_available=True,
            budget_permits=True,
            known_source_available=False,
        ),
        policy=ResearchValuePolicy(
            policy_id="research-value",
            version="fr17-v1",
            research_signals=frozenset({ResearchValueSignal.MATERIALITY}),
        ),
    )
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")

    trace = execute_prime_source_slice(
        execution_id="run:adaptive",
        seed=seed,
        code_sha="abc123",
        occurred_at=NOW,
        observation_memory=SqliteObservationMemory(tmp_path / "observations.sqlite3"),
        learning_memory=learning,
        request=request,
        source_policy=source_policy,
        source_acquirer=sensor,
        representation_port=representation_port,
        prior_rich_state=prior,
        contracts=(contract,),
        routing_policies=(
            DimensionRoutingPolicy(
                "reputation",
                "routing-v1",
                PrimeRoute.DETERMINISTIC,
            ),
        ),
        research_decisions=(research_decision,),
        execution_controller=_budget(),
        ports=PrimeExecutionPorts(
            deterministic=_Executor("deterministic"),
            structured_evaluator=_Executor("structured"),
            adaptive_research=_Executor("adaptive"),
        ),
    )

    assert trace.prime_plan is not None
    assert trace.prime_plan.items[0].route is PrimeRoute.ADAPTIVE_RESEARCH
    adaptive = next(
        event
        for event in learning.for_xeed("xeed:1")
        if event.kind is LearningEventKind.ADAPTIVE_RESEARCH
    )
    assert adaptive.outcome is LearningOutcome.COMPLETED
    assert adaptive.yield_.research_objectives_resolved == 1
    assert adaptive.mechanism.value == "ADAPTIVE_RESEARCH"


class _FailingSourceAcquirer:
    def observe(self, request, policy):
        raise RuntimeError("fixture acquisition failure")


def test_failed_source_retries_are_retained_as_distinct_learning_events(tmp_path: Path) -> None:
    seed = _authorized_seed()
    source_policy = _source_policy()
    request = _request(source_policy)
    _sensor_instance, artifacts = _sensor(tmp_path)
    learning = SqliteLearningMemory(tmp_path / "learning.sqlite3")

    for execution_id in ("run:retry:1", "run:retry:2"):
        with pytest.raises(RuntimeError, match="fixture acquisition failure"):
            execute_prime_source_slice(
                execution_id=execution_id,
                seed=seed,
                code_sha="abc123",
                occurred_at=NOW,
                observation_memory=SqliteObservationMemory(tmp_path / "observations.sqlite3"),
                learning_memory=learning,
                request=request,
                source_policy=source_policy,
                source_acquirer=_FailingSourceAcquirer(),
                representation_port=HtmlDocumentRepresentationAdapter(artifacts),
                prior_rich_state=compile_rich_subject_state(
                    subject_id="org:acme",
                    contributions=(),
                ),
                contracts=(_contract("market-mode"),),
                routing_policies=(
                    DimensionRoutingPolicy(
                        "market-mode",
                        "routing-v1",
                        PrimeRoute.DETERMINISTIC,
                    ),
                ),
                research_decisions=(),
                execution_controller=_budget(),
                ports=PrimeExecutionPorts(
                    deterministic=_Executor("deterministic"),
                    structured_evaluator=_Executor("structured"),
                    adaptive_research=_Executor("adaptive"),
                ),
            )

    failures = learning.for_xeed("xeed:1")
    assert len(failures) == 2
    assert all(event.kind is LearningEventKind.SOURCE_ACQUISITION for event in failures)
    assert all(event.outcome is LearningOutcome.FAILED for event in failures)
    assert failures[0].event_id != failures[1].event_id
    assert all(event.cost.amount_microunits is None for event in failures)
    assert all(event.reason_code == "SOURCE_ACQUISITION_FAILED:RuntimeError" for event in failures)
