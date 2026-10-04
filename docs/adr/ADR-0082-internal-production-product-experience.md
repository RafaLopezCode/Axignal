# ADR-0082 — Internal Production Product Experience

**Status:** ACCEPTED
**Date:** 2026-10-04
**Supersedes:** only ADR-0059 rule 1 to the narrow extent stated below.

## Context

ADR-0059 established AXIGNAL production inside the project-owned axignal-prod
Compose boundary and allowed only the Landing container to publish a host port.
That was correct while the product experience and Admin remained local QA
surfaces.

Customer Zero now consumes the same canonical subscriber product renderer and the
real governed runtime. Dogfooding is useful only if that product can run in the
production composition. Publishing Admin or Customer Zero through the public
Traefik edge is not authorized.

## Decision

Add one experience service to the existing axignal-prod Compose project.

- It shares only axignal_prod_internal with AXIGNAL services.
- It reaches the runtime only as the exact Docker peer runtime:18181.
- It publishes only 127.0.0.1:18182 -> 3810.
- It has no Traefik route and is not reachable from the public Internet.
- Access is through an authenticated SSH tunnel or equivalent explicitly
  authorized operator channel.
- AO-01 remains the authority boundary for Customer Zero.
- The browser never receives runtime network authority; Next validates the Admin
  session server-side and proxies only the governed Customer Zero contracts.
- The runtime adapter may accept runtime:18181 only when containerized; arbitrary
  network origins remain rejected.
- Landing remains the only public AXIGNAL web surface.
- Runtime remains unexposed on the host.
- Canonical persistence remains /var/lib/axignal/runtime.
- The service uses the same exact green main SHA as the Landing and runtime images.

## Consequences

ADR-0059's statement that only Landing publishes a host port is replaced by:
only Landing may publish a public-edge target; the product experience may publish
the dedicated loopback-only operator port 18182.

No public Admin route, new truth authority, second product renderer, datastore or
cross-project dependency is introduced. Removing the experience service is a
complete deployment rollback for this extension and does not alter canonical
runtime persistence.
