# Tasks — P0 Identity Authority

## Completed in this reconciliation proposal

- [x] Re-read current MASTER, Constitution, relevant ADRs, architecture references, HFX doctrine, current domain/application contracts, and Settings PR #31.
- [x] Preserve and audit the old Identity branch commit and five modified spec files without changing that worktree.
- [x] Separate Persona, Principal, external authenticated identity, Tenant, Membership, subscriber/payer, Xeed, Organization, and AXIGLAND.
- [x] Reconcile Google-first and email/password requirements, including verified email, mandatory password-path TOTP, recovery codes, and Google-path assurance.
- [x] Define provider-independent AuthenticationPort and entitlement boundaries; retain no provider selection.
- [x] Resolve Principal as owner of a future durable user-level UI-locale preference without adding a profile store.
- [x] Classify payer, cardinality, membership lifecycle, profile, and provider decisions as resolved or deferred.
- [x] Add a Settings PR #31 compatibility matrix without modifying PR #31.
- [x] Record deterministic, Graphify, Golden Master, secret-scan, and Landing-exception evidence in validation.md.

## Deferred product/CTO decisions

- [ ] Select payer/entitlement owner and Principal/Tenant/subscriber cardinalities.
- [ ] Define the priced Xignal-capacity relation to Tenant, Xeed, Principal, or payer.
- [ ] Decide any profile fields beyond the Principal preference-owner boundary.
- [ ] Define membership roles, invitations, removal, final-member behavior, and offboarding.
- [ ] Define Principal, external identity, Tenant, Xeed, subscription, and private-history retention/deletion.
- [ ] Set auth provider, hosting/data-location, session/revocation, cost, and support requirements.
- [ ] Verify the chosen provider supports password-path TOTP/recovery and safe linking without requiring AXIGNAL-managed TOTP for Google P0.
- [ ] Define entitlement refresh, cancellation/grace, downgrade, and unknown-state handling before billing runtime.

## Explicitly not started

- [ ] Authentication, Google OAuth, password/session/TOTP runtime, or onboarding UI.
- [ ] Account/Profile/Preference persistence, database schema, or migration.
- [ ] Membership writer, roles, invitations, Settings UI, or account-management commands.
- [ ] Stripe, billing provider, payer records, or entitlement persistence.
- [ ] Production, Golden Master, HFX runtime, Landing, or deployment.
