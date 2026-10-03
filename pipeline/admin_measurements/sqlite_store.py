"""SQLite persistence for AO-24 governed measurement registry."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_measurements import (
    MeasurementDefinition,
    MeasurementObservation,
    MeasurementState,
    MeasurementUnit,
)


class MeasurementRegistryStoreConflict(ValueError):
    pass


class SqliteMeasurementRegistryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS measurement_definitions (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    measure_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(measure_id, version)
                );
                CREATE TABLE IF NOT EXISTS measurement_observations (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id TEXT NOT NULL UNIQUE,
                    measure_id TEXT NOT NULL,
                    definition_version INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_measurement_observation_measure
                    ON measurement_observations(measure_id, definition_version, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _definition_payload(definition: MeasurementDefinition) -> str:
        return json.dumps(
            {
                "measure_id": definition.measure_id,
                "version": definition.version,
                "label": definition.label,
                "question_served": definition.question_served,
                "decision_served": definition.decision_served,
                "formula_or_coding_rule": definition.formula_or_coding_rule,
                "unit": definition.unit.value,
                "source_family": definition.source_family,
                "instrument_id": definition.instrument_id,
                "instrument_version": definition.instrument_version,
                "subject_scope": definition.subject_scope,
                "default_window": definition.default_window,
                "freshness_seconds": definition.freshness_seconds,
                "minimum_sample_size": definition.minimum_sample_size,
                "uncertainty_policy": definition.uncertainty_policy,
                "compatibility_key": definition.compatibility_key,
                "interpretation_limits": list(definition.interpretation_limits),
                "evaluation_cases": list(definition.evaluation_cases),
                "effective_at": definition.effective_at.isoformat(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_definition(self, definition: MeasurementDefinition) -> bool:
        payload = self._definition_payload(definition)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM measurement_definitions "
                "WHERE measure_id = ? AND version = ?",
                (definition.measure_id, definition.version),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise MeasurementRegistryStoreConflict(
                    "measurement definition version reused with different content"
                )
            previous = connection.execute(
                "SELECT MAX(version) AS max_version FROM measurement_definitions "
                "WHERE measure_id = ?",
                (definition.measure_id,),
            ).fetchone()
            max_version = None if previous is None else previous["max_version"]
            if max_version is None and definition.version != 1:
                raise MeasurementRegistryStoreConflict(
                    "first measurement definition version must be 1"
                )
            if max_version is not None and definition.version != int(max_version) + 1:
                raise MeasurementRegistryStoreConflict(
                    "measurement definition version is out of sequence"
                )
            connection.execute(
                "INSERT INTO measurement_definitions(measure_id, version, payload_json) "
                "VALUES (?, ?, ?)",
                (definition.measure_id, definition.version, payload),
            )
        return True

    def definitions(self) -> tuple[MeasurementDefinition, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM measurement_definitions ORDER BY measure_id, version"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                MeasurementDefinition(
                    measure_id=p["measure_id"],
                    version=int(p["version"]),
                    label=p["label"],
                    question_served=p["question_served"],
                    decision_served=p["decision_served"],
                    formula_or_coding_rule=p["formula_or_coding_rule"],
                    unit=MeasurementUnit(p["unit"]),
                    source_family=p["source_family"],
                    instrument_id=p["instrument_id"],
                    instrument_version=p["instrument_version"],
                    subject_scope=p["subject_scope"],
                    default_window=p["default_window"],
                    freshness_seconds=int(p["freshness_seconds"]),
                    minimum_sample_size=int(p["minimum_sample_size"]),
                    uncertainty_policy=p["uncertainty_policy"],
                    compatibility_key=p["compatibility_key"],
                    interpretation_limits=tuple(p["interpretation_limits"]),
                    evaluation_cases=tuple(p["evaluation_cases"]),
                    effective_at=datetime.fromisoformat(p["effective_at"]),
                )
            )
        return tuple(result)

    @staticmethod
    def _observation_payload(observation: MeasurementObservation) -> str:
        return json.dumps(
            {
                "observation_id": observation.observation_id,
                "measure_id": observation.measure_id,
                "definition_version": observation.definition_version,
                "subject_ref": observation.subject_ref,
                "instrument_id": observation.instrument_id,
                "instrument_version": observation.instrument_version,
                "compatibility_key": observation.compatibility_key,
                "state": observation.state.value,
                "observed_at": observation.observed_at.isoformat(),
                "window_start": observation.window_start.isoformat(),
                "window_end": observation.window_end.isoformat(),
                "sample_size": observation.sample_size,
                "informative_sample_size": observation.informative_sample_size,
                "value": observation.value,
                "currency": observation.currency,
                "uncertainty": observation.uncertainty,
                "source_refs": list(observation.source_refs),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def append_observation(self, observation: MeasurementObservation) -> bool:
        payload = self._observation_payload(observation)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM measurement_observations WHERE observation_id = ?",
                (observation.observation_id,),
            ).fetchone()
            if row is not None:
                if str(row["payload_json"]) == payload:
                    return False
                raise MeasurementRegistryStoreConflict(
                    "measurement observation id reused with different content"
                )
            connection.execute(
                "INSERT INTO measurement_observations("
                "observation_id, measure_id, definition_version, payload_json"
                ") VALUES (?, ?, ?, ?)",
                (
                    observation.observation_id,
                    observation.measure_id,
                    observation.definition_version,
                    payload,
                ),
            )
        return True

    def observations(self) -> tuple[MeasurementObservation, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM measurement_observations ORDER BY sequence"
            ).fetchall()
        result = []
        for row in rows:
            p = json.loads(str(row["payload_json"]))
            result.append(
                MeasurementObservation(
                    observation_id=p["observation_id"],
                    measure_id=p["measure_id"],
                    definition_version=int(p["definition_version"]),
                    subject_ref=p["subject_ref"],
                    instrument_id=p["instrument_id"],
                    instrument_version=p["instrument_version"],
                    compatibility_key=p["compatibility_key"],
                    state=MeasurementState(p["state"]),
                    observed_at=datetime.fromisoformat(p["observed_at"]),
                    window_start=datetime.fromisoformat(p["window_start"]),
                    window_end=datetime.fromisoformat(p["window_end"]),
                    sample_size=p["sample_size"],
                    informative_sample_size=p["informative_sample_size"],
                    value=p["value"],
                    currency=p["currency"],
                    uncertainty=p["uncertainty"],
                    source_refs=tuple(p["source_refs"]),
                )
            )
        return tuple(result)
