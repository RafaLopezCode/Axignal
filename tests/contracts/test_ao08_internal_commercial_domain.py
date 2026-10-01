from datetime import UTC, datetime
from pathlib import Path

from application.admin_commercial import AdminCommercialService
from application.admin_shell import project_admin_shell
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_commercial import CommercialOrigin, ConsentBasis
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _commercial_projection,
    _render_admin_shell,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 2, 0, 45, tzinfo=UTC)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="f" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
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


def test_runtime_commercial_projection_uses_private_owning_store(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCommercialService(runtime.admin_commercial_store)
    service.create_company(
        grant=_grant(),
        company_id="company:ao08",
        display_name="Acme",
        acquisition_source="frontier-brief",
        consent_basis=ConsentBasis.LEGITIMATE_INTEREST,
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="qualified prospect",
    )
    projection = _commercial_projection(runtime, grant=_grant(), now=NOW)

    assert projection.privacy_class == "PRIVATE_FIRST_PARTY"
    assert projection.company_count == 1
    assert projection.companies[0].company_id == "company:ao08"
    assert projection.pii_visible is False


def test_admin_commercial_bootstrap_excludes_contact_pii_and_preserves_boundary(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCommercialService(runtime.admin_commercial_store)
    service.create_company(
        grant=_grant(),
        company_id="company:ao08",
        display_name="Acme",
        acquisition_source="direct",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="self submitted",
    )
    service.create_contact(
        grant=_grant(),
        contact_id="contact:ao08",
        company_id="company:ao08",
        display_name="Private Contact",
        email="secret-contact@example.test",
        phone="+34000000000",
        acquisition_source="direct",
        consent_basis=ConsentBasis.CONSENT,
        origin=CommercialOrigin.USER_PROVIDED,
        now=NOW,
        reason="self submitted contact",
    )
    projection = _commercial_projection(runtime, grant=_grant(), now=NOW)
    shell = project_admin_shell(_grant(), requested_slug="customers-crm")
    rendered = _render_admin_shell(
        WEB_ROOT,
        shell,
        commercial=projection,
    ).decode("utf-8")

    assert '"commercial":' in rendered
    assert '"privacyClass":"PRIVATE_FIRST_PARTY"' in rendered
    assert '"piiVisible":false' in rendered
    assert "secret-contact@example.test" not in rendered
    assert "+34000000000" not in rendered
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in rendered


def test_support_projection_is_customer_safe_not_commercial_pipeline_projection(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCommercialService(runtime.admin_commercial_store)
    service.create_company(
        grant=_grant(),
        company_id="company:ao08",
        display_name="Acme",
        acquisition_source="direct",
        consent_basis=ConsentBasis.UNKNOWN,
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="prospect",
    )
    service.create_opportunity(
        grant=_grant(),
        opportunity_id="opp:secret",
        company_id="company:ao08",
        title="Private commercial opportunity",
        origin=CommercialOrigin.COMMERCIAL_CLAIM,
        now=NOW,
        reason="private pipeline",
    )

    projection = _commercial_projection(
        runtime,
        grant=_grant(AdminRole.SUPPORT),
        now=NOW,
    )
    assert projection.company_count == 1
    assert projection.opportunity_count == 0
    assert projection.audit_count == 0
    assert projection.origin_counts == ()


def test_ao08_ui_and_source_preserve_internal_crm_boundary() -> None:
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")
    source = (ROOT / "domain" / "admin_commercial" / "model.py").read_text(encoding="utf-8") + (
        ROOT / "application" / "admin_commercial" / "service.py"
    ).read_text(encoding="utf-8")

    assert "AXIGNAL first-party commercial state" in js
    assert "PII in projection" in js
    assert "Observed Organization ref" in js
    assert "navigation/deduplication only and grants no canonical write authority" in js
    assert 'id="admin-commercial-observatory"' in html

    forbidden_imports = (
        "domain.organizations",
        "domain.faxt",
        "domain.relationships",
        "domain.xignal",
        "domain.evidence.admission",
    )
    for forbidden in forbidden_imports:
        assert f"from {forbidden}" not in source
        assert f"import {forbidden}" not in source


def test_axigland_observation_cannot_silently_create_commercial_relationship(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.admin_observability.append_record(
        AdminEventEnvelope(
            record_id=AdminRecordId("axigland:org:observed"),
            record_type="axigland.organization.observed",
            record_class=AdminRecordClass.ADMIN_METRIC_OBSERVATION,
            schema_version=1,
            producer="axigland-owner",
            owning_domain="organizations",
            recorded_at=NOW,
            outcome_state="OBSERVED",
            completeness=DataCompleteness.KNOWN,
            privacy_class=AdminPrivacyClass.INTERNAL,
            subject_refs=("organization-id:org:canonical:77",),
            provenance_refs=("source:public-record",),
        )
    )

    projection = _commercial_projection(runtime, grant=_grant(), now=NOW)

    assert projection.prospect_count == 0
    assert projection.company_count == 0
    assert projection.contact_count == 0
    assert projection.opportunity_count == 0
    assert projection.deal_count == 0
    assert runtime.admin_commercial_store.audits() == ()
