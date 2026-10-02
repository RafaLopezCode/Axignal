# AXIGNAL Docker Production Migration

**Status:** ACTIVE RUNBOOK
**Date:** 2026-10-02
**Authority:** ADR-0059

## Canonical topology

```text
Traefik host :80/:443
  -> 127.0.0.1:18180
  -> axignal-prod-landing:8080
  -> axignal_prod_internal
  -> axignal-prod-runtime:18181
  -> /var/lib/axignal/runtime
```

The Compose project is `axignal-prod`. Do not reuse any pilot, preview, MERXAT, INKDIE or other project network/container/volume.

## Preconditions

- exact canonical `main` SHA is green in CI;
- `docker version` and `docker compose version` succeed;
- `/var/lib/axignal/runtime` exists and remains owned/readable-writable by runtime UID/GID 33;
- host `127.0.0.1:18180` currently belongs only to AXIGNAL;
- existing systemd services are healthy and preserved as rollback;
- Traefik continues to target host `127.0.0.1:18180`.

## Build without cutover

From an immutable source release:

```bash
export AXIGNAL_CODE_SHA=<exact-main-sha>
docker compose -p axignal-prod -f deploy/production/compose.yml build
```

The build MUST finish before stopping host services.

## Cutover

1. Record current runtime/landing targets and `/etc/axignal/runtime.env`.
2. Stop and disable only:
   - `axignal-runtime.service`
   - `axignal-landing.service`
3. Start Compose:
   ```bash
   export AXIGNAL_CODE_SHA=<exact-main-sha>
   docker compose -p axignal-prod -f deploy/production/compose.yml up -d
   ```
4. Require both containers healthy.
5. Verify:
   - `curl http://127.0.0.1:18180/healthz`;
   - external `https://axignal.com/healthz`;
   - external Landing;
   - exact code SHA;
   - public write surface closed;
   - runtime has **no published host port**;
   - only `127.0.0.1:18180` is published;
   - existing Observation/Learning/Admin row counts are unchanged;
   - Landing/Legal/Knowledge routes remain 200.
6. Verify systemd services remain disabled/inactive.

## Rollback

Rollback does not delete `/var/lib/axignal/runtime`.

```bash
docker compose -p axignal-prod -f deploy/production/compose.yml down
systemctl enable --now axignal-runtime.service
systemctl enable --now axignal-landing.service
```

Then verify loopback/external health and exact prior SHA.

## Production evidence

A migration is not DONE because containers are running. Record:

- source SHA;
- image IDs/digests;
- container names/status/health;
- dedicated network ID/name;
- published ports;
- persistence row counts before/after;
- external health and Landing;
- rollback evidence;
- confirmation that unrelated containers/networks were untouched.
