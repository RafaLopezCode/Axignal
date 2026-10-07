"""Evaluate a checkpoint's declared dependencies against the EB-06 temporal authority.

Observation Memory is the only temporal store: state is compiled as of the cut with
``compile_observation_state``, reuse rights with ``select_reusable_observations`` and
freshness with the temporal currentness policy. Nothing here writes or invents state.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationFieldState,
    ObservationMemory,
    ObservationState,
    compile_observation_state,
)
from application.economic_discovery.observation_reuse import (
    ObservationReuseContext,
    ObservationReuseDecision,
    ObservationReusePolicy,
    ReuseDisposition,
    ReusePurpose,
    ReuseTargetScope,
    select_reusable_observations,
)
from application.economic_discovery.temporal_currentness import (
    TemporalCurrentnessPolicy,
    evaluate_effective_currentness,
)
from application.subscriber_continuity.model import (
    ACTION_FOR_STATUS,
    DeclaredDependency,
    DependencyKind,
    DependencyStatus,
    InvalidationAction,
)
from domain.evidence.epistemics import Currentness

_PRECEDENCE = (
    DependencyStatus.MISSING,
    DependencyStatus.RIGHTS_BLOCKED,
    DependencyStatus.WITHDRAWN,
    DependencyStatus.REPLACED,
    DependencyStatus.STALE,
    DependencyStatus.REFRESHED,
    DependencyStatus.CURRENT,
)
_GONE = (ObservationFieldState.WITHDRAWN, ObservationFieldState.MEASURED_ABSENCE)


@dataclass(frozen=True, slots=True)
class DependencyEvaluation:
    key: str
    status: DependencyStatus
    reason: str

    @property
    def action(self) -> InvalidationAction:
        return ACTION_FOR_STATUS[self.status]


def _worst(*items: tuple[DependencyStatus, str]) -> tuple[DependencyStatus, str]:
    return min(items, key=lambda item: _PRECEDENCE.index(item[0]))


def evaluate_dependencies(
    dependencies: tuple[DeclaredDependency, ...],
    *,
    memory: ObservationMemory,
    tenant_id: str,
    xeed_id: str,
    as_of: datetime,
    reuse_policy: ObservationReusePolicy,
    temporal_policy: TemporalCurrentnessPolicy,
) -> dict[str, DependencyEvaluation]:
    """One status per dependency; each subject's history is read and compiled once."""

    if as_of.tzinfo is None:
        raise ValueError("dependency evaluation time must be timezone-aware")
    by_subject: dict[str, list[DeclaredDependency]] = defaultdict(list)
    results: dict[str, DependencyEvaluation] = {}
    for dependency in dependencies:
        if dependency.kind is DependencyKind.OBSERVATION and dependency.subject_id:
            by_subject[dependency.subject_id].append(dependency)
        elif dependency.kind is DependencyKind.DEMAND_RECORD:
            decision = evaluate_effective_currentness(
                observation_id=dependency.key,
                observed_at=dependency.observed_at,
                previous=Currentness.CURRENT,
                as_of=as_of,
                policy=temporal_policy,
            )
            status = (
                DependencyStatus.CURRENT
                if decision.current is Currentness.CURRENT
                else DependencyStatus.STALE
            )
            results[dependency.key] = DependencyEvaluation(
                dependency.key, status, f"DEMAND_RECORD_{decision.current.value}"
            )
        else:
            results[dependency.key] = DependencyEvaluation(
                dependency.key, DependencyStatus.MISSING, "UNSUPPORTED_DEPENDENCY"
            )

    for subject_id, items in by_subject.items():
        observations = memory.for_subject(subject_id)
        by_id: dict[str, GovernedObservation] = {
            item.record.observation_id: item for item in observations
        }
        selection = select_reusable_observations(
            memory,
            context=ObservationReuseContext(
                subject_id=subject_id,
                xeed_id=xeed_id,
                tenant_id=tenant_id,
                target_scope=ReuseTargetScope.GLOBAL_WORLD,
                purpose=ReusePurpose.HISTORICAL_REFERENCE,
                as_of=as_of,
            ),
            policy=reuse_policy,
            temporal_policy=temporal_policy,
        )
        decisions = {item.observation_id: item for item in selection.decisions}
        state = compile_observation_state(
            subject_id,
            tuple(item for item in observations if item.record.observation_id in decisions),
            as_of=as_of,
        )
        for dependency in items:
            observation_id = dependency.key.removeprefix("obs:")
            results[dependency.key] = DependencyEvaluation(
                dependency.key,
                *_observation_status(
                    dependency,
                    by_id.get(observation_id),
                    decision=decisions.get(observation_id),
                    decisions=decisions,
                    state=state,
                    observations=observations,
                    as_of=as_of,
                ),
            )
    return results


def _observation_status(
    dependency: DeclaredDependency,
    observation: GovernedObservation | None,
    *,
    decision: ObservationReuseDecision | None,
    decisions: dict[str, ObservationReuseDecision],
    state: ObservationState,
    observations: tuple[GovernedObservation, ...],
    as_of: datetime,
) -> tuple[DependencyStatus, str]:
    if observation is None or observation.record.observed_at > as_of:
        return DependencyStatus.MISSING, "OBSERVATION_NOT_AVAILABLE"
    if (
        dependency.content_fingerprint is not None
        and observation.record.content_fingerprint != dependency.content_fingerprint
    ):
        return DependencyStatus.MISSING, "OBSERVATION_INTEGRITY_MISMATCH"
    if decision is None or decision.disposition is not ReuseDisposition.ALLOW:
        reason = "NOT_EVALUATED" if decision is None else decision.reason.value
        return DependencyStatus.RIGHTS_BLOCKED, f"REUSE_{reason}"

    # What happened to the meaning this dependency carried (EB-06 typed state).
    changes: list[tuple[DependencyStatus, str]] = []
    refreshed_by: list[str] = []
    for name, value, _state in dependency.fields:
        current = state.get(name)
        if current is None:
            changes.append((DependencyStatus.MISSING, f"FIELD_ABSENT:{name}"))
        elif current.observation_id == observation.record.observation_id:
            continue
        elif current.state in _GONE:
            changes.append((DependencyStatus.WITHDRAWN, f"FIELD_{current.state.value}:{name}"))
        elif current.state is not ObservationFieldState.VALUE or current.value != value:
            changes.append((DependencyStatus.REPLACED, f"FIELD_CHANGED:{name}"))
        else:
            changes.append((DependencyStatus.REFRESHED, f"FIELD_REOBSERVED:{name}"))
            refreshed_by.append(current.observation_id)
    if not dependency.fields:
        newer = [
            item
            for item in observations
            if item.record.source_ref == observation.record.source_ref
            and observation.record.observed_at < item.record.observed_at <= as_of
        ]
        if newer:
            latest = max(
                newer, key=lambda item: (item.record.observed_at, item.record.observation_id)
            )
            if latest.record.content_fingerprint == observation.record.content_fingerprint:
                changes.append((DependencyStatus.REFRESHED, "SOURCE_REOBSERVED_SAME_CONTENT"))
                refreshed_by.append(latest.record.observation_id)
            else:
                changes.append((DependencyStatus.REPLACED, "SOURCE_CONTENT_CHANGED"))
    if changes:
        worst = _worst(*changes)
        if worst[0] is not DependencyStatus.REFRESHED:
            return worst
        # Same meaning re-observed: as fresh as that re-observation, never fresher.
        for observation_id in refreshed_by:
            refresh = decisions.get(observation_id)
            if refresh is None or refresh.effective_currentness is not Currentness.CURRENT:
                state_value = "UNKNOWN" if refresh is None else refresh.effective_currentness.value
                return DependencyStatus.STALE, f"REOBSERVATION_{state_value}"
        return worst
    if decision.effective_currentness is not Currentness.CURRENT:
        return DependencyStatus.STALE, f"EVIDENCE_{decision.effective_currentness.value}"
    return DependencyStatus.CURRENT, "EVIDENCE_CURRENT"
