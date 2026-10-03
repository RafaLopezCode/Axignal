"""AO-23 Tax / VAT / AEAT operations application service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_governance import (
    AdminGovernanceAuditRecord,
    AdminGovernanceCommandOutcome,
    AdminGovernanceCommandTarget,
)
from domain.admin_tax_operations import (
    TaxAdvisorExport,
    TaxApplicabilityState,
    TaxEvidence,
    TaxEvidenceKind,
    TaxObligation,
    TaxObligationState,
    TaxOperationsProjection,
    TaxOperationView,
    TaxPeriodicity,
    TaxRuleDefinition,
)


class TaxOperationsStore(Protocol):
    def append_rule(self, rule: TaxRuleDefinition) -> bool: ...
    def rules(self) -> tuple[TaxRuleDefinition, ...]: ...
    def append_obligation(self, obligation: TaxObligation) -> bool: ...
    def obligations(self) -> tuple[TaxObligation, ...]: ...
    def append_evidence(self, evidence: TaxEvidence) -> bool: ...
    def evidence_for(self, obligation_id: str) -> tuple[TaxEvidence, ...]: ...


class AuditStore(Protocol):
    def append(self, record: AdminGovernanceAuditRecord) -> bool: ...


_REQUIRED_FOR_PREPARED = (
    TaxEvidenceKind.APPLICABILITY,
    TaxEvidenceKind.SOURCE_DOCUMENT_SET,
    TaxEvidenceKind.RECONCILIATION,
    TaxEvidenceKind.HUMAN_APPROVAL,
)
_REQUIRED_FOR_COMPLETE = (
    *_REQUIRED_FOR_PREPARED,
    TaxEvidenceKind.FILING_RECEIPT,
    TaxEvidenceKind.AEAT_ACCEPTANCE,
)


def canonical_es_tax_rules() -> tuple[TaxRuleDefinition, ...]:
    effective = datetime(2026, 1, 1, tzinfo=UTC)
    return (
        TaxRuleDefinition(
            rule_id="es:iva:303:quarterly:2026-10-03",
            jurisdiction="ES",
            model_code="303",
            periodicity=TaxPeriodicity.QUARTERLY,
            effective_at=effective,
            deadline_policy=(
                "Q1-Q3: days 1-20 of April/July/October; Q4: days 1-30 January. "
                "Official calendar controls non-working-day shifts."
            ),
            applicability_policy=(
                "Periodic VAT self-assessment when the taxpayer is legally required to file "
                "quarterly; applicability must be evidenced, never inferred from company type alone."
            ),
            source_refs=("aeat:iva2026:303:deadlines", "aeat:iva2026:303:models"),
        ),
        TaxRuleDefinition(
            rule_id="es:iva:303:monthly:2026-10-03",
            jurisdiction="ES",
            model_code="303",
            periodicity=TaxPeriodicity.MONTHLY,
            effective_at=effective,
            deadline_policy=(
                "Days 1-30 of following month; January period through last day of February. "
                "Official calendar controls non-working-day shifts."
            ),
            applicability_policy=(
                "Monthly VAT period only where legally applicable; applicability requires "
                "official/accountant evidence."
            ),
            source_refs=("aeat:iva2026:303:deadlines", "aeat:iva2026:303:models"),
        ),
        TaxRuleDefinition(
            rule_id="es:iva:390:annual:2026-10-03",
            jurisdiction="ES",
            model_code="390",
            periodicity=TaxPeriodicity.ANNUAL,
            effective_at=effective,
            deadline_policy=(
                "When required, annual VAT summary is filed in the January window associated "
                "with the final VAT period; official calendar controls exact deadline."
            ),
            applicability_policy=(
                "Conditional annual VAT summary. Exemptions exist; obligation must remain "
                "UNKNOWN until applicability is evidenced."
            ),
            source_refs=("aeat:iva2026:390:applicability", "aeat:iva2026:303:deadlines"),
        ),
        TaxRuleDefinition(
            rule_id="es:iva:349:monthly:2026-10-03",
            jurisdiction="ES",
            model_code="349",
            periodicity=TaxPeriodicity.MONTHLY,
            effective_at=effective,
            deadline_policy=(
                "Generally first 20 calendar days of following month, with official exceptions "
                "for July and December; official calendar controls exact deadline."
            ),
            applicability_policy=(
                "Recapitulative intra-Community statement only where relevant operations and "
                "periodicity rules apply."
            ),
            source_refs=("aeat:349:deadlines:2026",),
        ),
        TaxRuleDefinition(
            rule_id="es:iva:349:quarterly:2026-10-03",
            jurisdiction="ES",
            model_code="349",
            periodicity=TaxPeriodicity.QUARTERLY,
            effective_at=effective,
            deadline_policy=(
                "Generally first 20 calendar days after quarter; Q4 first 30 days of January. "
                "Official calendar controls exact deadline."
            ),
            applicability_policy=(
                "Quarterly recapitulative intra-Community statement only where legal conditions "
                "for quarterly periodicity are evidenced."
            ),
            source_refs=("aeat:349:deadlines:2026",),
        ),
    )


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FISCAL_READ not in grant.scopes:
        raise PermissionError("tax operations require admin:fiscal:read")


def _require_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FISCAL_WRITE not in grant.scopes:
        raise PermissionError("tax operations mutation requires admin:fiscal:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("tax operations mutation requires STEP_UP assurance")


def _state_for(
    obligation: TaxObligation,
    evidence: tuple[TaxEvidence, ...],
    *,
    now: datetime,
) -> TaxOperationView:
    kinds = tuple(sorted({item.kind for item in evidence}, key=lambda item: item.value))
    kind_set = set(kinds)

    if obligation.applicability is TaxApplicabilityState.UNKNOWN:
        return TaxOperationView(
            obligation=obligation,
            state=TaxObligationState.UNKNOWN,
            overdue=False,
            evidence_kinds=kinds,
            missing_evidence=(TaxEvidenceKind.APPLICABILITY,),
            complete=False,
        )

    if obligation.applicability is TaxApplicabilityState.NOT_APPLICABLE:
        if TaxEvidenceKind.APPLICABILITY not in kind_set:
            return TaxOperationView(
                obligation=obligation,
                state=TaxObligationState.UNKNOWN,
                overdue=False,
                evidence_kinds=kinds,
                missing_evidence=(TaxEvidenceKind.APPLICABILITY,),
                complete=False,
            )
        return TaxOperationView(
            obligation=obligation,
            state=TaxObligationState.NOT_APPLICABLE,
            overdue=False,
            evidence_kinds=kinds,
            missing_evidence=(),
            complete=True,
        )

    missing_complete = tuple(item for item in _REQUIRED_FOR_COMPLETE if item not in kind_set)
    if TaxEvidenceKind.AEAT_REJECTION in kind_set:
        state = TaxObligationState.REJECTED
    elif not missing_complete:
        state = TaxObligationState.ACCEPTED
    elif TaxEvidenceKind.FILING_RECEIPT in kind_set:
        state = TaxObligationState.FILED
    elif all(item in kind_set for item in _REQUIRED_FOR_PREPARED):
        state = TaxObligationState.PREPARED
    else:
        state = TaxObligationState.DUE

    return TaxOperationView(
        obligation=obligation,
        state=state,
        overdue=now > obligation.due_at
        and state
        not in {
            TaxObligationState.ACCEPTED,
            TaxObligationState.NOT_APPLICABLE,
        },
        evidence_kinds=kinds,
        missing_evidence=missing_complete,
        complete=state is TaxObligationState.ACCEPTED,
    )


class TaxOperationsService:
    def __init__(self, store: TaxOperationsStore, audit_store: AuditStore) -> None:
        self._store = store
        self._audit = audit_store

    def install_rule(self, rule: TaxRuleDefinition) -> bool:
        return self._store.append_rule(rule)

    def create_obligation(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        obligation: TaxObligation,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        rule = next(
            (item for item in self._store.rules() if item.rule_id == obligation.rule_id), None
        )
        if rule is None:
            raise ValueError("tax obligation references unknown rule")
        if rule.model_code != obligation.model_code:
            raise ValueError("tax obligation model does not match rule")
        inserted = self._store.append_obligation(obligation)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"tax-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=AdminGovernanceCommandTarget.FISCAL,
                action="tax.obligation.created",
                reason=reason,
                required_scope=AdminScope.FISCAL_WRITE.value,
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code="TAX_OBLIGATION_RECORDED",
                after_ref=obligation.obligation_id,
            )
        )
        return inserted

    def record_evidence(
        self,
        *,
        grant: AdminAuthorizationGrant,
        operation_id: str,
        reason: str,
        evidence: TaxEvidence,
        now: datetime,
    ) -> bool:
        _require_write(grant)
        obligation = next(
            (
                item
                for item in self._store.obligations()
                if item.obligation_id == evidence.obligation_id
            ),
            None,
        )
        if obligation is None:
            raise ValueError("tax evidence references unknown obligation")
        inserted = self._store.append_evidence(evidence)
        self._audit.append(
            AdminGovernanceAuditRecord(
                audit_id=f"tax-audit:{operation_id}",
                command_id=operation_id,
                occurred_at=now,
                actor_principal_id=str(grant.principal_id),
                actor_session_id=str(grant.session_id),
                target=AdminGovernanceCommandTarget.FISCAL,
                action="tax.evidence.recorded",
                reason=reason,
                required_scope=AdminScope.FISCAL_WRITE.value,
                outcome=AdminGovernanceCommandOutcome.COMPLETED,
                result_code=f"TAX_EVIDENCE_{evidence.kind.value}",
                after_ref=evidence.evidence_id,
            )
        )
        return inserted


def project_tax_operations(
    *,
    store: TaxOperationsStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> TaxOperationsProjection:
    _require_read(grant)
    views = tuple(
        _state_for(
            obligation,
            store.evidence_for(obligation.obligation_id),
            now=generated_at,
        )
        for obligation in sorted(
            store.obligations(), key=lambda item: (item.due_at, item.obligation_id)
        )
    )
    return TaxOperationsProjection(
        generated_at=generated_at,
        privacy_class="PRIVATE_TAX_OPERATIONS_NOT_LEGAL_AUTHORITY",
        ruleset_version="es-tax-operations-2026-10-03",
        obligations=views,
        coverage_notes=(
            "Tax applicability is evidence-backed; company type or model name alone never creates an obligation.",
            "Prepared, filed and accepted are distinct states.",
            "Only AEAT acceptance evidence can make an applicable filing complete.",
            "Deadlines are instantiated from official calendar/advisor evidence; generic rules do not guess holiday shifts.",
            "AXENT/LLMs may explain records but cannot determine legal tax obligations or filing completion.",
        ),
    )


def advisor_exports(
    *,
    store: TaxOperationsStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> tuple[TaxAdvisorExport, ...]:
    projection = project_tax_operations(store=store, grant=grant, generated_at=generated_at)
    rows: list[TaxAdvisorExport] = []
    for view in projection.obligations:
        evidence = store.evidence_for(view.obligation.obligation_id)
        rows.append(
            TaxAdvisorExport(
                obligation_id=view.obligation.obligation_id,
                model_code=view.obligation.model_code,
                period_start=view.obligation.period_start.isoformat(),
                period_end=view.obligation.period_end.isoformat(),
                due_at=view.obligation.due_at.isoformat(),
                state=view.state.value,
                deadline_source_ref=view.obligation.deadline_source_ref,
                evidence_refs=tuple(item.source_ref for item in evidence),
                complete=view.complete,
            )
        )
    return tuple(rows)
