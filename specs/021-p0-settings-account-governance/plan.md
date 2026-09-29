# Plan: P0 Settings / Account Governance Authority

## Constitution check

- MASTER says AXIGNAL observes economic truth; subscriber input cannot directly
  edit it (MASTER §§2.1–2.3, §5).
- User/account preferences and Organization truth are separate (MASTER §6.1).
- The repository's domain dependency direction keeps UI orchestration outside
  domain; Settings is an aggregation surface, not a new domain aggregate.
- `UNKNOWN` remains unknown. Missing authentication, provider, persistence,
  mutation, deletion or retention authority cannot be supplied by a fixture or
  a Settings control.
- No requirement in this plan amends the MASTER or accepted product ontology.

## Plan outcome

Documentation-only governance spec reconciled after P0 Identity PR #36. Identity
now resolves the Principal/external-identity/Tenant/Membership/Xeed/Organization
separation, product authentication methods, Principal ownership of a future
durable UI-locale preference, and the provider-independent entitlement
boundary. There is still no safe Settings write vertical slice because no auth
provider/runtime, production preference store, bounded Settings command, or
production membership/Tenant/Xeed mutation authority exists. Do not implement
synthetic persistence or tests for nonexistent mutation types.

## Work packages

1. Record the evidence map from primary doctrine, Constitution, ADRs, specs,
   domain/application code, tests and the current UI prototype boundary.
2. Define per-field owner/scope/source/read/write/persistence/classification/
   audit/effects/deletion/unknown matrices.
3. State the canonical firewall and future mutation prerequisites for avatar,
   workspace identity, locale, security, billing, membership, Organization
   references and lifecycle operations.
4. Leave runtime, tests, UI and persistence unchanged until an explicit
   authority gap is resolved.

## Rollback

Remove this isolated spec directory and branch. No runtime data, schema,
Golden Master or provider state changes.

