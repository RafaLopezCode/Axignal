# P0-HFX-01 Implementation Plan

## Boundary

Add a pure application Subscriber Projection over the existing authorized
Organization and FAXT result types. Add a no-dependency browser surface and a
loopback-only test/dev server that builds its payload through the actual
authorization and read contracts. The in-memory data is labeled synthetic and
never presented as production AXIGLAND state.

## Work sequence

1. Preserve the P0-CORE-05 unknowns and the Golden Master source manifest.
2. Define an immutable projection with strict context-identity checks and a
   narrow supported-field allowlist.
3. Prove invariants with contract tests, including cross-Xeed and
   cross-Tenant separation.
4. Implement browser presentation and session-only interaction state without
   importing domain/application semantics into JavaScript.
5. Exercise the loopback flow in a real browser at desktop and narrow viewport;
   inspect interaction and failure/empty states.
6. Run all canonical gates, Graphify, deterministic frontend build, manifest,
   secret safety, scope review, and adversarial self-audit.
7. Commit/push/open one PR only after local and browser proof. Require exact
   branch-head CI; do not merge or deploy. Human visual sign-off remains open.

## Architecture constraints

- Dependency direction: browser → projection JSON → application contracts →
  domain. Browser JavaScript is presentation-only.
- Only test/dev support code constructs `TrustedRequestContext` from synthetic
  identities. The loopback server accepts no caller-selected tenant/Xeed IDs.
- No production storage/authentication or provider dependencies.
- User interaction directs attention only. It does not write FAXT,
  Organization, Xeed, evidence, relationships, or AXENT transcript.
- Canonical IDs stay distinct; raw FAXT subject stays opaque.
- Evidence references are excluded from browser output.

## Rollback

Revert the slice commit/PR if the projection violates an existing contract or
the Golden Master manifest changes. No persisted data or external state is
written by this slice.
