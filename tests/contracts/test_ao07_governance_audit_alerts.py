from datetime import UTC, datetime
from pathlib import Path

from application.admin_governance import AdminGovernanceService, BoundedCommandResult
from application.admin_shell import project_admin_shell
from application.economic_discovery.policy_governance import ActivePolicyRef
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_governance import AdminGovernanceCommandTarget, GovernancePolicyFamily
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _governance_projection,
    _render_admin_shell,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 1, 23, 15, tzinfo=UTC)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="f" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )


def _founder_grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("admin-session:ao07"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def test_runtime_governance_projection_has_all_policy_and_alert_classes(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.governance_policy_store.seed_active(
        ActivePolicyRef(
            policy_family=GovernancePolicyFamily.EXECUTION_BUDGET.value,
            policy_id="prime-execution-budget",
            policy_version="1",
            code_sha="f" * 40,
        )
    )
    projection = _governance_projection(runtime, now=NOW)

    assert len(projection.policies) == 7
    assert len(projection.alerts) == 8
    assert projection.unsupported_canonical_write_target_count == 0
    assert (
        next(
            item
            for item in projection.policies
            if item.family is GovernancePolicyFamily.EXECUTION_BUDGET
        ).policy_version
        == "1"
    )


def test_runtime_governance_bootstrap_is_inspectable_and_secret_free(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    service = AdminGovernanceService(runtime.governance_audit_store)
    service.execute(
        grant=_founder_grant(),
        command_id="command:ao07:policy",
        target=AdminGovernanceCommandTarget.POLICY_GOVERNANCE,
        action="PROMOTE_POLICY",
        reason="governed evidence approved",
        occurred_at=NOW,
        handler=lambda: BoundedCommandResult("POLICY_PROMOTED", "policy:v1", "policy:v2"),
        approval_ref="approval:ao07",
    )
    governance = _governance_projection(runtime, now=NOW)
    shell = project_admin_shell(_founder_grant(), requested_slug="governance")
    rendered = _render_admin_shell(
        WEB_ROOT,
        shell,
        governance=governance,
    ).decode("utf-8")

    assert '"governance":' in rendered
    assert '"unsupportedCanonicalWriteTargetCount":0' in rendered
    assert "command:ao07:policy" in rendered
    assert "governed evidence approved" in rendered
    assert "policy:v1" in rendered
    assert "policy:v2" in rendered
    assert "Bearer " not in rendered
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in rendered


def test_ao07_ui_exposes_registry_changes_alerts_and_audit() -> None:
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")

    required = (
        "Versioned policy registry",
        "Governed policy changes",
        "Unsupported canonical write targets",
        "Governed alerts",
        "Privileged action audit",
        "Effective version",
        "Inspect authorization and reason",
    )
    for marker in required:
        assert marker in js
    assert 'id="admin-governance-observatory"' in html


def test_ao07_command_boundary_rejects_canonical_targets_before_owner_handler() -> None:
    source = (ROOT / "application" / "admin_governance" / "service.py").read_text(encoding="utf-8")
    assert "UNSUPPORTED_CANONICAL_WRITE_TARGET" in source
    assert "if target not in _ALLOWED_TARGETS" in source
    assert "handler()" in source
    assert source.index("if target not in _ALLOWED_TARGETS") < source.index("handler()")
    assert "sqlite3" not in source
