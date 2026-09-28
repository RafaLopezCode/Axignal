# P0 Settings Authority Matrix

**Base:** `26f298425d88c67551cd432ab35da99d975c6a7a` (`origin/main`)
**Status:** For review; no Settings field has production write authority.

`NONE` means no implemented authority was found in this repository, not that a
future provider or policy cannot exist. `TEST_DEV` is not production
authority. Sensitivity entries are minimum proposed classifications for a
future design, not a claim that the datum is currently stored.

| Setting / operation | Meaning · owner · scope | Current source of truth · write/read authority · persistence | Sensitivity · audit | Side effects; AXIGLAND/research/presentation/billing | Delete · unknown behavior |
|---|---|---|---|---|---|
| `display_name` | Human presentation name · future user · USER | No Principal profile field; no provider/store or write/read contract | Proposed USER_PRIVATE; audit policy absent | Presentation only if authorized; cannot identify/authenticate actor; no AXIGLAND, research or billing effect | Clear/fallback semantics and retention unknown; currently absent |
| `avatar` | Human presentation image · future user · USER | No avatar field, upload API, object storage or persistence | Proposed USER_PRIVATE; minimize image metadata; audit policy absent | Presentation only; never evidence; no research or canonical effect | Replacement, deletion, fallback and retention unknown; currently absent |
| `preferred_locale` | UI language preference · future user · PRESENTATION | No production catalog or stored preference; browser locale is a client hint. Synthetic loopback preview is not authority | Proposed USER_PRIVATE if linked to account, otherwise browser-local; audit unnecessary unless policy says otherwise | Presentation only; no source-language, canonical-ID, predicate, epistemic or research effect | Clear override returns to browser/fallback only after a fallback is selected; currently no durable value |
| `theme` / `reduced_motion_override` | UI rendering preference · future user/device · PRESENTATION | Design System supports system reduced-motion behavior; no account override/store or theme engine | Proposed USER_PRIVATE if account-scoped; audit absent | Presentation only; no truth/research/billing effect | Reset behavior not selected; system preference remains browser/OS authority absent an override |
| `timezone` | Human-local display of time · owner/scope unresolved · PRESENTATION | No stored setting or conversion contract found | Classification depends on storage; audit absent | May affect presentation only if temporal semantics remain absolute and explicit; no canonical time mutation | Reset and default unknown; currently absent |
| `workspace_display_name` | Private subscriber/workspace label · WORKSPACE/TENANT only if such authority is adopted | Tenant currently means private isolation/Xeed ownership, not Workspace; no display field, subscriber model, writer or production store | Proposed TENANT_PRIVATE; audit policy absent | Private presentation only; cannot become Organization name or research evidence | Rename/delete/retention unknown; currently absent |
| `workspace_logo` | Private workspace branding · future WORKSPACE | No Workspace identity or object store | Proposed TENANT_PRIVATE; upload rules as avatar if later permitted | Presentation only; never canonical Organization logo/evidence | Replacement/delete/retention unknown; currently absent |
| `workspace_slug` | Workspace routing identifier · future WORKSPACE | No Workspace aggregate or route authority | Proposed TENANT_PRIVATE; security-sensitive if used for routing; audit policy absent | Must never authorize access; no canonical or research effect | Uniqueness, rename and redirect behavior unknown; currently absent |
| `PrincipalTenantMembership` | Principal may act in Tenant · MEMBERSHIP | Domain contract exists; `InMemoryXeedAuthority` is test/dev; application reader consumes a `MembershipReader`. No production store/writer/authentication | TENANT_PRIVATE; membership changes would require minimized audit | Authorizes current Xeed read boundary only; does not imply a role or Settings writes | Add/remove, invitation and audit lifecycle unknown; currently no mutation contract |
| `role` / invitations / member removal | Access administration · MEMBERSHIP | No role enum/model, invitation or management command | TENANT_PRIVATE; SECURITY_SENSITIVE for access events; audit policy needed | Could affect tenant access; may not alter canonical truth; billing side effects unknown | Member offboarding, ownership transfer, retention and last-member behavior unknown; absent |
| email/login identity, password, MFA, sessions, connected providers | Authentication/security · external AUTH PROVIDER if selected | No auth provider/adapter or account identity store found; Principal is an internal identity only | SECURITY_SENSITIVE; never store raw secrets/tokens/codes in Settings | Security flows may affect sessions/access; must not trigger research or AXIGLAND | Provider-owned lifecycle/recovery/deletion unknown; absent |
| billing name/address/tax ID/email/plan/payment | Commercial subscription identity · BILLING PROVIDER if adopted | No billing provider, billing model or integration found | BILLING_SENSITIVE; no duplicated payment data; audit policy required | Billing only; never copy to Organization or use as evidence | Cancellation, invoices, legal retention and provider delete semantics unknown; absent |
| Xeed list / selected context | Private observation context · Tenant-owned Xeed | Xeed model exists (`id`, `tenant_id`, `organization_id`, optional `label`); test/dev readers only; no production store/writer | TENANT_PRIVATE; access is membership-first through trusted boundary | Context may scope attention/retrieval; not ownership, truth, evidence or research result | Delete/list/select mutation semantics and retention unknown; no production settings access |
| Xeed `label` | Presentation label for one Xeed · Xeed/Tenant | Field exists and validates non-empty; no update command or persistence | TENANT_PRIVATE; audit policy absent | Label only; cannot alter Organization identity/name or canonical semantics | Rename/clear/delete behavior not selected; current object is immutable |
| `Xeed.organization_id` / “my organization” link | Private Xeed-to-global Organization reference · Xeed context | Canonical typed OrganizationId field and authorized contextual reader exist; no Settings writer or production store | TENANT_PRIVATE reference plus PUBLIC canonical target; audit for future reference change needed | Read resolves original global Organization; reference is not ownership, control or truth; changing it may redirect attention and requires explicit policy | Rebind/unlink effects on Xeed work, histories and references unknown; no mutation authorized |
| Organization name, capabilities, products, markets, certification, description | Global economic truth · CANONICAL_WORLD | Organization domain object is global; no subscriber edit capability. Canonical mutation requires independent observation and EvidenceAdmission | Public/canonical with evidence lineage; domain audit/provenance rules apply | Canonical-forbidden from Settings; research reevaluation only through separate governed path | Subscriber/account deletion does not erase independent canonical knowledge; canonical lifecycle remains domain-owned |
| Account/Tenant/Xeed delete, leave, cancel, unlink | Distinct lifecycle commands · relevant USER/TENANT/BILLING/XEED owners | No lifecycle provider, persistence or mutation APIs found | USER_PRIVATE / TENANT_PRIVATE / BILLING_SENSITIVE as relevant; audit required by future policy | No subscriber lifecycle command may delete admitted AXIGLAND truth | Exact retained/anonymized data, dependencies, billing and legal retention are `POLICY_GAP`; all operations absent |

## Source-of-truth matrix

| Authority | Current truth | Access/write state | Settings implication |
|---|---|---|---|
| Canonical Organization | `domain.organizations.Organization`, global world identity | Authorized reads exist in test/dev contracts; no subscriber edit path; canonical writes are admission-governed | Never mirror account/workspace name into it |
| Principal | `domain.tenancy.Principal` with `PrincipalId` | Internal identity contract only; authenticated outer boundary not implemented | No display name, email or avatar can be inferred from Principal ID |
| Tenant / membership | `Tenant`, `PrincipalTenantMembership` | Domain contract and in-memory test/dev authority; no production persistence, role or mutation | Tenant is an isolation boundary, not a product Workspace/account profile |
| Xeed | `domain.xeed.Xeed` | Domain data class; authorized reads via trusted context and membership; production store/writer absent | Current reference/label do not authorize user-edit commands |
| Authentication | None selected | No auth provider or adapter | Do not implement identity/security settings |
| Billing | None selected | No billing provider or data contract | Do not implement billing settings |
| User preferences | No account-level source | Browser/OS signals can influence presentation; local synthetic lab is not a production store | No persisted locale/theme/account preference claim |
| Avatar object | None | No upload/storage service | No upload control |
| AXENT/research | Attention/request boundary, independently observed evidence and admission | Separate from settings | No direct Settings→truth/research side effect |

## Permission matrix

| Action | Current actor authority | Future minimum check | Current status |
|---|---|---|---|
| Read a Xeed in a Tenant | Trusted context + resolved Principal + membership + Xeed Tenant match | Authenticated server-established actor, membership lookup before target read, then object scope check | Read contract exists in test/dev; not production auth/storage |
| Update user profile/avatar/locale | None | Authenticated Principal owns target user record; validate field-specific command and persist to one authority | Not authorized/absent |
| Update workspace identity | None; membership conveys no role | Explicit Workspace/Tenant policy and member capability resolved server-side; exact role policy required | Doctrine gap/absent |
| Manage members/roles | None; membership is binary | Explicit role/capability model, invitation lifecycle and server-side target checks | Doctrine gap/absent |
| Manage auth/security | None | Provider-native secure flow bound to verified actor | No provider/absent |
| Manage billing | None | Billing-provider authorization and bounded provider command | No provider/absent |
| Edit Xeed label or linked Organization | None | AuthorizedXeed plus explicit command contract, audit/concurrency policy, and real writer/store | No writer/persistence; policy gap |
| Edit Organization truth | Subscriber/account role is never sufficient | Independent evidence investigation and EvidenceAdmission only | Settings mutation forbidden |
| Delete any account/context | None | Separate lifecycle command, actor/scope checks, dependency/retention plan and audit | Policy gap/absent |

No `OWNER`, `ADMIN` or `MEMBER` role is proposed by this matrix. Existing
membership is not silently upgraded to RBAC.

## Data-classification matrix

| Data | Minimum future classification | Boundary |
|---|---|---|
| Display name/avatar/account locale | `USER_PRIVATE` | User-scoped; no cross-user access absent a separate policy |
| Workspace display identity, membership and Xeed metadata | `TENANT_PRIVATE` | Tenant-scoped; membership must be established server-side |
| Passwords/tokens/MFA/recovery material | `SECURITY_SENSITIVE` | Provider-owned; never copied into Settings |
| Billing contacts, tax IDs and subscription/payment metadata | `BILLING_SENSITIVE` | Billing-provider owned; minimize local copies |
| Canonical Organization/FAXT/evidence data | Canonical-world / evidence-specific access policy; disclosure class is not selected by Settings | Global AXIGLAND authority; never subscriber-owned |
| Browser locale hint | Not account data; client-provided, untrusted preference input | Resolve only against supported UI locales; no identity or authorization effect |

## Deletion matrix

| Operation | What may be deleted | What is retained / policy gap | Current behavior |
|---|---|---|---|
| Clear avatar | Future user-owned avatar object/reference | Fallback and storage purge timing must be defined; no storage exists | Absent |
| Clear locale override | Future user preference only | Re-resolve from supported browser locale then selected fallback; catalog/fallback not chosen | Absent |
| Leave Tenant / remove member | Membership edge and perhaps user access | Xeed ownership transfer, user data, audit history and last-member behavior are unresolved | No membership writer |
| Delete Principal/account | Provider identity and user-owned data per approved policy | Legal retention, anonymization, tenant data and provider effects are unresolved | No auth/account store |
| Delete Tenant/subscriber | Tenant-private data according to future policy | Billing, membership, Xeed, cognitive state and statutory retention are unresolved | No lifecycle API |
| Cancel subscription | Billing subscription only | Provider, billing period, invoices and retention rules are unresolved | No billing integration |
| Unlink Organization / delete Xeed | Private reference/context only if later authorized | Dependent history, FAXT references, research attention and retention are unresolved; canonical world retained | No writer/persistence |
| Delete canonical Organization/FAXT due to subscriber deletion | Nothing through Settings | Independently admitted AXIGLAND truth remains governed by canonical domain lifecycle | Forbidden |

`POLICY_GAP`: applicable legal retention/anonymization periods and provider
deletion behavior have not been selected.
