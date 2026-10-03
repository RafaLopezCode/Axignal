from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_measurements import (
    MeasurementRegistryService,
    compare_measurements,
    project_measurement_registry,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_governance import AdminGovernanceCommandTarget
from domain.admin_measurements import (
    MeasurementComparisonState,
    MeasurementDefinition,
    MeasurementFreshness,
    MeasurementObservation,
    MeasurementState,
    MeasurementUnit,
)
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_measurements import (
    MeasurementRegistryStoreConflict,
    SqliteMeasurementRegistryStore,
)

NOW = datetime(2026, 10, 3, 22, 0, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _definition(
    *,
    version: int = 1,
    instrument_version: str = "gsc-v1",
    compatibility_key: str = "search-impressions:28d:v1",
) -> MeasurementDefinition:
    return MeasurementDefinition(
        measure_id="measure:search-impressions-28d",
        version=version,
        label="Search impressions, 28 days",
        question_served="Is observable search demand changing for the measured subject?",
        decision_served="Decide whether search representation deserves investigation.",
        formula_or_coding_rule="SUM(GSC impressions) over declared 28-day window.",
        unit=MeasurementUnit.COUNT,
        source_family="GOOGLE_SEARCH_CONSOLE",
        instrument_id="instrument:gsc-search-analytics",
        instrument_version=instrument_version,
        subject_scope="ONE_REGISTERED_WEB_PROPERTY",
        default_window="P28D",
        freshness_seconds=172800,
        minimum_sample_size=1,
        uncertainty_policy="Coverage is limited to the connected GSC property and selected dimensions.",
        compatibility_key=compatibility_key,
        interpretation_limits=(
            "Impressions are search exposure, not revenue or business capability.",
            "A change can reflect query mix or indexing changes, not only market demand.",
        ),
        evaluation_cases=(
            "same property and same instrument version across adjacent windows",
            "instrument version drift must reject naive historical comparison",
        ),
        effective_at=NOW,
    )


def _observation(
    *,
    observation_id: str,
    definition_version: int = 1,
    instrument_version: str = "gsc-v1",
    compatibility_key: str = "search-impressions:28d:v1",
    state: MeasurementState = MeasurementState.MEASURED,
    observed_at: datetime = NOW,
    value: str | None = "3820",
    sample_size: int | None = 1,
    informative_sample_size: int | None = 1,
) -> MeasurementObservation:
    return MeasurementObservation(
        observation_id=observation_id,
        measure_id="measure:search-impressions-28d",
        definition_version=definition_version,
        subject_ref="web-property:axignal.com",
        instrument_id="instrument:gsc-search-analytics",
        instrument_version=instrument_version,
        compatibility_key=compatibility_key,
        state=state,
        observed_at=observed_at,
        window_start=observed_at - timedelta(days=28),
        window_end=observed_at,
        sample_size=sample_size,
        informative_sample_size=informative_sample_size,
        value=value,
        currency=None,
        uncertainty="GSC property/query coverage only; unmeasured search surfaces remain unknown.",
        source_refs=("gsc:property:axignal.com:28d",),
    )


def _service(tmp_path: Path):
    store = SqliteMeasurementRegistryStore(tmp_path / "measurements.sqlite3")
    audit = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    return MeasurementRegistryService(store, audit), store, audit


def test_unregistered_metric_cannot_become_measurement_authority(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)
    with pytest.raises(ValueError, match="unregistered definition"):
        service.record_observation(
            grant=_grant(),
            operation_id="measurement:unregistered",
            reason="attempt arbitrary KPI",
            observation=_observation(observation_id="obs:unregistered"),
            now=NOW,
        )


def test_definition_versions_are_immutable_and_sequential(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    assert service.register_definition(
        grant=_grant(),
        operation_id="definition:v1",
        reason="register governed KPI",
        definition=_definition(),
        now=NOW,
    )
    with pytest.raises(MeasurementRegistryStoreConflict, match="out of sequence"):
        store.append_definition(_definition(version=3))
    with pytest.raises(MeasurementRegistryStoreConflict, match="different content"):
        store.append_definition(replace(_definition(), label="Changed label"))


def test_insufficient_sample_must_not_be_recorded_as_measured(tmp_path: Path) -> None:
    service, _, _ = _service(tmp_path)
    definition = replace(_definition(), minimum_sample_size=10)
    service.register_definition(
        grant=_grant(),
        operation_id="definition:min-sample",
        reason="register minimum sample",
        definition=definition,
        now=NOW,
    )
    with pytest.raises(ValueError, match="must be recorded as INSUFFICIENT"):
        service.record_observation(
            grant=_grant(),
            operation_id="measurement:too-small",
            reason="reject false measured value",
            observation=_observation(
                observation_id="obs:too-small",
                sample_size=5,
                informative_sample_size=5,
            ),
            now=NOW,
        )


def test_not_measured_and_insufficient_never_carry_zero(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    service.register_definition(
        grant=_grant(),
        operation_id="definition:v1",
        reason="register governed KPI",
        definition=_definition(),
        now=NOW,
    )
    for state, suffix in (
        (MeasurementState.NOT_MEASURED, "not-measured"),
        (MeasurementState.INSUFFICIENT, "insufficient"),
    ):
        observation = _observation(
            observation_id=f"obs:{suffix}",
            state=state,
            value=None,
            sample_size=None,
            informative_sample_size=None,
        )
        service.record_observation(
            grant=_grant(),
            operation_id=f"measurement:{suffix}",
            reason="preserve missing measurement state",
            observation=observation,
            now=NOW,
        )

    projection = project_measurement_registry(
        store=store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert len(projection.readouts) == 2
    assert all(item.observation.value is None for item in projection.readouts)
    assert all(item.usable is False for item in projection.readouts)
    assert all(item.freshness is MeasurementFreshness.NOT_MEASURED for item in projection.readouts)


def test_instrument_version_drift_breaks_historical_comparison(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    v1 = _definition()
    v2 = _definition(version=2, instrument_version="gsc-v2")
    service.register_definition(
        grant=_grant(),
        operation_id="definition:v1",
        reason="register v1",
        definition=v1,
        now=NOW,
    )
    service.register_definition(
        grant=_grant(),
        operation_id="definition:v2",
        reason="instrument changed",
        definition=v2,
        now=NOW,
    )
    earlier = _observation(observation_id="obs:earlier")
    later = _observation(
        observation_id="obs:later",
        definition_version=2,
        instrument_version="gsc-v2",
        observed_at=NOW + timedelta(days=28),
        value="4100",
    )
    for index, observation in enumerate((earlier, later), start=1):
        service.record_observation(
            grant=_grant(),
            operation_id=f"measurement:obs:{index}",
            reason="record comparable-series candidate",
            observation=observation,
            now=observation.observed_at,
        )

    comparison = compare_measurements(store=store, earlier=earlier, later=later)
    assert comparison.state is MeasurementComparisonState.INCOMPATIBLE
    assert "instrument identity/version differs" in comparison.reason


def test_same_instrument_and_definition_can_compare(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    service.register_definition(
        grant=_grant(),
        operation_id="definition:v1",
        reason="register v1",
        definition=_definition(),
        now=NOW,
    )
    earlier = _observation(observation_id="obs:earlier", value="3820")
    later = _observation(
        observation_id="obs:later",
        observed_at=NOW + timedelta(days=28),
        value="4100",
    )
    comparison = compare_measurements(store=store, earlier=earlier, later=later)
    assert comparison.state is MeasurementComparisonState.COMPARABLE


def test_freshness_marks_stale_without_mutating_historical_value(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    service.register_definition(
        grant=_grant(),
        operation_id="definition:v1",
        reason="register v1",
        definition=_definition(),
        now=NOW,
    )
    observation = _observation(observation_id="obs:freshness")
    service.record_observation(
        grant=_grant(),
        operation_id="measurement:freshness",
        reason="record historical measurement",
        observation=observation,
        now=NOW,
    )
    fresh = project_measurement_registry(
        store=store,
        grant=_grant(),
        generated_at=NOW + timedelta(hours=1),
    ).readouts[0]
    stale = project_measurement_registry(
        store=store,
        grant=_grant(),
        generated_at=NOW + timedelta(days=3),
    ).readouts[0]

    assert fresh.freshness is MeasurementFreshness.FRESH
    assert fresh.usable is True
    assert stale.freshness is MeasurementFreshness.STALE
    assert stale.usable is False
    assert stale.observation.value == "3820"


def test_registry_mutations_are_audited_under_advisory_target(tmp_path: Path) -> None:
    service, _, audit = _service(tmp_path)
    service.register_definition(
        grant=_grant(),
        operation_id="definition:audit",
        reason="register governed metric",
        definition=_definition(),
        now=NOW,
    )
    records = audit.all()
    assert len(records) == 1
    assert records[0].target is AdminGovernanceCommandTarget.ADVISORY
    assert records[0].required_scope == "admin:advisory:write"


def test_registry_projection_requires_advisory_read(tmp_path: Path) -> None:
    _, store, _ = _service(tmp_path)
    with pytest.raises(PermissionError, match="admin:advisory:read"):
        project_measurement_registry(
            store=store,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_runtime_composes_empty_measurement_registry_and_frontier_surface(
    tmp_path: Path,
) -> None:
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="f" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=root / "apps" / "web",
        )
    )

    assert runtime.admin_measurement_store.path.is_file()
    projection = project_measurement_registry(
        store=runtime.admin_measurement_store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.definitions == ()
    assert projection.readouts == ()
    assert projection.privacy_class == "PRIVATE_GOVERNED_MEASUREMENT_REGISTRY"

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-measurement-registry" in html
    assert "Measurement authority for advisory work" in html
    assert "bootstrap.measurementRegistry" in javascript
    assert "No governed KPI definitions registered" in javascript
