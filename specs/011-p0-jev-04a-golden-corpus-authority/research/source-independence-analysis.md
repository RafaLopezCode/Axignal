# Source independence and authority

## Roles must be recorded separately

For each future case, retain the identity and version of (1) claim source, (2) evidence source, and (3) gold authority. Classify each relationship as `SAME_RECORD`, `SAME_DOCUMENT`, `SAME_ORGANIZATION_DIFFERENT_DOCUMENT`, `INDEPENDENT_ORGANIZATION`, `INDEPENDENT_REGULATOR`, `INDEPENDENT_HUMAN_ADJUDICATION`, or `MULTI_SOURCE`.

The labels `SELF_CONFIRMING_GOLD` and `CIRCULAR_LABEL_AUTHORITY` are mandatory when the same source assertion determines both the rendered relation and expected class. A deterministic transformation does not make its own source an independent authority.

## Candidate analysis

- **SEC Route B:** A registrant's filing is a human-authored claim source, but not independent corroboration of its own statement. An SEC final contested order can be an independent regulator source for the precise finding it actually makes. Settlements, complaints, allegations and press releases do not automatically meet that condition. A separate blinded human panel must adjudicate each claim/evidence pair against the written protocol. Independence is case-specific and must be retained as provenance, not inferred from institutional labels.
- **GLEIF Route C:** If a GLEIF relationship record supplies the source relation, a renderer creates the claim/evidence and the record determines expected class, then `SAME_RECORD`, `SELF_CONFIRMING_GOLD=YES`, `CIRCULAR_LABEL_AUTHORITY=YES`. This is a valid procedural test of whether a system maps the supplied fields and wording to a controlled relation. It is not independent natural gold and cannot validate external truth beyond the dataset's recorded field.
- **Wikidata:** Record the exact statement revision and each reference separately. Wikidata's statement and the referenced publisher are distinct authorities and rights sources.
- **Companies House / TED:** Registry/notice assertions are attributable to filer or contracting authority; attribution does not establish truth. Human adjudication and evidence-source separation remain necessary.

No majority vote may hide semantic uncertainty. Preserve both annotators' labels, rationale and evidence spans, adjudication rationale, and unresolved/excluded outcome.
