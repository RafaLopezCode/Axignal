# Plan: P0-HFX-00 Human First Cognitive UX Doctrine

## Objective and boundaries

Converge the CTO Human First research iteration into AXIGNAL's governed
product, engineering, architecture and research artifacts. Work on a dedicated
documentation-only branch based on the verified P0-DRI-00 main. Preserve PR #18
untouched. Do not start runtime, UI or adjacent slices.

## Workstreams

1. Audit the complete source pack as reference input, canonical authorities,
   relevant ADRs, subscriber/design/graph guidance, Xeed architecture and
   current PR/base state.
2. Research empirical and technical assertions against primary papers,
   standards and official documentation. Label evidence, guidance, inference,
   CTO hypothesis and canonical decision.
3. Add durable HFX product doctrine to the single MASTER; refresh pinned hash.
4. Derive Constitution constraints and create ADR-0016 (Human First capability)
   and ADR-0017 (private continuity/context boundary; storage selection remains
   open).
5. Converge Subscriber Experience, Design Doctrine/Governance and architecture
   documentation in place; preserve Today/Explore/Evolution/Evidence/Ask AXENT.
6. Create consolidated HFX research, human-output/taxonomy/visual grammar,
   cognitive memory/context routing and user-validation artifacts.
7. Complete Spec Kit: spec, clarifications, research, plan, architecture
   review, tasks and requirements checklist.
8. Audit authority consistency, private scope, uncertainty, storage
   non-decision, source-pack non-copying and absence of unauthorized scope.
9. Run all frozen gates, diff/scope audit, Graphify update/diagnose, push branch,
   open one unmerged PR and verify exact-head remote CI. Preserve PR #18 and
   stop before merge.

## Affected surfaces

MASTER and checksum; Engineering Constitution; ADR index/new ADRs; subscriber
product specification; design doctrine/governance; architecture overview/new
HFX architecture; docs index; HFX research documents; `specs/014-.../**`.
No runtime, provider, schema, UI, dependency or deployment files.

## Risks and controls

- **Hypothesis becomes fact:** label CTO hypotheses and AXIGNAL inferences;
  report no AXIGNAL user-study result.
- **Canonical state drift:** preserve existing epistemic vocabulary and DRI
  doctrine; do not collapse observed/potential/unknown/stale/historical.
- **Private memory becomes truth:** separate AXIGLAND, Xeed process and user
  continuity; EvidenceAdmission remains the only canonical write boundary.
- **Cross-client leakage:** scope before retrieval; portfolio intent and
  permission explicit; vector similarity is never authorization.
- **Premature infrastructure selection:** document PostgreSQL/pgvector only as
  a benchmarkable hypothesis; no extension or runtime change.
- **Accessibility overclaim:** WCAG 2.2 AA target plus COGA-informed research;
  no claim that conformance proves comprehension.
- **Research source limits:** report study task/population and avoid universal
  UX prescriptions.
- **Unauthorized worktree changes:** preserve local artifacts; never inspect or
  touch `.env`; no reset/clean.

## Rollback

Use a reviewed revert of this documentation slice and matching MASTER hash if
the CTO rejects the canonization. Preserve unrelated local/ignored artifacts,
branch history and PR #18. Never reset/clean or inspect `.env`.

## Verification

Run `uv sync --frozen`, Ruff format/check, mypy, full pytest, Architecture
Guard, axignal-governance, `git diff --check`, Graphify structural update and
diagnostics. Verify MASTER checksum, documentation-only diff, no source-pack
copy, no `.env` access, no unauthorized paths, PR #18 exact state, no runtime
calls, no implementation of HFX-01, DRI-01 or JEV-04, and remote CI green on
the exact PR head.

## Next-slice boundary (not started)

Recommended next: `P0-HFX-01_INFORMATION_ARCHITECTURE_AND_HUMAN_OUTPUT_CONTRACTS`.
It is not authorized by this slice and must not begin here.
