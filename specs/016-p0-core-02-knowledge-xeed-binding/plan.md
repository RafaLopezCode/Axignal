# Implementation Plan: P0-CORE-02 Canonical Knowledge-to-Xeed Binding

**Branch**: `architecture/p0-core-02-knowledge-xeed-binding`
**Base**: `6628d73a2f5931119069961d3cc9acb43be809fc`
**Spec**: [spec.md](spec.md)

## Summary

Add a typed global FAXT identity, immutable private Xeed-to-FAXT reference,
AuthorizedXeed-only application read contract, deterministic test/dev
authority, adversarial contract tests, and an ADR documenting exact scope.

## Technical context

- Python 3.11+, standard library only.
- Existing domain/application dependency direction is retained.
- Existing AuthorizedXeed is the only private read capability.
- No production persistence, write adapter, migration or external service.

## Design

```text
AuthorizedXeed + FaxtId
          ↓
lookup exact XeedFaxtReference
          ↓ (only if present)
resolve global FAXT by FaxtId
          ↓
AuthorizedXeedFaxt wrapper around original objects
```

Reference data contains no timestamp, lifecycle, provenance, confidence,
relevance, importance, discovery or source-rights fields. The result wraps the
existing canonical FAXT instance; it does not construct a private copy.

## Validation

Run unit/contract tests and every applicable local deterministic gate listed
in AGENTS.md and the P0-CORE-02 CTO order. TypeScript is not applicable to this
Python-only domain/application slice. Graphify structural update/check is
required; semantic extraction is prohibited/not required.

## Risks and rollback

The new reference deliberately has no temporal or lifecycle semantics.
Missing, stale, revoked or inaccessible FAXT behavior beyond fail-closed
resolution remains outside the contract. This isolated additive branch has no
data migration; reverting the branch removes the domain/application contract
and its tests/docs.
