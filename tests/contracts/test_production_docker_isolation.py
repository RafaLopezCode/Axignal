from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = (ROOT / "deploy" / "production" / "compose.yml").read_text(encoding="utf-8")
RUNTIME_DOCKERFILE = (ROOT / "deploy" / "production" / "docker" / "runtime.Dockerfile").read_text(
    encoding="utf-8"
)
LANDING_DOCKERFILE = (ROOT / "deploy" / "production" / "docker" / "landing.Dockerfile").read_text(
    encoding="utf-8"
)
LANDING_NGINX = (ROOT / "deploy" / "production" / "docker" / "landing-nginx.conf").read_text(
    encoding="utf-8"
)
ADR = (
    ROOT / "docs" / "adr" / "ADR-0059-axignal-production-project-owned-docker-isolation.md"
).read_text(encoding="utf-8")
RUNBOOK = (ROOT / "docs" / "operations" / "AXIGNAL_DOCKER_PRODUCTION_MIGRATION.md").read_text(
    encoding="utf-8"
)


def test_axignal_compose_owns_project_specific_containers_and_network() -> None:
    assert "name: axignal-prod" in COMPOSE
    assert "container_name: axignal-prod-runtime" in COMPOSE
    assert "container_name: axignal-prod-landing" in COMPOSE
    assert "name: axignal_prod_internal" in COMPOSE
    assert "axignal-pilot" not in COMPOSE
    assert "axignal-pr259-preview" not in COMPOSE
    assert "merxat" not in COMPOSE.lower()
    assert "inkdie" not in COMPOSE.lower()


def test_runtime_is_private_to_docker_network_and_landing_is_loopback_only() -> None:
    assert 'AXIGNAL_CONTAINERIZED: "true"' in COMPOSE
    assert "AXIGNAL_BIND_HOST: 0.0.0.0" in COMPOSE
    assert 'AXIGNAL_PORT: "18181"' in COMPOSE
    assert '      - "18181"' in COMPOSE
    assert '      - "127.0.0.1:18180:8080"' in COMPOSE
    assert "server runtime:18181;" in LANDING_NGINX
    assert "listen 8080;" in LANDING_NGINX

    runtime_section, landing_section = COMPOSE.split("  landing:", maxsplit=1)
    assert "ports:" not in runtime_section
    assert "expose:" in runtime_section
    assert "ports:" in landing_section
    assert "18181:" not in landing_section


def test_runtime_preserves_existing_host_persistence_and_runs_hardened() -> None:
    assert "/var/lib/axignal/runtime:/var/lib/axignal/runtime" in COMPOSE
    assert "read_only: true" in COMPOSE
    assert "cap_drop:" in COMPOSE
    assert "no-new-privileges:true" in COMPOSE
    assert 'user: "33:33"' in COMPOSE
    assert "pids_limit:" in COMPOSE
    assert "mem_limit:" in COMPOSE
    assert "max-size: 10m" in COMPOSE
    assert "USER 33:33" in RUNTIME_DOCKERFILE


def test_landing_image_is_non_root_read_only_and_contains_public_surfaces() -> None:
    assert "FROM nginx:1.27-alpine" in LANDING_DOCKERFILE
    assert "COPY apps/web/landing/" in LANDING_DOCKERFILE
    assert "COPY apps/web/knowledge/" in LANDING_DOCKERFILE
    assert "USER nginx" in LANDING_DOCKERFILE
    assert "read_only: true" in COMPOSE
    assert "location = /healthz" in LANDING_NGINX
    assert "/runtimez" not in LANDING_NGINX
    assert "/admin" not in LANDING_NGINX


def test_images_and_runtime_require_exact_canonical_sha() -> None:
    marker = "AXIGNAL_CODE_SHA: $" + "{AXIGNAL_CODE_SHA:?AXIGNAL_CODE_SHA is required}"
    assert marker in COMPOSE
    assert "org.opencontainers.image.revision" in RUNTIME_DOCKERFILE
    assert "org.opencontainers.image.revision" in LANDING_DOCKERFILE


def test_adr_and_runbook_keep_systemd_only_as_rollback() -> None:
    assert "**Status:** ACCEPTED" in ADR
    assert "systemd unit files remain installed as a rollback path" in ADR
    assert "disabled after successful Docker cutover" in ADR
    assert "docker compose -p axignal-prod" in RUNBOOK
    assert "systemctl enable --now axignal-runtime.service" in RUNBOOK
    assert "systemctl enable --now axignal-landing.service" in RUNBOOK
    assert "does not delete `/var/lib/axignal/runtime`" in RUNBOOK


def test_runbook_records_completed_production_docker_cutover() -> None:
    assert "## Production cutover evidence — 2026-10-02" in RUNBOOK
    assert "axignal-prod-runtime" in RUNBOOK
    assert "axignal-prod-landing" in RUNBOOK
    assert "axignal_prod_internal" in RUNBOOK
    assert "runtime host-published ports: **none**" in RUNBOOK
    assert "systemd runtime/landing: `inactive/disabled`" in RUNBOOK
    assert "Persistence before and after cutover was identical" in RUNBOOK
    assert "rollback automatically" in RUNBOOK
