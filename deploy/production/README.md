# AXIGNAL Production Deployment

**Canonical production authority:** `deploy/production/compose.yml` under ADR-0059.

AXIGNAL production runs as the isolated Compose project `axignal-prod`:

- `axignal-prod-landing` publishes the public-edge target only on `127.0.0.1:18180`;
- `axignal-prod-experience` publishes the operator-only product surface on `127.0.0.1:18182`, with no Traefik route;
- `axignal-prod-runtime` is reachable only on the dedicated `axignal_prod_internal` Docker network;
- canonical runtime persistence remains bind-mounted from `/var/lib/axignal/runtime`;
- host Traefik continues to route `axignal.com` only to `127.0.0.1:18180`.
- Customer Zero/Admin access uses an authenticated SSH tunnel (or equivalent authorized operator channel) to `18182`; it is not public Internet surface.

The legacy files `axignal-runtime.service`, `runtime.env.example` and
`axignal-landing-nginx.conf` are retained as the documented rollback topology.
They are not the canonical steady-state production execution model after the
ADR-0059 cutover.

Use `docs/operations/AXIGNAL_DOCKER_PRODUCTION_MIGRATION.md` for build,
cutover, verification and rollback.

## Internal Admin session over SSH

Customer Zero remains operator-only. Production composes AO-01 session validation,
but does not expose an external credential exchange. After authenticated root SSH,
issue a bounded PRIMARY-assurance session from the immutable deployed release:

    python3 -m tools.runtime.admin_session issue \
      --data-dir /var/lib/axignal/runtime \
      --principal-id admin:founder:operator \
      --output-file /run/axignal-admin-session.key \
      --hours 1

The output file is created exclusively with POSIX mode `0600`; the raw bearer is
not persisted in SQLite or logs. Transport it only through the authorized operator
channel to `/api/admin/session`. When the operator session ends, revoke it and
delete the token file:

    python3 -m tools.runtime.admin_session revoke \
      --data-dir /var/lib/axignal/runtime \
      --token-file /run/axignal-admin-session.key

This SSH operator adapter is internal bootstrap/session issuance for Customer Zero,
not the future general Admin browser identity provider. See ADR-0083.

## Autonomous observation daily timer

The existing `axignal-observation-daily.timer` wakes the existing runtime once
per UTC day (03:17 UTC + up to 15 minutes jitter, persistent catch-up). It does
not decide business cadence; the runtime selects due work. The one-shot runner
is **off by default** through the existing `AXIGNAL_OBSERVATION_RUNTIME_ENABLED`
flag in `/etc/axignal/observation-runtime/scheduler.env`. Missing/false returns
`DISABLED` before Docker/data access. Enabled but missing server-owned files
returns `NOT_CONFIGURED`, with zero child work:

- `/etc/axignal/observation-runtime/attention.json`
- `/etc/axignal/observation-runtime/enrollment.json`

Do not create placeholder tenant, principal, focus, market, or source-rights
values. Enrollment must refer to real authorized subscriber state. The runner
resolves `/srv/axignal/docker/current` on every invocation, uses that exact
runtime image, mounts canonical persistence and individual read-only config files,
publishes no port, runs as UID 33 and receives no provider/model credentials.
The shell lock and stable container name prevent overlapping scheduler entries.
SQLite still fences the daily work, including UTC-day overlap and expired tokens.
The 30-minute service limit is below the one-hour lease; service termination
stops only `axignal-prod-observation-daily`. A completed same-day replay is a no-op.

Install/update the scheduler from the deployed immutable release:

    /bin/sh deploy/production/install-observation-scheduler.sh --check
    /bin/sh deploy/production/install-observation-scheduler.sh --install

The installer validates syntax, installs only units, creates the disabled example
only when no scheduler config exists, preserves existing config, reloads systemd
and enables the existing timer. Repeating it is idempotent. It never changes the
immutable release or `current`. Run `--install` only after the CTO's canonical
integration/cutover; a candidate preflight uses `--check` only.

After authorized server-owned enrollment and attention exist with root:www-data
ownership and `0640` files, the CTO may set the flag to `true`, then run one tick:

    systemctl start axignal-observation-daily.service
    journalctl -u axignal-observation-daily.service --no-pager -n 20

Redacted results include day, duration, item/failed/blocked/deferred counts,
request count, STOP reason, next due and lease state. Full tick state plus
started/finished invocation metadata persist in `observation-runtime.sqlite3`.
For read-only status (no runtime/database creation, no tenant/focus ids or tokens):

    docker exec axignal-prod-runtime python -m tools.runtime.observation_daily --status

An interrupted invocation remains inspectable. A fresh process can resume after
the lease expires; already committed steps/receipts and daily spend survive.
Unknown source cost remains unroutable; UNKNOWN families are legitimate (T13).
No retries are added to systemd or the runner.

Rollback/kill switch, performed by the CTO: set the flag to `false`, then:

    systemctl disable --now axignal-observation-daily.timer
    systemctl stop axignal-observation-daily.service

This retains all operational/economic databases and enrollment. Do not delete
the store to retry a day. `ExecStopPost` stops the worker if it is still running.

Isolated preflight may override `AXIGNAL_OBSERVATION_RELEASE`,
`AXIGNAL_OBSERVATION_CONFIG_DIR`, `AXIGNAL_DATA_DIR`,
`AXIGNAL_OBSERVATION_CONTAINER_NAME` and `AXIGNAL_OBSERVATION_NETWORK`.
Use a candidate SHA directory, isolated empty arrays, a fresh data directory,
an own worker name and `network=none`; never mount mutable production data.
`AXIGNAL_OBSERVATION_DOCKER` exists for executable adapter testing only.

A disabled/unconfigured/no-work outcome is not evidence of actual production
observation. Controlled E2E proves configured due work through the real Brain;
the first real authorized production tick remains part of the CTO cutover.


## Private Google Search Console sync (AO-13)

AO-13 imports AXIGNAL's own Search Console performance as private first-party operating evidence. It does not write AXIGLAND and it does not turn Google Search Console metrics into public Digital Representation truth.

Production uses `axignal-gsc-sync.timer` to run `run-gsc-sync.sh` once per UTC day. The runner is fail-closed: without `/etc/axignal/secrets/gsc_oauth.json` the systemd unit is skipped, and the shell runner itself returns `{"state":"NOT_CONFIGURED"}`.

The server-owned OAuth secret file is JSON with `client_id`, `client_secret`, and `refresh_token`. It must be readable only by the production secret boundary and must never be committed, logged, embedded in image layers, or copied into runtime databases.

The canonical property is `sc-domain:axignal.com`. The sync reads one 28-day property summary plus query, page, country, device, and search-appearance breakdowns. Raw private rows persist in `admin-gsc.sqlite3`; governed summary outcomes are recorded in the AO-24 measurement registry with property, period, instrument version, uncertainty, and source references.

Operational invariants:

- `GSC_PRIVATE_METRIC != PUBLIC_OBSERVATION`.
- missing Search Console rows are not converted to global zero-demand claims;
- repeated synchronization of the same settled window is replay-safe;
- OAuth failure or revocation fails closed and produces no synthetic measurement;
- only the domain property feeds canonical own-site measurement; URL-prefix properties may be used for diagnostics but must not be added to the same totals.

## Direct SEO Production Truth

AXIGNAL does not require GSC Wizard in production. The direct SEO truth runtime reuses the AO-13 server-owned Search Console OAuth credential to inspect the canonical sitemap and URL indexing state through Google's official Search Console APIs. An optional Chrome UX Report API key adds origin-level field performance without blocking indexing truth when CrUX is unavailable.

`axignal-seo-truth-sync.timer` runs `run-seo-truth-sync.sh` incrementally every hour. Each run inspects at most 30 new sitemap URLs for the current UTC day; already persisted inspections are skipped, so repeated runs resume the daily sweep instead of starting over. This bounds runtime while allowing the full 528-URL corpus to be covered within the daily Search Console quota. The runner mounts `/etc/axignal/secrets/gsc_oauth.json` read-only and, when present, `/etc/axignal/secrets/crux_api_key` read-only. Both files must remain outside Git and image layers. The CrUX key should be restricted in Google Cloud to the Chrome UX Report API only.

Private URL Inspection and sitemap snapshots persist in `admin-seo-truth.sqlite3`. CrUX p75 measurements are admitted only into the governed AO-24 Measurement Registry; absence of a CrUX record is `INSUFFICIENT_DATA`, never zero performance. Search Console coverage labels remain Google observations and are not promoted into AXIGLAND truth.

Operational invariants:

- `URL_UNKNOWN_TO_GOOGLE != TECHNICAL_SEO_FAILURE`;
- `DISCOVERED_NOT_INDEXED != REJECTED`;
- `CRUX_NO_DATA != ZERO_LATENCY`;
- replay within the same inspection day is idempotent;
- sitemap URLs outside the canonical `https://axignal.com` origin fail closed;
- GSC Wizard may be used as an operator aid, but is not a production dependency.
