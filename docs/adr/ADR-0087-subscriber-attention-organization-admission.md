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
