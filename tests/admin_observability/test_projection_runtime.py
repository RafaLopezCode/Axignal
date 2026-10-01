from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_observability import (
    AdminProjectionConflict,
    AdminProjectionRuntime,
    AdminRecordInventoryProjection,
)
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)
from pipeline.admin_observability import SqliteAdminObservabilityStore


def _record(
    record_id: str,
    *,
    recorded_at: datetime,
    outcome: str = "SUCCEEDED",
    completeness: DataCompleteness = DataCompleteness.KNOWN,
    unknown_reason: str | None = None,
    supersedes: str | None = None,
    record_class: AdminRecordClass = AdminRecordClass.OPERATIONAL_EVENT,
    owning_domain: str = "test-domain",
) -> AdminEventEnvelope:
    return AdminEventEnvelope(
        record_id=AdminRecordId(record_id),
        record_type="test.operation",
        record_class=record_class,
        schema_version=1,
        producer="tests",
        owning_domain=owning_domain,
        recorded_at=recorded_at,
        occurred_at=recorded_at,
        outcome_state=outcome,
        completeness=completeness,
        unknown_reason=unknown_reason,
        privacy_class=AdminPrivacyClass.INTERNAL,
        subject_refs=("xeed:test",),
        provenance_refs=("source:test",),
        supersedes_record_id=(None if supersedes is None else AdminRecordId(supersedes)),
    )


def test_exact_replay_is_idempotent_and_conflicting_replay_fails(tmp_path: Path) -> None:
    store = SqliteAdminObservabilityStore(tmp_path / "admin.sqlite3")
    runtime = AdminProjectionRuntime(store)
    now = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    event = _record("event:1", recorded_at=now)

    assert runtime.ingest(event) is True
    assert runtime.ingest(event) is False

    conflicting = _record("event:1", recorded_at=now, outcome="FAILED")
    with pytest.raises(AdminProjectionConflict):
        runtime.ingest(conflicting)


def test_correction_preserves_history_and_changes_only_future_projection(tmp_path: Path) -> None:
    store = SqliteAdminObservabilityStore(tmp_path / "admin.sqlite3")
    runtime = AdminProjectionRuntime(store)
    t1 = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    original = _record("event:1", recorded_at=t1)
    correction = _record(
        "event:2",
        recorded_at=t1 + timedelta(minutes=10),
        outcome="CORRECTED",
        supersedes="event:1",
    )
    runtime.ingest(original)
    runtime.ingest(correction)

    before = runtime.build_snapshot(
        AdminRecordInventoryProjection(),
        scope="global",
        as_of=t1 + timedelta(minutes=5),
        generated_at=t1 + timedelta(minutes=11),
        persist=False,
    )
    after = runtime.build_snapshot(
        AdminRecordInventoryProjection(),
        scope="global",
        as_of=t1 + timedelta(minutes=10),
        generated_at=t1 + timedelta(minutes=11),
        persist=False,
    )

    assert before.source_record_ids == (AdminRecordId("event:1"),)
    assert after.source_record_ids == (AdminRecordId("event:2"),)
    assert store.get_record(AdminRecordId("event:1")) == original
    assert store.get_record(AdminRecordId("event:2")) == correction


def test_projection_replay_is_deterministic_and_snapshot_is_durable(tmp_path: Path) -> None:
    store = SqliteAdminObservabilityStore(tmp_path / "admin.sqlite3")
    runtime = AdminProjectionRuntime(store)
    now = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    runtime.ingest(_record("event:1", recorded_at=now))
    runtime.ingest(
        _record(
            "event:2",
            recorded_at=now + timedelta(seconds=1),
            record_class=AdminRecordClass.ECONOMIC_OBSERVATION,
            completeness=DataCompleteness.UNKNOWN,
            unknown_reason="cost_not_reported",
        )
    )
    as_of = now + timedelta(seconds=2)

    first = runtime.build_snapshot(
        AdminRecordInventoryProjection(),
        scope="global",
        as_of=as_of,
        generated_at=as_of + timedelta(seconds=1),
    )
    second = runtime.build_snapshot(
        AdminRecordInventoryProjection(),
        scope="global",
        as_of=as_of,
        generated_at=as_of + timedelta(seconds=20),
    )

    assert first.fingerprint == second.fingerprint
    assert first.snapshot_id == second.snapshot_id
    assert first.completeness is DataCompleteness.PARTIAL
    latest = store.latest_snapshot(first.projection_id, "global")
    assert latest is not None
    assert latest.fingerprint == first.fingerprint


def test_record_classes_remain_distinct(tmp_path: Path) -> None:
    store = SqliteAdminObservabilityStore(tmp_path / "admin.sqlite3")
    runtime = AdminProjectionRuntime(store)
    now = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    for index, record_class in enumerate(
        (
            AdminRecordClass.LOG_RECORD,
            AdminRecordClass.TRACE_RECORD,
            AdminRecordClass.ADMIN_METRIC_OBSERVATION,
            AdminRecordClass.OPERATIONAL_EVENT,
            AdminRecordClass.ECONOMIC_OBSERVATION,
        )
    ):
        runtime.ingest(
            _record(
                f"event:{index}",
                recorded_at=now + timedelta(seconds=index),
                record_class=record_class,
            )
        )

    snapshot = runtime.build_snapshot(
        AdminRecordInventoryProjection(),
        scope="global",
        as_of=now + timedelta(seconds=10),
        generated_at=now + timedelta(seconds=11),
        persist=False,
    )
    data = {item.key: item.value for item in snapshot.data}
    assert data["class:LOG_RECORD"] == "1"
    assert data["class:TRACE_RECORD"] == "1"
    assert data["class:ADMIN_METRIC_OBSERVATION"] == "1"
    assert data["class:OPERATIONAL_EVENT"] == "1"
    assert data["class:ECONOMIC_OBSERVATION"] == "1"


def test_invalid_correction_cannot_cross_owning_domain(tmp_path: Path) -> None:
    store = SqliteAdminObservabilityStore(tmp_path / "admin.sqlite3")
    runtime = AdminProjectionRuntime(store)
    now = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    runtime.ingest(_record("event:1", recorded_at=now))
    correction = _record(
        "event:2",
        recorded_at=now + timedelta(minutes=1),
        supersedes="event:1",
        owning_domain="other-domain",
    )
    with pytest.raises(AdminProjectionConflict, match="owning domain"):
        runtime.ingest(correction)
