"""AO-21 provider-neutral accounting reconciliation domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,239}$")
_ACCOUNT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,79}$")
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


class AccountingCategory(StrEnum):
    REVENUE = "REVENUE"
    REFUND = "REFUND"
    PROCESSOR_FEE = "PROCESSOR_FEE"
    SETTLEMENT = "SETTLEMENT"
    INFRASTRUCTURE_COST = "INFRASTRUCTURE_COST"
    BUSINESS_EXPENSE = "BUSINESS_EXPENSE"
    TAX = "TAX"


class ReconciliationIssueKind(StrEnum):
    UNMATCHED_FINANCIAL = "UNMATCHED_FINANCIAL"
    UNMATCHED_ACCOUNTING = "UNMATCHED_ACCOUNTING"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    SETTLEMENT_MISMATCH = "SETTLEMENT_MISMATCH"
    MISSING_ACCOUNT_MAPPING = "MISSING_ACCOUNT_MAPPING"


class ReconciliationIssueState(StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class PeriodCloseState(StrEnum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded opaque identifier")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _currency(value: str) -> str:
    if not _CURRENCY.fullmatch(value):
        raise ValueError("currency must be a three-letter code")
    return value.upper()


@dataclass(frozen=True, slots=True)
class AccountMapping:
    mapping_id: str
    integration_id: str
    category: AccountingCategory
    account_code: str
    effective_at: datetime
    version: int = 1

    def __post_init__(self) -> None:
        _identifier(self.mapping_id, "mapping_id")
        _identifier(self.integration_id, "integration_id")
        if not _ACCOUNT.fullmatch(self.account_code):
            raise ValueError("account_code must be a bounded external account identifier")
        _aware(self.effective_at, "effective_at")
        if self.version < 1:
            raise ValueError("mapping version must be positive")


@dataclass(frozen=True, slots=True)
class AccountingEntry:
    entry_id: str
    integration_id: str
    account_code: str
    category: AccountingCategory
    occurred_at: datetime
    recorded_at: datetime
    currency: str
    signed_amount_minor: int
    source_ref: str
    financial_record_id: str | None = None
    settlement_id: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.entry_id, "entry_id"),
            (self.integration_id, "integration_id"),
            (self.source_ref, "source_ref"),
        ):
            _identifier(value, name)
        if not _ACCOUNT.fullmatch(self.account_code):
            raise ValueError("account_code must be a bounded external account identifier")
        _aware(self.occurred_at, "occurred_at")
        _aware(self.recorded_at, "recorded_at")
        if self.recorded_at < self.occurred_at:
            raise ValueError("accounting entry cannot be recorded before occurrence")
        object.__setattr__(self, "currency", _currency(self.currency))
        if self.signed_amount_minor == 0:
            raise ValueError("accounting entry amount cannot be zero")
        if self.financial_record_id is not None:
            _identifier(self.financial_record_id, "financial_record_id")
        if self.settlement_id is not None:
            _identifier(self.settlement_id, "settlement_id")


@dataclass(frozen=True, slots=True)
class ProcessorSettlement:
    settlement_id: str
    integration_id: str
    processor: str
    occurred_at: datetime
    recorded_at: datetime
    currency: str
    gross_minor: int
    fee_minor: int
    net_minor: int
    source_ref: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.settlement_id, "settlement_id"),
            (self.integration_id, "integration_id"),
            (self.processor, "processor"),
            (self.source_ref, "source_ref"),
        ):
            _identifier(value, name)
        _aware(self.occurred_at, "occurred_at")
        _aware(self.recorded_at, "recorded_at")
        if self.recorded_at < self.occurred_at:
            raise ValueError("settlement cannot be recorded before occurrence")
        object.__setattr__(self, "currency", _currency(self.currency))
        if min(self.gross_minor, self.fee_minor, self.net_minor) < 0:
            raise ValueError("settlement amounts must be non-negative magnitudes")
        if self.gross_minor - self.fee_minor != self.net_minor:
            raise ValueError("settlement must reconcile gross - fee = net")


@dataclass(frozen=True, slots=True)
class ReconciliationIssue:
    issue_id: str
    kind: ReconciliationIssueKind
    state: ReconciliationIssueState
    opened_at: datetime
    currency: str | None
    expected_minor: int | None
    observed_minor: int | None
    financial_record_id: str | None = None
    accounting_entry_id: str | None = None
    settlement_id: str | None = None
    resolved_at: datetime | None = None
    resolution_ref: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.issue_id, "issue_id")
        _aware(self.opened_at, "opened_at")
        if self.currency is not None:
            object.__setattr__(self, "currency", _currency(self.currency))
        for value, name in (
            (self.financial_record_id, "financial_record_id"),
            (self.accounting_entry_id, "accounting_entry_id"),
            (self.settlement_id, "settlement_id"),
            (self.resolution_ref, "resolution_ref"),
        ):
            if value is not None:
                _identifier(value, name)
        if self.resolved_at is not None:
            _aware(self.resolved_at, "resolved_at")
        if self.state is ReconciliationIssueState.RESOLVED:
            if self.resolved_at is None or self.resolution_ref is None:
                raise ValueError("resolved discrepancy requires time and resolution reference")
        elif self.resolved_at is not None or self.resolution_ref is not None:
            raise ValueError("open discrepancy cannot carry resolution metadata")


@dataclass(frozen=True, slots=True)
class PeriodClose:
    period_id: str
    period_start: datetime
    period_end: datetime
    state: PeriodCloseState
    evaluated_at: datetime
    closed_at: datetime | None = None
    source_ref: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.period_id, "period_id")
        _aware(self.period_start, "period_start")
        _aware(self.period_end, "period_end")
        _aware(self.evaluated_at, "evaluated_at")
        if self.period_end <= self.period_start:
            raise ValueError("period end must follow period start")
        if self.closed_at is not None:
            _aware(self.closed_at, "closed_at")
        if self.source_ref is not None:
            _identifier(self.source_ref, "source_ref")
        if self.state is PeriodCloseState.CLOSED:
            if self.closed_at is None or self.source_ref is None:
                raise ValueError("closed period requires close time and source reference")
        elif self.closed_at is not None:
            raise ValueError("non-closed period cannot carry closed_at")
