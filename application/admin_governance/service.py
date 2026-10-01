"""AO-07 governance registry, bounded command execution, audit and alerts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from application.economic_discovery.learning_memory import (
    LearningEvent,
    LearningEventKind,
    LearningOutcome,
)
from application.economic_discovery.policy_governance import ActivePolicyStore
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminRiskClass,
    AdminScope,
)
from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
    AdminGovernanceProjection,
    GovernanceAlertClass,
    GovernanceAlertState,
    GovernancePolicyChange,
    GovernancePolicyFamily,
    GovernancePolicyState,
)
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminRecordClass,
    DataCompleteness,
)


class GovernanceAuditStore(Protocol):
    def append(self, record: AdminGovernanceAuditRecord) -> bool: ...
    def all(self) -> tuple[AdminGovernanceAuditRecord, ...]: ...


@dataclass(frozen=True, slots=True)
class BoundedCommandResult:
    result_code: str
    before_ref: str | None = None
    after_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.result_code.strip():
            raise ValueError("bounded command result code is required")


_ALLOWED_TARGETS = frozenset(
    {
        AdminGovernanceCommandTarget.POLICY_GOVERNANCE,
        AdminGovernanceCommandTarget.SOURCE_ACQUISITION,
        AdminGovernanceCommandTarget.RESEARCH_EXECUTION,
        AdminGovernanceCommandTarget.INTEGRATION,
        AdminGovernanceCommandTarget.SYSTEM,
    }
)

_POLICY_FAMILIES = tuple(GovernancePolicyFamily)


class AdminGovernanceService:
    """Authorize a bounded command, route it to its owner, then append immutable audit."""

    def __init__(self, audit_store: GovernanceAuditStore) -> None:
        self._audit_store = audit_store

    def execute(
        self,
        *,
        grant: AdminAuthorizationGrant,
        command_id: str,
        target: AdminGovernanceCommandTarget,
        action: str,
        reason: str,
        occurred_at: datetime,
        handler: Callable[[], BoundedCommandResult],
        risk: AdminRiskClass = AdminRiskClass.WRITE,
        approval_ref: str | None = None,
    ) -> AdminGovernanceAuditRecord:
        if not command_id.strip() or not action.strip() or not reason.strip():
            raise ValueError("bounded governance command identity/action/reason is required")
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("bounded governance command time must be timezone-aware")
        if AdminScope.GOVERNANCE_MANAGE not in grant.scopes:
            raise PermissionError("governance command requires admin:governance:manage")
        if grant.assurance is not AdminAssurance.STEP_UP:
            raise PermissionError("governance command requires step-up assurance")
        if risk is AdminRiskClass.CRITICAL and (approval_ref is None or not approval_ref.strip()):
            raise PermissionError(
                "critical governance command requires AO-01 dual-approval evidence"
            )

        audit_id = f"audit:{command_id}"
        if target not in _ALLOWED_TARGETS:
            record = AdminGovernanceAuditRecord(
                audit_id=audit_id,
                command_id=command_id,
                occurred_at=occurred_at,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=target,
                action=action,
                reason=reason,
                required_scope=AdminScope.GOVERNANCE_MANAGE.value,
                outcome=AdminGovernanceCommandOutcome.REJECTED,
                result_code="UNSUPPORTED_CANONICAL_WRITE_TARGET",
                approval_ref=approval_ref,
            )
            self._audit_store.append(record)
            return record

        try:
            result = handler()
        except Exception as exc:
            record = AdminGovernanceAuditRecord(
                audit_id=audit_id,
                command_id=command_id,
                occurred_at=occurred_at,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=target,
                action=action,
                reason=reason,
                required_scope=AdminScope.GOVERNANCE_MANAGE.value,
                outcome=AdminGovernanceCommandOutcome.FAILED,
                result_code=f"OWNING_SERVICE_FAILED:{type(exc).__name__}",
                approval_ref=approval_ref,
            )
            self._audit_store.append(record)
            raise

        record = AdminGovernanceAuditRecord(
            audit_id=audit_id,
            command_id=command_id,
            occurred_at=occurred_at,
            actor_principal_id=str(grant.principal_id),
            actor_session_id=str(grant.session_id),
            target=target,
            action=action,
            reason=reason,
            required_scope=AdminScope.GOVERNANCE_MANAGE.value,
            outcome=AdminGovernanceCommandOutcome.COMPLETED,
            result_code=result.result_code,
            before_ref=result.before_ref,
            after_ref=result.after_ref,
            approval_ref=approval_ref,
        )
        self._audit_store.append(record)
        return record


def _policy_state(
    policy_store: ActivePolicyStore,
    family: GovernancePolicyFamily,
) -> GovernancePolicyState:
    active = policy_store.current(family.value)
    history = policy_store.history(family.value)
    if active is None:
        return GovernancePolicyState(
            family=family,
            policy_id=None,
            policy_version=None,
            code_sha=None,
            effective_at=None,
            completeness=DataCompleteness.UNKNOWN,
            source_refs=(),
            change_count=len(history),
        )
    latest = policy_store.latest_decision(family.value)
    return GovernancePolicyState(
        family=family,
        policy_id=active.policy_id,
        policy_version=active.policy_version,
        code_sha=active.code_sha,
        effective_at=None if latest is None else latest.decided_at,
        completeness=DataCompleteness.KNOWN,
        source_refs=(() if latest is None else (latest.decision_id,)),
        change_count=len(history),
    )


def _policy_changes(policy_store: ActivePolicyStore) -> tuple[GovernancePolicyChange, ...]:
    changes: list[GovernancePolicyChange] = []
    for family in _POLICY_FAMILIES:
        for decision in policy_store.history(family.value):
            changes.append(
                GovernancePolicyChange(
                    decision_id=decision.decision_id,
                    family=decision.policy_family,
                    kind=decision.kind.value,
                    actor=decision.approved_by,
                    before_policy_id=decision.from_policy.policy_id,
                    before_version=decision.from_policy.policy_version,
                    after_policy_id=decision.to_policy.policy_id,
                    after_version=decision.to_policy.policy_version,
                    reason=decision.approval_rationale,
                    effective_at=decision.decided_at,
                )
            )
    return tuple(sorted(changes, key=lambda item: (item.effective_at, item.decision_id)))


def _owner_alert_records(
    records: tuple[AdminEventEnvelope, ...],
    alert_class: GovernanceAlertClass,
) -> tuple[AdminEventEnvelope, ...]:
    expected = f"governance.alert.{alert_class.value.lower()}"
    return tuple(record for record in records if record.record_type == expected)


def _explicit_alert_state(
    records: tuple[AdminEventEnvelope, ...],
    alert_class: GovernanceAlertClass,
) -> GovernanceAlertState | None:
    matches = _owner_alert_records(records, alert_class)
    if not matches:
        return None
    return GovernanceAlertState(
        alert_class=alert_class,
        count=len(matches),
        completeness=DataCompleteness.KNOWN,
        reason="EXPLICIT_OWNER_ALERT_RECORDS",
        source_refs=tuple(str(record.record_id) for record in matches),
    )


def _alert_states(
    *,
    learning_events: tuple[LearningEvent, ...],
    admin_records: tuple[AdminEventEnvelope, ...],
    audit_records: tuple[AdminGovernanceAuditRecord, ...],
) -> tuple[GovernanceAlertState, ...]:
    output: list[GovernanceAlertState] = []

    unsupported = tuple(
        record
        for record in audit_records
        if record.result_code == "UNSUPPORTED_CANONICAL_WRITE_TARGET"
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.UNSUPPORTED_WRITE_ATTEMPT,
            count=len(unsupported),
            completeness=DataCompleteness.KNOWN,
            reason="IMMUTABLE_GOVERNANCE_AUDIT",
            source_refs=tuple(record.audit_id for record in unsupported),
        )
    )

    source_failures = tuple(
        event
        for event in learning_events
        if event.kind is LearningEventKind.SOURCE_ACQUISITION
        and event.outcome is LearningOutcome.FAILED
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.SOURCE_FAILURE,
            count=len(source_failures),
            completeness=DataCompleteness.KNOWN,
            reason="LEARNING_MEMORY_SOURCE_ACQUISITION_FAILURES",
            source_refs=tuple(event.event_id for event in source_failures),
        )
    )

    provider_failures = tuple(
        event
        for event in learning_events
        if event.provider is not None and event.outcome is LearningOutcome.FAILED
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.PROVIDER_FAILURE,
            count=len(provider_failures),
            completeness=DataCompleteness.KNOWN,
            reason="LEARNING_MEMORY_PROVIDER_ATTRIBUTED_FAILURES",
            source_refs=tuple(event.event_id for event in provider_failures),
        )
    )

    stale_records = tuple(
        record
        for record in admin_records
        if "currentness" in record.record_type and record.outcome_state == "STALE"
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.STALE_COVERAGE,
            count=len(stale_records),
            completeness=DataCompleteness.KNOWN,
            reason="OWNER_CURRENTNESS_RECORDS",
            source_refs=tuple(str(record.record_id) for record in stale_records),
        )
    )

    security_records = tuple(
        record for record in admin_records if record.record_class is AdminRecordClass.SECURITY_EVENT
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.SECURITY_INCIDENT,
            count=len(security_records),
            completeness=DataCompleteness.KNOWN,
            reason="AO03_SECURITY_EVENT_RECORDS",
            source_refs=tuple(str(record.record_id) for record in security_records),
        )
    )

    payment_records = tuple(
        record
        for record in admin_records
        if record.record_type.startswith("billing.")
        and record.outcome_state in {"FAILED", "PAYMENT_FAILED"}
    )
    output.append(
        GovernanceAlertState(
            alert_class=GovernanceAlertClass.PAYMENT_FAILURE,
            count=len(payment_records),
            completeness=DataCompleteness.KNOWN,
            reason="BILLING_OWNER_FAILURE_RECORDS",
            source_refs=tuple(str(record.record_id) for record in payment_records),
        )
    )

    for alert_class in (
        GovernanceAlertClass.COST_SPIKE,
        GovernanceAlertClass.GOVERNANCE_DRIFT,
    ):
        explicit = _explicit_alert_state(admin_records, alert_class)
        if explicit is not None:
            output.append(explicit)
        else:
            output.append(
                GovernanceAlertState(
                    alert_class=alert_class,
                    count=None,
                    completeness=DataCompleteness.UNKNOWN,
                    reason=(
                        "ALERT_POLICY_OR_OWNER_SIGNAL_UNAVAILABLE"
                        if alert_class is GovernanceAlertClass.COST_SPIKE
                        else "GOVERNANCE_DRIFT_SIGNAL_UNAVAILABLE"
                    ),
                    source_refs=(),
                )
            )
    return tuple(output)


def project_admin_governance(
    *,
    policy_store: ActivePolicyStore,
    learning_events: tuple[LearningEvent, ...],
    admin_records: tuple[AdminEventEnvelope, ...],
    audit_records: tuple[AdminGovernanceAuditRecord, ...],
    as_of: datetime,
) -> AdminGovernanceProjection:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("governance projection as_of must be timezone-aware")
    eligible_learning = tuple(event for event in learning_events if event.occurred_at <= as_of)
    eligible_admin = tuple(record for record in admin_records if record.recorded_at <= as_of)
    eligible_audit = tuple(record for record in audit_records if record.occurred_at <= as_of)
    policies = tuple(_policy_state(policy_store, family) for family in _POLICY_FAMILIES)
    policy_changes = _policy_changes(policy_store)
    alerts = _alert_states(
        learning_events=eligible_learning,
        admin_records=eligible_admin,
        audit_records=eligible_audit,
    )
    unsupported = sum(
        record.result_code == "UNSUPPORTED_CANONICAL_WRITE_TARGET" for record in eligible_audit
    )
    completeness = (
        DataCompleteness.KNOWN
        if all(policy.completeness is DataCompleteness.KNOWN for policy in policies)
        and all(alert.completeness is DataCompleteness.KNOWN for alert in alerts)
        else DataCompleteness.PARTIAL
    )
    return AdminGovernanceProjection(
        as_of=as_of,
        completeness=completeness,
        policies=policies,
        policy_changes=policy_changes,
        alerts=alerts,
        audit_records=eligible_audit,
        unsupported_canonical_write_target_count=unsupported,
        coverage_notes=(
            "Policy registry reuses FR-20 ActivePolicyStore; Admin does not own policy truth.",
            "Bounded commands invoke an owning service before audit; Admin never mutates domain stores directly.",
            "Canonical AXIGLAND/FAXT command targets are rejected before handler invocation.",
            "UNKNOWN alert state is not zero: cost-spike and governance-drift require explicit policy/owner evidence.",
            "Alerts are operational signals, never FAXT, Xignal or canonical economic truth.",
        ),
    )
