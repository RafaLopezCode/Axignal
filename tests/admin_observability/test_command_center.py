from datetime import UTC, datetime, timedelta

from application.admin_command_center import project_command_center
from domain.admin_observability import (
    AdminProjectionId,
    AdminProjectionSnapshot,
    AdminProjectionSnapshotId,
    AdminRecordId,
    DataCompleteness,
    ProjectionDatum,
)

NOW = datetime(2026, 10, 1, 20, 30, tzinfo=UTC)


def _snapshot(
    projection_id: str,
    data: dict[str, str],
    *,
    source_ids: tuple[str, ...] = ("record:1",),
    completeness: DataCompleteness = DataCompleteness.KNOWN,
    as_of: datetime = NOW,
) -> AdminProjectionSnapshot:
    return AdminProjectionSnapshot(
        snapshot_id=AdminProjectionSnapshotId(f"snapshot:{projection_id}:{as_of.timestamp()}"),
        projection_id=AdminProjectionId(projection_id),
        schema_version=1,
        scope="global",
        as_of=as_of,
        generated_at=as_of,
        completeness=completeness,
        source_record_ids=tuple(AdminRecordId(value) for value in source_ids),
        data=tuple(ProjectionDatum(key=key, value=value) for key, value in data.items()),
        fingerprint=f"sha256:{'a' * 64}",
    )


def _metric(projection, metric_id: str):
    return next(item for item in projection.metrics if item.definition.metric_id == metric_id)


def test_absent_owner_projections_remain_unknown_not_zero() -> None:
    projection = project_command_center(
        current={},
        previous={},
        as_of=NOW,
        generated_at=NOW,
    )

    assert projection.completeness is DataCompleteness.PARTIAL
    assert len(projection.metrics) >= 15
    assert all(item.value is None for item in projection.metrics)
    assert all(item.completeness is DataCompleteness.UNKNOWN for item in projection.metrics)
    assert {item.unknown_reason for item in projection.metrics} == {"SOURCE_PROJECTION_UNAVAILABLE"}


def test_revenue_metrics_preserve_currency_method_period_and_lineage() -> None:
    revenue = _snapshot(
        "business-revenue-summary",
        {
            "mrr": "149.50",
            "arr": "1794.00",
            "paying_accounts": "12",
            "currency": "EUR",
            "methodology_version": "billing-v3",
            "period_start": "2026-09-01T00:00:00+00:00",
            "period_end": "2026-10-01T00:00:00+00:00",
        },
        source_ids=("billing:sub:1", "billing:invoice:9"),
    )
    projection = project_command_center(
        current={AdminProjectionId("business-revenue-summary"): revenue},
        previous={},
        as_of=NOW,
        generated_at=NOW,
    )

    mrr = _metric(projection, "mrr")
    assert mrr.value == "149.50"
    assert mrr.currency == "EUR"
    assert mrr.observed_methodology_version == "billing-v3"
    assert mrr.period_start == datetime(2026, 9, 1, tzinfo=UTC)
    assert mrr.source_record_ids == (
        AdminRecordId("billing:sub:1"),
        AdminRecordId("billing:invoice:9"),
    )


def test_methodology_change_is_not_presented_as_business_change() -> None:
    current = _snapshot(
        "business-revenue-summary",
        {
            "mrr": "150.00",
            "arr": "1800.00",
            "paying_accounts": "12",
            "currency": "EUR",
            "methodology_version": "billing-v2",
        },
    )
    previous = _snapshot(
        "business-revenue-summary",
        {
            "mrr": "140.00",
            "arr": "1680.00",
            "paying_accounts": "11",
            "currency": "EUR",
            "methodology_version": "billing-v1",
        },
        as_of=NOW - timedelta(days=30),
    )
    projection = project_command_center(
        current={AdminProjectionId("business-revenue-summary"): current},
        previous={AdminProjectionId("business-revenue-summary"): previous},
        as_of=NOW,
        generated_at=NOW,
    )

    mrr = _metric(projection, "mrr")
    assert mrr.comparison_state == "METHOD_CHANGED"
    assert mrr.previous_value is None


def test_currency_change_blocks_financial_comparison() -> None:
    current = _snapshot(
        "business-revenue-summary",
        {
            "mrr": "150.00",
            "arr": "1800.00",
            "paying_accounts": "12",
            "currency": "EUR",
            "methodology_version": "billing-v1",
        },
    )
    previous = _snapshot(
        "business-revenue-summary",
        {
            "mrr": "160.00",
            "arr": "1920.00",
            "paying_accounts": "12",
            "currency": "USD",
            "methodology_version": "billing-v1",
        },
        as_of=NOW - timedelta(days=30),
    )
    projection = project_command_center(
        current={AdminProjectionId("business-revenue-summary"): current},
        previous={AdminProjectionId("business-revenue-summary"): previous},
        as_of=NOW,
        generated_at=NOW,
    )

    assert _metric(projection, "mrr").comparison_state == "CURRENCY_CHANGED"


def test_incomplete_source_cannot_smuggle_numeric_value_as_known() -> None:
    source = _snapshot(
        "xeed-executive-summary",
        {
            "active_xeeds": "0",
            "cost_per_active_xeed_month": "0",
            "currency": "EUR",
            "methodology_version": "xeed-v1",
            "unknown_reason": "lifecycle_source_not_connected",
        },
        completeness=DataCompleteness.UNKNOWN,
    )
    projection = project_command_center(
        current={AdminProjectionId("xeed-executive-summary"): source},
        previous={},
        as_of=NOW,
        generated_at=NOW,
    )

    active = _metric(projection, "active_xeeds")
    assert active.value is None
    assert active.completeness is DataCompleteness.UNKNOWN
    assert active.unknown_reason == "lifecycle_source_not_connected"


def test_partial_metric_keeps_observed_value_and_discloses_exclusions() -> None:
    source = _snapshot(
        "axigland-quality-summary",
        {
            "evidence_coverage": "0.82",
            "currentness_quality": "AGING",
            "provenance_completeness": "0.91",
            "methodology_version": "quality-v2",
            "unknown_reason": "legacy_entities_excluded",
        },
        completeness=DataCompleteness.PARTIAL,
    )
    projection = project_command_center(
        current={AdminProjectionId("axigland-quality-summary"): source},
        previous={},
        as_of=NOW,
        generated_at=NOW,
    )

    evidence = _metric(projection, "evidence_coverage")
    assert evidence.value == "0.82"
    assert evidence.completeness is DataCompleteness.PARTIAL
    assert evidence.unknown_reason == "legacy_entities_excluded"


def test_unknown_source_preserves_available_lineage() -> None:
    source = _snapshot(
        "provider-system-health",
        {
            "source_health": "UNKNOWN",
            "provider_health": "UNKNOWN",
            "system_health": "UNKNOWN",
            "methodology_version": "health-v1",
            "unknown_reason": "probe_stale",
        },
        source_ids=("health:probe:7",),
        completeness=DataCompleteness.UNKNOWN,
    )
    projection = project_command_center(
        current={AdminProjectionId("provider-system-health"): source},
        previous={},
        as_of=NOW,
        generated_at=NOW,
    )

    health = _metric(projection, "provider_health")
    assert health.value is None
    assert health.unknown_reason == "probe_stale"
    assert health.source_record_ids == (AdminRecordId("health:probe:7"),)
