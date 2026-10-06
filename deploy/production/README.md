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
