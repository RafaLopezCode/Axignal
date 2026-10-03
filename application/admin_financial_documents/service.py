"""AO-20 application service over immutable private financial records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_billing import BillingEvent, BillingEventKind
from domain.admin_financial_documents import (
    FinancialExportRow,
    FinancialRecord,
    FinancialRecordKind,
    FinancialRecordState,
    FinancialSource,
    TaxBasisState,
    export_row,
)


class FinancialDocumentStore(Protocol):
    def append(self, record: FinancialRecord) -> bool: ...
    def get(self, record_id: str) -> FinancialRecord | None: ...
    def all(self) -> tuple[FinancialRecord, ...]: ...
    def for_account(self, account_id: str) -> tuple[FinancialRecord, ...]: ...
    def for_billing_event(self, billing_event_id: str) -> tuple[FinancialRecord, ...]: ...


@dataclass(frozen=True, slots=True)
class FinancialDocumentProjection:
    generated_at: datetime
    privacy_class: str
    records: tuple[FinancialRecord, ...]
    exports: tuple[FinancialExportRow, ...]
    coverage_notes: tuple[str, ...]


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FINANCE_READ not in grant.scopes:
        raise PermissionError("financial documents require admin:finance:read")


def _require_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FINANCE_WRITE not in grant.scopes:
        raise PermissionError("financial document write requires admin:finance:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("financial document write requires STEP_UP assurance")


class AdminFinancialDocumentService:
    def __init__(self, store: FinancialDocumentStore) -> None:
        self._store = store

    def _record_from_billing(
        self,
        *,
        event: BillingEvent,
        record_id: str,
        kind: FinancialRecordKind,
        state: FinancialRecordState,
        document_number: str | None = None,
    ) -> FinancialRecord:
        if event.amount_minor is None or event.currency is None:
            raise ValueError("billing event lacks monetary amount/currency")
        return FinancialRecord(
            record_id=record_id,
            account_id=event.account_id,
            kind=kind,
            state=state,
            occurred_at=event.provider_created_at,
            recorded_at=event.recorded_at,
            currency=event.currency,
            gross_minor=event.amount_minor,
            source=FinancialSource(
                system=event.provider.value.lower(),
                object_ref=event.external_object_id,
                event_ref=str(event.event_id),
            ),
            billing_event_id=str(event.event_id),
            document_number=document_number,
            tax_basis_state=TaxBasisState.UNKNOWN,
        )

    def ingest_billing_event(self, event: BillingEvent) -> tuple[FinancialRecord, ...]:
        existing = self._store.for_billing_event(str(event.event_id))
        if existing:
            return existing
        if event.amount_minor is None or event.currency is None:
            return ()
        records: list[FinancialRecord] = []
        if event.kind is BillingEventKind.INVOICE_PAID:
            records.extend(
                (
                    self._record_from_billing(
                        event=event,
                        record_id=f"financial:invoice:{event.event_id}",
                        kind=FinancialRecordKind.INVOICE,
                        state=FinancialRecordState.PAID,
                        document_number=event.external_object_id,
                    ),
                    self._record_from_billing(
                        event=event,
                        record_id=f"financial:payment:{event.event_id}",
                        kind=FinancialRecordKind.PAYMENT,
                        state=FinancialRecordState.PAID,
                    ),
                )
            )
        elif event.kind is BillingEventKind.PAYMENT_FAILED:
            records.append(
                self._record_from_billing(
                    event=event,
                    record_id=f"financial:payment:{event.event_id}",
                    kind=FinancialRecordKind.PAYMENT,
                    state=FinancialRecordState.FAILED,
                )
            )
        elif event.kind is BillingEventKind.REFUND_RECORDED:
            records.append(
                self._record_from_billing(
                    event=event,
                    record_id=f"financial:refund:{event.event_id}",
                    kind=FinancialRecordKind.REFUND,
                    state=FinancialRecordState.REFUNDED,
                )
            )
        for record in records:
            self._store.append(record)
        return tuple(records)

    def record_external_document(
        self,
        *,
        grant: AdminAuthorizationGrant,
        record: FinancialRecord,
    ) -> bool:
        _require_write(grant)
        if record.source.adapter_ref is None:
            raise ValueError("external financial document requires adapter_ref")
        return self._store.append(record)

    def record_credit_note(
        self,
        *,
        grant: AdminAuthorizationGrant,
        record_id: str,
        account_id: str,
        corrects_record_id: str,
        occurred_at: datetime,
        recorded_at: datetime,
        currency: str,
        gross_minor: int,
        source: FinancialSource,
        document_number: str | None = None,
        tax_basis_state: TaxBasisState = TaxBasisState.UNKNOWN,
        net_minor: int | None = None,
        tax_minor: int | None = None,
    ) -> FinancialRecord:
        _require_write(grant)
        corrected = self._store.get(corrects_record_id)
        if corrected is None:
            raise LookupError("credit note target does not exist")
        if corrected.account_id != account_id:
            raise ValueError("credit note account must match corrected record")
        if corrected.currency != currency.upper():
            raise ValueError("credit note currency must match corrected record")
        record = FinancialRecord(
            record_id=record_id,
            account_id=account_id,
            kind=FinancialRecordKind.CREDIT_NOTE,
            state=FinancialRecordState.ISSUED,
            occurred_at=occurred_at,
            recorded_at=recorded_at,
            currency=currency,
            gross_minor=gross_minor,
            source=source,
            document_number=document_number,
            tax_basis_state=tax_basis_state,
            net_minor=net_minor,
            tax_minor=tax_minor,
            corrects_record_id=corrects_record_id,
        )
        self._store.append(record)
        return record


def project_financial_documents(
    *,
    store: FinancialDocumentStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> FinancialDocumentProjection:
    _require_read(grant)
    records = store.all()
    return FinancialDocumentProjection(
        generated_at=generated_at,
        privacy_class="PRIVATE_FINANCIAL_OPERATIONS_NOT_FISCAL_AUTHORITY",
        records=records,
        exports=tuple(export_row(record) for record in records),
        coverage_notes=(
            "Stripe payment facts and invoice/document records are distinct records.",
            "Corrections are new credit-note records; prior history is immutable.",
            "Tax basis remains UNKNOWN unless supplied by an authorized source adapter.",
            "Admin display/export is not the legal or fiscal system of record.",
        ),
    )
