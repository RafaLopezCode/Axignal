from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_accounting import (
    AccountingReconciliationService,
    project_accounting_reconciliation,
)
from application.admin_financial_documents import AdminFinancialDocumentService
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_accounting import (
    AccountingCategory,
    AccountingEntry,
    AccountMapping,
    PeriodCloseState,
    ProcessorSettlement,
    ReconciliationIssueKind,
    ReconciliationIssueState,
)
from domain.admin_billing import (
    BillingEvent,
    BillingEventId,
    BillingEventKind,
    BillingPaymentState,
    BillingProvider,
)
from domain.admin_governance import AdminGovernanceCommandTarget
from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
)
from pipeline.admin_accounting import (
    AccountingStoreConflict,
    SqliteAccountingReconciliationStore,
)
from pipeline.admin_financial_documents import SqliteFinancialDocumentStore
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_integrations import SqliteAdminIntegrationStore

NOW = datetime(2026, 10, 3, 20, 5, tzinfo=UTC)
INTEGRATION_ID = "accounting-provider"


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _register_adapter(
    store: SqliteAdminIntegrationStore,
    *,
    enabled: bool = True,
    credential_state: CredentialState = CredentialState.CONFIGURED,
) -> None:
    store.append_definition(
        operation_id="register-accounting-provider",
        occurred_at=NOW,
        definition=IntegrationDefinition(
            integration_id=INTEGRATION_ID,
            provider="EXTERNAL_ACCOUNTING_PROVIDER",
            purpose="Accounting provider adapter for reconciliation imports",
            owner="AXIGNAL Finance",
            environment=IntegrationEnvironment.PRODUCTION,
            enabled=enabled,
            credential=CredentialLifecycle(
                reference=(
                    "secret://axignal/accounting/provider"
                    if credential_state
                    in {CredentialState.CONFIGURED, CredentialState.ROTATION_DUE}
                    else None
                ),
                state=credential_state,
                last_rotated_at=NOW if credential_state is CredentialState.CONFIGURED else None,
            ),
            scopes=("accounting.read", "expenses.read", "settlements.read"),
            direction=IntegrationDirection.INBOUND,
            authority_boundary=(
                "External provider owns accounting records; AXIGNAL stores reconciliation evidence only."
            ),
            webhook_capable=False,
            webhook_endpoint=None,
            rate_limit_posture="provider-governed",
            health_freshness_seconds=86400,
        ),
    )


def _billing_event() -> BillingEvent:
    return BillingEvent(
        event_id=BillingEventId("evt_invoice_ao21"),
        provider=BillingProvider.STRIPE,
        provider_event_type="invoice.paid",
        provider_created_at=NOW,
        recorded_at=NOW + timedelta(seconds=1),
        external_object_id="in_ao21",
        account_id="account:acme",
        kind=BillingEventKind.INVOICE_PAID,
        payment_state=BillingPaymentState.PAID,
        amount_minor=1210,
        currency="eur",
        source_ref="stripe:event:evt_invoice_ao21",
    )


def _stores(tmp_path: Path):
    accounting = SqliteAccountingReconciliationStore(tmp_path / "accounting.sqlite3")
    financial = SqliteFinancialDocumentStore(tmp_path / "financial.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    audit = SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3")
    return accounting, financial, integrations, audit


def _service(tmp_path: Path, *, register: bool = True):
    accounting, financial, integrations, audit = _stores(tmp_path)
    if register:
        _register_adapter(integrations)
    return (
        AccountingReconciliationService(accounting, financial, integrations, audit),
        accounting,
        financial,
        integrations,
        audit,
    )


def _mapping(
    category: AccountingCategory,
    code: str,
    *,
    mapping_id: str | None = None,
    version: int = 1,
) -> AccountMapping:
    return AccountMapping(
        mapping_id=mapping_id or f"mapping:{category.value.lower()}",
        integration_id=INTEGRATION_ID,
        category=category,
        account_code=code,
        effective_at=NOW,
        version=version,
    )


def _register_mapping(
    service: AccountingReconciliationService,
    mapping: AccountMapping,
    *,
    suffix: str,
) -> None:
    service.register_mapping(
        grant=_grant(),
        operation_id=f"mapping-op:{suffix}",
        reason="configure external chart-of-accounts mapping",
        mapping=mapping,
        now=NOW + timedelta(minutes=1),
    )


def test_accounting_import_requires_enabled_configured_ao18_adapter(tmp_path: Path) -> None:
    service, _, _, _, _ = _service(tmp_path, register=False)
    with pytest.raises(ValueError, match="not registered"):
        _register_mapping(service, _mapping(AccountingCategory.REVENUE, "700000"), suffix="missing")

    accounting, financial, integrations, audit = _stores(tmp_path / "disabled")
    _register_adapter(integrations, enabled=False)
    disabled = AccountingReconciliationService(accounting, financial, integrations, audit)
    with pytest.raises(ValueError, match="disabled"):
        _register_mapping(
            disabled, _mapping(AccountingCategory.REVENUE, "700000"), suffix="disabled"
        )

    accounting2, financial2, integrations2, audit2 = _stores(tmp_path / "missing-credential")
    _register_adapter(integrations2, credential_state=CredentialState.MISSING)
    unconfigured = AccountingReconciliationService(accounting2, financial2, integrations2, audit2)
    with pytest.raises(ValueError, match="credential is not configured"):
        _register_mapping(
            unconfigured,
            _mapping(AccountingCategory.REVENUE, "700000"),
            suffix="unconfigured",
        )


def test_chart_mapping_is_versioned_and_finance_mutations_are_audited(tmp_path: Path) -> None:
    service, accounting, _, _, audit = _service(tmp_path)
    first = _mapping(AccountingCategory.REVENUE, "700000", mapping_id="mapping:revenue")
    assert service.register_mapping(
        grant=_grant(),
        operation_id="mapping-revenue-v1",
        reason="initial revenue mapping",
        mapping=first,
        now=NOW + timedelta(minutes=1),
    )
    with pytest.raises(AccountingStoreConflict, match="out of sequence"):
        accounting.append_mapping(
            _mapping(
                AccountingCategory.REVENUE,
                "700100",
                mapping_id="mapping:revenue",
                version=3,
            )
        )
    second = _mapping(
        AccountingCategory.REVENUE,
        "700100",
        mapping_id="mapping:revenue",
        version=2,
    )
    assert service.register_mapping(
        grant=_grant(),
        operation_id="mapping-revenue-v2",
        reason="provider chart changed",
        mapping=second,
        now=NOW + timedelta(minutes=2),
    )
    assert accounting.mappings() == (second,)
    records = audit.all()
    assert len(records) == 2
    assert all(record.target is AdminGovernanceCommandTarget.FINANCE for record in records)
    assert records[-1].after_ref == "mapping:revenue:v2"


def test_billed_paid_settled_accounted_and_costs_reconcile_end_to_end(tmp_path: Path) -> None:
    service, accounting, financial, integrations, audit = _service(tmp_path)
    invoice, payment = AdminFinancialDocumentService(financial).ingest_billing_event(
        _billing_event()
    )
    assert invoice.kind.value == "INVOICE"
    assert payment.kind.value == "PAYMENT"

    for mapping, suffix in (
        (_mapping(AccountingCategory.REVENUE, "700000"), "revenue"),
        (_mapping(AccountingCategory.SETTLEMENT, "572100"), "settlement"),
        (_mapping(AccountingCategory.PROCESSOR_FEE, "626100"), "fee"),
        (_mapping(AccountingCategory.INFRASTRUCTURE_COST, "629100"), "infra"),
    ):
        _register_mapping(service, mapping, suffix=suffix)

    entries = (
        AccountingEntry(
            entry_id="acct:revenue:1",
            integration_id=INTEGRATION_ID,
            account_code="700000",
            category=AccountingCategory.REVENUE,
            occurred_at=NOW,
            recorded_at=NOW + timedelta(minutes=2),
            currency="EUR",
            signed_amount_minor=1210,
            source_ref="accounting:entry:revenue-1",
            financial_record_id=invoice.record_id,
        ),
        AccountingEntry(
            entry_id="acct:settlement:1",
            integration_id=INTEGRATION_ID,
            account_code="572100",
            category=AccountingCategory.SETTLEMENT,
            occurred_at=NOW + timedelta(days=2),
            recorded_at=NOW + timedelta(days=2, minutes=1),
            currency="EUR",
            signed_amount_minor=1175,
            source_ref="accounting:entry:settlement-1",
            settlement_id="settlement:stripe:1",
        ),
        AccountingEntry(
            entry_id="acct:fee:1",
            integration_id=INTEGRATION_ID,
            account_code="626100",
            category=AccountingCategory.PROCESSOR_FEE,
            occurred_at=NOW + timedelta(days=2),
            recorded_at=NOW + timedelta(days=2, minutes=1),
            currency="EUR",
            signed_amount_minor=-35,
            source_ref="accounting:entry:stripe-fee-1",
            settlement_id="settlement:stripe:1",
        ),
        AccountingEntry(
            entry_id="acct:infra:1",
            integration_id=INTEGRATION_ID,
            account_code="629100",
            category=AccountingCategory.INFRASTRUCTURE_COST,
            occurred_at=NOW + timedelta(days=3),
            recorded_at=NOW + timedelta(days=3, minutes=1),
            currency="EUR",
            signed_amount_minor=-500,
            source_ref="provider-bill:hosting:2026-10",
        ),
    )
    for index, entry in enumerate(entries, start=1):
        service.import_entry(
            grant=_grant(),
            operation_id=f"import-entry:{index}",
            reason="import external accounting entry with provenance",
            entry=entry,
            now=entry.recorded_at,
        )

    settlement = ProcessorSettlement(
        settlement_id="settlement:stripe:1",
        integration_id=INTEGRATION_ID,
        processor="stripe",
        occurred_at=NOW + timedelta(days=2),
        recorded_at=NOW + timedelta(days=2, minutes=1),
        currency="EUR",
        gross_minor=1210,
        fee_minor=35,
        net_minor=1175,
        source_ref="stripe:settlement:po_1",
    )
    service.import_settlement(
        grant=_grant(),
        operation_id="import-settlement:1",
        reason="import processor payout/fee evidence",
        settlement=settlement,
        now=settlement.recorded_at,
    )

    issues = service.reconcile(
        grant=_grant(),
        operation_id="reconcile:october:1",
        reason="reconcile billed paid settled and accounted values",
        now=NOW + timedelta(days=4),
    )
    assert issues == ()

    projection = project_accounting_reconciliation(
        store=accounting,
        financial_store=financial,
        integration_store=integrations,
        grant=_grant(),
        generated_at=NOW + timedelta(days=4),
    )
    assert projection.adapter_strategy == "EXTERNAL_PROVIDER_ADAPTER_VIA_AO18"
    assert projection.configured_integrations == (INTEGRATION_ID,)
    assert len(projection.totals) == 1
    total = projection.totals[0]
    assert total.currency == "EUR"
    assert total.billed_minor == 1210
    assert total.paid_minor == 1210
    assert total.refunded_minor == 0
    assert total.settled_gross_minor == 1210
    assert total.processor_fee_minor == 35
    assert total.settled_net_minor == 1175
    assert total.accounted_minor == 1210
    assert total.infrastructure_cost_minor == 500
    assert total.business_expense_minor == 0
    assert any(record.action == "accounting.reconciliation.executed" for record in audit.all())


def test_unmatched_values_remain_open_and_block_period_close(tmp_path: Path) -> None:
    service, accounting, financial, _, _ = _service(tmp_path)
    invoice, _ = AdminFinancialDocumentService(financial).ingest_billing_event(_billing_event())
    _register_mapping(
        service,
        _mapping(AccountingCategory.REVENUE, "700000"),
        suffix="revenue",
    )

    issues = service.reconcile(
        grant=_grant(),
        operation_id="reconcile:unmatched",
        reason="surface unresolved values without balancing",
        now=NOW + timedelta(days=1),
    )
    kinds = {issue.kind for issue in issues}
    assert ReconciliationIssueKind.UNMATCHED_FINANCIAL in kinds
    assert ReconciliationIssueKind.SETTLEMENT_MISMATCH in kinds
    assert all(issue.state is ReconciliationIssueState.OPEN for issue in issues)

    period = service.evaluate_period(
        grant=_grant(),
        operation_id="period:2026-10:attempt",
        reason="attempt month close",
        period_id="period:2026-10",
        period_start=NOW,
        period_end=NOW + timedelta(days=31),
        now=NOW + timedelta(days=32),
        close=True,
        source_ref="accounting:close:2026-10",
    )
    assert period.state is PeriodCloseState.BLOCKED

    for index, issue in enumerate(accounting.issues(), start=1):
        service.resolve_issue(
            grant=_grant(),
            operation_id=f"resolve:{index}",
            reason="operator reviewed external reconciliation evidence",
            issue_id=issue.issue_id,
            now=NOW + timedelta(days=33),
            resolution_ref=f"accounting:resolution:{index}",
        )
    assert all(issue.state is ReconciliationIssueState.RESOLVED for issue in accounting.issues())

    closed = service.evaluate_period(
        grant=_grant(),
        operation_id="period:2026-10:close",
        reason="close after all discrepancies were reviewed",
        period_id="period:2026-10",
        period_start=NOW,
        period_end=NOW + timedelta(days=31),
        now=NOW + timedelta(days=34),
        close=True,
        source_ref="accounting:close:2026-10",
    )
    assert closed.state is PeriodCloseState.CLOSED
    assert closed.source_ref == "accounting:close:2026-10"
    assert financial.get(invoice.record_id) == invoice


def test_unmapped_expense_is_not_silently_balanced(tmp_path: Path) -> None:
    service, accounting, _, _, _ = _service(tmp_path)
    expense = AccountingEntry(
        entry_id="acct:business-expense:1",
        integration_id=INTEGRATION_ID,
        account_code="629999",
        category=AccountingCategory.BUSINESS_EXPENSE,
        occurred_at=NOW,
        recorded_at=NOW + timedelta(minutes=1),
        currency="EUR",
        signed_amount_minor=-250,
        source_ref="supplier-invoice:software:1",
    )
    service.import_entry(
        grant=_grant(),
        operation_id="import-expense:1",
        reason="import business expense from accounting provider",
        entry=expense,
        now=expense.recorded_at,
    )
    issues = service.reconcile(
        grant=_grant(),
        operation_id="reconcile:expense",
        reason="detect unmapped imported expense",
        now=NOW + timedelta(minutes=2),
    )
    assert len(issues) == 1
    assert issues[0].kind is ReconciliationIssueKind.MISSING_ACCOUNT_MAPPING
    assert issues[0].accounting_entry_id == expense.entry_id
    assert accounting.entries() == (expense,)


def test_accounting_projection_requires_finance_read(tmp_path: Path) -> None:
    _, accounting, financial, integrations, _ = _service(tmp_path)
    with pytest.raises(PermissionError, match="admin:finance:read"):
        project_accounting_reconciliation(
            store=accounting,
            financial_store=financial,
            integration_store=integrations,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_mapping_series_must_start_at_version_one(tmp_path: Path) -> None:
    accounting = SqliteAccountingReconciliationStore(tmp_path / "accounting.sqlite3")
    with pytest.raises(AccountingStoreConflict, match="first mapping version must be 1"):
        accounting.append_mapping(
            _mapping(
                AccountingCategory.REVENUE,
                "700000",
                mapping_id="mapping:new-series",
                version=2,
            )
        )


def test_runtime_composes_accounting_store_and_admin_surface(tmp_path: Path) -> None:
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="c" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=root / "apps" / "web",
        )
    )
    assert runtime.admin_accounting_store.path.is_file()
    projection = project_accounting_reconciliation(
        store=runtime.admin_accounting_store,
        financial_store=runtime.admin_financial_document_store,
        integration_store=runtime.admin_integration_store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.adapter_strategy == "EXTERNAL_PROVIDER_ADAPTER_VIA_AO18"
    assert projection.configured_integrations == ()
    assert projection.totals == ()
    assert any("NOT authorized" in note for note in projection.coverage_notes)

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-accounting-summary" in html
    assert "Billed -> Paid -> Settled -> Accounted" in html
    assert "bootstrap.accountingReconciliation" in javascript
    assert "No accounting provider is configured yet" in javascript
