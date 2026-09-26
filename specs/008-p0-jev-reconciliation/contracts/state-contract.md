# Family State Contracts V-next

## Claim evidence support

Requires an explicit non-empty claim proposition and at least one evidence record with non-empty semantic passage and provenance source reference. If currentness is part of the claim, an explicit temporal reference is also required. `evidence_id` is a resolver key, never passage content.

## Entity alignment

Requires two non-empty named entity records (`a`, `b`) and semantic evidence with provenance. The decision target is same legal entity versus related, distinct or unresolved. Brand/parent relationships do not establish legal-entity identity. Exact ID equality is deterministic and should run before an evaluator.

## Economic relationship

Requires two endpoints, an explicit relation proposition, declared direction, semantic evidence and provenance. Temporal context is required when the case declares a currentness question. Relationship existence, type, time and contradiction are separate dimensions except in a named experiment that declares a compound comparator.

## Missingness and source assembly

The wire state preserves `ABSENT`, `EMPTY`, `UNKNOWN`, `UNAVAILABLE`, `NOT_APPLICABLE` and `PRESENT` distinctions. Assembly resolves only explicit references from the supplied catalog. Unknown IDs remain unresolved and block answerability. Normalization never guesses, fills empty strings, substitutes identifiers or infers absent content.
