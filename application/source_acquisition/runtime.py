"""Bridge governed source acquisition into Observation Memory and Brain planning."""

from __future__ import annotations

from dataclasses import dataclass

from application.economic_discovery import (
    CognitiveWorkPlan,
    GovernedObservation,
    ObservationIngress,
    ObservationMemory,
    ObservationMode,
    ObservationMutation,
    ObservationRecord,
    ObservationReuseAuthority,
    ObservedField,
    TypingDimensionContract,
    build_work_plan,
    ingest_observation,
)
from application.source_acquisition.contracts import SourceObservation, SourceRequest


def source_observation_id(request: SourceRequest, observation: SourceObservation) -> str:
    """Stable Observation Memory identity for one acquired source observation."""

    if observation.request_id != request.request_id:
        raise ValueError("source observation/request identity mismatch")
    return f"source:{request.request_id}:{observation.observation_fingerprint[:24]}"


def to_governed_observation(
    request: SourceRequest,
    observation: SourceObservation,
    *,
    reuse_authority: ObservationReuseAuthority | None = None,
) -> GovernedObservation:
    """Translate acquisition lineage without granting truth or semantic authority."""

    if observation.request_id != request.request_id:
        raise ValueError("source observation/request identity mismatch")
    if observation.subject_id != request.subject_id:
        raise ValueError("source observation/request subject mismatch")
    if observation.observation_slot != request.observation_slot:
        raise ValueError("source observation/request slot mismatch")
    if observation.requested_uri != request.target_uri:
        raise ValueError("source observation/request target mismatch")
    if observation.policy_id != request.policy_id:
        raise ValueError("source observation/request policy mismatch")
    if observation.policy_fingerprint != request.policy_fingerprint:
        raise ValueError("source observation/request policy fingerprint mismatch")

    prefix = f"source.{request.observation_slot}"
    fields: list[ObservedField] = [
        ObservedField(f"{prefix}.final_uri", observation.final_uri),
        ObservedField(f"{prefix}.observation_fingerprint", observation.observation_fingerprint),
    ]
    if observation.http_status is not None:
        fields.append(ObservedField(f"{prefix}.http_status", str(observation.http_status)))
    if observation.content_type is not None:
        fields.append(ObservedField(f"{prefix}.content_type", observation.content_type))
    if observation.body_fingerprint is not None:
        fields.append(ObservedField(f"{prefix}.content_fingerprint", observation.body_fingerprint))
    if observation.failure_state is not None:
        fields.append(ObservedField(f"{prefix}.failure_state", observation.failure_state))

    content_fingerprint = observation.body_fingerprint or observation.observation_fingerprint
    return GovernedObservation(
        record=ObservationRecord(
            observation_id=source_observation_id(request, observation),
            subject_id=request.subject_id,
            source_ref=observation.final_uri,
            source_type=request.source_type,
            observed_at=observation.retrieved_at,
            content_fingerprint=content_fingerprint,
            mode=ObservationMode.DETERMINISTIC_SENSOR,
        ),
        raw_artifact_ref=observation.raw_observation_ref,
        fields=tuple(fields),
        reuse_authority=(
            ObservationReuseAuthority() if reuse_authority is None else reuse_authority
        ),
    )


@dataclass(frozen=True, slots=True)
class SourceIngestionResult:
    mutation: ObservationMutation
    work_plan: CognitiveWorkPlan | None


def ingest_source_observation(
    *,
    memory: ObservationMemory,
    request: SourceRequest,
    observation: SourceObservation,
    contracts: tuple[TypingDimensionContract, ...],
    reuse_authority: ObservationReuseAuthority | None = None,
) -> SourceIngestionResult:
    """Persist one source observation and route only its actual state impact."""

    if reuse_authority is None:
        observation_id = source_observation_id(request, observation)
        existing = next(
            (
                item
                for item in memory.for_subject(request.subject_id)
                if item.record.observation_id == observation_id
            ),
            None,
        )
        if existing is not None:
            reuse_authority = existing.reuse_authority

    governed = to_governed_observation(
        request,
        observation,
        reuse_authority=reuse_authority,
    )
    mutation = ingest_observation(memory, governed)
    if mutation.change is None:
        return SourceIngestionResult(mutation=mutation, work_plan=None)

    work_plan = build_work_plan(
        ingress=ObservationIngress(
            observation_id=governed.record.observation_id,
            mode=ObservationMode.DETERMINISTIC_SENSOR,
            bound_subject_id=request.subject_id,
            requires_universe_discovery=False,
        ),
        change=mutation.change,
        contracts=contracts,
        available_state_fields=mutation.current_state.available_fields,
    )
    return SourceIngestionResult(mutation=mutation, work_plan=work_plan)
