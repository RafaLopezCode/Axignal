"""AO-22 SIF / VERI*FACTU architecture and live-enablement gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from domain.admin_access import AdminAssurance, AdminAuthorizationGrant, AdminScope
from domain.admin_fiscal_compliance import (
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
    FiscalEvidenceKind.HUMAN_APPROVAL,
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


def project_fiscal_compliance(
    *,
    store: FiscalComplianceStore,
    integration_store: IntegrationStore,
    ruleset: FiscalRuleSet,
    grant: AdminAuthorizationGrant,
    generated_at: datetime,
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
            evidence_kinds=(),
            missing_evidence=_REQUIRED_EVIDENCE,
            live_enablement_allowed=False,
            compliance_claim_allowed=False,
            coverage_notes=(
                "AO-22 chooses an external SIF provider route; no provider is selected yet.",
                "AXIGNAL-owned SIF remains unauthorized.",
                "No production invoice path may claim VERI*FACTU compliance without provider/version evidence.",
            ),
        )

    _configured_provider(integration_store, selection.integration_id)
    provider_evidence = tuple(
        item for item in store.evidence() if item.integration_id == selection.integration_id
    )
    versions = {item.provider_version for item in provider_evidence}
    provider_version = next(iter(versions)) if len(versions) == 1 else None
    kinds = tuple(sorted({item.kind for item in provider_evidence}, key=lambda item: item.value))
    missing = tuple(item for item in _REQUIRED_EVIDENCE if item not in kinds)

    if provider_version is None or missing:
        state = FiscalEnablementState.EVIDENCE_INCOMPLETE
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
        provider_version=provider_version,
        evidence_kinds=kinds,
        missing_evidence=missing,
        live_enablement_allowed=allowed,
        compliance_claim_allowed=allowed,
        coverage_notes=(
            "Provider evidence is version-specific; changing provider version invalidates a complete evidence set.",
            "Third-party SIF use does not remove the taxpayer's legal responsibility.",
            "Compliance status is private operational evidence and never AXIGLAND truth.",
        ),
    )
