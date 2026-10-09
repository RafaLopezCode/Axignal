"""Synthetic source/provider, real subscriber HTTP/auth/admission/jobs/store/projection.

No real Google login, provider-quality or production claim is made by this fixture.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from application.semantic_layer.contracts import SemanticBatch, SemanticQuestion
from domain.identity import XeedId
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.first_observation import harness
from tests.first_observation.harness import KNOWN, World, build, jev_rule, runtime
from tests.first_observation.test_first_observation_e2e import SOLARTEC, _attend, _view
from tests.integration.test_organization_admission_e2e import _headers
from tests.organization_admission.registry_fixture import ControlledRegistry, entity
from tests.semantic_layer.fakes import FakeSystemOne

SERVICES = KNOWN + "services"
HOME = """<html lang="en"><head><title>Solartec | photovoltaic installation</title></head>
<body><h1>We install photovoltaic panels.</h1><a href="/services">Services</a>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Solartec","address":{"@type":"PostalAddress","addressCountry":"ES"}}</script></body></html>"""
BEFORE = '<html lang="en"><body><p>We install photovoltaic panels.</p></body></html>'
AFTER = '<html lang="en"><body><p>We install photovoltaic panels for households.</p><p>Our systems reduce purchased electricity under suitable site conditions.</p></body></html>'


def synthetic_rule(batch: SemanticBatch, q: SemanticQuestion) -> tuple[str, float]:
    if not q.question_id.startswith("pu_"):
        return jev_rule(batch, q)
    if q.question_id == "pu_control_positive":
        return "true", 0.99
    if q.question_id == "pu_control_negative":
        return "false", 0.99
    phrase = {
        "pu_offer": "install photovoltaic",
        "pu_audience": "for households",
        "pu_outcome": "reduce purchased electricity",
    }[q.question_id]
    quotes = batch.state["quotations"]
    assert isinstance(quotes, list)
    match = next((r["id"] for r in quotes if phrase in r["text"].lower()), None)
    return str(match or "NOT_STATED"), 0.93


class SyntheticSites(harness.SiteWorld):
    """Only network replaced; source timestamps are the actual controlled acquisition."""

    def fetch(self, url: str, *, slot: str, retain_body: bool = False) -> Any:
        return replace(
            super().fetch(url, slot=slot, retain_body=retain_body), observed_at=datetime.now(UTC)
        )


def controlled_facade(root: Path, monkeypatch: Any) -> tuple[Any, World]:
    monkeypatch.setitem(harness.PAGES, KNOWN, HOME)
    monkeypatch.setitem(harness.PAGES, SERVICES, BEFORE)
    world = World(sites=SyntheticSites(), judge=FakeSystemOne(synthetic_rule))
    registry = ControlledRegistry(
        [
            entity(
                ContentAddressedArtifactStore(root / "artifacts"),
                legal_name="Solartec Energía SL",
                lei_value=SOLARTEC,
                websites=(KNOWN,),
            )
        ]
    )
    facade = build(root, world, identity_source=registry, public_understanding=True)
    return facade, world


def test_runtime_bidirectional_reobservation_is_private_durable_and_fresh(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, world = controlled_facade(tmp_path, monkeypatch)
    token, added = _attend(facade, tmp_path, "synthetic:agency-a", KNOWN)
    focus = str(added["focusId"])
    assert runtime(facade).drain() == 1
    view = _view(facade, token, focus)
    report = view["publicUnderstanding"]
    assert report["status"] == "MEASURED", report
    assert [d["state"] for d in report["dimensions"]] == [
        "STRENGTH",
        "CONSTRUCTIVE_GAP",
        "CONSTRUCTIVE_GAP",
    ]
    assert SERVICES in world.sites.requests  # routing was already sufficient on homepage
    assert (
        view["firstProofReady"] is True
        and report["authority"] == "DERIVED_CONDITIONED_NOT_CANONICAL"
    )
    assert "trace" not in report and "ledger" not in report
    context = facade.identity.authenticate(token)
    internal = runtime(facade).store.proof(str(context.tenant_id), focus)
    assert internal["publicUnderstanding"]["trace"][0]["answer"]["distribution"]
    assert not any(str(context.tenant_id) in json.dumps(b.state) for b in world.judge.calls)
    assert internal["ledger"]["lunaCalls"]["value"] == 0

    # AXENT explains from the persisted conditioned basis, with the same authorization.
    from application.axent.grounded.corpus import corpus_from_reading

    axent_reading = facade.axent.service.reader.read(context, XeedId(focus), datetime.now(UTC))
    corpus = corpus_from_reading(
        tenant_id=str(context.tenant_id),
        projection=axent_reading.projection,
        as_of=datetime.now(UTC),
    )
    conditioned = [i for i in corpus.items if i.item_id.startswith("public-understanding:")]
    assert conditioned and all(i.epistemic == "POTENTIAL" for i in conditioned)
    assert any("CONSTRUCTIVE_GAP" in i.text for i in conditioned)
    assert all(i.source_ref in {KNOWN, SERVICES} for i in conditioned)

    reply = facade.handle(
        "POST",
        f"/subscriber/organizations/{focus}/axent",
        _headers(token),
        {
            "question": "What can be understood about the public offer, audience and outcome?",
            "locale": "en",
        },
    )
    assert reply.status == 200
    assert any(str(ref).startswith("public-understanding:") for ref in reply.body["signalIds"])
    assert reply.body["grounding"]["modelCalls"] == 0
    assert any("CONSTRUCTIVE_GAP" in str(e["label"]) for e in reply.body["grounding"]["evidence"])

    source_cut = datetime.fromisoformat(report["sourceObservedAt"])
    earlier = facade.axent.service.reader.read(context, XeedId(focus), source_cut)
    assert "publicUnderstanding" not in earlier.projection
    earlier_corpus = corpus_from_reading(
        tenant_id=str(context.tenant_id), projection=axent_reading.projection, as_of=source_cut
    )
    assert not any(i.item_id.startswith("public-understanding:") for i in earlier_corpus.items)

    # Same homepage; changed service page must be fetched now, without waiting a week.
    monkeypatch.setitem(harness.PAGES, SERVICES, AFTER)
    before_calls = len(world.sites.requests)
    requested = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token),
        {"action": "reobserve", "requestRef": "synthetic:reobserve", "focusId": focus},
    )
    assert requested.status == 200 and requested.body["observationState"] == "QUEUED"
    assert runtime(facade).drain() == 1
    assert SERVICES in world.sites.requests[before_calls:]
    current = _view(facade, token, focus)["publicUnderstanding"]
    assert [d["state"] for d in current["dimensions"]] == ["STRENGTH"] * 3
    assert current["comparison"]["state"] == "COMPARABLE"
    assert {d["dimension"] for d in current["comparison"]["changes"]} == {"audience", "outcome"}
    assert len(current["history"]) == 1
    prior_cut = datetime.fromisoformat(report["measuredAt"])
    historical = facade.axent.service.reader.read(context, XeedId(focus), prior_cut)
    assert historical.projection["publicUnderstanding"]["reportId"] == report["reportId"]
    assert not historical.projection["publicUnderstanding"]["comparison"]
    assert current["history"][0]["currentness"] == "HISTORICAL"

    # Read after rebuilding the actual composition: reports and history survive.
    restarted = build(tmp_path, world, public_understanding=True)
    persisted = _view(restarted, token, focus)["publicUnderstanding"]
    assert persisted["reportId"] == current["reportId"] and len(persisted["history"]) == 1
    token_b, tenant_b = harness_pilot(restarted, tmp_path)
    assert tenant_b != str(context.tenant_id)
    denied = restarted.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(token_b))
    assert denied.status in {403, 404}
    assert focus not in json.dumps(denied.body)
    with sqlite3.connect(tmp_path / "canonical-organizations.sqlite3") as db:
        assert db.execute("SELECT COUNT(*) FROM canonical_legal_identities").fetchone()[0] == 1

    # Purge must remove content but keep a readable subscriber DTO after restart.
    expires = datetime.fromisoformat(persisted["contentExpiresAt"])
    runtime(restarted).store.purge(now=expires)
    expired = _view(restarted, token, focus)["publicUnderstanding"]
    assert expired["status"] == "NOT_MEASURED" and expired["cause"] == "CONTENT_EXPIRED"
    assert expired["currentness"] == "EXPIRED" and expired["history"] == []
    assert expired["citations"] == [] and expired["dimensions"] == []
    assert expired.get("sourceRights", []) == []
    assert expired["authority"] == "DERIVED_CONDITIONED_NOT_CANONICAL"
    assert expired["execution"] == persisted["execution"]
    assert expired["coverage"] == persisted["coverage"]
    assert "We install photovoltaic" not in json.dumps(expired)


def harness_pilot(facade: Any, path: Path) -> tuple[str, str]:
    from tests.integration.test_organization_admission_e2e import _pilot

    return _pilot(facade, path, "synthetic:agency-b")


def test_runtime_missing_service_page_does_not_blame_organization(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, _world = controlled_facade(tmp_path, monkeypatch)
    monkeypatch.delitem(harness.PAGES, SERVICES)
    token, added = _attend(facade, tmp_path, "synthetic:acquisition-miss", KNOWN)
    runtime(facade).drain()
    report = _view(facade, token, str(added["focusId"]))["publicUnderstanding"]
    assert report["coverage"] == "INCOMPLETE"
    assert all(
        d["state"] != "CONSTRUCTIVE_GAP" and d["proposal"] is None for d in report["dimensions"]
    )
    assert any(d["cause"] == "OBSERVATION_MISS" for d in report["dimensions"])


def test_opt_in_configuration_survives_allowlist() -> None:
    from tools.runtime.subscriber_configuration import load_subscriber_settings

    settings = load_subscriber_settings({"AXIGNAL_PUBLIC_UNDERSTANDING_ENABLED": "true"})
    assert settings.values["AXIGNAL_PUBLIC_UNDERSTANDING_ENABLED"] == "true"
