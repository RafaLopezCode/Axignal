"""Spec 063 end to end through the real subscriber composition (controlled network).

Six very different businesses: different business must not mean a broken pipeline, and
no useful opportunity must still produce a useful observation or a grounded UNKNOWN.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from application.organization_admission.service import organization_id_for
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.first_observation.harness import (
    BAKERY_FR,
    FORBIDDEN,
    KNOWN,
    PLACEHOLDER,
    SAAS_IE,
    SCHOOL_AR,
    SOLAR_ES,
    World,
    build,
    codes,
    discoveries,
    runtime,
)
from tests.integration.test_organization_admission_e2e import _add, _headers, _pilot, _portfolio
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei

SOLARTEC = lei("SOLARTEC0000000001")


def _attend(facade: Any, tmp_path: Path, subject: str, locator: str) -> tuple[str, dict[str, Any]]:
    token, _tenant = _pilot(facade, tmp_path, subject)
    added = _add(facade, token, f"add:{subject}", locator)
    assert added.status == 200, added.body
    return token, dict(added.body)


def _view(facade: Any, token: str, target: str) -> dict[str, Any]:
    read = facade.handle("GET", f"/subscriber/organizations/{target}/output", _headers(token))
    assert read.status == 200, read.body
    return dict(read.body["firstObservation"])


def _pending_id(facade: Any, token: str) -> str:
    (item,) = [i for i in _portfolio(facade, token) if i["state"] == "IDENTITY_PENDING"]
    return str(item["focusId"])


def _ledger(view: dict[str, Any], key: str) -> Any:
    return view["ledger"][key]["value"]


def test_solar_installer_in_spain_reaches_routed_public_demand(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, added = _attend(facade, tmp_path, "subject:solar", SOLAR_ES)
    # The request validated and enqueued only: nothing fetched inside it.
    assert (added["state"], added["observationState"]) == ("IDENTITY_PENDING", "QUEUED")
    assert world.sites.requests == []
    pending = _pending_id(facade, token)
    assert _portfolio(facade, token)[0]["observation"]["state"] == "QUEUED"

    assert runtime(facade).drain() == 1
    view = _view(facade, token, pending)
    assert view["state"] == "FIRST_PROOF_READY" and view["firstProofReady"] is True
    (activity,) = discoveries(view, "ACTIVITY")
    assert activity["code"] == "solar-pv-installation"
    assert activity["epistemicState"] == "POTENTIAL" and activity["detail"]["method"] == "LEXICON"
    assert activity["excerpt"] and activity["sourceUrl"] == SOLAR_ES
    (location,) = discoveries(view, "DECLARED_LOCATION")
    assert location["epistemicState"] == "DECLARED" and "ES" in location["statement"]
    (demand,) = discoveries(view, "DEMAND")
    assert demand["epistemicState"] == "POTENTIAL"
    assert demand["sourceUrl"].startswith("https://ted.europa.eu/")
    # Identity is never invented: the legal name the site declares is only a hint.
    hint = next(d for d in discoveries(view, "IDENTITY_HINT") if d["code"] == "LEGAL_NAME_DECLARED")
    assert hint["detail"]["admitted"] is False
    assert "IDENTITY_NOT_VERIFIED" in codes(view)
    assert view["attentionScopes"][0]["jurisdiction"] == "EU/ES"
    # Cheapest first: robots + homepage, no extra page (activity and place evidenced),
    # no semantic call (deterministic answer suffices), demand from the routed source.
    assert world.sites.requests == [SOLAR_ES.rstrip("/") + "/robots.txt", SOLAR_ES]
    assert world.judge.calls == []
    assert _ledger(view, "httpRequests") == 2 and _ledger(view, "lunaCalls") == 0
    assert "SKIPPED:SEMANTIC:DETERMINISTIC_SUFFICIENT" in view["ledger"]["decisions"]
    assert view["target"] == {
        "kind": "PENDING",
        "website": SOLAR_ES,
        "name": None,
        "identityLink": "IDENTITY_PENDING",
    }
    assert view["authority"] == "OPERATIONAL_NOT_CANONICAL"
    with sqlite3.connect(tmp_path / "canonical-organizations.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM canonical_legal_identities").fetchone()[0] == 0


def test_language_school_in_arkansas_is_understood_and_gets_a_grounded_source_gap(
    tmp_path: Path,
) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:school", SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "FIRST_PROOF_READY"
    (activity,) = discoveries(view, "ACTIVITY")
    assert (activity["code"], activity["detail"]["method"]) == ("isic-P", "SEMANTIC_JUDGMENT")
    assert activity["detail"]["model"] == "jev-1.13.0" and activity["detail"]["confidence"] > 0.6
    assert "NAICS:61" in activity["detail"]["routingCodes"]
    (place,) = [
        d for d in discoveries(view, "DECLARED_LOCATION") if d["code"] == "LOCATION_STATED_IN_TEXT"
    ]
    assert place["statement"] == "US/US-AR" and place["epistemicState"] == "POTENTIAL"
    assert "Arkansas" in place["excerpt"]
    # Not TED (EU only) and no invented US source: an explicit, non-negative gap.
    gaps = [d["code"] for d in view["discoveries"] if d["code"].startswith("NO_GOVERNED")]
    assert gaps == ["NO_GOVERNED_DEMAND_SOURCE:US/US-AR"]  # one per market, not per question
    assert world.ted.queries == []
    # Extra pages were read only because activity and location were UNKNOWN.
    assert SCHOOL_AR + "courses" in world.sites.requests
    assert SCHOOL_AR + "blog/2024/tips" not in world.sites.requests
    assert any(d.startswith("FETCHED:ACTIVITY") for d in view["ledger"]["decisions"])
    # One Jev batch, many questions; never Luna.
    assert len(world.judge.calls) == 1 and len(world.judge.calls[0].questions) >= 5
    assert _ledger(view, "jevCalls") == 1 and _ledger(view, "lunaCalls") == 0
    assert view["ledger"]["jevUsd"]["basis"] == "VENDOR_PUBLISHED"


def test_semantic_layer_off_keeps_a_deterministic_honest_first_observation(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world, semantic=False)
    token, _ = _attend(facade, tmp_path, "subject:school-off", SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "NOT_ENOUGH_CAPABILITY_EVIDENCE"
    assert view["firstProofReady"] is False
    assert {"PUBLIC_WEBSITE_OBSERVED", "LANGUAGES_PUBLISHED", "ACTIVITY_NOT_ESTABLISHED"} <= codes(
        view
    )
    assert "SKIPPED:SEMANTIC:LAYER_DISABLED" in view["ledger"]["decisions"]
    assert world.judge.calls == [] and world.ted.queries == []


def test_global_saas_and_local_bakery_are_classified_without_a_model(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    saas_token, _ = _attend(facade, tmp_path, "subject:saas", SAAS_IE)
    bakery_token, _ = _attend(facade, tmp_path, "subject:bakery", BAKERY_FR)
    assert runtime(facade).drain() == 2
    saas = _view(facade, saas_token, _pending_id(facade, saas_token))
    bakery = _view(facade, bakery_token, _pending_id(facade, bakery_token))
    assert [d["code"] for d in discoveries(saas, "ACTIVITY")] == ["isic-J"]
    assert [d["code"] for d in discoveries(bakery, "ACTIVITY")] == ["isic-I"]
    assert {"de", "en", "fr"} <= set(discoveries(saas, "LANGUAGES")[0]["detail"]["languages"])
    # Searched with the routed classification; nothing matched: not an absence of demand.
    assert "NO_RELEVANT_DEMAND_FOUND" in codes(saas) and "NO_RELEVANT_DEMAND_FOUND" in codes(bakery)
    assert saas["attentionScopes"][0]["jurisdiction"] == "EU/IE"
    assert world.judge.calls == []  # schema.org self-declaration answered it


def test_a_site_without_evidence_yields_grounded_unknowns_not_a_guess(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:placeholder", PLACEHOLDER)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "NOT_ENOUGH_CAPABILITY_EVIDENCE"
    assert {"NOT_AN_OPERATING_BUSINESS_SITE", "ACTIVITY_NOT_ESTABLISHED"} <= codes(view)
    assert discoveries(view, "ACTIVITY") == [] and discoveries(view, "DEMAND") == []


def test_robots_disallow_stops_before_any_page(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:robots", FORBIDDEN)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "SOURCE_UNAVAILABLE" and "ROBOTS_DISALLOWED" in codes(view)
    assert world.sites.requests == [FORBIDDEN.rstrip("/") + "/robots.txt"]


def test_known_canonical_organization_feeds_the_existing_focus_projection(tmp_path: Path) -> None:
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [entity(artifacts, legal_name="Solartec Energía SL", lei_value=SOLARTEC, websites=(KNOWN,))]
    )
    world = World()
    facade = build(tmp_path, world, identity_source=registry)
    token, added = _attend(facade, tmp_path, "subject:known", KNOWN)
    assert (added["state"], added["observationState"]) == ("CREATED", "QUEUED")
    focus = str(added["focusId"])
    runtime(facade).drain()
    read = facade.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(token))
    assert read.status == 200, read.body
    view = read.body["firstObservation"]
    assert view["target"]["identityLink"] == "REGISTRY_VERIFIED"
    assert view["state"] == "FIRST_PROOF_READY" and discoveries(view, "DEMAND")
    # The site was appended once under the canonical Organization subject and the
    # existing projection (evidence check, opportunities) consumed it unchanged.
    organization = str(organization_id_for("LEI", "GLEIF", SOLARTEC))
    with sqlite3.connect(tmp_path / "observation-memory.sqlite3") as db:
        rows = db.execute(
            "SELECT source_type FROM observations WHERE subject_id=?", (organization,)
        ).fetchall()
    assert rows == [("PUBLIC_WEBSITE",)]
    projection = read.body.get("projection") or {}
    assert projection, read.body
    assert "opportunit" in str(projection).lower()


def test_world_level_reuse_across_tenants_pays_the_public_work_once(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    first, _ = _attend(facade, tmp_path, "subject:t1", SOLAR_ES)
    runtime(facade).drain()
    http_before, ted_before = len(world.sites.requests), len(world.ted.queries)
    second, _ = _attend(facade, tmp_path, "subject:t2", SOLAR_ES)
    runtime(facade).drain()
    reused = _view(facade, second, _pending_id(facade, second))
    # Site reading and the same-day source query are world-level: zero new requests.
    assert len(world.sites.requests) == http_before and len(world.ted.queries) == ted_before
    assert _ledger(reused, "siteReuseHits") == 1 and _ledger(reused, "sourceCacheHits") >= 1
    assert _ledger(reused, "httpRequests") == 0 and _ledger(reused, "sourceRequests") == 0
    assert discoveries(reused, "DEMAND")
    # Tenant isolation: each tenant reads only its own private First Proof.
    other = _pending_id(facade, first)
    denied = facade.handle("GET", f"/subscriber/organizations/{other}/output", _headers(second))
    assert (denied.status, denied.body.get("code")) == (409, "FOCUS_NOT_FOUND")


def test_semantic_judgments_are_reused_across_tenants(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    _attend(facade, tmp_path, "subject:s1", SCHOOL_AR)
    runtime(facade).drain()
    token, _ = _attend(facade, tmp_path, "subject:s2", SCHOOL_AR)
    runtime(facade).drain()
    view = _view(facade, token, _pending_id(facade, token))
    assert len(world.judge.calls) == 1  # the second tenant paid no provider call
    assert _ledger(view, "jevCalls") == 0 and _ledger(view, "jevMemoryHits") >= 5
    assert discoveries(view, "ACTIVITY")[0]["code"] == "isic-P"


def test_transport_failure_is_retried_and_succeeds(tmp_path: Path) -> None:
    world = World()
    world.sites.fail_next.add(SOLAR_ES.rstrip("/") + "/robots.txt")
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:retry", SOLAR_ES)
    assert runtime(facade).drain() == 2  # first attempt failed, second completed
    view = _view(facade, token, _pending_id(facade, token))
    assert view["state"] == "FIRST_PROOF_READY"
    with sqlite3.connect(tmp_path / "first-observation.sqlite3") as db:
        assert db.execute("SELECT state, attempts FROM fo_jobs").fetchall() == [("DONE", 2)]


def test_cancelled_attention_is_reauthorized_away_before_any_request(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:cancel", SOLAR_ES)
    pending = _pending_id(facade, token)
    cancelled = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token),
        {"action": "cancel_pending", "requestRef": "cancel:1", "focusId": pending},
    )
    assert cancelled.status == 200, cancelled.body
    runtime(facade).drain()
    assert world.sites.requests == []
    with sqlite3.connect(tmp_path / "first-observation.sqlite3") as db:
        assert db.execute("SELECT state, last_error FROM fo_jobs").fetchall() == [
            ("FAILED", "TARGET_NO_LONGER_AUTHORIZED")
        ]


def test_pending_attention_cannot_observe_beyond_paid_capacity(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    token, _ = _attend(facade, tmp_path, "subject:capacity", SOLAR_ES)  # capacity 1 used
    second = _add(facade, token, "add:second", BAKERY_FR)
    assert second.body["observationState"] == "CAPACITY_REQUIRED"
    assert runtime(facade).drain() == 1  # only the first target was queued


def test_disabled_first_observation_keeps_todays_behaviour(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world, enabled=False)
    token, added = _attend(facade, tmp_path, "subject:baseline", SOLAR_ES)
    assert added["state"] == "IDENTITY_PENDING" and "observationState" not in added
    assert runtime(facade) is None and world.sites.requests == []
    assert not (tmp_path / "first-observation.sqlite3").exists()
    assert "observation" not in _portfolio(facade, token)[0]


def test_focus_first_observation_hands_over_to_reobservation_without_an_operator_file(
    tmp_path: Path,
) -> None:
    from application.xeed_access.reader import TrustedRequestContext
    from domain.identity import XeedId
    from tools.runtime.first_observation import first_observation_reader
    from tools.runtime.subscriber_observation import ConfiguredSubscriberObservationPlanReader

    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [entity(artifacts, legal_name="Solartec Energía SL", lei_value=SOLARTEC, websites=(KNOWN,))]
    )
    world = World()
    facade = build(tmp_path, world, identity_source=registry)
    token, added = _attend(facade, tmp_path, "subject:handover", KNOWN)
    runtime(facade).drain()
    context = facade.identity.authenticate(token)
    reader = ConfiguredSubscriberObservationPlanReader(
        economic=facade.outputs._economic,
        clock=facade.workflow._clock,
        attention=(),  # no operator file entry at all
        derived_for=first_observation_reader(tmp_path),
    )
    plan = reader.observation_plan_for(
        TrustedRequestContext(context.principal_id, context.tenant_id), XeedId(added["focusId"])
    )
    assert plan is not None
    assert [m.geography.code for m in plan.observation_context.markets] == ["EU/ES"]
    assert {c.capability_id for c in plan.observation_context.capabilities} == {
        "solar-pv-installation"
    }
    assert any(a.source_id == "ted-search-v3" for a in plan.strategy.actions)


def test_public_web_representation_is_measured_without_extra_requests(tmp_path: Path) -> None:
    world = World()
    facade = build(tmp_path, world)
    solar, _ = _attend(facade, tmp_path, "subject:web-solar", SOLAR_ES)
    saas, _ = _attend(facade, tmp_path, "subject:web-saas", SAAS_IE)
    runtime(facade).drain()
    solar_view = _view(facade, solar, _pending_id(facade, solar))
    saas_view = _view(facade, saas, _pending_id(facade, saas))
    (measured,) = discoveries(solar_view, "WEB_REPRESENTATION")
    checks = measured["detail"]["checks"]
    assert measured["detail"]["instrument"] == "site-reading.v1"
    assert (checks["organizationDeclared"], checks["offerDeclared"]) == (True, False)
    assert "score" not in str(measured).lower()
    (gap,) = discoveries(solar_view, "REPRESENTATION_GAP")
    assert gap["code"] == "OFFER_NOT_MACHINE_READABLE" and gap["epistemicState"] == "POTENTIAL"
    assert gap["detail"]["notCausal"] is True
    assert discoveries(saas_view, "REPRESENTATION_GAP") == []  # SoftwareApplication declared
    assert _ledger(solar_view, "httpRequests") == 2  # robots + homepage, nothing added
