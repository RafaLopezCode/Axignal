from __future__ import annotations

import json
import socket
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from application.economic_discovery.contracts import (
    ConfidenceCapability,
    ConfidenceSemantics,
    DistributionAvailability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredJudgment,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetPolicy,
    ExecutionReservationRejected,
    GovernedExecutionController,
)
from application.economic_discovery.explanation import BasisContribution
from application.economic_discovery.first_vertical import EconomicEvaluationRequest
from application.economic_discovery.first_vertical_e2e import (
    EconomicFieldSpec,
    FirstEconomicVerticalE2EResult,
    FirstVerticalSourcePlan,
    run_first_economic_vertical_e2e,
)
from application.economic_discovery.observation_memory import (
    ObservationAccessStatus,
    ObservationReuseScope,
    ObservationRightsStatus,
)
from application.economic_discovery.observation_reuse import ReusePurpose
from application.economic_discovery.source_registry import (
    RobotsDecision,
    RobotsRequirement,
    SourceRatePolicy,
    SourceRegistryAuthorization,
    SourceRegistryEntry,
    SourceRetentionPolicy,
    StaticSourceRegistry,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.semantic_extraction import (
    GroundingSurface,
    SemanticCandidateSet,
    SemanticExtractionContract,
    SemanticTarget,
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)
from application.source_acquisition import SourceObservation, SourceRequest, SourceTargetRule
from application.source_representation import DocumentRepresentation
from domain.evidence.admission import SourceAuthority
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.identity import IdentityBindingAuthority
from domain.identity_binding import GovernedIdentityBinding
from domain.representation import RepresentationSpan, TextRepresentation, TextSurface
from domain.xignal import XignalEpistemicState
from pipeline.entity_resolution import ExactNameResolver, ResolutionCandidate
from pipeline.source_acquisition import (
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PinnedHttpTransport,
    PublicSourcePolicyGate,
    RawHttpResponse,
    ResolvedTarget,
)
from pipeline.source_representation import HtmlDocumentRepresentationAdapter

CORPUS: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures/refrigeration-v1.json").read_text(encoding="utf-8")
)
OBSERVED_AT = datetime.fromisoformat(CORPUS["observed_at"])
AS_OF = datetime.fromisoformat(CORPUS["as_of"])
TEMPORAL = TemporalCurrentnessPolicy(
    "eb04-synthetic-currentness",
    "1",
    timedelta(days=30),
    timedelta(days=90),
)


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


class FixtureTransport(PinnedHttpTransport):
    instrument_ref = "synthetic-eb04-http/1"

    def __init__(self, bodies: dict[str, bytes]) -> None:
        super().__init__()
        self._bodies = bodies
        self.calls: list[str] = []

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        del timeout_ms, max_response_bytes
        self.calls.append(target.host)
        body = self._bodies[target.host]
        return RawHttpResponse(
            status=200,
            headers=(("Content-Type", "text/html; charset=utf-8"),),
            body=body,
            peer_ip="8.8.8.8",
        )


class FixtureSemanticExtractor:
    def __init__(
        self,
        fields_by_subject: dict[str, dict[str, str]],
        *,
        omit_targets: frozenset[str] = frozenset(),
    ) -> None:
        self._fields_by_subject = fields_by_subject
        self._omit_targets = omit_targets
        self.calls: list[str] = []

    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet:
        self.calls.append(representation.subject_id)
        fields = self._fields_by_subject[representation.subject_id]
        rows: list[dict[str, object]] = []
        for target in contract.targets:
            if target.target_id in self._omit_targets:
                continue
            value = fields[target.target_id]
            excerpt = value
            if target.target_id in {"capability", "legal_identity", "revenue"}:
                first_sentence = representation.visible_text.split(". ", 1)[0]
                excerpt = first_sentence if first_sentence.endswith(".") else f"{first_sentence}."
            rows.append(
                {
                    "semantic_target": target.target_id,
                    "statement": value,
                    "excerpt": excerpt,
                    "grounding_surface": (
                        GroundingSurface.VISIBLE_TEXT.value
                        if representation.visibility_resolved
                        else GroundingSurface.EXTRACTED_TEXT.value
                    ),
                }
            )
        request = build_semantic_extraction_request(representation, contract)
        return normalize_semantic_extraction_payload(
            request=request,
            provider="synthetic-eb04-extractor",
            payload={"provider_version": "fixture-v1", "candidates": rows},
            representation=representation,
            contract=contract,
        )


class FixtureIdentityBindingPort:
    def __init__(self) -> None:
        self._resolver = ExactNameResolver(
            (
                ResolutionCandidate("org:arbor-cooling", "Arbor Cooling"),
                ResolutionCandidate("org:harbor-storage", "Harbor Storage"),
            )
        )

    def bind(
        self,
        *,
        subject_id: str,
        mention: str,
        support: RepresentationSpan,
        representation: TextRepresentation,
    ) -> GovernedIdentityBinding:
        support_text = support.extract(representation)
        relative = support_text.find(mention)
        if relative < 0:
            raise ValueError("identity mention is absent from the supporting claim")
        mention_span = RepresentationSpan(
            representation.representation_id,
            representation.fingerprint,
            support.start + relative,
            support.start + relative + len(mention),
        )
        binding = self._resolver.bind_mention(
            representation=representation,
            mention_span=mention_span,
            decision_id=f"identity:eb04:{subject_id}",
            evidence_refs=(f"identity-authority:eb04:{subject_id}",),
            authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
            decided_by="eb04-synthetic-identity-authority",
            decided_at=OBSERVED_AT,
            as_of=OBSERVED_AT,
        )
        assert binding.request.entity_id == subject_id
        return binding


class AlwaysYesEvaluator:
    capability_profile = EvaluatorCapabilityProfile(
        "eb04-choice-only",
        "1",
        DistributionCapability.NEVER,
        ConfidenceCapability.NEVER,
        replay_reference_supported=True,
    )

    def __init__(self, *, fail: frozenset[str] = frozenset()) -> None:
        self.requests: list[EconomicEvaluationRequest] = []
        self.fail = fail

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        assert isinstance(request, EconomicEvaluationRequest)
        self.requests.append(request)
        if request.dimension.dimension_id in self.fail:
            raise TimeoutError("synthetic evaluator outage")
        return StructuredJudgment(
            selected_option="YES",
            evaluator="synthetic-eb04-choice-evaluator",
            evaluator_version="fixture-v1",
            decision_contract_id=request.decision_contract_id,
            state_fingerprint=request.state_fingerprint,
            question_fingerprint=request.question_fingerprint,
            choice_space_fingerprint=request.choice_space_fingerprint,
            capability_profile=self.capability_profile,
            distribution_availability=DistributionAvailability.UNAVAILABLE,
            confidence_semantics=ConfidenceSemantics.UNAVAILABLE,
            replay_reference=(
                f"eb04-eval:{request.dimension.dimension_id}:{request.state_fingerprint}"
            ),
        )


def _html(text: str) -> bytes:
    return f"<html><body><main><p>{text}</p></main></body></html>".encode()


class UnresolvedVisibilityRepresentationPort:
    def __init__(self, delegate: HtmlDocumentRepresentationAdapter) -> None:
        self._delegate = delegate

    def represent(
        self, *, request: SourceRequest, observation: SourceObservation
    ) -> DocumentRepresentation:
        representation = self._delegate.represent(request=request, observation=observation)
        return replace(
            representation,
            extracted_text=representation.document_text,
            extracted_text_fingerprint=representation.document_text_fingerprint,
            visibility_resolved=False,
        )


def _entry(document: dict[str, object], instrument_ref: str) -> SourceRegistryEntry:
    source_ref = str(document["source_ref"])
    host = source_ref.split("/")[2]
    source_type = str(document["source_type"])
    source_id = str(document["id"])
    return SourceRegistryEntry(
        source_id=source_id,
        version="1",
        source_type=source_type,
        instrument_ref=instrument_ref,
        decision_basis="AXIGNAL-authored synthetic EB-04 source fixture",
        targets=(SourceTargetRule(host, "/", ("https",)),),
        allowed_purposes=(ReusePurpose.CURRENT_STATE,),
        rights_status=ObservationRightsStatus.PERMITTED,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        reuse_scope=ObservationReuseScope.GLOBAL_PUBLIC,
        reuse_reason="AXIGNAL-authored synthetic source may be reused for deterministic tests",
        temporal_policy=TEMPORAL,
        retention_policy=SourceRetentionPolicy(
            policy_id="eb04-synthetic-retention",
            version="1",
            raw_retention_days=30,
            metadata_retention_days=365,
        ),
        rate_policy=SourceRatePolicy(
            policy_id="eb04-synthetic-rate",
            version="1",
            max_requests=20,
            window_seconds=60,
        ),
        robots_requirement=RobotsRequirement.NOT_REQUIRED_SINGLE_DOCUMENT,
        robots_decision=RobotsDecision.NOT_APPLICABLE,
        robots_policy_ref="robots:synthetic-single-document:v1",
        currentness=Currentness.CURRENT,
        timeout_ms=2_000,
    )


def _authorization(
    registry: StaticSourceRegistry,
    document: dict[str, object],
    instrument_ref: str,
) -> SourceRegistryAuthorization:
    source_id = str(document["id"])
    return registry.authorize(
        source_id=source_id,
        request_id=f"request:eb04:{source_id}",
        subject_id=str(document["subject_id"]),
        observation_slot="economic-source",
        target_uri=str(document["source_ref"]),
        source_type=str(document["source_type"]),
        purpose=ReusePurpose.CURRENT_STATE,
        instrument_ref=instrument_ref,
    )


def _contract(name: str, fields: dict[str, str]) -> SemanticExtractionContract:
    return SemanticExtractionContract(
        contract_id=f"eb04:{name}",
        version="1",
        targets=tuple(
            SemanticTarget(field, f"Extract the exact source-stated economic field '{field}'.")
            for field in fields
        ),
    )


def _run_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    subject_doc: dict[str, Any] | None = None,
    activity_doc: dict[str, Any] | None = None,
    subject_specs: tuple[EconomicFieldSpec, ...] | None = None,
    activity_field_names: tuple[str, ...] | None = None,
    evaluator: AlwaysYesEvaluator | None = None,
    budget_policy: ExecutionBudgetPolicy | None = None,
    transport: FixtureTransport | None = None,
    unresolved_visibility: bool = False,
) -> tuple[
    FirstEconomicVerticalE2EResult,
    FixtureTransport,
    FixtureSemanticExtractor,
    AlwaysYesEvaluator,
    GovernedExecutionController,
]:
    subject = subject_doc or CORPUS["documents"][0]
    activity = activity_doc or CORPUS["documents"][1]
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    fixture_transport = transport or FixtureTransport(
        {
            str(subject["source_ref"]).split("/")[2]: _html(str(subject["text"])),
            str(activity["source_ref"]).split("/")[2]: _html(str(activity["text"])),
        }
    )
    registry = StaticSourceRegistry(
        (
            _entry(subject, fixture_transport.instrument_ref),
            _entry(activity, fixture_transport.instrument_ref),
        )
    )
    subject_auth = _authorization(registry, subject, fixture_transport.instrument_ref)
    activity_auth = _authorization(registry, activity, fixture_transport.instrument_ref)

    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    source_acquirer = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=fixture_transport,
        artifacts=artifacts,
        clock=lambda: OBSERVED_AT,
    )
    representation_adapter = HtmlDocumentRepresentationAdapter(artifacts)
    representation_port = (
        UnresolvedVisibilityRepresentationPort(representation_adapter)
        if unresolved_visibility
        else representation_adapter
    )

    subject_fields = dict(subject["fields"])
    all_activity_fields = dict(activity["fields"])
    selected_activity_names = activity_field_names or tuple(all_activity_fields)
    selected_activity_fields = {name: all_activity_fields[name] for name in selected_activity_names}
    semantic_extractor = FixtureSemanticExtractor(
        {
            str(subject["subject_id"]): subject_fields,
            str(activity["subject_id"]): all_activity_fields,
        }
    )
    fixture_evaluator = evaluator or AlwaysYesEvaluator()

    default_subject_specs = tuple(
        EconomicFieldSpec(
            semantic_target=name,
            field_name=name,
            canonical_authority=SourceAuthority.OFFICIAL_WEB if name == "capability" else None,
            predicate_mention=(
                str(subject["capability_predicate_mention"]) if name == "capability" else None
            ),
        )
        for name in subject_fields
    )
    subject_plan = FirstVerticalSourcePlan(
        authorization=subject_auth,
        extraction_contract=_contract("subject", subject_fields),
        subject_mention=str(subject["subject_mention"]),
        fields=subject_specs or default_subject_specs,
    )
    activity_plan = FirstVerticalSourcePlan(
        authorization=activity_auth,
        extraction_contract=_contract("activity", selected_activity_fields),
        subject_mention="Harbor Storage",
        fields=tuple(
            EconomicFieldSpec(semantic_target=name, field_name=name)
            for name in selected_activity_fields
        ),
    )
    controller = GovernedExecutionController(
        budget_policy
        or ExecutionBudgetPolicy(
            policy_id="eb04-reference-run",
            version="1",
            max_requests=8,
            max_sources=2,
            max_elapsed_ms=10_000,
            max_loops=3,
        )
    )
    result = run_first_economic_vertical_e2e(
        subject_plan=subject_plan,
        activity_plan=activity_plan,
        source_acquirer=source_acquirer,
        representation_port=representation_port,
        semantic_extractor=semantic_extractor,
        binding_port=FixtureIdentityBindingPort(),
        evaluator=fixture_evaluator,
        execution_controller=controller,
        as_of=AS_OF,
    )
    return result, fixture_transport, semantic_extractor, fixture_evaluator, controller


def _wire(result: FirstEconomicVerticalE2EResult) -> dict[str, Any]:
    return cast(dict[str, Any], result.human_output.to_wire())


def _controller() -> GovernedExecutionController:
    return GovernedExecutionController(
        ExecutionBudgetPolicy(
            policy_id="eb04-e2e-budget",
            version="1",
            max_requests=8,
            max_sources=4,
            max_elapsed_ms=10_000,
            max_loops=3,
        )
    )


def test_first_economic_vertical_composes_real_governed_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    subject_doc = CORPUS["documents"][0]
    activity_doc = CORPUS["documents"][1]
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    transport = FixtureTransport(
        {
            str(subject_doc["source_ref"]).split("/")[2]: _html(str(subject_doc["text"])),
            str(activity_doc["source_ref"]).split("/")[2]: _html(str(activity_doc["text"])),
        }
    )
    registry = StaticSourceRegistry(
        (
            _entry(subject_doc, transport.instrument_ref),
            _entry(activity_doc, transport.instrument_ref),
        )
    )
    subject_auth = _authorization(registry, subject_doc, transport.instrument_ref)
    activity_auth = _authorization(registry, activity_doc, transport.instrument_ref)

    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    source_acquirer = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=transport,
        artifacts=artifacts,
        clock=lambda: OBSERVED_AT,
    )
    representation_port = HtmlDocumentRepresentationAdapter(artifacts)
    semantic_extractor = FixtureSemanticExtractor(
        {
            str(subject_doc["subject_id"]): subject_doc["fields"],
            str(activity_doc["subject_id"]): activity_doc["fields"],
        }
    )
    evaluator = AlwaysYesEvaluator()

    subject_plan = FirstVerticalSourcePlan(
        authorization=subject_auth,
        extraction_contract=_contract("subject", subject_doc["fields"]),
        subject_mention=str(subject_doc["subject_mention"]),
        fields=tuple(
            EconomicFieldSpec(
                semantic_target=name,
                field_name=name,
                canonical_authority=SourceAuthority.OFFICIAL_WEB if name == "capability" else None,
                predicate_mention=(
                    str(subject_doc["capability_predicate_mention"])
                    if name == "capability"
                    else None
                ),
            )
            for name in subject_doc["fields"]
        ),
    )
    activity_plan = FirstVerticalSourcePlan(
        authorization=activity_auth,
        extraction_contract=_contract("activity", activity_doc["fields"]),
        subject_mention="Harbor Storage",
        fields=tuple(
            EconomicFieldSpec(semantic_target=name, field_name=name)
            for name in activity_doc["fields"]
        ),
    )

    execution_controller = GovernedExecutionController(
        ExecutionBudgetPolicy(
            policy_id="eb04-reference-run",
            version="1",
            max_requests=8,
            max_sources=4,
            max_elapsed_ms=10_000,
            max_loops=3,
        )
    )
    result = run_first_economic_vertical_e2e(
        subject_plan=subject_plan,
        activity_plan=activity_plan,
        source_acquirer=source_acquirer,
        representation_port=representation_port,
        semantic_extractor=semantic_extractor,
        binding_port=FixtureIdentityBindingPort(),
        evaluator=evaluator,
        execution_controller=execution_controller,
        as_of=AS_OF,
    )

    subject_capability = next(
        item for item in result.subject_source.state.observations if item.datum.name == "capability"
    )
    activity_event = next(
        item for item in result.activity_source.state.observations if item.datum.name == "event"
    )
    wire = _wire(result)

    assert transport.calls == ["arbor-cooling.example", "harbor-storage.example"]
    assert semantic_extractor.calls == ["org:arbor-cooling", "org:harbor-storage"]
    assert result.pipeline_version == "economic-first-vertical-e2e:v2"
    assert result.epistemic_policy_version == "eb04-source-predicate-epistemics:v1"
    assert subject_capability is not None
    assert subject_capability.epistemic_state is EpistemicState.DECLARED
    assert subject_capability.canonical_support is not None
    assert subject_capability.canonical_support.epistemic_state is EpistemicState.DECLARED
    assert activity_event is not None
    assert activity_event.epistemic_state is EpistemicState.DECLARED
    assert result.reasoning.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL
    assert result.reasoning.interpretation.attention.value == "WARRANTED_ATTENTION"
    assert [request.dimension.dimension_id for request in evaluator.requests] == [
        "supplier_role",
        "customer_role",
        "functional_alignment",
    ]
    assert wire["epistemic_state"] == "POTENTIAL"
    assert wire["attention"] == "WARRANTED_ATTENTION"
    assert wire["headline"] == "Potential project relevance"
    assert result.execution_state.requests == 7
    assert result.execution_state.sources == 2
    assert result.execution_state.loops == 3
    assert result.execution_state.amount_microunits is None
    assert result.execution_state.cost_complete is False
    assert result.execution_state.elapsed_ms >= 0
    assert len(result.attempts) == 7
    assert tuple(item.attempt_kind for item in result.attempts) == (
        "source",
        "semantic",
        "source",
        "semantic",
        "structured-evaluate",
        "structured-evaluate",
        "structured-evaluate",
    )
    assert all(item.succeeded for item in result.attempts)
    assert execution_controller.active_reservation_ids == ()
    assert len(result.replay_refs) == 7
    assert len(wire["evidence"]) == 12
    assert {item["source_ref"] for item in wire["evidence"]} == {
        subject_doc["source_ref"],
        activity_doc["source_ref"],
    }
    assert any(item["canonical_support_ref"] for item in wire["evidence"])
    assert all(item["rights_basis_ref"] for item in wire["evidence"])
    assert all(item["support_span"] is not None for item in wire["evidence"])
    assert all(
        item["support_span"]["start"] < item["support_span"]["end"] for item in wire["evidence"]
    )
    assert "sale probability" in " ".join(wire["coverage_limits"]).lower()


def test_official_web_capability_stays_declared_with_unresolved_visibility(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result, _transport, _extractor, _evaluator, _controller = _run_fixture(
        monkeypatch,
        tmp_path,
        unresolved_visibility=True,
    )
    capability = next(
        item for item in result.subject_source.state.observations if item.datum.name == "capability"
    )

    assert capability.epistemic_state is EpistemicState.DECLARED
    assert capability.canonical_support is not None
    assert capability.canonical_support.epistemic_state is EpistemicState.DECLARED
    assert capability.representation is not None
    assert capability.representation.surface is TextSurface.EXTRACTED_TEXT
    assert capability.canonical_support.evidence_refs == (capability.basis.evidence_ref,)


def test_registry_legal_identity_is_observed_as_a_registry_proposition(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    subject_doc = dict(CORPUS["documents"][0])
    subject_doc.update(
        {
            "source_type": "REGISTRY",
            "text": "Arbor Cooling is registered as a limited company.",
            "fields": {"legal_identity": "Arbor Cooling"},
            "capability_predicate_mention": "is registered",
        }
    )
    spec = EconomicFieldSpec(
        semantic_target="legal_identity",
        field_name="legal_identity",
        canonical_authority=SourceAuthority.REGISTRY,
        predicate_mention="is registered",
    )
    result, *_ = _run_fixture(
        monkeypatch,
        tmp_path,
        subject_doc=subject_doc,
        subject_specs=(spec,),
    )
    identity = next(
        item
        for item in result.subject_source.state.observations
        if item.datum.name == "legal_identity"
    )

    assert identity.epistemic_state is EpistemicState.OBSERVED
    assert identity.canonical_support is not None
    assert identity.canonical_support.epistemic_state is EpistemicState.OBSERVED
    assert identity.canonical_support.predicate == "legal_identity"
    assert identity.canonical_support.object_or_value == "Arbor Cooling"


def test_admitted_corporate_revenue_pair_without_epistemic_rule_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    subject_doc = dict(CORPUS["documents"][0])
    subject_doc.update(
        {
            "source_type": "CORPORATE_DOCUMENT",
            "text": "Arbor Cooling reported revenue of $4m.",
            "fields": {"revenue": "$4m"},
            "capability_predicate_mention": "reported revenue",
        }
    )
    spec = EconomicFieldSpec(
        semantic_target="revenue",
        field_name="revenue",
        canonical_authority=SourceAuthority.CORPORATE_DOCUMENT,
        predicate_mention="reported revenue",
    )

    with pytest.raises(ValueError, match="no approved epistemic policy"):
        _run_fixture(
            monkeypatch,
            tmp_path,
            subject_doc=subject_doc,
            subject_specs=(spec,),
        )


def test_missing_material_context_stays_unknown_and_routes_to_investigation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    activity_fields = tuple(
        name for name in CORPUS["documents"][1]["fields"] if name != "required_certification"
    )

    result, _transport, _extractor, _evaluator, controller = _run_fixture(
        monkeypatch,
        tmp_path,
        activity_field_names=activity_fields,
    )
    wire = _wire(result)
    eligibility = next(item for item in wire["dimensions"] if item["dimension_id"] == "eligibility")

    assert result.reasoning.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.reasoning.interpretation.attention.value == "INVESTIGATE"
    assert eligibility["disposition"] == "NOT_ANSWERABLE"
    assert eligibility["value"] is None
    assert "MISSING:activity.required_certification" in str(eligibility["reason"])
    assert wire["headline"] == "Project relevance remains unresolved"
    assert controller.active_reservation_ids == ()


def test_evaluator_outage_degrades_safely_without_losing_attempt_accounting(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    evaluator = AlwaysYesEvaluator(fail=frozenset({"functional_alignment"}))

    result, _transport, _extractor, _evaluator, controller = _run_fixture(
        monkeypatch,
        tmp_path,
        evaluator=evaluator,
    )
    wire = _wire(result)
    alignment = next(
        item
        for item in result.reasoning.vector.evaluations
        if item.dimension_id == "functional_alignment"
    )

    assert result.reasoning.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.reasoning.interpretation.attention.value == "INVESTIGATE"
    assert alignment.disposition.value == "NOT_ANSWERABLE"
    assert alignment.reason == "EVALUATOR_FAILURE:TimeoutError"
    structured_attempts = tuple(
        item for item in result.attempts if item.attempt_kind == "structured-evaluate"
    )
    assert len(structured_attempts) == 3
    assert [item.succeeded for item in structured_attempts] == [True, True, False]
    assert result.execution_state.requests == 7
    assert result.execution_state.loops == 3
    assert controller.active_reservation_ids == ()
    assert wire["epistemic_state"] == "UNKNOWN"


def test_contradicting_source_material_prevents_positive_presentation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    base = CORPUS["documents"][0]
    dispute = CORPUS["documents"][2]
    subject_doc = dict(base)
    subject_fields = dict(base["fields"])
    subject_fields["capability_dispute"] = dispute["fields"]["capability_dispute"]
    subject_doc["fields"] = subject_fields
    subject_doc["text"] = f"{base['text']} {dispute['text']}"

    subject_specs = tuple(
        EconomicFieldSpec(
            semantic_target=name,
            field_name=name,
            canonical_authority=SourceAuthority.OFFICIAL_WEB if name == "capability" else None,
            predicate_mention=(
                str(base["capability_predicate_mention"]) if name == "capability" else None
            ),
            contribution=(
                BasisContribution.CONTRADICTS
                if name == "capability_dispute"
                else BasisContribution.SUPPORTS
            ),
            contradicts_fields=("capability",) if name == "capability_dispute" else (),
        )
        for name in subject_fields
    )

    result, _transport, _extractor, evaluator, controller = _run_fixture(
        monkeypatch,
        tmp_path,
        subject_doc=subject_doc,
        subject_specs=subject_specs,
    )
    wire = _wire(result)

    assert result.reasoning.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.reasoning.interpretation.attention.value == "INVESTIGATE"
    assert "functional_alignment" not in [
        request.dimension.dimension_id for request in evaluator.requests
    ]
    assert str(dispute["fields"]["capability_dispute"]) in wire["contradictions"]
    assert wire["epistemic_state"] == "UNKNOWN"
    assert wire["headline"] == "Project relevance remains unresolved"
    assert controller.active_reservation_ids == ()


def test_source_budget_blocks_second_fetch_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    subject_doc = CORPUS["documents"][0]
    activity_doc = CORPUS["documents"][1]
    transport = FixtureTransport(
        {
            str(subject_doc["source_ref"]).split("/")[2]: _html(str(subject_doc["text"])),
            str(activity_doc["source_ref"]).split("/")[2]: _html(str(activity_doc["text"])),
        }
    )

    with pytest.raises(ExecutionReservationRejected) as exc_info:
        _run_fixture(
            monkeypatch,
            tmp_path,
            transport=transport,
            budget_policy=ExecutionBudgetPolicy(
                policy_id="eb04-one-source-only",
                version="1",
                max_requests=8,
                max_sources=1,
                max_elapsed_ms=10_000,
                max_loops=3,
            ),
        )

    assert exc_info.value.decision.stop_reason is not None
    assert exc_info.value.decision.stop_reason.value == "SOURCE_BUDGET_EXHAUSTED"
    assert transport.calls == ["arbor-cooling.example"]


def test_replay_reproduces_same_semantic_output_and_references(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first, *_ = _run_fixture(monkeypatch, tmp_path / "first")
    second, *_ = _run_fixture(monkeypatch, tmp_path / "second")

    assert first.pipeline_version == second.pipeline_version
    assert first.replay_refs == second.replay_refs
    assert tuple(item.reservation_id for item in first.attempts) == tuple(
        item.reservation_id for item in second.attempts
    )
    assert first.human_output.output_id == second.human_output.output_id
    assert first.human_output.to_wire() == second.human_output.to_wire()
