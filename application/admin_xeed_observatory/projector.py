"""AO-05 deterministic Xeed and AXIGLAND observatory projection."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from application.economic_discovery.learning_memory import LearningEvent, LearningOutcome
from domain.admin_observability import AdminEventEnvelope, DataCompleteness
from domain.admin_xeed_observatory import (
    AxiglandRuntimeDiagnostic,
    XeedAxiglandObservatory,
    XeedRuntimeDiagnostic,
)

_XEED_PREFIX = "xeed-id:"


def _xeed_ref(record: AdminEventEnvelope) -> str | None:
    refs = [ref[len(_XEED_PREFIX) :] for ref in record.subject_refs if ref.startswith(_XEED_PREFIX)]
    if len(refs) != 1 or not refs[0]:
        return None
    return refs[0]


def _latest(records: tuple[AdminEventEnvelope, ...], record_type: str) -> AdminEventEnvelope | None:
    matches = [record for record in records if record.record_type == record_type]
    return max(matches, key=lambda item: (item.recorded_at, str(item.record_id)), default=None)


def _state(
    records: tuple[AdminEventEnvelope, ...],
    record_type: str,
    *,
    default_reason: str,
) -> tuple[str | None, DataCompleteness, str | None, tuple[str, ...]]:
    record = _latest(records, record_type)
    if record is None:
        return None, DataCompleteness.UNKNOWN, default_reason, ()
    reason = record.unknown_reason
    return record.outcome_state, record.completeness, reason, (str(record.record_id),)


def _ratio(numerator: int, denominator: int) -> str | None:
    if denominator <= 0:
        return None
    return f"{numerator / denominator:.4f}"


def _xeed_diagnostic(
    xeed_id: str,
    events: tuple[LearningEvent, ...],
    records: tuple[AdminEventEnvelope, ...],
) -> XeedRuntimeDiagnostic:
    ordered = tuple(sorted(events, key=lambda item: (item.occurred_at, item.event_id)))
    lifecycle, lifecycle_completeness, lifecycle_reason, lifecycle_ids = _state(
        records, "xeed.lifecycle", default_reason="XEED_LIFECYCLE_SOURCE_UNAVAILABLE"
    )
    currentness, currentness_completeness, currentness_reason, currentness_ids = _state(
        records, "xeed.currentness", default_reason="XEED_CURRENTNESS_SOURCE_UNAVAILABLE"
    )
    coverage, coverage_completeness, coverage_reason, coverage_ids = _state(
        records,
        "xeed.observation_coverage",
        default_reason="XEED_OBSERVATION_COVERAGE_UNAVAILABLE",
    )
    shared_state, shared_completeness, shared_reason, shared_ids = _state(
        records, "xeed.cost.shared", default_reason="SHARED_COST_ATTRIBUTION_UNAVAILABLE"
    )
    triggered_state, triggered_completeness, triggered_reason, triggered_ids = _state(
        records, "xeed.cost.triggered", default_reason="TRIGGERED_COST_ATTRIBUTION_UNAVAILABLE"
    )
    revenue_state, revenue_completeness, revenue_reason, revenue_ids = _state(
        records,
        "xeed.revenue.attribution",
        default_reason="XEED_REVENUE_ATTRIBUTION_UNAVAILABLE",
    )
    del shared_state, triggered_state, revenue_state

    reused = sum(event.yield_.observations_reused for event in ordered)
    added = sum(event.yield_.observations_added for event in ordered)
    costs: dict[str, int] = {}
    unknown_costs = 0
    for event in ordered:
        if event.cost.amount_microunits is None:
            unknown_costs += 1
        else:
            assert event.cost.currency is not None
            costs[event.cost.currency] = (
                costs.get(event.cost.currency, 0) + event.cost.amount_microunits
            )

    useful = [event.occurred_at for event in ordered if event.yield_.xignals_emitted > 0]
    first_activity = ordered[0].occurred_at if ordered else None
    first_useful = min(useful) if useful else None
    ttfv = (
        None
        if first_activity is None or first_useful is None
        else int((first_useful - first_activity).total_seconds() * 1000)
    )
    if not ordered:
        direct_cost_completeness = DataCompleteness.UNKNOWN
    elif unknown_costs == 0:
        direct_cost_completeness = DataCompleteness.KNOWN
    elif unknown_costs == len(ordered):
        direct_cost_completeness = DataCompleteness.UNKNOWN
    else:
        direct_cost_completeness = DataCompleteness.PARTIAL

    return XeedRuntimeDiagnostic(
        xeed_id=xeed_id,
        subject_ids=tuple(sorted({event.subject_id for event in ordered})),
        lifecycle_state=lifecycle,
        lifecycle_completeness=lifecycle_completeness,
        lifecycle_reason=lifecycle_reason,
        currentness_state=currentness,
        currentness_completeness=currentness_completeness,
        currentness_reason=currentness_reason,
        observation_coverage_state=coverage,
        observation_coverage_completeness=coverage_completeness,
        observation_coverage_reason=coverage_reason,
        first_activity_at=first_activity,
        last_activity_at=ordered[-1].occurred_at if ordered else None,
        first_useful_xignal_at=first_useful,
        time_to_first_useful_xignal_ms=ttfv,
        learning_event_count=len(ordered),
        failed_event_count=sum(event.outcome is LearningOutcome.FAILED for event in ordered),
        partial_event_count=sum(event.outcome is LearningOutcome.PARTIAL for event in ordered),
        observations_reused=reused,
        observations_added=added,
        reuse_ratio=_ratio(reused, reused + added),
        xignals_emitted=sum(event.yield_.xignals_emitted for event in ordered),
        canonical_admissions=sum(event.yield_.canonical_admissions for event in ordered),
        known_costs_by_currency=tuple(sorted(costs.items())),
        unknown_cost_event_count=unknown_costs,
        direct_cost_completeness=direct_cost_completeness,
        shared_cost_completeness=shared_completeness,
        shared_cost_reason=shared_reason or "SHARED_COST_ATTRIBUTION_PARTIAL",
        triggered_cost_completeness=triggered_completeness,
        triggered_cost_reason=triggered_reason or "TRIGGERED_COST_ATTRIBUTION_PARTIAL",
        revenue_attribution_completeness=revenue_completeness,
        revenue_attribution_reason=revenue_reason or "XEED_REVENUE_ATTRIBUTION_PARTIAL",
        source_learning_event_ids=tuple(event.event_id for event in ordered),
        source_admin_record_ids=tuple(
            sorted(
                set(
                    lifecycle_ids
                    + currentness_ids
                    + coverage_ids
                    + shared_ids
                    + triggered_ids
                    + revenue_ids
                )
            )
        ),
    )


def project_xeed_axigland_observatory(
    *,
    learning_events: tuple[LearningEvent, ...],
    admin_records: tuple[AdminEventEnvelope, ...],
    as_of: datetime,
    generated_at: datetime,
) -> XeedAxiglandObservatory:
    eligible_events = tuple(event for event in learning_events if event.occurred_at <= as_of)
    eligible_records = tuple(record for record in admin_records if record.recorded_at <= as_of)

    by_xeed: dict[str, list[LearningEvent]] = defaultdict(list)
    xeed_records: dict[str, list[AdminEventEnvelope]] = defaultdict(list)
    for event in eligible_events:
        if event.xeed_id is not None:
            by_xeed[event.xeed_id].append(event)
    for record in eligible_records:
        xeed_id = _xeed_ref(record)
        if xeed_id is not None:
            xeed_records[xeed_id].append(record)

    xeed_ids = sorted(set(by_xeed) | set(xeed_records))
    xeeds = tuple(
        _xeed_diagnostic(
            xeed_id,
            tuple(by_xeed.get(xeed_id, ())),
            tuple(xeed_records.get(xeed_id, ())),
        )
        for xeed_id in xeed_ids
    )

    reused = sum(event.yield_.observations_reused for event in eligible_events)
    added = sum(event.yield_.observations_added for event in eligible_events)
    canonical_admissions = sum(event.yield_.canonical_admissions for event in eligible_events)

    growth, growth_comp, _, growth_ids = _state(
        eligible_records,
        "axigland.growth",
        default_reason="AXIGLAND_GROWTH_PROJECTION_UNAVAILABLE",
    )
    contradiction, contradiction_comp, _, contradiction_ids = _state(
        eligible_records,
        "axigland.contradiction",
        default_reason="CONTRADICTION_PROJECTION_UNAVAILABLE",
    )
    identity, identity_comp, _, identity_ids = _state(
        eligible_records,
        "axigland.identity_resolution",
        default_reason="IDENTITY_RESOLUTION_PROJECTION_UNAVAILABLE",
    )
    currentness, currentness_comp, _, currentness_ids = _state(
        eligible_records,
        "axigland.currentness",
        default_reason="CURRENTNESS_PROJECTION_UNAVAILABLE",
    )
    provenance, provenance_comp, _, provenance_ids = _state(
        eligible_records,
        "axigland.provenance",
        default_reason="PROVENANCE_PROJECTION_UNAVAILABLE",
    )

    quality_completeness = (
        DataCompleteness.KNOWN
        if all(
            value is DataCompleteness.KNOWN
            for value in (
                growth_comp,
                contradiction_comp,
                identity_comp,
                currentness_comp,
                provenance_comp,
            )
        )
        else DataCompleteness.PARTIAL
    )
    overall = (
        DataCompleteness.KNOWN
        if xeeds and quality_completeness is DataCompleteness.KNOWN
        else DataCompleteness.PARTIAL
    )
    admin_quality_ids = (
        growth_ids + contradiction_ids + identity_ids + currentness_ids + provenance_ids
    )

    return XeedAxiglandObservatory(
        as_of=as_of,
        generated_at=generated_at,
        completeness=overall,
        xeeds=xeeds,
        axigland=AxiglandRuntimeDiagnostic(
            completeness=quality_completeness,
            canonical_admission_events=canonical_admissions,
            observations_reused=reused,
            observations_added=added,
            reuse_ratio=_ratio(reused, reused + added),
            growth_state=growth,
            growth_completeness=growth_comp,
            contradiction_state=contradiction,
            contradiction_completeness=contradiction_comp,
            identity_resolution_state=identity,
            identity_resolution_completeness=identity_comp,
            currentness_state=currentness,
            currentness_completeness=currentness_comp,
            provenance_state=provenance,
            provenance_completeness=provenance_comp,
            source_learning_event_ids=tuple(event.event_id for event in eligible_events),
            source_admin_record_ids=tuple(sorted(set(admin_quality_ids))),
        ),
        coverage_notes=(
            "Learning Memory is operational evidence, not AXIGLAND canonical truth.",
            "canonical_admission_events counts admissions emitted by learning events; it is not current FAXT cardinality.",
            "observations_reused measures reuse and never counts as new AXIGLAND growth.",
            "shared and triggered cost remain separate; absent attribution is UNKNOWN, never free.",
        ),
    )
