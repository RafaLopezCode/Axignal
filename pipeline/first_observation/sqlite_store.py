"""SQLite operational state of the First Observation loop (spec 063).

Three kinds of rows, none of them AXIGLAND truth:

* ``fo_sites``  — world-level site readings, one per website (origin and path; public data);
* ``fo_jobs``   — durable, leased, idempotent First Observation work items;
* ``fo_proofs`` — tenant-private First Proof per attention target.

Every stored time is UTC, so lease, due and daily comparisons are exact.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.first_observation.contracts import (
    AttentionTarget,
    FirstProof,
    JobState,
    ObservationJob,
    SiteReading,
)

#: Failed attempts wait 2, 4, 8... minutes before a retry (transient faults clear).
_BACKOFF_MINUTES = 2


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("first observation times must be timezone-aware")
    return value.astimezone(UTC).isoformat()


class SqliteFirstObservationStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS fo_sites (
                    origin TEXT PRIMARY KEY,
                    reading TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fo_jobs (
                    job_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    target TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('QUEUED','RUNNING','DONE','FAILED')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    lease_token TEXT,
                    lease_expires_at TEXT,
                    not_before TEXT,
                    claimed_at TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_fo_jobs_state ON fo_jobs(state, created_at);
                CREATE INDEX IF NOT EXISTS idx_fo_jobs_target ON fo_jobs(tenant_id, target_ref);
                CREATE TABLE IF NOT EXISTS fo_proofs (
                    tenant_id TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    organization_id TEXT,
                    state TEXT NOT NULL,
                    ready INTEGER NOT NULL,
                    proof TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    next_due_at TEXT,
                    retain_until TEXT,
                    PRIMARY KEY (tenant_id, target_ref)
                );
                CREATE TABLE IF NOT EXISTS fo_understanding_history (
                    tenant_id TEXT NOT NULL,
                    target_ref TEXT NOT NULL,
                    organization_id TEXT,
                    report_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    retain_until TEXT,
                    report TEXT NOT NULL,
                    PRIMARY KEY (tenant_id, target_ref, report_id)
                );
                CREATE INDEX IF NOT EXISTS idx_fo_understanding_history_scope
                    ON fo_understanding_history(tenant_id, target_ref, organization_id, observed_at);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.execute("ROLLBACK")
                raise
            db.execute("COMMIT")

    # ---- world-level site readings --------------------------------------------------
    def site(self, key: str) -> SiteReading | None:
        with self._connect() as db:
            row = db.execute("SELECT reading FROM fo_sites WHERE origin=?", (key,)).fetchone()
        return None if row is None else SiteReading.from_wire(json.loads(row["reading"]))

    def save_site(self, reading: SiteReading) -> None:
        with self._transaction() as db:
            db.execute(
                """INSERT INTO fo_sites VALUES (?,?,?,?)
                ON CONFLICT(origin) DO UPDATE SET reading=excluded.reading,
                observed_at=excluded.observed_at, fingerprint=excluded.fingerprint
                WHERE excluded.observed_at >= fo_sites.observed_at""",
                (
                    reading.origin,
                    json.dumps(reading.to_wire(), ensure_ascii=False, sort_keys=True),
                    _iso(reading.observed_at),
                    reading.fingerprint,
                ),
            )

    # ---- durable jobs ---------------------------------------------------------------
    @staticmethod
    def job_id(target: AttentionTarget, key: str) -> str:
        raw = f"{target.tenant_id}|{target.target_ref}|{target.website}|{key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def enqueue(self, target: AttentionTarget, *, key: str, now: datetime) -> tuple[str, bool]:
        """Idempotent: the same (target, website, key) is one job forever."""
        job_id = self.job_id(target, key)
        payload = json.dumps(target.to_wire(), sort_keys=True)
        with self._transaction() as db:
            cursor = db.execute(
                """INSERT OR IGNORE INTO fo_jobs
                (job_id, tenant_id, target_ref, target, state, attempts, created_at, updated_at)
                VALUES (?,?,?,?, 'QUEUED', 0, ?, ?)""",
                (job_id, target.tenant_id, target.target_ref, payload, _iso(now), _iso(now)),
            )
        return job_id, cursor.rowcount == 1

    def jobs_for(self, tenant_id: str, target_ref: str) -> tuple[str, ...]:
        """States of every job of one target, oldest first."""
        with self._connect() as db:
            rows = db.execute(
                """SELECT state FROM fo_jobs WHERE tenant_id=? AND target_ref=?
                ORDER BY created_at, job_id""",
                (tenant_id, target_ref),
            ).fetchall()
        return tuple(str(row["state"]) for row in rows)

    def claim(
        self, *, now: datetime, lease_seconds: int, max_attempts: int
    ) -> ObservationJob | None:
        token = secrets.token_hex(16)
        at = _iso(now)
        with self._transaction() as db:
            # A worker that died on the last attempt must not leave the job RUNNING forever.
            db.execute(
                """UPDATE fo_jobs SET state='FAILED', lease_token=NULL, lease_expires_at=NULL,
                last_error='LEASE_EXPIRED_ON_LAST_ATTEMPT', updated_at=?
                WHERE state='RUNNING' AND lease_expires_at < ? AND attempts >= ?""",
                (at, at, max_attempts),
            )
            row = db.execute(
                """SELECT * FROM fo_jobs WHERE attempts < ? AND (
                (state='QUEUED' AND (not_before IS NULL OR not_before <= ?))
                OR (state='RUNNING' AND lease_expires_at < ?))
                ORDER BY created_at, job_id LIMIT 1""",
                (max_attempts, at, at),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                """UPDATE fo_jobs SET state='RUNNING', attempts=attempts+1, lease_token=?,
                lease_expires_at=?, claimed_at=?, updated_at=? WHERE job_id=?""",
                (token, _iso(now + timedelta(seconds=lease_seconds)), at, at, row["job_id"]),
            )
        return ObservationJob(
            job_id=str(row["job_id"]),
            target=AttentionTarget.from_wire(json.loads(row["target"])),
            state=JobState.RUNNING,
            attempts=int(row["attempts"]) + 1,
            created_at=datetime.fromisoformat(str(row["created_at"])),
            lease_token=token,
        )

    def jobs_created_today(self, tenant_id: str, now: datetime) -> int:
        """Jobs one tenant created on the current UTC day (per-tenant fairness cap)."""
        day = _iso(now)[:10]
        with self._connect() as db:
            row = db.execute(
                "SELECT COUNT(*) FROM fo_jobs WHERE tenant_id=? AND substr(created_at,1,10)=?",
                (tenant_id, day),
            ).fetchone()
        return int(row[0])

    def jobs_started_on(self, day: str) -> int:
        """Jobs claimed on one UTC day (``YYYY-MM-DD``): the daily ceiling."""
        with self._connect() as db:
            row = db.execute(
                "SELECT COUNT(*) FROM fo_jobs WHERE substr(claimed_at,1,10)=?", (day,)
            ).fetchone()
        return int(row[0])

    def complete(self, job: ObservationJob, proof: FirstProof, *, now: datetime) -> bool:
        """Persist the proof only while this worker still owns the job's lease."""
        target = proof.target
        proof_wire = proof.to_wire()
        understanding = proof_wire.get("publicUnderstanding")
        report_payload: dict[str, Any] | None = None
        report_id: str | None = None
        report_at: str | None = None
        if understanding is not None:
            if not isinstance(understanding, Mapping):
                raise ValueError("public understanding must be a mapping")
            raw_report_id = understanding.get("reportId")
            raw_measured_at = understanding.get("measuredAt")
            if not isinstance(raw_report_id, str) or not raw_report_id.strip():
                raise ValueError("public understanding reportId is required")
            if not isinstance(raw_measured_at, str) or not raw_measured_at.strip():
                raise ValueError("public understanding measuredAt is required")
            try:
                parsed_report_at = datetime.fromisoformat(raw_measured_at)
            except ValueError as error:
                raise ValueError("public understanding measuredAt must be ISO-8601") from error
            report_id = raw_report_id
            report_at = _iso(parsed_report_at)
            report_payload = dict(understanding)
            source_expiry = report_payload.get("contentExpiresAt")
            if source_expiry is not None:
                if not isinstance(source_expiry, str):
                    raise ValueError("public understanding contentExpiresAt must be ISO-8601")
                try:
                    source_expiry_at = datetime.fromisoformat(source_expiry)
                except ValueError as error:
                    raise ValueError(
                        "public understanding contentExpiresAt must be ISO-8601"
                    ) from error
                _iso(source_expiry_at)
            else:
                source_expiry_at = None
            expiries = [
                value for value in (proof.retain_until, source_expiry_at) if value is not None
            ]
            report_payload["contentExpiresAt"] = None if not expiries else _iso(min(expiries))
            proof_wire["publicUnderstanding"] = report_payload
        with self._transaction() as db:
            owned = db.execute(
                "SELECT 1 FROM fo_jobs WHERE job_id=? AND state='RUNNING' AND lease_token=?",
                (job.job_id, job.lease_token),
            ).fetchone()
            if owned is None:
                return False
            db.execute(
                """UPDATE fo_jobs SET state='DONE', lease_token=NULL, lease_expires_at=NULL,
                updated_at=? WHERE job_id=?""",
                (_iso(now), job.job_id),
            )
            db.execute(
                """INSERT INTO fo_proofs VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(tenant_id, target_ref) DO UPDATE SET
                organization_id=excluded.organization_id, state=excluded.state,
                ready=excluded.ready, proof=excluded.proof, observed_at=excluded.observed_at,
                next_due_at=excluded.next_due_at, retain_until=excluded.retain_until""",
                (
                    target.tenant_id,
                    target.target_ref,
                    target.organization_id,
                    proof.state.value,
                    int(proof.ready),
                    json.dumps(proof_wire, ensure_ascii=False, sort_keys=True),
                    _iso(proof.observed_at),
                    None if proof.next_due_at is None else _iso(proof.next_due_at),
                    None if proof.retain_until is None else _iso(proof.retain_until),
                ),
            )
            if report_payload is not None and report_id is not None and report_at is not None:
                db.execute(
                    """INSERT OR IGNORE INTO fo_understanding_history
                    (tenant_id, target_ref, organization_id, report_id, observed_at,
                     retain_until, report) VALUES (?,?,?,?,?,?,?)""",
                    (
                        target.tenant_id,
                        target.target_ref,
                        target.organization_id,
                        report_id,
                        report_at,
                        report_payload["contentExpiresAt"],
                        json.dumps(report_payload, ensure_ascii=False, sort_keys=True),
                    ),
                )
                old_rows = db.execute(
                    """SELECT report_id FROM fo_understanding_history
                    WHERE tenant_id=? AND target_ref=? AND organization_id IS ?
                    ORDER BY observed_at DESC, report_id DESC LIMIT -1 OFFSET 8""",
                    (target.tenant_id, target.target_ref, target.organization_id),
                ).fetchall()
                db.executemany(
                    """DELETE FROM fo_understanding_history WHERE tenant_id=? AND target_ref=?
                    AND report_id=?""",
                    [(target.tenant_id, target.target_ref, row["report_id"]) for row in old_rows],
                )
        return True

    def purge(self, *, now: datetime) -> dict[str, int]:
        """Enforce retention: shared site text and private citations past their time."""
        at = _iso(now)
        sites = proofs = 0
        with self._transaction() as db:
            for row in db.execute("SELECT origin, reading FROM fo_sites").fetchall():
                reading = SiteReading.from_wire(json.loads(row["reading"]))
                if reading.shared_until is not None and _iso(reading.shared_until) <= at:
                    stripped = reading.without_content()
                    db.execute(
                        "UPDATE fo_sites SET reading=? WHERE origin=?",
                        (
                            json.dumps(stripped.to_wire(), ensure_ascii=False, sort_keys=True),
                            row["origin"],
                        ),
                    )
                    sites += 1
            for row in db.execute(
                """SELECT tenant_id, target_ref, proof, retain_until FROM fo_proofs"""
            ).fetchall():
                proof = json.loads(row["proof"])
                proof_expired = row["retain_until"] is not None and str(row["retain_until"]) <= at
                understanding = proof.get("publicUnderstanding")
                understanding_expired = proof_expired
                if isinstance(understanding, dict) and not understanding_expired:
                    content_expiry = understanding.get("contentExpiresAt")
                    if isinstance(content_expiry, str):
                        try:
                            understanding_expired = (
                                _iso(datetime.fromisoformat(content_expiry)) <= at
                            )
                        except ValueError:
                            understanding_expired = True
                if not proof_expired and not understanding_expired:
                    continue
                if proof_expired:
                    for discovery in proof.get("discoveries", ()):
                        discovery["excerpt"] = None
                    for capability in proof.get("capabilities", ()):
                        capability.get("basis", {})["excerpt"] = None
                if isinstance(understanding, dict) and understanding_expired:
                    proof["publicUnderstanding"] = {
                        key: understanding[key]
                        for key in (
                            "reportId",
                            "measuredAt",
                            "validUntil",
                            "contentExpiresAt",
                            "instrument",
                            "conditions",
                            "authority",
                            "execution",
                            "coverage",
                        )
                        if key in understanding
                    } | {
                        "status": "NOT_MEASURED",
                        "cause": "CONTENT_EXPIRED",
                        "currentness": "EXPIRED",
                        "citations": [],
                        "dimensions": [],
                    }
                if proof_expired:
                    proof["contentExpiredAt"] = at
                db.execute(
                    """UPDATE fo_proofs SET proof=?, retain_until=?
                    WHERE tenant_id=? AND target_ref=?""",
                    (
                        json.dumps(proof, ensure_ascii=False, sort_keys=True),
                        None if proof_expired else row["retain_until"],
                        row["tenant_id"],
                        row["target_ref"],
                    ),
                )  # fmt: skip
                proofs += 1
            db.execute(
                """DELETE FROM fo_understanding_history
                WHERE retain_until IS NOT NULL AND retain_until <= ?""",
                (at,),
            )
        return {"siteReadings": sites, "proofs": proofs}

    def fail(self, job: ObservationJob, *, error: str, now: datetime, retry: bool) -> None:
        """Retry later with backoff, or fail for good and stop scheduling re-checks."""
        not_before = (
            _iso(now + timedelta(minutes=_BACKOFF_MINUTES ** max(1, job.attempts)))
            if retry
            else None
        )
        with self._transaction() as db:
            db.execute(
                """UPDATE fo_jobs SET state=?, lease_token=NULL, lease_expires_at=NULL,
                not_before=?, last_error=?, updated_at=? WHERE job_id=? AND lease_token=?""",
                (
                    "QUEUED" if retry else "FAILED",
                    not_before,
                    error[:200],
                    _iso(now),
                    job.job_id,
                    job.lease_token,
                ),
            )
            if not retry:
                db.execute(
                    "UPDATE fo_proofs SET next_due_at=NULL WHERE tenant_id=? AND target_ref=?",
                    (job.target.tenant_id, job.target.target_ref),
                )

    # ---- tenant-private reads ---------------------------------------------------------
    def proof(self, tenant_id: str, target_ref: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT proof FROM fo_proofs WHERE tenant_id=? AND target_ref=?",
                (tenant_id, target_ref),
            ).fetchone()
        return None if row is None else dict(json.loads(row["proof"]))

    def history(
        self,
        tenant_id: str,
        target_ref: str,
        organization_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        """Latest bounded reports for exactly one tenant, target, and Organization."""
        if not 1 <= limit <= 8:
            raise ValueError("understanding history limit must be between 1 and 8")
        with self._connect() as db:
            rows = db.execute(
                """SELECT report FROM fo_understanding_history
                WHERE tenant_id=? AND target_ref=? AND organization_id IS ?
                ORDER BY observed_at DESC, report_id DESC LIMIT ?""",
                (tenant_id, target_ref, organization_id, limit),
            ).fetchall()
        return [dict(json.loads(row["report"])) for row in rows]

    def status(self, tenant_id: str, target_ref: str) -> str | None:
        """Open work, else a failure newer than the proof, else the proof state."""
        with self._connect() as db:
            job = db.execute(
                """SELECT state, updated_at FROM fo_jobs WHERE tenant_id=? AND target_ref=?
                ORDER BY created_at DESC, updated_at DESC LIMIT 1""",
                (tenant_id, target_ref),
            ).fetchone()
            proof = db.execute(
                "SELECT state, observed_at FROM fo_proofs WHERE tenant_id=? AND target_ref=?",
                (tenant_id, target_ref),
            ).fetchone()
        if job is not None and job["state"] == "QUEUED":
            return "QUEUED"
        if job is not None and job["state"] == "RUNNING":
            return "OBSERVING_PUBLIC_PRESENCE"
        if (
            job is not None
            and job["state"] == "FAILED"
            and (proof is None or str(job["updated_at"]) > str(proof["observed_at"]))
        ):
            return "OBSERVATION_FAILED"
        return None if proof is None else str(proof["state"])

    def observed_targets(self, tenant_id: str) -> frozenset[str]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT target_ref FROM fo_jobs WHERE tenant_id=?
                UNION SELECT target_ref FROM fo_proofs WHERE tenant_id=?""",
                (tenant_id, tenant_id),
            ).fetchall()
        return frozenset(str(row["target_ref"]) for row in rows)

    def due(self, *, now: datetime, limit: int = 100) -> tuple[AttentionTarget, ...]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT proof FROM fo_proofs WHERE next_due_at IS NOT NULL
                AND next_due_at <= ? ORDER BY next_due_at LIMIT ?""",
                (_iso(now), limit),
            ).fetchall()
        return tuple(AttentionTarget.from_wire(json.loads(row["proof"])["target"]) for row in rows)

    def proofs(self) -> tuple[dict[str, Any], ...]:
        """Every stored proof (operator metrics). Contains tenant-private derived state."""
        with self._connect() as db:
            rows = db.execute("SELECT proof FROM fo_proofs ORDER BY observed_at").fetchall()
        return tuple(dict(json.loads(row["proof"])) for row in rows)
