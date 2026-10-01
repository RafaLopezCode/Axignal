"""Deterministic Admin observability ingestion and temporal projection runtime."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from domain.admin_observability import (
    AdminEventEnvelope,
    AdminObservabilityError,
    AdminProjectionId,
    AdminProjectionSnapshot,
    AdminProjectionSnapshotId,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
    ProjectionDatum,
)


class AdminProjectionConflict(RuntimeError):
    """Raised when replay/correction semantics become ambiguous."""


class AdminObservabilityStore(Protocol):
    def append_record(self, record: AdminEventEnvelope) -> bool: ...

    def get_record(self, record_id: AdminRecordId) -> AdminEventEnvelope | None: ...

    def records_through(self, as_of: datetime) -> tuple[AdminEventEnvelope, ...]: ...

    def append_snapshot(self, snapshot: AdminProjectionSnapshot) -> bool: ...

    def latest_snapshot(
        self, projection_id: AdminProjectionId, scope: str
    ) -> AdminProjectionSnapshot | None: ...


@dataclass(frozen=True, slots=True)
class AdminProjectionDefinition:
    projection_id: AdminProjectionId
    schema_version: int
    supported_classes: frozenset[AdminRecordClass]

    def __post_init__(self) -> None:
        if not str(self.projection_id).strip():
            raise AdminObservabilityError("projection_id is required")
        if self.schema_version < 1:
            raise AdminObservabilityError("projection schema_version must be >= 1")
        if not self.supported_classes:
            raise AdminObservabilityError("projection requires at least one record class")


@dataclass(frozen=True, slots=True)
class AdminProjectionResult:
    completeness: DataCompleteness
    data: tuple[ProjectionDatum, ...]


class AdminProjectionReducer(Protocol):
    @property
    def definition(self) -> AdminProjectionDefinition: ...

    def reduce(
        self,
        records: tuple[AdminEventEnvelope, ...],
        *,
        scope: str,
        as_of: datetime,
    ) -> AdminProjectionResult: ...


class AdminRecordInventoryProjection:
    """Minimal substrate projection used to prove replay semantics.

    AO-04+ may add purpose-built projections, but they must consume the same
    envelope/runtime contract rather than inventing route-local aggregation.
    """

    definition = AdminProjectionDefinition(
        projection_id=AdminProjectionId("admin-record-inventory"),
        schema_version=1,
        supported_classes=frozenset(AdminRecordClass),
    )

    def reduce(
        self,
        records: tuple[AdminEventEnvelope, ...],
        *,
        scope: str,
        as_of: datetime,
    ) -> AdminProjectionResult:
        del scope, as_of
        counts = {record_class: 0 for record_class in AdminRecordClass}
        completeness = DataCompleteness.KNOWN
        for record in records:
            counts[record.record_class] += 1
            if record.completeness in {
                DataCompleteness.UNKNOWN,
                DataCompleteness.UNAVAILABLE,
            } or (
                record.completeness is DataCompleteness.PARTIAL
                and completeness is DataCompleteness.KNOWN
            ):
                completeness = DataCompleteness.PARTIAL
        data = [
            ProjectionDatum(key="record_count", value=str(len(records))),
            ProjectionDatum(
                key="last_recorded_at",
                value="" if not records else records[-1].recorded_at.isoformat(),
            ),
        ]
        data.extend(
            ProjectionDatum(key=f"class:{record_class.value}", value=str(counts[record_class]))
            for record_class in AdminRecordClass
        )
        return AdminProjectionResult(completeness=completeness, data=tuple(data))


def _projection_fingerprint(
    *,
    definition: AdminProjectionDefinition,
    scope: str,
    as_of: datetime,
    completeness: DataCompleteness,
    source_record_ids: tuple[AdminRecordId, ...],
    data: tuple[ProjectionDatum, ...],
) -> str:
    payload = {
        "projection_id": definition.projection_id,
        "schema_version": definition.schema_version,
        "scope": scope,
        "as_of": as_of.isoformat(),
        "completeness": completeness.value,
        "source_record_ids": list(source_record_ids),
        "data": [{"key": item.key, "value": item.value} for item in data],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class AdminProjectionRuntime:
    """Ingest metadata and build deterministic temporal read models."""

    def __init__(self, store: AdminObservabilityStore) -> None:
        self._store = store

    def ingest(self, record: AdminEventEnvelope) -> bool:
        """Persist once; exact replay is idempotent, conflicting replay fails."""

        if record.supersedes_record_id is not None:
            target = self._store.get_record(record.supersedes_record_id)
            if target is None:
                raise AdminProjectionConflict("correction target does not exist")
            if target.recorded_at > record.recorded_at:
                raise AdminProjectionConflict("correction cannot precede its target")
            if target.owning_domain != record.owning_domain:
                raise AdminProjectionConflict("correction cannot change owning domain")
            if target.record_type != record.record_type:
                raise AdminProjectionConflict("correction cannot change record type")
        return self._store.append_record(record)

    def build_snapshot(
        self,
        reducer: AdminProjectionReducer,
        *,
        scope: str,
        as_of: datetime,
        generated_at: datetime,
        persist: bool = True,
    ) -> AdminProjectionSnapshot:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("projection as_of must be timezone-aware")
        if generated_at.tzinfo is None or generated_at.utcoffset() is None:
            raise ValueError("projection generated_at must be timezone-aware")
        if generated_at < as_of:
            raise ValueError("projection cannot be generated before as_of")

        recorded = self._store.records_through(as_of)
        effective = self._effective_records(recorded)
        supported = tuple(
            record
            for record in effective
            if record.record_class in reducer.definition.supported_classes
        )
        result = reducer.reduce(supported, scope=scope, as_of=as_of)
        source_ids = tuple(record.record_id for record in supported)
        fingerprint = _projection_fingerprint(
            definition=reducer.definition,
            scope=scope,
            as_of=as_of,
            completeness=result.completeness,
            source_record_ids=source_ids,
            data=result.data,
        )
        snapshot = AdminProjectionSnapshot(
            snapshot_id=AdminProjectionSnapshotId(
                f"{reducer.definition.projection_id}:{fingerprint.removeprefix('sha256:')[:32]}"
            ),
            projection_id=reducer.definition.projection_id,
            schema_version=reducer.definition.schema_version,
            scope=scope,
            as_of=as_of,
            generated_at=generated_at,
            completeness=result.completeness,
            source_record_ids=source_ids,
            data=result.data,
            fingerprint=fingerprint,
        )
        if persist:
            self._store.append_snapshot(snapshot)
        return snapshot

    @staticmethod
    def _effective_records(
        records: tuple[AdminEventEnvelope, ...],
    ) -> tuple[AdminEventEnvelope, ...]:
        superseded = {
            record.supersedes_record_id
            for record in records
            if record.supersedes_record_id is not None
        }
        return tuple(record for record in records if record.record_id not in superseded)
