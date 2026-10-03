"""AO-23 private Tax / VAT / AEAT operations domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,239}$")
_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,31}$")


class TaxApplicabilityState(StrEnum):
    UNKNOWN = "UNKNOWN"
    APPLIES = "APPLIES"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TaxObligationState(StrEnum):
    UNKNOWN = "UNKNOWN"
    DUE = "DUE"
    PREPARED = "PREPARED"
    FILED = "FILED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TaxEvidenceKind(StrEnum):
    APPLICABILITY = "APPLICABILITY"
    SOURCE_DOCUMENT_SET = "SOURCE_DOCUMENT_SET"
    RECONCILIATION = "RECONCILIATION"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    FILING_RECEIPT = "FILING_RECEIPT"
    AEAT_ACCEPTANCE = "AEAT_ACCEPTANCE"
    AEAT_REJECTION = "AEAT_REJECTION"


class TaxPeriodicity(StrEnum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded opaque identifier")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TaxRuleDefinition:
    rule_id: str
    jurisdiction: str
    model_code: str
    periodicity: TaxPeriodicity
    effective_at: datetime
    deadline_policy: str
    applicability_policy: str
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier(self.rule_id, "rule_id")
        if self.jurisdiction != "ES":
            raise ValueError("AO-23 canonical tax rules currently govern Spain only")
        if not _MODEL.fullmatch(self.model_code):
            raise ValueError("model_code must be bounded")
        _aware(self.effective_at, "effective_at")
        if not self.deadline_policy.strip() or len(self.deadline_policy) > 800:
            raise ValueError("deadline_policy is required")
        if not self.applicability_policy.strip() or len(self.applicability_policy) > 800:
            raise ValueError("applicability_policy is required")
        if len(self.source_refs) < 1:
            raise ValueError("tax rule requires official source references")
        for source_ref in self.source_refs:
            _identifier(source_ref, "source_ref")


@dataclass(frozen=True, slots=True)
class TaxObligation:
    obligation_id: str
    taxpayer_ref: str
    rule_id: str
    model_code: str
    period_start: datetime
    period_end: datetime
    due_at: datetime
    deadline_source_ref: str
    applicability: TaxApplicabilityState
    created_at: datetime

    def __post_init__(self) -> None:
        for value, name in (
            (self.obligation_id, "obligation_id"),
            (self.taxpayer_ref, "taxpayer_ref"),
            (self.rule_id, "rule_id"),
            (self.deadline_source_ref, "deadline_source_ref"),
        ):
            _identifier(value, name)
        if not _MODEL.fullmatch(self.model_code):
            raise ValueError("model_code must be bounded")
        _aware(self.period_start, "period_start")
        _aware(self.period_end, "period_end")
        _aware(self.due_at, "due_at")
        _aware(self.created_at, "created_at")
        if self.period_end <= self.period_start:
            raise ValueError("tax period end must follow start")
        if self.due_at <= self.period_end:
            raise ValueError("tax due date must follow period end")


@dataclass(frozen=True, slots=True)
class TaxEvidence:
    evidence_id: str
    obligation_id: str
    kind: TaxEvidenceKind
    observed_at: datetime
    source_ref: str
    artifact_fingerprint: str
    actor_ref: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.evidence_id, "evidence_id"),
            (self.obligation_id, "obligation_id"),
            (self.source_ref, "source_ref"),
            (self.artifact_fingerprint, "artifact_fingerprint"),
        ):
            _identifier(value, name)
        _aware(self.observed_at, "observed_at")
        if not self.artifact_fingerprint.startswith("sha256:"):
            raise ValueError("tax evidence fingerprint must be sha256")
        if self.actor_ref is not None:
            _identifier(self.actor_ref, "actor_ref")


@dataclass(frozen=True, slots=True)
class TaxOperationView:
    obligation: TaxObligation
    state: TaxObligationState
    overdue: bool
    evidence_kinds: tuple[TaxEvidenceKind, ...]
    missing_evidence: tuple[TaxEvidenceKind, ...]
    complete: bool


@dataclass(frozen=True, slots=True)
class TaxOperationsProjection:
    generated_at: datetime
    privacy_class: str
    ruleset_version: str
    obligations: tuple[TaxOperationView, ...]
    coverage_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaxAdvisorExport:
    obligation_id: str
    model_code: str
    period_start: str
    period_end: str
    due_at: str
    state: str
    deadline_source_ref: str
    evidence_refs: tuple[str, ...]
    complete: bool
