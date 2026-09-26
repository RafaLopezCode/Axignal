# Tasks: P0-HFX-00

## 1. Preflight and source audit

- [x] Verify repository, clean base, merged P0-DRI-00 and PR #18 state/head.
- [x] Read all `.md` reference files in the CTO HFX source pack without copying
  the directory into the repository.
- [x] Read MASTER, Constitution, relevant ADRs, Subscriber Experience, design
  governance, Xeed architecture and Graphify/design guidance.
- [x] Query Graphify for HFX-related architecture relationships.
- [x] Independently check HCI, accessibility and PostgreSQL/pgvector assertions.

## 2. Canonical doctrine and architecture

- [x] Add durable HFX doctrine to MASTER; update pinned hash after final edit.
- [x] Derive binding HFX constraints in Constitution.
- [x] Create/index ADR-0016 and ADR-0017; leave physical storage unselected.
- [x] Converge Subscriber Experience, Design Doctrine and Design Governance.
- [x] Record three context authorities, continuity/provenance, AXENT typed
  routing, multi-client/portfolio scopes, security tests and SQL/vector caveats.

## 3. Research and Spec Kit

- [x] Add HCI evidence synthesis with study limits and source links.
- [x] Add human-level information taxonomy and conceptual Human Output Contract.
- [x] Add user research protocol and acceptance scenarios A–J.
- [x] Create spec, clarifications, research, plan, architecture review, tasks and
  requirements checklist.
- [x] Review cross-document local links and terminology; all checked links resolve.

## 4. Adversarial audit and quality gates

- [x] Verify no unauthorized runtime/schema/UI/provider/dependency/deployment
  changes and no source-pack dump.
- [x] Verify no `.env` read/write, no TypeSafe key access, no provider/JeV calls,
  and no HFX-01/DRI-01/JEV-04 start.
- [x] Run frozen sync, formatting, lint, mypy, pytest, Architecture Guard and
  git diff check; record the local governance exception and outcomes in
  `validation.md`.
- [x] Refresh/diagnose Graphify structurally and review resulting scope.
- [x] Verify PR #18 remains OPEN/unmerged at the expected SHA and untouched.
- [x] Publish the documentation-only branch and create one unmerged PR against
  main.
- [x] Verify green remote CI for the exact final PR head and return the CTO
  ledger. Exact remote run/head details are captured in the closure ledger.
