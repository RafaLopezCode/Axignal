# Tasks: P0 Settings / Account Governance Authority

## Completed

- [x] Verify clean canonical-main base in a separate managed worktree.
- [x] Inspect open PR #29/#30 status and preserve both branches and the dirty
  HFX checkout.
- [x] Build an evidence map of MASTER, Constitution, relevant ADRs, Subscriber
  and HFX specs, Design System, domain/application models and test/dev authority.
- [x] Inspect current main Settings/runtime boundary and classify synthetic
  locale/account UI as non-production authority.
- [x] Write the Settings authority, source-of-truth, permission,
  classification and deletion matrices.
- [x] Record doctrine gaps and the no-runtime-implementation decision.

## Blocked pending authority

- [ ] Select the authentication provider and implement the already-governed
  provider-independent verified-identity → Principal adapter/runtime contract.
- [ ] Select production persistence and write/read authority for user-scoped
  preferences/profile, if needed.
- [ ] Decide whether Workspace/Subscriber is a real aggregate, how it relates
  to Tenant, and its exact identity/display-name permissions.
- [ ] Decide whether membership needs roles/capabilities; do not assume
  OWNER/ADMIN/MEMBER.
- [ ] Select supported locale catalog, product fallback, persistence lifecycle
  and authenticated command. P0 Identity already resolves Principal as owner of
  a future durable UI-locale preference.
- [ ] Resolve avatar/object-storage policy, billing provider/authority, audit
  rules, retention, deletion and offboarding semantics.
- [ ] Decide if a user may change a Xeed label or `Xeed.organization_id`, with
  explicit private-context and research effects.
- [ ] Only after those decisions, create implementation plan and matching
  contract tests; then implement one authorized vertical slice.

## Explicitly not started

- [ ] Settings UI, runtime/API, persistence, migrations or providers.
- [ ] Tests for nonexistent Settings mutation abstractions.
- [ ] Changes to PR #29, PR #30, Golden Master or production.

