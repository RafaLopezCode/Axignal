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


## Production cutover evidence — 2026-10-02

Canonical Docker cutover was executed from green main SHA:

```text
bed3c977281d5dab6785fd404faa40dccc51ba21
```

Observed before cutover:

- `axignal-runtime.service` active/enabled on host `127.0.0.1:18181`;
- `axignal-landing.service` active/enabled on host `127.0.0.1:18180`;
- Docker project `axignal-prod` empty;
- existing unrelated containers (Biocultor, IAmancha, Traefik) running and untouched;
- canonical SQLite counts recorded under `/srv/axignal/docker/evidence/precutover-bed3c977281d5dab6785fd404faa40dccc51ba21.txt`.

Pre-cutover staging on the same KVM2 passed with:

- isolated temporary Docker network;
- temporary persistence directory;
- Landing on `127.0.0.1:18182`;
- runtime with no published host port;
- exact OCI revision labels;
- read-only roots, `cap_drop=ALL`, `no-new-privileges`;
- live production on `18180` remaining healthy throughout.

The first production cutover attempt exercised rollback automatically after a verification-script status-code defect. Docker resources were removed and both systemd services returned to `active/enabled` with external health restored to the prior SHA. No persistence counts changed.

The corrected cutover then completed successfully:

- Compose project: `axignal-prod`;
- containers:
  - `axignal-prod-runtime`;
  - `axignal-prod-landing`;
- dedicated network: `axignal_prod_internal`;
- runtime host-published ports: **none**;
- Landing host publication: **only** `127.0.0.1:18180 -> 8080`;
- systemd runtime/landing: `inactive/disabled`;
- external `https://axignal.com/healthz`: `status=ok`, exact Docker SHA, write surface closed;
- Landing, Privacy/RGPD and Knowledge routes: HTTP success;
- unrelated containers remained running.

Persistence before and after cutover was identical:

```text
admin-commercial.sqlite3
  admin_commercial_audit=0
  admin_commercial_records=0

admin-customer-accounts.sqlite3
  admin_customer_account_events=0

admin-governance-audit.sqlite3
  admin_governance_audit=0

admin-observability.sqlite3
  admin_observability_records=0
  admin_projection_snapshots=0

first-proof.sqlite3
  first_proof_sessions=1

learning-memory.sqlite3
  learning_events=6

observation-memory.sqlite3
  observation_fields=5
  observations=1

policy-governance.sqlite3
  active_policies=0
  policy_decisions=0
```

Docker image evidence for the functional cutover:

```text
Runtime image ID:
sha256:a7e6c6d3b6a3065539955c3bcf2a64d0eddb122bc69b5655412665e68bd294e1

Landing image ID:
sha256:cc8693b0225cfd565a3af1c3e91e962f78c72ff82d57e287a865cba2b7339a5b
```

Post-cutover delayed verification confirmed both containers remained `healthy`, only Docker owned host `127.0.0.1:18180`, no host listener existed on `18181`, systemd remained disabled/inactive, external health remained green and SQLite counts remained unchanged.

The host-systemd units and their prior immutable releases remain preserved exclusively as rollback.
