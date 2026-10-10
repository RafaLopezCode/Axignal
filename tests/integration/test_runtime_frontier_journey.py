"""One governed runtime journey over real loopback HTTP, compositions and SQLite.

Registry, RFC 2606 public sources, OIDC and semantic judgments are controlled ports.
This is composition evidence, not production/provider-quality certification.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from application.organization_admission.service import organization_id_for
from domain.identity import XeedId
from pipeline.source_acquisition import ContentAddressedArtifactStore
from tests.axent.fixtures import ScriptedLuna
from tests.first_observation import harness
from tests.first_observation.harness import KNOWN, World, build, discoveries, runtime
from tests.first_observation.test_understanding_e2e import (
    AFTER,
    BEFORE,
    HOME,
    SERVICES,
    SyntheticSites,
    synthetic_rule,
)
from tests.integration.runtime_frontier_harness import TcpSubscriber, serve
from tests.integration.test_organization_admission_e2e import (
    _add,
    _focuses,
    _headers,
    _organizations,
    _pilot,
    _portfolio,
)
from tests.integration.test_product_mcp_e2e import Client
from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei
from tests.semantic_layer.fakes import FakeSystemOne

SOLARTEC = lei("SOLARTEC0000000001")


def output(client: TcpSubscriber, session: str, focus: str) -> dict[str, Any]:
    response = client.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(session))
    assert response.status == 200, response.body
    return dict(response.body)


def reobserve(client: TcpSubscriber, session: str, focus: str, request: str) -> None:
    response = client.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(session),
        {"action": "reobserve", "requestRef": request, "focusId": focus},
    )
    assert response.status == 200 and response.body["observationState"] == "QUEUED", response.body


def observations(root: Path, organization: str) -> list[tuple[str, str, str]]:
    with sqlite3.connect(root / "observation-memory.sqlite3") as database:
        return list(
            database.execute(
                "SELECT observation_id, source_ref, content_fingerprint FROM observations "
                "WHERE subject_id=? ORDER BY observed_at, observation_id",
                (organization,),
            )
        )


def test_runtime_frontier_governed_journey(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_connect = socket.socket.connect

    def loopback_only(connection: socket.socket, address: Any) -> None:
        host = str(address[0])
        assert host == "localhost" or ipaddress.ip_address(host).is_loopback, address
        original_connect(connection, address)

    # Any accidental adapter/provider activation fails before external dispatch.
    monkeypatch.setattr(socket.socket, "connect", loopback_only)
    monkeypatch.setitem(harness.PAGES, KNOWN, HOME)
    monkeypatch.setitem(harness.PAGES, SERVICES, BEFORE)
    world = World(sites=SyntheticSites(), judge=FakeSystemOne(synthetic_rule))
    world.ted.records = tuple(
        replace(record, source_url=f"https://demand.example.com/notices/{record.record_id}")
        for record in world.ted.records
    )
    registry = ControlledRegistry()
    facade = build(tmp_path, world, identity_source=registry, public_understanding=True)
    organization = str(organization_id_for("LEI", "GLEIF", SOLARTEC))
    evidence: dict[str, Any] = {
        "scope": "LOCAL_SYNTHETIC_PORTS_REAL_COMPOSITION",
        "paidProviderCalls": 0,
        "productionVerification": "NOT_PERFORMED",
        "transport": "TCP_LOOPBACK_PRODUCTION_HANDLER",
        "syntheticPorts": [
            "OIDC",
            "REGISTRY",
            "RFC2606_WEBSITES",
            "PUBLIC_DEMAND",
            "SYSTEM_ONE",
            "AXENT_REASONER",
        ],
        "realServices": [
            "HTTP",
            "IDENTITY",
            "EVIDENCE_ADMISSION",
            "PORTFOLIO",
            "ENTITLEMENTS",
            "FIRST_OBSERVATION_JOBS",
            "OBSERVATION_MEMORY",
            "ECONOMIC_PROJECTION",
            "AXENT_GROUNDING",
            "OAUTH_PKCE",
            "PRODUCT_MCP",
        ],
        "events": [],
    }

    with serve(tmp_path, facade) as client:
        session, tenant = _pilot(client, tmp_path, "synthetic:frontier-a")
        assert (_organizations(tmp_path), _focuses(tmp_path)) == (0, 0)
        added = _add(client, session, "frontier:add", KNOWN)
        assert (added.body["state"], added.body["observationState"]) == (
            "IDENTITY_PENDING",
            "QUEUED",
        )
        assert not world.sites.requests
        (pending,) = _portfolio(client, session)
        pending_id = str(pending["focusId"])
        assert runtime(facade).drain() == 1
        pending_output = output(client, session, pending_id)
        assert pending_output["firstObservation"]["state"] == "FIRST_PROOF_READY"
        assert discoveries(pending_output["firstObservation"], "ACTIVITY")
        assert (_organizations(tmp_path), _focuses(tmp_path)) == (0, 0)
        assert observations(tmp_path, organization) == []
        evidence["events"].append(
            {"phase": "PENDING_PUBLIC_OBSERVATION", "canonicalOrganizations": 0, "focuses": 0}
        )

        # Only a later independent registry attestation may establish legal identity.
        registry.records.append(
            entity(
                ContentAddressedArtifactStore(tmp_path / "artifacts"),
                legal_name="Solartec Energía SL",
                lei_value=SOLARTEC,
                websites=(KNOWN,),
            )
        )
        admitted = client.handle(
            "POST",
            "/subscriber/portfolio",
            _headers(session),
            {"action": "retry_pending", "requestRef": "frontier:admit", "focusId": pending_id},
        )
        assert admitted.status == 200 and admitted.body["state"] == "CREATED", admitted.body
        focus = str(admitted.body["focusId"])
        assert admitted.body["organizationId"] == organization and focus != pending_id
        assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)
        assert runtime(facade).drain() == 1
        first = output(client, session, focus)
        proof = first["firstObservation"]
        assert proof["target"]["identityLink"] == "REGISTRY_VERIFIED"
        baseline = proof["publicUnderstanding"]
        assert baseline["status"] == "MEASURED"
        assert baseline["authority"] == "DERIVED_CONDITIONED_NOT_CANONICAL"
        assert [item["state"] for item in baseline["dimensions"]] == [
            "STRENGTH",
            "CONSTRUCTIVE_GAP",
            "CONSTRUCTIVE_GAP",
        ]
        source_rows = observations(tmp_path, organization)
        assert {row[1] for row in source_rows} == {KNOWN, SERVICES}
        opportunities = first["projection"]["cognition"]["opportunities"]
        assert opportunities and all(item["epistemic"] == "POTENTIAL" for item in opportunities)
        assert all(
            item["capability"]["sourceId"] in {row[0] for row in source_rows}
            for item in opportunities
        )
        internal = runtime(facade).store.proof(tenant, focus)
        assert internal["ledger"]["lunaCalls"]["value"] == 0
        assert "ledger" not in proof and "trace" not in baseline
        assert not any(tenant in json.dumps(batch.state) for batch in world.judge.calls)
        evidence["events"].append(
            {
                "phase": "ADMITTED_FOCUS_TO_MEMORY_AND_OPPORTUNITY",
                "canonicalOrganizations": 1,
                "websiteSources": [row[1] for row in source_rows],
                "opportunities": len(opportunities),
                "epistemic": "POTENTIAL",
            }
        )

        # The scripted reasoner cannot mutate truth; the real AXENT service validates citations.
        reasoner = ScriptedLuna(model="scripted-offline-luna-fixture")
        facade.axent.service.reasoner = reasoner
        answer = client.handle(
            "POST",
            f"/subscriber/organizations/{focus}/axent",
            _headers(session),
            {"question": "¿Qué oportunidades hay?", "locale": "es"},
        )
        assert answer.status == 200, answer.body
        grounding = cast(dict[str, Any], answer.body["grounding"])
        assert grounding["route"] == "MODEL" and len(reasoner.requests) == 1
        assert grounding["claims"] and all(
            claim["epistemic"] == "POTENTIAL" for claim in grounding["claims"]
        )
        cited = {ref for claim in grounding["claims"] for ref in claim["evidence"]}
        assert cited <= {item["ref"] for item in grounding["evidence"]}

        mcp = Client(client)
        mcp.connect(session)
        overview = mcp.call("get_xeed_overview", xeed_id=focus)
        assert not overview["error"] and overview["opportunities"]
        assert all(
            item["epistemic"] == "POTENTIAL" and item["evidence"]
            for item in overview["opportunities"]
        )
        sources = mcp.call("get_xeed_evidence", xeed_id=focus)
        assert not sources["error"] and sources["sources"]
        assert all(item["observed_at"] and item["currentness"] for item in sources["sources"])
        assert Client(client).rpc("tools/list").status == 401

        other_session, other_tenant = _pilot(client, tmp_path, "synthetic:frontier-b")
        assert other_tenant != tenant
        denied = client.handle(
            "GET", f"/subscriber/organizations/{focus}/output", _headers(other_session)
        )
        assert denied.status in {403, 404} and focus not in json.dumps(denied.body)
        denied_axent = client.handle(
            "POST",
            f"/subscriber/organizations/{focus}/axent",
            _headers(other_session),
            {"question": "¿Qué oportunidades hay?", "locale": "es"},
        )
        assert denied_axent.status in {403, 404} and len(reasoner.requests) == 1
        foreign = Client(client)
        foreign.connect(other_session)
        assert foreign.call("get_xeed_overview", xeed_id=focus)["error"] == "XEED_NOT_AVAILABLE"
        assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)
        evidence["events"].append(
            {
                "phase": "AXENT_MCP_AND_TENANT_ISOLATION",
                "axentScriptedCalls": len(reasoner.requests),
                "mcpSources": len(sources["sources"]),
            }
        )

    # Fresh runtime/HTTP composition over the same durable stores; no input reconstruction.
    restarted = build(tmp_path, world, identity_source=registry, public_understanding=True)
    with serve(tmp_path, restarted) as client:
        persisted = output(client, session, focus)
        assert (
            persisted["firstObservation"]["publicUnderstanding"]["reportId"] == baseline["reportId"]
        )
        assert observations(tmp_path, organization) == source_rows
        assert _portfolio(client, session)[0]["focusId"] == focus
        persisted_mcp = Client(client)
        persisted_mcp.token = mcp.token
        assert (
            persisted_mcp.call("get_xeed_overview", xeed_id=focus)["opportunities"]
            == overview["opportunities"]
        )

        before_requests = len(world.sites.requests)
        reobserve(client, session, focus, "frontier:unchanged")
        assert len(world.sites.requests) == before_requests
        assert runtime(restarted).drain() == 1
        assert {KNOWN, SERVICES} <= set(world.sites.requests[before_requests:])
        unchanged = output(client, session, focus)["firstObservation"]["publicUnderstanding"]
        assert unchanged["comparison"]["state"] == "COMPARABLE"
        assert unchanged["comparison"]["changes"] == []
        assert len(unchanged["history"]) == 1
        assert unchanged["history"][0]["reportId"] == baseline["reportId"]
        assert {row[2] for row in observations(tmp_path, organization)} == {
            row[2] for row in source_rows
        }
        evidence["events"].append(
            {
                "phase": "RESTART_AND_UNCHANGED_REOBSERVATION",
                "conditionedChanges": 0,
                "history": len(unchanged["history"]),
            }
        )

        monkeypatch.setitem(harness.PAGES, SERVICES, AFTER)
        reobserve(client, session, focus, "frontier:changed")
        assert runtime(restarted).drain() == 1
        changed_output = output(client, session, focus)
        changed = changed_output["firstObservation"]["publicUnderstanding"]
        assert [item["state"] for item in changed["dimensions"]] == ["STRENGTH"] * 3
        assert {item["dimension"] for item in changed["comparison"]["changes"]} == {
            "audience",
            "outcome",
        }
        assert (
            changed["comparison"]["meaning"]
            == "INTERPRETATION_CHANGE_NOT_PROVEN_BUSINESS_IMPROVEMENT"
        )
        assert (
            len(changed["history"]) == 2
            and changed["history"][0]["reportId"] == unchanged["reportId"]
        )
        assert changed["history"][1]["reportId"] == baseline["reportId"]
        assert {row[2] for row in observations(tmp_path, organization)} > {
            row[2] for row in source_rows
        }

        context = restarted.identity.authenticate(session)
        historical = restarted.axent.service.reader.read(
            context, XeedId(focus), datetime.fromisoformat(baseline["measuredAt"])
        )
        assert historical.projection["publicUnderstanding"]["reportId"] == baseline["reportId"]
        timeline = persisted_mcp.call("get_xeed_timeline", xeed_id=focus)
        assert not timeline["error"] and timeline["current"] and timeline["previous"]
        # Empty normalized bases cannot establish either economic change or no change.
        # The conditioned instrument has comparable audience/outcome changes above.
        assert changed["comparison"]["state"] == "COMPARABLE"
        assert all(item["changed_from_previous"] is None for item in timeline["history"])
        assert timeline["current"]["changed_from_previous"] is None
        assert timeline["previous"]["changed_from_previous"] is None
        assert timeline["material_changes"] == []
        assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)
        evidence["events"].append(
            {
                "phase": "CHANGED_SOURCE_WITH_CONDITIONED_HISTORY",
                "conditionedChanges": [
                    item["dimension"] for item in changed["comparison"]["changes"]
                ],
                "history": len(changed["history"]),
                "conditionedComparison": changed["comparison"]["state"],
                "normalizedEconomicChange": "UNKNOWN_NO_NORMALIZED_FIELDS",
                "normalizedChangeComparisons": [
                    item["changed_from_previous"] for item in timeline["history"]
                ],
                "normalizedEconomicMaterialChanges": len(timeline["material_changes"]),
            }
        )
        evidence["limitations"] = [
            "FirstObservation website seeds carry no normalized economic fields; economic change remains UNKNOWN, while audience/outcome changes are measured by a comparable conditioned interpretation."
        ]

    final_restart = build(tmp_path, world, identity_source=registry, public_understanding=True)
    with serve(tmp_path, final_restart) as client:
        final_output = output(client, session, focus)
        final_report = final_output["firstObservation"]["publicUnderstanding"]
        assert final_report["reportId"] == changed["reportId"]
        assert [item["reportId"] for item in final_report["history"]] == [
            unchanged["reportId"],
            baseline["reportId"],
        ]
        context = final_restart.identity.authenticate(session)
        historical = final_restart.axent.service.reader.read(
            context, XeedId(focus), datetime.fromisoformat(baseline["measuredAt"])
        )
        assert historical.projection["publicUnderstanding"]["reportId"] == baseline["reportId"]
        evidence["events"].append(
            {"phase": "HISTORY_SURVIVES_FINAL_RESTART", "history": len(final_report["history"])}
        )

    evidence["recordedAt"] = datetime.now(UTC).isoformat()
    (tmp_path / "journey.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    (tmp_path / "subscriber-contract-samples.json").write_text(
        json.dumps(
            {
                "pending": pending_output,
                "initial": first,
                "restarted": persisted,
                "changed": changed_output,
                "final": final_output,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
