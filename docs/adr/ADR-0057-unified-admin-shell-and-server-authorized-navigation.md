# ADR-0057: Unified Admin Shell and Server-Authorized Navigation

- **Status:** Accepted
- **Date:** 2026-10-01
- **Source doctrine:** MASTER §§2.1A, 5, 39, 46; Admin V0.2; ADR-0055; ADR-0056
- **Implementation:** AO-02

## Context

AXIGNAL Admin must operate the company AXIGNAL without becoming a visually or architecturally separate dashboard product. The subscriber product already has a Human-First shell with a left rail, central cognitive surface and persistent AXENT context. Rebuilding Admin as a conventional enterprise dashboard would split the product language, increase cognitive load and make private operational state easier to confuse with AXIGLAND economic truth.

AO-01 already established that Admin authorization is a separate server-side security plane. AO-02 therefore needs a shell that reuses AXIGNAL's visual grammar while preserving server-side scope enforcement and the private/canonical authority boundary.

## Decision

Admin uses the same AXIGNAL shell grammar:

```text
LEFT RAIL
→ privileged Admin domains

CENTER
→ current Admin operating domain

RIGHT AXENT
→ context-sensitive business intelligence
```

The Admin shell reuses AXIGNAL Design System tokens, brand assets, typography, subscriber shell geometry and AXENT visual language. It is not a separate dashboard application.

Admin is always visibly marked as privileged operating context. Operational cards and projections MUST be visually distinct from FAXT/Xignal/AXIGLAND evidence and MUST carry explicit operational/private semantics where confusion is possible.

## Server-authorized navigation

Navigation visibility is derived from the AO-01 `AdminAuthorizationGrant`.

The canonical Admin domains are: Command Center, Customers / CRM, Acquisition, Revenue, Xeeds, AXIGLAND Quality, AXENT / Brain, Governance, Integrations, Finance / Fiscal, Frontier Advisor and System.

Each domain declares one or more required Admin scopes. A domain is shown only when the current grant satisfies that domain's scope requirement.

Client-side hiding is presentation only. It is never authorization.

Deep links use `/admin/<domain-slug>`. The server resolves the live Admin session first and then evaluates whether the requested domain is visible to that grant. Known-but-denied domains return 403. Unknown domains return 404.

## Exposure boundary

`build_runtime()` does not compose Admin authentication by default.

```text
runtime.admin_access is None
→ /admin returns 404
```

The shell becomes reachable only when an Admin security plane is explicitly composed into the runtime. AO-02 does not select the production external authentication provider or browser credential transport; those remain separate deployment/auth adapter decisions from ADR-0056.

Static CSS/JS/brand assets may be readable because they carry no private data or authority. Rendered Admin HTML is `no-store`, has a restrictive CSP, and receives only a secret-free bootstrap projection containing principal identifier, active roles/scopes and authorized navigation. Raw session credentials are never rendered into HTML/JS.

## Responsive and accessibility contract

- Desktop preserves left rail → central surface → AXENT.
- Tablet may stack AXENT beneath the central surface.
- Mobile uses a compact horizontally scrollable Admin domain rail rather than shrinking the desktop left rail or consuming the viewport with all domains.
- Navigation remains keyboard-focusable and deep-linkable.
- `prefers-reduced-motion` preserves functionality without requiring motion.
- The active domain uses `aria-current="page"`.

## Epistemic boundary

```text
ADMIN OPERATIONAL CARD != FAXT
ADMIN OPERATIONAL CARD != XIGNAL
ADMIN PRIVATE STATE != AXIGLAND CANONICAL TRUTH
```

The shell must never use canonical epistemic labels in a way that implies an Admin metric or CRM/payment/fiscal state is public economic truth.

## Consequences

- AO-03 can populate real Admin projections without redesigning the shell.
- Role-limited staff see only domains their server-side grant exposes.
- A manipulated URL cannot grant access to a hidden domain.
- Subscriber/public runtime remains unchanged unless Admin is explicitly composed.
- AXENT has a consistent privileged context surface but receives no canonical write authority.
- Browser visual fixtures may be secret-free while HTTP authorization is tested against the real AO-01 service.

## Enforcement

- `application/admin_shell/` owns scope-derived navigation projection.
- `apps/web/admin/` owns the reusable Admin presentation shell.
- `tools/runtime/service.py` performs server-side session resolution and deep-link authorization before rendering Admin HTML.
- AO-02 contracts cover 401/403/404 behavior, role-limited navigation, deep links, no raw credentials in rendered HTML, responsive semantics and epistemic separation.
