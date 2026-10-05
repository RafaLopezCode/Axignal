"""EB-04 composition from governed source authorization to Human-First output.

This module composes existing AXIGNAL boundaries. It does not create a new truth
authority, source store, evaluator abstraction or graph. Canonical admission is
optional per field and occurs only before economic reasoning.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.economic_discovery.contracts import StructuredEvaluatorPort
from application.economic_discovery.economic_state import (
    EconomicObservation,
    EvidenceBackedEconomicState,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetState,
    GovernedExecutionController,
)
from application.economic_discovery.explanation import BasisContribution, BasisDatum
from application.economic_discovery.first_vertical import (
    EconomicReasoningResult,
    run_economic_vertical,
)
from application.economic_discovery.governed_dispatch import (
    ExecutionAttemptRecord,
    GovernedDispatchRecorder,
    GovernedSemanticExtractor,
    GovernedSourceAcquirer,
    GovernedStructuredEvaluator,
)
from application.economic_discovery.prime_execution import (
    SemanticExtractionPort,
    SourceAcquisitionPort,
    SourceRepresentationPort,
)
from application.economic_discovery.source_registry import SourceRegistryAuthorization
from application.semantic_extraction import (
    EconomicClaimCandidate,
    SemanticCandidateSet,
    SemanticExtractionContract,
)
from application.source_representation import (
    RichStateDatum,
    compile_rich_subject_state,
)
from application.subscriber_projection.economic_output import (
    EconomicHumanOutput,
    compile_economic_human_output,
)
from domain.evidence.admission import (
    AdmissionRequest,
    Evidence,
    EvidenceAdmission,
    GroundedClaim,
    SourceAuthority,
)
from domain.evidence.epistemics import Currentness, EpistemicState
from domain.faxt.model import FAXT
from domain.identity import FaxtId
from domain.identity_binding import GovernedIdentityBinding
from domain.representation import RepresentationSpan, TextRepresentation

_E2E_VERSION = "economic-first-vertical-e2e:v1"


class SubjectIdentityBindingPort(Protocol):
    """Bind one exact source mention to an already governed canonical identity."""

    def bind(
        self,
        *,
        subject_id: str,
        mention: str,
        support: RepresentationSpan,
        representation: TextRepresentation,
    ) -> GovernedIdentityBinding: ...


@dataclass(frozen=True, slots=True)
class EconomicFieldSpec:
    semantic_target: str
    field_name: str
    canonical_authority: SourceAuthority | None = None
    predicate_mention: str | None = None
    contribution: BasisContribution = BasisContribution.SUPPORTS
    contradicts_fields: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value in (self.semantic_target, self.field_name):
            if not value.strip():
                raise ValueError("economic field spec identity cannot be empty")
        if self.canonical_authority is not None:
            if self.predicate_mention is None or not self.predicate_mention.strip():
                raise ValueError("canonical economic field requires exact predicate mention")
        elif self.predicate_mention is not None:
            raise ValueError("non-canonical field must not imply canonical predicate grounding")
        if self.contribution is BasisContribution.CONTRADICTS and not self.contradicts_fields:
            raise ValueError("contradicting field requires explicit affected fields")


@dataclass(frozen=True, slots=True)
class FirstVerticalSourcePlan:
    authorization: SourceRegistryAuthorization
    extraction_contract: SemanticExtractionContract
    subject_mention: str
    fields: tuple[EconomicFieldSpec, ...]

    def __post_init__(self) -> None:
        if not self.subject_mention.strip():
            raise ValueError("source plan requires exact subject mention")
        if not self.fields:
            raise ValueError("source plan requires at least one economic field")
        targets = [item.semantic_target for item in self.fields]
        names = [item.field_name for item in self.fields]
        if len(targets) != len(set(targets)) or len(names) != len(set(names)):
            raise ValueError("source plan fields require unique targets and names")
        if not set(targets).issubset(self.extraction_contract.target_ids):
            raise ValueError("source plan field target is absent from extraction contract")


@dataclass(frozen=True, slots=True)
class MaterializedEconomicSource:
    authorization: SourceRegistryAuthorization
    candidates: SemanticCandidateSet
    state: EvidenceBackedEconomicState


@dataclass(frozen=True, slots=True)
class FirstEconomicVerticalE2EResult:
    subject_source: MaterializedEconomicSource
    activity_source: MaterializedEconomicSource
    reasoning: EconomicReasoningResult
    human_output: EconomicHumanOutput
    execution_state: ExecutionBudgetState
    attempts: tuple[ExecutionAttemptRecord, ...]
    replay_refs: tuple[str, ...]
    pipeline_version: str = _E2E_VERSION


def _faxt_id(candidate: EconomicClaimCandidate, field: EconomicFieldSpec) -> FaxtId:
    digest = hashlib.sha256(
        f"{candidate.candidate_id}|{field.field_name}|{candidate.statement}".encode()
    ).hexdigest()
    return FaxtId(f"faxt:eb04:{digest[:32]}")


def _canonical_support(
    *,
    candidate: EconomicClaimCandidate,
    field: EconomicFieldSpec,
    subject_mention: str,
    binding_port: SubjectIdentityBindingPort,
    currentness: Currentness,
) -> FAXT:
    if field.canonical_authority is None or field.predicate_mention is None:
        raise ValueError("canonical support requires explicit authority and predicate mention")
    if candidate.statement not in candidate.excerpt:
        raise ValueError("canonical candidate value must be literally present in support")
    if field.predicate_mention not in candidate.excerpt:
        raise ValueError("canonical predicate mention must be literally present in support")
    if subject_mention not in candidate.excerpt:
        raise ValueError("canonical subject mention must be literally present in support")

    binding = binding_port.bind(
        subject_id=candidate.subject_id,
        mention=subject_mention,
        support=candidate.supporting_span,
        representation=candidate.supporting_representation,
    )
    evidence = Evidence(
        id=f"evidence:{candidate.candidate_id}",
        source=candidate.source_ref,
        source_type=candidate.source_type,
        reference=candidate.source_ref,
        extracted_claim=candidate.excerpt,
        observed_at=candidate.observed_at,
        authority=field.canonical_authority,
        observation_subject_id=candidate.subject_id,
        grounded_claim=GroundedClaim(
            subject_id=candidate.subject_id,
            predicate=field.field_name,
            object_or_value=candidate.statement,
            subject_mention=subject_mention,
            predicate_mention=field.predicate_mention,
            object_mention=candidate.statement,
            supporting_excerpt=candidate.excerpt,
            supporting_span=candidate.supporting_span,
            subject_binding=binding,
        ),
        representation=candidate.supporting_representation,
    )
    decision = EvidenceAdmission.admit_claim(
        AdmissionRequest(
            evidence=evidence,
            subject_id=candidate.subject_id,
            predicate=field.field_name,
            object_or_value=candidate.statement,
            claim_proposition=candidate.excerpt,
        )
    )
    if not decision.admitted:
        raise ValueError(f"canonical economic input was not admitted: {decision.reason}")
    return FAXT.create(
        faxt_id=_faxt_id(candidate, field),
        subject_id=candidate.subject_id,
        predicate=field.field_name,
        object_or_value=candidate.statement,
        evidence=evidence,
        decision=decision,
        currentness=currentness,
    )


def _candidate_by_target(
    candidates: SemanticCandidateSet,
    target: str,
) -> EconomicClaimCandidate | None:
    matches = tuple(item for item in candidates.candidates if item.semantic_target == target)
    if len(matches) > 1:
        raise ValueError(f"ambiguous semantic target requires explicit resolution: {target}")
    return matches[0] if matches else None


def _materialize_source(
    *,
    plan: FirstVerticalSourcePlan,
    source_acquirer: SourceAcquisitionPort,
    representation_port: SourceRepresentationPort,
    semantic_extractor: SemanticExtractionPort,
    binding_port: SubjectIdentityBindingPort,
) -> MaterializedEconomicSource:
    authorization = plan.authorization
    observation = source_acquirer.observe(
        authorization.request,
        authorization.dispatch_policy,
    )
    if observation.failure_state is not None:
        raise ValueError(f"economic source acquisition failed: {observation.failure_state}")
    representation = representation_port.represent(
        request=authorization.request,
        observation=observation,
    )
    candidates = semantic_extractor.extract(
        representation=representation,
        contract=plan.extraction_contract,
    )
    if candidates.subject_id != authorization.request.subject_id:
        raise ValueError("semantic extraction subject does not match authorized source")
    if candidates.representation_id != representation.representation_id:
        raise ValueError("semantic extraction representation does not match source")
    rights_ref = authorization.reuse_authority.provenance_ref
    if rights_ref is None:
        raise ValueError("economic source lacks explicit reuse-rights provenance")

    observations: list[EconomicObservation] = []
    for field_spec in plan.fields:
        candidate = _candidate_by_target(candidates, field_spec.semantic_target)
        if candidate is None:
            continue
        if candidate.statement not in candidate.excerpt:
            raise ValueError("economic candidate value must be literally grounded in excerpt")

        excerpt_text = candidate.supporting_span.extract(candidate.supporting_representation)
        relative_value = excerpt_text.find(candidate.statement)
        if relative_value < 0 or excerpt_text.find(candidate.statement, relative_value + 1) >= 0:
            raise ValueError("economic candidate value requires one exact span inside support")
        value_span = candidate.supporting_representation.span(
            candidate.supporting_span.start + relative_value,
            candidate.supporting_span.start + relative_value + len(candidate.statement),
        )

        evidence_ref = f"evidence:{candidate.candidate_id}"
        support = None
        epistemic_state = EpistemicState.DECLARED
        if field_spec.canonical_authority is not None:
            support = _canonical_support(
                candidate=candidate,
                field=field_spec,
                subject_mention=plan.subject_mention,
                binding_port=binding_port,
                currentness=authorization.reuse_authority.currentness,
            )
            epistemic_state = EpistemicState.OBSERVED

        observations.append(
            EconomicObservation(
                datum=RichStateDatum(
                    name=field_spec.field_name,
                    value=candidate.statement,
                    observation_id=candidate.observation_id,
                    representation_id=candidate.supporting_representation.representation_id,
                    source_ref=candidate.source_ref,
                    observed_at=candidate.observed_at,
                    supporting_span=value_span,
                ),
                basis=BasisDatum(
                    datum_id=f"datum:{candidate.candidate_id}:{field_spec.field_name}",
                    observation_id=candidate.observation_id,
                    source_ref=candidate.source_ref,
                    source_type=candidate.source_type,
                    observed_at=candidate.observed_at,
                    excerpt_or_summary=candidate.excerpt,
                    contribution=field_spec.contribution,
                    evidence_ref=evidence_ref,
                    representation_fingerprint=candidate.supporting_representation.document_fingerprint,
                    extraction_fingerprint=candidate.result_fingerprint,
                ),
                epistemic_state=epistemic_state,
                currentness=authorization.reuse_authority.currentness,
                rights_basis_ref=rights_ref,
                canonical_support=support,
                contradicts_fields=field_spec.contradicts_fields,
                representation=candidate.supporting_representation,
            )
        )

    state = compile_rich_subject_state(
        subject_id=authorization.request.subject_id,
        contributions=tuple(item.datum for item in observations),
    )
    return MaterializedEconomicSource(
        authorization=authorization,
        candidates=candidates,
        state=EvidenceBackedEconomicState(state=state, observations=tuple(observations)),
    )


def run_first_economic_vertical_e2e(
    *,
    subject_plan: FirstVerticalSourcePlan,
    activity_plan: FirstVerticalSourcePlan,
    source_acquirer: SourceAcquisitionPort,
    representation_port: SourceRepresentationPort,
    semantic_extractor: SemanticExtractionPort,
    binding_port: SubjectIdentityBindingPort,
    evaluator: StructuredEvaluatorPort,
    execution_controller: GovernedExecutionController,
    as_of: datetime,
) -> FirstEconomicVerticalE2EResult:
    """Run the governed EB-04 reference chain without provider-specific authority."""

    if as_of.tzinfo is None:
        raise ValueError("EB-04 evaluation time must be timezone-aware")
    if (
        subject_plan.authorization.request.subject_id
        == activity_plan.authorization.request.subject_id
    ):
        raise ValueError("EB-04 requires independent organization/activity subjects")

    if execution_controller.active_reservation_ids:
        raise ValueError("EB-04 execution controller must start without active reservations")

    recorder = GovernedDispatchRecorder(execution_controller)
    budgeted_source = GovernedSourceAcquirer(source_acquirer, recorder)
    budgeted_semantic = GovernedSemanticExtractor(semantic_extractor, recorder)
    budgeted_evaluator = GovernedStructuredEvaluator(evaluator, recorder)

    subject_source = _materialize_source(
        plan=subject_plan,
        source_acquirer=budgeted_source,
        representation_port=representation_port,
        semantic_extractor=budgeted_semantic,
        binding_port=binding_port,
    )
    activity_source = _materialize_source(
        plan=activity_plan,
        source_acquirer=budgeted_source,
        representation_port=representation_port,
        semantic_extractor=budgeted_semantic,
        binding_port=binding_port,
    )
    temporal_policy = subject_plan.authorization.temporal_policy
    if activity_plan.authorization.temporal_policy != temporal_policy:
        raise ValueError("EB-04 source temporal policies must be identical for one evaluation")

    reasoning = run_economic_vertical(
        subject=subject_source.state,
        activity=activity_source.state,
        evaluator=budgeted_evaluator,
        as_of=as_of,
        temporal_policy=temporal_policy,
    )
    human_output = compile_economic_human_output(reasoning, as_of=as_of)
    replay_refs = (
        f"source:{subject_source.authorization.source_id}@{subject_source.authorization.source_version}:"
        f"{subject_source.authorization.source_fingerprint}",
        f"semantic:{subject_source.candidates.result_fingerprint}",
        f"source:{activity_source.authorization.source_id}@{activity_source.authorization.source_version}:"
        f"{activity_source.authorization.source_fingerprint}",
        f"semantic:{activity_source.candidates.result_fingerprint}",
        *(item.replay_reference for item in reasoning.raw_judgments),
    )
    return FirstEconomicVerticalE2EResult(
        subject_source=subject_source,
        activity_source=activity_source,
        reasoning=reasoning,
        human_output=human_output,
        execution_state=execution_controller.state,
        attempts=tuple(recorder.records),
        replay_refs=replay_refs,
    )
