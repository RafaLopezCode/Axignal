"""AO-08 application service for AXIGNAL first-party commercial operations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from domain.admin_access import AdminAuthorizationGrant, AdminScope
from domain.admin_commercial import (
    CommercialAuditId,
    CommercialAuditRecord,
    CommercialCompany,
    CommercialCompanyId,
    CommercialContact,
    CommercialContactId,
    CommercialDeal,
    CommercialDealId,
    CommercialNote,
    CommercialNoteId,
    CommercialOpportunity,
    CommercialOpportunityId,
    CommercialOrigin,
    CommercialProspect,
    CommercialProspectId,
    CommercialTask,
    CommercialTaskId,
    ConsentBasis,
    DealStage,
    OpportunityStage,
    ProspectStage,
    TaskState,
)


class CommercialStore(Protocol):
    def put_prospect(self, record: CommercialProspect) -> None: ...
    def put_company(self, record: CommercialCompany) -> None: ...
    def put_contact(self, record: CommercialContact) -> None: ...
    def put_opportunity(self, record: CommercialOpportunity) -> None: ...
    def put_deal(self, record: CommercialDeal) -> None: ...
    def put_note(self, record: CommercialNote) -> None: ...
    def put_task(self, record: CommercialTask) -> None: ...
    def append_audit(self, record: CommercialAuditRecord) -> bool: ...
    def prospects(self) -> tuple[CommercialProspect, ...]: ...
    def companies(self) -> tuple[CommercialCompany, ...]: ...
    def contacts(self) -> tuple[CommercialContact, ...]: ...
    def opportunities(self) -> tuple[CommercialOpportunity, ...]: ...
    def deals(self) -> tuple[CommercialDeal, ...]: ...
    def notes(self) -> tuple[CommercialNote, ...]: ...
    def tasks(self) -> tuple[CommercialTask, ...]: ...
    def audits(self) -> tuple[CommercialAuditRecord, ...]: ...


@dataclass(frozen=True, slots=True)
class CommercialCompanyView:
    company_id: str
    display_name: str
    acquisition_source: str
    consent_basis: str
    origin: str
    observed_organization_id: str | None
    account_id: str | None
    opportunity_count: int
    open_task_count: int
    note_count: int
    contact_count: int


@dataclass(frozen=True, slots=True)
class AdminCommercialProjection:
    privacy_class: str
    generated_at: datetime
    prospect_count: int
    company_count: int
    contact_count: int
    opportunity_count: int
    deal_count: int
    note_count: int
    open_task_count: int
    companies: tuple[CommercialCompanyView, ...]
    origin_counts: tuple[tuple[str, int], ...]
    audit_count: int
    pii_visible: bool
    coverage_notes: tuple[str, ...]


def _require_scope(grant: AdminAuthorizationGrant, scope: AdminScope) -> None:
    if scope not in grant.scopes:
        raise PermissionError(f"commercial operation requires {scope.value}")


def _company(store: CommercialStore, company_id: CommercialCompanyId) -> CommercialCompany:
    found = next((item for item in store.companies() if item.company_id == company_id), None)
    if found is None:
        raise LookupError(str(company_id))
    return found


def _audit(
    *,
    store: CommercialStore,
    audit_id: str,
    grant: AdminAuthorizationGrant,
    action: str,
    record_type: str,
    record_id: str,
    origin: CommercialOrigin,
    reason: str,
    occurred_at: datetime,
    before_ref: str | None = None,
    after_ref: str | None = None,
) -> None:
    store.append_audit(
        CommercialAuditRecord(
            audit_id=CommercialAuditId(audit_id),
            occurred_at=occurred_at,
            actor=str(grant.principal_id),
            action=action,
            record_type=record_type,
            record_id=record_id,
            origin=origin,
            reason=reason,
            before_ref=before_ref,
            after_ref=after_ref,
        )
    )


class AdminCommercialService:
    def __init__(self, store: CommercialStore) -> None:
        self._store = store

    def create_prospect(
        self,
        *,
        grant: AdminAuthorizationGrant,
        prospect_id: str,
        display_name: str,
        acquisition_source: str,
        consent_basis: ConsentBasis,
        origin: CommercialOrigin,
        now: datetime,
        reason: str,
    ) -> CommercialProspect:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        record = CommercialProspect(
            prospect_id=CommercialProspectId(prospect_id),
            display_name=display_name,
            acquisition_source=acquisition_source,
            consent_basis=consent_basis,
            origin=origin,
            stage=ProspectStage.NEW,
            created_at=now,
            created_by=str(grant.principal_id),
            updated_at=now,
        )
        if any(item.prospect_id == record.prospect_id for item in self._store.prospects()):
            raise ValueError("commercial prospect already exists")
        self._store.put_prospect(record)
        _audit(
            store=self._store,
            audit_id=f"audit:prospect:create:{prospect_id}",
            grant=grant,
            action="CREATE_PROSPECT",
            record_type="prospect",
            record_id=prospect_id,
            origin=origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-prospect:{prospect_id}",
        )
        return record

    def set_prospect_stage(
        self,
        *,
        grant: AdminAuthorizationGrant,
        prospect_id: str,
        stage: ProspectStage,
        now: datetime,
        reason: str,
        company_id: str | None = None,
        disposition_reason: str | None = None,
    ) -> CommercialProspect:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        current = next(
            (
                item
                for item in self._store.prospects()
                if item.prospect_id == CommercialProspectId(prospect_id)
            ),
            None,
        )
        if current is None:
            raise LookupError(prospect_id)
        linked_company_id = current.company_id
        if company_id is not None:
            linked_company = _company(self._store, CommercialCompanyId(company_id))
            linked_company_id = linked_company.company_id
        updated = replace(
            current,
            stage=stage,
            updated_at=now,
            company_id=linked_company_id,
            disposition_reason=disposition_reason,
        )
        self._store.put_prospect(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:prospect:stage:{prospect_id}:{stage.value}:{now.isoformat()}",
            grant=grant,
            action="SET_PROSPECT_STAGE",
            record_type="prospect",
            record_id=prospect_id,
            origin=current.origin,
            reason=reason,
            occurred_at=now,
            before_ref=f"prospect-stage:{current.stage.value}",
            after_ref=f"prospect-stage:{stage.value}",
        )
        return updated

    def create_company(
        self,
        *,
        grant: AdminAuthorizationGrant,
        company_id: str,
        display_name: str,
        acquisition_source: str,
        consent_basis: ConsentBasis,
        origin: CommercialOrigin,
        now: datetime,
        reason: str,
    ) -> CommercialCompany:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        record = CommercialCompany(
            company_id=CommercialCompanyId(company_id),
            display_name=display_name,
            acquisition_source=acquisition_source,
            consent_basis=consent_basis,
            origin=origin,
            created_at=now,
            created_by=str(grant.principal_id),
        )
        if any(item.company_id == record.company_id for item in self._store.companies()):
            raise ValueError("commercial company already exists")
        self._store.put_company(record)
        _audit(
            store=self._store,
            audit_id=f"audit:company:create:{company_id}",
            grant=grant,
            action="CREATE_COMPANY",
            record_type="company",
            record_id=company_id,
            origin=origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-company:{company_id}",
        )
        return record

    def map_observed_organization(
        self,
        *,
        grant: AdminAuthorizationGrant,
        company_id: str,
        organization_id: str,
        mapping_reason: str,
        now: datetime,
    ) -> CommercialCompany:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        current = _company(self._store, CommercialCompanyId(company_id))
        updated = replace(
            current,
            observed_organization_id=organization_id,
            observed_mapping_reason=mapping_reason,
        )
        self._store.put_company(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:company:org-map:{company_id}:{organization_id}",
            grant=grant,
            action="MAP_OBSERVED_ORGANIZATION_ID",
            record_type="company",
            record_id=company_id,
            origin=CommercialOrigin.PUBLIC_OBSERVATION_REFERENCE,
            reason=mapping_reason,
            occurred_at=now,
            before_ref=(
                None
                if current.observed_organization_id is None
                else f"organization-id:{current.observed_organization_id}"
            ),
            after_ref=f"organization-id:{organization_id}",
        )
        return updated

    def link_account(
        self,
        *,
        grant: AdminAuthorizationGrant,
        company_id: str,
        account_id: str,
        now: datetime,
        reason: str,
    ) -> CommercialCompany:
        _require_scope(grant, AdminScope.CUSTOMERS_WRITE)
        current = _company(self._store, CommercialCompanyId(company_id))
        updated = replace(current, account_id=account_id)
        self._store.put_company(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:company:account:{company_id}:{account_id}",
            grant=grant,
            action="LINK_AXIGNAL_ACCOUNT_REFERENCE",
            record_type="company",
            record_id=company_id,
            origin=CommercialOrigin.USER_PROVIDED,
            reason=reason,
            occurred_at=now,
            before_ref=None if current.account_id is None else f"account-id:{current.account_id}",
            after_ref=f"account-id:{account_id}",
        )
        return updated

    def create_contact(
        self,
        *,
        grant: AdminAuthorizationGrant,
        contact_id: str,
        company_id: str | None,
        display_name: str,
        email: str | None,
        phone: str | None,
        acquisition_source: str,
        consent_basis: ConsentBasis,
        origin: CommercialOrigin,
        now: datetime,
        reason: str,
    ) -> CommercialContact:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        if company_id is not None:
            _company(self._store, CommercialCompanyId(company_id))
        record = CommercialContact(
            contact_id=CommercialContactId(contact_id),
            company_id=None if company_id is None else CommercialCompanyId(company_id),
            display_name=display_name,
            email=email,
            phone=phone,
            acquisition_source=acquisition_source,
            consent_basis=consent_basis,
            origin=origin,
            created_at=now,
            created_by=str(grant.principal_id),
        )
        self._store.put_contact(record)
        _audit(
            store=self._store,
            audit_id=f"audit:contact:create:{contact_id}",
            grant=grant,
            action="CREATE_CONTACT",
            record_type="contact",
            record_id=contact_id,
            origin=origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-contact:{contact_id}",
        )
        return record

    def create_opportunity(
        self,
        *,
        grant: AdminAuthorizationGrant,
        opportunity_id: str,
        company_id: str,
        title: str,
        origin: CommercialOrigin,
        now: datetime,
        reason: str,
    ) -> CommercialOpportunity:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        _company(self._store, CommercialCompanyId(company_id))
        record = CommercialOpportunity(
            opportunity_id=CommercialOpportunityId(opportunity_id),
            company_id=CommercialCompanyId(company_id),
            title=title,
            stage=OpportunityStage.NEW,
            origin=origin,
            created_at=now,
            created_by=str(grant.principal_id),
            updated_at=now,
        )
        self._store.put_opportunity(record)
        _audit(
            store=self._store,
            audit_id=f"audit:opportunity:create:{opportunity_id}",
            grant=grant,
            action="CREATE_OPPORTUNITY",
            record_type="opportunity",
            record_id=opportunity_id,
            origin=origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-opportunity:{opportunity_id}",
        )
        return record

    def set_opportunity_stage(
        self,
        *,
        grant: AdminAuthorizationGrant,
        opportunity_id: str,
        stage: OpportunityStage,
        now: datetime,
        reason: str,
        loss_reason: str | None = None,
    ) -> CommercialOpportunity:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        current = next(
            (
                item
                for item in self._store.opportunities()
                if item.opportunity_id == CommercialOpportunityId(opportunity_id)
            ),
            None,
        )
        if current is None:
            raise LookupError(opportunity_id)
        updated = replace(current, stage=stage, updated_at=now, loss_reason=loss_reason)
        self._store.put_opportunity(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:opportunity:stage:{opportunity_id}:{stage.value}:{now.isoformat()}",
            grant=grant,
            action="SET_OPPORTUNITY_STAGE",
            record_type="opportunity",
            record_id=opportunity_id,
            origin=current.origin,
            reason=reason,
            occurred_at=now,
            before_ref=f"opportunity-stage:{current.stage.value}",
            after_ref=f"opportunity-stage:{stage.value}",
        )
        return updated

    def create_deal(
        self,
        *,
        grant: AdminAuthorizationGrant,
        deal_id: str,
        opportunity_id: str,
        now: datetime,
        reason: str,
    ) -> CommercialDeal:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        opportunity = next(
            (
                item
                for item in self._store.opportunities()
                if item.opportunity_id == CommercialOpportunityId(opportunity_id)
            ),
            None,
        )
        if opportunity is None:
            raise LookupError(opportunity_id)
        record = CommercialDeal(
            deal_id=CommercialDealId(deal_id),
            opportunity_id=opportunity.opportunity_id,
            stage=DealStage.OPEN,
            created_at=now,
            created_by=str(grant.principal_id),
            updated_at=now,
        )
        self._store.put_deal(record)
        _audit(
            store=self._store,
            audit_id=f"audit:deal:create:{deal_id}",
            grant=grant,
            action="CREATE_DEAL",
            record_type="deal",
            record_id=deal_id,
            origin=opportunity.origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-deal:{deal_id}",
        )
        return record

    def set_deal_stage(
        self,
        *,
        grant: AdminAuthorizationGrant,
        deal_id: str,
        stage: DealStage,
        now: datetime,
        reason: str,
        account_id: str | None = None,
        close_reason: str | None = None,
    ) -> CommercialDeal:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        current = next(
            (item for item in self._store.deals() if item.deal_id == CommercialDealId(deal_id)),
            None,
        )
        if current is None:
            raise LookupError(deal_id)
        updated = replace(
            current,
            stage=stage,
            updated_at=now,
            account_id=account_id if account_id is not None else current.account_id,
            close_reason=close_reason,
        )
        self._store.put_deal(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:deal:stage:{deal_id}:{stage.value}:{now.isoformat()}",
            grant=grant,
            action="SET_DEAL_STAGE",
            record_type="deal",
            record_id=deal_id,
            origin=CommercialOrigin.COMMERCIAL_CLAIM,
            reason=reason,
            occurred_at=now,
            before_ref=f"deal-stage:{current.stage.value}",
            after_ref=f"deal-stage:{stage.value}",
        )
        return updated

    def add_note(
        self,
        *,
        grant: AdminAuthorizationGrant,
        note_id: str,
        company_id: str,
        body: str,
        origin: CommercialOrigin,
        now: datetime,
        reason: str,
    ) -> CommercialNote:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        _company(self._store, CommercialCompanyId(company_id))
        record = CommercialNote(
            note_id=CommercialNoteId(note_id),
            company_id=CommercialCompanyId(company_id),
            body=body,
            origin=origin,
            created_at=now,
            created_by=str(grant.principal_id),
        )
        self._store.put_note(record)
        _audit(
            store=self._store,
            audit_id=f"audit:note:create:{note_id}",
            grant=grant,
            action="ADD_COMMERCIAL_NOTE",
            record_type="note",
            record_id=note_id,
            origin=origin,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-note:{note_id}",
        )
        return record

    def add_task(
        self,
        *,
        grant: AdminAuthorizationGrant,
        task_id: str,
        company_id: str,
        title: str,
        due_at: datetime | None,
        now: datetime,
        reason: str,
    ) -> CommercialTask:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        _company(self._store, CommercialCompanyId(company_id))
        record = CommercialTask(
            task_id=CommercialTaskId(task_id),
            company_id=CommercialCompanyId(company_id),
            title=title,
            due_at=due_at,
            state=TaskState.OPEN,
            created_at=now,
            created_by=str(grant.principal_id),
        )
        self._store.put_task(record)
        _audit(
            store=self._store,
            audit_id=f"audit:task:create:{task_id}",
            grant=grant,
            action="ADD_COMMERCIAL_TASK",
            record_type="task",
            record_id=task_id,
            origin=CommercialOrigin.COMMERCIAL_CLAIM,
            reason=reason,
            occurred_at=now,
            after_ref=f"commercial-task:{task_id}",
        )
        return record

    def set_task_state(
        self,
        *,
        grant: AdminAuthorizationGrant,
        task_id: str,
        state: TaskState,
        now: datetime,
        reason: str,
    ) -> CommercialTask:
        _require_scope(grant, AdminScope.COMMERCIAL_WRITE)
        current = next(
            (item for item in self._store.tasks() if item.task_id == CommercialTaskId(task_id)),
            None,
        )
        if current is None:
            raise LookupError(task_id)
        updated = replace(current, state=state)
        self._store.put_task(updated)
        _audit(
            store=self._store,
            audit_id=f"audit:task:state:{task_id}:{state.value}:{now.isoformat()}",
            grant=grant,
            action="SET_TASK_STATE",
            record_type="task",
            record_id=task_id,
            origin=CommercialOrigin.COMMERCIAL_CLAIM,
            reason=reason,
            occurred_at=now,
            before_ref=f"task-state:{current.state.value}",
            after_ref=f"task-state:{state.value}",
        )
        return updated


def project_admin_commercial(
    *,
    store: CommercialStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> AdminCommercialProjection:
    if (
        AdminScope.COMMERCIAL_READ not in grant.scopes
        and AdminScope.CUSTOMERS_READ not in grant.scopes
    ):
        raise PermissionError("commercial projection requires customer or commercial read scope")
    prospects = store.prospects()
    companies = store.companies()
    contacts = store.contacts()
    opportunities = store.opportunities()
    deals = store.deals()
    notes = store.notes()
    tasks = store.tasks()
    audits = store.audits()
    commercial_read = AdminScope.COMMERCIAL_READ in grant.scopes

    origin_counts: dict[str, int] = {}
    for prospect_record in prospects:
        origin_counts[prospect_record.origin.value] = (
            origin_counts.get(prospect_record.origin.value, 0) + 1
        )
    for company_record in companies:
        origin_counts[company_record.origin.value] = (
            origin_counts.get(company_record.origin.value, 0) + 1
        )
    for contact_record in contacts:
        origin_counts[contact_record.origin.value] = (
            origin_counts.get(contact_record.origin.value, 0) + 1
        )
    for opportunity_record in opportunities:
        origin_counts[opportunity_record.origin.value] = (
            origin_counts.get(opportunity_record.origin.value, 0) + 1
        )
    for note_record in notes:
        origin_counts[note_record.origin.value] = origin_counts.get(note_record.origin.value, 0) + 1

    views = []
    for company in companies:
        company_contacts = tuple(item for item in contacts if item.company_id == company.company_id)
        company_opportunities = tuple(
            item for item in opportunities if item.company_id == company.company_id
        )
        company_notes = tuple(item for item in notes if item.company_id == company.company_id)
        company_tasks = tuple(item for item in tasks if item.company_id == company.company_id)
        views.append(
            CommercialCompanyView(
                company_id=str(company.company_id),
                display_name=company.display_name,
                acquisition_source=company.acquisition_source,
                consent_basis=company.consent_basis.value,
                origin=company.origin.value,
                observed_organization_id=(
                    company.observed_organization_id if commercial_read else None
                ),
                account_id=company.account_id,
                opportunity_count=len(company_opportunities) if commercial_read else 0,
                open_task_count=sum(item.state is TaskState.OPEN for item in company_tasks)
                if commercial_read
                else 0,
                note_count=len(company_notes) if commercial_read else 0,
                contact_count=len(company_contacts),
            )
        )

    return AdminCommercialProjection(
        privacy_class="PRIVATE_FIRST_PARTY",
        generated_at=generated_at,
        prospect_count=len(prospects) if commercial_read else 0,
        company_count=len(companies),
        contact_count=len(contacts),
        opportunity_count=len(opportunities) if commercial_read else 0,
        deal_count=len(deals) if commercial_read else 0,
        note_count=len(notes) if commercial_read else 0,
        open_task_count=sum(item.state is TaskState.OPEN for item in tasks)
        if commercial_read
        else 0,
        companies=tuple(views),
        origin_counts=tuple(sorted(origin_counts.items())) if commercial_read else (),
        audit_count=len(audits) if commercial_read else 0,
        pii_visible=False,
        coverage_notes=(
            "AXIGNAL internal commercial state is private first-party operational data, not AXIGLAND economic truth.",
            "Observed Organization links are explicit ID references only; they grant no canonical write authority or identity equivalence.",
            "Account references are external AO-09 identifiers only and do not make commercial records account authority.",
            "Contact PII is excluded from this Admin projection; the owning store retains it under separate authorization.",
            "Commercial claim, user-provided data and public-observation references remain explicitly distinct origins.",
        ),
    )


def export_admin_commercial(
    *,
    store: CommercialStore,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
) -> dict[str, object]:
    _require_scope(grant, AdminScope.COMMERCIAL_READ)
    projection = project_admin_commercial(store=store, grant=grant, generated_at=generated_at)
    return {
        "classification": "PRIVATE_FIRST_PARTY",
        "generatedAt": projection.generated_at.isoformat(),
        "prospectCount": projection.prospect_count,
        "companyCount": projection.company_count,
        "contactCount": projection.contact_count,
        "opportunityCount": projection.opportunity_count,
        "dealCount": projection.deal_count,
        "openTaskCount": projection.open_task_count,
        "companies": [
            {
                "companyId": item.company_id,
                "displayName": item.display_name,
                "acquisitionSource": item.acquisition_source,
                "consentBasis": item.consent_basis,
                "origin": item.origin,
                "observedOrganizationId": item.observed_organization_id,
                "accountId": item.account_id,
            }
            for item in projection.companies
        ],
        "piiIncluded": False,
    }
