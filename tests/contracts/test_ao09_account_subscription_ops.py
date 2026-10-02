from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_customer_accounts import AdminCustomerAccountService
from application.admin_shell import project_admin_shell
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_customer_accounts import AccountUserRole, FunnelStage
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _customer_operations_projection,
    _render_admin_shell,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 2, 6, 0, tzinfo=UTC)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="9" * 40,
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


def test_axigland_observation_does_not_create_customer_account(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.admin_observability.append_record(
        AdminEventEnvelope(
            record_id=AdminRecordId("axigland:organization:observed"),
            record_type="axigland.organization.observed",
            record_class=AdminRecordClass.ADMIN_METRIC_OBSERVATION,
            schema_version=1,
            producer="axigland-owner",
            owning_domain="organizations",
            recorded_at=NOW,
            outcome_state="OBSERVED",
            completeness=DataCompleteness.KNOWN,
            privacy_class=AdminPrivacyClass.INTERNAL,
            subject_refs=("organization-id:org:77",),
            provenance_refs=("source:public-record",),
        )
    )

    projection = _customer_operations_projection(runtime, grant=_grant(), now=NOW)

    assert projection.account_count == 0
    assert projection.total_entitled_xeeds == 0
    assert runtime.admin_customer_account_store.all_events() == ()


def test_runtime_customer_projection_keeps_mrr_unknown_until_ao11(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCustomerAccountService(runtime.admin_customer_account_store)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Agency Account",
        now=NOW,
        reason="signup",
    )
    service.add_user(
        grant=_grant(),
        account_id="account:1",
        user_id="user:owner",
        principal_id="principal:1",
        role=AccountUserRole.OWNER,
        now=NOW + timedelta(seconds=1),
        reason="owner",
    )
    service.activate_subscription(
        grant=_grant(),
        account_id="account:1",
        subscription_id="subscription:1",
        xeed_capacity=2,
        now=NOW + timedelta(seconds=2),
        reason="service activation",
    )
    with pytest.raises(ValueError, match="verified billing"):
        service.entitle_xeed(
            grant=_grant(),
            account_id="account:1",
            xeed_id="xeed:1",
            now=NOW + timedelta(seconds=3),
            reason="must wait for verified Stripe billing",
        )
    service.record_funnel_stage(
        grant=_grant(),
        account_id="account:1",
        stage=FunnelStage.FIRST_MAP_VIEWED,
        definition_version="behavior-v1",
        now=NOW + timedelta(seconds=4),
        reason="first map",
    )

    projection = _customer_operations_projection(runtime, grant=_grant(), now=NOW)

    assert projection.account_count == 1
    assert projection.active_account_count == 1
    assert projection.total_entitled_xeeds == 0
    assert projection.mrr_eur is None
    assert projection.payment_authority == "STRIPE_VERIFIED_EVENTS"
    assert projection.customers[0].mrr_eur is None
    assert projection.customers[0].pricing_hypothesis_monthly_eur == "14.90"


def test_customers_admin_bootstrap_has_account_projection_without_user_identity(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCustomerAccountService(runtime.admin_customer_account_store)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Agency Account",
        now=NOW,
        reason="signup",
    )
    service.add_user(
        grant=_grant(),
        account_id="account:1",
        user_id="private-user-id",
        principal_id="private-principal-id",
        role=AccountUserRole.OWNER,
        now=NOW + timedelta(seconds=1),
        reason="owner",
    )

    projection = _customer_operations_projection(runtime, grant=_grant(), now=NOW)
    shell = project_admin_shell(_grant(), requested_slug="customers-crm")
    rendered = _render_admin_shell(
        WEB_ROOT,
        shell,
        customer_operations=projection,
    ).decode("utf-8")

    assert '"customerOperations":' in rendered
    assert '"privacyClass":"PRIVATE_FIRST_PARTY_SERVICE"' in rendered
    assert '"paymentAuthority":"STRIPE_VERIFIED_EVENTS"' in rendered
    assert '"mrrEur":null' in rendered
    assert "private-user-id" not in rendered
    assert "private-principal-id" not in rendered
    assert "CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE" in rendered


def test_ao09_source_has_no_canonical_write_dependency() -> None:
    sources = (
        (ROOT / "domain" / "admin_customer_accounts" / "model.py").read_text(encoding="utf-8")
        + (ROOT / "application" / "admin_customer_accounts" / "service.py").read_text(
            encoding="utf-8"
        )
        + (ROOT / "pipeline" / "admin_customer_accounts" / "sqlite_store.py").read_text(
            encoding="utf-8"
        )
    )
    forbidden = (
        "domain.organizations",
        "domain.faxt",
        "domain.relationships",
        "domain.xignal",
        "EvidenceAdmission",
        "stripe",
    )
    for value in forbidden:
        assert value not in sources


def test_customers_ui_exposes_service_authority_boundary() -> None:
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")

    assert "AXIGNAL account / subscription authority" in js
    assert "CUSTOMER_ACCOUNT_STATE != ORGANIZATION_STATE" in js
    assert "Payment authority" in js
    assert "Pricing hypothesis" in js
    assert 'id="admin-customer-operations-summary"' in html
    assert 'id="admin-customer-account-list"' in html


def test_support_role_can_read_customer_projection_but_not_mutate_subscription(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminCustomerAccountService(runtime.admin_customer_account_store)
    service.signup(
        grant=_grant(),
        account_id="account:1",
        tenant_id="tenant:1",
        display_name="Account One",
        now=NOW,
        reason="signup",
    )

    projection = _customer_operations_projection(
        runtime,
        grant=_grant(AdminRole.SUPPORT),
        now=NOW,
    )
    assert projection.account_count == 1

    with pytest.raises(PermissionError, match="admin:customers:write"):
        service.activate_subscription(
            grant=_grant(AdminRole.SUPPORT),
            account_id="account:1",
            subscription_id="subscription:1",
            xeed_capacity=1,
            now=NOW + timedelta(seconds=1),
            reason="not authorized",
        )
