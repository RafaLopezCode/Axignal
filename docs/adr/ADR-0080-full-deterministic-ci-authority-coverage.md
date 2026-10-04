# ADR-0080 — Full Deterministic CI Authority Coverage

**Status:** ACCEPTED  
**Date:** 2026-10-04  
**Scope:** AUD-09; GitHub Actions deterministic validation; cognitive and epistemic test coverage  
**Derives from:** MASTER §56.19; Engineering Constitution X; deterministic validation doctrine

## Context

AXIGNAL's CI validation job executed pytest only for four explicitly named directories:

- tests/unit
- tests/experiments
- tests/contracts
- tests/architecture

The repository's pytest configuration declares `testpaths = ["tests"]`, but the CI path filters bypassed many test families that exercise runtime cognitive and epistemic boundaries.

Immediately before AUD-09, the complete suite collected 1017 tests while the old CI path selection collected only 706. 311 tests were therefore outside the pytest CI gate.

Omitted families included economic discovery, subscriber projection, source acquisition, source representation, semantic extraction, pipeline and Xeed germination. Architecture Guard remains necessary, but import/AST constraints do not execute semantic negative cases.

## Decision

The deterministic validation job executes exactly one unfiltered pytest command:

```
uv run pytest
```

No pytest directory/path filters are allowed in the canonical CI workflow.

Because pyproject.toml declares:

```
testpaths = ["tests"]
```

every pytest-discoverable test under tests/ participates in the same CI exit code, including future top-level test families.

### Permanent authority coverage contract

`tests/contracts/test_aud09_ci_authority_coverage.py` protects the CI boundary.

It verifies that:

1. the canonical CI workflow contains exactly one pytest invocation;
2. that invocation is `uv run pytest` with no directory filter;
3. pytest testpaths remains `tests`;
4. critical negative cases are actually collectable by pytest;
5. critical top-level suite families remain under the full testpath.

The collection contract includes representatives for:

- proposition-bound EvidenceAdmission;
- canonical/relationship OBSERVED materialization;
- subscriber explainability and narrative integrity;
- tenant/private evidence authorization;
- temporal currentness/reuse;
- deterministic model/extraction failure;
- fiscal evidence/as-of authority;
- legacy evidence replay conflict.

### Determinism

AUD-09 does not add external network, LLM or provider dependencies to CI.

Tests may use deterministic local fixtures, in-memory components, SQLite temporary stores and loopback-only runtime tests. External provider/network behavior remains mocked or adapter-bounded.

### Failure semantics

There is one pytest process responsible for the entire repository testpath. Therefore a failing collected test in any suite family makes that CI step non-zero and fails deterministic validation.

New test directories under tests/ cannot be silently omitted merely because CI was not edited to enumerate them.

## Invariants

```
CI_GREEN => FULL_DETERMINISTIC_TESTPATH_PASSED
NEW_TEST_FAMILY_UNDER_TESTS => INCLUDED_BY_DEFAULT
ARCHITECTURE_GUARD != SEMANTIC_AUTHORITY_TESTS
IMPORT_SAFETY != AUTHORITY_SAFETY
EXTERNAL_LLM_OR_PROVIDER != DETERMINISTIC_CI_DEPENDENCY
```

## Consequences

CI duration increases modestly, but its green status now covers the complete deterministic test surface rather than a hand-maintained subset.

Future authority regressions in admission, projection, tenancy, temporal logic, fiscal gates, replay handling or cognitive execution cannot remain invisible merely because their test directory is absent from a workflow list.
