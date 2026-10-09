"""SQLite persistence adapter for governed Observation Memory."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from application.economic_discovery.brain_contracts import ObservationMode, ObservationRecord
from application.economic_discovery.observation_memory import (
    GovernedObservation,
    ObservationAccessMetadata,
    ObservationAccessStatus,
    ObservationFieldState,
    ObservationMemoryConflict,
    ObservationReuseAuthority,
    ObservedField,
    observation_reuse_authority_from_payload,
    observation_reuse_authority_payload,
)


class SqliteObservationMemory:
    """Small durable append-only store behind the application persistence port."""

    def __init__(self, database_path: str | Path, *, read_only: bool = False) -> None:
        self._path = Path(database_path)
        self._read_only = read_only
        if read_only:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"{self._path.resolve().as_uri()}?mode=ro" if self._read_only else self._path,
            uri=self._read_only,
            timeout=10,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        restricted_reuse_json = json.dumps(
            observation_reuse_authority_payload(ObservationReuseAuthority()),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    content_fingerprint TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    raw_content TEXT,
                    raw_artifact_ref TEXT,
                    reuse_json TEXT NOT NULL,
                    CHECK (raw_content IS NOT NULL OR raw_artifact_ref IS NOT NULL)
                )
                """
            )
            columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(observations)").fetchall()
            }
            if "reuse_json" not in columns:
                connection.execute("ALTER TABLE observations ADD COLUMN reuse_json TEXT")
                connection.execute(
                    "UPDATE observations SET reuse_json = ? WHERE reuse_json IS NULL",
                    (restricted_reuse_json,),
                )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS observation_fields (
                    observation_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    field_value TEXT NOT NULL,
                    field_state TEXT NOT NULL DEFAULT 'VALUE',
                    competing_values_json TEXT NOT NULL DEFAULT '[]',
                    field_position INTEGER NOT NULL,
                    PRIMARY KEY (observation_id, field_name),
                    FOREIGN KEY (observation_id)
                        REFERENCES observations(observation_id)
                        ON DELETE RESTRICT
                )
                """
            )
            field_columns = {
                str(row[1])
                for row in connection.execute("PRAGMA table_info(observation_fields)").fetchall()
            }
            if "field_state" not in field_columns:
                connection.execute(
                    "ALTER TABLE observation_fields "
                    "ADD COLUMN field_state TEXT NOT NULL DEFAULT 'VALUE'"
                )
            if "competing_values_json" not in field_columns:
                connection.execute(
                    "ALTER TABLE observation_fields "
                    "ADD COLUMN competing_values_json TEXT NOT NULL DEFAULT '[]'"
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_observation_subject_time
                ON observations(subject_id, observed_at, observation_id)
                """
            )

    @staticmethod
    def _serialize(observation: GovernedObservation) -> tuple[object, ...]:
        record = observation.record
        return (
            record.observation_id,
            record.subject_id,
            record.source_ref,
            record.source_type,
            record.observed_at.astimezone(UTC).isoformat(),
            record.content_fingerprint,
            record.mode.value,
            observation.raw_content,
            observation.raw_artifact_ref,
            json.dumps(
                observation_reuse_authority_payload(observation.reuse_authority),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
        )

    @staticmethod
    def _deserialize(
        row: sqlite3.Row | tuple[object, ...],
        fields: tuple[ObservedField, ...],
    ) -> GovernedObservation:
        observation_id = str(row[0])
        return GovernedObservation(
            record=ObservationRecord(
                observation_id=observation_id,
                subject_id=str(row[1]),
                source_ref=str(row[2]),
                source_type=str(row[3]),
                observed_at=datetime.fromisoformat(str(row[4])),
                content_fingerprint=str(row[5]),
                mode=ObservationMode(str(row[6])),
            ),
            raw_content=None if row[7] is None else str(row[7]),
            raw_artifact_ref=None if row[8] is None else str(row[8]),
            fields=fields,
            reuse_authority=observation_reuse_authority_from_payload(json.loads(str(row[9]))),
        )

    def _load_by_id(
        self,
        connection: sqlite3.Connection,
        observation_id: str,
    ) -> GovernedObservation | None:
        row = connection.execute(
            """
            SELECT observation_id, subject_id, source_ref, source_type,
                   observed_at, content_fingerprint, mode, raw_content, raw_artifact_ref,
                   reuse_json
            FROM observations
            WHERE observation_id = ?
            """,
            (observation_id,),
        ).fetchone()
        if row is None:
            return None
        field_rows = connection.execute(
            """
            SELECT field_name, field_value, field_state, competing_values_json
            FROM observation_fields
            WHERE observation_id = ?
            ORDER BY field_position
            """,
            (observation_id,),
        ).fetchall()
        fields = tuple(
            ObservedField(
                str(item[0]),
                str(item[1]),
                ObservationFieldState(str(item[2])),
                tuple(str(value) for value in json.loads(str(item[3]))),
            )
            for item in field_rows
        )
        return self._deserialize(row, fields)

    def append(self, observation: GovernedObservation) -> bool:
        if not isinstance(observation, GovernedObservation):
            raise TypeError("Observation Memory accepts GovernedObservation instances only")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = self._load_by_id(connection, observation.record.observation_id)
            if existing is not None:
                if existing == observation:
                    return False
                raise ObservationMemoryConflict(
                    "observation id already exists with different governed content"
                )

            connection.execute(
                """
                INSERT INTO observations (
                    observation_id, subject_id, source_ref, source_type,
                    observed_at, content_fingerprint, mode, raw_content, raw_artifact_ref,
                    reuse_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._serialize(observation),
            )
            connection.executemany(
                """
                INSERT INTO observation_fields (
                    observation_id, field_name, field_value, field_state,
                    competing_values_json, field_position
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        observation.record.observation_id,
                        field.name,
                        field.value,
                        field.state.value,
                        json.dumps(
                            field.competing_values,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ),
                        position,
                    )
                    for position, field in enumerate(observation.fields)
                ),
            )
        return True

    def purge_first_observation_content(
        self,
        *,
        now: datetime,
        retain_until: Callable[[str, datetime], datetime | None],
    ) -> int:
        """Withdraw raw FO material when rights lapse; keep the historical envelope.

        Raw text becomes an empty non-evidentiary value so readers that require
        evidence ignore it. The reuse authority is withdrawn atomically.
        Does not mutate any observation outside the fo: namespace.
        """
        restricted = json.dumps(
            observation_reuse_authority_payload(
                ObservationReuseAuthority(
                    access_status=ObservationAccessStatus.INACCESSIBLE,
                )
            ),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        purged = 0
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """SELECT observation_id, source_ref, observed_at FROM observations
                WHERE observation_id LIKE 'fo:%' AND source_type='PUBLIC_WEBSITE'
                AND (raw_content != '' OR raw_artifact_ref IS NOT NULL)"""
            ).fetchall()
            for identifier, source_ref, observed_at in rows:
                expiry = retain_until(str(source_ref), datetime.fromisoformat(str(observed_at)))
                if expiry is not None and expiry > now:
                    continue
                connection.execute(
                    """UPDATE observations SET raw_content='', raw_artifact_ref=NULL,
                    reuse_json=? WHERE observation_id=?""",
                    (restricted, identifier),
                )
                purged += 1
        return purged

    def access_metadata(
        self,
        subject_id: str,
        observation_id: str,
    ) -> ObservationAccessMetadata | None:
        if not subject_id.strip() or not observation_id.strip():
            raise ValueError("observation access identity is required")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT observation_id, subject_id, source_ref, source_type, observed_at, content_fingerprint, mode, reuse_json "
                "FROM observations WHERE subject_id = ? AND observation_id = ?",
                (subject_id, observation_id),
            ).fetchone()
        if row is None:
            return None
        return ObservationAccessMetadata(
            record=ObservationRecord(
                observation_id=str(row[0]),
                subject_id=str(row[1]),
                source_ref=str(row[2]),
                source_type=str(row[3]),
                observed_at=datetime.fromisoformat(str(row[4])),
                content_fingerprint=str(row[5]),
                mode=ObservationMode(str(row[6])),
            ),
            reuse_authority=observation_reuse_authority_from_payload(json.loads(str(row[7]))),
        )

    def get_observation(
        self,
        subject_id: str,
        observation_id: str,
    ) -> GovernedObservation | None:
        if not subject_id.strip() or not observation_id.strip():
            raise ValueError("observation access identity is required")
        with self._connect() as connection:
            observation = self._load_by_id(connection, observation_id)
        if observation is None or observation.record.subject_id != subject_id:
            return None
        return observation

    def for_subject(self, subject_id: str) -> tuple[GovernedObservation, ...]:
        if not subject_id.strip():
            raise ValueError("observation subject identity is required")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT observation_id, subject_id, source_ref, source_type,
                       observed_at, content_fingerprint, mode, raw_content, raw_artifact_ref,
                       reuse_json
                FROM observations
                WHERE subject_id = ?
                ORDER BY observed_at, observation_id
                """,
                (subject_id,),
            ).fetchall()
            observations: list[GovernedObservation] = []
            for row in rows:
                observation_id = str(row[0])
                field_rows = connection.execute(
                    """
                    SELECT field_name, field_value, field_state, competing_values_json
                    FROM observation_fields
                    WHERE observation_id = ?
                    ORDER BY field_position
                    """,
                    (observation_id,),
                ).fetchall()
                fields = tuple(
                    ObservedField(
                        str(item[0]),
                        str(item[1]),
                        ObservationFieldState(str(item[2])),
                        tuple(str(value) for value in json.loads(str(item[3]))),
                    )
                    for item in field_rows
                )
                observations.append(self._deserialize(row, fields))
        return tuple(observations)
