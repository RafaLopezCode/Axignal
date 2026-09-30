"""SQLite adapter for append-only policy governance history."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from application.economic_discovery.policy_governance import (
    ActivePolicyRef,
    GovernanceAction,
    PolicyDecisionKind,
    PolicyDecisionRecord,
    PolicyGovernanceConflict,
    RolloutMode,
    RolloutPlan,
)


def _policy_payload(policy: ActivePolicyRef) -> dict[str, object]:
    return {
        "policy_family": policy.policy_family,
        "policy_id": policy.policy_id,
        "policy_version": policy.policy_version,
        "code_sha": policy.code_sha,
        "candidate_fingerprint": policy.candidate_fingerprint,
    }


def _policy_from_payload(data: dict[str, object]) -> ActivePolicyRef:
    return ActivePolicyRef(
        policy_family=str(data["policy_family"]),
        policy_id=str(data["policy_id"]),
        policy_version=str(data["policy_version"]),
        code_sha=str(data["code_sha"]),
        candidate_fingerprint=(
            None
            if data.get("candidate_fingerprint") is None
            else str(data["candidate_fingerprint"])
        ),
    )


def _record_payload(record: PolicyDecisionRecord) -> str:
    payload = asdict(record)
    payload["kind"] = record.kind.value
    payload["decided_at"] = record.decided_at.isoformat()
    payload["approved_at"] = record.approved_at.isoformat()
    payload["approval_action"] = record.approval_action.value
    payload["rollout"]["mode"] = record.rollout.mode.value
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _record_from_payload(payload_json: str) -> PolicyDecisionRecord:
    data = json.loads(payload_json)
    rollout = data["rollout"]
    return PolicyDecisionRecord(
        decision_id=str(data["decision_id"]),
        kind=PolicyDecisionKind(data["kind"]),
        policy_family=str(data["policy_family"]),
        decided_at=datetime.fromisoformat(str(data["decided_at"])),
        approved_by=str(data["approved_by"]),
        approved_at=datetime.fromisoformat(str(data["approved_at"])),
        approval_rationale=str(data["approval_rationale"]),
        approval_id=str(data["approval_id"]),
        approval_action=GovernanceAction(data["approval_action"]),
        from_policy=_policy_from_payload(data["from_policy"]),
        to_policy=_policy_from_payload(data["to_policy"]),
        reason_code=str(data["reason_code"]),
        gate_policy_id=str(data["gate_policy_id"]),
        gate_policy_version=str(data["gate_policy_version"]),
        rollout=RolloutPlan(
            mode=RolloutMode(rollout["mode"]),
            canary_percent=rollout.get("canary_percent"),
        ),
        candidate_id=str(data["candidate_id"]),
        candidate_fingerprint=str(data["candidate_fingerprint"]),
        comparison_fingerprint=str(data["comparison_fingerprint"]),
        previous_decision_id=(
            None if data.get("previous_decision_id") is None else str(data["previous_decision_id"])
        ),
        rollback_of=None if data.get("rollback_of") is None else str(data["rollback_of"]),
    )


class SqliteActivePolicyStore:
    """Atomic current-policy pointer backed by immutable decision history."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS policy_decisions (
                    decision_id TEXT PRIMARY KEY,
                    policy_family TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_policy_decisions_family_time
                    ON policy_decisions(policy_family, decided_at, decision_id);

                CREATE TABLE IF NOT EXISTS active_policies (
                    policy_family TEXT PRIMARY KEY,
                    policy_json TEXT NOT NULL,
                    latest_decision_id TEXT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def seed_active(self, policy: ActivePolicyRef) -> bool:
        """Establish the pre-governance baseline once; never overwrite it."""

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT policy_json, latest_decision_id FROM active_policies "
                "WHERE policy_family = ?",
                (policy.policy_family,),
            ).fetchone()
            if existing is not None:
                loaded = _policy_from_payload(json.loads(existing["policy_json"]))
                if loaded == policy and existing["latest_decision_id"] is None:
                    connection.commit()
                    return False
                raise PolicyGovernanceConflict("active policy family is already initialized")
            history = connection.execute(
                "SELECT 1 FROM policy_decisions WHERE policy_family = ? LIMIT 1",
                (policy.policy_family,),
            ).fetchone()
            if history is not None:
                raise PolicyGovernanceConflict(
                    "cannot seed active policy after governance history exists"
                )
            connection.execute(
                "INSERT INTO active_policies(policy_family, policy_json, latest_decision_id) "
                "VALUES (?, ?, NULL)",
                (
                    policy.policy_family,
                    json.dumps(
                        _policy_payload(policy),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
            connection.commit()
            return True

    def current(self, policy_family: str) -> ActivePolicyRef | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT policy_json FROM active_policies WHERE policy_family = ?",
                (policy_family,),
            ).fetchone()
        if row is None:
            return None
        return _policy_from_payload(json.loads(row["policy_json"]))

    def latest_decision(self, policy_family: str) -> PolicyDecisionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT latest_decision_id FROM active_policies WHERE policy_family = ?",
                (policy_family,),
            ).fetchone()
        if row is None or row["latest_decision_id"] is None:
            return None
        return self.get_decision(str(row["latest_decision_id"]))

    def get_decision(self, decision_id: str) -> PolicyDecisionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM policy_decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
        if row is None:
            return None
        return _record_from_payload(str(row["payload_json"]))

    def history(self, policy_family: str) -> tuple[PolicyDecisionRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM policy_decisions "
                "WHERE policy_family = ? ORDER BY decided_at, decision_id",
                (policy_family,),
            ).fetchall()
        return tuple(_record_from_payload(str(row["payload_json"])) for row in rows)

    def append_and_activate(self, record: PolicyDecisionRecord) -> bool:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT fingerprint FROM policy_decisions WHERE decision_id = ?",
                (record.decision_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["fingerprint"]) != record.fingerprint:
                    raise PolicyGovernanceConflict(
                        "policy decision id already exists with different content"
                    )
                active = connection.execute(
                    "SELECT policy_json, latest_decision_id FROM active_policies "
                    "WHERE policy_family = ?",
                    (record.policy_family,),
                ).fetchone()
                if active is None:
                    raise PolicyGovernanceConflict(
                        "idempotent decision exists without active policy pointer"
                    )
                current = _policy_from_payload(json.loads(active["policy_json"]))
                if (
                    current != record.to_policy
                    or active["latest_decision_id"] != record.decision_id
                ):
                    raise PolicyGovernanceConflict(
                        "idempotent decision does not match active policy pointer"
                    )
                connection.commit()
                return False

            active = connection.execute(
                "SELECT policy_json, latest_decision_id FROM active_policies "
                "WHERE policy_family = ?",
                (record.policy_family,),
            ).fetchone()
            if active is None:
                raise PolicyGovernanceConflict(
                    "cannot append governance decision without active baseline"
                )
            current = _policy_from_payload(json.loads(active["policy_json"]))
            if current != record.from_policy:
                raise PolicyGovernanceConflict(
                    "policy decision from-policy does not match current active pointer"
                )
            latest_id = active["latest_decision_id"]
            expected_previous = None if latest_id is None else str(latest_id)
            if record.previous_decision_id != expected_previous:
                raise PolicyGovernanceConflict(
                    "policy decision previous pointer does not match durable history"
                )

            connection.execute(
                "INSERT INTO policy_decisions("
                "decision_id, policy_family, decided_at, fingerprint, payload_json"
                ") VALUES (?, ?, ?, ?, ?)",
                (
                    record.decision_id,
                    record.policy_family,
                    record.decided_at.isoformat(),
                    record.fingerprint,
                    _record_payload(record),
                ),
            )
            connection.execute(
                "UPDATE active_policies "
                "SET policy_json = ?, latest_decision_id = ? "
                "WHERE policy_family = ?",
                (
                    json.dumps(
                        _policy_payload(record.to_policy),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    record.decision_id,
                    record.policy_family,
                ),
            )
            connection.commit()
            return True
