from dataclasses import replace
from datetime import UTC, datetime

import pytest

from application.admin_governance import (
    AdminGovernanceService,
    BoundedCommandResult,
    project_admin_governance,
)
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
)
from application.economic_discovery.policy_governance import (
    ActivePolicyRef,
    GovernanceAction,
    PolicyDecisionKind,
    PolicyDecisionRecord,
    RolloutMode,
    RolloutPlan,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRiskClass,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_governance import (
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
    GovernanceAlertClass,
    GovernancePolicyFamily,
)
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)
from pipeline.admin_governance import (
    AdminGovernanceAuditConflict,
    SqliteAdminGovernanceAuditStore,
)
from pipeline.policy_governance import SqliteActivePolicyStore

NOW = datetime(2026, 10, 1, 23, 0, tzinfo=UTC)


def _grant(*, step_up: bool = True) -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("session:ao07"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP if step_up else AdminAssurance.PRIMARY,
    )


def _learning(
    event_id: str,
    *,
    kind: LearningEventKind,
    outcome: LearningOutcome,
    provider: str | None = None,
) -> LearningEvent:
    return LearningEvent(
        event_id=event_id,
        kind=kind,
        outcome=outcome,
        occurred_at=NOW,
        subject_id="org:ao07",
        activity_ref=f"activity:{event_id}",
        policy_id="test-policy",
        policy_version="1",
        code_sha="a" * 40,
        mechanism=(
            LearningMechanism.STRUCTURED_EVALUATOR
            if provider is not None
            else LearningMechanism.DETERMINISTIC
        ),
        input_fingerprint=f"input:{event_id}",
        reason_code="TEST",
        provider=provider,
        provider_version=None if provider is None else "model-1",
        cost=LearningCost(),
        yield_=LearningYield(),
    )


def _admin_record(
    record_id: str,
    record_type: str,
    outcome: str,
    *,
    record_class: AdminRecordClass = AdminRecordClass.OPERATIONAL_EVENT,
) -> AdminEventEnvelope:
    return AdminEventEnvelope(
        record_id=AdminRecordId(record_id),
        record_type=record_type,
        record_class=record_class,
        schema_version=1,
        producer="owner",
        owning_domain="owner-domain",
        recorded_at=NOW,
        outcome_state=outcome,
        completeness=DataCompleteness.KNOWN,
        privacy_class=AdminPrivacyClass.INTERNAL,
        provenance_refs=(f"source:{record_id}",),
    )


def test_bounded_command_routes_to_owner_then_records_before_after_reason(tmp_path) -> None:
    audits = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    service = AdminGovernanceService(audits)
    called = []

    def owner_service() -> BoundedCommandResult:
        called.append("called")
        return BoundedCommandResult(
            result_code="POLICY_PROMOTED",
            before_ref="policy:prime:v1",
            after_ref="policy:prime:v2",
        )

    record = service.execute(
        grant=_grant(),
        command_id="command:promote:v2",
        target=AdminGovernanceCommandTarget.POLICY_GOVERNANCE,
        action="PROMOTE_POLICY",
        reason="approved holdout and canary evidence",
        occurred_at=NOW,
        handler=owner_service,
        approval_ref="approval:human:2",
    )

    assert called == ["called"]
    assert record.outcome is AdminGovernanceCommandOutcome.COMPLETED
    assert record.before_ref == "policy:prime:v1"
    assert record.after_ref == "policy:prime:v2"
    assert record.actor_principal_id == "admin:founder"
    assert record.reason == "approved holdout and canary evidence"
    assert audits.all() == (record,)


def test_canonical_target_is_rejected_before_handler_and_audited(tmp_path) -> None:
    audits = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    service = AdminGovernanceService(audits)
    called = []

    record = service.execute(
        grant=_grant(),
        command_id="command:bad-write",
        target=AdminGovernanceCommandTarget.AXIGLAND_CANONICAL,
        action="WRITE_FAXT",
        reason="must be rejected",
        occurred_at=NOW,
        handler=lambda: called.append("wrong") or BoundedCommandResult("WRONG"),
    )

    assert called == []
    assert record.outcome is AdminGovernanceCommandOutcome.REJECTED
    assert record.result_code == "UNSUPPORTED_CANONICAL_WRITE_TARGET"


def test_governance_command_requires_manage_scope_and_step_up(tmp_path) -> None:
    audits = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    service = AdminGovernanceService(audits)
    with pytest.raises(PermissionError, match="step-up"):
        service.execute(
            grant=_grant(step_up=False),
            command_id="command:no-stepup",
            target=AdminGovernanceCommandTarget.SYSTEM,
            action="RESTART_OWNED_RUNTIME",
            reason="test",
            occurred_at=NOW,
            handler=lambda: BoundedCommandResult("OK"),
        )
    assert audits.all() == ()


def test_governance_audit_is_idempotent_but_immutable(tmp_path) -> None:
    store = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    service = AdminGovernanceService(store)
    record = service.execute(
        grant=_grant(),
        command_id="command:one",
        target=AdminGovernanceCommandTarget.SYSTEM,
        action="TEST",
        reason="same",
        occurred_at=NOW,
        handler=lambda: BoundedCommandResult("OK"),
    )
    assert store.append(record) is False
    changed = replace(record, reason="different")
    with pytest.raises(AdminGovernanceAuditConflict):
        store.append(changed)


def test_registry_and_alert_projection_preserve_unknown_and_zero_semantics(tmp_path) -> None:
    policies = SqliteActivePolicyStore(tmp_path / "policies.sqlite3")
    baseline = ActivePolicyRef(
        policy_family=GovernancePolicyFamily.EXECUTION_BUDGET.value,
        policy_id="prime-execution-budget",
        policy_version="1",
        code_sha="b" * 40,
    )
    policies.seed_active(baseline)
    promoted = ActivePolicyRef(
        policy_family=GovernancePolicyFamily.EXECUTION_BUDGET.value,
        policy_id="prime-execution-budget",
        policy_version="2",
        code_sha="c" * 40,
        candidate_fingerprint="candidate:fingerprint",
    )
    policies.append_and_activate(
        PolicyDecisionRecord(
            decision_id="decision:budget:v2",
            kind=PolicyDecisionKind.PROMOTION,
            policy_family=GovernancePolicyFamily.EXECUTION_BUDGET.value,
            decided_at=NOW,
            approved_by="governance:human:1",
            approved_at=NOW,
            approval_rationale="holdout evidence approved",
            approval_id="approval:budget:v2",
            approval_action=GovernanceAction.PROMOTE,
            from_policy=baseline,
            to_policy=promoted,
            reason_code="GOVERNED_POLICY_PROMOTION",
            gate_policy_id="promotion-gate",
            gate_policy_version="1",
            rollout=RolloutPlan(mode=RolloutMode.CANARY, canary_percent=10),
            candidate_id="candidate:budget:v2",
            candidate_fingerprint="candidate:fingerprint",
            comparison_fingerprint="comparison:fingerprint",
        )
    )
    audits = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    learning = (
        _learning(
            "source-failed",
            kind=LearningEventKind.SOURCE_ACQUISITION,
            outcome=LearningOutcome.FAILED,
        ),
        _learning(
            "provider-failed",
            kind=LearningEventKind.STRUCTURED_EVALUATION,
            outcome=LearningOutcome.FAILED,
            provider="provider-a",
        ),
    )
    records = (
        _admin_record("stale", "axigland.currentness", "STALE"),
        _admin_record("pay", "billing.payment", "PAYMENT_FAILED"),
        _admin_record(
            "security",
            "security.incident",
            "OPEN",
            record_class=AdminRecordClass.SECURITY_EVENT,
        ),
    )
    projection = project_admin_governance(
        policy_store=policies,
        learning_events=learning,
        admin_records=records,
        audit_records=audits.all(),
        as_of=NOW,
    )

    by_family = {item.family: item for item in projection.policies}
    assert by_family[GovernancePolicyFamily.EXECUTION_BUDGET].completeness is DataCompleteness.KNOWN
    assert by_family[GovernancePolicyFamily.EXECUTION_BUDGET].policy_version == "2"
    assert by_family[GovernancePolicyFamily.RETENTION].completeness is DataCompleteness.UNKNOWN
    assert projection.policy_changes[0].actor == "governance:human:1"
    assert projection.policy_changes[0].before_version == "1"
    assert projection.policy_changes[0].after_version == "2"
    assert projection.policy_changes[0].reason == "holdout evidence approved"
    assert projection.policy_changes[0].effective_at == NOW

    alerts = {item.alert_class: item for item in projection.alerts}
    assert alerts[GovernanceAlertClass.UNSUPPORTED_WRITE_ATTEMPT].count == 0
    assert alerts[GovernanceAlertClass.SOURCE_FAILURE].count == 1
    assert alerts[GovernanceAlertClass.PROVIDER_FAILURE].count == 1
    assert alerts[GovernanceAlertClass.STALE_COVERAGE].count == 1
    assert alerts[GovernanceAlertClass.PAYMENT_FAILURE].count == 1
    assert alerts[GovernanceAlertClass.SECURITY_INCIDENT].count == 1
    assert alerts[GovernanceAlertClass.COST_SPIKE].count is None
    assert alerts[GovernanceAlertClass.COST_SPIKE].completeness is DataCompleteness.UNKNOWN
    assert projection.unsupported_canonical_write_target_count == 0


def test_critical_command_requires_prior_ao01_dual_approval_evidence(tmp_path) -> None:
    audits = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    service = AdminGovernanceService(audits)
    called = []
    with pytest.raises(PermissionError, match="dual-approval evidence"):
        service.execute(
            grant=_grant(),
            command_id="command:critical",
            target=AdminGovernanceCommandTarget.SYSTEM,
            action="CRITICAL_SYSTEM_CHANGE",
            reason="high-impact test",
            occurred_at=NOW,
            handler=lambda: called.append("wrong") or BoundedCommandResult("WRONG"),
            risk=AdminRiskClass.CRITICAL,
        )
    assert called == []
    assert audits.all() == ()
