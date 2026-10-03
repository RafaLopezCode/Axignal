from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_tax_operations import (
    TaxOperationsService,
    advisor_exports,
    canonical_es_tax_rules,
    project_tax_operations,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_governance import AdminGovernanceCommandTarget
from domain.admin_tax_operations import (
    TaxApplicabilityState,
    TaxEvidence,
    TaxEvidenceKind,
    TaxObligation,
    TaxObligationState,
)
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_tax_operations import (
    SqliteTaxOperationsStore,
    TaxOperationsStoreConflict,
)

NOW = datetime(2026, 10, 3, 21, 15, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _stores(tmp_path: Path):
    return (
        SqliteTaxOperationsStore(tmp_path / "tax.sqlite3"),
        SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3"),
    )


def _install_rules(store: SqliteTaxOperationsStore) -> None:
    for rule in canonical_es_tax_rules():
        store.append_rule(rule)


def _obligation(
    *,
    obligation_id: str = "tax:303:2026q3",
    applicability: TaxApplicabilityState = TaxApplicabilityState.APPLIES,
    due_at: datetime = datetime(2026, 10, 20, 23, 59, tzinfo=UTC),
) -> TaxObligation:
    return TaxObligation(
        obligation_id=obligation_id,
        taxpayer_ref="taxpayer:axignal",
        rule_id="es:iva:303:quarterly:2026-10-03",
        model_code="303",
        period_start=datetime(2026, 7, 1, tzinfo=UTC),
        period_end=datetime(2026, 10, 1, tzinfo=UTC),
        due_at=due_at,
        deadline_source_ref="aeat:calendar:2026:model303:q3",
        applicability=applicability,
        created_at=NOW,
    )


def _evidence(
    obligation_id: str,
    kind: TaxEvidenceKind,
    *,
    suffix: str | None = None,
) -> TaxEvidence:
    suffix = suffix or kind.value.lower()
    return TaxEvidence(
        evidence_id=f"tax-evidence:{obligation_id}:{suffix}",
        obligation_id=obligation_id,
        kind=kind,
        observed_at=NOW,
        source_ref=f"artifact:{obligation_id}:{suffix}",
        artifact_fingerprint="sha256:" + "b" * 64,
        actor_ref="admin:founder" if kind is TaxEvidenceKind.HUMAN_APPROVAL else None,
    )


def _service(tmp_path: Path):
    store, audit = _stores(tmp_path)
    _install_rules(store)
    return TaxOperationsService(store, audit), store, audit


def test_canonical_rules_are_versioned_and_do_not_assume_conditional_models_apply() -> None:
    rules = canonical_es_tax_rules()
    assert {rule.model_code for rule in rules} >= {"303", "390", "349"}
    model_390 = next(rule for rule in rules if rule.model_code == "390")
    assert "Exemptions exist" in model_390.applicability_policy
    assert all(rule.source_refs for rule in rules)


def test_unknown_applicability_remains_unknown_even_after_due_date(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    obligation = _obligation(
        applicability=TaxApplicabilityState.UNKNOWN,
        due_at=datetime(2026, 10, 2, 12, 0, tzinfo=UTC),
    )
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:unknown",
        reason="calendar candidate pending applicability evidence",
        obligation=obligation,
        now=NOW,
    )

    view = project_tax_operations(
        store=store,
        grant=_grant(),
        generated_at=NOW,
    ).obligations[0]

    assert view.state is TaxObligationState.UNKNOWN
    assert view.overdue is False
    assert view.complete is False
    assert view.missing_evidence == (TaxEvidenceKind.APPLICABILITY,)


def test_not_applicable_requires_applicability_evidence(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    obligation = _obligation(
        obligation_id="tax:390:2026",
        applicability=TaxApplicabilityState.NOT_APPLICABLE,
    )
    obligation = TaxObligation(
        obligation_id=obligation.obligation_id,
        taxpayer_ref=obligation.taxpayer_ref,
        rule_id="es:iva:390:annual:2026-10-03",
        model_code="390",
        period_start=datetime(2026, 1, 1, tzinfo=UTC),
        period_end=datetime(2027, 1, 1, tzinfo=UTC),
        due_at=datetime(2027, 1, 30, 23, 59, tzinfo=UTC),
        deadline_source_ref="aeat:calendar:2027:model390",
        applicability=TaxApplicabilityState.NOT_APPLICABLE,
        created_at=NOW,
    )
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:390",
        reason="track annual VAT summary applicability",
        obligation=obligation,
        now=NOW,
    )
    before = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert before.state is TaxObligationState.UNKNOWN
    assert before.complete is False

    service.record_evidence(
        grant=_grant(),
        operation_id="tax-evidence:390-applicability",
        reason="accountant confirmed applicable exemption",
        evidence=_evidence(obligation.obligation_id, TaxEvidenceKind.APPLICABILITY),
        now=NOW,
    )
    after = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert after.state is TaxObligationState.NOT_APPLICABLE
    assert after.complete is True


def test_prepared_filed_and_accepted_are_distinct_evidence_states(tmp_path: Path) -> None:
    service, store, audit = _service(tmp_path)
    obligation = _obligation()
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:303-q3",
        reason="instantiate Q3 VAT obligation from official calendar",
        obligation=obligation,
        now=NOW,
    )

    initial = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert initial.state is TaxObligationState.DUE
    assert initial.complete is False

    for index, kind in enumerate(
        (
            TaxEvidenceKind.APPLICABILITY,
            TaxEvidenceKind.SOURCE_DOCUMENT_SET,
            TaxEvidenceKind.RECONCILIATION,
            TaxEvidenceKind.HUMAN_APPROVAL,
        ),
        start=1,
    ):
        service.record_evidence(
            grant=_grant(),
            operation_id=f"tax-prep:{index}",
            reason="prepare VAT filing with source/reconciliation/accountant evidence",
            evidence=_evidence(obligation.obligation_id, kind),
            now=NOW,
        )

    prepared = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert prepared.state is TaxObligationState.PREPARED
    assert prepared.complete is False

    service.record_evidence(
        grant=_grant(),
        operation_id="tax-filed:303-q3",
        reason="record AEAT submission receipt",
        evidence=_evidence(obligation.obligation_id, TaxEvidenceKind.FILING_RECEIPT),
        now=NOW,
    )
    filed = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert filed.state is TaxObligationState.FILED
    assert filed.complete is False

    service.record_evidence(
        grant=_grant(),
        operation_id="tax-accepted:303-q3",
        reason="record AEAT acceptance evidence",
        evidence=_evidence(obligation.obligation_id, TaxEvidenceKind.AEAT_ACCEPTANCE),
        now=NOW,
    )
    accepted = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert accepted.state is TaxObligationState.ACCEPTED
    assert accepted.complete is True
    assert accepted.missing_evidence == ()

    records = audit.all()
    assert records
    assert all(record.target is AdminGovernanceCommandTarget.FISCAL for record in records)


def test_rejection_prevails_and_incomplete_due_obligation_can_be_overdue(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    obligation = _obligation(due_at=datetime(2026, 10, 1, 12, 0, tzinfo=UTC))
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:overdue",
        reason="track overdue VAT obligation",
        obligation=obligation,
        now=NOW,
    )
    due = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert due.state is TaxObligationState.DUE
    assert due.overdue is True

    service.record_evidence(
        grant=_grant(),
        operation_id="tax-rejected:303-q3",
        reason="record AEAT rejection",
        evidence=_evidence(obligation.obligation_id, TaxEvidenceKind.AEAT_REJECTION),
        now=NOW,
    )
    rejected = project_tax_operations(store=store, grant=_grant(), generated_at=NOW).obligations[0]
    assert rejected.state is TaxObligationState.REJECTED
    assert rejected.complete is False
    assert rejected.overdue is True


def test_advisor_export_preserves_deadline_and_evidence_without_claiming_completion(
    tmp_path: Path,
) -> None:
    service, store, _ = _service(tmp_path)
    obligation = _obligation()
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:export",
        reason="prepare advisor export",
        obligation=obligation,
        now=NOW,
    )
    service.record_evidence(
        grant=_grant(),
        operation_id="tax-export:source-docs",
        reason="attach source document bundle",
        evidence=_evidence(obligation.obligation_id, TaxEvidenceKind.SOURCE_DOCUMENT_SET),
        now=NOW,
    )

    row = advisor_exports(store=store, grant=_grant(), generated_at=NOW)[0]
    assert row.model_code == "303"
    assert row.deadline_source_ref == "aeat:calendar:2026:model303:q3"
    assert row.evidence_refs
    assert row.complete is False
    assert row.state == "DUE"


def test_same_evidence_identity_with_different_content_fails_closed(tmp_path: Path) -> None:
    service, store, _ = _service(tmp_path)
    obligation = _obligation()
    service.create_obligation(
        grant=_grant(),
        operation_id="tax-create:conflict",
        reason="test immutable tax evidence",
        obligation=obligation,
        now=NOW,
    )
    evidence = _evidence(obligation.obligation_id, TaxEvidenceKind.APPLICABILITY)
    assert store.append_evidence(evidence) is True
    changed = TaxEvidence(
        evidence_id=evidence.evidence_id,
        obligation_id=evidence.obligation_id,
        kind=evidence.kind,
        observed_at=evidence.observed_at + timedelta(seconds=1),
        source_ref=evidence.source_ref,
        artifact_fingerprint=evidence.artifact_fingerprint,
        actor_ref=evidence.actor_ref,
    )
    with pytest.raises(TaxOperationsStoreConflict):
        store.append_evidence(changed)


def test_tax_projection_requires_fiscal_read_scope(tmp_path: Path) -> None:
    _, store, _ = _service(tmp_path)
    with pytest.raises(PermissionError, match="admin:fiscal:read"):
        project_tax_operations(
            store=store,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_runtime_installs_versioned_tax_rules_and_admin_starts_without_obligations(
    tmp_path: Path,
) -> None:
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="e" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=root / "apps" / "web",
        )
    )

    assert runtime.admin_tax_operations_store.path.is_file()
    rules = runtime.admin_tax_operations_store.rules()
    assert len(rules) == 5
    assert all("2026-10-03" in rule.rule_id for rule in rules)

    projection = project_tax_operations(
        store=runtime.admin_tax_operations_store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.ruleset_version == "es-tax-operations-2026-10-03"
    assert projection.obligations == ()

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-tax-obligations" in html
    assert "Tax obligations and filing evidence" in html
    assert "bootstrap.taxOperations" in javascript
    assert "No instantiated tax obligations" in javascript
