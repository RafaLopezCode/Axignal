"""AO-20 private financial document domain.

These records explain AXIGNAL commercial money/document flows. They are not a
legal/fiscal system of record unless a later ADR explicitly grants that authority.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,239}$")
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


class FinancialRecordKind(StrEnum):
    INVOICE = "INVOICE"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    CREDIT_NOTE = "CREDIT_NOTE"


class FinancialRecordState(StrEnum):
    OBSERVED = "OBSERVED"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    ISSUED = "ISSUED"


class TaxBasisState(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _text(value: str, name: str, maximum: int = 500) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} is required and must be at most {maximum} characters")


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded opaque identifier")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class FinancialSource:
    system: str
    object_ref: str
    event_ref: str | None = None
    adapter_ref: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.system, "source system")
        _identifier(self.object_ref, "source object ref")
        if self.event_ref is not None:
            _identifier(self.event_ref, "source event ref")
        if self.adapter_ref is not None:
            _identifier(self.adapter_ref, "adapter ref")


@dataclass(frozen=True, slots=True)
class FinancialRecord:
    record_id: str
    account_id: str
    kind: FinancialRecordKind
    state: FinancialRecordState
    occurred_at: datetime
    recorded_at: datetime
    currency: str
    gross_minor: int
    source: FinancialSource
    billing_event_id: str | None = None
    document_number: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    tax_basis_state: TaxBasisState = TaxBasisState.UNKNOWN
    net_minor: int | None = None
    tax_minor: int | None = None
    corrects_record_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.record_id, "record_id")
        _identifier(self.account_id, "account_id")
        _aware(self.occurred_at, "occurred_at")
        _aware(self.recorded_at, "recorded_at")
        if self.recorded_at < self.occurred_at:
            raise ValueError("financial record cannot be recorded before occurrence")
        if not _CURRENCY.fullmatch(self.currency):
            raise ValueError("currency must be a three-letter code")
        object.__setattr__(self, "currency", self.currency.upper())
        if self.gross_minor < 0:
            raise ValueError("gross_minor is magnitude and cannot be negative")
        if self.billing_event_id is not None:
            _identifier(self.billing_event_id, "billing_event_id")
        if self.document_number is not None:
            _text(self.document_number, "document_number", 160)
        if self.period_start is not None:
            _aware(self.period_start, "period_start")
        if self.period_end is not None:
            _aware(self.period_end, "period_end")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("financial period end cannot precede start")
        if self.net_minor is not None and self.net_minor < 0:
            raise ValueError("net_minor cannot be negative")
        if self.tax_minor is not None and self.tax_minor < 0:
            raise ValueError("tax_minor cannot be negative")
        if self.tax_basis_state is TaxBasisState.KNOWN:
            if self.net_minor is None or self.tax_minor is None:
                raise ValueError("known tax basis requires net and tax amounts")
            if self.net_minor + self.tax_minor != self.gross_minor:
                raise ValueError("known tax basis must reconcile net + tax = gross")
        elif self.net_minor is not None or self.tax_minor is not None:
            raise ValueError("unknown/non-applicable tax basis cannot carry tax amounts")
        if self.kind is FinancialRecordKind.CREDIT_NOTE:
            if self.corrects_record_id is None:
                raise ValueError("credit note must reference the record it corrects")
            _identifier(self.corrects_record_id, "corrects_record_id")
        elif self.corrects_record_id is not None:
            raise ValueError("only credit notes may correct a prior financial record")


@dataclass(frozen=True, slots=True)
class FinancialExportRow:
    record_id: str
    account_id: str
    kind: str
    state: str
    occurred_at: str
    currency: str
    signed_gross_minor: int
    source_system: str
    source_object_ref: str
    source_event_ref: str | None
    adapter_ref: str | None
    billing_event_id: str | None
    document_number: str | None
    tax_basis_state: str
    net_minor: int | None
    tax_minor: int | None
    corrects_record_id: str | None


def signed_gross_minor(record: FinancialRecord) -> int:
    if record.kind in {FinancialRecordKind.REFUND, FinancialRecordKind.CREDIT_NOTE}:
        return -record.gross_minor
    return record.gross_minor


def export_row(record: FinancialRecord) -> FinancialExportRow:
    return FinancialExportRow(
        record_id=record.record_id,
        account_id=record.account_id,
        kind=record.kind.value,
        state=record.state.value,
        occurred_at=record.occurred_at.isoformat(),
        currency=record.currency,
        signed_gross_minor=signed_gross_minor(record),
        source_system=record.source.system,
        source_object_ref=record.source.object_ref,
        source_event_ref=record.source.event_ref,
        adapter_ref=record.source.adapter_ref,
        billing_event_id=record.billing_event_id,
        document_number=record.document_number,
        tax_basis_state=record.tax_basis_state.value,
        net_minor=record.net_minor,
        tax_minor=record.tax_minor,
        corrects_record_id=record.corrects_record_id,
    )
