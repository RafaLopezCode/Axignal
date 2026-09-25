# Data Model: P0-JEV-03

## Smoke Result

- `artifact_type`: `p0-jev-03-smoke-result`
- `timestamp_utc`: local observation time in ISO-8601 UTC form
- `smoke_id`: fixed slice identifier
- `source_revision`: Git SHA captured before the request
- `case_id`, `corpus_version`, `question_id`, `question_version`, `grammar_version`
- `state_contract_version`, `state_compiler_version`, `state_variant_id`, `state_variant_version`, `state_fingerprint`
- `requested_model`; `resolved_model` only when returned as a string
- `primitive`: existing grammar value (`CHOICE`)
- `raw_answer`: whitelisted selected choice, provider probability mapping when present, provider confidence when present
- `normalized_judgment`: current provider-independent laboratory judgment
- `provider_usage`: only fields actually reported by the provider; absent values stay absent
- `latency_seconds`: local monotonic duration if measured
- `retry_count`: zero as enforced by the client policy
- `adapter_version`, `sdk_version`
- `failure_category`: safe enumerated category or null
- `smoke_gate`: operator-evaluated pass/fail with reasons; it does not claim model quality
- `result_id`: digest over all preceding artifact content

No credential, SDK response object, exception text, request/response body, header, or identifier derived from the credential is part of this entity.

## Controlled Experiment Result

Uses the immutable P0-JEV-02 `decision-lab-result` shape: original experiment definition and digest, all 10 records, source judgments, distributions, normalized judgments, compositions, labels, safe failure categories, provider metadata, metrics, predeclared evaluator result, pricing policy when calculable, and reproducibility manifest. No result fields are backfilled from inference.

## Replay Result

Contains a reference to the verified source digest and deterministic recomputation of normalizations/compositions/metrics/outcome. It is a separate create-only artifact; it does not replace the source observation.
