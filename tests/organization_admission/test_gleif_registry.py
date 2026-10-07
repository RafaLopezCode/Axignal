"""Recorded public GLEIF response through the real sensor, parser and admission seam."""

from __future__ import annotations

import gzip
import json
import logging
import sqlite3
import ssl
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest

from application.organization_admission.locator import parse_locator
from application.organization_admission.service import (
    OrganizationAdmissionService,
    RegistryLookupStatus,
    prepare_admission,
)
from pipeline.entity_resolution.gleif_registry import (
    BASE,
    PARSER,
    RIGHTS,
    GLEIFRegistryIdentitySource,
)
from pipeline.entity_resolution.organization_store import SqliteCanonicalOrganizationStore
from pipeline.entity_resolution.sqlite_store import SqliteIdentityGovernanceStore
from pipeline.source_acquisition import (
    ContentAddressedArtifactIntegrityAdapter,
    ContentAddressedArtifactStore,
)
from pipeline.source_acquisition.http_sensor import HttpSourceSensor
from pipeline.source_acquisition.http_transport import (
    PinnedHttpTransport,
    RawHttpResponse,
    SourceDeadlineExceeded,
)
from pipeline.source_acquisition.policy import PublicSourcePolicyGate, ResolvedTarget
from tests.integration.test_organization_admission_e2e import (
    _add,
    _focuses,
    _organizations,
    _pilot,
    _portfolio,
)
from tests.integration.test_subscriber_composition import _build
from tools.runtime.organization_registry import build_registry_source
from tools.runtime.subscriber_configuration import load_subscriber_settings

LEI = "5493001KJTIIGC8Y1R12"
NOW = datetime(2026, 10, 7, 12, tzinfo=UTC)
BODY = (Path(__file__).parent / "fixtures" / f"gleif-{LEI}.json").read_bytes()


class Transport(PinnedHttpTransport):
    def __init__(
        self,
        body: bytes = BODY,
        status: int = 200,
        failure: str | None = None,
        exception: Exception | None = None,
        headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        super().__init__()
        self.calls = 0
        self.exception = exception
        self.response = RawHttpResponse(
            status,
            (("Content-Type", "application/vnd.api+json"), *headers),
            body,
            "1.1.1.1",
            failure,
        )

    def fetch(
        self, target: ResolvedTarget, *, timeout_ms: int, max_response_bytes: int
    ) -> RawHttpResponse:
        self.calls += 1
        assert (
            target.uri.startswith(BASE)
            and target.host == "api.gleif.org"
            and target.scheme == "https"
        )
        assert max_response_bytes == 262144 and timeout_ms <= 5000
        if self.exception:
            raise self.exception
        return self.response


@pytest.fixture(autouse=True)
def public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("1.1.1.1", 443))])


def source(
    root: Path, transport: Transport | None = None, clock=None
) -> GLEIFRegistryIdentitySource:
    root.mkdir(exist_ok=True)
    artifacts = ContentAddressedArtifactStore(root / "artifacts")
    effective = clock or (lambda: NOW)
    return GLEIFRegistryIdentitySource(
        sensor=HttpSourceSensor(
            policy_gate=PublicSourcePolicyGate(),
            transport=transport or Transport(),
            artifacts=artifacts,
            clock=effective,
        ),
        artifacts=artifacts,
        database=root / "gleif-registry.sqlite3",
        clock=effective,
    )


def lookup(provider: GLEIFRegistryIdentitySource):
    return provider.lookup(parse_locator("LEI " + LEI))


def test_exact_record_is_grounded_registry_evidence_with_raw_snapshot(tmp_path: Path) -> None:
    provider = source(tmp_path)
    result = lookup(provider)
    assert result.status is RegistryLookupStatus.FOUND and len(result.records) == 1
    record = result.records[0]
    assert record.legal_name.object_or_value == "Bloomberg Finance L.P."
    assert not record.official_websites
    assert prepare_admission(record) is not None
    representation = record.legal_name.evidence.representation
    assert representation is not None
    assert provider.artifacts.read(representation.source_artifact_ref) == BODY
    metadata = json.loads(provider.artifacts.read(representation.source_observation_artifact_ref))
    assert (
        metadata["parser"],
        metadata["rights"],
        metadata["license"],
        metadata["query_identifier"],
    ) == (PARSER, RIGHTS, "CC0-1.0", LEI)
    assert record.legal_name.evidence.observed_at == NOW


@pytest.mark.parametrize(
    "kwargs",
    [
        {"status": 429},
        {"status": 500},
        {"status": 403},
        {"exception": SourceDeadlineExceeded()},
        {"exception": ssl.SSLError()},
        {"body": b"{"},
        {"body": b'{"data":{},"data":{}}'},
        {"body": b"\xff"},
        {"body": gzip.compress(BODY)},
        {"body": b"x" * 262145, "failure": "response_too_large"},
        {"status": 302, "headers": (("Location", "https://evil.example/"),)},
        {"status": 404, "body": b"{}"},
        {"status": 200, "body": b'{"data":[]}'},
    ],
)
def test_source_errors_are_unavailable_not_absence(tmp_path: Path, kwargs: dict) -> None:
    transport = Transport(**kwargs)
    assert lookup(source(tmp_path, transport)).status is RegistryLookupStatus.UNAVAILABLE
    assert transport.calls == 1


@pytest.mark.parametrize(
    "mutator",
    [
        "identifier",
        "type",
        "inactive",
        "lapsed",
        "renewal",
        "future",
        "html",
        "surrogate",
        "multiple",
    ],
)
def test_schema_subject_and_currentness_fail_closed(tmp_path: Path, mutator: str) -> None:
    payload = json.loads(BODY)
    data = payload["data"]
    attrs = data["attributes"]
    if mutator == "identifier":
        attrs["lei"] = "WRONG"
    if mutator == "type":
        data["type"] = "unknown"
    if mutator == "inactive":
        attrs["entity"]["status"] = "INACTIVE"
    if mutator == "lapsed":
        attrs["registration"]["status"] = "LAPSED"
    if mutator == "renewal":
        attrs["registration"]["nextRenewalDate"] = "2020-01-01T00:00:00Z"
    if mutator == "future":
        attrs["registration"]["lastUpdateDate"] = "2030-01-01T00:00:00Z"
    if mutator == "html":
        attrs["entity"]["legalName"]["name"] = "<script>"
    if mutator == "surrogate":
        attrs["entity"]["legalName"]["name"] = "bad\ud800"
    if mutator == "multiple":
        payload["data"] = [data, data]
    assert (
        lookup(source(tmp_path, Transport(json.dumps(payload).encode()))).status
        is RegistryLookupStatus.UNAVAILABLE
    )


def test_reliable_404_only_and_not_cached(tmp_path: Path) -> None:
    transport = Transport(b'{"errors":[{"status":"404","title":"Not Found"}]}', 404)
    provider = source(tmp_path, transport)
    assert lookup(provider).status is lookup(provider).status is RegistryLookupStatus.NOT_FOUND
    assert transport.calls == 2


def test_unsupported_coverage_and_invalid_input_never_dispatch(tmp_path: Path) -> None:
    transport = Transport()
    provider = source(tmp_path, transport)
    for locator in ("Acme SL", "https://www.acme.com", "LEI " + LEI + " https://www.acme.com"):
        assert provider.lookup(parse_locator(locator)).status is RegistryLookupStatus.UNAVAILABLE
    service = OrganizationAdmissionService(index=None, source=provider)
    assert service.decide("LEI 5493001KJTIIGC8Y1R13").status.value == "INVALID_INPUT"
    assert transport.calls == 0


def test_cache_is_versioned_current_bounded_and_integrity_checked(tmp_path: Path) -> None:
    clock = [NOW]
    transport = Transport()
    provider = source(tmp_path, transport, lambda: clock[0])
    first = lookup(provider)
    assert lookup(provider).records == first.records and transport.calls == 1
    clock[0] += timedelta(hours=1, seconds=1)
    assert lookup(provider).status is RegistryLookupStatus.FOUND and transport.calls == 2
    record = first.records[0]
    rep = record.legal_name.evidence.representation
    assert rep is not None
    digest = provider.artifacts.digest(rep.source_artifact_ref)
    (tmp_path / "artifacts" / digest[:2] / digest).write_bytes(b"corrupted")
    assert lookup(provider).status is RegistryLookupStatus.UNAVAILABLE


def test_persistent_rate_limit_denies_before_transport(tmp_path: Path) -> None:
    transport = Transport(b'{"errors":[{"status":"404"}]}', 404)
    provider = source(tmp_path, transport)
    for _ in range(30):
        assert lookup(provider).status is RegistryLookupStatus.NOT_FOUND
    assert lookup(provider).status is RegistryLookupStatus.UNAVAILABLE
    assert transport.calls == 30
    assert lookup(source(tmp_path, transport)).status is RegistryLookupStatus.UNAVAILABLE


def test_corrupted_raw_artifact_cannot_enter_canonical_store(tmp_path: Path) -> None:
    provider = source(tmp_path)
    record = lookup(provider).records[0]
    rep = record.legal_name.evidence.representation
    assert rep is not None
    digest = provider.artifacts.digest(rep.source_artifact_ref)
    (tmp_path / "artifacts" / digest[:2] / digest).write_bytes(b"corrupted")
    store = SqliteCanonicalOrganizationStore(
        tmp_path / "canonical.sqlite3",
        integrity=ContentAddressedArtifactIntegrityAdapter(provider.artifacts),
        governance=SqliteIdentityGovernanceStore(tmp_path / "governance.sqlite3"),
    )
    admission = prepare_admission(record)
    assert admission is not None
    with pytest.raises(ValueError):
        store.admit(*admission)
    assert (
        sqlite3.connect(tmp_path / "canonical.sqlite3")
        .execute("select count(*) from canonical_legal_identities")
        .fetchone()[0]
        == 0
    )


def test_config_requires_provider_and_explicit_rights_acknowledgement(tmp_path: Path) -> None:
    for values in (
        {},
        {"AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "gleif"},
        {
            "AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "other",
            "AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS": RIGHTS,
        },
    ):
        assert (
            build_registry_source(values, tmp_path).lookup(parse_locator("LEI " + LEI)).status
            is RegistryLookupStatus.UNAVAILABLE
        )
    values = {
        "AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "gleif",
        "AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS": RIGHTS,
    }
    settings = load_subscriber_settings(values)
    assert isinstance(build_registry_source(settings.values, tmp_path), GLEIFRegistryIdentitySource)


def test_real_adapter_pilot_admission_restart_and_concurrent_private_foci(tmp_path: Path) -> None:
    provider = source(tmp_path)
    facade = _build(tmp_path, pilot=True, identity_source=provider)
    token_a, _ = _pilot(facade, tmp_path, "gleif:a")
    token_b, _ = _pilot(facade, tmp_path, "gleif:b")
    gate = Barrier(2)

    def add(token: str, ref: str):
        gate.wait(timeout=10)
        return _add(facade, token, ref, "LEI " + LEI)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(add, token_a, "gleif:add:a")
        b = pool.submit(add, token_b, "gleif:add:b")
        added_a, added_b = a.result(timeout=30), b.result(timeout=30)
    assert added_a.body["state"] == added_b.body["state"] == "CREATED"
    assert added_a.body["organizationId"] == added_b.body["organizationId"]
    assert added_a.body["focusId"] != added_b.body["focusId"]
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 2)
    restarted = _build(tmp_path, pilot=True, identity_source=source(tmp_path))
    assert _portfolio(restarted, token_a)[0]["focusId"] == added_a.body["focusId"]
    denied = restarted.handle(
        "GET",
        f"/subscriber/organizations/{added_a.body['focusId']}/output",
        {"Origin": "https://axignal.com", "Authorization": "Bearer " + token_b},
    )
    assert denied.status in (403, 404)


def test_real_adapter_unavailable_keeps_identity_pending_without_focus(tmp_path: Path) -> None:
    facade = _build(tmp_path, pilot=True, identity_source=source(tmp_path, Transport(status=500)))
    token, _ = _pilot(facade, tmp_path, "gleif:offline")
    added = _add(facade, token, "gleif:offline:add", "LEI " + LEI)
    assert (
        added.body["state"] == "IDENTITY_PENDING"
        and added.body["reason"] == "IDENTITY_SOURCE_UNAVAILABLE"
    )
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (0, 0)


def test_production_settings_select_adapter_without_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.integration import test_subscriber_composition as composition

    original = composition._settings

    def configured(*args, **kwargs):
        settings = original(*args, **kwargs)
        return replace(
            settings,
            values={
                **settings.values,
                "AXIGNAL_ORGANIZATION_REGISTRY_PROVIDER": "gleif",
                "AXIGNAL_ORGANIZATION_REGISTRY_RIGHTS": RIGHTS,
            },
        )

    monkeypatch.setattr(composition, "_settings", configured)
    monkeypatch.setattr("tools.runtime.organization_registry.PinnedHttpTransport", Transport)
    facade = _build(tmp_path, pilot=True)
    token, _ = _pilot(facade, tmp_path, "gleif:configured")
    assert _add(facade, token, "gleif:configured:add", "LEI " + LEI).body["state"] == "CREATED"
    assert (_organizations(tmp_path), _focuses(tmp_path)) == (1, 1)


def test_private_dns_and_unexpected_content_type_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport = Transport()
    provider = source(tmp_path, transport)
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 443))])
    assert lookup(provider).status is RegistryLookupStatus.UNAVAILABLE and transport.calls == 0
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("1.1.1.1", 443))])
    transport.response = replace(transport.response, headers=(("Content-Type", "text/html"),))
    assert lookup(provider).status is RegistryLookupStatus.UNAVAILABLE and transport.calls == 1


def test_daily_limit_is_persistent_and_logs_omit_identifier(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    transport = Transport()
    provider = source(tmp_path, transport)
    with sqlite3.connect(provider.database) as db:
        db.executemany(
            "INSERT INTO gleif_attempts VALUES (?)",
            [((NOW - timedelta(hours=2)).isoformat(),)] * 500,
        )
    with caplog.at_level(logging.INFO):
        assert lookup(provider).status is RegistryLookupStatus.UNAVAILABLE
    assert transport.calls == 0
    assert (
        "LOCAL_LIMIT" in caplog.text and LEI not in caplog.text and "Bloomberg" not in caplog.text
    )
