from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.admin_fiscal_compliance import (
    CANONICAL_AO22_DECISION,
    FiscalComplianceService,
    project_fiscal_compliance,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_fiscal_compliance import (
    FiscalArchitectureRoute,
    FiscalComplianceEvidence,
    FiscalEnablementState,
    FiscalEvidenceKind,
    FiscalProviderSelection,
    FiscalRuleSet,
)
from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
)
from pipeline.admin_fiscal_compliance import SqliteFiscalComplianceStore
from pipeline.admin_integrations import SqliteAdminIntegrationStore

NOW = datetime(2026, 10, 3, 20, 45, tzinfo=UTC)
RULESET = FiscalRuleSet(
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


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _register_sif(store: SqliteAdminIntegrationStore) -> None:
    store.append_definition(
        operation_id="register-sif-provider",
        occurred_at=NOW,
        definition=IntegrationDefinition(
            integration_id="sif-provider",
            provider="EXTERNAL_SIF_PROVIDER",
            purpose="External SIF / VERI*FACTU invoice issuance adapter",
            owner="AXIGNAL Finance",
            environment=IntegrationEnvironment.PRODUCTION,
            enabled=True,
            credential=CredentialLifecycle(
                reference="secret://axignal/fiscal/sif-provider",
                state=CredentialState.CONFIGURED,
                last_rotated_at=NOW,
            ),
            scopes=("invoice.issue", "invoice.cancel", "fiscal.status.read"),
            direction=IntegrationDirection.BIDIRECTIONAL,
            authority_boundary=(
                "Provider owns regulated SIF mechanics; AXIGNAL owns private operational references."
            ),
            webhook_capable=True,
            webhook_endpoint="https://axignal.com/internal/webhooks/fiscal",
            rate_limit_posture="provider-governed",
            health_freshness_seconds=3600,
        ),
    )


def _evidence(
    kind: FiscalEvidenceKind, *, version: str = "provider-v1"
) -> FiscalComplianceEvidence:
    return FiscalComplianceEvidence(
        evidence_id=f"fiscal-evidence:{kind.value.lower()}:{version}",
        integration_id="sif-provider",
        kind=kind,
        provider_version=version,
        observed_at=NOW,
        source_ref=f"artifact:{kind.value.lower()}:{version}",
        artifact_fingerprint="sha256:" + "a" * 64,
    )


def test_ao22_canonical_decision_is_external_provider_and_own_sif_is_forbidden() -> None:
    assert CANONICAL_AO22_DECISION.route is FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER
    assert CANONICAL_AO22_DECISION.own_sif_authorized is False
    with pytest.raises(ValueError, match="not authorized"):
        FiscalProviderSelection(
            selection_id="selection:own-sif",
            integration_id="axignal-own-sif",
            route=FiscalArchitectureRoute.AXIGNAL_OWN_SIF,
            selected_at=NOW,
            decision_ref="adr:0069",
        )


def test_no_provider_means_no_live_enablement_or_compliance_claim(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")

    projection = project_fiscal_compliance(
        store=fiscal,
        integration_store=integrations,
        ruleset=RULESET,
        grant=_grant(),
        generated_at=NOW,
    )

    assert projection.state is FiscalEnablementState.NO_PROVIDER
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False
    assert projection.ruleset.corporate_deadline.year == 2027
    assert projection.ruleset.other_taxpayer_deadline.month == 7


def test_selected_provider_requires_ao18_registration_and_complete_evidence(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    service = FiscalComplianceService(fiscal, integrations)
    selection = FiscalProviderSelection(
        selection_id="selection:sif-provider:v1",
        integration_id="sif-provider",
        route=FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER,
        selected_at=NOW,
        decision_ref="adr:0069",
    )

    with pytest.raises(ValueError, match="not registered"):
        service.select_external_provider(grant=_grant(), selection=selection)

    _register_sif(integrations)
    assert service.select_external_provider(grant=_grant(), selection=selection) is True

    service.record_evidence(
        grant=_grant(),
        evidence=_evidence(FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION),
    )
    incomplete = project_fiscal_compliance(
        store=fiscal,
        integration_store=integrations,
        ruleset=RULESET,
        grant=_grant(),
        generated_at=NOW,
    )
    assert incomplete.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert incomplete.live_enablement_allowed is False
    assert FiscalEvidenceKind.NON_PRODUCTION_TEST in incomplete.missing_evidence


def test_full_same_version_evidence_allows_live_enablement(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    _register_sif(integrations)
    service = FiscalComplianceService(fiscal, integrations)
    service.select_external_provider(
        grant=_grant(),
        selection=FiscalProviderSelection(
            selection_id="selection:sif-provider:v1",
            integration_id="sif-provider",
            route=FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER,
            selected_at=NOW,
            decision_ref="adr:0069",
        ),
    )

    for kind in FiscalEvidenceKind:
        service.record_evidence(grant=_grant(), evidence=_evidence(kind))

    projection = project_fiscal_compliance(
        store=fiscal,
        integration_store=integrations,
        ruleset=RULESET,
        grant=_grant(),
        generated_at=NOW,
    )

    assert projection.state is FiscalEnablementState.LIVE_ENABLEMENT_ALLOWED
    assert projection.provider_version == "provider-v1"
    assert projection.missing_evidence == ()
    assert projection.live_enablement_allowed is True
    assert projection.compliance_claim_allowed is True


def test_mixed_provider_versions_invalidate_complete_evidence_set(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    _register_sif(integrations)
    service = FiscalComplianceService(fiscal, integrations)
    service.select_external_provider(
        grant=_grant(),
        selection=FiscalProviderSelection(
            selection_id="selection:sif-provider:v1",
            integration_id="sif-provider",
            route=FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER,
            selected_at=NOW,
            decision_ref="adr:0069",
        ),
    )

    for index, kind in enumerate(FiscalEvidenceKind):
        version = "provider-v2" if index == 0 else "provider-v1"
        service.record_evidence(grant=_grant(), evidence=_evidence(kind, version=version))

    projection = project_fiscal_compliance(
        store=fiscal,
        integration_store=integrations,
        ruleset=RULESET,
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.provider_version is None
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False


def test_fiscal_projection_requires_fiscal_read_scope(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")

    with pytest.raises(PermissionError, match="admin:fiscal:read"):
        project_fiscal_compliance(
            store=fiscal,
            integration_store=integrations,
            ruleset=RULESET,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
        )


def test_runtime_starts_fiscal_compliance_fail_closed_without_provider(tmp_path: Path) -> None:
    from application.admin_fiscal_compliance import (
        canonical_es_sif_ruleset,
        project_fiscal_compliance,
    )
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime

    root = Path(__file__).resolve().parents[2]
    runtime = build_runtime(
        RuntimeConfig(
            environment="development",
            bind_host="127.0.0.1",
            port=8765,
            code_sha="d" * 40,
            data_dir=tmp_path / "runtime-data",
            web_root=root / "apps" / "web",
        )
    )
    assert runtime.admin_fiscal_compliance_store.path.is_file()
    projection = project_fiscal_compliance(
        store=runtime.admin_fiscal_compliance_store,
        integration_store=runtime.admin_integration_store,
        ruleset=canonical_es_sif_ruleset(),
        grant=_grant(),
        generated_at=NOW,
    )
    assert projection.state is FiscalEnablementState.NO_PROVIDER
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False
    assert projection.ruleset.corporate_deadline.isoformat().startswith("2027-01-01")
    assert projection.ruleset.other_taxpayer_deadline.isoformat().startswith("2027-07-01")

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-fiscal-summary" in html
    assert "Fiscal compliance gate" in html
    assert "bootstrap.fiscalCompliance" in javascript
    assert "Compliance claim" in javascript
