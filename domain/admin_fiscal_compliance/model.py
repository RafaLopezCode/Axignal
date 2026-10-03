"""AO-22 provider-neutral SIF / VERI*FACTU compliance-decision domain."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,239}$")


class FiscalArchitectureRoute(StrEnum):
    EXTERNAL_SIF_PROVIDER = "EXTERNAL_SIF_PROVIDER"
    AXIGNAL_OWN_SIF = "AXIGNAL_OWN_SIF"


class FiscalEvidenceKind(StrEnum):
    PROVIDER_RESPONSIBLE_DECLARATION = "PROVIDER_RESPONSIBLE_DECLARATION"
    PROVIDER_TECHNICAL_CONTRACT = "PROVIDER_TECHNICAL_CONTRACT"
    NON_PRODUCTION_TEST = "NON_PRODUCTION_TEST"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class FiscalEnablementState(StrEnum):
    NO_PROVIDER = "NO_PROVIDER"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_READY = "EVIDENCE_READY"
    LIVE_ENABLEMENT_ALLOWED = "LIVE_ENABLEMENT_ALLOWED"


def _identifier(value: str, name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{name} must be a bounded opaque identifier")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class FiscalRuleSet:
    ruleset_id: str
    jurisdiction: str
    effective_at: datetime
    corporate_deadline: datetime
    other_taxpayer_deadline: datetime
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier(self.ruleset_id, "ruleset_id")
        if self.jurisdiction != "ES":
            raise ValueError("AO-22 ruleset currently governs Spain only")
        for value, name in (
            (self.effective_at, "effective_at"),
            (self.corporate_deadline, "corporate_deadline"),
            (self.other_taxpayer_deadline, "other_taxpayer_deadline"),
        ):
            _aware(value, name)
        if self.corporate_deadline <= self.effective_at:
            raise ValueError("corporate deadline must follow ruleset effective time")
        if self.other_taxpayer_deadline < self.corporate_deadline:
            raise ValueError("other taxpayer deadline cannot precede corporate deadline")
        if len(self.source_refs) < 2:
            raise ValueError("fiscal ruleset requires multiple official source references")
        for source_ref in self.source_refs:
            _identifier(source_ref, "source_ref")


@dataclass(frozen=True, slots=True)
class FiscalProviderSelection:
    selection_id: str
    integration_id: str
    route: FiscalArchitectureRoute
    selected_at: datetime
    decision_ref: str

    def __post_init__(self) -> None:
        _identifier(self.selection_id, "selection_id")
        _identifier(self.integration_id, "integration_id")
        _aware(self.selected_at, "selected_at")
        _identifier(self.decision_ref, "decision_ref")
        if self.route is not FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER:
            raise ValueError(
                "AXIGNAL-owned SIF is not authorized by AO-22; separate ADR/compliance project required"
            )


@dataclass(frozen=True, slots=True)
class FiscalComplianceEvidence:
    evidence_id: str
    integration_id: str
    kind: FiscalEvidenceKind
    provider_version: str
    observed_at: datetime
    source_ref: str
    artifact_fingerprint: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.evidence_id, "evidence_id"),
            (self.integration_id, "integration_id"),
            (self.provider_version, "provider_version"),
            (self.source_ref, "source_ref"),
            (self.artifact_fingerprint, "artifact_fingerprint"),
        ):
            _identifier(value, name)
        _aware(self.observed_at, "observed_at")
        if not self.artifact_fingerprint.startswith("sha256:"):
            raise ValueError("artifact fingerprint must be sha256")


@dataclass(frozen=True, slots=True)
class FiscalComplianceProjection:
    generated_at: datetime
    route: FiscalArchitectureRoute
    state: FiscalEnablementState
    ruleset: FiscalRuleSet
    integration_id: str | None
    provider_version: str | None
    evidence_kinds: tuple[FiscalEvidenceKind, ...]
    missing_evidence: tuple[FiscalEvidenceKind, ...]
    live_enablement_allowed: bool
    compliance_claim_allowed: bool
    coverage_notes: tuple[str, ...]
