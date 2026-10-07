"""SQLite adapter for EB-07 shared observation work."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from application.economic_discovery.continuous_observation import (
    ObservationWorkLease,
    ObservationWorkState,
    PrimeResearchAuthority,
    SharedObservationIntent,
    SharedObservationWork,
    require_shareable_requester_ref,
)
from application.economic_discovery.research_scheduler import (
    ResearchScheduleOutcome,
    ResearchScheduleState,
)


def _utc(value: datetime, label: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


class SqliteSharedObservationWorkMemory:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_observation_work (
                    work_key TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    state_fingerprint TEXT NOT NULL,
                    dimension_id TEXT NOT NULL,
                    missing_requirements_json TEXT NOT NULL,
                    research_policy_id TEXT NOT NULL,
                    research_policy_version TEXT NOT NULL,
                    research_context_fingerprint TEXT NOT NULL,
                    state TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_observation_requesters (
                    work_key TEXT NOT NULL,
                    requester_ref TEXT NOT NULL,
                    PRIMARY KEY (work_key, requester_ref),
                    FOREIGN KEY (work_key) REFERENCES shared_observation_work(work_key)
                        ON DELETE RESTRICT
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_observation_leases (
                    work_key TEXT PRIMARY KEY,
                    lease_token TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (work_key) REFERENCES shared_observation_work(work_key)
                        ON DELETE RESTRICT
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_observation_schedule (
                    work_key TEXT PRIMARY KEY,
                    attempt_count INTEGER NOT NULL,
                    no_progress_count INTEGER NOT NULL,
                    next_eligible_at TEXT NOT NULL,
                    last_outcome TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (work_key) REFERENCES shared_observation_work(work_key)
                        ON DELETE RESTRICT
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS prime_research_authority (
                    subject_id TEXT PRIMARY KEY,
                    state_fingerprint TEXT NOT NULL,
                    observation_watermark_at TEXT NOT NULL,
                    observation_watermark_id TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    temporal_policy_id TEXT NOT NULL,
                    temporal_policy_version TEXT NOT NULL
                )
                """
            )
            authority_columns = {
                str(row[1])
                for row in db.execute("PRAGMA table_info(prime_research_authority)").fetchall()
            }
            for column in (
                "observation_watermark_at",
                "observation_watermark_id",
                "valid_until",
                "temporal_policy_id",
                "temporal_policy_version",
            ):
                if column not in authority_columns:
                    db.execute(f"ALTER TABLE prime_research_authority ADD COLUMN {column} TEXT")

            db.execute(
                """
                CREATE TABLE IF NOT EXISTS prime_research_authorized_work (
                    subject_id TEXT NOT NULL,
                    state_fingerprint TEXT NOT NULL,
                    work_key TEXT NOT NULL,
                    PRIMARY KEY (subject_id, work_key),
                    FOREIGN KEY (subject_id) REFERENCES prime_research_authority(subject_id)
                        ON DELETE CASCADE
                )
                """
            )

    def replace_prime_authority(self, authority: PrimeResearchAuthority) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                INSERT INTO prime_research_authority(
                    subject_id, state_fingerprint, observation_watermark_at,
                    observation_watermark_id, valid_until, temporal_policy_id,
                    temporal_policy_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(subject_id) DO UPDATE SET
                    state_fingerprint=excluded.state_fingerprint,
                    observation_watermark_at=excluded.observation_watermark_at,
                    observation_watermark_id=excluded.observation_watermark_id,
                    valid_until=excluded.valid_until,
                    temporal_policy_id=excluded.temporal_policy_id,
                    temporal_policy_version=excluded.temporal_policy_version
                """,
                (
                    authority.subject_id,
                    authority.state_fingerprint,
                    authority.observation_watermark_at.astimezone(UTC).isoformat(),
                    authority.observation_watermark_id,
                    authority.valid_until.astimezone(UTC).isoformat(),
                    authority.temporal_policy_id,
                    authority.temporal_policy_version,
                ),
            )
            db.execute(
                "DELETE FROM prime_research_authorized_work WHERE subject_id=?",
                (authority.subject_id,),
            )
            db.executemany(
                """
                INSERT INTO prime_research_authorized_work(
                    subject_id, state_fingerprint, work_key
                ) VALUES (?, ?, ?)
                """,
                (
                    (authority.subject_id, authority.state_fingerprint, work_key)
                    for work_key in sorted(authority.authorized_work_keys)
                ),
            )

    def prime_authority(self, subject_id: str) -> PrimeResearchAuthority | None:
        if not subject_id.strip():
            raise ValueError("Prime research authority subject is required")
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM prime_research_authority WHERE subject_id=?",
                (subject_id,),
            ).fetchone()
            if row is None:
                return None
            required = (
                row["observation_watermark_at"],
                row["observation_watermark_id"],
                row["valid_until"],
                row["temporal_policy_id"],
                row["temporal_policy_version"],
            )
            if any(value is None for value in required):
                return None
            keys = db.execute(
                """
                SELECT work_key FROM prime_research_authorized_work
                WHERE subject_id=? AND state_fingerprint=?
                ORDER BY work_key
                """,
                (subject_id, str(row["state_fingerprint"])),
            ).fetchall()
        return PrimeResearchAuthority(
            subject_id=subject_id,
            state_fingerprint=str(row["state_fingerprint"]),
            authorized_work_keys=frozenset(str(item["work_key"]) for item in keys),
            observation_watermark_at=datetime.fromisoformat(str(row["observation_watermark_at"])),
            observation_watermark_id=str(row["observation_watermark_id"]),
            valid_until=datetime.fromisoformat(str(row["valid_until"])),
            temporal_policy_id=str(row["temporal_policy_id"]),
            temporal_policy_version=str(row["temporal_policy_version"]),
        )

    @staticmethod
    def _intent_from_row(row: sqlite3.Row) -> SharedObservationIntent:
        return SharedObservationIntent(
            subject_id=str(row["subject_id"]),
            state_fingerprint=str(row["state_fingerprint"]),
            dimension_id=str(row["dimension_id"]),
            missing_requirements=tuple(
                str(item) for item in json.loads(str(row["missing_requirements_json"]))
            ),
            research_policy_id=str(row["research_policy_id"]),
            research_policy_version=str(row["research_policy_version"]),
            research_context_fingerprint=str(row["research_context_fingerprint"]),
        )

    def enqueue(self, intent: SharedObservationIntent, requester_ref: str) -> bool:
        require_shareable_requester_ref(requester_ref)
        key = intent.work_key
        inserted = False
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM shared_observation_work WHERE work_key=?",
                (key,),
            ).fetchone()
            if row is None:
                db.execute(
                    """
                    INSERT INTO shared_observation_work (
                        work_key, subject_id, state_fingerprint, dimension_id,
                        missing_requirements_json, research_policy_id,
                        research_policy_version, research_context_fingerprint,
                        state, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        key,
                        intent.subject_id,
                        intent.state_fingerprint,
                        intent.dimension_id,
                        json.dumps(
                            sorted(intent.missing_requirements),
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ),
                        intent.research_policy_id,
                        intent.research_policy_version,
                        intent.research_context_fingerprint,
                        ObservationWorkState.PENDING.value,
                    ),
                )
                inserted = True
            elif self._intent_from_row(row) != intent:
                raise ValueError("shared work key collision with different governed intent")
            db.execute(
                """
                INSERT OR IGNORE INTO shared_observation_requesters (work_key, requester_ref)
                VALUES (?, ?)
                """,
                (key, requester_ref),
            )
        return inserted

    def get(self, work_key: str) -> SharedObservationWork | None:
        if not work_key.strip():
            raise ValueError("shared observation work key is required")
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM shared_observation_work WHERE work_key=?",
                (work_key,),
            ).fetchone()
            if row is None:
                return None
            requesters = db.execute(
                """
                SELECT requester_ref FROM shared_observation_requesters
                WHERE work_key=? ORDER BY requester_ref
                """,
                (work_key,),
            ).fetchall()
        completed = row["completed_at"]
        return SharedObservationWork(
            intent=self._intent_from_row(row),
            state=ObservationWorkState(str(row["state"])),
            requester_refs=tuple(str(item["requester_ref"]) for item in requesters),
            completed_at=None if completed is None else datetime.fromisoformat(str(completed)),
        )

    def get_schedule(self, work_key: str) -> ResearchScheduleState | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM shared_observation_schedule WHERE work_key=?",
                (work_key,),
            ).fetchone()
        if row is None:
            return None
        return ResearchScheduleState(
            work_key=str(row["work_key"]),
            attempt_count=int(row["attempt_count"]),
            no_progress_count=int(row["no_progress_count"]),
            next_eligible_at=datetime.fromisoformat(str(row["next_eligible_at"])),
            last_outcome=ResearchScheduleOutcome(str(row["last_outcome"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def record_schedule(self, state: ResearchScheduleState) -> None:
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO shared_observation_schedule (
                    work_key, attempt_count, no_progress_count, next_eligible_at,
                    last_outcome, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(work_key) DO UPDATE SET
                    attempt_count=excluded.attempt_count,
                    no_progress_count=excluded.no_progress_count,
                    next_eligible_at=excluded.next_eligible_at,
                    last_outcome=excluded.last_outcome,
                    updated_at=excluded.updated_at
                """,
                (
                    state.work_key,
                    state.attempt_count,
                    state.no_progress_count,
                    state.next_eligible_at.astimezone(UTC).isoformat(),
                    state.last_outcome.value,
                    state.updated_at.astimezone(UTC).isoformat(),
                ),
            )

    def pending_work_keys(self) -> tuple[str, ...]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT work_key FROM shared_observation_work
                WHERE state=? ORDER BY work_key
                """,
                (ObservationWorkState.PENDING.value,),
            ).fetchall()
        return tuple(str(row["work_key"]) for row in rows)

    def claim(
        self,
        work_key: str,
        *,
        now: datetime,
        lease_for: timedelta,
    ) -> ObservationWorkLease | None:
        now_utc = _utc(now, "lease claim time")
        if lease_for <= timedelta(0):
            raise ValueError("lease duration must be positive")
        expires = now_utc + lease_for
        token = f"lease:{uuid.uuid4().hex}"
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            work = db.execute(
                "SELECT state FROM shared_observation_work WHERE work_key=?",
                (work_key,),
            ).fetchone()
            if work is None:
                raise LookupError(work_key)
            if str(work["state"]) != ObservationWorkState.PENDING.value:
                return None
            existing = db.execute(
                "SELECT lease_token, expires_at FROM shared_observation_leases WHERE work_key=?",
                (work_key,),
            ).fetchone()
            if existing is not None:
                existing_expires = datetime.fromisoformat(str(existing["expires_at"]))
                if existing_expires > now_utc:
                    return None
                db.execute(
                    "DELETE FROM shared_observation_leases WHERE work_key=?",
                    (work_key,),
                )
            db.execute(
                """
                INSERT INTO shared_observation_leases
                (work_key, lease_token, acquired_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (work_key, token, now_utc.isoformat(), expires.isoformat()),
            )
        return ObservationWorkLease(work_key, token, now_utc, expires)

    def complete(
        self,
        work_key: str,
        lease_token: str,
        *,
        completed_at: datetime,
    ) -> bool:
        completed = _utc(completed_at, "work completion time")
        if not lease_token.strip():
            raise ValueError("lease token is required")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            work = db.execute(
                "SELECT state FROM shared_observation_work WHERE work_key=?",
                (work_key,),
            ).fetchone()
            if work is None:
                raise LookupError(work_key)
            if str(work["state"]) == ObservationWorkState.COMPLETE.value:
                return False
            lease = db.execute(
                """
                SELECT lease_token, expires_at FROM shared_observation_leases
                WHERE work_key=?
                """,
                (work_key,),
            ).fetchone()
            if (
                lease is None
                or str(lease["lease_token"]) != lease_token
                or datetime.fromisoformat(str(lease["expires_at"])) <= completed
            ):
                return False
            db.execute(
                """
                UPDATE shared_observation_work
                SET state=?, completed_at=?
                WHERE work_key=? AND state=?
                """,
                (
                    ObservationWorkState.COMPLETE.value,
                    completed.isoformat(),
                    work_key,
                    ObservationWorkState.PENDING.value,
                ),
            )
            db.execute(
                "DELETE FROM shared_observation_leases WHERE work_key=? AND lease_token=?",
                (work_key, lease_token),
            )
        return True

    def release(self, work_key: str, lease_token: str) -> bool:
        if not lease_token.strip():
            raise ValueError("lease token is required")
        with self._connect() as db:
            cursor = db.execute(
                "DELETE FROM shared_observation_leases WHERE work_key=? AND lease_token=?",
                (work_key, lease_token),
            )
        return cursor.rowcount == 1
