"""Append-only SQLite persistence for AO-16 weekly brief artifacts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from domain.admin_weekly_brief import (
    WeeklyBriefApproval,
    WeeklyBriefCorrection,
    WeeklyBriefDelivery,
    WeeklyBriefIssue,
    WeeklyBriefIssueKind,
    WeeklyBriefItem,
)
from domain.evidence.epistemics import Currentness


class WeeklyBriefStoreConflict(ValueError):
    pass


class SqliteWeeklyBriefStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS weekly_brief_issues (
                    issue_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS weekly_brief_approvals (
                    issue_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS weekly_brief_deliveries (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    delivery_id TEXT NOT NULL UNIQUE,
                    issue_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_weekly_brief_delivery_issue
                    ON weekly_brief_deliveries(issue_id, sequence);
                CREATE TABLE IF NOT EXISTS weekly_brief_corrections (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    correction_id TEXT NOT NULL UNIQUE,
                    issue_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_weekly_brief_correction_issue
                    ON weekly_brief_corrections(issue_id, sequence);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _fingerprint(payload: str) -> str:
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _dump(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _item_payload(item: WeeklyBriefItem) -> dict[str, object]:
        return {
            "observation_id": item.observation_id,
            "source_ref": item.source_ref,
            "observed_at": item.observed_at.isoformat(),
            "content_fingerprint": item.content_fingerprint,
            "condition": item.condition.value,
            "observation_summary": item.observation_summary,
            "why_may_matter": item.why_may_matter,
            "unknowns": list(item.unknowns),
        }

    @classmethod
    def _issue_payload(cls, issue: WeeklyBriefIssue) -> dict[str, object]:
        return {
            "issue_id": issue.issue_id,
            "request_id": issue.request_id,
            "subject_reference": issue.subject_reference,
            "issue_version": issue.issue_version,
            "composition_policy_id": issue.composition_policy_id,
            "composition_policy_version": issue.composition_policy_version,
            "created_at": issue.created_at.isoformat(),
            "kind": issue.kind.value,
            "items": [cls._item_payload(item) for item in issue.items],
            "evidence_fingerprint": issue.evidence_fingerprint,
        }

    @staticmethod
    def _issue_from_payload(payload: dict[str, object]) -> WeeklyBriefIssue:
        raw_items = payload["items"]
        if not isinstance(raw_items, list):
            raise ValueError("weekly brief issue items must be an array")
        items = tuple(
            WeeklyBriefItem(
                observation_id=str(item["observation_id"]),
                source_ref=str(item["source_ref"]),
                observed_at=datetime.fromisoformat(str(item["observed_at"])),
                content_fingerprint=str(item["content_fingerprint"]),
                condition=Currentness(str(item["condition"])),
                observation_summary=str(item["observation_summary"]),
                why_may_matter=str(item["why_may_matter"]),
                unknowns=tuple(str(value) for value in item["unknowns"]),
            )
            for item in raw_items
        )
        return WeeklyBriefIssue(
            issue_id=str(payload["issue_id"]),
            request_id=str(payload["request_id"]),
            subject_reference=str(payload["subject_reference"]),
            issue_version=str(payload["issue_version"]),
            composition_policy_id=str(payload["composition_policy_id"]),
            composition_policy_version=str(payload["composition_policy_version"]),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            kind=WeeklyBriefIssueKind(str(payload["kind"])),
            items=items,
            evidence_fingerprint=str(payload["evidence_fingerprint"]),
        )

    def _insert_once(
        self,
        *,
        table: str,
        id_column: str,
        identity: str,
        issue_id: str | None,
        payload: str,
    ) -> bool:
        fingerprint = self._fingerprint(payload)
        with self._connect() as connection:
            existing = connection.execute(
                f"SELECT payload_json, fingerprint FROM {table} WHERE {id_column} = ?",
                (identity,),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["payload_json"]) == payload
                    and str(existing["fingerprint"]) == fingerprint
                ):
                    return False
                raise WeeklyBriefStoreConflict(f"{id_column} reused with different content")
            if issue_id is None:
                connection.execute(
                    f"INSERT INTO {table}({id_column}, payload_json, fingerprint) VALUES (?, ?, ?)",
                    (identity, payload, fingerprint),
                )
            else:
                connection.execute(
                    f"INSERT INTO {table}({id_column}, issue_id, payload_json, fingerprint) VALUES (?, ?, ?, ?)",
                    (identity, issue_id, payload, fingerprint),
                )
        return True

    def put_issue(self, issue: WeeklyBriefIssue) -> bool:
        payload = self._dump(self._issue_payload(issue))
        return self._insert_once(
            table="weekly_brief_issues",
            id_column="issue_id",
            identity=issue.issue_id,
            issue_id=None,
            payload=payload,
        )

    def get_issue(self, issue_id: str) -> WeeklyBriefIssue | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM weekly_brief_issues WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
        if row is None:
            return None
        return self._issue_from_payload(json.loads(str(row["payload_json"])))

    def put_approval(self, approval: WeeklyBriefApproval) -> bool:
        payload = self._dump(
            {
                "issue_id": approval.issue_id,
                "reviewer_principal_id": approval.reviewer_principal_id,
                "approved_at": approval.approved_at.isoformat(),
            }
        )
        return self._insert_once(
            table="weekly_brief_approvals",
            id_column="issue_id",
            identity=approval.issue_id,
            issue_id=None,
            payload=payload,
        )

    def get_approval(self, issue_id: str) -> WeeklyBriefApproval | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM weekly_brief_approvals WHERE issue_id = ?",
                (issue_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(str(row["payload_json"]))
        return WeeklyBriefApproval(
            issue_id=str(payload["issue_id"]),
            reviewer_principal_id=str(payload["reviewer_principal_id"]),
            approved_at=datetime.fromisoformat(str(payload["approved_at"])),
        )

    def put_delivery(self, delivery: WeeklyBriefDelivery) -> bool:
        payload = self._dump(
            {
                "delivery_id": delivery.delivery_id,
                "issue_id": delivery.issue_id,
                "delivered_at": delivery.delivered_at.isoformat(),
                "integration_id": delivery.integration_id,
                "provider_message_ref": delivery.provider_message_ref,
            }
        )
        return self._insert_once(
            table="weekly_brief_deliveries",
            id_column="delivery_id",
            identity=delivery.delivery_id,
            issue_id=delivery.issue_id,
            payload=payload,
        )

    def deliveries_for_issue(self, issue_id: str) -> tuple[WeeklyBriefDelivery, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM weekly_brief_deliveries WHERE issue_id = ? ORDER BY sequence",
                (issue_id,),
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            result.append(
                WeeklyBriefDelivery(
                    delivery_id=str(payload["delivery_id"]),
                    issue_id=str(payload["issue_id"]),
                    delivered_at=datetime.fromisoformat(str(payload["delivered_at"])),
                    integration_id=str(payload["integration_id"]),
                    provider_message_ref=str(payload["provider_message_ref"]),
                )
            )
        return tuple(result)

    def put_correction(self, correction: WeeklyBriefCorrection) -> bool:
        payload = self._dump(
            {
                "correction_id": correction.correction_id,
                "issue_id": correction.issue_id,
                "occurred_at": correction.occurred_at.isoformat(),
                "actor_principal_id": correction.actor_principal_id,
                "reason": correction.reason,
                "note": correction.note,
            }
        )
        return self._insert_once(
            table="weekly_brief_corrections",
            id_column="correction_id",
            identity=correction.correction_id,
            issue_id=correction.issue_id,
            payload=payload,
        )

    def corrections_for_issue(self, issue_id: str) -> tuple[WeeklyBriefCorrection, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM weekly_brief_corrections WHERE issue_id = ? ORDER BY sequence",
                (issue_id,),
            ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            result.append(
                WeeklyBriefCorrection(
                    correction_id=str(payload["correction_id"]),
                    issue_id=str(payload["issue_id"]),
                    occurred_at=datetime.fromisoformat(str(payload["occurred_at"])),
                    actor_principal_id=str(payload["actor_principal_id"]),
                    reason=str(payload["reason"]),
                    note=str(payload["note"]),
                )
            )
        return tuple(result)

    def all_issues(self) -> tuple[WeeklyBriefIssue, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM weekly_brief_issues ORDER BY issue_id"
            ).fetchall()
        return tuple(self._issue_from_payload(json.loads(str(row["payload_json"]))) for row in rows)

    def all_deliveries(self) -> tuple[WeeklyBriefDelivery, ...]:
        result: list[WeeklyBriefDelivery] = []
        for issue in self.all_issues():
            result.extend(self.deliveries_for_issue(issue.issue_id))
        return tuple(result)

    def all_corrections(self) -> tuple[WeeklyBriefCorrection, ...]:
        result: list[WeeklyBriefCorrection] = []
        for issue in self.all_issues():
            result.extend(self.corrections_for_issue(issue.issue_id))
        return tuple(result)
