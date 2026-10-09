"""Issue 176 E2E: real auth/admission/jobs/persistence/AXENT/OAuth/MCP; synthetic sources.

No network or model output is required. Revocation changes the operator rights file
while the SAME composition, sessions, stores and MCP client remain running.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from application.axent.grounded.corpus import corpus_from_reading
from application.economic_discovery.observation_memory import ObservationRightsStatus
from application.subscriber_projection.evidence_delivery import WITHHELD_TEXT
from application.subscriber_projection.subscriber_runtime import StoredEconomicOutput
from application.xeed_access.reader import XeedReadError
from domain.identity import XeedId
from tests.first_observation import harness
from tests.first_observation.harness import EXAMPLE_HOSTS, KNOWN, runtime
from tests.first_observation.test_first_observation_e2e import _attend
from tests.first_observation.test_understanding_rights import _measured
from tests.integration.test_organization_admission_e2e import _headers
from tests.integration.test_product_mcp_e2e import Client
from tools.runtime.evidence_content import LiveEvidenceContentRights
from tools.runtime.first_observation import first_observation_reader

QUOTE = "Solartec | photovoltaic installation"


def _read(facade: Any, token: str, focus: str) -> dict[str, Any]:
    context = facade.identity.authenticate(token)
    return facade.outputs._economic.read(context, XeedId(focus), datetime.now(UTC)).projection


def _snapshot(facade: Any, token: str, focus: str) -> Any:
    context = facade.identity.authenticate(token)
    economic = facade.outputs._economic
    authorized = economic.authorize(context, XeedId(focus))
    return economic.opportunity_store.latest(
        tenant_id=str(context.tenant_id),
        xeed_id=focus,
        organization_id=authorized.organization.id,
        as_of=datetime.now(UTC),
    )


def _assert_consumers(facade: Any, token: str, focus: str, client: Client) -> None:
    subscriber = facade.handle("GET", f"/subscriber/organizations/{focus}/output", _headers(token))
    assert subscriber.status == 200
    context = facade.identity.authenticate(token)
    axent = facade.axent.service.reader.read(context, XeedId(focus), datetime.now(UTC))
    reply = facade.handle(
        "POST",
        f"/subscriber/organizations/{focus}/axent",
        _headers(token),
        {"question": "What opportunities and evidence are available?", "locale": "en"},
    )
    assert reply.status == 200 and reply.body["grounding"]["modelCalls"] == 0
    responses = [subscriber.body, axent.projection, reply.body]
    for tool in ("get_xeed_overview", "get_xeed_evidence", "get_xeed_timeline"):
        result = client.call(tool, xeed_id=focus)
        assert not result["error"], result
        responses.append(result)
    for payload in responses:
        assert QUOTE not in json.dumps(payload, ensure_ascii=False)


def test_revocation_removes_persisted_economic_excerpts_without_restart(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    context = facade.identity.authenticate(token)
    economic = facade.outputs._economic
    before = _read(facade, token, focus)
    opportunity = before["cognition"]["opportunities"][0]
    assert opportunity["capability"]["excerpt"] == QUOTE
    source_id = opportunity["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(before["organization"]["id"], source_id)
    assert metadata.reuse_authority.rights_status is ObservationRightsStatus.PERMITTED
    assert source_id.startswith("fo:")
    stored = _snapshot(facade, token, focus)
    assert QUOTE in json.dumps(stored.cognition)
    client = Client(facade)
    client.connect(token)  # Real consent + OAuth PKCE; same token after revocation.
    initial = client.call("get_xeed_overview", xeed_id=focus)
    assert not initial["error"] and QUOTE in json.dumps(initial)
    corpus = corpus_from_reading(
        tenant_id=str(context.tenant_id), projection=before, as_of=datetime.now(UTC)
    )

    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    _assert_consumers(facade, token, focus, client)
    after = _read(facade, token, focus)
    kept = after["cognition"]["opportunities"][0]
    assert kept["capability"]["excerpt"] == WITHHELD_TEXT
    assert kept["capability"]["contentAccess"] == "UNKNOWN"
    assert kept["capability"]["label"] == opportunity["capability"]["label"]
    assert kept["epistemic"] == opportunity["epistemic"] == "POTENTIAL"
    assert kept["demand"] == opportunity["demand"]
    assert kept["known"] == opportunity["known"]
    assert kept["relevance"] == opportunity["relevance"]
    # Independent demand source (including its text) survives; identity/provenance/history survive.
    demand_id = kept["demand"]["sourceId"]
    for sources in (before["cognition"]["sources"], after["cognition"]["sources"]):
        next(row for row in sources if row["id"] == demand_id).pop("currentnessEvaluatedAt")
    assert next(row for row in after["cognition"]["sources"] if row["id"] == demand_id) == next(
        row for row in before["cognition"]["sources"] if row["id"] == demand_id
    )
    assert after["temporalHistory"]["disposition"] == before["temporalHistory"]["disposition"]
    for old_item, current_item in zip(
        before["temporalHistory"]["items"], after["temporalHistory"]["items"], strict=True
    ):
        assert all(current_item[key] == value for key, value in old_item.items())
    assert _snapshot(facade, token, focus) == stored  # Immutable history is not erased.
    assert (
        economic.observation_memory.access_metadata(before["organization"]["id"], source_id)
        == metadata
    )
    updated_corpus = corpus_from_reading(
        tenant_id=str(context.tenant_id), projection=after, as_of=datetime.now(UTC)
    )
    assert (
        updated_corpus.dependency_fingerprint != corpus.dependency_fingerprint
    )  # AXENT cache miss.
    _, reusable = economic.observation_seed(context, XeedId(focus), as_of=datetime.now(UTC))
    assert not any(item.record.observation_id == source_id for item, _ in reusable)
    derived = first_observation_reader(tmp_path, rights=runtime(facade).service._rights)
    internal_read = derived(context, XeedId(focus))
    assert internal_read["capabilities"] == []
    assert internal_read["publicUnderstanding"]["citations"] == []
    assert QUOTE not in json.dumps(internal_read)
    # A historical cut cannot recover current forbidden text.
    old_cut = economic.read(context, XeedId(focus), stored.as_of).projection
    assert QUOTE not in json.dumps(old_cut)
    # Physical raw-content purge is independent of safe delivery.
    runtime(facade).purge()
    _assert_consumers(facade, token, focus, client)


@pytest.mark.parametrize("change", ["zero", "shorter", "wider", "missing", "invalid"])
def test_changed_or_missing_grant_never_upgrades_a_materialized_snapshot(
    tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    if change in {"zero", "shorter", "wider"}:
        rights.write(hosts=EXAMPLE_HOSTS, days={"zero": 0, "shorter": 7, "wider": 365}[change])
    elif change == "missing":
        rights.path.unlink()
    else:
        rights.path.write_text("broken json", encoding="utf-8")
    if change in {"shorter", "wider"}:
        economic = facade.outputs._economic
        initial = _read(facade, token, focus)
        source_id = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
        metadata = economic.observation_memory.access_metadata(
            initial["organization"]["id"], source_id
        )
        at = metadata.record.observed_at + timedelta(days=8 if change == "shorter" else 91)
        economic.content_rights = LiveEvidenceContentRights(
            runtime(facade).service._rights, lambda: at
        )
    projection = _read(facade, token, focus)
    assert QUOTE not in json.dumps(projection)
    assert projection["cognition"]["opportunities"][0]["capability"]["contentAccess"] in {
        "UNKNOWN",
        "WITHHELD",
    }
    assert projection["cognition"]["opportunities"][0]["epistemic"] == "POTENTIAL"


def test_expiry_uses_live_clock_even_when_the_requested_cut_is_historical(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, _rights, token, focus = _measured(tmp_path, monkeypatch)
    context = facade.identity.authenticate(token)
    economic = facade.outputs._economic
    snapshot = _snapshot(facade, token, focus)
    initial = economic.read(context, XeedId(focus), snapshot.as_of).projection
    source_id = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(initial["organization"]["id"], source_id)
    expiry = metadata.record.observed_at + timedelta(days=90)
    policy = runtime(facade).service._rights
    economic.content_rights = LiveEvidenceContentRights(
        policy, lambda: expiry - timedelta(microseconds=1)
    )
    assert QUOTE in json.dumps(economic.read(context, XeedId(focus), snapshot.as_of).projection)
    economic.content_rights = LiveEvidenceContentRights(policy, lambda: expiry)
    after = economic.read(context, XeedId(focus), snapshot.as_of).projection
    assert QUOTE not in json.dumps(after)
    assert after["cognition"]["opportunities"][0]["capability"]["contentAccess"] == "WITHHELD"
    assert _snapshot(facade, token, focus) == snapshot


def test_provider_only_revocation_keeps_economic_content(tmp_path: Path, monkeypatch: Any) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    rights.write(hosts=EXAMPLE_HOSTS, provider=False)
    assert QUOTE in json.dumps(_read(facade, token, focus))


def test_legacy_economic_wire_narratives_and_copied_trace_obey_current_rights(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    context = facade.identity.authenticate(token)
    initial = _read(facade, token, focus)
    org = initial["organization"]["id"]
    source_id = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(org, source_id)
    at = datetime.now(UTC)
    # Pre-policy persisted DTO: no new content annotations or permission deadline.
    output = StoredEconomicOutput(
        tenant_id=str(context.tenant_id),
        xeed_id=focus,
        organization_id=org,
        output_id="economic-output:legacy-regression",
        as_of=at,
        output_wire={
            "output_id": "economic-output:legacy-regression",
            "subject_ref": org,
            "as_of": at.isoformat(),
            "epistemic_state": "POTENTIAL",
            "dimensions": [{"dimension_id": "capability", "value": "solar-pv-installation"}],
            "evidence": [
                {
                    "observation_ref": source_id,
                    "source_ref": KNOWN,
                    "observed_at": metadata.record.observed_at.isoformat(),
                    "excerpt": QUOTE,
                    "rights_basis_ref": metadata.reuse_authority.provenance_ref,
                }
            ],
            "contradictions": [f"Historic source stated {QUOTE}"],
        },
        runtime_signal={
            "id": "signal:legacy-regression",
            "nodeKind": "XIGNAL",
            "epistemicState": "POTENTIAL",
            "title": "Potential project relevance",
            "whyAttention": "A sourced economic match",
            "observedAt": at.isoformat(),
            "evidenceNarrative": {
                "steps": [
                    {
                        "kind": "OBSERVATION",
                        "sourceRef": KNOWN,
                        "observedAt": metadata.record.observed_at.isoformat(),
                        "label": QUOTE,
                    }
                ]
            },
            "executionTrace": {"historicalExplanation": f"Previously read {QUOTE}"},
        },
    )
    assert economic.output_store.append(output)
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    after = _read(facade, token, focus)
    assert QUOTE not in json.dumps(after)
    assert after["economicOutput"]["dimensions"] == output.output_wire["dimensions"]
    assert after["economicOutput"]["evidence"][0]["observation_ref"] == source_id
    assert (
        after["economicOutput"]["evidence"][0]["rights_basis_ref"]
        == metadata.reuse_authority.provenance_ref
    )
    assert after["economicOutput"]["epistemic_state"] == "POTENTIAL"
    assert (
        economic.output_store.latest(
            tenant_id=str(context.tenant_id), xeed_id=focus, organization_id=org, as_of=at
        )
        == output
    )


def test_reobservation_does_not_reauthorize_old_snapshots_or_cross_tenant_access(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token_a, focus_a = _measured(tmp_path, monkeypatch)
    token_b, added_b = _attend(facade, tmp_path, "synthetic:tenant-b", KNOWN)
    focus_b = str(added_b["focusId"])
    runtime(facade).drain()
    context_b = facade.identity.authenticate(token_b)
    old = _snapshot(facade, token_a, focus_a)
    rights.write(hosts=EXAMPLE_HOSTS)
    entries = json.loads(rights.path.read_text(encoding="utf-8"))
    for entry in entries:
        if entry["host"] == "solartec.example.com":
            entry["rightsBasis"] = "synthetic: new authorization, original withdrawn"
    rights.path.write_text(json.dumps(entries), encoding="utf-8")
    assert QUOTE not in json.dumps(_read(facade, token_a, focus_a))
    new_quote = "Solartec | photovoltaic installation after reobservation"
    monkeypatch.setitem(harness.PAGES, KNOWN, harness.PAGES[KNOWN].replace(QUOTE, new_quote))
    reobserve = facade.handle(
        "POST",
        "/subscriber/portfolio",
        _headers(token_a),
        {"action": "reobserve", "requestRef": "reobserve:new-grant", "focusId": focus_a},
    )
    assert reobserve.status == 200
    assert runtime(facade).drain() == 1
    current = _read(facade, token_a, focus_a)
    assert current["cognition"]["opportunities"][0]["capability"]["excerpt"] == new_quote
    historic = facade.outputs._economic.read(
        facade.identity.authenticate(token_a), XeedId(focus_a), old.as_of
    ).projection
    assert QUOTE not in json.dumps(historic)
    # Tenant B's existing snapshot remains blocked until B legitimately reobserves.
    assert QUOTE not in json.dumps(_read(facade, token_b, focus_b))
    assert (
        facade.handle(
            "GET", f"/subscriber/organizations/{focus_a}/output", _headers(token_b)
        ).status
        == 403
    )
    with pytest.raises(XeedReadError):
        facade.outputs._economic.read(context_b, XeedId(focus_a), datetime.now(UTC))
    with pytest.raises(XeedReadError):
        facade.axent.service.reader.read(context_b, XeedId(focus_a), datetime.now(UTC))
    client_b = Client(facade)
    client_b.connect(token_b)
    assert client_b.call("get_xeed_overview", xeed_id=focus_a)["error"]


def test_revocation_does_not_affect_an_independent_organization_with_valid_rights(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from pipeline.source_acquisition import ContentAddressedArtifactStore
    from tests.first_observation.harness import SOLAR_ES, World, build
    from tests.first_observation.test_first_observation_e2e import SOLARTEC
    from tests.first_observation.test_understanding_e2e import HOME
    from tests.first_observation.test_understanding_rights import _RightsFile
    from tests.organization_admission.registry_fixture import ControlledRegistry, entity, lei
    from tools.runtime.first_observation import ReloadingContentRights

    rights = _RightsFile(tmp_path / "content-rights.json")
    rights.write(hosts=EXAMPLE_HOSTS)
    artifacts = ContentAddressedArtifactStore(tmp_path / "artifacts")
    registry = ControlledRegistry(
        [
            entity(artifacts, legal_name="Solartec SL", lei_value=SOLARTEC, websites=(KNOWN,)),
            entity(
                artifacts,
                legal_name="Solaria Norte SL",
                lei_value=lei("SOLARIA00000000001"),
                websites=(SOLAR_ES,),
            ),
        ]
    )
    monkeypatch.setitem(harness.PAGES, KNOWN, HOME)
    facade = build(
        tmp_path, World(), identity_source=registry, rights=ReloadingContentRights(rights.path)
    )
    token_a, a = _attend(facade, tmp_path, "synthetic:org-a", KNOWN)
    token_b, b = _attend(facade, tmp_path, "synthetic:org-b", SOLAR_ES)
    assert runtime(facade).drain() == 2
    focus_a, focus_b = str(a["focusId"]), str(b["focusId"])
    baseline = _snapshot(facade, token_b, focus_b)
    before = _read(facade, token_b, focus_b)["cognition"]["opportunities"][0]
    assert before["capability"]["excerpt"]
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    assert QUOTE not in json.dumps(_read(facade, token_a, focus_a))
    after = _read(facade, token_b, focus_b)["cognition"]["opportunities"][0]
    assert after["capability"] == before["capability"]
    assert after["whyPotential"] == before["whyPotential"]
    assert _snapshot(facade, token_b, focus_b) == baseline


def test_legacy_ledger_missing_metadata_and_independent_identical_words(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    context = facade.identity.authenticate(token)
    economic = facade.outputs._economic
    before = _read(facade, token, focus)
    org = before["organization"]["id"]
    source_id = before["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(org, source_id)
    observation = next(
        o
        for o in economic.observation_memory.for_subject(org)
        if o.record.observation_id == source_id
    )
    grant = runtime(facade).service._rights.rights_for(harness.SOLAR_ES, now=datetime.now(UTC))
    independent = replace(
        observation,
        record=replace(
            observation.record, observation_id="fo:independent", source_ref=harness.SOLAR_ES
        ),
        reuse_authority=replace(observation.reuse_authority, provenance_ref=grant.basis_ref),
    )
    economic.observation_memory.append(independent)
    snapshot = {
        "organization": {**before["organization"], "name": QUOTE},
        "realityLedger": [
            {
                "observationId": source_id,
                "fields": {"capability.excerpt": QUOTE, "capability.id": "solar-pv-installation"},
            },
            {
                "observationId": "fo:unknown-legacy",
                "fields": [{"name": "capability.excerpt", "value": "A lost legacy quotation"}],
            },
        ],
        "copies": [f"Old text {QUOTE}"],
        "independent": {"sourceId": "fo:independent", "excerpt": QUOTE},
    }
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    delivered = economic.deliver_content(context, XeedId(focus), snapshot)
    assert delivered["realityLedger"][0]["fields"]["capability.excerpt"] == WITHHELD_TEXT
    assert delivered["realityLedger"][0]["fields"]["capability.id"] == "solar-pv-installation"
    assert delivered["realityLedger"][1]["fields"][0]["value"] is None
    assert QUOTE not in json.dumps(delivered["copies"])
    assert delivered["independent"]["excerpt"] == QUOTE
    assert delivered["organization"]["name"] == QUOTE
    assert snapshot["realityLedger"][0]["fields"]["capability.excerpt"] == QUOTE
    assert economic.observation_memory.access_metadata(org, source_id) == metadata


def test_live_economic_rights_over_real_http_socket(tmp_path: Path, monkeypatch: Any) -> None:
    import threading
    from http.server import ThreadingHTTPServer

    from tests.contracts.test_product_mcp_http_socket import _send
    from tools.runtime.service import RuntimeConfig, build_runtime, make_handler

    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    client = Client(facade)
    client.connect(token)
    host = build_runtime(
        RuntimeConfig(
            environment="production",
            bind_host="127.0.0.1",
            port=0,
            code_sha="a" * 40,
            data_dir=tmp_path / "isolated-host",
            web_root=Path(__file__).resolve().parents[2] / "apps" / "web",
        )
    )
    host.subscriber = facade
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(host))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = str(server.server_address[0]), int(server.server_address[1])
    try:
        headers = [("Authorization", f"Bearer {token}"), ("Origin", "https://axignal.com")]
        path = f"/subscriber/organizations/{focus}/output"
        status, cache, body = _send(base, "GET", path, headers=headers)
        assert status == 200 and QUOTE in body.decode()
        assert "no-store" in cache["Cache-Control"]
        rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
        status, _, body = _send(base, "GET", path, headers=headers)
        assert status == 200 and QUOTE not in body.decode()
        payload = json.dumps(
            {"question": "What economic opportunities are known?", "locale": "en"}
        ).encode()
        status, _, body = _send(
            base,
            "POST",
            f"/subscriber/organizations/{focus}/axent",
            payload,
            [*headers, ("Content-Type", "application/json")],
        )
        assert status == 200 and QUOTE not in body.decode()
        rpc = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_xeed_overview", "arguments": {"xeed_id": focus}},
            }
        ).encode()
        status, cache, body = _send(
            base,
            "POST",
            "/mcp",
            rpc,
            [("Authorization", f"Bearer {client.token}"), ("Content-Type", "application/json")],
        )
        assert status == 200 and not json.loads(body)["result"]["isError"]
        assert QUOTE not in body.decode() and "no-store" in cache["Cache-Control"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_legacy_record_without_original_retention_is_not_implicitly_authorized(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, _rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    before = _read(facade, token, focus)
    source_id = before["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(before["organization"]["id"], source_id)
    assert metadata.reuse_authority.content_retention_days == 90
    legacy = replace(
        metadata, reuse_authority=replace(metadata.reuse_authority, content_retention_days=None)
    )
    assert economic.content_rights.decision(legacy).value == "UNKNOWN"


def test_raw_purge_preserves_history_and_never_uses_a_wider_live_retention(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    initial = _read(facade, token, focus)
    org = initial["organization"]["id"]
    source_id = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    memory = economic.observation_memory
    metadata = memory.access_metadata(org, source_id)
    rights.write(hosts=EXAMPLE_HOSTS, days=365)
    at = metadata.record.observed_at + timedelta(days=91)
    assert (
        memory.purge_first_observation_content(
            now=at, retain_until=lambda u, t: t + timedelta(days=365)
        )
        >= 1
    )
    archived = memory.get_observation(org, source_id)
    assert (
        archived.content_removed
        and archived.raw_content is None
        and archived.raw_artifact_ref is None
    )
    assert archived.record == metadata.record
    assert archived.reuse_authority.rights_status == metadata.reuse_authority.rights_status
    assert archived.reuse_authority.provenance_ref == metadata.reuse_authority.provenance_ref
    assert archived.reuse_authority.content_retention_days == 90
    assert archived.reuse_authority.access_status.value == "INACCESSIBLE"
    # This envelope can be loaded, but cannot reenter the reusable material set.
    context = facade.identity.authenticate(token)
    _, reusable = economic.observation_seed(context, XeedId(focus), as_of=datetime.now(UTC))
    assert not any(item.record.observation_id == source_id for item, _ in reusable)


def test_source_only_legacy_descriptors_resolve_authorized_metadata(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    context = facade.identity.authenticate(token)
    initial = _read(facade, token, focus)
    identifier = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(
        initial["organization"]["id"], identifier
    )
    legacy = {
        "evidence": [
            {
                "source_ref": metadata.record.source_ref,
                "observed_at": metadata.record.observed_at.isoformat(),
                "excerpt": QUOTE,
            }
        ],
        "trace": {"priorCopy": f"Previously {QUOTE}"},
    }
    assert QUOTE in json.dumps(economic.deliver_content(context, XeedId(focus), legacy))
    undated = {"evidence": [{"source_ref": metadata.record.source_ref, "excerpt": QUOTE}]}
    assert QUOTE not in json.dumps(economic.deliver_content(context, XeedId(focus), undated))
    legacy["evidence"][0]["observed_at"] = metadata.record.observed_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert QUOTE in json.dumps(economic.deliver_content(context, XeedId(focus), legacy))
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    delivered = economic.deliver_content(context, XeedId(focus), legacy)
    assert QUOTE not in json.dumps(delivered)
    assert delivered["evidence"][0]["contentAccess"] == "UNKNOWN"
    assert delivered["evidence"][0]["source_ref"] == metadata.record.source_ref
    assert QUOTE in json.dumps(legacy)
    # An unrelated or mismatched observation cannot authorize a source-only copy.
    rights.write(hosts=EXAMPLE_HOSTS)
    legacy["evidence"][0]["observed_at"] = (
        metadata.record.observed_at - timedelta(days=1)
    ).isoformat()
    assert QUOTE not in json.dumps(economic.deliver_content(context, XeedId(focus), legacy))
    legacy["evidence"][0]["source_ref"] = "https://missing.example.com/"
    assert QUOTE not in json.dumps(economic.deliver_content(context, XeedId(focus), legacy))


def test_undated_legacy_row_cannot_borrow_same_source_dated_permission(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, _rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    context = facade.identity.authenticate(token)
    initial = _read(facade, token, focus)
    identifier = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(
        initial["organization"]["id"], identifier
    )
    source = metadata.record.source_ref
    original = {
        "evidence": [
            {
                "source_ref": source,
                "observed_at": metadata.record.observed_at.isoformat(),
                "excerpt": "Authorized dated citation",
            },
            {
                "source_ref": source,
                "excerpt": "Undated untraceable legacy citation",
                "fields": {"capability.id": "normalized-capability"},
            },
        ]
    }
    delivered = economic.deliver_content(context, XeedId(focus), original)
    assert delivered["evidence"][0]["excerpt"] == "Authorized dated citation"
    assert delivered["evidence"][1]["excerpt"] == WITHHELD_TEXT
    assert delivered["evidence"][1]["contentAccess"] == "UNKNOWN"
    assert delivered["evidence"][1]["fields"]["capability.id"] == "normalized-capability"
    assert original["evidence"][1]["excerpt"] == "Undated untraceable legacy citation"
    # Same as with an earlier registered grant: time can be represented equivalently.
    original["evidence"][0]["observed_at"] = metadata.record.observed_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert (
        economic.deliver_content(context, XeedId(focus), original)["evidence"][0]["excerpt"]
        == "Authorized dated citation"
    )


def test_explicit_observation_identity_must_match_source_and_time(
    tmp_path: Path, monkeypatch: Any
) -> None:
    facade, _rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    context = facade.identity.authenticate(token)
    initial = _read(facade, token, focus)
    identifier = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    metadata = economic.observation_memory.access_metadata(
        initial["organization"]["id"], identifier
    )
    valid = {
        "observationId": identifier,
        "source_ref": metadata.record.source_ref,
        "observed_at": metadata.record.observed_at.isoformat(),
        "excerpt": "Authorized matching citation",
    }
    wrong_source = {
        **valid,
        "source_ref": "https://completely-different.example.com/",
        "excerpt": "Unauthenticated unrelated quote",
        "fields": {"capability.id": "economic-fact"},
    }
    wrong_time = {
        **valid,
        "observed_at": (metadata.record.observed_at - timedelta(days=1)).isoformat(),
        "excerpt": "Unauthenticated wrong-time quote",
    }
    original = {"evidence": [valid, wrong_source, wrong_time]}
    delivered = economic.deliver_content(context, XeedId(focus), original)
    assert delivered["evidence"][0]["excerpt"] == "Authorized matching citation"
    assert delivered["evidence"][1]["excerpt"] == WITHHELD_TEXT
    assert delivered["evidence"][1]["contentAccess"] == "UNKNOWN"
    assert delivered["evidence"][1]["fields"]["capability.id"] == "economic-fact"
    assert delivered["evidence"][2]["excerpt"] == WITHHELD_TEXT
    assert delivered["evidence"][2]["contentAccess"] == "UNKNOWN"
    assert original["evidence"][1]["excerpt"] == "Unauthenticated unrelated quote"


def test_purge_removes_content_fields_and_preserves_normalized_economic_facts(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import sqlite3

    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    initial = _read(facade, token, focus)
    identifier = initial["cognition"]["opportunities"][0]["capability"]["sourceId"]
    memory = economic.observation_memory
    original = memory.get_observation(initial["organization"]["id"], identifier)
    from application.economic_discovery.observation_memory import (
        ObservationFieldState,
        ObservedField,
    )

    # Explicit synthetic legacy field capture: normalized fact + verbatim/conflicting text.
    original = replace(
        original,
        record=replace(original.record, observation_id="fo:legacy-field-capture"),
        fields=(
            ObservedField("capability.id", "solar-pv-installation"),
            ObservedField("capability.excerpt", QUOTE),
            ObservedField(
                "capture.quotation",
                QUOTE,
                ObservationFieldState.CONFLICTING,
                (QUOTE, "Another original source quotation"),
            ),
        ),
    )
    memory.append(original)
    identifier = original.record.observation_id
    assert any(
        field.name == "capability.excerpt" and field.value == QUOTE for field in original.fields
    )
    facts = tuple(field for field in original.fields if field.name == "capability.id")
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    runtime(facade).purge()
    retired = memory.get_observation(initial["organization"]["id"], identifier)
    assert retired.fields == facts
    assert QUOTE not in repr(retired)
    assert retired.record == original.record
    assert retired.reuse_authority.rights_status == original.reuse_authority.rights_status
    with sqlite3.connect(memory._path) as connection:
        rows = connection.execute(
            "SELECT field_value, competing_values_json FROM observation_fields WHERE observation_id=?",
            (identifier,),
        ).fetchall()
    assert QUOTE not in repr(rows)


def test_continuity_retains_facts_without_reusing_withdrawn_text(
    tmp_path: Path, monkeypatch: Any
) -> None:
    from application.subscriber_continuity.model import OpenQuestion, QuestionKind

    facade, rights, token, focus = _measured(tmp_path, monkeypatch)
    economic = facade.outputs._economic
    context = facade.identity.authenticate(token)
    now = datetime.now(UTC)
    continuity = economic.continuity
    checkpoint, _ = continuity.record(context, XeedId(focus), as_of=now)
    # Simulate an already materialized checkpoint from the pre-policy runtime.
    dependency = next(d for d in checkpoint.state.dependencies if d.key.startswith("obs:fo:"))
    legacy_dependency = replace(
        dependency,
        fields=(
            *(f for f in dependency.fields if f[0] != "capability.excerpt"),
            ("capability.excerpt", QUOTE, "VALUE"),
        ),
    )
    legacy_state = replace(
        checkpoint.state,
        dependencies=tuple(
            legacy_dependency if d.key == dependency.key else d
            for d in checkpoint.state.dependencies
        ),
        questions=(
            *checkpoint.state.questions,
            OpenQuestion(
                "q:legacy-copy",
                QuestionKind.MISSING_CONTEXT,
                "offer",
                f"Previously {QUOTE}",
                (dependency.key,),
            ),
        ),
    )
    legacy, _ = continuity.store.append(str(context.tenant_id), focus, legacy_state)
    assert QUOTE in json.dumps(continuity.read(context, XeedId(focus), as_of=now))
    rights.write(hosts=tuple(h for h in EXAMPLE_HOSTS if h != "solartec.example.com"))
    assert QUOTE not in json.dumps(continuity.read(context, XeedId(focus), as_of=now))
    assert continuity.store.get(str(context.tenant_id), focus, legacy.checkpoint_id) == legacy
    current, _ = continuity.record(context, XeedId(focus), as_of=now)
    assert QUOTE not in repr(current.state.dependencies)
    preserved = next(d for d in current.state.dependencies if d.key == dependency.key)
    assert preserved.source_ref == dependency.source_ref
    assert preserved.content_fingerprint == dependency.content_fingerprint
    assert tuple(f for f in preserved.fields if f[0] != "capability.excerpt") == tuple(
        f for f in dependency.fields if f[0] != "capability.excerpt"
    )
