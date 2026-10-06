"""SQLite operational state for the autonomous observation runtime.

One row per UTC day fences the daily tick: the first claimant owns it, a live
lease blocks a second worker, an expired lease is resumed, and a completed day
is never run again. Every step is committed atomically and only by the token
that owns the day, so a worker that lost its lease cannot write. Nothing here
is canonical AXIGLAND state.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from application.observation_intelligence.contracts import (
    OpportunityFamily,
    SourceCapability,
    TaxonomyCode,
)
from application.observation_intelligence.findings import ProcurementRecord
from application.observation_intelligence.learning import (
    OperationalLearning,
    SourceOperationalStats,
)
from application.observation_intelligence.loop import OpportunityCandidate
from application.observation_runtime.budget import BudgetUsage
from application.observation_runtime.families import LeadKind, ObservationFamily
from application.observation_runtime.frontier import (
    LeadOutcome,
    LeadStatus,
    LeadTier,
    ResearchLead,
)
from application.observation_runtime.ports import (
    EvidenceState,
    LeaseLost,
    PendingRecompute,
    RecomputeTrigger,
    StoredCandidate,
    TickClaim,
)
from domain.evidence.epistemics import Currentness
from domain.xignal import XignalEpistemicState

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS aor_ticks (
        day TEXT PRIMARY KEY, token TEXT NOT NULL, lease_expires_at TEXT NOT NULL,
        started_at TEXT NOT NULL, completed_at TEXT, report TEXT)""",
    "CREATE TABLE IF NOT EXISTS aor_leads (lead_id TEXT PRIMARY KEY, xeed_id TEXT NOT NULL, payload TEXT NOT NULL)",
    """CREATE TABLE IF NOT EXISTS aor_evidence (
        xeed_id TEXT NOT NULL, family TEXT NOT NULL, key TEXT NOT NULL, payload TEXT NOT NULL,
        PRIMARY KEY (xeed_id, family, key))""",
    "CREATE TABLE IF NOT EXISTS aor_candidates (candidate_id TEXT PRIMARY KEY, xeed_id TEXT NOT NULL, payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS aor_budget (day TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS aor_learning (source_id TEXT PRIMARY KEY, payload TEXT NOT NULL)",
    """CREATE TABLE IF NOT EXISTS aor_recompute (
        xeed_id TEXT NOT NULL, family TEXT NOT NULL, payload TEXT NOT NULL,
        PRIMARY KEY (xeed_id, family))""",
)


def _utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("runtime store times must be timezone-aware")
    return value.astimezone(UTC).isoformat()


def _time(value: object) -> datetime | None:
    return None if value is None else datetime.fromisoformat(str(value))


def _required_time(value: object) -> datetime:
    parsed = _time(value)
    if parsed is None:
        raise ValueError("stored time is required")
    return parsed


def _code(value: TaxonomyCode | None) -> list[str] | None:
    return None if value is None else [value.scheme, value.code]


def _from_code(value: Any) -> TaxonomyCode | None:
    return None if value is None else TaxonomyCode(str(value[0]), str(value[1]))


def _codes(values: tuple[TaxonomyCode, ...]) -> list[list[str]]:
    return [[c.scheme, c.code] for c in values]


def _from_codes(values: Any) -> tuple[TaxonomyCode, ...]:
    return tuple(TaxonomyCode(str(s), str(c)) for s, c in values)


def encode_lead(lead: ResearchLead) -> dict[str, object]:
    return {
        "lead_id": lead.lead_id,
        "xeed_id": lead.xeed_id,
        "family": lead.family.value,
        "kind": lead.kind.value,
        "target": lead.target,
        "geography": _code(lead.geography),
        "question": lead.question,
        "reduces_unknown": lead.reduces_unknown,
        "depth": lead.depth,
        "parent_lead_id": lead.parent_lead_id,
        "origin_evidence": list(lead.origin_evidence),
        "reasons": list(lead.reasons),
        "next_due_at": _utc(lead.next_due_at),
        "tier": lead.tier.name,
        "scheduling_reason": lead.scheduling_reason,
        "status": lead.status.value,
        "attempts": lead.attempts,
        "failures": lead.failures,
        "no_gain_streak": lead.no_gain_streak,
        "last_outcome": None if lead.last_outcome is None else lead.last_outcome.value,
        "last_attempt_at": None if lead.last_attempt_at is None else _utc(lead.last_attempt_at),
        "last_success_at": None if lead.last_success_at is None else _utc(lead.last_success_at),
        "last_material_change_at": (
            None if lead.last_material_change_at is None else _utc(lead.last_material_change_at)
        ),
        "blocked_reason": lead.blocked_reason,
        "evidence_keys": list(lead.evidence_keys),
    }


def decode_lead(raw: dict[str, Any]) -> ResearchLead:
    return ResearchLead(
        lead_id=str(raw["lead_id"]),
        xeed_id=str(raw["xeed_id"]),
        family=ObservationFamily(raw["family"]),
        kind=LeadKind(raw["kind"]),
        target=str(raw["target"]),
        geography=_from_code(raw["geography"]),
        question=str(raw["question"]),
        reduces_unknown=str(raw["reduces_unknown"]),
        depth=int(raw["depth"]),
        parent_lead_id=raw["parent_lead_id"],
        origin_evidence=tuple(raw["origin_evidence"]),
        reasons=tuple(raw["reasons"]),
        next_due_at=_required_time(raw["next_due_at"]),
        tier=LeadTier[raw["tier"]],
        scheduling_reason=str(raw["scheduling_reason"]),
        status=LeadStatus(raw["status"]),
        attempts=int(raw["attempts"]),
        failures=int(raw["failures"]),
        no_gain_streak=int(raw["no_gain_streak"]),
        last_outcome=None if raw["last_outcome"] is None else LeadOutcome(raw["last_outcome"]),
        last_attempt_at=_time(raw["last_attempt_at"]),
        last_success_at=_time(raw["last_success_at"]),
        last_material_change_at=_time(raw["last_material_change_at"]),
        blocked_reason=raw["blocked_reason"],
        evidence_keys=tuple(raw["evidence_keys"]),
    )


def _encode_evidence(row: EvidenceState) -> dict[str, object]:
    return {
        "xeed_id": row.xeed_id,
        "family": row.family.value,
        "key": row.key,
        "fingerprint": row.fingerprint,
        "source_id": row.source_id,
        "provenance_ref": row.provenance_ref,
        "lead_id": row.lead_id,
        "first_observed_at": _utc(row.first_observed_at),
        "observed_at": _utc(row.observed_at),
        "changed_at": _utc(row.changed_at),
        "currentness": row.currentness.value,
    }


def _decode_evidence(raw: dict[str, Any]) -> EvidenceState:
    return EvidenceState(
        xeed_id=str(raw["xeed_id"]),
        family=ObservationFamily(raw["family"]),
        key=str(raw["key"]),
        fingerprint=str(raw["fingerprint"]),
        source_id=str(raw["source_id"]),
        provenance_ref=str(raw["provenance_ref"]),
        lead_id=str(raw["lead_id"]),
        first_observed_at=_required_time(raw["first_observed_at"]),
        observed_at=_required_time(raw["observed_at"]),
        changed_at=_required_time(raw["changed_at"]),
        currentness=Currentness(raw["currentness"]),
    )


def _encode_candidate(item: StoredCandidate) -> dict[str, object]:
    c, r = item.candidate, item.candidate.record
    return {
        "lead_id": item.lead_id,
        "first_seen_at": _utc(item.first_seen_at),
        "candidate_id": c.candidate_id,
        "xeed_id": c.xeed_id,
        "record": {
            "record_id": r.record_id,
            "source_id": r.source_id,
            "kind": r.kind.value,
            "title": r.title,
            "buyer_name": r.buyer_name,
            "places": _codes(r.places),
            "demand_codes": _codes(r.demand_codes),
            "published_at": _utc(r.published_at),
            "source_url": r.source_url,
            "deadline": r.deadline,
            "winners": list(r.winners),
        },
        "market": _code(c.market),
        "capability_ids": list(c.capability_ids),
        "matched_codes": _codes(c.matched_codes),
        "why_looked": list(c.why_looked),
        "missing_context": list(c.missing_context),
        "observed_at": _utc(c.observed_at),
        "match_basis": list(c.match_basis),
        "opportunity_family": c.opportunity_family.value,
        "demand_form": c.demand_form,
        "epistemic_state": c.epistemic_state.value,
    }


def _decode_candidate(raw: dict[str, Any]) -> StoredCandidate:
    r = raw["record"]
    market = _from_code(raw["market"])
    assert market is not None
    candidate = OpportunityCandidate(
        candidate_id=str(raw["candidate_id"]),
        xeed_id=str(raw["xeed_id"]),
        record=ProcurementRecord(
            record_id=str(r["record_id"]),
            source_id=str(r["source_id"]),
            kind=SourceCapability(r["kind"]),
            title=str(r["title"]),
            buyer_name=r["buyer_name"],
            places=_from_codes(r["places"]),
            demand_codes=_from_codes(r["demand_codes"]),
            published_at=_required_time(r["published_at"]),
            source_url=str(r["source_url"]),
            deadline=r["deadline"],
            winners=tuple(r["winners"]),
        ),
        market=market,
        capability_ids=tuple(raw["capability_ids"]),
        matched_codes=_from_codes(raw["matched_codes"]),
        why_looked=tuple(raw["why_looked"]),
        missing_context=tuple(raw["missing_context"]),
        observed_at=_required_time(raw["observed_at"]),
        match_basis=tuple(raw["match_basis"]),
        opportunity_family=OpportunityFamily(raw["opportunity_family"]),
        demand_form=str(raw["demand_form"]),
        epistemic_state=XignalEpistemicState(raw["epistemic_state"]),
    )
    return StoredCandidate(candidate, str(raw["lead_id"]), _required_time(raw["first_seen_at"]))


def _dumps(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SqliteObservationRuntimeStore:
    def __init__(self, database_path: str | Path) -> None:
        self._path = Path(database_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._transaction() as db:
            for statement in _SCHEMA:
                db.execute(statement)

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self._path, isolation_level=None)) as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
            except BaseException:
                db.execute("ROLLBACK")
                raise
            db.execute("COMMIT")

    def _read(self, sql: str, args: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        with closing(sqlite3.connect(self._path)) as db:
            db.row_factory = sqlite3.Row
            return list(db.execute(sql, args).fetchall())

    def claim_tick(self, day: str, *, now: datetime, lease_seconds: int) -> TickClaim | None:
        if lease_seconds <= 0:
            raise ValueError("tick lease must be positive")
        token = uuid.uuid4().hex
        expires = _utc(now + timedelta(seconds=lease_seconds))
        with self._transaction() as db:
            row = db.execute("SELECT * FROM aor_ticks WHERE day=?", (day,)).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO aor_ticks VALUES (?, ?, ?, ?, NULL, NULL)",
                    (day, token, expires, _utc(now)),
                )
                return TickClaim(day, token, resumed=False)
            if row["completed_at"] is not None or _required_time(row["lease_expires_at"]) > now:
                return None
            db.execute(
                "UPDATE aor_ticks SET token=?, lease_expires_at=? WHERE day=?",
                (token, expires, day),
            )
            return TickClaim(day, token, resumed=True)

    def _fence(self, db: sqlite3.Connection, claim: TickClaim) -> None:
        row = db.execute(
            "SELECT token, completed_at FROM aor_ticks WHERE day=?", (claim.day,)
        ).fetchone()
        if row is None or row["token"] != claim.token or row["completed_at"] is not None:
            raise LeaseLost(f"tick {claim.day} is no longer owned by this worker")

    def tick_report(self, day: str) -> dict[str, object] | None:
        rows = self._read(
            "SELECT report FROM aor_ticks WHERE day=? AND completed_at IS NOT NULL", (day,)
        )
        if not rows:
            return None
        report = json.loads(str(rows[0]["report"]))
        assert isinstance(report, dict)
        return report

    def complete_tick(
        self, claim: TickClaim, *, completed_at: datetime, report: dict[str, object]
    ) -> None:
        with self._transaction() as db:
            self._fence(db, claim)
            db.execute(
                "UPDATE aor_ticks SET completed_at=?, report=? WHERE day=?",
                (_utc(completed_at), _dumps(report), claim.day),
            )

    def leads(self) -> tuple[ResearchLead, ...]:
        rows = self._read("SELECT payload FROM aor_leads ORDER BY lead_id")
        return tuple(decode_lead(json.loads(str(row["payload"]))) for row in rows)

    def evidence(self) -> tuple[EvidenceState, ...]:
        rows = self._read("SELECT payload FROM aor_evidence ORDER BY xeed_id, family, key")
        return tuple(_decode_evidence(json.loads(str(row["payload"]))) for row in rows)

    def candidates(self, xeed_id: str) -> tuple[StoredCandidate, ...]:
        rows = self._read(
            "SELECT payload FROM aor_candidates WHERE xeed_id=? ORDER BY candidate_id", (xeed_id,)
        )
        return tuple(_decode_candidate(json.loads(str(row["payload"]))) for row in rows)

    def budget_usage(self, day: str) -> BudgetUsage:
        rows = self._read("SELECT payload FROM aor_budget WHERE day=?", (day,))
        if not rows:
            return BudgetUsage(day=day)
        return BudgetUsage.from_payload(json.loads(str(rows[0]["payload"])))

    def learning(self) -> OperationalLearning:
        learning = OperationalLearning()
        for row in self._read("SELECT payload FROM aor_learning ORDER BY source_id"):
            raw = json.loads(str(row["payload"]))
            learning.stats[str(raw["source_id"])] = SourceOperationalStats(**raw)
        return learning

    def pending_recompute(self) -> tuple[PendingRecompute, ...]:
        rows = self._read("SELECT payload FROM aor_recompute ORDER BY xeed_id, family")
        items = []
        for row in rows:
            raw = json.loads(str(row["payload"]))
            items.append(
                PendingRecompute(
                    str(raw["xeed_id"]),
                    ObservationFamily(raw["family"]),
                    RecomputeTrigger(raw["trigger"]),
                    tuple(raw["evidence_keys"]),
                )
            )
        return tuple(items)

    def commit(
        self,
        claim: TickClaim,
        *,
        now: datetime,
        leads: tuple[ResearchLead, ...],
        evidence: tuple[EvidenceState, ...],
        candidates: tuple[StoredCandidate, ...],
        usage: BudgetUsage,
        learning: OperationalLearning,
        recompute: tuple[PendingRecompute, ...],
    ) -> None:
        with self._transaction() as db:
            self._fence(db, claim)
            db.executemany(
                "INSERT OR REPLACE INTO aor_leads VALUES (?, ?, ?)",
                [(lead.lead_id, lead.xeed_id, _dumps(encode_lead(lead))) for lead in leads],
            )
            db.executemany(
                "INSERT OR REPLACE INTO aor_evidence VALUES (?, ?, ?, ?)",
                [
                    (row.xeed_id, row.family.value, row.key, _dumps(_encode_evidence(row)))
                    for row in evidence
                ],
            )
            # Candidates are content-addressed: a replay can never duplicate one.
            db.executemany(
                "INSERT OR IGNORE INTO aor_candidates VALUES (?, ?, ?)",
                [
                    (
                        item.candidate.candidate_id,
                        item.candidate.xeed_id,
                        _dumps(_encode_candidate(item)),
                    )
                    for item in candidates
                ],
            )
            db.execute(
                "INSERT OR REPLACE INTO aor_budget VALUES (?, ?)",
                (usage.day, _dumps(usage.to_payload())),
            )
            db.executemany(
                "INSERT OR REPLACE INTO aor_learning VALUES (?, ?)",
                [
                    (source_id, _dumps({"source_id": source_id, **_stats(stats)}))
                    for source_id, stats in sorted(learning.stats.items())
                ],
            )
            db.executemany(
                "INSERT OR REPLACE INTO aor_recompute VALUES (?, ?, ?)",
                [
                    (
                        item.xeed_id,
                        item.family.value,
                        _dumps(
                            {
                                "xeed_id": item.xeed_id,
                                "family": item.family.value,
                                "trigger": item.trigger.value,
                                "evidence_keys": list(item.evidence_keys),
                            }
                        ),
                    )
                    for item in recompute
                ],
            )

    def clear_recompute(self, claim: TickClaim, *, xeed_id: str, family: ObservationFamily) -> None:
        with self._transaction() as db:
            self._fence(db, claim)
            db.execute(
                "DELETE FROM aor_recompute WHERE xeed_id=? AND family=?", (xeed_id, family.value)
            )


def _stats(stats: SourceOperationalStats) -> dict[str, int]:
    return {
        "attempts": stats.attempts,
        "failures": stats.failures,
        "requests": stats.requests,
        "records": stats.records,
        "new_records": stats.new_records,
        "duplicates": stats.duplicates,
        "candidates": stats.candidates,
        "follow_ups": stats.follow_ups,
        "latency_ms": stats.latency_ms,
        "amount_microunits": stats.amount_microunits,
    }
