# ADR-0059 — AXIGNAL Production Runs in Project-Owned Docker Isolation

**Status:** ACCEPTED
**Date:** 2026-10-02

## Context

AXIGNAL production originally ran as two host-level systemd services:

- `axignal-landing.service` on `127.0.0.1:18180`;
- `axignal-runtime.service` on `127.0.0.1:18181`.

That topology preserved project-specific ports, directories and persistence, but process and dependency isolation remained host-level. The KVM2 already runs Docker for unrelated projects. AXIGNAL MUST NOT reuse their containers, networks, volumes, ports or lifecycle.

Historical Docker networks whose names contain AXIGNAL but belong to old pilot/preview environments are not production authority and MUST NOT be reused.

## Decision

AXIGNAL production execution is owned by one Compose project named `axignal-prod`.

The production graph is:

```text
Internet
  -> existing host Traefik :80/:443
  -> host loopback 127.0.0.1:18180
  -> axignal-prod-landing:8080
       -> dedicated Docker network axignal_prod_internal
       -> axignal-prod-runtime:18181
            -> bind-mounted /var/lib/axignal/runtime
```

Rules:

1. Only the Landing container publishes a host port, and it publishes **only** `127.0.0.1:18180`.
2. Runtime publishes no host port. `18181` is Docker-network-only.
3. Runtime may bind `0.0.0.0` in production only when `AXIGNAL_CONTAINERIZED=true`. Non-containerized production retains the loopback-only fail-closed rule.
4. AXIGNAL gets a dedicated bridge network `axignal_prod_internal`; unrelated Docker networks are never reused.
5. Existing canonical persistence stays at `/var/lib/axignal/runtime` and is bind-mounted read/write into the runtime container. Data is not copied into an image or deleted during rollback.
6. Images are built from an exact green canonical main SHA and carry that SHA as OCI revision metadata and runtime `AXIGNAL_CODE_SHA`.
7. Both containers run read-only filesystems, drop all Linux capabilities, enable `no-new-privileges`, cap PIDs/memory/CPU and rotate local container logs.
8. Landing serves only the public Landing/Legal/Knowledge surface plus `/healthz`. Runtime inspection and Admin remain non-public.
9. Existing systemd unit files remain installed as a rollback path but are disabled after successful Docker cutover.
10. Docker restart policy owns normal production restart after cutover. A rollback explicitly stops/removes the AXIGNAL Compose project before re-enabling systemd.
11. Traefik configuration and unrelated projects are unchanged.

## Consequences

- Runtime is no longer reachable directly on host `127.0.0.1:18181`; operational inspection uses `docker compose exec runtime` or container-local health checks.
- Host `127.0.0.1:18180` remains stable, so the existing Traefik route does not need to change.
- Existing SQLite persistence and canonical state survive container/image replacement.
- Host-level Python/nginx dependency drift no longer determines AXIGNAL execution.
- Systemd rollback remains immediately available until a later explicit ADR retires it.

## Rejected alternatives

### Reuse old AXIGNAL pilot/preview networks

Rejected. They are not current production authority and would weaken project isolation.

### Host networking for containers

Rejected. It would preserve loopback semantics but remove the network isolation gained by Docker.

### Publish runtime on host loopback

Rejected. There is no product need for a host-published runtime port once Landing and operational health run inside the project network.

### Move persistence into a Docker named volume during this migration

Rejected for this slice. The current governed data already lives at `/var/lib/axignal/runtime`; moving it at the same time would create an unnecessary data-migration risk.
