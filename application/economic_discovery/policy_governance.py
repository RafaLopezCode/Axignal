"""Human/governance policy promotion and rollback gate.

FR-20 is the only application boundary allowed to move an active policy pointer from
an FR-19 candidate. Runtime yield, Learning Memory and shadow reports have no promotion
authority on their own.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from application.economic_discovery.policy_experiment import (
    PolicyCandidate,
    PolicyComparisonReport,
    policy_counter_metrics,
)


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("policy-governance identity is required")


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def comparison_fingerprint(report: PolicyComparisonReport) -> str:
    return _fingerprint(
        {
            "candidate_id": report.candidate_id,
            "candidate_fingerprint": report.candidate_fingerprint,
            "split_id": report.split_id,
            "split_fingerprint": report.split_fingerprint,
            "evaluations": [
                {
                    "event_id": item.event_id,
                    "subject_id": item.subject_id,
                    "occurred_at": item.occurred_at.astimezone(UTC).isoformat(),
                    "source_outcome": item.source_outcome.value,
                    "status": item.status.value,
                    "baseline": (
                        None
                        if item.baseline is None
                        else {
                            "state": item.baseline.state.value,
                            "reason_code": item.baseline.reason_code,
                            "value": item.baseline.value,
                        }
                    ),
                    "candidate": (
                        None
                        if item.candidate is None
                        else {
                            "state": item.candidate.state.value,
                            "reason_code": item.candidate.reason_code,
                            "value": item.candidate.value,
                        }
                    ),
                    "reason_code": item.reason_code,
                }
                for item in report.evaluations
            ],
            "metrics": asdict(report.metrics),
        }
    )


class RolloutMode(StrEnum):
    DIRECT = "DIRECT"
    CANARY = "CANARY"


class GovernanceDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class GovernanceAction(StrEnum):
    PROMOTE = "PROMOTE"
    ROLLBACK = "ROLLBACK"


class PolicyDecisionKind(StrEnum):
    PROMOTION = "PROMOTION"
    ROLLBACK = "ROLLBACK"


@dataclass(frozen=True, slots=True)
class ActivePolicyRef:
    policy_family: str
    policy_id: str
    policy_version: str
    code_sha: str
    candidate_fingerprint: str | None = None

    def __post_init__(self) -> None:
        _required(self.policy_family, self.policy_id, self.policy_version, self.code_sha)
        if self.candidate_fingerprint is not None:
            _required(self.candidate_fingerprint)


@dataclass(frozen=True, slots=True)
class RolloutPlan:
    mode: RolloutMode
    canary_percent: int | None = None

    def __post_init__(self) -> None:
        if self.mode is RolloutMode.CANARY:
            if self.canary_percent is None or not 1 <= self.canary_percent < 100:
                raise ValueError("canary rollout requires percent from 1 through 99")
        elif self.canary_percent is not None:
            raise ValueError("direct rollout cannot carry canary percent")


@dataclass(frozen=True, slots=True)
class PromotionGatePolicy:
    policy_id: str
    version: str
    min_evaluated_holdout_cases: int
    max_non_replayable_cases: int
    require_zero_regressions: bool = True
    require_canary: bool = False

    def __post_init__(self) -> None:
        _required(self.policy_id, self.version)
        if self.min_evaluated_holdout_cases < 1:
            raise ValueError("promotion gate requires at least one evaluated holdout case")
        if self.max_non_replayable_cases < 0:
            raise ValueError("promotion gate non-replayable limit cannot be negative")


@dataclass(frozen=True, slots=True)
class GovernanceApproval:
    approval_id: str
    action: GovernanceAction
    candidate_id: str
    candidate_fingerprint: str
    comparison_fingerprint: str
    gate_policy_id: str
    gate_policy_version: str
    decision: GovernanceDecision
    approved_by: str
    approved_at: datetime
    rationale: str
    target_decision_id: str | None = None

    def __post_init__(self) -> None:
        _required(
            self.approval_id,
            self.candidate_id,
            self.candidate_fingerprint,
            self.comparison_fingerprint,
            self.gate_policy_id,
            self.gate_policy_version,
            self.approved_by,
            self.rationale,
        )
        if self.approved_at.tzinfo is None:
            raise ValueError("governance approval time must be timezone-aware")
        if self.action is GovernanceAction.PROMOTE:
            if self.target_decision_id is not None:
                raise ValueError("promotion approval cannot target an existing decision")
        elif self.target_decision_id is None or not self.target_decision_id.strip():
            raise ValueError("rollback approval must target the promotion decision")


@dataclass(frozen=True, slots=True)
class PolicyDecisionRecord:
    decision_id: str
    kind: PolicyDecisionKind
    policy_family: str
    decided_at: datetime
    approved_by: str
    approved_at: datetime
    approval_rationale: str
    approval_id: str
    approval_action: GovernanceAction
    from_policy: ActivePolicyRef
    to_policy: ActivePolicyRef
    reason_code: str
    gate_policy_id: str
    gate_policy_version: str
    rollout: RolloutPlan
    candidate_id: str
    candidate_fingerprint: str
    comparison_fingerprint: str
    previous_decision_id: str | None = None
    rollback_of: str | None = None

    def __post_init__(self) -> None:
        _required(
            self.decision_id,
            self.policy_family,
            self.approved_by,
            self.approval_rationale,
            self.reason_code,
            self.approval_id,
            self.candidate_id,
            self.candidate_fingerprint,
            self.comparison_fingerprint,
            self.gate_policy_id,
            self.gate_policy_version,
        )
        if self.decided_at.tzinfo is None or self.approved_at.tzinfo is None:
            raise ValueError("policy decision and approval times must be timezone-aware")
        if self.approved_at > self.decided_at:
            raise ValueError("policy decision cannot precede its approval")
        if self.from_policy.policy_family != self.policy_family:
            raise ValueError("from-policy family must match decision family")
        if self.to_policy.policy_family != self.policy_family:
            raise ValueError("to-policy family must match decision family")
        if self.kind is PolicyDecisionKind.PROMOTION:
            if self.approval_action is not GovernanceAction.PROMOTE:
                raise ValueError("promotion record requires promotion approval")
            if self.rollback_of is not None:
                raise ValueError("promotion cannot carry rollback lineage")
        else:
            if self.approval_action is not GovernanceAction.ROLLBACK:
                raise ValueError("rollback record requires rollback approval")
            if self.rollback_of is None or not self.rollback_of.strip():
                raise ValueError("rollback requires the reverted decision id")

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["decided_at"] = self.decided_at.astimezone(UTC).isoformat()
        payload["approved_at"] = self.approved_at.astimezone(UTC).isoformat()
        payload["approval_action"] = self.approval_action.value
        payload["rollout"]["mode"] = self.rollout.mode.value
        return _fingerprint(payload)


class PolicyGovernanceConflict(ValueError):
    """Raised when immutable governance history or current-policy state conflicts."""


class ActivePolicyStore(Protocol):
    """Durable append-only governance history plus current policy pointer."""

    def current(self, policy_family: str) -> ActivePolicyRef | None:
        """Return the active policy for one family."""

    def latest_decision(self, policy_family: str) -> PolicyDecisionRecord | None:
        """Return the latest immutable decision for one family."""

    def get_decision(self, decision_id: str) -> PolicyDecisionRecord | None:
        """Return one immutable governance decision."""

    def history(self, policy_family: str) -> tuple[PolicyDecisionRecord, ...]:
        """Return append-only decision history."""

    def append_and_activate(self, record: PolicyDecisionRecord) -> bool:
        """Append once and atomically move current pointer to record.to_policy."""


def _validate_promotion_evidence(
    *,
    candidate: PolicyCandidate,
    report: PolicyComparisonReport,
    gate: PromotionGatePolicy,
    rollout: RolloutPlan,
) -> str:
    if report.candidate_id != candidate.candidate_id:
        raise ValueError("comparison candidate identity mismatch")
    if report.candidate_fingerprint != candidate.fingerprint:
        raise ValueError("comparison candidate fingerprint mismatch")
    if (
        report.split_id != candidate.split_id
        or report.split_fingerprint != candidate.split_fingerprint
    ):
        raise ValueError("comparison split does not match candidate")
    recomputed_metrics = policy_counter_metrics(report.evaluations)
    if report.metrics != recomputed_metrics:
        raise ValueError("promotion report metrics do not match sealed evaluations")
    if report.metrics.evaluated_cases < gate.min_evaluated_holdout_cases:
        raise ValueError("promotion evidence has insufficient evaluated holdout cases")
    if report.metrics.non_replayable_cases > gate.max_non_replayable_cases:
        raise ValueError("promotion evidence exceeds non-replayable case limit")
    if gate.require_zero_regressions and report.metrics.has_regression:
        raise ValueError("promotion evidence contains governed regressions")
    if gate.require_canary and rollout.mode is not RolloutMode.CANARY:
        raise ValueError("promotion gate requires canary rollout")
    return comparison_fingerprint(report)


def _validate_approval(
    *,
    approval: GovernanceApproval,
    candidate: PolicyCandidate,
    report_fingerprint: str,
    gate: PromotionGatePolicy,
) -> None:
    if approval.action is not GovernanceAction.PROMOTE:
        raise ValueError("policy promotion requires a promotion-scoped approval")
    if approval.decision is not GovernanceDecision.APPROVE:
        raise ValueError("policy promotion requires explicit APPROVE decision")
    if approval.candidate_id != candidate.candidate_id:
        raise ValueError("approval candidate identity mismatch")
    if approval.candidate_fingerprint != candidate.fingerprint:
        raise ValueError("approval candidate fingerprint mismatch")
    if approval.comparison_fingerprint != report_fingerprint:
        raise ValueError("approval comparison evidence mismatch")
    if approval.gate_policy_id != gate.policy_id or approval.gate_policy_version != gate.version:
        raise ValueError("approval promotion-gate version mismatch")


def promote_policy(
    *,
    candidate: PolicyCandidate,
    report: PolicyComparisonReport,
    approval: GovernanceApproval,
    gate: PromotionGatePolicy,
    rollout: RolloutPlan,
    store: ActivePolicyStore,
    decision_id: str,
    decided_at: datetime,
) -> PolicyDecisionRecord:
    """Promote only after explicit governed evidence and human/governance approval."""

    _required(decision_id)
    if decided_at.tzinfo is None:
        raise ValueError("promotion decision time must be timezone-aware")
    active = store.current(candidate.policy_family)
    if active is None:
        raise ValueError("promotion requires an existing active baseline policy")
    if (
        active.policy_id != candidate.baseline_policy_id
        or active.policy_version != candidate.baseline_policy_version
    ):
        raise ValueError("candidate baseline is stale relative to active production policy")
    if candidate.candidate_version == active.policy_version:
        raise ValueError("candidate version must differ from active baseline")

    report_fingerprint = _validate_promotion_evidence(
        candidate=candidate,
        report=report,
        gate=gate,
        rollout=rollout,
    )
    _validate_approval(
        approval=approval,
        candidate=candidate,
        report_fingerprint=report_fingerprint,
        gate=gate,
    )
    if approval.approved_at < candidate.created_at:
        raise ValueError("promotion approval cannot predate candidate creation")
    if approval.approved_at > decided_at:
        raise ValueError("promotion decision cannot precede approval")
    latest = store.latest_decision(candidate.policy_family)
    to_policy = ActivePolicyRef(
        policy_family=candidate.policy_family,
        policy_id=candidate.baseline_policy_id,
        policy_version=candidate.candidate_version,
        code_sha=candidate.code_sha,
        candidate_fingerprint=candidate.fingerprint,
    )
    record = PolicyDecisionRecord(
        decision_id=decision_id,
        kind=PolicyDecisionKind.PROMOTION,
        policy_family=candidate.policy_family,
        decided_at=decided_at,
        approved_by=approval.approved_by,
        approved_at=approval.approved_at,
        approval_rationale=approval.rationale,
        approval_id=approval.approval_id,
        approval_action=approval.action,
        from_policy=active,
        to_policy=to_policy,
        reason_code="GOVERNED_POLICY_PROMOTION",
        gate_policy_id=gate.policy_id,
        gate_policy_version=gate.version,
        rollout=rollout,
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint,
        comparison_fingerprint=report_fingerprint,
        previous_decision_id=None if latest is None else latest.decision_id,
    )
    store.append_and_activate(record)
    return record


def rollback_policy(
    *,
    promotion_decision_id: str,
    approval: GovernanceApproval,
    gate: PromotionGatePolicy,
    store: ActivePolicyStore,
    decision_id: str,
    decided_at: datetime,
) -> PolicyDecisionRecord:
    """Append a rollback decision; never delete or rewrite promotion history."""

    _required(promotion_decision_id, decision_id)
    if decided_at.tzinfo is None:
        raise ValueError("rollback decision time must be timezone-aware")
    promotion = store.get_decision(promotion_decision_id)
    if promotion is None or promotion.kind is not PolicyDecisionKind.PROMOTION:
        raise ValueError("rollback target must be an existing promotion decision")
    active = store.current(promotion.policy_family)
    if active != promotion.to_policy:
        raise ValueError("rollback target is not the current active policy")
    if approval.action is not GovernanceAction.ROLLBACK:
        raise ValueError("policy rollback requires a rollback-scoped approval")
    if approval.target_decision_id != promotion.decision_id:
        raise ValueError("rollback approval targets a different promotion decision")
    if approval.decision is not GovernanceDecision.APPROVE:
        raise ValueError("policy rollback requires explicit APPROVE decision")
    if approval.candidate_id != promotion.candidate_id:
        raise ValueError("rollback approval candidate mismatch")
    if approval.candidate_fingerprint != promotion.candidate_fingerprint:
        raise ValueError("rollback approval candidate fingerprint mismatch")
    if approval.comparison_fingerprint != promotion.comparison_fingerprint:
        raise ValueError("rollback approval evidence mismatch")
    if approval.gate_policy_id != gate.policy_id or approval.gate_policy_version != gate.version:
        raise ValueError("rollback approval promotion-gate version mismatch")

    if approval.approved_at > decided_at:
        raise ValueError("rollback decision cannot precede approval")
    latest = store.latest_decision(promotion.policy_family)
    record = PolicyDecisionRecord(
        decision_id=decision_id,
        kind=PolicyDecisionKind.ROLLBACK,
        policy_family=promotion.policy_family,
        decided_at=decided_at,
        approved_by=approval.approved_by,
        approved_at=approval.approved_at,
        approval_rationale=approval.rationale,
        approval_id=approval.approval_id,
        approval_action=approval.action,
        from_policy=active,
        to_policy=promotion.from_policy,
        reason_code="GOVERNED_POLICY_ROLLBACK",
        gate_policy_id=gate.policy_id,
        gate_policy_version=gate.version,
        rollout=RolloutPlan(mode=RolloutMode.DIRECT),
        candidate_id=promotion.candidate_id,
        candidate_fingerprint=promotion.candidate_fingerprint,
        comparison_fingerprint=promotion.comparison_fingerprint,
        previous_decision_id=None if latest is None else latest.decision_id,
        rollback_of=promotion.decision_id,
    )
    store.append_and_activate(record)
    return record
