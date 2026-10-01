"""AO-08 first-party AXIGNAL commercial operations domain.

This domain owns AXIGNAL's private commercial records only. It has no canonical
AXIGLAND write authority and intentionally avoids imports from canonical
Organization/FAXT/Relationship/Xignal domains.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

CommercialProspectId = NewType("CommercialProspectId", str)
CommercialCompanyId = NewType("CommercialCompanyId", str)
CommercialContactId = NewType("CommercialContactId", str)
CommercialOpportunityId = NewType("CommercialOpportunityId", str)
CommercialDealId = NewType("CommercialDealId", str)
CommercialNoteId = NewType("CommercialNoteId", str)
CommercialTaskId = NewType("CommercialTaskId", str)
CommercialAuditId = NewType("CommercialAuditId", str)


class CommercialOrigin(StrEnum):
    COMMERCIAL_CLAIM = "COMMERCIAL_CLAIM"
    USER_PROVIDED = "USER_PROVIDED"
    PUBLIC_OBSERVATION_REFERENCE = "PUBLIC_OBSERVATION_REFERENCE"


class ConsentBasis(StrEnum):
    UNKNOWN = "UNKNOWN"
    CONSENT = "CONSENT"
    LEGITIMATE_INTEREST = "LEGITIMATE_INTEREST"
    CONTRACT = "CONTRACT"


class ProspectStage(StrEnum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    DISQUALIFIED = "DISQUALIFIED"
    CONVERTED = "CONVERTED"


class OpportunityStage(StrEnum):
    NEW = "NEW"
    QUALIFYING = "QUALIFYING"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"


class DealStage(StrEnum):
    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"
    CANCELLED = "CANCELLED"


class TaskState(StrEnum):
    OPEN = "OPEN"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class CommercialProspect:
    prospect_id: CommercialProspectId
    display_name: str
    acquisition_source: str
    consent_basis: ConsentBasis
    origin: CommercialOrigin
    stage: ProspectStage
    created_at: datetime
    created_by: str
    updated_at: datetime
    company_id: CommercialCompanyId | None = None
    disposition_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.prospect_id, "prospect id")
        _text(self.display_name, "display name")
        _text(self.acquisition_source, "acquisition source")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        _aware(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("prospect updated_at cannot precede created_at")
        if self.company_id is not None:
            _text(self.company_id, "company id")
        if self.stage is ProspectStage.CONVERTED and self.company_id is None:
            raise ValueError("converted prospect requires commercial company reference")
        if self.stage is ProspectStage.DISQUALIFIED and not self.disposition_reason:
            raise ValueError("disqualified prospect requires reason")


@dataclass(frozen=True, slots=True)
class CommercialCompany:
    company_id: CommercialCompanyId
    display_name: str
    acquisition_source: str
    consent_basis: ConsentBasis
    origin: CommercialOrigin
    created_at: datetime
    created_by: str
    observed_organization_id: str | None = None
    observed_mapping_reason: str | None = None
    account_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.company_id, "company id")
        _text(self.display_name, "display name")
        _text(self.acquisition_source, "acquisition source")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        if self.observed_organization_id is not None:
            _text(self.observed_organization_id, "observed organization id")
            if self.observed_mapping_reason is None:
                raise ValueError("explicit observed Organization mapping requires reason")
            _text(self.observed_mapping_reason, "observed mapping reason")
        elif self.observed_mapping_reason is not None:
            raise ValueError("mapping reason requires observed Organization id")
        if self.account_id is not None:
            _text(self.account_id, "account id")


@dataclass(frozen=True, slots=True)
class CommercialContact:
    contact_id: CommercialContactId
    company_id: CommercialCompanyId | None
    display_name: str
    email: str | None
    phone: str | None
    acquisition_source: str
    consent_basis: ConsentBasis
    origin: CommercialOrigin
    created_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        _text(self.contact_id, "contact id")
        _text(self.display_name, "display name")
        _text(self.acquisition_source, "acquisition source")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        if self.company_id is not None:
            _text(self.company_id, "company id")
        if self.email is not None:
            _text(self.email, "email")
        if self.phone is not None:
            _text(self.phone, "phone")


@dataclass(frozen=True, slots=True)
class CommercialOpportunity:
    opportunity_id: CommercialOpportunityId
    company_id: CommercialCompanyId
    title: str
    stage: OpportunityStage
    origin: CommercialOrigin
    created_at: datetime
    created_by: str
    updated_at: datetime
    loss_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.opportunity_id, "opportunity id")
        _text(self.company_id, "company id")
        _text(self.title, "title")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        _aware(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("opportunity updated_at cannot precede created_at")
        if self.stage is OpportunityStage.LOST and not self.loss_reason:
            raise ValueError("lost opportunity requires loss reason")


@dataclass(frozen=True, slots=True)
class CommercialDeal:
    deal_id: CommercialDealId
    opportunity_id: CommercialOpportunityId
    stage: DealStage
    created_at: datetime
    created_by: str
    updated_at: datetime
    account_id: str | None = None
    close_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.deal_id, "deal id")
        _text(self.opportunity_id, "opportunity id")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        _aware(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("deal updated_at cannot precede created_at")
        if self.account_id is not None:
            _text(self.account_id, "account id")
        if self.stage in {DealStage.LOST, DealStage.CANCELLED} and not self.close_reason:
            raise ValueError("closed unsuccessful deal requires close reason")


@dataclass(frozen=True, slots=True)
class CommercialNote:
    note_id: CommercialNoteId
    company_id: CommercialCompanyId
    body: str
    origin: CommercialOrigin
    created_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        _text(self.note_id, "note id")
        _text(self.company_id, "company id")
        _text(self.body, "note body")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class CommercialTask:
    task_id: CommercialTaskId
    company_id: CommercialCompanyId
    title: str
    due_at: datetime | None
    state: TaskState
    created_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        _text(self.task_id, "task id")
        _text(self.company_id, "company id")
        _text(self.title, "title")
        _text(self.created_by, "created by")
        _aware(self.created_at, "created_at")
        if self.due_at is not None:
            _aware(self.due_at, "due_at")


@dataclass(frozen=True, slots=True)
class CommercialAuditRecord:
    audit_id: CommercialAuditId
    occurred_at: datetime
    actor: str
    action: str
    record_type: str
    record_id: str
    origin: CommercialOrigin
    reason: str
    before_ref: str | None = None
    after_ref: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.audit_id, "audit id"),
            (self.actor, "actor"),
            (self.action, "action"),
            (self.record_type, "record type"),
            (self.record_id, "record id"),
            (self.reason, "reason"),
        ):
            _text(value, name)
        _aware(self.occurred_at, "occurred_at")
