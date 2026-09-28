# Plan: P0-HFX-00 Golden Master and Subscriber Boundary

**Base:** `dbd347861040070e673891953da4b8cdd3c754a6`
**Branch:** `architecture/p0-hfx-00-golden-master-boundary`
**Spec:** [spec.md](spec.md)

## Work units

1. Record the source inventory and exact-byte SHA-256 recipe in a versioned
   external-root-independent manifest.
2. Add standard-library tooling that verifies inventory, per-file digests,
   aggregate digest, missing paths, unexpected V2 source files and symlinks.
3. Test the recipe on temporary trees for repeatability, order independence,
   byte sensitivity, generated-output exclusion and fail-closed behavior.
4. Document the authorized read-to-projection boundary and field matrix from
   actual CORE models/readers and current presentation source.
5. Run canonical repository gates, repeat external manifest verification, and
   record the result without asserting visual equivalence or production state.

## Architecture

The manifest tool lives in `tools/governance/`; it is a deterministic local
governance utility and has no runtime dependencies. The future projection is
specified as an application-layer, read-only assembler. It is not implemented
in this plan. `apps/web` remains a renderer of governed output and ephemeral
interaction state.

## Explicit exclusions

No frontend runtime, projection code, domain changes, database, API,
authentication, Context Broker/Router, persistence, evidence lookup, model or
provider integration, Golden Master source change, HFX-01, deployment, or
visual redesign.
