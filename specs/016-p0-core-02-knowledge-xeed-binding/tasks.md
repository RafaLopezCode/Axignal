# Tasks: P0-CORE-02 Canonical Knowledge-to-Xeed Binding

## Contract and domain

- [x] T001 Record CTO ontology and out-of-scope rules in the spec.
- [x] T002 Add typed FAXT identity and immutable `(XeedId, FaxtId)` reference.
- [x] T003 Add reference/FAXT-separated in-memory test authority.

## Authorized application read

- [x] T004 Add AuthorizedXeed-only reader and fail-closed outcomes.
- [x] T005 Check contextual reference before global FAXT resolution.
- [x] T006 Return the original FAXT object without copying or upgrading state.

## Adversarial proof and governance

- [x] T007 Add authorization, isolation, reuse, enumeration and negative tests.
- [x] T008 Add ADR and update architecture status without rewriting history.
- [x] T009 Add Spec Kit artifacts following the next existing number.
- [ ] T010 Run applicable local gates and Graphify structural update/check.
- [ ] T011 Review diff and self-audit; commit, push and open unmerged PR only if
  every required gate passes.
