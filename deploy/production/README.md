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

The autonomous observation entrypoint is deployed as a bounded one-shot container,
scheduled by `axignal-observation-daily.timer` once per UTC day. The timer may be
enabled before subscriber enrollment exists: the service has systemd
`ConditionPathExists` guards and therefore skips cleanly until both server-owned
files exist:

- `/etc/axignal/observation-runtime/attention.json`
- `/etc/axignal/observation-runtime/enrollment.json`

Do not create placeholder tenant, principal, focus, market, or source-rights
values. Enrollment must refer to real authorized subscriber state. The runner
resolves `/srv/axignal/docker/current` on every invocation, uses that exact
runtime image, mounts canonical persistence, publishes no port, runs as UID 33,
and does not receive model credentials.

Install/update the scheduler from the deployed immutable release:

    install -o root -g root -m 0755 \
      deploy/production/run-observation-daily.sh \
      /srv/axignal/docker/current/deploy/production/run-observation-daily.sh
    install -o root -g root -m 0644 \
      deploy/production/axignal-observation-daily.service \
      /etc/systemd/system/axignal-observation-daily.service
    install -o root -g root -m 0644 \
      deploy/production/axignal-observation-daily.timer \
      /etc/systemd/system/axignal-observation-daily.timer
    systemctl daemon-reload
    systemctl enable --now axignal-observation-daily.timer

A skipped service because enrollment/configuration is absent is not evidence of
an autonomous observation E2E. Verify the first configured tick manually before
claiming production E2E.


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
