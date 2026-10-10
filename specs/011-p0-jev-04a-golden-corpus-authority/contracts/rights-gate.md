# Rights and transmission gate

For each source, create a machine-readable record with: `SOURCE_ID`, `SOURCE_NAME`, `SOURCE_OWNER`, official source/license URLs, `OBSERVED_AT`, `CONTENT_TYPE`, copyright, license, database-right status, commercial reuse, modification, attribution, share-alike, third-party content and rights, personal/sensitive data, automated access/API terms, derived-data/storage/redistribution rights, provider transmission, evidence notes, and `LICENSE_STATUS`.

Permitted evidence statuses are `CONFIRMED`, `INFERRED`, `UNKNOWN`. `LICENSE_STATUS` is exactly `CLEAR`, `CONDITIONAL`, `UNKNOWN` or `REJECTED`.

## Hard rules

1. Public accessibility does not imply reuse permission.
2. A blanket source permission does not clear third-party exhibits, images, submitted documents or per-record restrictions.
3. CC0 source rights do not automatically grant rights to transmit content to a provider; the provider contract and customer input license are a separate gate.
4. For future live use, source rights, commercial reuse and provider transmission must each be `CLEAR` / `YES`, with attribution and share-alike obligations implementable. No score or waiver compensates an unknown.
5. A `CONDITIONAL`, `UNKNOWN` or `REJECTED` source is excluded until the condition is resolved and a new reviewed manifest records the evidence.
6. Provider transmission requires review of current MSA, privacy policy, DPA and service/API terms. “No model-weight training” must never be recorded as “no processing.”
7. This contract is a technical screening rule, not a legal opinion.

The source-level records and fail-closed results are in `../corpus-candidates.json`; provider clause analysis is in `../research/provider-transmission-analysis.md`.
