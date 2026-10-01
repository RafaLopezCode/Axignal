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
from domain.admin_observability import (
    AdminEventEnvelope,
    AdminPrivacyClass,
    AdminRecordClass,
    AdminRecordId,
    DataCompleteness,
)
from tools.runtime.config import RuntimeConfig
from tools.runtime.service import (
    _brain_observatory_projection,
    _render_admin_shell,
    build_runtime,
)

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
NOW = datetime(2026, 10, 1, 22, 30, tzinfo=UTC)


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
        session_id=AdminSessionId("admin-session:ao06"),
        principal_id=AdminPrincipalId("admin:founder"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def _provider_event() -> LearningEvent:
    return LearningEvent(
        event_id="learn:ao06:jev-like",
        kind=LearningEventKind.STRUCTURED_EVALUATION,
        outcome=LearningOutcome.PARTIAL,
        occurred_at=NOW,
        subject_id="org:ao06",
        activity_ref="job:ao06",
        policy_id="decision-contract",
        policy_version="3",
        code_sha="f" * 40,
        mechanism=LearningMechanism.STRUCTURED_EVALUATOR,
        input_fingerprint="state:ao06",
        reason_code="STRUCTURED_RESULT",
        xeed_id="xeed:ao06",
        provider="jev-like",
        provider_version="model-v7",
        cost=LearningCost(
            amount_microunits=450,
            currency="EUR",
            latency_ms=320,
            input_units=1200,
            output_units=80,
        ),
        yield_=LearningYield(semantic_judgments_produced=1),
    )


def _budget_record() -> AdminEventEnvelope:
    return AdminEventEnvelope(
        record_id=AdminRecordId("brain-budget:ao06"),
        record_type="brain.budget",
        record_class=AdminRecordClass.OPERATIONAL_EVENT,
        schema_version=1,
        producer="research-owner",
        owning_domain="research",
        recorded_at=NOW,
        outcome_state="WITHIN_BUDGET",
        completeness=DataCompleteness.KNOWN,
        privacy_class=AdminPrivacyClass.INTERNAL,
        provenance_refs=("policy:budget-v1",),
    )


def test_runtime_brain_observatory_uses_learning_and_admin_evidence(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.learning_memory.append(_provider_event())
    runtime.admin_observability.append_record(_budget_record())

    projection = _brain_observatory_projection(runtime, now=NOW)

    assert projection.structured_evaluator_event_count == 1
    assert projection.provider_attributed_event_count == 1
    assert projection.control.budget_state == "WITHIN_BUDGET"
    provider = projection.provider_slices[0]
    assert provider.provider == "jev-like"
    assert provider.average_latency_ms == 320
    assert provider.known_costs_by_currency == (("EUR", 450),)
    assert provider.comparison_key == "STRUCTURED_EVALUATION|decision-contract|3"


def test_brain_admin_bootstrap_is_inspectable_provider_neutral_and_secret_free(
    tmp_path: Path,
) -> None:
    runtime = build_runtime(_config(tmp_path))
    runtime.learning_memory.append(_provider_event())
    observatory = _brain_observatory_projection(runtime, now=NOW)
    shell = project_admin_shell(_founder_grant(), requested_slug="axent-brain")

    rendered = _render_admin_shell(
        WEB_ROOT,
        shell,
        brain_observatory=observatory,
    ).decode("utf-8")

    assert '"brainObservatory":' in rendered
    assert "learn:ao06:jev-like" in rendered
    assert "STRUCTURED_EVALUATION|decision-contract|3" in rendered
    assert "Provider/model identity is mutable execution policy" in rendered
    assert "Bearer " not in rendered
    assert "ADMIN_PRIVATE_OPERATIONS != AXIGLAND_CANONICAL_TRUTH" in rendered


def test_ao06_ui_exposes_failure_abstention_frontier_and_compatible_comparison() -> None:
    js = (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "admin" / "index.html").read_text(encoding="utf-8")

    assert "Structured evaluator" in js
    assert "Adaptive research" in js
    assert "Stop reason" in js
    assert "No progress" in js
    assert "Retry" in js
    assert "Abstention" in js
    assert "Knowledge Frontier" in js
    assert "Unresolved gap" in js
    assert "Comparable only with matching key" in js
    assert "Useful-output events" in js
    assert 'id="admin-brain-observatory"' in html


def test_ao06_does_not_introduce_global_provider_score_or_rank() -> None:
    source = (
        (ROOT / "application" / "admin_brain_observatory" / "projector.py").read_text(
            encoding="utf-8"
        )
        + (WEB_ROOT / "admin" / "admin.js").read_text(encoding="utf-8")
    ).lower()
    assert "provider score" not in source
    assert "provider rank" not in source
    assert "winner" not in source
