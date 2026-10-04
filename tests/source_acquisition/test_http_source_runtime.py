from __future__ import annotations

import http.server
import json
import socket
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest

from application.economic_discovery import (
    DimensionDisposition,
    SemanticPrimitive,
    TypingDimensionContract,
)
from application.source_acquisition import (
    DispatchDisposition,
    SourceDispatchPolicy,
    SourceRequest,
    SourceTargetRule,
    ingest_source_observation,
    public_acquisition_rejection_reason,
    public_source_reference,
)
from pipeline.observation_memory import SqliteObservationMemory
from pipeline.source_acquisition import (
    ContentAddressedArtifactStore,
    HttpSourceSensor,
    PinnedHttpTransport,
    PublicSourcePolicyGate,
    RawHttpResponse,
    ResolvedTarget,
    SourcePolicyRejected,
)

NOW = datetime(2026, 9, 30, 14, 30, tzinfo=UTC)


def _policy(
    *,
    disposition: DispatchDisposition = DispatchDisposition.ALLOW,
    max_response_bytes: int = 2_000_000,
) -> SourceDispatchPolicy:
    return SourceDispatchPolicy(
        policy_id="policy:web-root:v1",
        disposition=disposition,
        decision_basis="public corporate site approved for bounded observation",
        targets=(SourceTargetRule("example.test", "/docs", ("https",)),),
        max_response_bytes=max_response_bytes,
        timeout_ms=1_500,
        max_redirects=2,
    )


def _request(policy: SourceDispatchPolicy) -> SourceRequest:
    return SourceRequest(
        request_id="request:acme:web-root:1",
        subject_id="org:acme",
        observation_slot="website",
        target_uri="https://example.test/docs/company",
        source_type="OFFICIAL_WEB",
        policy_id=policy.policy_id,
        policy_fingerprint=policy.fingerprint,
    )


def _public_dns(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
    return [
        (
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP,
            "",
            ("8.8.8.8", 443),
        )
    ]


def test_policy_resolves_only_explicit_public_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()

    resolved = PublicSourcePolicyGate().resolve(
        "https://example.test/docs/company?locale=en",
        policy,
    )

    assert resolved.host == "example.test"
    assert resolved.addresses == ("8.8.8.8",)
    assert resolved.path_and_query == "/docs/company?locale=en"


@pytest.mark.parametrize(
    ("uri", "reason"),
    [
        ("http://example.test/docs/company", "host_path_or_scheme_not_authorized"),
        ("https://example.test/private", "host_path_or_scheme_not_authorized"),
        ("https://127.0.0.1/docs/company", "ip_literal_not_allowed"),
        ("https://localhost/docs/company", "localhost_not_allowed"),
        ("https://example.test:8443/docs/company", "nonstandard_port"),
        ("https://example.test:80/docs/company", "scheme_port_mismatch"),
        ("https://example.test:invalid/docs/company", "invalid_port"),
        ("https://example.test/docs/%2e%2e/private", "dot_segment_not_allowed"),
        (
            "https://example.test/docs/%252e%252e/private",
            "ambiguous_path_encoding",
        ),
    ],
)
def test_policy_rejects_target_expansion_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    uri: str,
    reason: str,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)

    with pytest.raises(SourcePolicyRejected, match=reason):
        PublicSourcePolicyGate().resolve(uri, _policy())


def test_policy_rejects_nonpublic_dns_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 443))
        ],
    )

    with pytest.raises(SourcePolicyRejected, match="dns_returned_nonpublic_address"):
        PublicSourcePolicyGate().resolve("https://example.test/docs/company", _policy())


def test_denied_policy_performs_no_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_dns(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
        raise AssertionError("DNS must not run for denied policy")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden_dns)

    with pytest.raises(SourcePolicyRejected, match="policy_denied"):
        PublicSourcePolicyGate().resolve(
            "https://example.test/docs/company",
            _policy(disposition=DispatchDisposition.DENY),
        )


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    body = b"<html><p>AXIGNAL fixture observation</p></html>"

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.body)))
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def test_pinned_transport_fetches_exact_validated_address() -> None:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        target = ResolvedTarget(
            uri="http://fixture.test/",
            scheme="http",
            host="fixture.test",
            port=server.server_port,
            path_and_query="/",
            addresses=("127.0.0.1",),
        )

        response = PinnedHttpTransport().fetch(
            target,
            timeout_ms=1_500,
            max_response_bytes=10_000,
        )

        assert response.status == 200
        assert response.peer_ip == "127.0.0.1"
        assert response.body == _FixtureHandler.body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_pinned_transport_fails_closed_on_response_budget() -> None:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        target = ResolvedTarget(
            uri="http://fixture.test/",
            scheme="http",
            host="fixture.test",
            port=server.server_port,
            path_and_query="/",
            addresses=("127.0.0.1",),
        )
        response = PinnedHttpTransport().fetch(
            target,
            timeout_ms=1_500,
            max_response_bytes=8,
        )

        assert response.failure_state == "response_too_large"
        assert response.body == b""
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class _StubTransport(PinnedHttpTransport):
    instrument_ref = "test-pinned-http/1"

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        assert timeout_ms == 1_500
        assert max_response_bytes == 2_000_000
        return RawHttpResponse(
            status=200,
            headers=(("Content-Type", "text/html; charset=utf-8"),),
            body=b"<html><h1>ACME industrial pumps</h1></html>",
            peer_ip=target.addresses[0],
        )


def test_sensor_preserves_raw_body_policy_and_instrument(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=_StubTransport(),
        artifacts=store,
        clock=lambda: NOW,
    )

    observation = sensor.observe(_request(policy), policy)
    envelope = json.loads(store.read(observation.raw_observation_ref))

    assert observation.body_artifact_ref is not None
    assert (
        store.read(observation.body_artifact_ref) == b"<html><h1>ACME industrial pumps</h1></html>"
    )
    assert observation.policy_fingerprint == policy.fingerprint
    assert observation.instrument_ref == "test-pinned-http/1"
    assert observation.peer_ips == ("8.8.8.8",)
    assert envelope["policy"]["policy_fingerprint"] == policy.fingerprint
    assert envelope["instrument_ref"] == "test-pinned-http/1"


def test_source_observation_flows_into_memory_and_brain_without_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()
    request = _request(policy)
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=_StubTransport(),
        artifacts=ContentAddressedArtifactStore(tmp_path / "artifacts"),
        clock=lambda: NOW,
    )
    observation = sensor.observe(request, policy)
    contract = TypingDimensionContract(
        dimension_id="website-currentness",
        version="1",
        semantic_target="website currentness",
        primitive=SemanticPrimitive.CHOICE,
        question="Is the website observation available for semantic evaluation?",
        state_requirements=("source.website.content_fingerprint",),
        dependencies=("source.website.content_fingerprint",),
        mutually_exclusive=True,
        abstention_policy="abstain when source content is unavailable",
    )

    result = ingest_source_observation(
        memory=SqliteObservationMemory(tmp_path / "observation-memory.sqlite3"),
        request=request,
        observation=observation,
        contracts=(contract,),
    )

    assert result.mutation.change is not None
    assert "source.website.content_fingerprint" in result.mutation.change.changed_fields
    assert result.work_plan is not None
    assert result.work_plan.retrieval_required is False
    assert result.work_plan.state_mutation_required is True
    assert result.work_plan.research_dimensions == ()
    assert len(result.work_plan.evaluation) == 1
    assert result.work_plan.evaluation[0].disposition is DimensionDisposition.ANSWERABLE


def test_exact_source_replay_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()
    request = _request(policy)
    memory = SqliteObservationMemory(tmp_path / "observation-memory.sqlite3")
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=_StubTransport(),
        artifacts=ContentAddressedArtifactStore(tmp_path / "artifacts"),
        clock=lambda: NOW,
    )
    observation = sensor.observe(request, policy)

    first = ingest_source_observation(
        memory=memory,
        request=request,
        observation=observation,
        contracts=(),
    )
    replay = ingest_source_observation(
        memory=memory,
        request=request,
        observation=observation,
        contracts=(),
    )

    assert first.mutation.inserted is True
    assert replay.mutation.inserted is False
    assert replay.mutation.change is None
    assert replay.work_plan is None


class _RedirectEscapeTransport(PinnedHttpTransport):
    instrument_ref = "test-pinned-http/redirect"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        self.calls += 1
        return RawHttpResponse(
            status=302,
            headers=(("Location", "https://evil.test/private"),),
            body=b"",
            peer_ip=target.addresses[0],
        )


def test_redirect_is_reauthorized_and_cannot_escape_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()
    transport = _RedirectEscapeTransport()
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=transport,
        artifacts=ContentAddressedArtifactStore(tmp_path / "artifacts"),
        clock=lambda: NOW,
    )

    observation = sensor.observe(_request(policy), policy)

    assert transport.calls == 1
    assert observation.failure_state == "redirect_policy_rejected"
    assert observation.redirect_chain == ("https://example.test/docs/company",)
    assert observation.final_uri == "https://example.test/docs/company"
    assert observation.peer_ips == ("8.8.8.8",)


def test_request_policy_fingerprint_mismatch_fails_before_dns(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def forbidden_dns(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
        raise AssertionError("DNS must not run for a policy fingerprint mismatch")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden_dns)
    policy = _policy()
    request = SourceRequest(
        request_id="request:bad-policy",
        subject_id="org:acme",
        observation_slot="website",
        target_uri="https://example.test/docs/company",
        source_type="OFFICIAL_WEB",
        policy_id=policy.policy_id,
        policy_fingerprint="sha256:not-the-policy",
    )
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=_StubTransport(),
        artifacts=ContentAddressedArtifactStore(tmp_path / "artifacts"),
        clock=lambda: NOW,
    )

    with pytest.raises(SourcePolicyRejected, match="request_policy_fingerprint_mismatch"):
        sensor.observe(request, policy)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.test/docs/company?access_token=AUDIT_SYNTHETIC_TOKEN",
        "https://example.test/docs/company?api_key=AUDIT_SYNTHETIC_KEY",
        "https://example.test/docs/company?password=AUDIT_SYNTHETIC_PASSWORD",
        "https://example.test/docs/company?client_secret=AUDIT_SYNTHETIC_SECRET",
        "https://example.test/docs/company?X-Amz-Signature=AUDIT_SYNTHETIC_SIGNATURE",
        "https://example.test/docs/company?%61ccess_token=AUDIT_SYNTHETIC_TOKEN",
        "https://user:AUDIT_SYNTHETIC_PASSWORD@example.test/docs/company",
    ],
)
def test_sensitive_public_target_is_rejected_before_dns_or_cas(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    uri: str,
) -> None:
    def forbidden_dns(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
        raise AssertionError("sensitive public URI must fail before DNS")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden_dns)
    policy = _policy()
    request = SourceRequest(
        request_id="request:sensitive",
        subject_id="org:acme",
        observation_slot="website",
        target_uri=uri,
        source_type="OFFICIAL_WEB",
        policy_id=policy.policy_id,
        policy_fingerprint=policy.fingerprint,
    )
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=_StubTransport(),
        artifacts=store,
        clock=lambda: NOW,
    )

    with pytest.raises(SourcePolicyRejected) as rejected:
        sensor.observe(request, policy)

    rendered_error = str(rejected.value)
    assert "AUDIT_SYNTHETIC" not in rendered_error
    assert list((tmp_path / "artifacts").rglob("*")) == []


def test_safe_query_parameters_are_preserved_exactly_for_traceability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    uri = "https://example.test/docs/company?locale=es&page=2&category=industrial%20pumps"

    resolved = PublicSourcePolicyGate().resolve(uri, _policy())

    assert resolved.uri == uri
    assert resolved.path_and_query == "/docs/company?locale=es&page=2&category=industrial%20pumps"
    assert public_acquisition_rejection_reason(uri) is None
    assert public_source_reference(uri) == uri


def test_public_source_reference_redacts_only_sensitive_material() -> None:
    contaminated = (
        "https://user:AUDIT_SYNTHETIC_PASSWORD@example.test/docs/company"
        "?locale=es&access_token=AUDIT_SYNTHETIC_TOKEN&page=2"
        "&api_key=AUDIT_SYNTHETIC_KEY"
    )

    safe = public_source_reference(contaminated)

    assert safe == "https://example.test/docs/company?locale=es&page=2"
    assert "AUDIT_SYNTHETIC" not in safe
    assert "access_token" not in safe
    assert "api_key" not in safe


class _SensitiveRedirectTransport(PinnedHttpTransport):
    instrument_ref = "test-pinned-http/sensitive-redirect"

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def fetch(
        self,
        target: ResolvedTarget,
        *,
        timeout_ms: int,
        max_response_bytes: int,
    ) -> RawHttpResponse:
        self.calls += 1
        if self.calls == 1:
            return RawHttpResponse(
                status=302,
                headers=(
                    (
                        "Location",
                        "/docs/company?locale=es&access_token=AUDIT_SYNTHETIC_TOKEN",
                    ),
                ),
                body=b"",
                peer_ip=target.addresses[0],
            )
        raise AssertionError("sensitive redirect must never be fetched")


def test_sensitive_redirect_fails_closed_without_persisting_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    policy = _policy()
    store = ContentAddressedArtifactStore(tmp_path / "artifacts")
    transport = _SensitiveRedirectTransport()
    sensor = HttpSourceSensor(
        policy_gate=PublicSourcePolicyGate(),
        transport=transport,
        artifacts=store,
        clock=lambda: NOW,
    )

    observation = sensor.observe(_request(policy), policy)
    envelope = store.read(observation.raw_observation_ref).decode()

    assert transport.calls == 1
    assert observation.failure_state == "redirect_policy_rejected"
    assert observation.redirect_chain == ("https://example.test/docs/company",)
    assert observation.final_uri == "https://example.test/docs/company"
    assert "AUDIT_SYNTHETIC_TOKEN" not in envelope
    assert "access_token" not in envelope
