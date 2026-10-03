"""AO-22 SIF / VERI*FACTU architecture and live-enablement gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_fiscal_compliance import (
    FiscalApprovalDecision,
    FiscalApprovalEvent,
    FiscalArchitectureRoute,
    FiscalComplianceEvidence,
    FiscalComplianceProjection,
    FiscalEnablementState,
    FiscalEvidenceKind,
    FiscalProviderSelection,
    FiscalRuleSet,
)
from domain.admin_integrations import CredentialState, IntegrationDefinition


class FiscalComplianceStore(Protocol):
    def put_selection(self, selection: FiscalProviderSelection) -> bool: ...
    def selection(self) -> FiscalProviderSelection | None: ...
    def append_evidence(self, evidence: FiscalComplianceEvidence) -> bool: ...
    def evidence(self) -> tuple[FiscalComplianceEvidence, ...]: ...
    def append_approval(self, event: FiscalApprovalEvent) -> bool: ...
    def approvals(self) -> tuple[FiscalApprovalEvent, ...]: ...


class FiscalArtifactIntegrity(Protocol):
    def verify(self, reference: str) -> bool: ...


class IntegrationStore(Protocol):
    def all_definitions(self) -> tuple[IntegrationDefinition, ...]: ...


def canonical_es_sif_ruleset() -> FiscalRuleSet:
    return FiscalRuleSet(
        ruleset_id="es-sif-verifactu-2026-10-03",
        jurisdiction="ES",
        effective_at=datetime(2025, 12, 4, tzinfo=UTC),
        corporate_deadline=datetime(2027, 1, 1, tzinfo=UTC),
        other_taxpayer_deadline=datetime(2027, 7, 1, tzinfo=UTC),
        source_refs=(
            "boe:rd1007:consolidated:2025-12-03",
            "boe:rdl15:2025-12-02",
            "aeat:verifactu:faq:2026-07-21",
        ),
    )


_REQUIRED_EVIDENCE = (
    FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION,
    FiscalEvidenceKind.PROVIDER_TECHNICAL_CONTRACT,
    FiscalEvidenceKind.NON_PRODUCTION_TEST,
)


@dataclass(frozen=True, slots=True)
class FiscalArchitectureDecision:
    route: FiscalArchitectureRoute
    own_sif_authorized: bool
    provider_neutral: bool
    decision_ref: str
    rationale: tuple[str, ...]


CANONICAL_AO22_DECISION = FiscalArchitectureDecision(
    route=FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER,
    own_sif_authorized=False,
    provider_neutral=True,
    decision_ref="adr:0069",
    rationale=(
        "Avoid making AXIGNAL the producer of regulated billing software.",
        "Keep invoice/SIF regulatory mechanics behind a replaceable AO-18 adapter.",
        "Preserve AO-20 financial documents and AO-21 accounting as private operational domains.",
        "Require provider/version evidence before any live compliance claim or enablement.",
    ),
)


def _require_read(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FISCAL_READ not in grant.scopes:
        raise PermissionError("fiscal compliance requires admin:fiscal:read")


def _require_write(grant: AdminAuthorizationGrant) -> None:
    if AdminScope.FISCAL_WRITE not in grant.scopes:
        raise PermissionError("fiscal compliance mutation requires admin:fiscal:write")
    if grant.assurance is not AdminAssurance.STEP_UP:
        raise PermissionError("fiscal compliance mutation requires STEP_UP assurance")


def _configured_provider(
    integration_store: IntegrationStore, integration_id: str
) -> IntegrationDefinition:
    definition = next(
        (
            item
            for item in integration_store.all_definitions()
            if item.integration_id == integration_id
        ),
        None,
    )
    if definition is None:
        raise ValueError("SIF provider is not registered in AO-18")
    if not definition.enabled:
        raise ValueError("SIF provider integration is disabled")
    if definition.credential.state not in {
        CredentialState.CONFIGURED,
        CredentialState.ROTATION_DUE,
    }:
        raise ValueError("SIF provider credential is not configured")
    purpose = definition.purpose.lower()
    if "sif" not in purpose and "verifactu" not in purpose and "factur" not in purpose:
        raise ValueError("AO-18 integration is not declared for SIF/VERI*FACTU use")
    return definition


class FiscalComplianceService:
    def __init__(
        self,
        store: FiscalComplianceStore,
        integration_store: IntegrationStore,
    ) -> None:
        self._store = store
        self._integration_store = integration_store

    def select_external_provider(
        self,
        *,
        grant: AdminAuthorizationGrant,
        selection: FiscalProviderSelection,
    ) -> bool:
        _require_write(grant)
        _configured_provider(self._integration_store, selection.integration_id)
        if selection.route is not FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER:
            raise ValueError("only the AO-22 external SIF route is authorized")
        return self._store.put_selection(selection)

    def record_evidence(
        self,
        *,
        grant: AdminAuthorizationGrant,
        evidence: FiscalComplianceEvidence,
    ) -> bool:
        _require_write(grant)
        selection = self._store.selection()
        if selection is None or selection.integration_id != evidence.integration_id:
            raise ValueError("fiscal evidence must belong to selected SIF provider")
        _configured_provider(self._integration_store, evidence.integration_id)
        return self._store.append_evidence(evidence)

    def record_approval(
        self,
        *,
        grant: AdminAuthorizationGrant,
        event: FiscalApprovalEvent,
    ) -> bool:
        _require_write(grant)
        selection = self._store.selection()
        if selection is None or selection.integration_id != event.integration_id:
            raise ValueError("fiscal approval must belong to selected SIF provider")
        if event.actor_ref != str(grant.principal_id):
            raise ValueError("fiscal approval actor must match the STEP_UP admin principal")
        _configured_provider(self._integration_store, event.integration_id)
        return self._store.append_approval(event)


def project_fiscal_compliance(
    *,
    store: FiscalComplianceStore,
    integration_store: IntegrationStore,
    ruleset: FiscalRuleSet,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
    artifact_integrity: FiscalArtifactIntegrity,
) -> FiscalComplianceProjection:
    _require_read(grant)
    selection = store.selection()
    if selection is None:
        return FiscalComplianceProjection(
            generated_at=generated_at,
            route=CANONICAL_AO22_DECISION.route,
            state=FiscalEnablementState.NO_PROVIDER,
            ruleset=ruleset,
            integration_id=None,
            provider_version=None,
            adapter_version=None,
            integration_definition_version=None,
            approval_effective=False,
            evidence_kinds=(),
            missing_evidence=_REQUIRED_EVIDENCE,
            live_enablement_allowed=False,
            compliance_claim_allowed=False,
            invalid_reasons=("NO_PROVIDER",),
            coverage_notes=(
                "AO-22 chooses an external SIF provider route; no provider is selected yet.",
                "AXIGNAL-owned SIF remains unauthorized.",
                "No production invoice path may claim VERI*FACTU compliance without provider/version evidence.",
            ),
        )

    definition = _configured_provider(integration_store, selection.integration_id)
    invalid_reasons: list[str] = []

    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("fiscal compliance generated_at must be timezone-aware")
    if selection.selected_at > generated_at:
        invalid_reasons.append("SELECTION_FROM_FUTURE")
    if ruleset.ruleset_id != selection.ruleset_id:
        invalid_reasons.append("RULESET_DRIFT")
    if definition.version != selection.integration_definition_version:
        invalid_reasons.append("INTEGRATION_DEFINITION_DRIFT")

    eligible: list[FiscalComplianceEvidence] = []
    for item in store.evidence():
        if item.integration_id != selection.integration_id:
            continue
        if item.observed_at > generated_at:
            invalid_reasons.append(f"FUTURE_EVIDENCE:{item.evidence_id}")
            continue
        if item.provider_product_version != selection.provider_product_version:
            invalid_reasons.append(f"PROVIDER_PRODUCT_VERSION_DRIFT:{item.evidence_id}")
            continue
        if item.adapter_version != selection.adapter_version:
            invalid_reasons.append(f"ADAPTER_VERSION_DRIFT:{item.evidence_id}")
            continue
        if item.integration_definition_version != selection.integration_definition_version:
            invalid_reasons.append(f"INTEGRATION_VERSION_DRIFT:{item.evidence_id}")
            continue
        if item.ruleset_id != selection.ruleset_id:
            invalid_reasons.append(f"EVIDENCE_RULESET_DRIFT:{item.evidence_id}")
            continue
        expected_ref = "cas:" + item.artifact_fingerprint
        if item.artifact_ref != expected_ref or not artifact_integrity.verify(item.artifact_ref):
            invalid_reasons.append(f"ARTIFACT_UNVERIFIED:{item.evidence_id}")
            continue
        eligible.append(item)

    kinds = tuple(sorted({item.kind for item in eligible}, key=lambda item: item.value))
    missing = tuple(item for item in _REQUIRED_EVIDENCE if item not in kinds)

    approval_events = sorted(
        (
            event
            for event in store.approvals()
            if event.integration_id == selection.integration_id
            and event.provider_product_version == selection.provider_product_version
            and event.adapter_version == selection.adapter_version
            and event.integration_definition_version == selection.integration_definition_version
            and event.ruleset_id == selection.ruleset_id
            and event.occurred_at <= generated_at
        ),
        key=lambda event: (event.occurred_at, event.approval_event_id),
    )
    approval_effective = bool(
        approval_events and approval_events[-1].decision is FiscalApprovalDecision.APPROVED
    )
    if not approval_effective:
        invalid_reasons.append("HUMAN_APPROVAL_NOT_EFFECTIVE")

    binding_blockers = {
        "SELECTION_FROM_FUTURE",
        "RULESET_DRIFT",
        "INTEGRATION_DEFINITION_DRIFT",
    }
    if missing or any(reason in binding_blockers for reason in invalid_reasons):
        state = FiscalEnablementState.EVIDENCE_INCOMPLETE
        allowed = False
    elif not approval_effective:
        state = FiscalEnablementState.EVIDENCE_READY
        allowed = False
    else:
        state = FiscalEnablementState.LIVE_ENABLEMENT_ALLOWED
        allowed = True

    return FiscalComplianceProjection(
        generated_at=generated_at,
        route=selection.route,
        state=state,
        ruleset=ruleset,
        integration_id=selection.integration_id,
        provider_version=selection.provider_product_version,
        adapter_version=selection.adapter_version,
        integration_definition_version=selection.integration_definition_version,
        approval_effective=approval_effective,
        evidence_kinds=kinds,
        missing_evidence=missing,
        live_enablement_allowed=allowed,
        compliance_claim_allowed=allowed,
        invalid_reasons=tuple(sorted(set(invalid_reasons))),
        coverage_notes=(
            "Evidence is artifact-verified and evaluated as-of against the exact provider product, adapter, integration definition and ruleset binding.",
            "A HUMAN_APPROVAL evidence kind is not authority; effective approval comes only from the governed approval event ledger.",
            "Provider/version drift invalidates a complete evidence set until the exact deployed binding is re-evidenced and re-approved.",
            "Third-party SIF use does not remove the taxpayer's legal responsibility.",
            "Compliance status is private operational evidence and never AXIGLAND truth.",
        ),
    )
