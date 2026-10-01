"""AO-04 executive projection composer over AO-03 source snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from domain.admin_command_center import (
    AdminCommandCenterProjection,
    AdminMetricDefinition,
    AdminMetricReadout,
    AdminMetricUnit,
)
from domain.admin_observability import (
    AdminProjectionId,
    AdminProjectionSnapshot,
    DataCompleteness,
)


def _metric(
    metric_id: str,
    label: str,
    group: str,
    purpose: str,
    unit: AdminMetricUnit,
    source_projection: str,
    source_key: str,
    source_types: tuple[str, ...],
    window: str,
) -> AdminMetricDefinition:
    return AdminMetricDefinition(
        metric_id=metric_id,
        label=label,
        group=group,
        purpose=purpose,
        unit=unit,
        source_projection_id=AdminProjectionId(source_projection),
        source_value_key=source_key,
        methodology_version="ao04-v1",
        source_record_types=source_types,
        default_window=window,
    )


COMMAND_CENTER_METRICS: tuple[AdminMetricDefinition, ...] = (
    _metric(
        "mrr",
        "MRR",
        "Business",
        "Recurring subscription revenue.",
        AdminMetricUnit.CURRENCY,
        "business-revenue-summary",
        "mrr",
        ("billing.subscription", "billing.invoice"),
        "30d",
    ),
    _metric(
        "arr",
        "ARR",
        "Business",
        "Annualized recurring revenue from governed MRR.",
        AdminMetricUnit.CURRENCY,
        "business-revenue-summary",
        "arr",
        ("billing.subscription",),
        "30d",
    ),
    _metric(
        "paying_accounts",
        "Paying accounts",
        "Business",
        "Accounts with an active paid subscription.",
        AdminMetricUnit.COUNT,
        "business-revenue-summary",
        "paying_accounts",
        ("account.subscription",),
        "as-of",
    ),
    _metric(
        "active_xeeds",
        "Active Xeeds",
        "Xeeds",
        "Customer-facing Xeeds active under the governed lifecycle definition.",
        AdminMetricUnit.COUNT,
        "xeed-executive-summary",
        "active_xeeds",
        ("xeed.lifecycle",),
        "as-of",
    ),
    _metric(
        "cost_per_active_xeed_month",
        "Cost / active Xeed month",
        "Xeeds",
        "Recurring attributable service cost per active Xeed-month.",
        AdminMetricUnit.CURRENCY,
        "xeed-executive-summary",
        "cost_per_active_xeed_month",
        ("cost.observation", "cost.attribution", "xeed.lifecycle"),
        "30d",
    ),
    _metric(
        "customer_product_activity",
        "Customer product activity",
        "Business",
        "Accounts with material product activity in the period.",
        AdminMetricUnit.COUNT,
        "customer-activity-summary",
        "active_accounts",
        ("product.activity",),
        "30d",
    ),
    _metric(
        "source_health",
        "Source health",
        "System",
        "Observed health of governed acquisition adapters.",
        AdminMetricUnit.STATUS,
        "provider-system-health",
        "source_health",
        ("source.health",),
        "15m",
    ),
    _metric(
        "provider_health",
        "Provider health",
        "System",
        "Observed health of cognitive/external providers.",
        AdminMetricUnit.STATUS,
        "provider-system-health",
        "provider_health",
        ("provider.health",),
        "15m",
    ),
    _metric(
        "system_health",
        "System health",
        "System",
        "Observed runtime health across owned services.",
        AdminMetricUnit.STATUS,
        "provider-system-health",
        "system_health",
        ("system.health",),
        "5m",
    ),
    _metric(
        "evidence_coverage",
        "Evidence coverage",
        "AXIGLAND quality",
        "Material graph elements with adequate evidence.",
        AdminMetricUnit.RATIO,
        "axigland-quality-summary",
        "evidence_coverage",
        ("quality.evidence",),
        "as-of",
    ),
    _metric(
        "currentness_quality",
        "Currentness",
        "AXIGLAND quality",
        "Distribution-aware governed currentness indicator.",
        AdminMetricUnit.STATUS,
        "axigland-quality-summary",
        "currentness_quality",
        ("quality.currentness",),
        "as-of",
    ),
    _metric(
        "provenance_completeness",
        "Provenance completeness",
        "AXIGLAND quality",
        "Material knowledge with reconstructable provenance lineage.",
        AdminMetricUnit.RATIO,
        "axigland-quality-summary",
        "provenance_completeness",
        ("quality.provenance",),
        "as-of",
    ),
    _metric(
        "open_incidents",
        "Open incidents",
        "Attention",
        "Open operational incidents requiring attention.",
        AdminMetricUnit.COUNT,
        "incident-summary",
        "open_incidents",
        ("incident.state",),
        "as-of",
    ),
    _metric(
        "critical_alerts",
        "Critical alerts",
        "Attention",
        "Open critical alerts under the active alert policy.",
        AdminMetricUnit.COUNT,
        "incident-summary",
        "critical_alerts",
        ("alert.state",),
        "as-of",
    ),
    _metric(
        "axigland_reuse_ratio",
        "AXIGLAND reuse ratio",
        "Flywheel",
        "Knowledge required by Xeeds already available and reusable.",
        AdminMetricUnit.RATIO,
        "flywheel-summary",
        "axigland_reuse_ratio",
        ("reuse.observation",),
        "30d",
    ),
    _metric(
        "marginal_cost_per_xeed",
        "Marginal cost / Xeed",
        "Flywheel",
        "Measured marginal cost of an additional Xeed under the declared method.",
        AdminMetricUnit.CURRENCY,
        "flywheel-summary",
        "marginal_cost_per_xeed",
        ("cost.observation", "reuse.observation"),
        "30d",
    ),
)


def _data(snapshot: AdminProjectionSnapshot) -> dict[str, str]:
    return {item.key: item.value for item in snapshot.data}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        return None
    return result if result.tzinfo is not None and result.utcoffset() is not None else None


def _unknown(
    definition: AdminMetricDefinition,
    reason: str,
    source: AdminProjectionSnapshot | None = None,
) -> AdminMetricReadout:
    values = {} if source is None else _data(source)
    completeness = DataCompleteness.UNKNOWN
    if source is not None and source.completeness in {
        DataCompleteness.UNKNOWN,
        DataCompleteness.UNAVAILABLE,
    }:
        completeness = source.completeness
    return AdminMetricReadout(
        definition=definition,
        completeness=completeness,
        value=None,
        currency=None,
        period_start=_parse_datetime(values.get("period_start")),
        period_end=_parse_datetime(values.get("period_end")),
        observed_methodology_version=values.get("methodology_version"),
        source_record_ids=() if source is None else source.source_record_ids,
        unknown_reason=reason,
        comparison_state="NO_COMPARABLE_HISTORY",
    )


def _read_metric(
    definition: AdminMetricDefinition,
    current: AdminProjectionSnapshot | None,
    previous: AdminProjectionSnapshot | None,
) -> AdminMetricReadout:
    if current is None:
        return _unknown(definition, "SOURCE_PROJECTION_UNAVAILABLE")

    values = _data(current)
    value = values.get(definition.source_value_key)
    observed_method = values.get("methodology_version")
    if not value:
        return _unknown(definition, "SOURCE_VALUE_UNAVAILABLE", current)
    if not observed_method:
        return _unknown(definition, "METHODOLOGY_VERSION_UNAVAILABLE", current)

    completeness = current.completeness
    if completeness in {DataCompleteness.UNKNOWN, DataCompleteness.UNAVAILABLE}:
        return _unknown(definition, values.get("unknown_reason", "SOURCE_INCOMPLETE"), current)

    currency = values.get("currency") if definition.unit is AdminMetricUnit.CURRENCY else None
    if definition.unit is AdminMetricUnit.CURRENCY and not currency:
        return _unknown(definition, "CURRENCY_UNAVAILABLE", current)

    comparison_state = "NO_COMPARABLE_HISTORY"
    previous_value: str | None = None
    if previous is not None and previous.completeness in {
        DataCompleteness.KNOWN,
        DataCompleteness.PARTIAL,
    }:
        previous_data = _data(previous)
        previous_method = previous_data.get("methodology_version")
        if previous_method != observed_method:
            comparison_state = "METHOD_CHANGED"
        elif previous_data.get(definition.source_value_key):
            if (
                definition.unit is AdminMetricUnit.CURRENCY
                and previous_data.get("currency") != currency
            ):
                comparison_state = "CURRENCY_CHANGED"
            else:
                comparison_state = "COMPARABLE"
                previous_value = previous_data[definition.source_value_key]

    return AdminMetricReadout(
        definition=definition,
        completeness=completeness,
        value=value,
        currency=currency,
        period_start=_parse_datetime(values.get("period_start")),
        period_end=_parse_datetime(values.get("period_end")),
        observed_methodology_version=observed_method,
        source_record_ids=current.source_record_ids,
        unknown_reason=(
            (values.get("unknown_reason") or "SOURCE_PARTIAL")
            if completeness is DataCompleteness.PARTIAL
            else None
        ),
        comparison_state=comparison_state,
        previous_value=previous_value,
    )


def project_command_center(
    *,
    current: Mapping[AdminProjectionId, AdminProjectionSnapshot],
    previous: Mapping[AdminProjectionId, AdminProjectionSnapshot] | None,
    as_of: datetime,
    generated_at: datetime,
) -> AdminCommandCenterProjection:
    previous = previous or {}
    metrics = tuple(
        _read_metric(
            definition,
            current.get(definition.source_projection_id),
            previous.get(definition.source_projection_id),
        )
        for definition in COMMAND_CENTER_METRICS
    )
    known = sum(item.completeness is DataCompleteness.KNOWN for item in metrics)
    completeness = DataCompleteness.KNOWN if known == len(metrics) else DataCompleteness.PARTIAL
    return AdminCommandCenterProjection(
        as_of=as_of,
        generated_at=generated_at,
        completeness=completeness,
        metrics=metrics,
    )
