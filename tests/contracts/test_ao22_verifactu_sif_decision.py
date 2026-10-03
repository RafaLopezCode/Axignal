from dataclasses import replace
from datetime import UTC, datetime, timedelta
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
    FiscalApprovalDecision,
    FiscalApprovalEvent,
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
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)

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
PRODUCT_VERSION = "provider-product-v1"
ADAPTER_VERSION = "axignal-fiscal-adapter-v1"
DOC_KINDS = (
    FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION,
    FiscalEvidenceKind.PROVIDER_TECHNICAL_CONTRACT,
    FiscalEvidenceKind.NON_PRODUCTION_TEST,
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


def _definition(*, version: int = 1, enabled: bool = True) -> IntegrationDefinition:
    return IntegrationDefinition(
        integration_id="sif-provider",
        provider="EXTERNAL_SIF_PROVIDER",
        purpose="External SIF / VERI*FACTU invoice issuance adapter",
        owner="AXIGNAL Finance",
        environment=IntegrationEnvironment.PRODUCTION,
        enabled=enabled,
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
        version=version,
    )


def _register_sif(store: SqliteAdminIntegrationStore, *, version: int = 1) -> None:
    store.append_definition(
        operation_id=f"register-sif-provider-v{version}",
        occurred_at=NOW + timedelta(minutes=version - 1),
        definition=_definition(version=version),
    )


def _selection(
    *,
    product_version: str = PRODUCT_VERSION,
    adapter_version: str = ADAPTER_VERSION,
    integration_version: int = 1,
    ruleset_id: str = RULESET.ruleset_id,
) -> FiscalProviderSelection:
    return FiscalProviderSelection(
        selection_id=f"selection:sif-provider:v{integration_version}",
        integration_id="sif-provider",
        route=FiscalArchitectureRoute.EXTERNAL_SIF_PROVIDER,
        selected_at=NOW,
        decision_ref="adr:0069",
        provider_product_version=product_version,
        adapter_version=adapter_version,
        integration_definition_version=integration_version,
        ruleset_id=ruleset_id,
    )


def _evidence(
    kind: FiscalEvidenceKind,
    *,
    artifacts: ContentAddressedArtifactStore,
    observed_at: datetime = NOW,
    product_version: str = PRODUCT_VERSION,
    adapter_version: str = ADAPTER_VERSION,
    integration_version: int = 1,
    ruleset_id: str = RULESET.ruleset_id,
    suffix: str = "base",
) -> FiscalComplianceEvidence:
    payload = (
        f"{kind.value}|{product_version}|{adapter_version}|"
        f"{integration_version}|{ruleset_id}|{suffix}"
    ).encode()
    artifact_ref = artifacts.put_bytes(payload)
    fingerprint = "sha256:" + ContentAddressedArtifactStore.digest(artifact_ref)
    return FiscalComplianceEvidence(
        evidence_id=f"fiscal-evidence:{kind.value.lower()}:{suffix}",
        integration_id="sif-provider",
        kind=kind,
        provider_product_version=product_version,
        adapter_version=adapter_version,
        integration_definition_version=integration_version,
        ruleset_id=ruleset_id,
        observed_at=observed_at,
        source_ref=f"provider-evidence:{kind.value.lower()}:{suffix}",
        artifact_ref=artifact_ref,
        artifact_fingerprint=fingerprint,
    )


def _approval(
    *,
    decision: FiscalApprovalDecision = FiscalApprovalDecision.APPROVED,
    occurred_at: datetime = NOW,
    suffix: str = "approved",
    product_version: str = PRODUCT_VERSION,
    adapter_version: str = ADAPTER_VERSION,
    integration_version: int = 1,
    ruleset_id: str = RULESET.ruleset_id,
) -> FiscalApprovalEvent:
    return FiscalApprovalEvent(
        approval_event_id=f"fiscal-approval:{suffix}",
        integration_id="sif-provider",
        provider_product_version=product_version,
        adapter_version=adapter_version,
        integration_definition_version=integration_version,
        ruleset_id=ruleset_id,
        decision=decision,
        occurred_at=occurred_at,
        actor_ref="admin:founder",
        decision_ref=f"decision:fiscal:{suffix}",
    )


def _integrity(artifacts: ContentAddressedArtifactStore):
    return ContentAddressedArtifactIntegrityAdapter(artifacts)


def _project(
    *,
    fiscal: SqliteFiscalComplianceStore,
    integrations: SqliteAdminIntegrationStore,
    artifacts: ContentAddressedArtifactStore,
    as_of: datetime = NOW,
    ruleset: FiscalRuleSet = RULESET,
):
    return project_fiscal_compliance(
        store=fiscal,
        integration_store=integrations,
        ruleset=ruleset,
        grant=_grant(),
        generated_at=as_of,
        artifact_integrity=_integrity(artifacts),
    )


def _ready_fixture(tmp_path: Path):
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    _register_sif(integrations)
    service = FiscalComplianceService(fiscal, integrations)
    service.select_external_provider(grant=_grant(), selection=_selection())
    return fiscal, integrations, artifacts, service


def _record_documents(
    service: FiscalComplianceService,
    artifacts: ContentAddressedArtifactStore,
    **kwargs,
) -> None:
    for kind in DOC_KINDS:
        service.record_evidence(
            grant=_grant(),
            evidence=_evidence(kind, artifacts=artifacts, **kwargs),
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
            provider_product_version=PRODUCT_VERSION,
            adapter_version=ADAPTER_VERSION,
            integration_definition_version=1,
            ruleset_id=RULESET.ruleset_id,
        )


def test_no_provider_means_no_live_enablement_or_compliance_claim(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    projection = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert projection.state is FiscalEnablementState.NO_PROVIDER
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False
    assert projection.approval_effective is False
    assert projection.invalid_reasons == ("NO_PROVIDER",)


def test_selected_provider_requires_verified_documents_and_effective_approval(
    tmp_path: Path,
) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    service = FiscalComplianceService(fiscal, integrations)
    with pytest.raises(ValueError, match="not registered"):
        service.select_external_provider(grant=_grant(), selection=_selection())
    _register_sif(integrations)
    assert service.select_external_provider(grant=_grant(), selection=_selection()) is True

    service.record_evidence(
        grant=_grant(),
        evidence=_evidence(
            FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION,
            artifacts=artifacts,
        ),
    )
    incomplete = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert incomplete.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert incomplete.live_enablement_allowed is False
    assert FiscalEvidenceKind.NON_PRODUCTION_TEST in incomplete.missing_evidence

    _record_documents(service, artifacts, suffix="complete")
    ready = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert ready.state is FiscalEnablementState.EVIDENCE_READY
    assert ready.approval_effective is False
    assert ready.live_enablement_allowed is False
    assert ready.missing_evidence == ()

    service.record_approval(grant=_grant(), event=_approval())
    live = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert live.state is FiscalEnablementState.LIVE_ENABLEMENT_ALLOWED
    assert live.provider_version == PRODUCT_VERSION
    assert live.adapter_version == ADAPTER_VERSION
    assert live.integration_definition_version == 1
    assert live.approval_effective is True
    assert live.live_enablement_allowed is True
    assert live.compliance_claim_allowed is True


def test_future_evidence_cannot_enable_as_of_projection(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(
        service,
        artifacts,
        observed_at=NOW + timedelta(days=1),
        suffix="future",
    )
    service.record_approval(grant=_grant(), event=_approval())
    projection = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
        as_of=NOW,
    )
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert set(projection.missing_evidence) == set(DOC_KINDS)
    assert any(reason.startswith("FUTURE_EVIDENCE:") for reason in projection.invalid_reasons)
    assert projection.live_enablement_allowed is False


def test_missing_or_fingerprint_mismatched_artifact_cannot_count(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    service.record_evidence(
        grant=_grant(),
        evidence=_evidence(
            FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION,
            artifacts=artifacts,
            suffix="valid",
        ),
    )

    missing_digest = "b" * 64
    service.record_evidence(
        grant=_grant(),
        evidence=FiscalComplianceEvidence(
            evidence_id="fiscal-evidence:provider_technical_contract:missing",
            integration_id="sif-provider",
            kind=FiscalEvidenceKind.PROVIDER_TECHNICAL_CONTRACT,
            provider_product_version=PRODUCT_VERSION,
            adapter_version=ADAPTER_VERSION,
            integration_definition_version=1,
            ruleset_id=RULESET.ruleset_id,
            observed_at=NOW,
            source_ref="provider-evidence:technical:missing",
            artifact_ref=f"cas:sha256:{missing_digest}",
            artifact_fingerprint=f"sha256:{missing_digest}",
        ),
    )

    first_ref = artifacts.put_bytes(b"non-production-test-a")
    second_ref = artifacts.put_bytes(b"non-production-test-b")
    service.record_evidence(
        grant=_grant(),
        evidence=FiscalComplianceEvidence(
            evidence_id="fiscal-evidence:non_production_test:mismatch",
            integration_id="sif-provider",
            kind=FiscalEvidenceKind.NON_PRODUCTION_TEST,
            provider_product_version=PRODUCT_VERSION,
            adapter_version=ADAPTER_VERSION,
            integration_definition_version=1,
            ruleset_id=RULESET.ruleset_id,
            observed_at=NOW,
            source_ref="provider-evidence:test:mismatch",
            artifact_ref=first_ref,
            artifact_fingerprint="sha256:" + ContentAddressedArtifactStore.digest(second_ref),
        ),
    )
    service.record_approval(grant=_grant(), event=_approval())

    projection = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert FiscalEvidenceKind.PROVIDER_TECHNICAL_CONTRACT in projection.missing_evidence
    assert FiscalEvidenceKind.NON_PRODUCTION_TEST in projection.missing_evidence
    assert (
        sum(reason.startswith("ARTIFACT_UNVERIFIED:") for reason in projection.invalid_reasons) == 2
    )
    assert projection.live_enablement_allowed is False


def test_opaque_human_approval_evidence_does_not_authorize_live(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(service, artifacts)
    service.record_evidence(
        grant=_grant(),
        evidence=_evidence(
            FiscalEvidenceKind.HUMAN_APPROVAL,
            artifacts=artifacts,
            suffix="opaque-human-approval",
        ),
    )
    projection = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)
    assert projection.state is FiscalEnablementState.EVIDENCE_READY
    assert projection.approval_effective is False
    assert "HUMAN_APPROVAL_NOT_EFFECTIVE" in projection.invalid_reasons
    assert projection.live_enablement_allowed is False


def test_approval_is_effective_as_of_and_revocation_is_historical(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(service, artifacts)
    approved_at = NOW + timedelta(hours=1)
    revoked_at = NOW + timedelta(hours=3)
    service.record_approval(
        grant=_grant(),
        event=_approval(occurred_at=approved_at, suffix="approved-later"),
    )
    service.record_approval(
        grant=_grant(),
        event=_approval(
            decision=FiscalApprovalDecision.REVOKED,
            occurred_at=revoked_at,
            suffix="revoked",
        ),
    )
    before = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts, as_of=NOW)
    during = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
        as_of=NOW + timedelta(hours=2),
    )
    after = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
        as_of=NOW + timedelta(hours=4),
    )
    assert before.state is FiscalEnablementState.EVIDENCE_READY
    assert before.approval_effective is False
    assert during.state is FiscalEnablementState.LIVE_ENABLEMENT_ALLOWED
    assert during.approval_effective is True
    assert after.state is FiscalEnablementState.EVIDENCE_READY
    assert after.approval_effective is False


@pytest.mark.parametrize(
    ("selection_kwargs", "reason_prefix"),
    [
        (
            {"product_version": "provider-product-v2"},
            "PROVIDER_PRODUCT_VERSION_DRIFT:",
        ),
        (
            {"adapter_version": "axignal-fiscal-adapter-v2"},
            "ADAPTER_VERSION_DRIFT:",
        ),
        (
            {"integration_version": 2},
            "INTEGRATION_VERSION_DRIFT:",
        ),
        (
            {"ruleset_id": "es-sif-ruleset-v2"},
            "EVIDENCE_RULESET_DRIFT:",
        ),
    ],
)
def test_selected_binding_drift_requires_exact_re_evidence(
    tmp_path: Path,
    selection_kwargs: dict[str, object],
    reason_prefix: str,
) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    _register_sif(integrations)
    service = FiscalComplianceService(fiscal, integrations)
    service.select_external_provider(
        grant=_grant(),
        selection=_selection(**selection_kwargs),
    )
    _record_documents(service, artifacts, suffix="old")
    service.record_approval(
        grant=_grant(),
        event=_approval(**selection_kwargs),
    )

    projection = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)

    assert any(reason.startswith(reason_prefix) for reason in projection.invalid_reasons)
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False


def test_old_drift_evidence_does_not_poison_exact_re_evidenced_binding(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    service.record_evidence(
        grant=_grant(),
        evidence=_evidence(
            FiscalEvidenceKind.PROVIDER_RESPONSIBLE_DECLARATION,
            artifacts=artifacts,
            product_version="provider-product-v0",
            suffix="old-version",
        ),
    )
    _record_documents(service, artifacts, suffix="current")
    service.record_approval(grant=_grant(), event=_approval())

    projection = _project(fiscal=fiscal, integrations=integrations, artifacts=artifacts)

    assert any(
        reason.startswith("PROVIDER_PRODUCT_VERSION_DRIFT:")
        for reason in projection.invalid_reasons
    )
    assert projection.state is FiscalEnablementState.LIVE_ENABLEMENT_ALLOWED
    assert projection.live_enablement_allowed is True
    assert projection.compliance_claim_allowed is True


def test_registry_version_is_not_treated_as_provider_product_version(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(service, artifacts)
    service.record_approval(grant=_grant(), event=_approval())
    _register_sif(integrations, version=2)
    projection = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
        as_of=NOW + timedelta(minutes=2),
    )
    assert projection.provider_version == PRODUCT_VERSION
    assert projection.integration_definition_version == 1
    assert "INTEGRATION_DEFINITION_DRIFT" in projection.invalid_reasons
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert projection.live_enablement_allowed is False


def test_ruleset_drift_invalidates_complete_evidence_until_re_evidenced(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(service, artifacts)
    service.record_approval(grant=_grant(), event=_approval())
    changed_ruleset = replace(RULESET, ruleset_id="es-sif-verifactu-2026-10-04")
    projection = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
        ruleset=changed_ruleset,
    )
    assert "RULESET_DRIFT" in projection.invalid_reasons
    assert projection.state is FiscalEnablementState.EVIDENCE_INCOMPLETE
    assert projection.live_enablement_allowed is False


def test_fiscal_projection_requires_fiscal_read_scope(tmp_path: Path) -> None:
    fiscal = SqliteFiscalComplianceStore(tmp_path / "fiscal.sqlite3")
    integrations = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    with pytest.raises(PermissionError, match="admin:fiscal:read"):
        project_fiscal_compliance(
            store=fiscal,
            integration_store=integrations,
            ruleset=RULESET,
            grant=_grant(AdminRole.SUPPORT),
            generated_at=NOW,
            artifact_integrity=_integrity(artifacts),
        )


def test_runtime_starts_fiscal_compliance_fail_closed_without_provider(tmp_path: Path) -> None:
    from application.admin_fiscal_compliance import canonical_es_sif_ruleset
    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import _fiscal_compliance_projection, build_runtime

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
    projection = _fiscal_compliance_projection(runtime, grant=_grant(), now=NOW)
    assert projection.state is FiscalEnablementState.NO_PROVIDER
    assert projection.live_enablement_allowed is False
    assert projection.compliance_claim_allowed is False
    assert projection.ruleset == canonical_es_sif_ruleset()

    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-fiscal-summary" in html
    assert "Fiscal compliance gate" in html
    assert "bootstrap.fiscalCompliance" in javascript
    assert "Compliance claim" in javascript
    assert "fiscal.adapterVersion" in javascript
    assert "fiscal.integrationDefinitionVersion" in javascript
    assert "fiscal.approvalEffective" in javascript
    assert "fiscal.invalidReasons" in javascript


def test_approval_actor_and_binding_must_match_effective_context(tmp_path: Path) -> None:
    fiscal, integrations, artifacts, service = _ready_fixture(tmp_path)
    _record_documents(service, artifacts)

    forged_actor = replace(_approval(suffix="forged"), actor_ref="admin:other")
    with pytest.raises(ValueError, match="actor must match"):
        service.record_approval(grant=_grant(), event=forged_actor)

    service.record_approval(
        grant=_grant(),
        event=_approval(
            suffix="wrong-adapter",
            adapter_version="axignal-fiscal-adapter-v2",
        ),
    )
    projection = _project(
        fiscal=fiscal,
        integrations=integrations,
        artifacts=artifacts,
    )
    assert projection.state is FiscalEnablementState.EVIDENCE_READY
    assert projection.approval_effective is False
    assert projection.live_enablement_allowed is False
