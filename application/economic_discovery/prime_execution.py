"""Application composition root for governed AXIGNAL Prime execution.

This is intentionally small. It composes existing organs; it does not redefine
their authority or create a second Brain.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from application.economic_discovery.brain_contracts import (
    DimensionDisposition,
    TypingDimensionContract,
)
from application.economic_discovery.execution_budget import (
    ExecutionBudgetDelta,
    GovernedExecutionController,
)
from application.economic_discovery.execution_learning import execution_stop_learning_event
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningMemory,
    LearningOutcome,
    LearningReplayReference,
    LearningYield,
)
from application.economic_discovery.observation_memory import ObservationMemory
from application.economic_discovery.planner import assess_dimension_work
from application.economic_discovery.prime import (
    DimensionRoutingPolicy,
    PrimeControlPlan,
    PrimeRoute,
    PrimeWorkItem,
    build_prime_control_plan,
)
from application.economic_discovery.research_value import ResearchValueDecision
from application.semantic_extraction import (
    SemanticCandidateSet,
    SemanticExtractionContract,
)
from application.source_acquisition import (
    SourceDispatchPolicy,
    SourceObservation,
    SourceRequest,
    ingest_source_observation,
    source_observation_id,
)
from application.source_representation import (
    DocumentRepresentation,
    RichSubjectState,
    compile_rich_subject_state,
    representation_state_data,
    rich_state_change,
)
from application.xeed_access.organization_reader import AuthorizedXeedOrganization


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class SourceAcquisitionPort(Protocol):
    def observe(
        self,
        request: SourceRequest,
        policy: SourceDispatchPolicy,
    ) -> SourceObservation: ...


class SourceRepresentationPort(Protocol):
    def represent(
        self,
        *,
        request: SourceRequest,
        observation: SourceObservation,
    ) -> DocumentRepresentation: ...


class SemanticExtractionPort(Protocol):
    def extract(
        self,
        *,
        representation: DocumentRepresentation,
        contract: SemanticExtractionContract,
    ) -> SemanticCandidateSet: ...


@dataclass(frozen=True, slots=True)
class PrimeMechanismResult:
    output_fingerprint: str
    made_progress: bool
    cost: LearningCost = field(default_factory=LearningCost)
    requests: int = 0
    sources: int = 0
    retries: int = 0
    state_fields_changed: int = 0
    semantic_judgments_produced: int = 0

    def __post_init__(self) -> None:
        if not self.output_fingerprint.strip():
            raise ValueError("Prime mechanism result fingerprint is required")
        for value in (
            self.requests,
            self.sources,
            self.retries,
            self.state_fields_changed,
            self.semantic_judgments_produced,
        ):
            if value < 0:
                raise ValueError("Prime mechanism result counts cannot be negative")


class PrimeMechanismExecutor(Protocol):
    def execute(
        self,
        *,
        item: PrimeWorkItem,
        state: RichSubjectState,
        semantic_candidates: SemanticCandidateSet | None,
    ) -> PrimeMechanismResult: ...


@dataclass(frozen=True, slots=True)
class PrimeExecutionPorts:
    deterministic: PrimeMechanismExecutor
    structured_evaluator: PrimeMechanismExecutor
    adaptive_research: PrimeMechanismExecutor


@dataclass(frozen=True, slots=True)
class PrimeExecutionTrace:
    trace_id: str
    subject_id: str
    xeed_id: str
    source_request_id: str
    source_observation_fingerprint: str
    source_artifact_ref: str
    representation_id: str
    representation_fingerprint: str
    rich_state_fingerprint: str
    semantic_extraction_id: str | None
    semantic_result_fingerprint: str | None
    prime_plan: PrimeControlPlan | None
    budget_stop_reason: str | None
    learning_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        required = (
            self.trace_id,
            self.subject_id,
            self.xeed_id,
            self.source_request_id,
            self.source_observation_fingerprint,
            self.source_artifact_ref,
            self.representation_id,
            self.representation_fingerprint,
            self.rich_state_fingerprint,
        )
        if any(not value.strip() for value in required):
            raise ValueError("Prime execution trace requires complete identity/provenance")


def _learning_event(
    *,
    event_id: str,
    kind: LearningEventKind,
    outcome: LearningOutcome,
    occurred_at: datetime,
    subject_id: str,
    xeed_id: str,
    activity_ref: str,
    policy_id: str,
    policy_version: str,
    code_sha: str,
    mechanism: LearningMechanism,
    input_fingerprint: str,
    output_fingerprint: str | None,
    reason_code: str,
    before_state_fingerprint: str | None,
    after_state_fingerprint: str | None,
    cost: LearningCost,
    yield_: LearningYield,
    replay: LearningReplayReference | None = None,
) -> LearningEvent:
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=outcome,
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref=activity_ref,
        policy_id=policy_id,
        policy_version=policy_version,
        code_sha=code_sha,
        mechanism=mechanism,
        input_fingerprint=input_fingerprint,
        output_fingerprint=output_fingerprint,
        reason_code=reason_code,
        before_state_fingerprint=before_state_fingerprint,
        after_state_fingerprint=after_state_fingerprint,
        replay=(
            LearningReplayReference.non_replayable("EXACT_REPLAY_INPUTS_UNAVAILABLE")
            if replay is None
            else replay
        ),
        cost=cost,
        yield_=yield_,
    )


def _answerable_dimensions(
    *,
    contracts: tuple[TypingDimensionContract, ...],
    available_state_fields: frozenset[str],
) -> frozenset[str]:
    return frozenset(
        item.dimension_id
        for item in assess_dimension_work(
            contracts=contracts,
            available_state_fields=available_state_fields,
        )
        if item.disposition is DimensionDisposition.ANSWERABLE
    )


def _executor_for(
    route: PrimeRoute,
    ports: PrimeExecutionPorts,
) -> PrimeMechanismExecutor:
    if route is PrimeRoute.DETERMINISTIC:
        return ports.deterministic
    if route is PrimeRoute.STRUCTURED_EVALUATOR:
        return ports.structured_evaluator
    return ports.adaptive_research


def execute_prime_source_slice(
    *,
    execution_id: str,
    seed: AuthorizedXeedOrganization,
    code_sha: str,
    occurred_at: datetime,
    observation_memory: ObservationMemory,
    learning_memory: LearningMemory,
    request: SourceRequest,
    source_policy: SourceDispatchPolicy,
    source_acquirer: SourceAcquisitionPort,
    representation_port: SourceRepresentationPort,
    prior_rich_state: RichSubjectState,
    contracts: tuple[TypingDimensionContract, ...],
    routing_policies: tuple[DimensionRoutingPolicy, ...],
    research_decisions: tuple[ResearchValueDecision, ...],
    execution_controller: GovernedExecutionController,
    ports: PrimeExecutionPorts,
    semantic_extractor: SemanticExtractionPort | None = None,
    semantic_contract: SemanticExtractionContract | None = None,
) -> PrimeExecutionTrace:
    """Execute one governed source-to-Prime slice and retain exact lineage."""

    if not execution_id.strip():
        raise ValueError("Prime execution identity is required")
    if not isinstance(seed, AuthorizedXeedOrganization):
        raise TypeError("Prime execution requires AuthorizedXeedOrganization")
    xeed_id = seed.authorized_xeed.xeed.id
    subject_id = seed.organization.id
    if request.subject_id != subject_id:
        raise ValueError("Prime execution request does not match canonical subject")
    if (
        request.policy_id != source_policy.policy_id
        or request.policy_fingerprint != source_policy.fingerprint
    ):
        raise ValueError("Prime execution source policy mismatch")

    source_event_id = f"learn:{execution_id}:01-source:{request.request_id}"
    try:
        observation = source_acquirer.observe(request, source_policy)
        if observation.subject_id != subject_id:
            raise ValueError("Prime execution cannot cross canonical subjects")
    except Exception as exc:
        learning_memory.append(
            _learning_event(
                event_id=source_event_id,
                kind=LearningEventKind.SOURCE_ACQUISITION,
                outcome=LearningOutcome.FAILED,
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=request.request_id,
                policy_id=request.policy_id,
                policy_version=request.policy_fingerprint,
                code_sha=code_sha,
                mechanism=LearningMechanism.DETERMINISTIC,
                input_fingerprint=request.policy_fingerprint,
                output_fingerprint=None,
                reason_code=f"SOURCE_ACQUISITION_FAILED:{type(exc).__name__}",
                before_state_fingerprint=None,
                after_state_fingerprint=None,
                cost=LearningCost(),
                yield_=LearningYield(),
            )
        )
        raise

    source_event = _learning_event(
        event_id=source_event_id,
        kind=LearningEventKind.SOURCE_ACQUISITION,
        outcome=LearningOutcome.COMPLETED,
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref=observation.raw_observation_ref,
        policy_id=request.policy_id,
        policy_version=request.policy_fingerprint,
        code_sha=code_sha,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=request.policy_fingerprint,
        output_fingerprint=observation.observation_fingerprint,
        reason_code="SOURCE_ACQUIRED",
        before_state_fingerprint=None,
        after_state_fingerprint=None,
        cost=LearningCost(),
        yield_=LearningYield(),
        replay=LearningReplayReference.replayable(
            artifact_ref=observation.raw_observation_ref,
            code_sha=code_sha,
            observation_fingerprint=observation.observation_fingerprint,
            source_policy_id=request.policy_id,
            source_policy_fingerprint=request.policy_fingerprint,
        ),
    )
    learning_memory.append(source_event)

    ingestion_event_id = (
        f"learn:{execution_id}:02-ingestion:{source_observation_id(request, observation)}"
    )
    try:
        source_result = ingest_source_observation(
            memory=observation_memory,
            request=request,
            observation=observation,
            contracts=contracts,
        )
    except Exception as exc:
        learning_memory.append(
            _learning_event(
                event_id=ingestion_event_id,
                kind=LearningEventKind.OBSERVATION_INGESTION,
                outcome=LearningOutcome.FAILED,
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=source_observation_id(request, observation),
                policy_id=request.policy_id,
                policy_version=request.policy_fingerprint,
                code_sha=code_sha,
                mechanism=LearningMechanism.DETERMINISTIC,
                input_fingerprint=observation.observation_fingerprint,
                output_fingerprint=None,
                reason_code=f"OBSERVATION_INGESTION_FAILED:{type(exc).__name__}",
                before_state_fingerprint=None,
                after_state_fingerprint=None,
                cost=LearningCost(),
                yield_=LearningYield(),
            )
        )
        raise

    ingestion_event = _learning_event(
        event_id=ingestion_event_id,
        kind=LearningEventKind.OBSERVATION_INGESTION,
        outcome=(
            LearningOutcome.NO_CHANGE
            if source_result.mutation.change is None
            else LearningOutcome.COMPLETED
        ),
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref=source_observation_id(request, observation),
        policy_id=request.policy_id,
        policy_version=request.policy_fingerprint,
        code_sha=code_sha,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=observation.observation_fingerprint,
        output_fingerprint=source_result.mutation.current_state.fingerprint,
        reason_code=(
            "OBSERVATION_REPLAY_NO_CHANGE"
            if source_result.mutation.change is None
            else "OBSERVATION_INGESTED"
        ),
        before_state_fingerprint=source_result.mutation.previous_state.fingerprint,
        after_state_fingerprint=source_result.mutation.current_state.fingerprint,
        cost=LearningCost(),
        yield_=LearningYield(
            observations_added=1 if source_result.mutation.inserted else 0,
            state_fields_changed=(
                0
                if source_result.mutation.change is None
                else len(source_result.mutation.change.changed_fields)
            ),
        ),
        replay=LearningReplayReference.replayable(
            artifact_ref=observation.raw_observation_ref,
            code_sha=code_sha,
            observation_id=source_observation_id(request, observation),
            observation_fingerprint=observation.observation_fingerprint,
            source_policy_id=request.policy_id,
            source_policy_fingerprint=request.policy_fingerprint,
        ),
    )
    learning_memory.append(ingestion_event)

    try:
        representation = representation_port.represent(
            request=request,
            observation=observation,
        )
        if representation.subject_id != subject_id:
            raise ValueError("representation subject does not match Prime execution subject")
        if representation.observation_id != source_observation_id(request, observation):
            raise ValueError("representation is not bound to the acquired observation")
        if representation.source_observation_fingerprint != observation.observation_fingerprint:
            raise ValueError("representation observation fingerprint mismatch")
        if observation.body_fingerprint is not None and (
            representation.source_content_fingerprint != observation.body_fingerprint
        ):
            raise ValueError("representation content fingerprint mismatch")
    except Exception as exc:
        learning_memory.append(
            _learning_event(
                event_id=f"learn:{execution_id}:03-representation:failed",
                kind=LearningEventKind.REPRESENTATION,
                outcome=LearningOutcome.FAILED,
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=request.request_id,
                policy_id="document-representation",
                policy_version="unknown",
                code_sha=code_sha,
                mechanism=LearningMechanism.DETERMINISTIC,
                input_fingerprint=observation.observation_fingerprint,
                output_fingerprint=None,
                reason_code=f"REPRESENTATION_FAILED:{type(exc).__name__}",
                before_state_fingerprint=None,
                after_state_fingerprint=None,
                cost=LearningCost(),
                yield_=LearningYield(),
            )
        )
        raise

    contribution = representation_state_data(
        representation,
        observation_slot=request.observation_slot,
    )
    rich_state = compile_rich_subject_state(
        subject_id=subject_id,
        contributions=(*prior_rich_state.data, *contribution),
    )
    state_change = rich_state_change(prior_rich_state, rich_state)
    answerable_before = _answerable_dimensions(
        contracts=contracts,
        available_state_fields=prior_rich_state.available_fields,
    )
    answerable_after = _answerable_dimensions(
        contracts=contracts,
        available_state_fields=rich_state.available_fields,
    )
    dimensions_became_answerable = len(answerable_after - answerable_before)

    representation_event_id = (
        f"learn:{execution_id}:03-representation:{representation.representation_id}"
    )
    representation_event = _learning_event(
        event_id=representation_event_id,
        kind=LearningEventKind.REPRESENTATION,
        outcome=(LearningOutcome.NO_CHANGE if state_change is None else LearningOutcome.COMPLETED),
        occurred_at=occurred_at,
        subject_id=subject_id,
        xeed_id=xeed_id,
        activity_ref=representation.representation_id,
        policy_id="document-representation",
        policy_version=representation.representation_version,
        code_sha=code_sha,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint=representation.source_observation_fingerprint,
        output_fingerprint=representation.fingerprint,
        reason_code=("RICH_STATE_UNCHANGED" if state_change is None else "RICH_STATE_UPDATED"),
        before_state_fingerprint=prior_rich_state.fingerprint,
        after_state_fingerprint=rich_state.fingerprint,
        cost=LearningCost(),
        yield_=LearningYield(
            state_fields_changed=0 if state_change is None else len(state_change.changed_fields),
            dimensions_became_answerable=dimensions_became_answerable,
        ),
        replay=LearningReplayReference.replayable(
            code_sha=code_sha,
            normalization_version=representation.normalization_version,
            representation_artifact_ref=representation.artifact_ref,
            representation_id=representation.representation_id,
            representation_version=representation.representation_version,
            source_artifact_ref=observation.raw_observation_ref,
            source_observation_fingerprint=observation.observation_fingerprint,
            source_policy_fingerprint=request.policy_fingerprint,
        ),
    )
    learning_memory.append(representation_event)

    candidate_set: SemanticCandidateSet | None = None
    semantic_event_id: str | None = None
    if semantic_contract is not None:
        if semantic_extractor is None:
            raise ValueError("semantic contract requires a semantic extraction port")
        try:
            candidate_set = semantic_extractor.extract(
                representation=representation,
                contract=semantic_contract,
            )
            if (
                candidate_set.subject_id != subject_id
                or candidate_set.representation_id != representation.representation_id
                or candidate_set.contract_fingerprint != semantic_contract.fingerprint
            ):
                raise ValueError("semantic extraction result does not match governed execution")
        except Exception as exc:
            failed_semantic_id = (
                f"learn:{execution_id}:04-semantic:failed:{representation.representation_id}"
            )
            learning_memory.append(
                _learning_event(
                    event_id=failed_semantic_id,
                    kind=LearningEventKind.SEMANTIC_EXTRACTION,
                    outcome=LearningOutcome.FAILED,
                    occurred_at=occurred_at,
                    subject_id=subject_id,
                    xeed_id=xeed_id,
                    activity_ref=representation.representation_id,
                    policy_id=semantic_contract.contract_id,
                    policy_version=semantic_contract.version,
                    code_sha=code_sha,
                    mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
                    input_fingerprint=representation.fingerprint,
                    output_fingerprint=None,
                    reason_code=f"SEMANTIC_EXTRACTION_FAILED:{type(exc).__name__}",
                    before_state_fingerprint=None,
                    after_state_fingerprint=None,
                    cost=LearningCost(),
                    yield_=LearningYield(),
                )
            )
            raise
        semantic_event_id = f"learn:{execution_id}:04-semantic:{candidate_set.extraction_id}"
        learning_memory.append(
            _learning_event(
                event_id=semantic_event_id,
                kind=LearningEventKind.SEMANTIC_EXTRACTION,
                outcome=LearningOutcome.COMPLETED,
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=candidate_set.extraction_id,
                policy_id=semantic_contract.contract_id,
                policy_version=semantic_contract.version,
                code_sha=code_sha,
                mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
                input_fingerprint=representation.fingerprint,
                output_fingerprint=candidate_set.result_fingerprint,
                reason_code="GROUNDED_CANDIDATES_NORMALIZED",
                before_state_fingerprint=None,
                after_state_fingerprint=None,
                cost=LearningCost(),
                yield_=LearningYield(
                    semantic_judgments_produced=len(candidate_set.candidates),
                ),
                replay=LearningReplayReference.non_replayable(
                    "PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE",
                    code_sha=code_sha,
                    contract_fingerprint=semantic_contract.fingerprint,
                    provider=candidate_set.provider,
                    provider_version=candidate_set.provider_version,
                    representation_artifact_ref=representation.artifact_ref,
                    representation_id=representation.representation_id,
                    representation_version=representation.representation_version,
                    result_fingerprint=candidate_set.result_fingerprint,
                ),
            )
        )

    learning_ids = [source_event_id, ingestion_event_id, representation_event_id]
    if semantic_event_id is not None:
        learning_ids.append(semantic_event_id)

    if state_change is None:
        return PrimeExecutionTrace(
            trace_id=f"prime-trace:{_fingerprint((execution_id, xeed_id, representation.fingerprint))[:32]}",
            subject_id=subject_id,
            xeed_id=xeed_id,
            source_request_id=request.request_id,
            source_observation_fingerprint=observation.observation_fingerprint,
            source_artifact_ref=observation.raw_observation_ref,
            representation_id=representation.representation_id,
            representation_fingerprint=representation.fingerprint,
            rich_state_fingerprint=rich_state.fingerprint,
            semantic_extraction_id=None if candidate_set is None else candidate_set.extraction_id,
            semantic_result_fingerprint=(
                None if candidate_set is None else candidate_set.result_fingerprint
            ),
            prime_plan=None,
            budget_stop_reason=None,
            learning_event_ids=tuple(learning_ids),
        )

    prime_plan = build_prime_control_plan(
        change=state_change,
        contracts=contracts,
        available_state_fields=rich_state.available_fields,
        routing_policies=routing_policies,
        research_decisions=research_decisions,
    )

    stop_reason: str | None = None
    for item_index, item in enumerate(prime_plan.items):
        if item.route is None:
            continue
        authorization = execution_controller.authorize_next()
        if not authorization.may_continue:
            stop_reason = authorization.stop_reason.value if authorization.stop_reason else None
            stop_event = execution_stop_learning_event(
                event_id=(
                    f"learn:{execution_id}:05-prime:{item_index:04d}:stop:"
                    f"{item.dimension_id}:{execution_controller.state.fingerprint[:16]}"
                ),
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=item.dimension_id,
                code_sha=code_sha,
                kind=(
                    LearningEventKind.ADAPTIVE_RESEARCH
                    if item.route is PrimeRoute.ADAPTIVE_RESEARCH
                    else LearningEventKind.STRUCTURED_EVALUATION
                    if item.route is PrimeRoute.STRUCTURED_EVALUATOR
                    else LearningEventKind.DETERMINISTIC_EVALUATION
                ),
                mechanism=(
                    LearningMechanism.ADAPTIVE_RESEARCH
                    if item.route is PrimeRoute.ADAPTIVE_RESEARCH
                    else LearningMechanism.STRUCTURED_EVALUATOR
                    if item.route is PrimeRoute.STRUCTURED_EVALUATOR
                    else LearningMechanism.DETERMINISTIC
                ),
                policy=execution_controller.policy,
                state=execution_controller.state,
                decision=authorization,
            )
            learning_memory.append(stop_event)
            learning_ids.append(stop_event.event_id)
            break

        executor = _executor_for(item.route, ports)
        try:
            result = executor.execute(
                item=item,
                state=rich_state,
                semantic_candidates=candidate_set,
            )
        except Exception as exc:
            failed_id = (
                f"learn:{execution_id}:05-prime:{item_index:04d}:failed:"
                f"{item.dimension_id}:{rich_state.fingerprint[:16]}"
            )
            failed_kind = (
                LearningEventKind.ADAPTIVE_RESEARCH
                if item.route is PrimeRoute.ADAPTIVE_RESEARCH
                else LearningEventKind.STRUCTURED_EVALUATION
                if item.route is PrimeRoute.STRUCTURED_EVALUATOR
                else LearningEventKind.DETERMINISTIC_EVALUATION
            )
            failed_mechanism = (
                LearningMechanism.ADAPTIVE_RESEARCH
                if item.route is PrimeRoute.ADAPTIVE_RESEARCH
                else LearningMechanism.STRUCTURED_EVALUATOR
                if item.route is PrimeRoute.STRUCTURED_EVALUATOR
                else LearningMechanism.DETERMINISTIC
            )
            learning_memory.append(
                _learning_event(
                    event_id=failed_id,
                    kind=failed_kind,
                    outcome=LearningOutcome.FAILED,
                    occurred_at=occurred_at,
                    subject_id=subject_id,
                    xeed_id=xeed_id,
                    activity_ref=item.dimension_id,
                    policy_id="prime-routing",
                    policy_version=item.policy_version,
                    code_sha=code_sha,
                    mechanism=failed_mechanism,
                    input_fingerprint=rich_state.fingerprint,
                    output_fingerprint=None,
                    reason_code=f"PRIME_EXECUTION_FAILED:{type(exc).__name__}",
                    before_state_fingerprint=None,
                    after_state_fingerprint=None,
                    cost=LearningCost(),
                    yield_=LearningYield(),
                )
            )
            raise
        execution_controller.record(
            ExecutionBudgetDelta(
                amount_microunits=result.cost.amount_microunits,
                currency=result.cost.currency,
                elapsed_ms=result.cost.latency_ms or 0,
                requests=result.requests,
                sources=result.sources,
                retries=result.retries,
                loops=1,
                made_progress=result.made_progress,
            )
        )
        kind = (
            LearningEventKind.ADAPTIVE_RESEARCH
            if item.route is PrimeRoute.ADAPTIVE_RESEARCH
            else LearningEventKind.STRUCTURED_EVALUATION
            if item.route is PrimeRoute.STRUCTURED_EVALUATOR
            else LearningEventKind.DETERMINISTIC_EVALUATION
        )
        mechanism = (
            LearningMechanism.ADAPTIVE_RESEARCH
            if item.route is PrimeRoute.ADAPTIVE_RESEARCH
            else LearningMechanism.STRUCTURED_EVALUATOR
            if item.route is PrimeRoute.STRUCTURED_EVALUATOR
            else LearningMechanism.DETERMINISTIC
        )
        event_id = (
            f"learn:{execution_id}:05-prime:{item_index:04d}:"
            f"{item.dimension_id}:{rich_state.fingerprint[:16]}"
        )
        replay = (
            LearningReplayReference.replayable(
                code_sha=code_sha,
                prime_route=item.route.value,
                routing_policy_version=item.policy_version,
                state_fingerprint=rich_state.fingerprint,
            )
            if item.route is PrimeRoute.DETERMINISTIC
            else LearningReplayReference.non_replayable(
                "PROVIDER_MODEL_OR_HARNESS_REFERENCE_UNAVAILABLE",
                code_sha=code_sha,
                prime_route=item.route.value,
                representation_artifact_ref=representation.artifact_ref,
                routing_policy_version=item.policy_version,
                state_fingerprint=rich_state.fingerprint,
            )
        )
        learning_memory.append(
            _learning_event(
                event_id=event_id,
                kind=kind,
                outcome=(
                    LearningOutcome.COMPLETED if result.made_progress else LearningOutcome.NO_CHANGE
                ),
                occurred_at=occurred_at,
                subject_id=subject_id,
                xeed_id=xeed_id,
                activity_ref=item.dimension_id,
                policy_id="prime-routing",
                policy_version=item.policy_version,
                code_sha=code_sha,
                mechanism=mechanism,
                input_fingerprint=rich_state.fingerprint,
                output_fingerprint=result.output_fingerprint,
                reason_code=(
                    "PRIME_WORK_PROGRESS" if result.made_progress else "PRIME_WORK_NO_CHANGE"
                ),
                before_state_fingerprint=None,
                after_state_fingerprint=None,
                cost=result.cost,
                replay=replay,
                yield_=LearningYield(
                    state_fields_changed=result.state_fields_changed,
                    semantic_judgments_produced=result.semantic_judgments_produced,
                    research_objectives_resolved=(
                        1
                        if item.route is PrimeRoute.ADAPTIVE_RESEARCH and result.made_progress
                        else 0
                    ),
                ),
            )
        )
        learning_ids.append(event_id)

    return PrimeExecutionTrace(
        trace_id=f"prime-trace:{_fingerprint((execution_id, xeed_id, representation.fingerprint, prime_plan.state_fingerprint))[:32]}",
        subject_id=subject_id,
        xeed_id=xeed_id,
        source_request_id=request.request_id,
        source_observation_fingerprint=observation.observation_fingerprint,
        source_artifact_ref=observation.raw_observation_ref,
        representation_id=representation.representation_id,
        representation_fingerprint=representation.fingerprint,
        rich_state_fingerprint=rich_state.fingerprint,
        semantic_extraction_id=None if candidate_set is None else candidate_set.extraction_id,
        semantic_result_fingerprint=(
            None if candidate_set is None else candidate_set.result_fingerprint
        ),
        prime_plan=prime_plan,
        budget_stop_reason=stop_reason,
        learning_event_ids=tuple(learning_ids),
    )
