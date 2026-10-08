"""Daily autonomous observation through the real subscriber Brain, end to end.

fractal daily tick → real acquisition (TED adapter) → new evidence and POTENTIAL
candidate → MATERIAL_CHANGE → canonical reobservation entry (plan reader →
SubscriberEconomicRuntime.execute_observation_loop, membership re-checked) →
governed opportunity projection → subscriber reading.
The downstream replays the runtime's own retrievals: no second Brain, no refetch.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest

from application.observation_runtime import TickReport
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import PrincipalId, XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.observation_intelligence import TedSearchAdapter
from pipeline.observation_runtime import SqliteObservationRuntimeStore
from tests.integration.test_organization_admission_e2e import _pilot
from tests.integration.test_subscriber_composition import (
    _append_opportunity_capability_source,
    _build,
    _commit_verified_projection,
    _register_canonical_organization,
)
from tests.observation_intelligence.scenarios import AS_OF
from tests.observation_runtime.harness import NEW_CALL, CountingTed
from tools.runtime.observation_daily import (
    ObservationEnrollment,
    SubscriberBrainRecomputation,
    build_economic_runtime,
    run_once,
    run_scheduled_tick,
)

Opportunities = list[dict[str, object]]


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def _opportunities(wire: dict[str, object]) -> Opportunities:
    cognition = cast(dict[str, object], cast(dict[str, object], wire["projection"])["cognition"])
    return cast(Opportunities, cognition["opportunities"])


@pytest.mark.parametrize("scheduled", [False, True])
def test_daily_tick_reaches_the_real_subscriber_brain_and_changes_the_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scheduled: bool,
) -> None:
    _register_canonical_organization(tmp_path)
    attention_file = tmp_path / "subscriber-observation-plan.json"
    attention_file.write_text(
        '[{"organizationId":"org:registry:shared","markets":'
        '[{"jurisdiction":"EU/ES","roles":["PUBLIC_BUYERS"]}]}]',
        encoding="utf-8",
    )
    # The production scheduler now requires persistent entitlement, not just a
    # manually supplied membership context. Use the real pilot redemption flow.
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_ENABLED", "true")
    monkeypatch.setenv("AXIGNAL_SUBSCRIBER_PILOT_ENABLED", "true")
    facade = _build(tmp_path, pilot=True)
    token, tenant_id = _pilot(facade, tmp_path, "subject:autonomous")
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(billing, tenant_id, now=datetime.now(AS_OF.tzinfo))
    added = facade.handle(
        "POST",
        "/subscriber/portfolio",
        {"Origin": "https://axignal.com", "Authorization": f"Bearer {token}"},
        {"action": "add", "requestRef": "add:autonomous", "locator": "Shared Registry Example SLU"},
    )
    assert added.status == 200
    focus_id = XeedId(str(added.body["focusId"]))
    _append_opportunity_capability_source(tmp_path)
    member = facade.identity.authenticate(token)
    enrolled = ObservationEnrollment(
        TrustedRequestContext(member.principal_id, member.tenant_id), focus_id
    )
    # Enrollment is not authority: a principal without membership observes nothing.
    intruder = ObservationEnrollment(
        TrustedRequestContext(PrincipalId("principal:intruder"), member.tenant_id),
        XeedId("xeed:not-enrolled"),
    )

    ted = CountingTed()
    clock = _Clock(AS_OF)
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    store_path = tmp_path / "observation-runtime.sqlite3"

    def read() -> Opportunities:
        """What /subscriber/organizations/{focus}/output serves, at the controlled time."""
        return _opportunities(economic.read(enrolled.context, focus_id, clock.now()).to_wire())

    def tick(day: int) -> tuple[TickReport, SubscriberBrainRecomputation]:
        clock.current = AS_OF + timedelta(days=day - 1)
        if scheduled:
            from tools.runtime import observation_daily

            results: list[tuple[TickReport, SubscriberBrainRecomputation]] = []

            def capture(**kwargs: Any) -> tuple[TickReport, SubscriberBrainRecomputation]:
                result = run_once(**kwargs)
                results.append(result)
                return result

            monkeypatch.setattr(observation_daily, "run_once", capture)
            summary = run_scheduled_tick(
                root=tmp_path,
                clock=clock,
                code_sha="test-code-sha",
                economic=economic,
                attention_file=attention_file,
                enrollment=(enrolled, intruder),
                source_ports={"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)},
            )
            assert summary["state"] == "COMPLETED"
            status = SqliteObservationRuntimeStore.inspect(store_path, now=clock.now())
            assert status["last_invocation"] is not None and status["lease_status"] == "COMPLETED"
            return results[0]
        return run_once(
            economic=economic,
            store=SqliteObservationRuntimeStore(store_path),
            clock=clock,
            attention_file=attention_file,
            enrollment=(enrolled, intruder),
            source_ports={"ted-search-v3": TedSearchAdapter(ted, clock=clock.now)},
        )

    assert read() == []

    # DAY 1: the first autonomous observation reaches the Brain and the reading.
    d1, brain1 = tick(1)
    assert d1.scheduler_model_calls == 0 and d1.candidates_total >= 1
    assert {xeed for xeed, *_ in brain1.outcomes} == {focus_id}, "only the enrolled member"
    published = [o for o in brain1.outcomes if o[3].startswith("PROJECTION_RECOMPUTED:")]
    assert len(published) == 1 and published[0][1:3] == ("demand", "MATERIAL_CHANGE")
    assert len(ted.bodies) == d1.requests, "the Brain replays retrievals, it never refetches"
    # Without an adopted, rights-documented adapter a family stays blocked and UNKNOWN.
    reasons = dict(d1.blocked).values()
    assert any(r.startswith("NO_ADAPTER:official-public-website") for r in reasons)
    assert any("PUBLIC_REVIEWS_AND_MENTIONS" in r for r in reasons)
    day1 = read()
    assert day1 and all(o["epistemic"] == "POTENTIAL" for o in day1)
    assert all(cast(dict[str, object], o["capability"])["sourceId"] for o in day1)
    # The fractal regional follow-up is replayed as well: demand reached via revealed codes.
    assert any(o["market"] == "EU/ES/ES5/ES52" for o in day1)
    # The real HTTP facade serves the same governed reading (its clock is past day 1).
    output = facade.handle(
        "GET", f"/subscriber/organizations/{focus_id}/output", {"Authorization": f"Bearer {token}"}
    )
    assert output.status == 200
    assert {o["id"] for o in _opportunities(output.body)} == {o["id"] for o in day1}
    ids_day1 = {o["id"] for o in day1}

    # DAY 2: nothing new; selective recomputation leaves the Brain untouched.
    d2, brain2 = tick(2)
    assert d2.candidates_new == 0
    assert not any(o[3].startswith("PROJECTION_RECOMPUTED") for o in brain2.outcomes)
    assert {o["id"] for o in read()} == ids_day1

    # New public demand appears; the next due tick finds it and the reading changes.
    ted.publish(NEW_CALL)
    found_on = None
    spent = d1.requests + d2.requests
    for day in range(3, 8):
        report, brain = tick(day)
        spent += report.requests
        assert len(ted.bodies) == spent, "recomputation adds no source request"
        if report.candidates_new:
            found_on = day
            assert any(o[3].startswith("PROJECTION_RECOMPUTED:") for o in brain.outcomes)
            break
    assert found_on is not None and found_on <= 6
    after = read()
    new = [o for o in after if o["id"] not in ids_day1]
    assert len(new) == 1
    assert new[0]["title"] == "Instalación fotovoltaica en mercados municipales"
    assert new[0]["epistemic"] == "POTENTIAL" and new[0]["unknown"]
    assert ids_day1 <= {o["id"] for o in after}, "earlier POTENTIAL candidates are kept"

    # A restarted process reads the same governed projection.
    restarted = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    persisted = _opportunities(restarted.read(enrolled.context, focus_id, clock.now()).to_wire())
    assert {o["id"] for o in persisted} == {o["id"] for o in after}
