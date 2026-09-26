# Clarifications — P0-JEV-04A

## Resolved from the controlling order

- `CES.SUPPORT.vNext.2` is the target question/answer-space version; vNext.1 history is immutable.
- Independent human labels created later are `INDEPENDENT_HUMAN_GOLD`, not `PREEXISTING_GOLD`.
- This slice may freeze an annotation protocol but may not execute annotation or claim valid golden provenance.
- Procedural cases are explicitly constructed and cannot substantiate real-world natural-language or production claims.
- A source with `LICENSE_STATUS != CLEAR` or `MODEL_PROVIDER_TRANSMISSION_ALLOWED != YES` is ineligible for a future live run.
- No ambiguity in provider terms is resolved by inference; the transmission result is `UNKNOWN` and fails closed.
- No data sample was downloaded, no records/cases were made, and no provider/runtime call occurred.

## Research-specific decisions

- Route B remains the strongest natural candidate for further feasibility work: human-authored company filings and genuinely final, contested regulator findings, with independent blinded human adjudication. Settlements, allegations, press releases, and self-reported filings are not automatically independent findings.
- GLEIF Level 2 is the strongest procedural candidate found. A same-record-derived proposition, rendered evidence and label is allowed only as a declared controlled semantic test with `SELF_CONFIRMING_GOLD=YES` and `CIRCULAR_LABEL_AUTHORITY=YES`.
- This decision does not treat uncertainty as a negative result. It records a blocked engineering gate, not a legal opinion and not proof that an acceptable corpus cannot eventually be built.

## Unknowns that remain blocking

- TypeSafe MSA §2.3's restriction on using Services or Output to develop a similar/competing service and its interaction with AXIGNAL's benchmark/development purpose requires a clear written interpretation or contractual clarification before any future transmission. The service's subprocessor list was not independently confirmed during this review.
- No small sample feasibility audit was performed, so a realistic yield across eligible class strata, independent documents and held-out partitions remains unproven.
- SEC record-level exclusions for third-party exhibits and privacy must be checked document by document; GLEIF record-level person filtering and relationship semantics must also be verified before any sample is admitted.
