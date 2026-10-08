"""Real HTTP gap → private ledger → governed T12 → continuity → independent AXENT read."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId
from pipeline.axent import SqliteResearchRequestLedger
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tests.axent.fixtures import ScriptedLuna
from tests.integration.test_autonomous_observation_brain import _Clock
from tests.integration.test_axent_grounded_e2e import _ask
from tests.integration.test_organization_admission_e2e import _pilot
from tests.integration.test_subscriber_composition import (
    _append_opportunity_capability_source,
    _build,
    _register_canonical_organization,
)
from tests.observation_runtime.harness import CountingTed
from tools.runtime.observation_daily import ObservationEnrollment, build_economic_runtime, run_once
from tools.runtime.observation_research import configured_research_access


def test_two_tenants_real_feedback_and_independent_next_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    _register_canonical_organization(tmp_path)
    plan = tmp_path / "attention.json"
    plan.write_text(
        '[{"organizationId":"org:registry:shared","markets":[{"jurisdiction":"EU/ES","roles":["PUBLIC_BUYERS"]}]}]',
        encoding="utf-8",
    )
    facade = _build(tmp_path, pilot=True)
    tenants = []
    for subject in ("feedback:a", "feedback:b"):
        token, tenant = _pilot(facade, tmp_path, subject)
        added = facade.handle(
            "POST",
            "/subscriber/portfolio",
            {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
            {"action": "add", "requestRef": subject, "locator": "Shared Registry Example SLU"},
        )
        assert added.status == 200
        member = facade.identity.authenticate(token)
        tenants.append(
            (
                token,
                tenant,
                str(added.body["focusId"]),
                TrustedRequestContext(member.principal_id, member.tenant_id),
            )
        )
    _append_opportunity_capability_source(tmp_path)
    clock = _Clock(datetime.now(UTC))
    facade.axent.service.clock = clock.now
    luna = ScriptedLuna()
    facade.axent.service.reasoner = luna
    ledger = SqliteResearchRequestLedger(
        tmp_path / "axent-research.sqlite3", runtime_path=tmp_path / "observation-runtime.sqlite3"
    )
    for token, tenant, focus, _ in tenants:
        initial = _ask(facade, token, focus, "¿Qué oportunidades hay?")
        assert initial["grounding"]["route"] == "ABSTAINED"
        assert initial["grounding"]["research"]
        duplicate = _ask(facade, token, focus, "¿Qué oportunidades hay?")
        assert (
            duplicate["grounding"]["research"]["requestId"]
            == initial["grounding"]["research"]["requestId"]
        )
        assert len(ledger.states(tenant_id=tenant, xeed_id=focus)) == 1
    assert not luna.requests
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_PILOT_ENABLED", "true")
    economic = build_economic_runtime(tmp_path, code_sha="feedback-test")
    ted = CountingTed()
    store = SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3")
    kwargs = dict(
        economic=economic,
        store=store,
        clock=clock,
        attention_file=plan,
        enrollment=tuple(
            ObservationEnrollment(context, XeedId(focus)) for _, _, focus, context in tenants
        ),
        source_ports={"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)},
        research_ledger=ledger,
        research_access=configured_research_access(tmp_path, clock),
    )
    report, brain = run_once(**kwargs)
    assert report.shared_acquisitions and report.scheduler_model_calls == 0
    assert len(ted.bodies) == report.requests  # continuity and Brain replay do not refetch
    assert (
        len({item[0] for item in brain.outcomes if item[3].startswith("PROJECTION_RECOMPUTED")})
        == 2
    )
    assert not luna.requests, "completion never auto-queries AXENT"
    for token, tenant, focus, _context in tenants:
        lifecycle = ledger.states(tenant_id=tenant, xeed_id=focus)[0]
        assert lifecycle.status == "OBSERVATION_COMPLETED" and lifecycle.attempts == 1
        assert lifecycle.evidence_keys and lifecycle.work_ids
        assert economic.continuity.store.latest(tenant, focus)
        assert (
            ledger.states(
                tenant_id=tenants[1][1] if tenant == tenants[0][1] else tenants[0][1], xeed_id=focus
            )
            == ()
        )
        later = _ask(facade, token, focus, "¿Qué oportunidades hay?")
        assert later["grounding"]["route"] == "MODEL" and later["grounding"]["claims"]
        assert all(c["epistemic"] == "POTENTIAL" for c in later["grounding"]["claims"])
        cached = _ask(facade, token, focus, "¿Qué oportunidades hay?")
        assert cached["grounding"]["modelCalls"] == 0
    assert len(luna.requests) == 2, "each tenant has an independent authorized cache"
    calls = len(ted.bodies)
    run_once(**kwargs)
    assert len(ted.bodies) == calls
