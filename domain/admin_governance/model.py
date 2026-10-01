"""AO-07 Admin governance, bounded-command audit and alert semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domain.admin_observability import DataCompleteness


class GovernancePolicyFamily(StrEnum):
    EXECUTION_BUDGET = "execution-budget"
    SOURCE_ACQUISITION = "source-acquisition"
    TEMPORAL_CURRENTNESS = "temporal-currentness"
    RETENTION = "retention"
    PROVIDER_ROUTING = "prime-routing"
    CANONICAL_ADMISSION = "canonical-admission"
    ALERTING = "alerting"


class GovernanceAlertClass(StrEnum):
    UNSUPPORTED_WRITE_ATTEMPT = "UNSUPPORTED_WRITE_ATTEMPT"
    STALE_COVERAGE = "STALE_COVERAGE"
    SOURCE_FAILURE = "SOURCE_FAILURE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    COST_SPIKE = "COST_SPIKE"
    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    GOVERNANCE_DRIFT = "GOVERNANCE_DRIFT"


class AdminGovernanceCommandTarget(StrEnum):
    POLICY_GOVERNANCE = "POLICY_GOVERNANCE"
    SOURCE_ACQUISITION = "SOURCE_ACQUISITION"
    RESEARCH_EXECUTION = "RESEARCH_EXECUTION"
    INTEGRATION = "INTEGRATION"
    SYSTEM = "SYSTEM"
    AXIGLAND_CANONICAL = "AXIGLAND_CANONICAL"
    FAXT_STORE = "FAXT_STORE"


class AdminGovernanceCommandOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class GovernancePolicyState:
    family: GovernancePolicyFamily
    policy_id: str | None
    policy_version: str | None
    code_sha: str | None
    effective_at: datetime | None
    completeness: DataCompleteness
    source_refs: tuple[str, ...]
    change_count: int

    def __post_init__(self) -> None:
        if self.change_count < 0:
            raise ValueError("policy change count cannot be negative")
        if self.completeness is DataCompleteness.KNOWN and (
            not self.policy_id or not self.policy_version or not self.code_sha
        ):
            raise ValueError("known policy state requires complete policy identity")


@dataclass(frozen=True, slots=True)
class GovernancePolicyChange:
    decision_id: str
    family: str
    kind: str
    actor: str
    before_policy_id: str
    before_version: str
    after_policy_id: str
    after_version: str
    reason: str
    effective_at: datetime

    def __post_init__(self) -> None:
        values = (
            self.decision_id,
            self.family,
            self.kind,
            self.actor,
            self.before_policy_id,
            self.before_version,
            self.after_policy_id,
            self.after_version,
            self.reason,
        )
        if any(not value.strip() for value in values):
            raise ValueError("policy change audit fields are required")
        if self.effective_at.tzinfo is None or self.effective_at.utcoffset() is None:
            raise ValueError("policy change effective time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class GovernanceAlertState:
    alert_class: GovernanceAlertClass
    count: int | None
    completeness: DataCompleteness
    reason: str | None
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.count is not None and self.count < 0:
            raise ValueError("alert count cannot be negative")
        if self.completeness is DataCompleteness.KNOWN and self.count is None:
            raise ValueError("known alert state requires a count")
        if (
            self.completeness in {DataCompleteness.UNKNOWN, DataCompleteness.UNAVAILABLE}
            and not self.reason
        ):
            raise ValueError("unknown alert state requires reason")


@dataclass(frozen=True, slots=True)
class AdminGovernanceAuditRecord:
    audit_id: str
    command_id: str
    occurred_at: datetime
    actor_principal_id: str
    actor_session_id: str
    target: AdminGovernanceCommandTarget
    action: str
    reason: str
    required_scope: str
    outcome: AdminGovernanceCommandOutcome
    result_code: str
    before_ref: str | None = None
    after_ref: str | None = None
    approval_ref: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.audit_id,
            self.command_id,
            self.actor_principal_id,
            self.actor_session_id,
            self.action,
            self.reason,
            self.required_scope,
            self.result_code,
        )
        if any(not value.strip() for value in required):
            raise ValueError("governance audit identity/reason/result is required")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("governance audit time must be timezone-aware")

    @property
    def fingerprint(self) -> str:
        payload = {
            "audit_id": self.audit_id,
            "command_id": self.command_id,
            "occurred_at": self.occurred_at.isoformat(),
            "actor_principal_id": self.actor_principal_id,
            "actor_session_id": self.actor_session_id,
            "target": self.target.value,
            "action": self.action,
            "reason": self.reason,
            "required_scope": self.required_scope,
            "outcome": self.outcome.value,
            "result_code": self.result_code,
            "before_ref": self.before_ref,
            "after_ref": self.after_ref,
            "approval_ref": self.approval_ref,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class AdminGovernanceProjection:
    as_of: datetime
    completeness: DataCompleteness
    policies: tuple[GovernancePolicyState, ...]
    policy_changes: tuple[GovernancePolicyChange, ...]
    alerts: tuple[GovernanceAlertState, ...]
    audit_records: tuple[AdminGovernanceAuditRecord, ...]
    unsupported_canonical_write_target_count: int
    coverage_notes: tuple[str, ...]
