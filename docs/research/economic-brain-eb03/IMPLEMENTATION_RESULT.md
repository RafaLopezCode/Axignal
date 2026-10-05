# EB-03 — Source Rights & Reuse Registry implementation result

**Base:** main@23a6453
**Branch:** cto/eb03-source-rights
**Status:** IMPLEMENTED; final repository validation pending at document creation time.

## Implemented

- Versioned source policy lineage across SourceDispatchPolicy, SourceRequest and SourceObservation.
- Deterministic StaticSourceRegistry with source/instrument, purpose, rights, access, scope, currentness, retention, rate and robots metadata.
- One registry authorization emits both acquisition policy and ObservationReuseAuthority, preventing independent widening.
- ObservationReuseAuthority persists registry id/version, explicit reuse reason and retention/robots/rate references while remaining backward-compatible for historical rows.
- HTTP sensor rejects request/policy version mismatch before DNS and persists version in the immutable observation envelope.
- Ingestion rejects observation/request policy-version mismatch before Observation Memory mutation.
- Prime validates policy version and records the semantic policy version in Learning Memory rather than misusing a fingerprint as version.
- FirstProof now derives public-homepage dispatch and reuse metadata from one narrow registry entry.
- Deterministic adversarial tests cover rights UNKNOWN/PROHIBITED, inaccessible sources, wrong purpose, wrong instrument, robots fail-closed, policy-version mismatch and reuse-authority serialization.

## Deliberately not implemented

- No crawler or subresource authorization. FirstProof is one bounded public root document.
- No robots.txt fetch/parser. The FirstProof entry explicitly uses NOT_REQUIRED_SINGLE_DOCUMENT; any source requiring robots evaluation fails without explicit PERMITTED metadata.
- No actual host rate-bucket runtime yet; rate policy is registered metadata.
- No automated raw-data deletion/retention worker yet; retention policy is registered metadata.
- No persistent/admin-editable registry, scheduler, conditional GET or shared monitoring worker.
- No legal conclusion is inferred from registry metadata.
- No canonical FAXT/Relationship authority is added.

These limitations remain blockers for broad autonomous monitoring, not for the narrow EB-03 contract.

## Evidence so far

Focused chain after registry integration:
- registry + reuse + HTTP: 53 passed.
- FirstProof + registry + HTTP: 60 passed.
- source acquisition + Prime + FirstProof + registry: 65 passed.
- latest acquisition/Prime/FirstProof/registry/reuse after policy-version closure: 79 passed.
- focused Ruff checks: PASS.

## Final validation

- Full repository pytest: **1116 passed in 89.86s** using a basetemp outside the repository.
- Ruff focused checks: PASS.
- Mypy: **Success, no issues found in 264 source files**.
- Architecture Guard: PASS, no violations.
- AXIGNAL Governance: PASS for architecture, deps, docs, graphify, hygiene, no-generated-data, spec and terminology.
- git diff --check: PASS.

A final exact-state format/check/gate pass is required immediately before commit; no deployment is authorized by EB-03.
