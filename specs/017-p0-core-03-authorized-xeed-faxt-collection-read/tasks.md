# Tasks: P0-CORE-03 Authorized Xeed FAXT Collection Read

## Application boundary

- [x] T001 Add a Xeed-scoped reference collection port.
- [x] T002 Add an AuthorizedXeed-only collection reader.
- [x] T003 Preserve the existing authorized FAXT wrapper and fail closed for
  invalid, duplicate and dangling collection members.
- [x] T004 Define deterministic identity ordering without semantic ranking.

## Adversarial proof and governance

- [x] T005 Extend the test/dev in-memory authority with scoped reference listing.
- [x] T006 Cover isolation, lookup ordering, fail-closed behavior and semantic
  non-invention.
- [x] T007 Record the CTO decision and update current architecture/spec status.
- [x] T008 Run all required local gates, Graphify structural update/check and
  local diff secret-safety review. Gitleaks remains a required remote PR check.
- [ ] T009 Self-audit, commit, push, open one PR, and verify exact-head CI.
