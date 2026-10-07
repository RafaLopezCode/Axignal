from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import tools.runtime.gsc_sync as gsc_sync
from application.admin_gsc import GscIngestionService, project_private_gsc
from application.admin_gsc.measurements import (
    GSC_INSTRUMENT_VERSION,
    record_gsc_summary_measurements,
)
from application.admin_measurements import MeasurementRegistryService, project_measurement_registry
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_gsc import GscSearchRow
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_gsc import SqliteAdminGscStore
from pipeline.admin_measurements import SqliteMeasurementRegistryStore
from tools.runtime.gsc_sync import run_sync

NOW = datetime(2026, 10, 7, tzinfo=UTC)
START = date(2026, 9, 7)
END = date(2026, 10, 4)


def _row(
    *,
    dimensions: tuple[tuple[str, str], ...] = (),
    clicks: float = 0,
    impressions: float = 17,
    ctr: float = 0,
    position: float = 69.11764705882354,
) -> GscSearchRow:
    suffix = "summary" if not dimensions else dimensions[0][0]
    return GscSearchRow(
        property_ref="sc-domain:axignal.com",
        window_start=START,
        window_end=END,
        dimensions=dimensions,
        clicks=clicks,
        impressions=impressions,
        ctr=ctr,
        position=position,
        observed_at=NOW,
        source_ref=f"gsc:axignal-com:2026-09-07:2026-10-04:{suffix}",
        instrument_version=GSC_INSTRUMENT_VERSION,
    )


def _grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("session:founder"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def test_private_gsc_store_is_replay_safe_and_preserves_breakdowns(tmp_path: Path) -> None:
    store = SqliteAdminGscStore(tmp_path / "gsc.sqlite3")
    service = GscIngestionService(store)
    rows = (
        _row(),
        _row(dimensions=(("query", "ausschreibungen überwachen"),), impressions=9, position=96.2),
        _row(dimensions=(("page", "https://axignal.com/"),), impressions=2, position=1.5),
        _row(dimensions=(("country", "esp"),), impressions=2, position=12),
        _row(dimensions=(("device", "DESKTOP"),), impressions=10, position=50),
        _row(dimensions=(("searchAppearance", "WEB_RESULT"),), impressions=17, position=69.1),
    )
    inserted = service.ingest(
        sync_id="gsc-sync:axignal-20261004",
        property_ref="sc-domain:axignal.com",
        rows=rows,
        window_start=START,
        window_end=END,
        observed_at=NOW,
        source_ref=rows[0].source_ref,
    )
    assert inserted == 6
    assert (
        service.ingest(
            sync_id="gsc-sync:axignal-20261004",
            property_ref="sc-domain:axignal.com",
            rows=rows,
            window_start=START,
            window_end=END,
            observed_at=NOW,
            source_ref=rows[0].source_ref,
        )
        == 0
    )

    projection = project_private_gsc(store=store, generated_at=NOW)
    assert projection.privacy_class == "PRIVATE_AXIGNAL_GSC"
    assert projection.property_ref == "sc-domain:axignal.com"
    assert projection.latest_row_count == 6
    assert dict(projection.breakdown_counts) == {
        "country": 1,
        "device": 1,
        "page": 1,
        "query": 1,
        "searchAppearance": 1,
        "summary": 1,
    }
    assert "GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION." in projection.coverage_notes


def test_gsc_summary_enters_governed_measurement_registry_without_admin_impersonation(
    tmp_path: Path,
) -> None:
    measurements = SqliteMeasurementRegistryStore(tmp_path / "measurements.sqlite3")
    audit = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    registry = MeasurementRegistryService(measurements, audit)

    observation_ids = record_gsc_summary_measurements(registry=registry, summary=_row(), now=NOW)
    assert len(observation_ids) == 4

    projection = project_measurement_registry(
        store=measurements,
        grant=_grant(),
        generated_at=NOW,
    )
    values = {item.observation.measure_id: item.observation.value for item in projection.readouts}
    assert values == {
        "measure:gsc-average-position-28d": "69.11764705882354",
        "measure:gsc-clicks-28d": "0",
        "measure:gsc-ctr-28d": "0",
        "measure:gsc-impressions-28d": "17",
    }
    assert all(
        item.observation.subject_ref == "web-property:axignal.com" for item in projection.readouts
    )
    assert all(
        definition.source_family == "GOOGLE_SEARCH_CONSOLE"
        for definition in projection.definitions
        if definition.measure_id.startswith("measure:gsc-")
    )

    records = audit.all()
    instrument_records = tuple(
        item for item in records if item.actor_principal_id == "integration:gsc-axignal-own-site"
    )
    assert len(instrument_records) == 8
    assert all(item.target.value == "INTEGRATION" for item in instrument_records)
    assert not any("AXIGLAND" in item.action for item in instrument_records)

    # Same semantic window is replay-safe: definitions and observations do not multiply.
    assert len(record_gsc_summary_measurements(registry=registry, summary=_row(), now=NOW)) == 4
    assert len(measurements.definitions()) == 4
    assert len(measurements.observations()) == 4


def test_gsc_ingestion_rejects_cross_property_mix(tmp_path: Path) -> None:
    store = SqliteAdminGscStore(tmp_path / "gsc.sqlite3")
    other = GscSearchRow(
        property_ref="sc-domain:other.example",
        window_start=START,
        window_end=END,
        dimensions=(),
        clicks=0,
        impressions=1,
        ctr=0,
        position=1,
        observed_at=NOW,
        source_ref="gsc:other-example:2026-09-07:2026-10-04:summary",
        instrument_version=GSC_INSTRUMENT_VERSION,
    )
    with pytest.raises(ValueError, match="cannot mix properties"):
        GscIngestionService(store).ingest(
            sync_id="gsc-sync:mixed",
            property_ref="sc-domain:axignal.com",
            rows=(_row(), other),
            window_start=START,
            window_end=END,
            observed_at=NOW,
            source_ref=_row().source_ref,
        )


def test_gsc_sync_fails_closed_without_server_owned_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AXIGNAL_GSC_ENABLED", raising=False)
    monkeypatch.delenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", raising=False)
    monkeypatch.delenv("AXIGNAL_GSC_PROPERTY", raising=False)
    assert run_sync(now=NOW) == {"state": "DISABLED"}

    monkeypatch.setenv("AXIGNAL_GSC_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATA_DIR", "unused")
    assert run_sync(now=NOW) == {"state": "NOT_CONFIGURED"}


def test_gsc_dimension_name_is_strict() -> None:
    with pytest.raises(ValueError, match="unsupported GSC dimension"):
        _row(dimensions=(("unsupported", "x"),))


def test_production_gsc_sync_is_fail_closed_and_secret_mounted_read_only() -> None:
    root = Path(__file__).resolve().parents[2]
    runner = (root / "deploy" / "production" / "run-gsc-sync.sh").read_text(encoding="utf-8")
    service = (root / "deploy" / "production" / "axignal-gsc-sync.service").read_text(
        encoding="utf-8"
    )
    timer = (root / "deploy" / "production" / "axignal-gsc-sync.timer").read_text(encoding="utf-8")

    assert "/etc/axignal/secrets/gsc_oauth.json" in runner
    assert "dst=/run/secrets/gsc_oauth.json,readonly" in runner
    assert "AXIGNAL_GSC_PROPERTY=sc-domain:axignal.com" in runner
    assert "--read-only" in runner
    assert "--cap-drop ALL" in runner
    assert "ConditionPathExists=/etc/axignal/secrets/gsc_oauth.json" in service
    assert "OnCalendar=*-*-* 06:17:00 UTC" in timer
    assert "client_secret" not in runner
    assert "refresh_token" not in runner


def test_server_sync_composes_real_gsc_shapes_into_private_store_and_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = tmp_path / "gsc-oauth.json"
    secret.write_text(
        '{"client_id":"fixture-client","client_secret":"fixture-secret","refresh_token":"fixture-refresh"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("AXIGNAL_GSC_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AXIGNAL_GSC_OAUTH_SECRET_FILE", str(secret))
    monkeypatch.setenv("AXIGNAL_GSC_PROPERTY", "sc-domain:axignal.com")

    class FakeClient:
        def __init__(self, credentials: object) -> None:
            self.credentials = credentials

        def query(
            self,
            *,
            property_ref: str,
            start_date: date,
            end_date: date,
            dimensions: tuple[object, ...],
            row_limit: int = 25000,
        ) -> tuple[dict[str, object], ...]:
            del property_ref, start_date, end_date, row_limit
            if not dimensions:
                return (
                    {
                        "keys": [],
                        "clicks": 0,
                        "impressions": 17,
                        "ctr": 0,
                        "position": 69.11764705882354,
                    },
                )
            name = str(dimensions[0].value)
            values = {
                "query": "ausschreibungen überwachen",
                "page": "https://axignal.com/",
                "country": "deu",
                "device": "DESKTOP",
                "searchAppearance": "WEB_RESULT",
            }
            return (
                {
                    "keys": [values[name]],
                    "clicks": 0,
                    "impressions": 1,
                    "ctr": 0,
                    "position": 10,
                },
            )

    monkeypatch.setattr(gsc_sync, "GoogleSearchConsoleClient", FakeClient)
    result = run_sync(now=NOW)
    assert result["state"] == "COMPLETED"
    assert result["rows"] == 6
    assert len(result["measurementObservations"]) == 4

    gsc_store = SqliteAdminGscStore(tmp_path / "admin-gsc.sqlite3")
    assert len(gsc_store.rows("sc-domain:axignal.com")) == 6
    measurements = SqliteMeasurementRegistryStore(tmp_path / "admin-measurements.sqlite3")
    assert len(measurements.observations()) == 4
