# Plan — P0 Identity Authority Reconciliation

**Base:** `7d30966a68168a372ce25ab48d757c6887883adf` (`origin/main`)
**Source:** `codex/p0-identity-account-authority` plus its five local spec edits. The source worktree remains preserved and was not rebased or modified.

## Authority check

- MASTER §6.1 distinguishes conceptual User account/subscription/preferences from Organization identity; it does not define an Account schema or payer cardinality.
- Constitution and ADR-0001/0004 preserve one canonical AXIGLAND and prohibit subscriber ownership/editing of Organization truth.
- ADR-0017 keeps private Tenant/client/Xeed context separate from canonical economic truth.
- ADR-0018 defines Principal, Tenant, binary membership, Tenant-owned Xeeds, and the membership-first authorized read; it does not implement production authentication or persistence.
- ADR-0021 preserves Xeed's reference to the original global Organization.
- Current P0 product requirements specify Google-first sign-in and mandatory password-path TOTP/recovery; no production provider is selected.
- Current HFX locale controls are not production account persistence. Durable user-level UI-locale preference ownership is Principal; catalog and fallback remain presentation authority.

## Reconciliation decisions

Carry forward the valid identity-plane separation, current code-contract inventory, external subject mapping, safe linking, dated candidate research, and private/canonical deletion firewall. Replace the source proposal's unresolved password TOTP and Google TOTP entries with the current explicit product decision. Add the provider-independent entitlement boundary and Settings compatibility matrix required by Q2. Keep payer, cardinality, billing, membership lifecycle, and broad profile choices deferred.

## Architecture and rollback

Documentation only in `specs/022-p0-identity-account-authority/`. No code, dependency, persistence, migration, provider configuration, Golden Master, or production state is touched. Revert by removing only this spec directory and its reconciliation branch; do not affect the preserved source worktree, stash, or Landing assets.
