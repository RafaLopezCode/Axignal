from datetime import UTC, datetime
from pathlib import Path

from application.admin_shell import project_admin_shell
from application.economic_discovery.learning_memory import (
    LearningCost,
    LearningEvent,
    LearningEventKind,
    LearningMechanism,
    LearningOutcome,
    LearningYield,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _render_admin_shell,
    _xeed_observatory_projection,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 1, 22, 0, tzinfo=UTC)


def _config(tmp_path: Path) -> RuntimeConfig:
    return RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="e" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )


def _founder_grant() -> AdminAuthorizationGrant:
    roles = frozenset({AdminRole.FOUNDER})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId("admin-session:ao05"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _learning_event() -> LearningEvent:
    return LearningEvent(
        event_id="learn:ao05:1",
        kind=LearningEventKind.DETERMINISTIC_EVALUATION,
        outcome=LearningOutcome.COMPLETED,
        occurred_at=NOW,
        subject_id="org:ao05",
        activity_ref="activity:ao05",
        policy_id="policy",
        policy_version="1",
        code_sha="e" * 40,
        mechanism=LearningMechanism.DETERMINISTIC,
        input_fingerprint="input:ao05",
        reason_code="AO05_TEST",
        xeed_id="xeed:ao05",
        cost=LearningCost(amount_microunits=250, currency="EUR"),
        yield_=LearningYield(
            observations_reused=2,
            observations_added=1,
            xignals_emitted=1,
            canonical_admissions=1,
        ),
    )


def test_runtime_observatory_uses_governed_learning_memory(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.learning_memory.append(_learning_event())

    projection = _xeed_observatory_projection(runtime, now=NOW)

    assert len(projection.xeeds) == 1
    xeed = projection.xeeds[0]
    assert xeed.xeed_id == "xeed:ao05"
    assert xeed.observations_reused == 2
    assert xeed.observations_added == 1
    assert xeed.known_costs_by_currency == (("EUR", 250),)
    assert xeed.shared_cost_reason == "SHARED_COST_ATTRIBUTION_UNAVAILABLE"


def test_xeed_admin_bootstrap_is_inspectable_and_secret_free(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.learning_memory.append(_learning_event())
    observatory = _xeed_observatory_projection(runtime, now=NOW)
    shell = project_admin_shell(_founder_grant(), requested_slug="xeeds")

    rendered = _render_admin_shell(
        WEB_ROOT,
        shell,
        xeed_observatory=observatory,
    ).decode("utf-8")

    assert '"xeedObservatory":' in rendered
    assert "learn:ao05:1" in rendered
    assert "SHARED_COST_ATTRIBUTION_UNAVAILABLE" in rendered
    assert "Bearer " not in rendered
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in rendered


def test_ao05_ui_distinguishes_reuse_growth_and_cost_scopes() -> None:
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")

    assert "Observations reused" in js
    assert "Observations added" in js
    assert "Canonical admissions" in js
    assert "Shared cost attribution" in js
    assert "Triggered cost attribution" in js
    assert "Diagnose this Xeed" in js
    assert "does not prove that zero Xeeds exist" in js
    assert 'id="admin-observatory"' in html


def test_active_observatory_hides_generic_domain_preview() -> None:
    css = (WEB_ROOT / "admin" / "admin.css").read_text(encoding="utf-8")
    assert ".admin-observatory[hidden]" in css
    assert ".admin-grid[hidden]" in css
