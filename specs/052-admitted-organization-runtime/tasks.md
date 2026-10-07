# Tasks

Reconciled with the repository on 2026-10-07 (ADR-0087). Earlier state: the store and
composition existed, but no production path wrote canonical identities and only exact
legal names resolved, so every real subscriber locator stayed pending.

- [x] T001 Specify, clarify and review the bounded admission/materialization seam.
- [x] T002 Persist exact admitted legal names and provenance behind admission.
      Was partial (legal name only, no production writer). Now: legal name, registry
      identifiers and registry-recorded websites, each with evidence ref, digests,
      policy and observation time; atomic `admit`; uniqueness under concurrency.
- [x] T003 Resolve global canonical identities with ambiguity/integrity/topology checks.
      Was exact-name only. Now: `OrganizationAdmissionService` — identifier → website →
      exact name over the canonical index, then an independent registry source;
      RESOLVED_EXISTING / ADMITTED_NEW / IDENTITY_PENDING / AMBIGUOUS / CONFLICT /
      INVALID_INPUT; integrity and topology revalidation withhold identities.
- [x] T004 Prove restart, replay, negative authority and shared-identity behavior.
      `tests/organization_admission/`, `tests/integration/test_organization_admission_e2e.py`.
- [x] T005 Integrate root composition and converge with repository gates.
      The portfolio resolves through the admission service over the same store; the
      registry source is injected (production default: unavailable → pending).
- [ ] T006 Select and authorize a governed production registry source (CTO decision).
