# Corpus authority contract

## Per-case fields required before any future corpus admission

`case_id`; `decision_family`; `question_id`; `question_version`; `answer_space_version`; natural/procedural stratum; claim text and source id/revision/URI/publication timestamp; evidence text and source id/revision/URI/publication and valid-time; retrieved-at; observation-time; as-of-time if material; transformation id/version/hash if procedural; gold authority id/type; annotator labels/rationales/evidence spans and adjudication record if human; rights-gate record ids; privacy-filter result; source-independence class; self-confirming/circular flags; leakage clusters; split assignment; exclusion status/reason.

## Authority invariants

- A gold label has an identified authority and derivation path independent from the evaluated model.
- Natural claim/evidence text exists before benchmark construction and is not model-generated or template-rendered.
- Procedural text is marked procedural and carries a deterministic renderer version/hash.
- A claim, evidence and expected class derived from the same record is circular procedural gold and cannot be presented as independent factual confirmation.
- Human-gold labels require two independent blinded annotations and separate adjudication under `human-adjudication-protocol.md`.
- Freeze held-out labels before any future Jev calls. Any post-call mutation is forbidden; corrections require a new corpus version and disclosure, not silent overwrite.
- Rights, provider transmission and privacy are independent hard gates; all must be clear for each admitted source/case.
- Missing records do not establish `NOT_SUPPORTED`, `NO_EVIDENCE`, `CONTRADICTED` or any other class.

## Dataset-level manifest

Freeze source-selection rules, source license snapshots/URLs and observed date, inclusion/exclusion rules, class coverage report, independent annotation guide hash, transformation code/version/hash (if procedural), near-duplicate method, split unit assignments, retrieval timestamps, and a manifest hash before held-out evaluation. No dataset manifest or cases are created in this slice.
