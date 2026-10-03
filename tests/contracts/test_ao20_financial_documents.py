from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_financial_documents import (
    AdminFinancialDocumentService,
    project_financial_documents,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_billing import (
    BillingEvent,
    BillingEventId,
    BillingEventKind,
    BillingPaymentState,
    BillingProvider,
)
from domain.admin_financial_documents import (
    FinancialRecord,
    FinancialRecordKind,
    FinancialRecordState,
    FinancialSource,
    TaxBasisState,
)
from pipeline.admin_financial_documents import (
    FinancialDocumentStoreConflict,
    SqliteFinancialDocumentStore,
)

NOW = datetime(2026, 10, 3, 19, 30, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _billing(
    *,
    event_id: str,
    kind: BillingEventKind,
    amount: int,
    object_id: str,
    state: BillingPaymentState,
) -> BillingEvent:
    return BillingEvent(
        event_id=BillingEventId(event_id),
        provider=BillingProvider.STRIPE,
        provider_event_type={
            BillingEventKind.INVOICE_PAID: "invoice.paid",
            BillingEventKind.PAYMENT_FAILED: "invoice.payment_failed",
            BillingEventKind.REFUND_RECORDED: "charge.refunded",
        }[kind],
        provider_created_at=NOW,
        recorded_at=NOW + timedelta(seconds=1),
        external_object_id=object_id,
        account_id="account:acme",
        kind=kind,
        payment_state=state,
        amount_minor=amount,
        currency="eur",
        source_ref=f"stripe:event:{event_id}",
    )


def test_invoice_and_payment_are_distinct_immutable_records(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    service = AdminFinancialDocumentService(store)
    event = _billing(
        event_id="evt_invoice_1",
        kind=BillingEventKind.INVOICE_PAID,
        amount=1490,
        object_id="in_123",
        state=BillingPaymentState.PAID,
    )

    records = service.ingest_billing_event(event)

    assert [record.kind for record in records] == [
        FinancialRecordKind.INVOICE,
        FinancialRecordKind.PAYMENT,
    ]
    assert records[0].record_id != records[1].record_id
    assert records[0].source.object_ref == "in_123"
    assert records[1].source.object_ref == "in_123"
    assert records[0].tax_basis_state is TaxBasisState.UNKNOWN
    assert records[0].net_minor is None
    assert records[0].tax_minor is None
    assert service.ingest_billing_event(event) == records
    assert len(store.all()) == 2


def test_same_record_identity_with_different_content_fails_closed(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    source = FinancialSource(system="manual", object_ref="doc:1", adapter_ref="adapter:test")
    original = FinancialRecord(
        record_id="financial:invoice:manual-1",
        account_id="account:acme",
        kind=FinancialRecordKind.INVOICE,
        state=FinancialRecordState.ISSUED,
        occurred_at=NOW,
        recorded_at=NOW,
        currency="EUR",
        gross_minor=1210,
        source=source,
        tax_basis_state=TaxBasisState.KNOWN,
        net_minor=1000,
        tax_minor=210,
    )
    assert store.append(original) is True
    changed = FinancialRecord(
        record_id=original.record_id,
        account_id=original.account_id,
        kind=original.kind,
        state=original.state,
        occurred_at=original.occurred_at,
        recorded_at=original.recorded_at,
        currency=original.currency,
        gross_minor=1209,
        source=source,
        tax_basis_state=TaxBasisState.UNKNOWN,
    )
    with pytest.raises(FinancialDocumentStoreConflict):
        store.append(changed)


def test_credit_note_preserves_invoice_history_and_export_reconciles(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    service = AdminFinancialDocumentService(store)
    invoice, payment = service.ingest_billing_event(
        _billing(
            event_id="evt_invoice_2",
            kind=BillingEventKind.INVOICE_PAID,
            amount=1210,
            object_id="in_456",
            state=BillingPaymentState.PAID,
        )
    )
    credit = service.record_credit_note(
        grant=_grant(),
        record_id="financial:credit-note:cn-1",
        account_id="account:acme",
        corrects_record_id=invoice.record_id,
        occurred_at=NOW + timedelta(days=1),
        recorded_at=NOW + timedelta(days=1, seconds=1),
        currency="EUR",
        gross_minor=1210,
        source=FinancialSource(
            system="accounting-adapter",
            object_ref="credit-note:CN-1",
            adapter_ref="adapter:future-accounting",
        ),
        document_number="CN-1",
        tax_basis_state=TaxBasisState.KNOWN,
        net_minor=1000,
        tax_minor=210,
    )

    assert store.get(invoice.record_id) == invoice
    assert credit.corrects_record_id == invoice.record_id
    projection = project_financial_documents(
        store=store,
        grant=_grant(),
        generated_at=NOW + timedelta(days=1),
    )
    by_id = {row.record_id: row for row in projection.exports}
    assert by_id[invoice.record_id].signed_gross_minor == 1210
    assert by_id[payment.record_id].signed_gross_minor == 1210
    assert by_id[credit.record_id].signed_gross_minor == -1210
    assert (
        sum(
            row.signed_gross_minor
            for row in projection.exports
            if row.kind in {"INVOICE", "CREDIT_NOTE"}
        )
        == 0
    )


def test_refund_is_distinct_from_payment_and_is_negative_in_export(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    service = AdminFinancialDocumentService(store)
    records = service.ingest_billing_event(
        _billing(
            event_id="evt_refund_1",
            kind=BillingEventKind.REFUND_RECORDED,
            amount=500,
            object_id="ch_123",
            state=BillingPaymentState.REFUNDED,
        )
    )
    assert len(records) == 1
    assert records[0].kind is FinancialRecordKind.REFUND
    projection = project_financial_documents(store=store, grant=_grant(), generated_at=NOW)
    assert projection.exports[0].signed_gross_minor == -500


def test_external_adapter_document_requires_finance_write_and_adapter_ref(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    service = AdminFinancialDocumentService(store)
    record = FinancialRecord(
        record_id="financial:invoice:external-1",
        account_id="account:acme",
        kind=FinancialRecordKind.INVOICE,
        state=FinancialRecordState.ISSUED,
        occurred_at=NOW,
        recorded_at=NOW,
        currency="EUR",
        gross_minor=1210,
        source=FinancialSource(system="accounting", object_ref="invoice:external-1"),
        tax_basis_state=TaxBasisState.UNKNOWN,
    )
    with pytest.raises(ValueError, match="adapter_ref"):
        service.record_external_document(grant=_grant(), record=record)


def test_financial_projection_requires_finance_read_scope(tmp_path: Path) -> None:
    store = SqliteFinancialDocumentStore(tmp_path / "finance.sqlite3")
    with pytest.raises(PermissionError, match="admin:finance:read"):
        project_financial_documents(
            store=store,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_runtime_composes_durable_financial_store_and_admin_surface(tmp_path: Path) -> None:
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="b" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=root / "apps" / "web",
        )
    )
    assert runtime.admin_financial_document_store.path.is_file()
    projection = project_financial_documents(
        store=runtime.admin_financial_document_store,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.records == ()

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-finance-observatory" in html
    assert "Invoices / Payments / Refunds / Credit Notes" in html
    assert "bootstrap.financialDocuments" in javascript
    assert "Tax basis" in javascript
