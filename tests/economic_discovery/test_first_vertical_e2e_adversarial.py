"""EB-04 exit criteria over public APIs; unmarked failures are implementation gaps.

All documents/entities are authored synthetic fixtures at reserved .example
URLs. No network, provider SDK or private payload is used. Fixture assembly is
explicit test composition, not evidence that a production composition exists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.economic_discovery.brain_contracts import (
    AttentionDisposition,
    DimensionDisposition,
)
from application.economic_discovery.contracts import (
    ConfidenceCapability,
    ConfidenceSemantics,
    DistributionAvailability,
    DistributionCapability,
    EvaluatorCapabilityProfile,
    StructuredEvaluationRequest,
    StructuredJudgment,
)
from application.economic_discovery.economic_state import (
    EconomicObservation,
    EvidenceBackedEconomicState,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    ExecutionBudgetPolicy,
    ExecutionBudgetReservation,
    ExecutionBudgetState,
    ExecutionReservationRejected,
    ExecutionStopReason,
    GovernedExecutionController,
)
from application.economic_discovery.explanation import BasisContribution, BasisDatum
from application.economic_discovery.first_vertical import (
    EconomicEvaluationRequest,
    run_economic_vertical,
)
from application.economic_discovery.governed_dispatch import (
    GovernedDispatchRecorder,
    GovernedStructuredEvaluator,
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
    SourceRegistryRejected,
    SourceRetentionPolicy,
    StaticSourceRegistry,
)
from application.economic_discovery.temporal_currentness import TemporalCurrentnessPolicy
from application.semantic_extraction import (
    SemanticExtractionContract,
    SemanticTarget,
    build_semantic_extraction_request,
    normalize_semantic_extraction_payload,
)
from application.source_acquisition import SourceObservation, SourceTargetRule
from application.source_representation import (
    DocumentRepresentation,
    RichStateDatum,
    compile_rich_subject_state,
)
from application.subscriber_projection.economic_output import compile_economic_human_output
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    EvidenceAdmissionRequired,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId, IdentityBindingAuthority
from domain.relationships.model import ObservedRelationship
from domain.representation import text_fingerprint
from domain.xignal import XignalEpistemicState
from pipeline.entity_resolution import ExactNameResolver, ResolutionCandidate, ResolutionStatus
from pipeline.source_acquisition import ContentAddressedArtifactStore
from pipeline.source_representation import represent_html_observation

NOW = datetime(2026, 10, 5, 12, tzinfo=UTC)
TEMPORAL = TemporalCurrentnessPolicy(
    "eb04-synthetic-currentness", "1", timedelta(30), timedelta(90)
)
CLAIM = "ACME manufactures industrial pumps."
SUBJECT_FIELDS = {
    "capability": "industrial pumps",
    "supply_activity": "supplies pump systems",
    "purchase_activity": "purchases electrical motors",
    "reach_region": "region:coast",
    "delivery_mode": "onsite",
    "certification": "pump-cert:v1",
}
ACTIVITY_FIELDS = {
    "event": "announces a pump station expansion",
    "required_capability": "pump installation",
    "region": "region:coast",
    "delivery_mode": "onsite",
    "required_certification": "pump-cert:v1",
    "action_until": "2026-11-01T00:00:00+00:00",
}
SUBJECT_TEXT = (
    f"{CLAIM} Supplier activity: supplies pump systems. Customer activity: purchases electrical motors. "
    "Pump delivery region: region:coast. Pump delivery mode: onsite. Pump certification: pump-cert:v1."
)
ACTIVITY_TEXT = (
    "PORT announces a pump station expansion. Required capability: pump installation. "
    "Project region: region:coast. Project delivery mode: onsite. Project qualification: pump-cert:v1. "
    "Attention window ends at 2026-11-01T00:00:00+00:00. No supplier or contract is named."
)


def _entry(subject_id: str, source_type: str = "OFFICIAL_WEB") -> SourceRegistryEntry:
    return SourceRegistryEntry(
        source_id=f"synthetic:{subject_id}",
        version="1",
        source_type=source_type,
        instrument_ref="authored-synthetic-capture:v1",
        decision_basis="AXIGNAL-authored fictional documents; no external acquisition",
        targets=(SourceTargetRule("eb04.example", "/", ("https",)),),
        allowed_purposes=(ReusePurpose.CURRENT_STATE,),
        rights_status=ObservationRightsStatus.PERMITTED,
        access_status=ObservationAccessStatus.ACCESSIBLE,
        reuse_scope=ObservationReuseScope.GLOBAL_PUBLIC,
        reuse_reason="Authored synthetic public test material, reusable with exact provenance",
        temporal_policy=TEMPORAL,
        retention_policy=SourceRetentionPolicy("synthetic-retention", "1", 30, 90),
        rate_policy=SourceRatePolicy("synthetic-rate", "1", 6, 60),
        robots_requirement=RobotsRequirement.NOT_REQUIRED_SINGLE_DOCUMENT,
        robots_decision=RobotsDecision.NOT_APPLICABLE,
        robots_policy_ref="synthetic-single-document:v1",
    )


def _authorize(entry: SourceRegistryEntry) -> SourceRegistryAuthorization:
    return StaticSourceRegistry((entry,)).authorize(
        source_id=entry.source_id,
        request_id=f"request:{entry.source_id}",
        subject_id=entry.source_id.removeprefix("synthetic:"),
        observation_slot="economic-document",
        target_uri=f"https://eb04.example/{entry.source_id}",
        source_type=entry.source_type,
        purpose=ReusePurpose.CURRENT_STATE,
        instrument_ref=entry.instrument_ref,
    )


def _document(
    root: Path, subject_id: str, text: str, source_type: str = "OFFICIAL_WEB"
) -> tuple[DocumentRepresentation, SourceRegistryAuthorization]:
    # Authorize metadata before writing or representing any fixture payload.
    authorization = _authorize(_entry(subject_id, source_type))
    request = authorization.request
    store = ContentAddressedArtifactStore(root)
    html = f"<html><body><p>{text}</p></body></html>"
    observation = SourceObservation(
        request_id=request.request_id,
        subject_id=subject_id,
        observation_slot=request.observation_slot,
        requested_uri=request.target_uri,
        final_uri=request.target_uri,
        retrieved_at=NOW,
        http_status=200,  # Simulated response envelope; never fetched.
        content_type="text/html; charset=utf-8",
        body_fingerprint=text_fingerprint(html),
        body_artifact_ref=store.put_bytes(html.encode()),
        raw_observation_ref=store.put_json({"fixture": "eb04-adversarial:v1", "text": text}),
        observation_fingerprint=text_fingerprint(subject_id + html),
        instrument_ref="authored-synthetic-capture:v1",
        policy_id=request.policy_id,
        policy_version=request.policy_version,
        policy_fingerprint=request.policy_fingerprint,
        redirect_chain=(request.target_uri,),
        peer_ips=("192.0.2.10",),  # Documentation address in the simulated envelope.
        failure_state=None,
    )
    return (
        represent_html_observation(request=request, observation=observation, artifacts=store),
        authorization,
    )


def _evidence(document: DocumentRepresentation) -> Evidence:
    representation = document.text_representation()
    binding = ExactNameResolver((ResolutionCandidate("org:acme", "ACME"),)).bind_mention(
        representation=representation,
        mention_span=representation.unique_span("ACME"),
        decision_id="identity:acme:v1",
        evidence_refs=("synthetic-registry:acme:v1",),
        authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
        decided_by="synthetic-identity-control-plane",
        decided_at=NOW,
        as_of=NOW,
    )
    return Evidence(
        id="evidence:acme:capability",
        source=document.source_ref,
        source_type=document.source_type,
        reference=document.source_ref,
        extracted_claim=CLAIM,
        observed_at=NOW,
        authority=SourceAuthority.OFFICIAL_WEB,
        observation_subject_id="org:acme",
        representation=representation,
        grounded_claim=GroundedClaim(
            subject_id="org:acme",
            predicate="capability",
            object_or_value=SUBJECT_FIELDS["capability"],
            subject_mention="ACME",
            predicate_mention="manufactures",
            object_mention=SUBJECT_FIELDS["capability"],
            supporting_excerpt=CLAIM,
            supporting_span=representation.unique_span(CLAIM),
            subject_binding=binding,
        ),
    )


def _state(subject_id: str, observations: tuple[EconomicObservation, ...]):
    return EvidenceBackedEconomicState(
        compile_rich_subject_state(
            subject_id=subject_id, contributions=tuple(item.datum for item in observations)
        ),
        observations,
    )


def _observations(document, authorization, fields, support=None):
    contract = SemanticExtractionContract(
        "eb04-synthetic-field-extraction",
        "1",
        tuple(
            SemanticTarget(name, f"Source-stated {name} in this document's scope")
            for name in fields
        ),
    )
    proposals = normalize_semantic_extraction_payload(
        request=build_semantic_extraction_request(document, contract),
        provider="synthetic-field-proposer",
        payload={
            "provider_version": "1",
            "candidates": [
                {
                    "semantic_target": name,
                    "statement": value,
                    "excerpt": value,
                    "grounding_surface": "VISIBLE_TEXT",
                }
                for name, value in fields.items()
            ],
        },
        representation=document,
        contract=contract,
    )
    assert not proposals.is_canonical_truth
    observations = []
    for proposal in proposals.candidates:
        canonical = support if proposal.semantic_target == "capability" else None
        observations.append(
            EconomicObservation(
                datum=RichStateDatum(
                    proposal.semantic_target,
                    proposal.excerpt,
                    document.observation_id,
                    document.representation_id,
                    document.source_ref,
                    NOW,
                    proposal.supporting_span,
                ),
                basis=BasisDatum(
                    datum_id=f"datum:{document.subject_id}:{proposal.semantic_target}",
                    observation_id=document.observation_id,
                    source_ref=document.source_ref,
                    source_type=document.source_type,
                    observed_at=NOW,
                    excerpt_or_summary=proposal.excerpt,
                    contribution=BasisContribution.SUPPORTS,
                    evidence_ref="evidence:acme:capability"
                    if canonical
                    else f"evidence:{document.subject_id}:{proposal.semantic_target}",
                    representation_fingerprint=document.fingerprint,
                    extraction_fingerprint=proposals.result_fingerprint,
                ),
                epistemic_state=EpistemicState.OBSERVED if canonical else EpistemicState.DECLARED,
                currentness=Currentness.CURRENT,
                rights_basis_ref=authorization.reuse_authority.provenance_ref,
                canonical_support=canonical,
                representation=proposal.supporting_representation,
            )
        )
    return tuple(observations)


@dataclass(frozen=True)
class Fixture:
    subject: EvidenceBackedEconomicState
    activity: EvidenceBackedEconomicState
    evidence: Evidence
    subject_document: DocumentRepresentation
    activity_document: DocumentRepresentation
    subject_authorization: SourceRegistryAuthorization


@pytest.fixture
def vertical(tmp_path: Path) -> Fixture:
    document, authorization = _document(tmp_path / "artifacts", "org:acme", SUBJECT_TEXT)
    activity, activity_authorization = _document(
        tmp_path / "artifacts", "org:port", ACTIVITY_TEXT, "CORPORATE_DOCUMENT"
    )
    evidence = _evidence(document)
    request = AdmissionRequest(evidence, "org:acme", "capability", "industrial pumps", CLAIM)
    decision = EvidenceAdmission.admit_claim(request)
    assert decision.is_proposition_bound
    support = FAXT.create(
        faxt_id=FaxtId("faxt:acme:capability"),
        subject_id=request.subject_id,
        predicate=request.predicate,
        object_or_value=request.object_or_value,
        evidence=evidence,
        decision=decision,
        currentness=Currentness.CURRENT,
    )
    return Fixture(
        _state("org:acme", _observations(document, authorization, SUBJECT_FIELDS, support)),
        _state("org:port", _observations(activity, activity_authorization, ACTIVITY_FIELDS)),
        evidence,
        document,
        activity,
        authorization,
    )


class DeterministicEvaluator:
    capability_profile = EvaluatorCapabilityProfile(
        "eb04-adversarial-choice",
        "1",
        DistributionCapability.NEVER,
        ConfidenceCapability.NEVER,
        True,
    )

    def __init__(self, *, failure: bool = False) -> None:
        self.failure = failure
        self.requests: list[EconomicEvaluationRequest] = []

    def evaluate(self, request: StructuredEvaluationRequest) -> StructuredJudgment:
        assert isinstance(request, EconomicEvaluationRequest)
        self.requests.append(request)
        if self.failure:
            raise TimeoutError("SECRET diagnostic that must not reach Human Output")
        return StructuredJudgment(
            "YES",
            "synthetic-deterministic-evaluator",
            "1",
            request.decision_contract_id,
            request.state_fingerprint,
            request.question_fingerprint,
            request.choice_space_fingerprint,
            self.capability_profile,
            DistributionAvailability.UNAVAILABLE,
            ConfidenceSemantics.UNAVAILABLE,
            f"synthetic-replay:{request.decision_contract_id}:{request.state_fingerprint}",
        )


def _run(vertical, evaluator=None):
    return run_economic_vertical(
        subject=vertical.subject,
        activity=vertical.activity,
        evaluator=evaluator or DeterministicEvaluator(),
        as_of=NOW,
        temporal_policy=TEMPORAL,
    )


def test_exact_span_identity_admission_and_independent_need_to_human_output(vertical, monkeypatch):
    capability = vertical.subject.get("capability")
    assert capability.canonical_support.evidence_refs == (vertical.evidence.id,)
    grounding = vertical.evidence.grounded_claim
    assert grounding.subject_binding.is_governed
    assert not grounding.subject_binding.is_canonical_truth
    assert grounding.supporting_span.extract(vertical.evidence.representation) == CLAIM
    assert "ACME" not in vertical.activity_document.visible_text
    assert all(item.canonical_support is None for item in vertical.activity.observations)
    before = (vertical.subject, vertical.activity, capability.canonical_support)

    def forbidden_write(*args, **kwargs):
        pytest.fail("economic judgment or presentation attempted canonical admission/write")

    monkeypatch.setattr(EvidenceAdmission, "admit_claim", forbidden_write)
    monkeypatch.setattr(FAXT, "create", forbidden_write)
    monkeypatch.setattr(ObservedRelationship, "create", forbidden_write)
    result = _run(vertical)
    wire = compile_economic_human_output(result, as_of=NOW).to_wire()
    assert wire["epistemic_state"] == "POTENTIAL"
    assert wire["attention"] == "WARRANTED_ATTENTION"
    assert before == (vertical.subject, vertical.activity, capability.canonical_support)
    assert {axis.dimension_id: axis.selected_option for axis in result.vector.evaluations}[
        "supplier_role"
    ] == "YES"
    assert (
        next(
            axis for axis in result.vector.evaluations if axis.dimension_id == "customer_role"
        ).selected_option
        == "YES"
    )
    by_evidence = {
        item.basis.evidence_ref: item for item in (*before[0].observations, *before[1].observations)
    }
    for item in wire["evidence"]:
        observation = by_evidence[item["evidence_ref"]]
        assert item["excerpt"] == observation.datum.supporting_span.extract(
            observation.representation
        )
        assert item["source_ref"] == observation.representation.source_ref
        assert item["representation_fingerprint"] == observation.representation.document_fingerprint
        assert item["rights_basis_ref"] == observation.rights_basis_ref
    for axis in wire["dimensions"]:
        basis = next(item for item in result.dimension_bases if item.basis_id == axis["basis_ref"])
        assert axis["evidence_refs"] == tuple(item.evidence_ref for item in basis.data)
    assert wire["basis_ref"] == result.basis.basis_id
    assert _run(vertical) == result
    assert compile_economic_human_output(_run(vertical), as_of=NOW).to_wire() == wire


@pytest.mark.parametrize("field", ["reach_region", "delivery_mode", "certification"])
def test_missing_subject_context_abstains_without_false_or_zero(vertical, field):
    subject = _state(
        "org:acme",
        tuple(item for item in vertical.subject.observations if item.datum.name != field),
    )
    result = _run(replace(vertical, subject=subject))
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE
    wire = compile_economic_human_output(result, as_of=NOW).to_wire()
    assert any(
        axis["value"] is None and f"MISSING:subject.{field}" in axis["reason"]
        for axis in wire["dimensions"]
    )


@pytest.mark.parametrize("field", ["action_until", "required_certification", "region"])
def test_missing_activity_context_abstains(vertical, field):
    activity = _state(
        "org:port",
        tuple(item for item in vertical.activity.observations if item.datum.name != field),
    )
    result = _run(replace(vertical, activity=activity))
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE


def test_outage_retains_evidence_and_suppresses_untrusted_diagnostic(vertical):
    evaluator = DeterministicEvaluator(failure=True)
    result = _run(vertical, evaluator)
    wire = compile_economic_human_output(result, as_of=NOW).to_wire()
    assert len(evaluator.requests) == 3 and result.raw_judgments == ()
    assert wire["epistemic_state"] == "UNKNOWN" and wire["attention"] == "INVESTIGATE"
    assert len(wire["evidence"]) == 12
    assert "SECRET" not in json.dumps(wire)


def test_homonym_binding_fails_closed_in_both_candidate_orders(vertical):
    representation = vertical.subject_document.text_representation()
    candidates = (ResolutionCandidate("org:acme", "ACME"), ResolutionCandidate("org:other", "ACME"))
    for ordered in (candidates, tuple(reversed(candidates))):
        resolver = ExactNameResolver(ordered)
        assert resolver.resolve_identity("ACME").status is ResolutionStatus.AMBIGUOUS
        with pytest.raises(ValueError):
            resolver.bind_mention(
                representation=representation,
                mention_span=representation.unique_span("ACME"),
                decision_id="identity:ambiguous",
                evidence_refs=("synthetic-registry:homonyms",),
                authority=IdentityBindingAuthority.DETERMINISTIC_POLICY,
                decided_by="synthetic-control-plane",
                decided_at=NOW,
                as_of=NOW,
            )
    # A parser cannot replace missing governed binding with a guessed organization ID.
    evidence = replace(
        vertical.evidence,
        grounded_claim=replace(vertical.evidence.grounded_claim, subject_binding=None),
    )
    request = AdmissionRequest(evidence, "org:acme", "capability", "industrial pumps", CLAIM)
    assert not EvidenceAdmission.admit_claim(request).admitted
    with pytest.raises(EvidenceAdmissionRequired):
        EvidenceAdmission.require_claim(EvidenceAdmission.admit_claim(request), request)


def test_ambiguous_repeated_semantic_support_never_selects_first(tmp_path):
    document, _ = _document(tmp_path / "artifacts", "org:ambiguous", f"{CLAIM} {CLAIM}")
    contract = SemanticExtractionContract(
        "ambiguous-support", "1", (SemanticTarget("capability", "Economic capability"),)
    )
    with pytest.raises(ValueError, match="ambiguous"):
        normalize_semantic_extraction_payload(
            request=build_semantic_extraction_request(document, contract),
            provider="synthetic-proposer",
            payload={
                "provider_version": "1",
                "candidates": [
                    {
                        "semantic_target": "capability",
                        "statement": CLAIM,
                        "excerpt": CLAIM,
                        "grounding_surface": "VISIBLE_TEXT",
                    }
                ],
            },
            representation=document,
            contract=contract,
        )


@pytest.mark.parametrize(
    "rights", [ObservationRightsStatus.UNKNOWN, ObservationRightsStatus.PROHIBITED]
)
def test_registry_denies_unauthorized_rights_before_payload(rights):
    with pytest.raises(SourceRegistryRejected):
        _authorize(replace(_entry("org:acme"), rights_status=rights))


def test_registry_policy_change_changes_economic_input_lineage(vertical):
    changed_authority = _authorize(replace(_entry("org:acme"), version="2")).reuse_authority
    changed = _state(
        "org:acme",
        tuple(
            replace(item, rights_basis_ref=changed_authority.provenance_ref)
            for item in vertical.subject.observations
        ),
    )
    assert changed.fingerprint != vertical.subject.fingerprint
    assert (
        _run(replace(vertical, subject=changed)).candidate.fingerprint
        != _run(vertical).candidate.fingerprint
    )
    authority = vertical.subject_authorization.reuse_authority
    assert authority.scope is ObservationReuseScope.GLOBAL_PUBLIC
    assert authority.authority_version == "1"
    assert (
        authority.retention_policy_ref and authority.rate_policy_ref and authority.robots_policy_ref
    )


def test_unknown_cost_preserves_lower_bound_and_reservation_counters():
    controller = GovernedExecutionController(
        ExecutionBudgetPolicy(
            "eb04-budget",
            "1",
            currency="USD",
            max_amount_microunits=100,
            max_requests=4,
            max_sources=2,
            max_loops=3,
        ),
        ExecutionBudgetState(amount_microunits=7, currency="USD"),
    )
    for reservation_id, delta in (
        ("unknown", ExecutionBudgetDelta(requests=1, sources=1, elapsed_ms=17)),
        (
            "known",
            ExecutionBudgetDelta(amount_microunits=1, currency="USD", requests=1, elapsed_ms=11),
        ),
    ):
        controller.reserve(ExecutionBudgetReservation(reservation_id, requests=1, loops=1))
        controller.reconcile(reservation_id, delta)
    assert controller.state.amount_microunits == 8 and controller.state.cost_complete is False
    assert (
        controller.state.requests,
        controller.state.sources,
        controller.state.loops,
        controller.state.elapsed_ms,
    ) == (2, 1, 2, 28)
    assert controller.active_reservation_ids == ()
    controller.policy = replace(controller.policy, stop_on_unknown_cost=True)
    with pytest.raises(ExecutionReservationRejected) as rejected:
        controller.reserve(ExecutionBudgetReservation("forbidden", requests=1))
    assert rejected.value.decision.stop_reason is ExecutionStopReason.COST_UNKNOWN


def test_material_supplier_contradiction_blocks_positive_attention(vertical, tmp_path):
    document, authorization = _document(
        tmp_path / "dispute", "org:acme", "ACME has suspended all pump supply."
    )
    contradiction = _observations(
        document, authorization, {"supply_dispute": "suspended all pump supply"}
    )[0]
    contradiction = replace(
        contradiction,
        basis=replace(contradiction.basis, contribution=BasisContribution.CONTRADICTS),
        contradicts_fields=("supply_activity",),
    )
    subject = _state("org:acme", (*vertical.subject.observations, contradiction))
    result = _run(replace(vertical, subject=subject))
    supplier = next(
        axis for axis in result.vector.evaluations if axis.dimension_id == "supplier_role"
    )
    assert supplier.disposition is DimensionDisposition.NOT_ANSWERABLE
    assert result.interpretation.epistemic_state is XignalEpistemicState.UNKNOWN, (
        "EB04-P0-2: material supplier contradiction must block POTENTIAL"
    )
    assert result.interpretation.attention is AttentionDisposition.INVESTIGATE


def test_human_output_rejects_invented_basis_summary(vertical):
    observation = vertical.activity.get("event")
    invented = "ACME has signed a supply contract with PORT."
    assert invented not in observation.representation.text
    with pytest.raises(ValueError):
        replace(
            observation,
            basis=replace(
                observation.basis, excerpt_or_summary=f"{observation.datum.value}. {invented}"
            ),
        )


def test_material_declared_input_requires_verifiable_span(vertical):
    observation = vertical.activity.get("required_capability")
    with pytest.raises(ValueError):
        replace(
            observation, datum=replace(observation.datum, supporting_span=None), representation=None
        )


def test_provider_dispatch_requires_prior_governed_reservation(vertical, monkeypatch):
    # Simulated externally costly port, with no actual billing/network. Observe
    # any use of the existing reservation API; do not invent a budget argument.
    events = []
    original = GovernedExecutionController.reserve

    def reserve(controller, reservation):
        result = original(controller, reservation)
        events.append(("reserved", reservation.reservation_id))
        return result

    class MeteredEvaluator(DeterministicEvaluator):
        def evaluate(self, request):
            events.append(("dispatch", request.decision_contract_id))
            return super().evaluate(request)

    monkeypatch.setattr(GovernedExecutionController, "reserve", reserve)
    controller = GovernedExecutionController(
        ExecutionBudgetPolicy(
            "eb04-provider-dispatch",
            "1",
            max_requests=3,
            max_loops=3,
            max_elapsed_ms=10_000,
        )
    )
    recorder = GovernedDispatchRecorder(controller)
    result = _run(
        vertical,
        GovernedStructuredEvaluator(MeteredEvaluator(), recorder),
    )
    dispatched = [index for index, event in enumerate(events) if event[0] == "dispatch"]
    assert len(dispatched) == 3
    assert sum(event[0] == "reserved" for event in events) == len(dispatched)
    assert events[0][0] == "reserved"
    assert controller.active_reservation_ids == ()
    assert result.interpretation.epistemic_state is XignalEpistemicState.POTENTIAL
