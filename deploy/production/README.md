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
