# Implementation Plan: P0-CORE-03 Authorized Xeed FAXT Collection Read

**Branch**: `architecture/p0-core-03-authorized-faxt-collection`
**Base**: `9d159f5225441305e1dbedb8cec9b9277559189a`
**Spec**: [spec.md](spec.md)

## Design

Extend the application read boundary with a collection reader whose entry
point requires `AuthorizedXeed`. Its reference port lists only that Xeed's
references. Validate the complete reference set and reject duplicate or
malformed entries before resolving canonical FAXTs. Resolve in stable
`FaxtId` order, reuse `AuthorizedXeedFaxt`, and fail the whole read on any
dangling or mismatched FAXT.

```text
AuthorizedXeed
      ↓
list_for_xeed(AuthorizedXeed.xeed.id)
      ↓ validate exact-Xeed references, reject duplicates
      ↓ stable FaxtId order (determinism only)
resolve original global FAXTs
      ↓
tuple[AuthorizedXeedFaxt, ...]
```

Only the in-memory test/dev authority implements the new scoped list port.
There is no production persistence or writer and no Evidence dependency.

## Validation

Run the required local deterministic gates in `AGENTS.md` and the CTO order,
including contract tests, Architecture Guard, governance, structural Graphify,
and deterministic build. No runtime/provider calls or secret access.
