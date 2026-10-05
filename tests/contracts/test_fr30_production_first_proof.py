from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from application.source_acquisition import SourceObservation
from pipeline.learning_memory import SqliteLearningMemory
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import ContentAddressedArtifactStore, HttpSourceSensor
from tools.runtime.config import RuntimeConfig
from tools.runtime.first_proof import (
    FirstProofInsufficientEvidence,
    FirstProofService,
    FirstProofStore,
)
from tools.runtime.service import build_runtime, make_handler

SHA = "b" * 40
NOW = datetime(2026, 10, 1, 12, 30, tzinfo=UTC)


def _service(tmp_path: Path) -> FirstProofService:
    data = tmp_path / "runtime"
    artifacts = ContentAddressedArtifactStore(data / "artifacts")
    return FirstProofService(
        code_sha=SHA,
        allowed_host="axignal.com",
        store=FirstProofStore(data / "first-proof.sqlite3"),
        observation_memory=SqliteObservationMemory(data / "observation-memory.sqlite3"),
        learning_memory=SqliteLearningMemory(data / "learning-memory.sqlite3"),
        artifacts=artifacts,
    )


def _install_source(monkeypatch: pytest.MonkeyPatch, service: FirstProofService) -> None:
    body = (
        b"<!doctype html><html lang='en'><head><title>AXIGNAL</title>"
        b"<meta name='description' content='Observe the economic world from the outside.'>"
        b"</head><body><main>AXIGNAL observes the economic world from the outside.</main></body></html>"
    )
    body_ref = service.artifacts.put_bytes(body)
    body_fingerprint = f"sha256:{hashlib.sha256(body).hexdigest()}"
    envelope_ref = service.artifacts.put_json(
        {
            "schema": "axignal.source-observation/0.1",
            "source": "fr30-controlled-test",
            "body_artifact_ref": body_ref,
            "body_fingerprint": body_fingerprint,
        }
    )
    observation_fingerprint = f"sha256:{ContentAddressedArtifactStore.digest(envelope_ref)}"

    def observe(self, request, policy):
        del self
        return SourceObservation(
            request_id=request.request_id,
            subject_id=request.subject_id,
            observation_slot=request.observation_slot,
            requested_uri=request.target_uri,
            final_uri=request.target_uri,
            retrieved_at=service.clock(),
            http_status=200,
            content_type="text/html; charset=utf-8",
            body_fingerprint=body_fingerprint,
            body_artifact_ref=body_ref,
            raw_observation_ref=envelope_ref,
            observation_fingerprint=observation_fingerprint,
            instrument_ref="fr30-controlled-http/1",
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            redirect_chain=(request.target_uri,),
            peer_ips=("203.0.113.10",),
            failure_state=None,
        )

    monkeypatch.setattr(HttpSourceSensor, "observe", observe)


def test_first_proof_rejects_non_allowlisted_or_non_https_target(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(ValueError, match="configured HTTPS host"):
        service.plant(label="bad", target_uri="https://example.com/")
    with pytest.raises(ValueError, match="configured HTTPS host"):
        service.plant(label="bad", target_uri="http://axignal.com/")


def test_first_xeed_reaches_real_governed_first_proof_and_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _service(tmp_path)
    _install_source(monkeypatch, service)
    projection = service.plant(label="AXIGNAL first proof", target_uri="https://axignal.com/")
    assert projection["realityLevel"] == "LIVE_PRODUCTION_FIRST_PROOF"
    assert projection["runtimeCodeSha"] == SHA
    assert projection["lifecycleStatus"] == "LIVE"
    assert projection["reloadContinuity"] == "PERSISTED_RUNTIME_READ_MODEL"
    assert projection["organization"] == {
        "id": "org:axignal",
        "name": "AXIGNAL",
        "capabilities": [],
        "markets": [],
    }
    nodes = projection["nodes"]
    assert isinstance(nodes, list) and len(nodes) == 1
    xignal = nodes[0]
    assert xignal["nodeKind"] == "XIGNAL"
    assert xignal["epistemicState"] == "OBSERVED"
    assert xignal["currentness"] == "CURRENT"
    assert xignal["observationSupportRefs"]
    assert xignal["unknowns"]

    narrative = xignal["evidenceNarrative"]
    kinds = [step["kind"] for step in narrative["steps"]]
    assert narrative["xignalId"] == xignal["id"]
    assert kinds[0] == "XIGNAL"
    assert {"OBSERVATION", "SOURCE", "UNKNOWN"}.issubset(kinds)
    assert any(step["artifactVerified"] is True for step in narrative["steps"])
    observations = service.observation_memory.for_subject("org:axignal")
    assert len(observations) == 1
    learning = service.learning_memory.for_xeed(projection["context"]["id"])
    assert len(learning) >= 5
    assert any(event.yield_.xignals_emitted == 1 for event in learning)
    assert projection["learning"]["linkedXignalEventId"] in {event.event_id for event in learning}
    assert projection["today"]["disposition"] == "READY"
    assert FirstProofStore(service.store.path).latest() == projection


def test_second_plant_is_distinct_private_xeed_same_canonical_org(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _service(tmp_path)
    _install_source(monkeypatch, service)
    first = service.plant(label="First", target_uri="https://axignal.com/")
    second = service.plant(label="Second", target_uri="https://axignal.com/")
    assert first["context"]["id"] != second["context"]["id"]
    assert first["organization"]["id"] == second["organization"]["id"] == "org:axignal"
    assert service.current_projection() == second


def test_persisted_payload_contains_no_demo_or_synthetic_markers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _service(tmp_path)
    _install_source(monkeypatch, service)
    projection = service.plant(label="AXIGNAL first proof", target_uri="https://axignal.com/")
    serialized = json.dumps(projection).lower()
    assert "demo" not in serialized
    assert "synthetic" not in serialized
    assert "sale_probability" not in serialized
    assert "provider_confidence" not in serialized


def test_observed_surface_without_usable_body_is_explicit_insufficient_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service = _service(tmp_path)

    def observe(self, request, policy):
        del self
        return SourceObservation(
            request_id=request.request_id,
            subject_id=request.subject_id,
            observation_slot=request.observation_slot,
            requested_uri=request.target_uri,
            final_uri=request.target_uri,
            retrieved_at=NOW,
            http_status=200,
            content_type="text/html; charset=utf-8",
            body_fingerprint=None,
            body_artifact_ref=None,
            raw_observation_ref=service.artifacts.put_json({"failure": "response_too_large"}),
            observation_fingerprint="sha256:" + "c" * 64,
            instrument_ref="fr30-controlled-http/1",
            policy_id=policy.policy_id,
            policy_fingerprint=policy.fingerprint,
            redirect_chain=(request.target_uri,),
            peer_ips=("203.0.113.10",),
            failure_state="response_too_large",
        )

    monkeypatch.setattr(HttpSourceSensor, "observe", observe)
    with pytest.raises(FirstProofInsufficientEvidence, match="SOURCE_NOT_EVALUABLE"):
        service.plant(label="AXIGNAL first proof", target_uri="https://axignal.com/")
    assert service.current_projection() is None


def _http_runtime(tmp_path: Path):
    config = RuntimeConfig(
        environment="production",
        bind_host="127.0.0.1",
        port=8765,
        code_sha=SHA,
        data_dir=tmp_path / "http-runtime",
        web_root=Path(__file__).resolve().parents[2] / "apps" / "web",
        first_proof_allowed_host="axignal.com",
    )
    runtime = build_runtime(config)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return runtime, server, thread, f"http://{host}:{port}"


def test_runtime_http_first_proof_no_xeed_plant_and_reload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime, server, thread, base = _http_runtime(tmp_path)
    assert runtime.first_proof is not None
    _install_source(monkeypatch, runtime.first_proof)
    try:
        with urllib.request.urlopen(base + "/api/subscriber-context", timeout=3) as response:
            empty = json.loads(response.read())
        assert empty == {"realityLevel": "LIVE_PRODUCTION_FIRST_PROOF", "state": "NO_XEED"}

        body = json.dumps(
            {"label": "HTTP first proof", "targetUri": "https://axignal.com/"}
        ).encode()
        request = urllib.request.Request(
            base + "/api/xeeds", body, {"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 201
            created = json.loads(response.read())
        assert created["lifecycleStatus"] == "LIVE"

        with urllib.request.urlopen(base + "/api/subscriber-context", timeout=3) as response:
            reloaded = json.loads(response.read())
        assert reloaded == created
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_runtime_http_persists_customer_zero_across_full_runtime_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime, server, thread, base = _http_runtime(tmp_path)
    assert runtime.first_proof is not None
    _install_source(monkeypatch, runtime.first_proof)
    try:
        body = json.dumps(
            {"label": "AXIGNAL Customer Zero", "targetUri": "https://axignal.com/"}
        ).encode()
        request = urllib.request.Request(
            base + "/api/xeeds",
            body,
            {"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.status == 201
            created = json.loads(response.read())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    restarted, restarted_server, restarted_thread, restarted_base = _http_runtime(tmp_path)
    assert restarted.first_proof is not None
    try:
        with urllib.request.urlopen(
            restarted_base + "/api/subscriber-context", timeout=3
        ) as response:
            reloaded = json.loads(response.read())

        assert reloaded["context"] == created["context"]
        assert reloaded["organization"] == created["organization"]
        assert reloaded["runtimeCodeSha"] == created["runtimeCodeSha"]
        assert reloaded["reloadContinuity"] == "PERSISTED_RUNTIME_READ_MODEL"
        assert reloaded["nodes"][0]["id"] == created["nodes"][0]["id"]
        assert reloaded["nodes"][0]["observedAt"] == created["nodes"][0]["observedAt"]
        assert reloaded["nodes"][0]["epistemicState"] == "OBSERVED"
        assert reloaded["nodes"][0]["currentness"] == created["nodes"][0]["currentness"]
        assert reloaded["nodes"][0]["sourceRefs"] == ["https://axignal.com/"]
        assert reloaded["nodes"][0]["evidenceNarrative"] == created["nodes"][0]["evidenceNarrative"]
        assert reloaded["today"] == created["today"]
    finally:
        restarted_server.shutdown()
        restarted_server.server_close()
        restarted_thread.join(timeout=3)


def test_runtime_http_distinguishes_invalid_target_and_insufficient_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runtime, server, thread, base = _http_runtime(tmp_path)
    assert runtime.first_proof is not None
    try:
        invalid = urllib.request.Request(
            base + "/api/xeeds",
            json.dumps({"label": "bad", "targetUri": "https://example.com/"}).encode(),
            {"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as invalid_error:
            urllib.request.urlopen(invalid, timeout=3)
        assert invalid_error.value.code == 400

        def observe(self, request, policy):
            del self
            return SourceObservation(
                request_id=request.request_id,
                subject_id=request.subject_id,
                observation_slot=request.observation_slot,
                requested_uri=request.target_uri,
                final_uri=request.target_uri,
                retrieved_at=NOW,
                http_status=200,
                content_type="text/html; charset=utf-8",
                body_fingerprint=None,
                body_artifact_ref=None,
                raw_observation_ref=runtime.first_proof.artifacts.put_json({"failure": "empty"}),
                observation_fingerprint="sha256:" + "d" * 64,
                instrument_ref="fr30-controlled-http/1",
                policy_id=policy.policy_id,
                policy_fingerprint=policy.fingerprint,
                redirect_chain=(request.target_uri,),
                peer_ips=("203.0.113.10",),
                failure_state="empty_body",
            )

        monkeypatch.setattr(HttpSourceSensor, "observe", observe)
        insufficient = urllib.request.Request(
            base + "/api/xeeds",
            json.dumps({"label": "insufficient", "targetUri": "https://axignal.com/"}).encode(),
            {"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as insufficient_error:
            urllib.request.urlopen(insufficient, timeout=3)
        assert insufficient_error.value.code == 422
        payload = json.loads(insufficient_error.value.read())
        assert payload["state"] == "INSUFFICIENT_EVIDENCE"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_fr30_deployment_keeps_first_proof_write_api_loopback_only() -> None:
    root = Path(__file__).resolve().parents[2]
    env = (root / "deploy" / "production" / "runtime.env.example").read_text(encoding="utf-8")
    nginx = (root / "deploy" / "production" / "axignal-landing-nginx.conf").read_text(
        encoding="utf-8"
    )
    app = (root / "apps" / "web" / "subscriber" / "app.js").read_text(encoding="utf-8")

    assert "AXIGNAL_FIRST_PROOF_ALLOWED_HOST=axignal.com" in env
    assert "/api/xeeds" not in nginx
    assert "/api/subscriber-context" not in nginx
    assert "/subscriber" not in nginx
    assert "response.status === 422" in app
    assert "failure.state === 'INSUFFICIENT_EVIDENCE'" in app
    assert "nodeKindForSource" in app
    assert "projectionKey('FAXT'" not in app


def test_current_projection_recomputes_visible_currentness_without_mutating_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.clock = lambda: NOW
    _install_source(monkeypatch, service)
    created = service.plant(
        label="Temporal first proof",
        target_uri="https://axignal.com/",
    )
    stored = FirstProofStore(service.store.path).latest()
    assert stored == created

    recent = service.current_projection(as_of=NOW + timedelta(days=10))
    assert recent == created

    future = service.current_projection(as_of=NOW + timedelta(days=120))
    assert future is not None
    node = future["nodes"][0]
    assert node["currentness"] == "HISTORICAL"
    assert future["today"] == {"disposition": "EMPTY", "items": []}
    relevant_steps = [
        step
        for step in node["evidenceNarrative"]["steps"]
        if step["kind"] in {"XIGNAL", "OBSERVATION", "SOURCE", "CONTRADICTION"}
    ]
    assert relevant_steps
    assert all(step["currentness"] == "HISTORICAL" for step in relevant_steps)

    # Reprojection is derived; the persisted historical snapshot is unchanged.
    assert FirstProofStore(service.store.path).latest() == created
    assert created["nodes"][0]["currentness"] == "CURRENT"
    assert created["today"]["disposition"] == "READY"


def test_fresh_reobservation_restores_current_projection_without_freshening_old_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    service.clock = lambda: NOW
    _install_source(monkeypatch, service)
    first = service.plant(label="First", target_uri="https://axignal.com/")

    future_at = NOW + timedelta(days=120)
    service.clock = lambda: future_at
    aged = service.current_projection()
    assert aged is not None
    assert aged["nodes"][0]["currentness"] == "HISTORICAL"

    second = service.plant(label="Fresh", target_uri="https://axignal.com/")
    assert second["nodes"][0]["currentness"] == "CURRENT"
    assert second["today"]["disposition"] == "READY"
    assert service.current_projection() == second

    observations = service.observation_memory.for_subject("org:axignal")
    assert len(observations) == 2
    assert observations[0].record.observed_at == NOW
    assert observations[1].record.observed_at == future_at
    first_authority = observations[0].reuse_authority
    assert first_authority.currentness.value == "CURRENT"
    assert first_authority.authority_id == "fr30-official-homepage"
    assert first_authority.authority_version == "1"
    assert first_authority.scope.value == "GLOBAL_PUBLIC"
    assert first_authority.reuse_reason
    assert first_authority.retention_policy_ref == "fr30-public-evidence-retention@1"
    assert first_authority.robots_policy_ref == "robots:single-public-root-document:v1"
    assert first_authority.rate_policy_ref == "fr30-public-root-rate@1"
    assert first_authority.provenance_ref is not None
    assert first_authority.provenance_ref.startswith("source-registry:fr30-official-homepage@1:")
    assert first["nodes"][0]["currentness"] == "CURRENT"


def test_http_subscriber_context_reprojects_under_future_runtime_clock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runtime, server, thread, base = _http_runtime(tmp_path)
    assert runtime.first_proof is not None
    runtime.first_proof.clock = lambda: NOW
    _install_source(monkeypatch, runtime.first_proof)
    try:
        body = json.dumps(
            {"label": "Temporal HTTP proof", "targetUri": "https://axignal.com/"}
        ).encode()
        request = urllib.request.Request(
            base + "/api/xeeds",
            body,
            {"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            created = json.loads(response.read())
        assert created["nodes"][0]["currentness"] == "CURRENT"

        runtime.first_proof.clock = lambda: NOW + timedelta(days=120)
        with urllib.request.urlopen(base + "/api/subscriber-context", timeout=3) as response:
            future = json.loads(response.read())

        assert future["nodes"][0]["currentness"] == "HISTORICAL"
        assert future["today"] == {"disposition": "EMPTY", "items": []}
        assert runtime.first_proof.store.latest() == created
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_first_proof_rejects_sensitive_target_before_persisting_any_session(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    secret = "AUDIT_SYNTHETIC_TOKEN"
    target = f"https://axignal.com/?locale=es&access_token={secret}&page=2"

    with pytest.raises(ValueError) as rejected:
        service.plant(label="sensitive", target_uri=target)

    assert secret not in str(rejected.value)
    with sqlite3.connect(service.store.path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM first_proof_sessions").fetchone()[0]
    assert count == 0
    assert secret.encode() not in service.store.path.read_bytes()


def test_first_proof_preserves_safe_query_semantics_in_persisted_public_refs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    _install_source(monkeypatch, service)
    target = "https://axignal.com/?locale=es&page=2&view=overview"

    projection = service.plant(label="safe query", target_uri=target)

    with sqlite3.connect(service.store.path) as connection:
        stored_target = connection.execute(
            "SELECT target_uri FROM first_proof_sessions ORDER BY sequence DESC LIMIT 1"
        ).fetchone()[0]
    assert stored_target == target
    assert target in projection["nodes"][0]["sourceRefs"]
    narrative_refs = [
        step["sourceRef"]
        for step in projection["nodes"][0]["evidenceNarrative"]["steps"]
        if step["sourceRef"] is not None
    ]
    assert target in narrative_refs
