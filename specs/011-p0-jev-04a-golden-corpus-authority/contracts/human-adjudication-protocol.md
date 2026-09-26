# Independent human adjudication protocol (frozen design; not executed)

**Guide version:** `P0-JEV-04A-HAG-1.0`
**Guide file:** [`annotation-guide-P0-JEV-04A-HAG-1.0.md`](annotation-guide-P0-JEV-04A-HAG-1.0.md)
**Guide SHA-256:** `00d74947fa3b052d2e384158aec801f2cbd62c5f2750cc3d6e94564c5ff1908d`
**Annotators:** at least 2 independent annotators; one separate independent third adjudicator (or documented equivalent).
**Blinding:** `BLINDED_TO_JEV=YES`; `BLINDED_TO_FUTURE_MODEL_OUTPUTS=YES`.

## Materials and procedure

Annotators receive the exact claim, evidence passages with provenance/date, the vNext.2 answer definitions, time/as-of context, and written inclusion/exclusion rules. They do not receive model outputs, expected procedural labels, source-family class balance, or another annotator's work. Each independently selects one answer and records (a) the decisive evidence span(s), (b) relation rationale, (c) temporal/scope assumptions, and (d) uncertainty.

Answer space, frozen to the applicable contract: `SUPPORTED`, `PARTIAL`, `CONTRADICTED`, `NOT_SUPPORTED`, `NO_EVIDENCE`, `CONFLICTING`, `UNRESOLVED`.

## Disagreement and quality

Preserve original independent labels and rationales. Use nominal multiclass Krippendorff's alpha as the predeclared inter-annotator agreement statistic, report raw agreement and class-wise confusion as descriptive context, and do not use an agreement threshold to erase hard disagreements. The adjudicator reviews both rationales and source material independently, records a reasoned resolution, or assigns `UNRESOLVED`/exclusion. Majority vote is not a substitute for semantic adjudication.

## Ambiguity and exclusions

Exclude cases with unclear claim scope, temporal mismatch, unresolvable entity identity, insufficiently preserved evidence, unclear rights, unfilterable person data, unrecoverable provenance, or leakage overlap. `NO_EVIDENCE` requires a bounded search protocol and logged sources/query scope; absence from a partial dataset alone is not enough. Preserve genuinely conflicting sources as `CONFLICTING` only when both are in-scope and temporally aligned. Use `UNRESOLVED` when careful review cannot support a determinate class.

## Freeze and mutation

Annotator instructions are versioned and hashed before held-out review begins. Held-out adjudication must finish and labels be frozen before Jev is called. `LABEL_MUTATION_AFTER_JEV=FORBIDDEN`. Corrections require a new dataset version with an audit trail and cannot silently replace evaluated gold.

This protocol is design-only: no annotator was engaged, no case was labeled and no golden provenance is claimed.
