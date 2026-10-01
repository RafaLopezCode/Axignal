from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.admin_shell import project_admin_shell
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_observability import (
    AdminProjectionId,
    AdminProjectionSnapshot,
    AdminProjectionSnapshotId,
    AdminRecordId,
    DataCompleteness,
    ProjectionDatum,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _command_center_projection,
    _render_admin_shell,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 1, 21, 0, tzinfo=UTC)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="c" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )


def _founder_grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("admin-session:ao04"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _revenue_snapshot(
    snapshot_id: str,
    *,
    as_of: datetime,
    mrr: str,
    method: str,
) -> AdminProjectionSnapshot:
    return AdminProjectionSnapshot(
        snapshot_id=AdminProjectionSnapshotId(snapshot_id),
        projection_id=AdminProjectionId("business-revenue-summary"),
        schema_version=1,
        scope="global",
        as_of=as_of,
        generated_at=as_of,
        completeness=DataCompleteness.KNOWN,
        source_record_ids=(AdminRecordId(f"billing:{snapshot_id}"),),
        data=(
            ProjectionDatum(key="mrr", value=mrr),
            ProjectionDatum(key="arr", value=str(float(mrr) * 12)),
            ProjectionDatum(key="paying_accounts", value="3"),
            ProjectionDatum(key="currency", value="EUR"),
            ProjectionDatum(key="methodology_version", value=method),
            ProjectionDatum(
                key="period_start",
                value=(as_of - timedelta(days=30)).isoformat(),
            ),
            ProjectionDatum(key="period_end", value=as_of.isoformat()),
        ),
        fingerprint=f"sha256:{'b' * 64}",
    )


def test_runtime_command_center_starts_unknown_instead_of_zero(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    projection = _command_center_projection(runtime, now=NOW)

    assert projection.completeness is DataCompleteness.PARTIAL
    assert all(metric.value is None for metric in projection.metrics)
    rendered = _render_admin_shell(
        WEB_ROOT,
        project_admin_shell(_founder_grant()),
        command_center=projection,
    ).decode("utf-8")
    assert '"commandCenter":' in rendered
    assert '"unknownReason":"SOURCE_PROJECTION_UNAVAILABLE"' in rendered
    assert '"value":null' in rendered
    assert "Why is this number here?" in (WEB_ROOT / "admin" / "admin.js").read_text(
        encoding="utf-8"
    )


def test_runtime_uses_latest_non_future_snapshots_and_marks_method_change(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    older = _revenue_snapshot(
        "revenue:older",
        as_of=NOW - timedelta(days=30),
        mrr="90.00",
        method="billing-v1",
    )
    current = _revenue_snapshot(
        "revenue:current",
        as_of=NOW,
        mrr="100.00",
        method="billing-v2",
    )
    future = _revenue_snapshot(
        "revenue:future",
        as_of=NOW + timedelta(days=1),
        mrr="9999.00",
        method="billing-v3",
    )
    for snapshot in (older, current, future):
        runtime.admin_observability.append_snapshot(snapshot)

    projection = _command_center_projection(runtime, now=NOW)
    mrr = next(item for item in projection.metrics if item.definition.metric_id == "mrr")

    assert mrr.value == "100.00"
    assert mrr.observed_methodology_version == "billing-v2"
    assert mrr.comparison_state == "METHOD_CHANGED"
    assert mrr.previous_value is None
    assert mrr.source_record_ids == current.source_record_ids


def test_command_center_bootstrap_contains_no_credentials_or_canonical_write_surface(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    projection = _command_center_projection(runtime, now=NOW)
    rendered = _render_admin_shell(
        WEB_ROOT,
        project_admin_shell(_founder_grant(), requested_slug="command-center"),
        command_center=projection,
    ).decode("utf-8")

    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in rendered
    assert "canonical write" in rendered.lower()
    assert "Bearer " not in rendered
    assert "secret" not in rendered.lower()
