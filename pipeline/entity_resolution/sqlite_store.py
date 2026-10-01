"""SQLite adapter for append-only canonical identity governance."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from application.identity_resolution.governance import (
    IdentityDecisionAuthority,
    IdentityDecisionKind,
    IdentityDecisionRecord,
    IdentityGovernanceConflict,
    IdentitySubjectPointer,
    IdentitySubjectState,
)
from domain.identity import OrganizationId


class SqliteIdentityGovernanceStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_subjects (
                    organization_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    redirect_to TEXT,
                    last_decision_id TEXT,
                    requires_revalidation INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS identity_decisions (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    reverses_decision_id TEXT
                )
                """
            )

    def seed_subject(self, organization_id: OrganizationId) -> bool:
        if not organization_id.strip():
            raise ValueError("organization id is required")
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT organization_id FROM identity_subjects WHERE organization_id = ?",
                (str(organization_id),),
            ).fetchone()
            if existing is not None:
                return False
            connection.execute(
                """
                INSERT INTO identity_subjects (
                    organization_id, state, redirect_to, last_decision_id,
                    requires_revalidation
                ) VALUES (?, ?, NULL, NULL, 0)
                """,
                (str(organization_id), IdentitySubjectState.ACTIVE.value),
            )
            return True

    def current(self, organization_id: OrganizationId) -> IdentitySubjectPointer | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT organization_id, state, redirect_to, last_decision_id,
                       requires_revalidation
                FROM identity_subjects
                WHERE organization_id = ?
                """,
                (str(organization_id),),
            ).fetchone()
        return None if row is None else self._pointer(row)

    def get_decision(self, decision_id: str) -> IdentityDecisionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM identity_decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
        return None if row is None else self._decision(json.loads(row["payload_json"]))

    def latest_decision_id(self) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT decision_id FROM identity_decisions ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        return None if row is None else str(row["decision_id"])

    def history(self) -> tuple[IdentityDecisionRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM identity_decisions ORDER BY sequence"
            ).fetchall()
        return tuple(self._decision(json.loads(row["payload_json"])) for row in rows)

    def append_and_apply(self, record: IdentityDecisionRecord) -> None:
        payload = self._payload(record)
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """
                SELECT fingerprint, payload_json
                FROM identity_decisions
                WHERE decision_id = ?
                """,
                (record.decision_id,),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["fingerprint"]) == record.fingerprint
                    and str(existing["payload_json"]) == serialized
                ):
                    connection.rollback()
                    return
                raise IdentityGovernanceConflict("identity decision id already exists")

            latest = connection.execute(
                "SELECT decision_id FROM identity_decisions ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            latest_id = None if latest is None else str(latest["decision_id"])
            if record.previous_decision_id != latest_id:
                raise IdentityGovernanceConflict(
                    "identity decision previous pointer does not match durable history"
                )

            if record.kind is IdentityDecisionKind.MERGE:
                self._apply_merge(connection, record)
            elif record.kind is IdentityDecisionKind.SPLIT:
                self._apply_split(connection, record)
            else:
                self._apply_reversal(connection, record)

            connection.execute(
                """
                INSERT INTO identity_decisions (
                    decision_id, kind, fingerprint, payload_json, reverses_decision_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record.decision_id,
                    record.kind.value,
                    record.fingerprint,
                    serialized,
                    record.reverses_decision_id,
                ),
            )
            connection.commit()

    def _apply_merge(
        self,
        connection: sqlite3.Connection,
        record: IdentityDecisionRecord,
    ) -> None:
        target = record.to_organization_ids[0]
        self._require_active(connection, target)
        for source in record.from_organization_ids:
            self._require_active(connection, source)
            connection.execute(
                """
                UPDATE identity_subjects
                SET state = ?, redirect_to = ?, last_decision_id = ?,
                    requires_revalidation = 0
                WHERE organization_id = ?
                """,
                (
                    IdentitySubjectState.REDIRECTED.value,
                    str(target),
                    record.decision_id,
                    str(source),
                ),
            )
        connection.execute(
            """
            UPDATE identity_subjects
            SET last_decision_id = ?
            WHERE organization_id = ?
            """,
            (record.decision_id, str(target)),
        )

    def _apply_split(
        self,
        connection: sqlite3.Connection,
        record: IdentityDecisionRecord,
    ) -> None:
        source = record.from_organization_ids[0]
        self._require_active(connection, source)
        for target in record.to_organization_ids:
            self._require_active(connection, target)
        connection.execute(
            """
            UPDATE identity_subjects
            SET state = ?, redirect_to = NULL, last_decision_id = ?,
                requires_revalidation = 1
            WHERE organization_id = ?
            """,
            (
                IdentitySubjectState.AMBIGUOUS.value,
                record.decision_id,
                str(source),
            ),
        )
        for target in record.to_organization_ids:
            connection.execute(
                """
                UPDATE identity_subjects
                SET last_decision_id = ?, requires_revalidation = 1
                WHERE organization_id = ?
                """,
                (record.decision_id, str(target)),
            )

    def _apply_reversal(
        self,
        connection: sqlite3.Connection,
        record: IdentityDecisionRecord,
    ) -> None:
        assert record.reverses_decision_id is not None
        target_row = connection.execute(
            """
            SELECT payload_json
            FROM identity_decisions
            WHERE decision_id = ?
            """,
            (record.reverses_decision_id,),
        ).fetchone()
        if target_row is None:
            raise IdentityGovernanceConflict("identity reversal target does not exist")
        already_reversed = connection.execute(
            """
            SELECT decision_id
            FROM identity_decisions
            WHERE reverses_decision_id = ?
            LIMIT 1
            """,
            (record.reverses_decision_id,),
        ).fetchone()
        if already_reversed is not None:
            raise IdentityGovernanceConflict("identity decision was already reversed")

        target = self._decision(json.loads(target_row["payload_json"]))
        if target.kind is IdentityDecisionKind.REVERSAL:
            raise IdentityGovernanceConflict("identity reversal cannot target reversal")

        affected = set(target.from_organization_ids) | set(target.to_organization_ids)
        for organization_id in affected:
            pointer = self._require_pointer(connection, organization_id)
            if pointer.last_decision_id != target.decision_id:
                raise IdentityGovernanceConflict(
                    "identity reversal target is stale for an affected subject"
                )

        if target.kind is IdentityDecisionKind.MERGE:
            retained = target.to_organization_ids[0]
            for source in target.from_organization_ids:
                pointer = self._require_pointer(connection, source)
                if (
                    pointer.state is not IdentitySubjectState.REDIRECTED
                    or pointer.redirect_to != retained
                ):
                    raise IdentityGovernanceConflict(
                        "merge topology no longer matches reversal target"
                    )
                self._set_active_revalidation(connection, source, record.decision_id)
            self._set_active_revalidation(connection, retained, record.decision_id)
        else:
            source = target.from_organization_ids[0]
            pointer = self._require_pointer(connection, source)
            if pointer.state is not IdentitySubjectState.AMBIGUOUS:
                raise IdentityGovernanceConflict("split topology no longer matches reversal target")
            self._set_active_revalidation(connection, source, record.decision_id)
            for child in target.to_organization_ids:
                self._set_active_revalidation(connection, child, record.decision_id)

    @staticmethod
    def _set_active_revalidation(
        connection: sqlite3.Connection,
        organization_id: OrganizationId,
        decision_id: str,
    ) -> None:
        connection.execute(
            """
            UPDATE identity_subjects
            SET state = ?, redirect_to = NULL, last_decision_id = ?,
                requires_revalidation = 1
            WHERE organization_id = ?
            """,
            (
                IdentitySubjectState.ACTIVE.value,
                decision_id,
                str(organization_id),
            ),
        )

    def _require_active(
        self,
        connection: sqlite3.Connection,
        organization_id: OrganizationId,
    ) -> IdentitySubjectPointer:
        pointer = self._require_pointer(connection, organization_id)
        if pointer.state is not IdentitySubjectState.ACTIVE:
            raise IdentityGovernanceConflict("identity subject is not active")
        return pointer

    def _require_pointer(
        self,
        connection: sqlite3.Connection,
        organization_id: OrganizationId,
    ) -> IdentitySubjectPointer:
        row = connection.execute(
            """
            SELECT organization_id, state, redirect_to, last_decision_id,
                   requires_revalidation
            FROM identity_subjects
            WHERE organization_id = ?
            """,
            (str(organization_id),),
        ).fetchone()
        if row is None:
            raise IdentityGovernanceConflict("identity subject is not registered")
        return self._pointer(row)

    @staticmethod
    def _pointer(row: sqlite3.Row) -> IdentitySubjectPointer:
        redirect = row["redirect_to"]
        return IdentitySubjectPointer(
            organization_id=OrganizationId(str(row["organization_id"])),
            state=IdentitySubjectState(str(row["state"])),
            redirect_to=(None if redirect is None else OrganizationId(str(redirect))),
            last_decision_id=(
                None if row["last_decision_id"] is None else str(row["last_decision_id"])
            ),
            requires_revalidation=bool(row["requires_revalidation"]),
        )

    @staticmethod
    def _payload(record: IdentityDecisionRecord) -> dict[str, Any]:
        payload = asdict(record)
        payload["kind"] = record.kind.value
        payload["authority"] = record.authority.value
        payload["decided_at"] = record.decided_at.isoformat()
        return payload

    @staticmethod
    def _decision(payload: dict[str, Any]) -> IdentityDecisionRecord:
        return IdentityDecisionRecord(
            decision_id=str(payload["decision_id"]),
            kind=IdentityDecisionKind(str(payload["kind"])),
            from_organization_ids=tuple(
                OrganizationId(str(item)) for item in payload["from_organization_ids"]
            ),
            to_organization_ids=tuple(
                OrganizationId(str(item)) for item in payload["to_organization_ids"]
            ),
            evidence_refs=tuple(str(item) for item in payload["evidence_refs"]),
            reason_code=str(payload["reason_code"]),
            authority=IdentityDecisionAuthority(str(payload["authority"])),
            decided_by=str(payload["decided_by"]),
            decided_at=datetime.fromisoformat(str(payload["decided_at"])),
            previous_decision_id=(
                None
                if payload.get("previous_decision_id") is None
                else str(payload["previous_decision_id"])
            ),
            reverses_decision_id=(
                None
                if payload.get("reverses_decision_id") is None
                else str(payload["reverses_decision_id"])
            ),
            requires_revalidation_ids=tuple(
                OrganizationId(str(item)) for item in payload.get("requires_revalidation_ids", ())
            ),
        )
