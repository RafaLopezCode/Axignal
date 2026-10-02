# FR-29 Production Runtime Integration

**Status:** DONE · HISTORICAL HOST-SYSTEMD BASELINE
**Date:** 2026-10-01

> **Current production execution authority:** ADR-0059 and `deploy/production/compose.yml` supersede the host-systemd steady-state topology documented below. The FR-29 systemd artifacts are retained as rollback only; its epistemic/runtime invariants remain binding.

## Observed production topology before FR-29

Direct VPS inspection established:

- host: `srv1597364`;
- public edge: Traefik owns ports 80/443;
- AXIGNAL frontend: `axignal-landing.service` runs isolated nginx on `127.0.0.1:18180`;
- AXIGNAL content root: `/srv/axignal/landing/current`;
- pre-FR-29 deployed landing revision: `170edc8`;
- Python: 3.12.3 at `/usr/bin/python3`;
- `127.0.0.1:18181` was unused at inspection time;
- unrelated project listeners/containers are not part of AXIGNAL and MUST NOT be reused or changed.

## FR-29 target topology

```text
Internet
  -> existing Traefik :80/:443
  -> AXIGNAL nginx 127.0.0.1:18180
       -> static landing from /srv/axignal/landing/current
       -> /healthz only
          -> axignal-runtime 127.0.0.1:18181
               -> /srv/axignal/runtime/current
               -> /var/lib/axignal/runtime/observation-memory.sqlite3
               -> /var/lib/axignal/runtime/learning-memory.sqlite3
```

`/runtimez` is deliberately NOT proxied by nginx. It is a localhost-only operational inspection endpoint. The runtime exposes no public mutation API. The subscriber UI is also kept loopback-only in FR-29 because its current browser projection still declares `DEMO ? DATOS DE EJEMPLO`; exposing it publicly before FR-30 would misrepresent synthetic state as a production product path.

## Runtime invariants

- production binds loopback only;
- exact `AXIGNAL_CODE_SHA` is mandatory;
- Observation Memory and Learning Memory use the production SQLite adapters;
- public `POST/PUT/PATCH/DELETE` fail closed;
- health does not expose row counts;
- isolated persistence probes never write subscriber/business data into live memories;
- AXIGNAL does not reuse ports, databases, services, runners or containers belonging to other projects.

## Deployment sequence

1. Merge a green commit to `main`; record the exact SHA.
2. Create immutable release `/srv/axignal/runtime/releases/<sha>` and atomically point `current` to it.
3. Create `/var/lib/axignal/runtime` writable only for the AXIGNAL runtime service identity.
4. Install `/etc/axignal/runtime.env` with exact SHA and no secrets.
5. Install/start `axignal-runtime.service`; verify `127.0.0.1:18181/healthz` and `/runtimez`.
6. Run the isolated Observation/Learning persistence probe outside live memories.
7. Preserve the prior `/etc/axignal/landing/nginx.conf`, validate the new config, then restart only `axignal-landing.service`; only `/healthz` crosses from nginx to the runtime in FR-29.
8. Publish the matching landing release and verify localhost plus external HTTPS. Keep subscriber/runtime inspection on loopback until FR-30.
9. Record deployed SHA and evidence in the FR roadmap.

## Rollback

Rollback never touches Traefik or other projects:

1. restore the previous `/srv/axignal/landing/current` target;
2. restore the saved AXIGNAL nginx config and restart `axignal-landing.service`;
3. stop/disable `axignal-runtime.service` if the runtime is the cause;
4. repoint `/srv/axignal/runtime/current` to the previous runtime release when one exists;
5. preserve `/var/lib/axignal/runtime` append-only memories unless corruption is independently proven; do not delete data as a rollback mechanism;
6. verify `127.0.0.1:18180/healthz` and `https://axignal.com/`.

## Completion evidence

Deployment completed 2026-10-01 from canonical main SHA `25b64844a9467cb2dd96fb654eb7b865d00268c8`.

- `axignal-runtime.service`: enabled and active on `127.0.0.1:18181`.
- `axignal-landing.service`: active on `127.0.0.1:18180`.
- `/healthz`: `status=ok`; exact code SHA; Observation/Learning stores healthy; public write surface closed.
- `/runtimez` on loopback: both SQLite memories healthy with zero live business rows at deployment time; public write API false.
- isolated probe as `www-data`: Observation and Learning append/reopen PASS; second execution idempotent-replay PASS.
- landing release moved from `170edc8` to `25b64844`; exact full SHA recorded in `/srv/axignal/landing/DEPLOYED_SHA`.
- nginx pre-FR-29 rollback: `/etc/axignal/landing/nginx.conf.pre-fr29-20261001T114952Z`.
- external `https://axignal.com/`: HTTP 200; FR-28 copy present.
- external `/healthz`: full edge path reaches the runtime and returns the exact deployed SHA.
- subscriber synthetic demo remains non-public; FR-30 owns real public E2E exposure.

FR-29 is production-complete. FR-30 remains responsible for the real subscriber first-Xeed-to-first-proof E2E path.
