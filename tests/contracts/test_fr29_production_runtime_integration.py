from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from tools.runtime.config import RuntimeConfig
from tools.runtime.probe import run_probe
from tools.runtime.service import build_runtime, make_handler

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "apps" / "web"
SHA = "a" * 40


def _config(tmp_path: Path, *, environment: str = "production") -> RuntimeConfig:
    return RuntimeConfig(
        environment=environment,
        bind_host="127.0.0.1",
        port=8765,
        code_sha=SHA,
        data_dir=tmp_path / "runtime-data",
        web_root=WEB_ROOT,
    )


def test_production_config_fails_closed_without_exact_sha_or_loopback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AXIGNAL_ENV", "production")
    monkeypatch.setenv("AXIGNAL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("AXIGNAL_WEB_ROOT", str(WEB_ROOT))
    monkeypatch.delenv("AXIGNAL_CODE_SHA", raising=False)
    with pytest.raises(ValueError, match="AXIGNAL_CODE_SHA"):
        RuntimeConfig.from_env()

    monkeypatch.setenv("AXIGNAL_CODE_SHA", SHA)
    monkeypatch.setenv("AXIGNAL_BIND_HOST", "0.0.0.0")
    monkeypatch.delenv("AXIGNAL_CONTAINERIZED", raising=False)
    with pytest.raises(ValueError, match="loopback"):
        RuntimeConfig.from_env()

    monkeypatch.setenv("AXIGNAL_CONTAINERIZED", "true")
    config = RuntimeConfig.from_env()
    assert config.bind_host == "0.0.0.0"
    assert config.containerized is True

    monkeypatch.setenv("AXIGNAL_BIND_HOST", "192.0.2.10")
    with pytest.raises(ValueError, match="loopback"):
        RuntimeConfig.from_env()


def test_runtime_builds_real_durable_observation_and_learning_stores(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    payload = runtime.health_payload()

    assert payload["status"] == "ok"
    assert payload["code_sha"] == SHA
    assert payload["write_surface"] == "closed"
    assert runtime.observation_db.is_file()
    assert runtime.research_work_db.is_file()
    assert runtime.learning_db.is_file()
    assert payload["persistence"] == {
        "observation_memory": {"status": "ok"},
        "research_work_memory": {"status": "ok"},
        "learning_memory": {"status": "ok"},
    }
    detailed = runtime.health_payload(detailed=True)
    assert detailed["persistence"] == {
        "observation_memory": {"status": "ok", "rows": 0},
        "research_work_memory": {"status": "ok", "rows": 0},
        "learning_memory": {"status": "ok", "rows": 0},
    }


def test_isolated_probe_uses_production_adapters_and_survives_reopen(tmp_path: Path) -> None:
    probe_dir = tmp_path / "probe"
    first = run_probe(probe_dir=probe_dir, code_sha=SHA)
    second = run_probe(probe_dir=probe_dir, code_sha=SHA)

    assert first["status"] == "ok"
    assert first["observation_append"] == "created"
    assert first["learning_append"] == "created"
    assert first["observation_reopen"] == "ok"
    assert first["learning_reopen"] == "ok"
    assert second["observation_append"] == "idempotent-replay"
    assert second["learning_append"] == "idempotent-replay"


def test_http_runtime_serves_health_ui_and_rejects_public_writes(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        with urllib.request.urlopen(base + "/healthz", timeout=3) as response:
            health = json.loads(response.read())
        assert health["status"] == "ok"
        assert health["code_sha"] == SHA

        with urllib.request.urlopen(base + "/runtimez", timeout=3) as response:
            runtime_payload = json.loads(response.read())
        assert runtime_payload["capabilities"]["public_write_api"] is False
        assert runtime_payload["persistence"]["observation_memory"]["rows"] == 0
        assert runtime_payload["persistence"]["learning_memory"]["rows"] == 0
        assert runtime_payload["capabilities"]["first_xeed_runtime"] == (
            "application-contract-loaded"
        )

        with urllib.request.urlopen(base + "/", timeout=3) as response:
            landing = response.read().decode("utf-8")
        assert "Observe the economic world from the outside" in landing

        for path in (
            "/subscriber/",
            "/subscriber.css",
            "/brand/logo-light.svg",
            "/design-system/global.css",
            "/assets/icons/lucide/axignal-ui.svg",
        ):
            with urllib.request.urlopen(base + path, timeout=3) as response:
                assert response.status == 200

        request = urllib.request.Request(base + "/runtimez", data=b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(request, timeout=3)
        assert exc_info.value.code == 405
        rejected = json.loads(exc_info.value.read())
        assert rejected == {"reason": "PUBLIC_WRITE_SURFACE_CLOSED", "status": "rejected"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_runtime_static_router_rejects_path_traversal(tmp_path: Path) -> None:
    runtime = build_runtime(_config(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"http://{host}:{port}/landing/../../pyproject.toml", timeout=3)
        assert exc_info.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_production_topology_keeps_axignal_isolated_on_loopback() -> None:
    unit = (ROOT / "deploy" / "production" / "axignal-runtime.service").read_text(encoding="utf-8")
    env = (ROOT / "deploy" / "production" / "runtime.env.example").read_text(encoding="utf-8")
    nginx = (ROOT / "deploy" / "production" / "axignal-landing-nginx.conf").read_text(
        encoding="utf-8"
    )

    assert "User=www-data" in unit
    assert "ReadWritePaths=/var/lib/axignal/runtime" in unit
    assert "AXIGNAL_BIND_HOST=127.0.0.1" in env
    assert "AXIGNAL_PORT=18181" in env
    assert "AXIGNAL_CODE_SHA=REPLACE_WITH_EXACT_MAIN_SHA" in env
    assert "listen 127.0.0.1:18180;" in nginx
    assert "server 127.0.0.1:18181;" in nginx
    assert "proxy_pass http://axignal_runtime/healthz;" in nginx
    assert "/runtimez" not in nginx
    assert "/subscriber" not in nginx
    assert "/app.js" not in nginx
    assert "3000" not in nginx
    assert "5432" not in nginx
