"""Derive a Focus's continuity state from its authorized Brain read (deterministic).

Inputs are the membership-checked subscriber read projection, the immutable snapshots it
was built from, and Observation Memory for dependency identity. Open questions are
derived from governed state only (UNKNOWN dimensions, missing context, non-current
support, unobserved families, unmeasured representation); no model writes them.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationMemory,
)
from application.subscriber_continuity.model import (
    ContinuityItem,
    ContinuityState,
    DeclaredDependency,
    DependencyKind,
    OpenQuestion,
    QuestionKind,
    semantic_hash,
)


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _str(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _observation_dependency(observation: GovernedObservation) -> DeclaredDependency:
    record = observation.record
    return DeclaredDependency(
        key=f"obs:{record.observation_id}",
        kind=DependencyKind.OBSERVATION,
        source_ref=record.source_ref,
        observed_at=record.observed_at,
        subject_id=record.subject_id,
        content_fingerprint=record.content_fingerprint,
        fields=tuple(
            sorted((field.name, field.value, field.state.value) for field in observation.fields)
        ),
    )


def execution_trace_identity(trace: Mapping[str, object] | None) -> dict[str, object]:
    """T022 trace: MarketMap, EB-04 replay refs and versions; no clocks or costs."""

    if not trace:
        return {}
    market = _dict(trace.get("marketMap"))
    routing = _dict(trace.get("marketPlanRouting"))
    return {
        "marketMapFingerprint": market.get("stateFingerprint"),
        "replayRefs": sorted(str(item) for item in _list(trace.get("replayRefs"))),
        "pipelineVersion": trace.get("pipelineVersion"),
        "epistemicPolicyVersion": trace.get("epistemicPolicyVersion"),
        "marketPlan": [
            routing.get("selectedDescriptorId"),
            routing.get("selectedDescriptorVersion"),
        ],
    }


def derive_continuity_state(
    projection: Mapping[str, object],
    *,
    organization_id: str,
    snapshot_refs: tuple[str, ...],
    execution_trace: Mapping[str, object] | None,
    memory: ObservationMemory,
    temporal_cut: datetime,
) -> ContinuityState:
    economic = _dict(projection.get("economicOutput"))
    subjects = {organization_id}
    subjects.update(
        value
        for value in (_str(economic.get("subject_ref")), _str(economic.get("activity_subject_ref")))
        if value is not None
    )
    observations: dict[str, GovernedObservation] = {}
    for subject in sorted(subjects):
        for item in memory.for_subject(subject):
            if item.record.observed_at <= temporal_cut:
                observations[item.record.observation_id] = item
    dependencies: dict[str, DeclaredDependency] = {}

    def observation_key(observation_id: object) -> str | None:
        found = observations.get(str(observation_id)) if observation_id is not None else None
        if found is None:
            return None
        dependency = _observation_dependency(found)
        dependencies[dependency.key] = dependency
        return dependency.key

    items: list[ContinuityItem] = []
    questions: list[OpenQuestion] = []
    cognition = _dict(projection.get("cognition"))
    sources = {
        str(row.get("id")): row
        for row in (_dict(item) for item in _list(cognition.get("sources")))
        if row.get("id") is not None
    }
    instruments: set[str] = set()
    for raw in _list(cognition.get("opportunities")):
        opportunity = _dict(raw)
        identifier = _str(opportunity.get("id"))
        if identifier is None:
            continue
        key = f"opportunity:{identifier}"
        capability = _dict(opportunity.get("capability"))
        demand = _dict(opportunity.get("demand"))
        keys: list[str] = []
        capability_key = observation_key(capability.get("sourceId"))
        if capability_key is not None:
            keys.append(capability_key)
        demand_source = sources.get(str(demand.get("sourceId")))
        if demand_source is not None and _str(demand_source.get("observedAt")):
            demand_key = f"demand:{demand.get('sourceId')}"
            dependencies[demand_key] = DeclaredDependency(
                key=demand_key,
                kind=DependencyKind.DEMAND_RECORD,
                source_ref=str(
                    demand_source.get("sourceRef") or demand_source.get("provenanceRef")
                ),
                observed_at=datetime.fromisoformat(str(demand_source["observedAt"])),
                content_fingerprint=semantic_hash(
                    [demand_source.get("provenanceRef"), demand_source.get("title")]
                ),
            )
            keys.append(demand_key)
            if _str(demand_source.get("instrument")):
                instruments.add(str(demand_source["instrument"]))
        items.append(
            ContinuityItem(
                key=key,
                kind="OPPORTUNITY",
                family=_str(opportunity.get("familyId")),
                epistemic=str(opportunity.get("epistemic") or "UNKNOWN"),
                currentness=str(opportunity.get("currentness") or "UNKNOWN"),
                value_fingerprint=semantic_hash(
                    {
                        "family": opportunity.get("opportunityFamily"),
                        "title": opportunity.get("title"),
                        "buyer": opportunity.get("buyer"),
                        "market": opportunity.get("market"),
                        "form": opportunity.get("form"),
                        "deadline": opportunity.get("deadline"),
                        "capability": capability.get("label"),
                        "demandCode": demand.get("code"),
                        "matchBasis": sorted(str(x) for x in _list(opportunity.get("matchBasis"))),
                    }
                ),
                dependency_keys=tuple(sorted(keys)),
            )
        )
        for text in sorted({str(item) for item in _list(opportunity.get("unknown"))}):
            questions.append(
                OpenQuestion(
                    key=f"q:missing:{identifier}:{semantic_hash(text)[:16]}",
                    kind=QuestionKind.MISSING_CONTEXT,
                    about=key,
                    reason=text,
                    dependency_keys=tuple(sorted(keys)),
                )
            )

    if economic:
        evidence_by_ref: dict[str, str] = {}
        output_keys: list[str] = []
        for raw in _list(economic.get("evidence")):
            datum = _dict(raw)
            dep_key = observation_key(datum.get("observation_ref"))
            if dep_key is None:
                continue
            output_keys.append(dep_key)
            if datum.get("evidence_ref") is not None:
                evidence_by_ref[str(datum["evidence_ref"])] = dep_key
        for raw in _list(economic.get("dimensions")):
            dimension = _dict(raw)
            dimension_id = _str(dimension.get("dimension_id"))
            if dimension_id is None:
                continue
            refs = [
                evidence_by_ref[str(ref)]
                for ref in _list(dimension.get("evidence_refs"))
                if str(ref) in evidence_by_ref
            ]
            keys = sorted(set(refs or output_keys))
            key = f"economic:{dimension_id}"
            items.append(
                ContinuityItem(
                    key=key,
                    kind="ECONOMIC_DIMENSION",
                    family=None,
                    epistemic=str(economic.get("epistemic_state") or "UNKNOWN"),
                    currentness=str(economic.get("temporal_state") or "UNKNOWN"),
                    value_fingerprint=semantic_hash(
                        {
                            "value": dimension.get("value"),
                            "disposition": dimension.get("disposition"),
                        }
                    ),
                    dependency_keys=tuple(keys),
                )
            )
            if dimension.get("value") is None and dimension.get("disposition") != "NOT_APPLICABLE":
                questions.append(
                    OpenQuestion(
                        key=f"q:dimension:{dimension_id}",
                        kind=QuestionKind.DIMENSION_UNKNOWN,
                        about=key,
                        reason=str(dimension.get("reason") or "UNKNOWN"),
                        dependency_keys=tuple(keys),
                    )
                )

    for conclusion in items:
        if conclusion.currentness != "CURRENT":
            questions.append(
                OpenQuestion(
                    key=f"q:currentness:{conclusion.key}",
                    kind=QuestionKind.EVIDENCE_NOT_CURRENT,
                    about=conclusion.key,
                    reason=f"SUPPORT_{conclusion.currentness}",
                    dependency_keys=conclusion.dependency_keys,
                )
            )
    if not any(conclusion.family == "demand" for conclusion in items):
        questions.append(
            OpenQuestion(
                key="q:family:demand",
                kind=QuestionKind.FAMILY_UNOBSERVED,
                about="family:demand",
                reason="No governed demand evidence supports an opportunity at this cut.",
            )
        )
    representation = _dict(projection.get("digitalRepresentation"))
    if representation.get("state") == "NOT_MEASURED":
        reason = _dict(representation.get("reason")).get("code") or "NOT_MEASURED"
        questions.append(
            OpenQuestion(
                key="q:representation",
                kind=QuestionKind.REPRESENTATION_UNMEASURED,
                about="digitalRepresentation",
                reason=str(reason),
            )
        )
    trace = execution_trace_identity(execution_trace)
    if instruments:
        trace = {**trace, "instruments": sorted(instruments)}
    return ContinuityState(
        organization_id=organization_id,
        snapshot_refs=tuple(sorted(snapshot_refs)),
        temporal_cut=temporal_cut,
        items=tuple(sorted(items, key=lambda item: item.key)),
        questions=tuple(sorted(questions, key=lambda item: item.key)),
        dependencies=tuple(sorted(dependencies.values(), key=lambda item: item.key)),
        trace=trace,
    )
