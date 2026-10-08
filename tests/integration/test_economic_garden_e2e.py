"""Spec 059 end to end through the real subscriber composition.

Organization → observed capability and delivery → capability-specific reach → world
demand (TED) → Economic Relevance Gate → only in-garden demand reaches the subscriber as
POTENTIAL with an ExplanationTrace; a far-away energy shock becomes exposure, never an
opportunity; two Tenants on one Organization read the same evidence-derived garden.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.economic_reach.exposure import DriverEvent, DriverKind
from application.observation_intelligence.contracts import EvidenceRef, geo
from application.xeed_access.reader import TrustedRequestContext
from domain.identity import XeedId
from pipeline.admin_billing.subscriber_store import SqliteSubscriberBillingStore
from pipeline.observation_intelligence import UrllibTedTransport
from pipeline.observation_memory.sqlite_store import SqliteObservationMemory
from tests.economic_reach.harness import page
from tests.integration.test_subscriber_composition import (
    _build,
    _commit_verified_projection,
    _register_canonical_organization,
    _signup,
)
from tests.observation_intelligence.ted_fixture import FixtureTedTransport
from tools.runtime.observation_daily import build_economic_runtime
from tools.runtime.subscriber_observation import (
    ConfiguredSubscriberObservationPlanReader,
    load_observation_attention,
)

ORIGIN = "https://axignal.com"
ORGANIZATION = "org:registry:shared"
HOMEPAGE = (
    "Solartec Energía. Instalamos autoconsumo fotovoltaico en la Comunidad de Madrid. "
    "Nueva delegación en Valencia."
)


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


def _subscriber(facade: Any, tmp_path: Path, subject: str, ref: str) -> tuple[str, str]:
    token, tenant_id = _signup(facade, subject)
    billing = SqliteSubscriberBillingStore(tmp_path / "subscriber-billing.sqlite3")
    _commit_verified_projection(billing, tenant_id, now=datetime.now(UTC))
    added = facade.handle(
        "POST", "/subscriber/portfolio", {"Origin": ORIGIN, "Authorization": f"Bearer {token}"},
        {"action": "add", "requestRef": ref, "locator": "Shared Registry Example SLU"},
    )  # fmt: skip
    assert added.status == 200, added.body
    return token, str(added.body["focusId"])


def _reobserve(facade: Any, token: str, focus: str, ref: str) -> dict[str, Any]:
    run = facade.handle(
        "POST", "/subscriber/portfolio", {"Origin": ORIGIN, "Authorization": f"Bearer {token}"},
        {"action": "reobserve", "requestRef": ref, "focusId": focus},
    )  # fmt: skip
    assert run.body["observationState"] == "COMPLETED", run.body
    output = facade.handle(
        "GET", f"/subscriber/organizations/{focus}/output", {"Authorization": f"Bearer {token}"}
    )
    assert output.status == 200, output.body
    return dict(output.body["projection"]["cognition"])


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    _register_canonical_organization(tmp_path)
    plan = tmp_path / "subscriber-observation-plan.json"
    plan.write_text(
        '[{"organizationId":"org:registry:shared","markets":'
        '[{"jurisdiction":"EU/ES","roles":["PUBLIC_BUYERS"]}]}]',
        encoding="utf-8",
    )
    ted = FixtureTedTransport()
    monkeypatch.setattr(UrllibTedTransport, "post", lambda self, body: ted.post(body))
    facade = _build(tmp_path, observation_plan_path=plan)
    SqliteObservationMemory(tmp_path / "observation-memory.sqlite3").append(
        page(
            ORGANIZATION,
            "https://solartec.example/",
            HOMEPAGE,
            at=datetime.now(UTC) - timedelta(minutes=30),
        )
    )
    return facade, plan


def test_only_in_garden_demand_reaches_the_subscriber_with_its_explanation(
    tmp_path: Path, world
) -> None:  # type: ignore[no-untyped-def]
    facade, _plan = world
    token, focus = _subscriber(facade, tmp_path, "subject:garden", "add:garden")
    cognition = _reobserve(facade, token, focus, "reobserve:garden")

    garden = cognition["economicGarden"]
    (solar,) = [c for c in garden["capabilities"] if c["capabilityId"] == "solar-pv-installation"]
    assert solar["deliveryModes"] == ["CUSTOMER_SITE"]
    assert {p["geography"] for p in solar["operating"]} == {"EU/ES/ES3/ES30"}
    assert {p["geography"] for p in solar["expansion"]} == {"EU/ES/ES5/ES52/ES523"}
    assert "FUEL_AND_TRAVEL" in garden["exposureChannels"]

    opportunities = cognition["opportunities"]
    assert opportunities, cognition.get("relevanceFiltered")
    for item in opportunities:
        assert item["epistemic"] in {"POTENTIAL", "UNKNOWN"}  # never OBSERVED
        relevance = item["relevance"]
        assert relevance["scope"] == "OPERATING_REACH"
        assert relevance["relevantThrough"] == ["solar-pv-installation"]
        geo_judgments = [
            j for c in relevance["channels"] for j in c["judgments"]
            if j["family"] == "GEOGRAPHIC_ECONOMIC_REACH" and c["scope"] == "OPERATING_REACH"
        ]  # fmt: skip
        assert geo_judgments and geo_judgments[0]["reason"] == "WITHIN_STATED_REACH"
        assert geo_judgments[0]["evidence"][0]["excerpt"].startswith("Instalamos autoconsumo")
        assert "LOGISTICS_FEASIBILITY:solar-pv-installation" in relevance["unknown"]
        assert item["reachSourceIds"]  # declared dependency for continuity/T12
    assert "Getafe" in " ".join(str(item["buyer"]) for item in opportunities)
    # Córdoba (and other world demand outside Madrid) is real but not this garden's.
    assert cognition["relevanceFiltered"].get("OUTSIDE_XEED_REACH", 0) >= 1


def test_two_tenants_share_the_evidence_derived_garden(tmp_path: Path, world) -> None:  # type: ignore[no-untyped-def]
    facade, _plan = world
    token_a, focus_a = _subscriber(facade, tmp_path, "subject:garden-a", "add:a")
    token_b, focus_b = _subscriber(facade, tmp_path, "subject:garden-b", "add:b")
    a = _reobserve(facade, token_a, focus_a, "reobserve:a")
    b = _reobserve(facade, token_b, focus_b, "reobserve:b")
    assert focus_a != focus_b
    # Same canonical evidence, same garden; private attention never changed it.
    assert (
        a["economicGarden"]["operatingModelFingerprint"]
        == b["economicGarden"]["operatingModelFingerprint"]
    )
    assert [o["relevance"]["scope"] for o in a["opportunities"]] == [
        o["relevance"]["scope"] for o in b["opportunities"]
    ]


def test_far_away_energy_shock_is_exposure_not_opportunity(tmp_path: Path, world) -> None:  # type: ignore[no-untyped-def]
    facade, plan = world
    token, focus = _subscriber(facade, tmp_path, "subject:exposure", "add:exposure")
    member = facade.identity.authenticate(token)
    context = TrustedRequestContext(member.principal_id, member.tenant_id)
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    clock = _Clock(datetime.now(UTC) + timedelta(minutes=5))
    reader = ConfiguredSubscriberObservationPlanReader(
        economic=economic, clock=clock, attention=load_observation_attention(plan)
    )
    execution = reader.observation_plan_for(context, XeedId(focus))  # type: ignore[arg-type]
    assert execution is not None
    oil = DriverEvent(
        "driver:oil-shock", DriverKind.FUEL_PRICE,
        EvidenceRef("obs:news:oil", "https://news.example.com/oil", "Brent crude rises 30%", clock.now()),
        locus=geo("ME"),
    )  # fmt: skip
    economic.execute_observation_loop(
        context, XeedId(focus), observation_context=execution.observation_context,
        strategy=execution.strategy, adapters=execution.adapters, coverage=execution.coverage,
        learning=execution.learning, registry=execution.registry, drivers=(oil,),
    )  # fmt: skip
    cognition = economic.read(context, XeedId(focus), clock.now()).projection["cognition"]
    (exposure,) = cognition["exposure"]
    assert exposure["eventId"] == "driver:oil-shock" and exposure["isOpportunity"] is False
    assert {path["channel"] for path in exposure["transmission"]} == {"FUEL_AND_TRAVEL"}
    assert exposure["state"] == "POTENTIAL"
    assert all(item["id"] != "driver:oil-shock" for item in cognition["opportunities"])


def test_changed_reach_evidence_reuses_continuity_invalidation_and_t12(
    tmp_path: Path, world
) -> None:  # type: ignore[no-untyped-def]
    from pipeline.observation_runtime import SqliteObservationRuntimeStore

    facade, _plan = world
    token, focus = _subscriber(facade, tmp_path, "subject:reach-change", "add:reach-change")
    _reobserve(facade, token, focus, "reobserve:reach-change")
    member = facade.identity.authenticate(token)
    economic = build_economic_runtime(tmp_path, code_sha="test-code-sha")
    xeed = economic.authorize(
        TrustedRequestContext(member.principal_id, member.tenant_id), XeedId(focus)
    ).authorized_xeed.xeed
    checkpoint = economic.continuity.store.latest(xeed.tenant_id, xeed.id)
    homepage = "obs:obs:org:registry:shared:home:1"
    assert checkpoint is not None and homepage in {d.key for d in checkpoint.state.dependencies}
    # The website now states a different service area: the garden's support changed.
    SqliteObservationMemory(tmp_path / "observation-memory.sqlite3").append(
        page(ORGANIZATION, "https://solartec.example/",
             "Instalamos autoconsumo fotovoltaico en toda España.", at=datetime.now(UTC), n=2)
    )  # fmt: skip
    report = economic.continuity.reconcile(
        xeed.tenant_id, xeed.id, now=datetime.now(UTC) + timedelta(minutes=1),
        owe=SqliteObservationRuntimeStore(tmp_path / "observation-runtime.sqlite3"),
    )  # fmt: skip
    assert report.statuses[homepage] == "REPLACED"
    assert report.owed == ("demand",) and report.delivered == ("demand",)  # T12 recomputes
