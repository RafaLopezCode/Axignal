# Annotation guide P0-JEV-04A-HAG-1.0

This is a protocol artifact only. No cases have been selected or labeled.

## Task

For the exact claim and supplied evidence, determine the relation in the specified time and scope. Use only the supplied evidence bundle and documented context. Do not introduce outside knowledge unless a later preregistration explicitly defines a bounded source-search protocol for a `NO_EVIDENCE` decision.

## Labels

- `SUPPORTED`: evidence supports the full in-scope proposition.
- `PARTIAL`: evidence supports only a material subset of the proposition, and the unsupported remainder is identifiable.
- `CONTRADICTED`: evidence directly supports an incompatible proposition within the same entity, scope and time.
- `NOT_SUPPORTED`: a bounded evidence set does not substantiate the claim, but there is not enough basis to say there is no evidence in the defined search scope.
- `NO_EVIDENCE`: a predeclared, completed, bounded search finds no admissible evidence relevant to the claim. Missingness in one dataset alone is insufficient.
- `CONFLICTING`: admissible, in-scope sources support incompatible conclusions for the same relevant time/scope and neither resolves the conflict.
- `UNRESOLVED`: ambiguity, identity, scope, time or source quality prevents a defensible determination.

## Required annotation record

Each annotator records exactly one label, decisive evidence span(s) or `NONE`, a concise rationale tied to those spans, the entity/scope/time interpretation, uncertainty, and any exclusion concern. Each annotator works independently and blind to other labels, expected procedural class and all model outputs.

## Disagreement

Preserve both annotations and rationales. A separate reviewer compares them against the source bundle, documents a reasoned resolution or retains `UNRESOLVED`/excludes the case. Do not resolve by majority vote. Report nominal multiclass Krippendorff's alpha and raw agreement; do not hide low agreement or class-specific disagreement.

## Exclude when

Rights are not clear; person data cannot be removed; source/version/time cannot be traced; the claim is materially ambiguous; evidence was altered/generated; entity matching is uncertain; evidence scope is insufficient to distinguish labels; or the case leaks across development/held-out units. Do not force a label to preserve sample size.

## Freeze rule

Complete held-out annotation and adjudication and freeze labels before any future Jev call. Post-call label mutation is forbidden. Any correction requires a new corpus version, audit record and separate reporting.
