# AXIGNAL Subscriber E2E Configuration Runbook

**State:** prepared configuration; not deployed, not externally verified, and
not a production-readiness claim.
**Date:** 2026-10-06
**Authority:** optional `deploy/production/compose.subscriber.override.yml`
overlay; the canonical `compose.yml`, the legacy AO-10 systemd topology, and
the deployment migration runbook remain unchanged.

## What this configuration enables

The overlay enables the subscriber application setting and Google OIDC
configuration while keeping contracting disabled. It routes only the
subscriber account surface, its named authentication endpoints, subscriber
API paths, and Next.js static assets from the public landing proxy to the
internal Experience service. The runtime and Experience services remain on the
existing internal Docker network. Experience stays bound on the host to
`127.0.0.1:18182` for the existing operator channel; the overlay adds no host
port and no Traefik route to Customer Zero or Admin.

The overlay is opt-in. The current canonical Compose file is unaffected unless
both files are supplied to `docker compose`. Do not change the host's active
Compose project or legacy systemd services as part of this preparation.

The overlay selects a separate subscriber runtime image. Its build installs
only the frozen `subscriber-auth` dependency group and does not install the
development, semantic-retrieval, decision-lab, or research-canary groups. The
canonical runtime Dockerfile and service definition remain the baseline when
the overlay is omitted. The image definition is prepared but has not been
built or externally verified.

## Configuration and authority boundary

`deploy/production/subscriber-runtime.example.conf` contains only whitelisted,
non-secret settings and known public identifiers. It configures:

- `AXIGNAL_SUBSCRIBER_ENABLED=true`;
- `AXIGNAL_SUBSCRIBER_CONTRACTING_ENABLED=false`;
- the public origin `https://axignal.com` for subscriber origin and callback
  validation;
- the supplied Google web client ID and exact callback
  `https://axignal.com/api/auth/callback/google`;
- ChatGPT sign-in disabled (`AXIGNAL_CHATGPT_REGISTERED=false`);
- known Stripe merchant/product identifiers and EUR 9.95 / EUR 4.95 monthly
  prices, tax-exclusive.

The value `AXIGNAL_GOOGLE_REGISTERED=true` is an operator assertion, not proof
of provider registration. Before using the overlay, confirm that the supplied
Google client has the exact HTTPS callback registered and that its separate
client-secret file is valid. No Google secret value was read, created, copied,
or verified for this preparation. Without that file, the provider remains
unavailable.

Authentication and contracting are separate. An authenticated subscriber can
exist with an empty portfolio and without purchasing any Observation Focuses.
`contracting` must remain false until AXIGNAL's legal identity and terms are
complete and an active, independently confirmed tax registration is available
for the live environment. A missing secret file does not prevent subscriber
runtime composition; partial or invalid credential configuration fails closed.

Billing intentionally is not configured by the sample. The known account is
`acct_1TybkH8feyjV8Pem`; the supplied base/additional-Xeed Price IDs are
`price_1UNYXv8feyjV8PemcFisvBJ2` and
`price_1UNYY88feyjV8PemyuI3unra`. There is no configured Stripe API version,
API key, webhook signing secret, or approved tax configuration. The active
Stripe Tax registration list was observed empty. Price/account identifiers
alone do not enable Checkout or authorize a charge. Do not set
`AXIGNAL_STRIPE_LIVE_ENABLED=true` or enable contracting on that basis.

No authorized subscriber execution-plan reader or registry-backed source
acquirer is attached to this deployment configuration. Consequently, enabling
sign-in does not establish a live paid journey or guarantee that registering
an Organization can produce a Brain output. Customer Zero remains AXIGNAL's
internal use and is not the subscriber onboarding flow.

## Host files and permissions

The overlay expects these host paths by default:

| Host file | Mounted path | Purpose | Runtime identity access |
| --- | --- | --- | --- |
| `/etc/axignal/subscriber-runtime.conf` | `/run/secrets/subscriber_configuration` | Whitelisted non-secret subscriber settings | UID/GID `33:33`, read-only |
| `/etc/axignal/secrets/google_client_secret` | `/run/secrets/google_client_secret` | Google OIDC client secret | UID/GID `33:33`, read-only |

The runtime container runs as `33:33`. Create the directory with root ownership
and group 33 traversal, then install the configuration and secret with
root:33 ownership and mode `0440`. Keep parent directories non-world-readable
and group-traversable only as required. Example commands, to be run by the
authorized production operator after obtaining the Google secret from the
approved secret manager:

```bash
sudo install -d -o root -g 33 -m 0750 /etc/axignal
sudo install -d -o root -g 33 -m 0750 /etc/axignal/secrets
sudo install -o root -g 33 -m 0440 \
  deploy/production/subscriber-runtime.example.conf \
  /etc/axignal/subscriber-runtime.conf
sudo install -o root -g 33 -m 0440 \
  <approved-secret-manager-output-file> \
  /etc/axignal/secrets/google_client_secret
```

The final command consumes a path provided by the authorized secret manager;
it does not read or source an `axignal.env` file. Never put a credential in the
configuration file, shell history, Compose environment, a repository file, or
an operator command argument. Do not print either host file. Verify only
ownership, mode, and readability as UID 33:

```bash
sudo stat -c '%U:%G %a %n' \
  /etc/axignal/subscriber-runtime.conf \
  /etc/axignal/secrets/google_client_secret
sudo -u '#33' -- test -r /etc/axignal/subscriber-runtime.conf
sudo -u '#33' -- test -r /etc/axignal/secrets/google_client_secret
```

The local Compose secrets implementation mounts source files read-only; file
ownership/mode is set on the host so the unprivileged runtime UID can read
them. Do not broaden permissions to world-readable to work around a mount or
identity mismatch.

## Safe configuration validation

From the exact immutable release that has passed CI, load only the existing
non-secret runtime environment file and the public host paths. Keep the exact
approved source SHA in `AXIGNAL_CODE_SHA`; do not use the worktree SHA as a
release candidate.

```bash
export AXIGNAL_CODE_SHA=<approved-main-sha>
export AXIGNAL_SUBSCRIBER_CONFIGURATION_HOST_FILE=/etc/axignal/subscriber-runtime.conf
export AXIGNAL_GOOGLE_CLIENT_SECRET_HOST_FILE=/etc/axignal/secrets/google_client_secret
docker compose --env-file /etc/axignal/runtime.env \
  -p axignal-prod \
  -f deploy/production/compose.yml \
  -f deploy/production/compose.subscriber.override.yml \
  config --quiet
```

`docker compose config --quiet` validates Compose interpolation and merged
configuration only. It does not read the contents of secret files, contact
Google or Stripe, start containers, confirm OAuth registration, validate a
live key, prove tax eligibility, or prove runtime health. Do not run `up`,
`restart`, `pull`, `build`, or any cutover command under this preparation.

## Public routing and invariants

The optional `subscriber-edge-nginx.conf` forwards these public paths to the
internal `experience:3810` upstream:

- `/account` and `/account/â€¦`;
- `/login` and `/signup`;
- `/panorama` for the illustrative public demo and `/panorama/live`, which
  redirects to the subscriber account at `/account`;
- `/api/auth/start`, `/api/auth/status`, `/api/auth/logout`;
- exact Google and OpenAI callback paths;
- exact `GET /api/projection` for the demo's illustrative projection and
  `POST /api/axent` for its bounded contextual explanation;
- `/api/subscriber/â€¦`, including signed billing ingress;
- `/_next/â€¦` assets required to render the Next.js subscriber surface;
- only the public `/brand/`, `/observer/`, and `/fonts/` asset namespaces used
  by the Panorama demo.

The inherited Traefik target remains `127.0.0.1:18180` to the Landing
container. Existing exact Landing/Runtime acquisition endpoints and health
proxy remain in the optional edge configuration. Other `/api/` paths fall
through to the existing static landing behavior; no general runtime or write
proxy is introduced. The browser origin and server-side
`AXIGNAL_EXPERIENCE_ORIGIN` both use `https://axignal.com`; the Next.js
upstream remains `http://runtime:18181` on the internal network. Preserve
Host/forwarded-protocol headers so origin checks and Secure `__Host-` cookies
use the public HTTPS origin.

The local landing CTA now checks `/api/auth/status` and routes available users
to `/account`, or unauthenticated users to `/login` and `/signup`. `/panorama`
now serves the public, no-index demo with illustrative data; `/panorama/live`
leads to the real subscriber account. This closes the observed routing gap
between public demo and subscriber entry in the local code. The changes have
not been validated in a built image or on the public production origin, so
they do not establish that live subscriber entry works. `/api/axent` accepts
only POST at the edge; its runtime mode still requires the operator session
and authority checked by the application. The exact demo paths do not expose
Customer Zero or Admin routes.

The optional overlay must not change these boundaries:

- runtime has no published host port;
- Experience remains host-bound to loopback `18182`;
- Traefik continues to expose only the existing Landing host port `18180`;
- Admin and Customer Zero remain operator-only;
- legacy AO-10 service files and the canonical base Compose remain untouched;
- subscriber configuration and OAuth credentials are mounted read-only;
- unauthenticated access, callback mismatch, invalid session, and cross-origin
  writes remain denied.

## Separate outstanding gates

This prepared configuration is not evidence of a completed subscriber E2E,
paid service, or production readiness. Before enabling contracting, billing,
or public subscriber operations, the owner must separately provide and review
the missing legal/fiscal/provider/source authorities and then authorize the
appropriate validation/deployment work. No production deployment is
authorized by this runbook or the prepared files.
