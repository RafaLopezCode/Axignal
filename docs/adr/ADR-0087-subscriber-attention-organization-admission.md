# ADR-0087: Subscriber attention → governed Organization admission

- **Status:** Accepted for review (CTO)
- **Date:** 2026-10-07
- **Authority:** MASTER §6 (perspective is a query), §14, §15.1 (CLAIM ≠ WRITE), §15.3 (registry → legal identity), §15.4 (UNKNOWN); Constitution; ADR-0049 (deterministic identity resolution), ADR-0072 (proposition-bound admission), ADR-0081 (credential-safe URLs), ADR-0085 (pilot).
- **Scope:** the seam between a subscriber's "observe this organization" input and the one canonical Organization store (spec 052). No new entity-resolution platform.

## Context

The subscriber portfolio already resolved locators through `SqliteCanonicalOrganizationStore`, but nothing in production ever wrote to that store, and it matched only exact legal names. Every real input stayed pending forever; a website never resolved; ambiguity, conflict and "not found" were indistinguishable.

## Decision

1. **Locator = attention.** A locator is classified into signals (name, public website, checksum-valid LEI). Internal ids (`org:`, `focus_`…), emails, credentials, IPs and private hosts are `INVALID_INPUT`. Classification never resolves or trusts anything.
2. **Resolution order** (`OrganizationAdmissionService`, the portfolio's `OrganizationResolutionPort`):
   1. canonical index — verified identifier, then registry-recorded website, then exact admitted legal name (ADR-0049 normalization);
   2. only if no verified key is known, an independent **registry source** port;
   3. EvidenceAdmission, then the canonical store.
   Outcomes: `RESOLVED_EXISTING`, `ADMITTED_NEW`, `IDENTITY_PENDING`, `AMBIGUOUS`, `CONFLICT`, `INVALID_INPUT`. No first match wins.
3. **Signals must agree.** Verified keys that point at different Organizations, or a name that is the admitted legal name of a *different* Organization, are `CONFLICT`. A name that matches nothing is only a hint next to a verified key. A supplied verified key unknown to AXIGLAND next to a known one is pending (all verified keys must be known and agree).
4. **Only REGISTRY admits.** A record is admitted only if the source record attests exactly the signal the subscriber gave (identifier, website, or — for a bare name — the exact legal name). Predicates: `legal_identity`, `registration` (`SCHEME|AUTHORITY|VALUE`) and **`official_website`**, the website a registry records for the entity (added to the REGISTRY-only legal-identity policy). A website declaring itself never admits identity.
5. **Deterministic identity.** `OrganizationId = org:id:<sha256(min registry identifier)>`. The control plane (not the source) issues `DETERMINISTIC_POLICY` identity bindings from the registry entry identifier mention to that id, so the subject is grounded without inventing text.
6. **Store invariants.** One transaction per admission; primary keys on identifiers and websites make "one key, two Organizations" impossible under concurrency; an admitted identity is reused, never rewritten (a different admitted name is `CONFLICT`); every key keeps evidence ref, digests, policy and observation time.
7. **Pending is inspectable.** The portfolio persists the reason (`NOT_FOUND_IN_IDENTITY_SOURCE`, `IDENTITY_SOURCE_UNAVAILABLE`, `AMBIGUOUS:…`, `CONFLICT:…`) next to the private pending request; no Focus, observation or canonical write happens until identity resolves. Retrying the same request re-runs resolution.
8. **No configured registry source by default.** Production composes `UnavailableRegistrySource`: unknown identities stay `IDENTITY_SOURCE_UNAVAILABLE` (UNKNOWN), never invented. Choosing and authorizing a real registry source (licence, network, coverage — e.g. GLEIF for LEI holders, a national business register) is a separate CTO decision behind the same port.

## Consequences

- Two Tenants observing one company share one canonical Organization and keep separate private Foci; removing a Focus never deletes the Organization.
- The Customer Zero operator catalog keeps its legacy `org:axignal` binding (`legacy-fr30`), which has no registry evidence; it is not bridged into the subscriber store.
- Admission is global: an entitled Tenant at capacity may cause a registry-attested identity to be admitted, but receives no Focus.

## Amendment 2026-10-16: identity verification is an optional upgrade, not a gate to observe

- **Status:** Proposed (CTO decision requested in review).
- **Authority:**
  - MASTER §22 (line 1377): an agency may create 100 Foci over clients, competitors or targets without proving it represents any of them, because a Focus **writes nothing about them**; it only directs persistent observation.
  - MASTER §15.3: the official website is the source for declared products and capabilities; registry and authority are the source for legal identity.
  - MASTER §15.4: UNKNOWN ≠ FALSE.

**Measured problem.** The first real pilot (a Spanish shop, 2026-10-16) stayed `IDENTITY_PENDING / IDENTITY_SOURCE_UNAVAILABLE`. The only configured registry is GLEIF, which covers LEI holders. Its consequences:
- No Focus is created, and the autonomous loop has nothing to observe.
- Every small business without an LEI, and every competitor (whose identity a subscriber can never verify), is blocked.

The gate is stricter than the MASTER requires.

**Decision (proposed).**

1. **Web-anchored subject.** When admission ends `IDENTITY_PENDING` for a locator with a public website, the portfolio may create the Focus on a **web-anchored subject**:
   - its id is `org:web:<sha256(registrable domain)>`;
   - it is stored in its own operational store (`web-subjects.sqlite3`), **never in the canonical Organization store or AXIGLAND**;
   - it carries only the registrable domain, the locator and the creation time.
2. **What it may observe.** Everything public whose source is the website or public surfaces about it: presence (SEO, GEO, web), reputation, value (declared offer), markets, relationships, demand, activity, context and evolution in time.
   - Legal-identity predicates stay **UNKNOWN** with `IDENTITY_NOT_VERIFIED`, as the first observation already shows: legal name, registrations, register filings, accounts, awards bound to a legal entity, and group structure.
   - Nothing about a web-anchored subject is a canonical write or a FAXT.
3. **A website still never admits identity.** Item 4 of this ADR is unchanged. The subject is attention plus observation, never a legal identity. Display uses the domain, not an invented legal name.
4. **Verification is an optional upgrade.** The subscriber (or AXIGNAL, when a registry source later resolves the same locator) may verify the identity:
   - registry admission creates or finds the canonical Organization;
   - the Focus is re-pointed with the existing `replace` flow;
   - the web-anchored observation history stays attached to the Focus, so continuity is not lost;
   - the newly reachable legal predicates are then observed.
5. **Unchanged:**
   - INVALID_INPUT, CONFLICT and AMBIGUOUS keep their current outcomes;
   - private hosts and IPs are still rejected;
   - capacity and entitlement rules are unchanged;
   - one Tenant's Focus never writes anything about the organization.

**Consequences.**
- Small businesses and competitors can be observed continuously from day one.
- Verified identity becomes a value-adding upgrade: it unlocks registry, financial and award facts.
- Two Tenants observing the same domain share one web-anchored subject, as with canonical Organizations.
- Merging a later verified identity is explicit and auditable.
