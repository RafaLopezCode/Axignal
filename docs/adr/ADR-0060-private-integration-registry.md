# ADR-0060: Private integration registry and credential boundary

## Status

Accepted for AO-18 implementation.

## Context

Stripe and other external capabilities are upcoming AO dependencies. Credentials and provider state must not be scattered across business domains, Admin HTML or logs. AO-01 already owns Admin authorization; AO-07 owns append-oriented privileged-action audit; AO-03 provides the shared projection substrate. Admin is a private operational projection and has no authority over AXIGLAND.

## Decision

- AXIGNAL owns provider-neutral integration definitions and private operational metadata in `domain/admin_integrations`, `application/admin_integrations` and an append-only SQLite event store.
- Credential values are not modeled or persisted. Registry metadata may carry only a validated `secret://` locator and non-secret lifecycle timestamps/state. Secret resolution belongs to a future process-local adapter backed by deployment-managed secret storage.
- Definition metadata, credential lifecycle and provider health are represented as distinct types. Missing health and credential observations remain `UNKNOWN`.
- Each integration declares a positive health-freshness window. `STALE` is derived at projection/use time when the last eligible observation reaches that age; it is never stored as a provider observation. Provider work is denied unless the integration is enabled, belongs to the runtime environment, has a non-expired resolvable credential, grants all requested scopes, and has a fresh `HEALTHY` observation.
- Health projections are temporal: only records known and observed by `as_of` are eligible; the greatest observation time wins, with append sequence as a tie-breaker. A late-arriving older observation cannot roll back newer health.
- Registry changes require `admin:integrations:manage`, step-up assurance, a reason, operation identity and actor/session audit lineage. Reads use `admin:integrations:read`.
- The Admin browser view is read-only. No browser credential transport or Admin action transport is introduced by AO-18.
- Webhook endpoint locators remain server-side registry metadata. The browser bootstrap receives only a boolean indicating whether an endpoint is configured.
- Existing Admin security and audit contracts remain authoritative; Admin remains unexposed unless its security plane is explicitly composed.

## Alternatives considered

- Store credential material in the registry database: rejected because a private metadata database would become a secret vault without an approved encryption/key lifecycle.
- Read arbitrary environment variables directly in Admin code: rejected because it couples business capability logic to deployment configuration and increases accidental disclosure risk.
- Select a cloud secret manager now: rejected because the production secret manager, access policy and operational ownership are not yet decided.
- Add browser credential management: rejected because the current shell has no browser-side Admin session transport and would expose a new privileged mutation surface.

## Tradeoffs

AO-18 can govern references and deny unavailable connections, but cannot prove a credential is usable until a provider adapter performs a bounded health check. A deployment-managed secret provider and browser Admin action transport remain future decisions.

## Consequences

- Integration availability is `UNKNOWN` until a health observation exists; configuration metadata does not imply provider health.
- Health freshness is explicit per integration. Old observations remain available as history but project as `STALE` and cannot authorize provider work.
- Late-arriving health observations preserve temporal order instead of replacing a newer observation by append order.
- No integration is activated by a successful browser return or manually declared Admin state.
- Provider-specific adapters can be added behind the registry without changing credential ownership or AXIGLAND semantics.
- Additive SQLite initialization is safe on startup; production schema/data is not mutated by this code change until a future authorized release.
