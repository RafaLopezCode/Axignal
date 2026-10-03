from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.admin_api_operations import (
    WebhookOperationsService,
    WebhookReplayConflict,
    canonical_api_inventory,
    project_api_operations,
)
from domain.admin_access import (
    AdminAssurance,
    AdminAuthorizationGrant,
    AdminPrincipalId,
    AdminRole,
    AdminSessionId,
    scopes_for_roles,
)
from domain.admin_api_operations import (
    ApiOperationObservation,
    WebhookDisposition,
)
from pipeline.admin_api_operations import SqliteApiOperationsStore

NOW = datetime(2026, 10, 3, 18, 45, tzinfo=UTC)


def _grant(role: AdminRole = AdminRole.FOUNDER) -> AdminAuthorizationGrant:
    roles = frozenset({role})
    return AdminAuthorizationGrant(
        session_id=AdminSessionId(f"session:{role.value.lower()}"),
        principal_id=AdminPrincipalId(f"admin:{role.value.lower()}"),
        roles=roles,
        scopes=scopes_for_roles(roles),
        assurance=AdminAssurance.STEP_UP,
    )


def test_api_inventory_is_bounded_and_contains_no_arbitrary_request_console() -> None:
    inventory = canonical_api_inventory()
    assert {item.endpoint_id for item in inventory} >= {
        "public.healthz",
        "public.acquisition.events",
        "internal.stripe.webhook",
        "admin.shell",
    }
    rendered = repr(inventory).lower()
    assert "authorization" not in rendered
    assert "credential" not in rendered
    assert "arbitrary" not in rendered


def test_operations_projection_preserves_unknown_metrics_and_classifies_errors(
    tmp_path: Path,
) -> None:
    store = SqliteApiOperationsStore(tmp_path / "ops.sqlite3")
    store.append_observation(
        ApiOperationObservation(
            observation_id="obs:health:1",
            endpoint_id="public.healthz",
            occurred_at=NOW,
            latency_ms=14,
            status_code=200,
        )
    )
    store.append_observation(
        ApiOperationObservation(
            observation_id="obs:health:2",
            endpoint_id="public.healthz",
            occurred_at=NOW + timedelta(seconds=1),
            latency_ms=20,
            status_code=503,
            error_category="DEPENDENCY_UNAVAILABLE",
            quota_remaining=9,
            rate_limited=False,
        )
    )

    projection = project_api_operations(store=store, grant=_grant(), generated_at=NOW)
    health = next(x for x in projection.endpoints if x.endpoint.endpoint_id == "public.healthz")
    unknown = next(x for x in projection.endpoints if x.endpoint.endpoint_id == "public.runtimez")
    assert health.request_count == 2
    assert health.error_count == 1
    assert health.error_rate == 0.5
    assert health.average_latency_ms == 17
    assert health.quota_remaining == 9
    assert unknown.request_count == 0
    assert unknown.error_rate is None
    assert unknown.average_latency_ms is None


class RetryableDependency(RuntimeError):
    pass


def test_webhook_inbox_exact_replay_short_circuits_and_conflicting_payload_fails(
    tmp_path: Path,
) -> None:
    store = SqliteApiOperationsStore(tmp_path / "ops.sqlite3")
    service = WebhookOperationsService(store)
    calls = 0

    def processor() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    envelope, result, replayed = service.receive_and_process(
        integration_id="stripe-billing",
        provider_event_id="evt_1",
        event_type="invoice.paid",
        payload=b'{"id":"evt_1"}',
        schema_version="stripe-event-v1",
        received_at=NOW,
        processor=processor,
    )
    assert envelope.disposition is WebhookDisposition.SUCCEEDED
    assert result == "ok"
    assert replayed is False
    assert calls == 1

    replay, result, replayed = service.receive_and_process(
        integration_id="stripe-billing",
        provider_event_id="evt_1",
        event_type="invoice.paid",
        payload=b'{"id":"evt_1"}',
        schema_version="stripe-event-v1",
        received_at=NOW + timedelta(seconds=1),
        processor=processor,
    )
    assert replay.disposition is WebhookDisposition.SUCCEEDED
    assert result is None
    assert replayed is True
    assert calls == 1

    with pytest.raises(WebhookReplayConflict):
        service.receive_and_process(
            integration_id="stripe-billing",
            provider_event_id="evt_1",
            event_type="invoice.paid",
            payload=b'{"id":"evt_1","changed":true}',
            schema_version="stripe-event-v1",
            received_at=NOW + timedelta(seconds=2),
            processor=processor,
        )


def test_transient_failures_are_bounded_then_dead_lettered_without_payload_storage(
    tmp_path: Path,
) -> None:
    store = SqliteApiOperationsStore(tmp_path / "ops.sqlite3")
    service = WebhookOperationsService(store, max_attempts=3)

    def processor() -> None:
        raise RetryableDependency("provider unavailable; token=must-not-be-stored")

    for attempt in range(1, 4):
        with pytest.raises(RetryableDependency):
            service.receive_and_process(
                integration_id="stripe-billing",
                provider_event_id="evt_retry",
                event_type="invoice.paid",
                payload=b'{"id":"evt_retry","secret":"sensitive-body"}',
                schema_version="stripe-event-v1",
                received_at=NOW + timedelta(minutes=attempt),
                processor=processor,
                transient_exceptions=(RetryableDependency,),
            )
        envelope = store.webhook("stripe-billing", "evt_retry")
        assert envelope is not None
        assert envelope.attempt_count == attempt

    assert envelope.disposition is WebhookDisposition.DEAD_LETTER
    assert envelope.next_retry_at is None
    raw = (tmp_path / "ops.sqlite3").read_bytes()
    assert b"sensitive-body" not in raw
    assert b"must-not-be-stored" not in raw

    projection = project_api_operations(store=store, grant=_grant(), generated_at=NOW)
    assert projection.webhook_dead_letter_count == 1
    assert projection.dead_letters[0].provider_event_id == "evt_retry"


def test_operations_projection_requires_integration_read_scope(tmp_path: Path) -> None:
    store = SqliteApiOperationsStore(tmp_path / "ops.sqlite3")
    with pytest.raises(PermissionError, match="admin:integrations:read"):
        project_api_operations(store=store, grant=_grant(AdminRole.SUPPORT), generated_at=NOW)


def test_runtime_http_emits_ao19_operational_observation(tmp_path: Path) -> None:
    import json
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer

    from tools.runtime.config import RuntimeConfig
    from tools.runtime.service import build_runtime, make_handler

    root = Path(__file__).resolve().parents[2]
    config = RuntimeConfig(
        environment="development",
        bind_host="127.0.0.1",
        port=8765,
        code_sha="a" * 40,
        data_dir=tmp_path / "runtime-data",
        web_root=root / "apps" / "web",
    )
    runtime = build_runtime(config)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/healthz", timeout=3) as response:
            payload = json.loads(response.read())
        assert payload["status"] == "ok"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    observations = runtime.admin_api_operations_store.observations()
    health = tuple(item for item in observations if item.endpoint_id == "public.healthz")
    assert len(health) == 1
    assert health[0].status_code == 200
    assert health[0].latency_ms is not None
    assert health[0].latency_ms >= 0


def test_admin_integrations_surface_contains_ao19_console() -> None:
    root = Path(__file__).resolve().parents[2]
    html = (root / "apps" / "web" / "admin" / "index.html").read_text(encoding="utf-8")
    javascript = (root / "apps" / "web" / "admin" / "admin.js").read_text(encoding="utf-8")
    assert "admin-api-operations-list" in html
    assert "API & Webhook Operations" in html
    assert "bootstrap.apiOperations" in javascript
    assert "Average latency" in javascript
    assert "Quota remaining" in javascript
