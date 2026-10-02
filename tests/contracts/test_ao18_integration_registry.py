from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_integrations.service import (
    AdminIntegrationService,
    IntegrationConnectionDenied,
    project_admin_integrations,
)
from application.admin_shell import project_admin_shell
from application.admin_shell.model import AdminShellRouteDenied
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminScope,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_governance import AdminGovernanceCommandTarget
from domain.admin_integrations import (
    CredentialLifecycle,
    CredentialState,
    IntegrationDefinition,
    IntegrationDirection,
    IntegrationEnvironment,
    IntegrationHealth,
    IntegrationHealthState,
)
from pipeline.admin_governance import SqliteAdminGovernanceAuditStore
from pipeline.admin_integrations import IntegrationRegistryConflict, SqliteAdminIntegrationStore
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import _render_admin_shell, build_runtime

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 2, 8, 0, tzinfo=UTC)


def _grant(
    role: AdminRole = AdminRole.TECHNICAL_SYSTEM,
    *,
    assurance: AdminAssurance = AdminAssurance.STEP_UP,
    scopes: frozenset[AdminScope] | None = None,
) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes if scopes is not None else scopes_for_roles(roles),
        assurance=assurance,
    )


def _definition(
    *,
    enabled: bool = True,
    state: CredentialState = CredentialState.CONFIGURED,
    reference: str | None = "secret://stripe/production/api-key",
    version: int = 1,
) -> IntegrationDefinition:
    return IntegrationDefinition(
        integration_id="stripe-billing",
        provider="Stripe",
        purpose="AXIGNAL first-party billing and payment lifecycle",
        owner="Finance and Engineering",
        environment=IntegrationEnvironment.PRODUCTION,
        enabled=enabled,
        credential=CredentialLifecycle(reference=reference, state=state),
        scopes=("customers.read", "subscriptions.read", "webhooks.write"),
        direction=IntegrationDirection.BIDIRECTIONAL,
        authority_boundary="Stripe owns payment/subscription status; AXIGNAL owns Xeed entitlement state.",
        webhook_capable=True,
        webhook_endpoint="https://axignal.com/webhooks/stripe",
        rate_limit_posture="Provider quota enforced; retry after provider guidance.",
        health_freshness_seconds=300,
        version=version,
    )


def _stores(tmp_path: Path):
    return (
        SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3"),
        SqliteAdminGovernanceAuditStore(tmp_path / "audit.sqlite3"),
    )


class _CredentialResolver:
    def __init__(self, available: bool = True) -> None:
        self.available = available

    def is_resolvable(self, *, reference: str, environment: IntegrationEnvironment) -> bool:
        assert reference.startswith("secret://")
        assert environment is IntegrationEnvironment.PRODUCTION
        return self.available


def test_secret_material_is_rejected_and_secret_reference_is_not_projected(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    with pytest.raises(ValueError, match="secret:// locator"):
        _definition(reference="Bearer fixture-only-credential")
    with pytest.raises(ValueError, match="no userinfo, query, or fragment"):
        replace(
            _definition(),
            webhook_endpoint="https://axignal.com/webhooks/stripe?mode=private",
        )

    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="AO-10 provider boundary preparation",
        occurred_at=NOW,
        definition=_definition(),
    )
    projection = project_admin_integrations(store=store, grant=_grant(), as_of=NOW)
    assert (
        projection.integrations[0].definition.credential.reference
        == "secret://stripe/production/api-key"
    )
    html = _render_admin_shell(
        WEB_ROOT,
        project_admin_shell(_grant(), requested_slug="integrations"),
        integrations=projection,
    ).decode("utf-8")
    assert "secret://stripe/production/api-key" not in html
    assert "https://axignal.com/webhooks/stripe" not in html
    assert '"webhookConfigured":true' in html
    assert "webhookEndpoint" not in html
    assert '"credentialConfigured":true' in html
    assert '"health":"UNKNOWN"' in html


def test_integration_change_requires_scope_and_step_up(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    with pytest.raises(PermissionError, match="admin:integrations:manage"):
        service.register(
            grant=_grant(AdminRole.SUPPORT),
            operation_id="register-denied",
            reason="support cannot manage providers",
            occurred_at=NOW,
            definition=_definition(),
        )
    with pytest.raises(PermissionError, match="step-up"):
        service.register(
            grant=_grant(assurance=AdminAssurance.PRIMARY),
            operation_id="register-primary",
            reason="primary assurance is insufficient",
            occurred_at=NOW,
            definition=_definition(),
        )
    assert store.all_definitions() == ()
    assert audit.all() == ()
    with pytest.raises(AdminShellRouteDenied):
        project_admin_shell(_grant(AdminRole.SUPPORT), requested_slug="integrations")


def test_definition_replay_is_idempotent_conflicting_replay_is_rejected(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    args = {
        "grant": _grant(),
        "operation_id": "register-stripe-v1",
        "reason": "AO-10 provider boundary preparation",
        "occurred_at": NOW,
        "definition": _definition(),
    }
    assert service.register(**args) is True
    assert service.register(**args) is False
    assert len(store.all_definitions()) == 1
    assert len(audit.all()) == 1
    assert audit.all()[0].target is AdminGovernanceCommandTarget.INTEGRATION
    assert audit.all()[0].required_scope == AdminScope.INTEGRATIONS_MANAGE.value

    with pytest.raises(IntegrationRegistryConflict, match="different content"):
        store.append_definition(
            operation_id="register-stripe-v1",
            occurred_at=NOW,
            definition=_definition(enabled=False),
        )


def test_definition_replay_repairs_audit_after_audit_store_failure(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)

    class FailFirstAppend:
        failed = False

        def append(self, record):
            if not self.failed:
                self.failed = True
                raise OSError("temporary audit store failure")
            return audit.append(record)

    service = AdminIntegrationService(store, FailFirstAppend())
    args = {
        "grant": _grant(),
        "operation_id": "register-stripe-v1",
        "reason": "AO-10 provider boundary preparation",
        "occurred_at": NOW,
        "definition": _definition(),
    }

    with pytest.raises(OSError, match="temporary audit store failure"):
        service.register(**args)
    assert len(store.all_definitions()) == 1
    assert audit.all() == ()

    assert service.register(**args) is False
    assert len(audit.all()) == 1


def test_registry_update_requires_next_version_and_survives_restart(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="register provider",
        occurred_at=NOW,
        definition=_definition(),
    )
    with pytest.raises(IntegrationRegistryConflict, match="version is out of sequence"):
        store.append_definition(
            operation_id="invalid-version",
            occurred_at=NOW + timedelta(seconds=1),
            definition=_definition(enabled=False),
        )

    service.register(
        grant=_grant(),
        operation_id="disable-stripe-v2",
        reason="disable until runtime verification",
        occurred_at=NOW + timedelta(seconds=1),
        definition=_definition(enabled=False, version=2),
    )
    reopened = SqliteAdminIntegrationStore(tmp_path / "integrations.sqlite3")
    assert reopened.all_definitions()[0].version == 2
    assert reopened.all_definitions()[0].enabled is False


def test_provider_work_fails_closed_for_unknown_disabled_expired_or_out_of_scope(
    tmp_path: Path,
) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="provider boundary preparation",
        occurred_at=NOW,
        definition=_definition(),
    )
    service.record_health(
        grant=_grant(),
        operation_id="stripe-health-ready",
        reason="record healthy provider check",
        occurred_at=NOW,
        observation=IntegrationHealth(
            integration_id="stripe-billing",
            state=IntegrationHealthState.HEALTHY,
            observed_at=NOW,
            last_success_at=NOW,
            source_ref="health-check:stripe:ready",
        ),
    )
    assert (
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW,
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        ).integration_id
        == "stripe-billing"
    )
    with pytest.raises(IntegrationConnectionDenied, match="environment"):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.STAGING,
            now=NOW,
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        )
    with pytest.raises(IntegrationConnectionDenied, match="scope"):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW,
            required_scopes=frozenset({"customers.write"}),
            credential_resolver=_CredentialResolver(),
        )
    with pytest.raises(IntegrationConnectionDenied, match="credential"):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW,
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(available=False),
        )
    with pytest.raises(IntegrationConnectionDenied, match="disabled"):
        service.register(
            grant=_grant(),
            operation_id="disable-stripe-v2",
            reason="disable connection",
            occurred_at=NOW + timedelta(seconds=1),
            definition=_definition(enabled=False, version=2),
        )
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW + timedelta(seconds=2),
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        )


@pytest.mark.parametrize(
    ("credential", "message"),
    [
        (CredentialLifecycle(None, CredentialState.MISSING), "credential is unavailable"),
        (
            CredentialLifecycle(
                "secret://stripe/production/api-key",
                CredentialState.REVOKED,
                revoked_at=NOW,
            ),
            "credential is unavailable",
        ),
        (
            CredentialLifecycle(
                "secret://stripe/production/api-key",
                CredentialState.CONFIGURED,
                expires_at=NOW - timedelta(seconds=1),
            ),
            "credential has expired",
        ),
    ],
)
def test_missing_revoked_and_expired_credentials_deny_connection(
    tmp_path: Path, credential: CredentialLifecycle, message: str
) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="credential lifecycle contract",
        occurred_at=NOW,
        definition=replace(_definition(), credential=credential),
    )
    with pytest.raises(IntegrationConnectionDenied, match=message):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW,
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        )


def test_secrets_in_audit_reason_are_rejected_before_persistence(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    with pytest.raises(ValueError, match="credential-like material"):
        service.register(
            grant=_grant(),
            operation_id="register-stripe-v1",
            reason="Bearer fixture-only-credential",
            occurred_at=NOW,
            definition=_definition(),
        )
    assert store.all_definitions() == ()
    assert audit.all() == ()


def test_health_observation_is_separate_from_definition_and_unknown_is_not_healthy(
    tmp_path: Path,
) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="registry definition",
        occurred_at=NOW,
        definition=_definition(),
    )
    projection = project_admin_integrations(store=store, grant=_grant(), as_of=NOW)
    assert projection.integrations[0].health is None
    with pytest.raises(IntegrationConnectionDenied, match="health is not verified healthy"):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW,
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        )

    observation = IntegrationHealth(
        integration_id="stripe-billing",
        state=IntegrationHealthState.FAILING,
        observed_at=NOW + timedelta(minutes=1),
        last_failure_at=NOW + timedelta(minutes=1),
        failure_category="AUTH_REJECTED",
        source_ref="health-check:stripe:1",
    )
    assert (
        service.record_health(
            grant=_grant(),
            operation_id="stripe-health-1",
            reason="record verified provider check",
            occurred_at=NOW + timedelta(minutes=1),
            observation=observation,
        )
        is True
    )
    view = project_admin_integrations(store=store, grant=_grant(), as_of=NOW + timedelta(minutes=2))
    assert view.integrations[0].definition.enabled is True
    assert view.integrations[0].health == observation


def test_health_freshness_derives_stale_and_denies_provider_work(tmp_path: Path) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="registry definition",
        occurred_at=NOW,
        definition=_definition(),
    )
    service.record_health(
        grant=_grant(),
        operation_id="stripe-health-ready",
        reason="record healthy provider check",
        occurred_at=NOW,
        observation=IntegrationHealth(
            integration_id="stripe-billing",
            state=IntegrationHealthState.HEALTHY,
            observed_at=NOW,
            last_success_at=NOW,
        ),
    )

    fresh = project_admin_integrations(
        store=store, grant=_grant(), as_of=NOW + timedelta(seconds=299)
    )
    stale = project_admin_integrations(
        store=store, grant=_grant(), as_of=NOW + timedelta(seconds=300)
    )
    assert fresh.integrations[0].health_state is IntegrationHealthState.HEALTHY
    assert stale.integrations[0].health_state is IntegrationHealthState.STALE
    assert stale.integrations[0].health is not None
    assert stale.integrations[0].health.state is IntegrationHealthState.HEALTHY

    with pytest.raises(IntegrationConnectionDenied, match="health observation is stale"):
        service.require_connection(
            integration_id="stripe-billing",
            environment=IntegrationEnvironment.PRODUCTION,
            now=NOW + timedelta(seconds=300),
            required_scopes=frozenset({"subscriptions.read"}),
            credential_resolver=_CredentialResolver(),
        )


def test_health_projection_is_as_of_and_ignores_late_older_observations(
    tmp_path: Path,
) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="registry definition",
        occurred_at=NOW,
        definition=_definition(),
    )

    newer_failure = IntegrationHealth(
        integration_id="stripe-billing",
        state=IntegrationHealthState.FAILING,
        observed_at=NOW + timedelta(seconds=60),
        last_failure_at=NOW + timedelta(seconds=60),
        failure_category="AUTH_REJECTED",
    )
    older_success = IntegrationHealth(
        integration_id="stripe-billing",
        state=IntegrationHealthState.HEALTHY,
        observed_at=NOW + timedelta(seconds=30),
        last_success_at=NOW + timedelta(seconds=30),
    )
    service.record_health(
        grant=_grant(),
        operation_id="stripe-health-newer",
        reason="record newer failing check",
        occurred_at=NOW + timedelta(seconds=60),
        observation=newer_failure,
    )
    service.record_health(
        grant=_grant(),
        operation_id="stripe-health-late-arrival",
        reason="record delayed older check",
        occurred_at=NOW + timedelta(seconds=90),
        observation=older_success,
    )

    historical = project_admin_integrations(
        store=store, grant=_grant(), as_of=NOW + timedelta(seconds=50)
    )
    current = project_admin_integrations(
        store=store, grant=_grant(), as_of=NOW + timedelta(seconds=120)
    )
    assert historical.integrations[0].health is None
    assert current.integrations[0].health == newer_failure
    assert current.integrations[0].health_state is IntegrationHealthState.FAILING


def test_health_observation_cannot_be_recorded_before_its_observed_time(
    tmp_path: Path,
) -> None:
    store, audit = _stores(tmp_path)
    service = AdminIntegrationService(store, audit)
    service.register(
        grant=_grant(),
        operation_id="register-stripe-v1",
        reason="registry definition",
        occurred_at=NOW,
        definition=_definition(),
    )
    future_observation = IntegrationHealth(
        integration_id="stripe-billing",
        state=IntegrationHealthState.HEALTHY,
        observed_at=NOW + timedelta(seconds=1),
        last_success_at=NOW + timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="cannot be later than its recorded time"):
        service.record_health(
            grant=_grant(),
            operation_id="stripe-health-future",
            reason="reject future-dated health",
            occurred_at=NOW,
            observation=future_observation,
        )
    assert store.latest_health("stripe-billing", as_of=NOW + timedelta(seconds=5)) is None


def test_admin_integration_route_is_closed_when_security_plane_is_absent(tmp_path: Path) -> None:
    config = RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="9" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )
    runtime = build_runtime(config)
    assert runtime.admin_access is None
    assert runtime.admin_integration_store.all_definitions() == ()


def test_admin_integrations_view_uses_safe_dom_and_existing_design_tokens() -> None:
    source = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    styles = (WEB_ROOT / "admin" / "admin.css").read_text(encoding="utf-8")
    assert "credentialConfigured" in source
    assert "authorityBoundary" in source
    assert "textContent" in source
    assert "innerHTML" not in source[source.index("const integrations = bootstrap.integrations") :]
    assert "var(--admin-private)" in styles
    assert "@media (max-width: 420px)" in styles
