# P0 Identity and Account Authority

**Status:** Reconciled authority proposal for review; no authentication or account runtime authorized
**Base:** `7d30966a68168a372ce25ab48d757c6887883adf` (`origin/main`)
**Source proposal:** `codex/p0-identity-account-authority` at `f1d4d8776c012c0b72862aeff8576e3089fce74b`, plus five preserved local edits
**Authority:** MASTER → Constitution → ADRs → feature contracts → this spec → implementation

## Objective and scope

Define the minimum provider-independent identity, private-scope, and entitlement boundaries needed before Settings or authentication runtime is designed. This is domain authority only. It adds no runtime, provider, persistence, schema, migration, authentication UI, Settings UI, or billing integration.

This spec reconciles the existing Principal, Tenant, membership, AuthorizedXeed, Xeed, and canonical Organization contracts with the current product requirements for Google-first sign-in and email/password security. It does not promote test/development contracts into production claims.

## Current implemented authority

The repository already defines `PrincipalId`, `TenantId`, `XeedId`, and `OrganizationId`; `Principal`, `Tenant`, and binary `PrincipalTenantMembership`; and a membership-first `AuthorizedXeedReader` contract.

`TrustedRequestContext` contains a Principal and selected Tenant but explicitly does not authenticate either. The application reader resolves the Principal, verifies membership, resolves the Xeed, verifies that the Xeed belongs to the selected Tenant, and only then returns `AuthorizedXeed`. Current readers are test/development contracts; no production authentication adapter, identity mapping store, membership writer/store, or Xeed persistence is established.

Each Xeed belongs to one Tenant and references one global Organization. A Tenant may own multiple Xeeds. The reference does not copy, own, or grant authority to edit Organization truth. These meanings come from ADR-0018 and ADR-0021 and remain unchanged.

## Identity planes and canonical meanings

| Concept | Authority and boundary |
|---|---|
| Person / persona | A human or a future human-facing presentation of that human. Persona copy or preferences are not credentials, authorization, a Principal, or a subscriber-company identity. No broad persona/profile aggregate is established here. |
| Principal | AXIGNAL's stable internal actor identity (`PrincipalId`). It answers who acts inside AXIGNAL; it is not a provider user ID, payer, Tenant, Organization, role, or profile. |
| Authenticated identity | An issuer-scoped external credential identity, keyed for adapter mapping by issuer and subject. The provider authenticates it; an AXIGNAL-owned adapter maps it to a Principal. Email, display name, avatar, provider organization, and roles are not identity keys. |
| Tenant | The current private isolation, authorization-scope, and Xeed-ownership boundary. Selecting a Tenant is not proof of membership. Tenant is not a payer, legal customer, Workspace, or Organization. |
| Membership | The existing binary Principal–Tenant relation. It authorizes the existing private Xeed read path only. It defines no role, invitation, administrator, or write capability. |
| Subscriber / payer identity | Commercial ownership is not modeled by the current domain. No subscriber-company identity or payer aggregate is authorized by this spec. |
| Xeed | A Tenant-owned private observation context with one global Organization reference. Xeed is not a private Organization or a copy of AXIGLAND. |
| Organization | One observer-independent economic entity in AXIGLAND. It has no subscriber, Principal, Tenant, payer, or owner scope. |
| AXIGLAND | AXIGNAL's one canonical economic world. Subscriber identity, authentication, preferences, entitlement, and Xeed lifecycle cannot rewrite or delete its admitted truth. |

Therefore: `Persona ≠ Principal ≠ AuthenticatedIdentity ≠ Tenant ≠ Membership ≠ Subscriber/Payer ≠ Xeed ≠ Organization ≠ AXIGLAND`.

Do not create a generic `Account`, `Subscriber`, or `Workspace` aggregate merely to match auth-provider vocabulary. The MASTER's User/account/subscription/preferences diagram is a product concept, not a schema, owner/cardinality rule, or persistence authorization. ADR-0018 remains the Tenant/Xeed authority; ADR-0001 and ADR-0004 keep Organization global and XIGNAL as observation rather than ownership.

## Authentication and authorization

Authentication establishes a verified external identity under the selected sign-in path's assurance. It does not establish Tenant membership, authorize a Xeed, create a payer, or grant canonical-write authority.

Before any future authenticated application request can construct trusted identity context, a provider-independent `AuthenticationPort` must return a verified issuer-scoped identity or a fail-closed outcome. An AXIGNAL adapter resolves that identity to `PrincipalId`. A Principal may have multiple external identities only through a provider-supported linking flow that verifies control of the identities being linked. Matching email text alone never links or merges AXIGNAL Principals; ambiguity fails closed. Provider IDs remain adapter-side references, never AXIGNAL domain IDs.

Authorization remains in AXIGNAL. The selected Tenant is untrusted scope input until the current Principal–Tenant membership check succeeds. The existing membership-first AuthorizedXeed sequence remains required. Provider roles, organization claims, email domains, login method, and email equality do not grant AXIGNAL permissions. No subscriber membership roles, invitations, membership writer, or broader subscriber policy are added here. AO-01 later introduces a **separate Admin RBAC plane** under ADR-0056; `AdminPrincipalId`/Admin roles/scopes do not extend or reinterpret `PrincipalTenantMembership`.

### P0 product sign-in requirements

- **Primary:** Continue with Google for the intended low-friction first run.
- **Secondary:** email and password.
- The email/password path requires provider-enforced email verification before the identity is treated as verified.
- TOTP enrollment is mandatory for the email/password path. Account credential creation need not be coupled to TOTP enrollment in one transaction, but security onboarding for that path is incomplete until enrollment succeeds.
- Recovery codes are issued as part of that TOTP enrollment and are handled by the authentication provider.
- For P0, Google sign-in relies on the external identity provider's authentication assurance. AXIGNAL-managed TOTP is not additionally required solely because the user signed in with Google.
- Sensitive operations, once runtime exists, require their explicitly defined authentication assurance. This spec defines no sensitive-operation list or step-up flow.
- SMS is not the primary MFA mechanism.

These are product requirements, not provider selection. No provider is selected, installed, or configured.

## Provider-independent entitlement boundary

Entitlement is separate from authentication, authorization, private scope, and canonical economic identity. A future provider-independent `EntitlementPort` resolves whether a requested AXIGNAL capability or capacity is available for a governed consumption scope. Tenant may be the consumption/authorization scope passed to that boundary; this does not make Tenant the payer, legal customer, billing identity, or commercial aggregate.

AXIGNAL owns the interpretation that maps verified commercial state to product capabilities and limits. A billing adapter may associate external billing references with the governed consumption scope, but external provider IDs and claims do not define Principal, Tenant, Membership, Xeed, or Organization. An unknown entitlement remains `UNKNOWN` and cannot grant new paid capacity; it must not be relabeled as `FALSE` or as a confirmed cancellation.

No payer-to-Tenant cardinality, billing ownership, Xeed-capacity consumption mapping, or commercial lifecycle is selected. MASTER now establishes Xeed as the priced persistent-observation unit and Xignals as non-billable emergent signals; payer/consumption ownership still remains deferred. No billing provider or Stripe-specific ID enters this domain contract.

## Profile and preferences

No broad editable business profile is authorized. Canonical Organization facts, Xeed economic truth, subscriber-company descriptions, and market/capability claims never belong in a Principal profile.

When a human-level UI preference is persisted across sessions, its owner is the Principal, independently of Tenant membership. In particular, an explicit UI-locale preference belongs to the Principal; a browser locale remains an untrusted presentation hint. A minimal `PrincipalPreferences` concept is sufficient if persistence is later authorized. It is not a new identity, commercial aggregate, or profile store, and this spec creates no schema or writer. Locale catalog, supported-locale resolution, and fallback policy remain presentation-layer concerns. UI locale never changes source language, canonical identifiers, epistemic state, or Organization identity.

Display name and avatar storage, editability, provider-claim import, lifecycle, and cross-account presentation remain unapproved. They must not be inferred from provider metadata.

## Lifecycle and canonical-world firewall

Membership removal denies subsequent Tenant/Xeed reads under the existing contract. Tenant/Xeed ownership, last-member behavior, Principal suspension/deletion, subscription cancellation, private-history retention, and legal erasure are not implemented and remain policy decisions.

Deleting or unlinking a Principal, external identity, membership, Tenant, Xeed, private attention, or future subscription must not delete independently admitted AXIGLAND Organization, FAXT, evidence, or relationship truth merely because private attention initiated observation. Canonical lifecycle remains governed independently by evidence admission and domain authority.

## Compatibility with Settings PR #31

PR #31 remains an independent governance proposal and is not modified by Q2. Its Settings surface is an aggregation of separately authorized capabilities, not a new domain aggregate. This matrix classifies the Identity dependency; it does not authorize any Settings runtime or write.

| Settings concept in PR #31 | Identity authority required | Resolved by Q2 | Follow-up before runtime/write |
|---|---|---|---|
| Display name / avatar | Authenticated Principal owner | Owner boundary is Principal if later approved; no profile schema or stored fields | Define field necessity, source, editing, storage, provider-claim policy, fallback, and deletion. |
| Preferred UI locale | Principal preference owner for durable user selection | Owner resolved as Principal; browser locale is only a hint | Define catalog, locale resolution/fallback, durable preference lifecycle, and authenticated command. |
| Theme / reduced-motion override | Principal if cross-device; device/browser if local | Identity does not choose storage scope; presentation-only semantics remain | Choose account vs device scope, reset behavior, and Settings command. System reduced-motion remains independent. |
| Timezone | No identity owner established | No | Choose owner and define presentation-only temporal conversion. |
| Workspace display name / logo / slug | Would require a distinct Workspace or adopted Tenant display authority | No Workspace aggregate; Tenant is only private scope/Xeed owner | Product decision required before names, branding, routes, role checks, or persistence. |
| Principal–Tenant membership | Principal and Tenant | Binary membership and current Xeed-read use are canonical | Production store, writer, audit, add/remove, and last-member policy. |
| Subscriber roles / invitations / member removal | Principal, Tenant, explicit access-administration policy | No subscriber membership roles or member-management authority; Admin RBAC is a separate plane under ADR-0056 | Product decision and separate subscriber authorization contract. |
| Email/login, password, MFA, sessions, connected providers | Principal mapped through external identity adapter | Product methods and provider-owned mechanisms resolved; no provider selected | Select provider; define session, revocation, recovery, security operations, and runtime policy. |
| Billing name/address/tax/payment/plan | Future payer and billing provider | Not resolved; Tenant is not payer | Decide payer identity/cardinality, external reference mapping, billing owner, lifecycle, and retention. |
| Xeed list / selected context / label | Tenant membership and Tenant-owned Xeed | Ownership and reference boundaries resolved; no production list/writer | Define list/select/rename/delete commands, persistence, audit, and history effects. |
| Xeed-to-Organization link | AuthorizedXeed and canonical Organization authority | Read-only reference is resolved; no Settings mutation authority | Any rebind/unlink requires separate product decision, writer, history, and audit policy. |
| Organization facts | Global AXIGLAND evidence authority | Settings edits are forbidden | Reevaluate through governed research and EvidenceAdmission only. |
| Account/Tenant/Xeed deletion, leaving, cancellation | Separate Principal, Tenant, Xeed, and billing lifecycle authorities | Canonical knowledge firewall resolved; deletion policy is not | Define retention, erasure, dependencies, offboarding, billing, and audit per owner. |

**Relationship:** Identity authority precedes Settings runtime. PR #31's governance document can be reviewed as a bounded authority-gap inventory, but its Principal-scoped writes, auth/security behavior, payer mapping, and Tenant/Workspace operations remain blocked on the follow-ups above. Q2 unblocks Settings reconciliation against stable identity terms; it does not unblock Settings implementation.

## Deferred decisions

- Payer identity and its cardinality relative to Principal and Tenant.
- Whether one Principal can belong to multiple Tenants as a product guarantee; the current pair shape does not decide cardinality.
- Whether multiple Principals share one commercial subscriber scope, and how membership administration works.
- How priced Xeed capacity maps to Tenant, Principal, payer, or another governed commercial reference. Xignals are not billable capacity units.
- Cross-subscriber Xignal/attention cardinality for the same Organization; canonical Organization remains singular.
- Profile fields beyond the Principal ownership boundary for durable human preferences.
- Principal, external-identity, membership, Tenant, Xeed, and private-history deletion, retention, and offboarding policies.
- Auth provider, hosting/data-location requirements, session lifetime/revocation, operational availability, and provider-specific linking/recovery evidence.
- Entitlement refresh, grace-period, downgrade, and billing lifecycle semantics.
- Roles, invitations, Workspace, and subscriber-company identity.

## Out of scope

Clerk/Google OAuth integration, password/session/TOTP runtime, login or onboarding UI, Settings UI, profile or preferences persistence, database/schema/migrations, membership writers/roles/invitations, Stripe/billing, entitlement persistence, AXIGLAND/Xeed writers, production deployment, and Landing.

## Acceptance criteria

- Identity planes above remain distinct and consistent with MASTER, Constitution, ADR-0017, ADR-0018, and ADR-0021.
- The provider-independent authentication and entitlement boundaries are explicit, while no provider, payer, or runtime is selected.
- Google-first, email/password, verified email, mandatory password-path TOTP, recovery codes, Google-path assurance, account-linking safeguards, and non-primary SMS policy are unambiguous.
- Tenant remains the private Xeed owner and may be an entitlement consumption scope, but is not presumed to be a payer or Organization.
- Principal owns a durable UI-locale preference if one is authorized; no generic profile or persistence model is created.
- All Settings PR #31 dependencies are classified without changing PR #31.
- Unknown commercial ownership and lifecycle remain explicitly unknown/deferred; no unsupported authority is inferred.
- This slice changes documentation only; runtime, database, Golden Master, production, and Landing remain untouched.
