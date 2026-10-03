"""AO-21 accounting adapter and reconciliation application boundary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_accounting import (
    AccountingCategory,
    AccountingEntry,
    AccountMapping,
    PeriodClose,
    PeriodCloseState,
    ProcessorSettlement,
    ReconciliationIssue,
    ReconciliationIssueKind,
    ReconciliationIssueState,
)
from domain.admin_financial_documents import (
    FinancialRecord,
    FinancialRecordKind,
    signed_gross_minor,
)
from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
)
from domain.admin_integrations import CredentialState, IntegrationDefinition


class FinancialSourceStore(Protocol):
    def all(self) -> tuple[FinancialRecord, ...]: ...


class AccountingReconciliationStore(Protocol):
    def append_mapping(self, mapping: AccountMapping) -> bool: ...
    def mappings(self) -> tuple[AccountMapping, ...]: ...
    def append_entry(self, entry: AccountingEntry) -> bool: ...
    def entries(self) -> tuple[AccountingEntry, ...]: ...
    def append_settlement(self, settlement: ProcessorSettlement) -> bool: ...
    def settlements(self) -> tuple[ProcessorSettlement, ...]: ...
    def put_issue(self, issue: ReconciliationIssue) -> bool: ...
    def issues(self) -> tuple[ReconciliationIssue, ...]: ...
    def put_period(self, period: PeriodClose) -> bool: ...
    def periods(self) -> tuple[PeriodClose, ...]: ...


class AccountingIntegrationStore(Protocol):
    def all_definitions(self) -> tuple[IntegrationDefinition, ...]: ...


class AccountingAuditStore(Protocol):
    def append(self, record: AdminGovernanceAuditRecord) -> bool: ...


@dataclass(frozen=True, slots=True)
class ReconciliationTotals:
    currency: str
    billed_minor: int
    paid_minor: int
    refunded_minor: int
    credit_note_minor: int
    settled_gross_minor: int
    processor_fee_minor: int
    settled_net_minor: int
    accounted_minor: int
    infrastructure_cost_minor: int
    business_expense_minor: int


@dataclass(frozen=True, slots=True)
class AccountingReconciliationProjection:
    generated_at: datetime
    privacy_class: str
    adapter_strategy: str
    configured_integrations: tuple[str, ...]
    mappings: tuple[AccountMapping, ...]
    entries: tuple[AccountingEntry, ...]
    settlements: tuple[ProcessorSettlement, ...]
    issues: tuple[ReconciliationIssue, ...]
    periods: tuple[PeriodClose, ...]
    totals: tuple[ReconciliationTotals, ...]
    coverage_notes: tuple[str, ...]


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FINANCE_READ not in grant.scopes:
        raise PermissionError("accounting reconciliation requires admin:finance:read")


def _require_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FINANCE_WRITE not in grant.scopes:
        raise PermissionError("accounting mutation requires admin:finance:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("accounting mutation requires STEP_UP assurance")


def _category_for_financial(kind: FinancialRecordKind) -> AccountingCategory | None:
    if kind is FinancialRecordKind.INVOICE:
        return AccountingCategory.REVENUE
    if kind in {FinancialRecordKind.REFUND, FinancialRecordKind.CREDIT_NOTE}:
        return AccountingCategory.REFUND
    return None


class AccountingReconciliationService:
    def __init__(
        self,
        store: AccountingReconciliationStore,
        financial_store: FinancialSourceStore,
        integration_store: AccountingIntegrationStore,
        audit_store: AccountingAuditStore,
    ) -> None:
        self._store = store
        self._financial_store = financial_store
        self._integration_store = integration_store
        self._audit_store = audit_store

    def _require_registered_adapter(self, integration_id: str) -> IntegrationDefinition:
        definition = next(
            (
                item
                for item in self._integration_store.all_definitions()
                if item.integration_id == integration_id
            ),
            None,
        )
        if definition is None:
            raise ValueError("accounting adapter is not registered in AO-18")
        if not definition.enabled:
            raise ValueError("accounting adapter is disabled in AO-18")
        if definition.credential.state not in {
            CredentialState.CONFIGURED,
            CredentialState.ROTATION_DUE,
        }:
            raise ValueError("accounting adapter credential is not configured in AO-18")
        return definition

    def _audit(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        occurred_at: datetime,
        action: str,
        result_code: str,
        before_ref: str | None = None,
        after_ref: str | None = None,
    ) -> None:
        self._audit_store.append(
            AdminGovernanceAuditRecord(
                audit_id=f"finance-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=occurred_at,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=AdminGovernanceCommandTarget.FINANCE,
                action=action,
                reason=reason,
                required_scope=AdminScope.FINANCE_WRITE.value,
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code=result_code,
                before_ref=before_ref,
                after_ref=after_ref,
            )
        )

    def register_mapping(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        mapping: AccountMapping,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        self._require_registered_adapter(mapping.integration_id)
        inserted = self._store.append_mapping(mapping)
        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.mapping.registered",
            result_code="ACCOUNTING_MAPPING_RECORDED",
            after_ref=f"{mapping.mapping_id}:v{mapping.version}",
        )
        return inserted

    def import_entry(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        entry: AccountingEntry,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        self._require_registered_adapter(entry.integration_id)
        inserted = self._store.append_entry(entry)
        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.entry.imported",
            result_code="ACCOUNTING_ENTRY_IMPORTED",
            after_ref=entry.entry_id,
        )
        return inserted

    def import_settlement(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        settlement: ProcessorSettlement,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        self._require_registered_adapter(settlement.integration_id)
        inserted = self._store.append_settlement(settlement)
        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.settlement.imported",
            result_code="ACCOUNTING_SETTLEMENT_IMPORTED",
            after_ref=settlement.settlement_id,
        )
        return inserted

    def reconcile(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        now: datetime,
    ) -> tuple[ReconciliationIssue, ...]:
        _require_write(grant)
        records = self._financial_store.all()
        entries = self._store.entries()
        mappings = self._store.mappings()
        settlements = self._store.settlements()
        generated: list[ReconciliationIssue] = []

        relevant = tuple(
            record for record in records if _category_for_financial(record.kind) is not None
        )
        entries_by_financial = {
            entry.financial_record_id: entry
            for entry in entries
            if entry.financial_record_id is not None
        }
        financial_ids = {record.record_id for record in relevant}
        mapping_keys = {
            (item.integration_id, item.category, item.account_code) for item in mappings
        }

        for record in relevant:
            entry = entries_by_financial.get(record.record_id)
            if entry is None:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:financial:{record.record_id}",
                        kind=ReconciliationIssueKind.UNMATCHED_FINANCIAL,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=record.currency,
                        expected_minor=signed_gross_minor(record),
                        observed_minor=None,
                        financial_record_id=record.record_id,
                    )
                )
                continue
            if (entry.integration_id, entry.category, entry.account_code) not in mapping_keys:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:mapping:{entry.entry_id}",
                        kind=ReconciliationIssueKind.MISSING_ACCOUNT_MAPPING,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=entry.currency,
                        expected_minor=signed_gross_minor(record),
                        observed_minor=entry.signed_amount_minor,
                        financial_record_id=record.record_id,
                        accounting_entry_id=entry.entry_id,
                    )
                )
                continue
            expected = signed_gross_minor(record)
            if entry.currency != record.currency:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:currency:{record.record_id}:{entry.entry_id}",
                        kind=ReconciliationIssueKind.CURRENCY_MISMATCH,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=record.currency,
                        expected_minor=expected,
                        observed_minor=entry.signed_amount_minor,
                        financial_record_id=record.record_id,
                        accounting_entry_id=entry.entry_id,
                    )
                )
            elif entry.signed_amount_minor != expected:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:amount:{record.record_id}:{entry.entry_id}",
                        kind=ReconciliationIssueKind.AMOUNT_MISMATCH,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=record.currency,
                        expected_minor=expected,
                        observed_minor=entry.signed_amount_minor,
                        financial_record_id=record.record_id,
                        accounting_entry_id=entry.entry_id,
                    )
                )

        for entry in entries:
            mapping_key = (entry.integration_id, entry.category, entry.account_code)
            if mapping_key not in mapping_keys:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:mapping:{entry.entry_id}",
                        kind=ReconciliationIssueKind.MISSING_ACCOUNT_MAPPING,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=entry.currency,
                        expected_minor=None,
                        observed_minor=entry.signed_amount_minor,
                        accounting_entry_id=entry.entry_id,
                        settlement_id=entry.settlement_id,
                    )
                )
            if (
                entry.financial_record_id is not None
                and entry.financial_record_id not in financial_ids
            ):
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:accounting:{entry.entry_id}",
                        kind=ReconciliationIssueKind.UNMATCHED_ACCOUNTING,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=entry.currency,
                        expected_minor=None,
                        observed_minor=entry.signed_amount_minor,
                        accounting_entry_id=entry.entry_id,
                    )
                )

        entries_by_settlement: dict[str, list[AccountingEntry]] = {}
        for entry in entries:
            if entry.settlement_id is not None:
                entries_by_settlement.setdefault(entry.settlement_id, []).append(entry)
        for settlement in settlements:
            settlement_entries = entries_by_settlement.get(settlement.settlement_id, [])
            observed_net = sum(
                item.signed_amount_minor
                for item in settlement_entries
                if item.category is AccountingCategory.SETTLEMENT
            )
            observed_fee = -sum(
                item.signed_amount_minor
                for item in settlement_entries
                if item.category is AccountingCategory.PROCESSOR_FEE
            )
            if observed_net != settlement.net_minor or observed_fee != settlement.fee_minor:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:settlement:{settlement.settlement_id}",
                        kind=ReconciliationIssueKind.SETTLEMENT_MISMATCH,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=settlement.currency,
                        expected_minor=settlement.net_minor,
                        observed_minor=observed_net,
                        settlement_id=settlement.settlement_id,
                    )
                )

        currencies = sorted(
            {record.currency for record in records} | {item.currency for item in settlements}
        )
        for currency in currencies:
            paid_total = sum(
                record.gross_minor
                for record in records
                if record.currency == currency
                and record.kind is FinancialRecordKind.PAYMENT
                and record.state.value == "PAID"
            )
            refund_total = sum(
                record.gross_minor
                for record in records
                if record.currency == currency and record.kind is FinancialRecordKind.REFUND
            )
            settled_gross = sum(
                item.gross_minor for item in settlements if item.currency == currency
            )
            expected_settled_gross = max(0, paid_total - refund_total)
            if settled_gross != expected_settled_gross:
                generated.append(
                    ReconciliationIssue(
                        issue_id=f"recon:settlement-total:{currency}",
                        kind=ReconciliationIssueKind.SETTLEMENT_MISMATCH,
                        state=ReconciliationIssueState.OPEN,
                        opened_at=now,
                        currency=currency,
                        expected_minor=expected_settled_gross,
                        observed_minor=settled_gross,
                    )
                )

        existing = {issue.issue_id: issue for issue in self._store.issues()}
        for issue in generated:
            previous = existing.get(issue.issue_id)
            if previous is None:
                self._store.put_issue(issue)
            elif previous.state is ReconciliationIssueState.RESOLVED:
                reopen_id = issue.issue_id + f":reopened:{int(now.timestamp())}"
                self._store.put_issue(replace(issue, issue_id=reopen_id))

        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.reconciliation.executed",
            result_code="ACCOUNTING_RECONCILIATION_COMPLETED",
            after_ref=f"reconciliation:{int(now.timestamp())}",
        )
        return self._store.issues()

    def resolve_issue(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        issue_id: str,
        now: datetime,
        resolution_ref: str,
    ) -> ReconciliationIssue:
        _require_write(grant)
        issue = next((item for item in self._store.issues() if item.issue_id == issue_id), None)
        if issue is None:
            raise LookupError(issue_id)
        if issue.state is ReconciliationIssueState.RESOLVED:
            return issue
        resolved = replace(
            issue,
            state=ReconciliationIssueState.RESOLVED,
            resolved_at=now,
            resolution_ref=resolution_ref,
        )
        self._store.put_issue(resolved)
        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.discrepancy.resolved",
            result_code="ACCOUNTING_DISCREPANCY_RESOLVED",
            before_ref=issue.issue_id,
            after_ref=resolution_ref,
        )
        return resolved

    def evaluate_period(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        period_id: str,
        period_start: datetime,
        period_end: datetime,
        now: datetime,
        close: bool,
        source_ref: str | None = None,
    ) -> PeriodClose:
        _require_write(grant)
        open_issues = tuple(
            issue for issue in self._store.issues() if issue.state is ReconciliationIssueState.OPEN
        )
        if close and open_issues:
            period = PeriodClose(
                period_id=period_id,
                period_start=period_start,
                period_end=period_end,
                state=PeriodCloseState.BLOCKED,
                evaluated_at=now,
            )
        elif close:
            if source_ref is None:
                raise ValueError("period close requires accounting source reference")
            period = PeriodClose(
                period_id=period_id,
                period_start=period_start,
                period_end=period_end,
                state=PeriodCloseState.CLOSED,
                evaluated_at=now,
                closed_at=now,
                source_ref=source_ref,
            )
        else:
            period = PeriodClose(
                period_id=period_id,
                period_start=period_start,
                period_end=period_end,
                state=PeriodCloseState.OPEN,
                evaluated_at=now,
            )
        self._store.put_period(period)
        self._audit(
            grant=grant,
            operation_id=operation_id,
            reason=reason,
            occurred_at=now,
            action="accounting.period.evaluated",
            result_code=f"ACCOUNTING_PERIOD_{period.state.value}",
            after_ref=f"{period.period_id}:{period.state.value}",
        )
        return period


def project_accounting_reconciliation(
    *,
    store: AccountingReconciliationStore,
    financial_store: FinancialSourceStore,
    integration_store: AccountingIntegrationStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> AccountingReconciliationProjection:
    _require_read(grant)
    records = financial_store.all()
    entries = store.entries()
    settlements = store.settlements()
    currencies = sorted(
        {record.currency for record in records}
        | {entry.currency for entry in entries}
        | {item.currency for item in settlements}
    )
    totals: list[ReconciliationTotals] = []
    for currency in currencies:
        billed = sum(
            record.gross_minor
            for record in records
            if record.currency == currency and record.kind is FinancialRecordKind.INVOICE
        )
        paid = sum(
            record.gross_minor
            for record in records
            if record.currency == currency
            and record.kind is FinancialRecordKind.PAYMENT
            and record.state.value == "PAID"
        )
        refunded = sum(
            record.gross_minor
            for record in records
            if record.currency == currency and record.kind is FinancialRecordKind.REFUND
        )
        credit_notes = sum(
            record.gross_minor
            for record in records
            if record.currency == currency and record.kind is FinancialRecordKind.CREDIT_NOTE
        )
        settled_gross = sum(item.gross_minor for item in settlements if item.currency == currency)
        fee = sum(item.fee_minor for item in settlements if item.currency == currency)
        settled_net = sum(item.net_minor for item in settlements if item.currency == currency)
        accounted = sum(
            entry.signed_amount_minor
            for entry in entries
            if entry.currency == currency
            and entry.category in {AccountingCategory.REVENUE, AccountingCategory.REFUND}
        )
        infrastructure_cost = -sum(
            entry.signed_amount_minor
            for entry in entries
            if entry.currency == currency
            and entry.category is AccountingCategory.INFRASTRUCTURE_COST
        )
        business_expense = -sum(
            entry.signed_amount_minor
            for entry in entries
            if entry.currency == currency and entry.category is AccountingCategory.BUSINESS_EXPENSE
        )
        totals.append(
            ReconciliationTotals(
                currency=currency,
                billed_minor=billed,
                paid_minor=paid,
                refunded_minor=refunded,
                credit_note_minor=credit_notes,
                settled_gross_minor=settled_gross,
                processor_fee_minor=fee,
                settled_net_minor=settled_net,
                accounted_minor=accounted,
                infrastructure_cost_minor=infrastructure_cost,
                business_expense_minor=business_expense,
            )
        )

    configured = tuple(
        sorted(
            item.integration_id
            for item in integration_store.all_definitions()
            if item.enabled and "account" in item.purpose.lower()
        )
    )
    return AccountingReconciliationProjection(
        generated_at=generated_at,
        privacy_class="PRIVATE_ACCOUNTING_RECONCILIATION_NOT_AXIGLAND",
        adapter_strategy="EXTERNAL_PROVIDER_ADAPTER_VIA_AO18",
        configured_integrations=configured,
        mappings=store.mappings(),
        entries=entries,
        settlements=settlements,
        issues=store.issues(),
        periods=store.periods(),
        totals=tuple(totals),
        coverage_notes=(
            "AXIGNAL-owned accounting ledger is NOT authorized.",
            "Accounting entries must come from an external provider adapter governed by AO-18.",
            "Unknown or unmatched transactions remain unresolved; reconciliation never auto-balances.",
            "Period close is blocked while reconciliation discrepancies remain open.",
            "Accounting mutations are audited and accounting state never becomes AXIGLAND truth.",
        ),
    )
