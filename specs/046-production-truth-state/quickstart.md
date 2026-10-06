# Quickstart: Validate EB-04 Truth-State Preservation

This guide covers verification of the architecture-reviewed EB-04 implementation.

## Preconditions

- Root architecture review has approved exact authority/predicate mappings and unresolved-visibility behavior.
- The implementation preserves the selected policy/version with the output and does not change global FAXT defaults.

## Focused validation cases

1. Run the EB-04 official-web capability case. Expect `EconomicObservation=DECLARED` and `FAXT=DECLARED`; verify exact evidence, predicate/value, span, time, currentness, and rights reference.
2. Run an exact admitted registry identity/legal_identity/registration proposition. Expect `EconomicObservation=OBSERVED` and FAXT `OBSERVED` for the registry proposition only; verify exact evidence and identity/source-authority checks.
3. Run unsupported authority/predicate pairs. Expect canonical materialization to fail closed, no `OBSERVED` fallback, no `FALSE`, and no `UNKNOWN` FAXT.
4. Run the official-web declaration with unresolved visibility. Expect `DECLARED` plus `TextSurface.EXTRACTED_TEXT` and unresolved visibility to remain explicit; do not describe it as human-visible rendering or an independently observed capability.
5. Run a state/currentness mismatch case. Expect economic state construction to reject it.
6. Run existing exact-proposition admission, unauthorized source, attention-only source, evidence span, and FAXT construction regression tests.
7. Confirm the global `FAXT.create` default and an unrelated default-using caller are unchanged.

## Commands (after implementation)

```powershell
`UV_CACHE_DIR` and pytest's temporary directory must be outside the repository so local runs do not pollute the worktree.

```powershell
$env:UV_CACHE_DIR = 'D:\AXIGNAL\.uv-cache'
uv run pytest --basetemp D:\AXIGNAL\Temp\axignal-046-pytest tests/economic_discovery
uv run pytest --basetemp D:\AXIGNAL\Temp\axignal-046-pytest tests/contracts/test_evidence_admission.py tests/contracts/test_faxt_requires_admission.py tests/contracts/test_observed_vs_potential.py tests/contracts/test_eb02_identity_representation.py tests/source_representation/test_document_representation.py
uv run ruff format --check application/economic_discovery/first_vertical_e2e.py tests/economic_discovery/test_first_vertical_e2e.py tests/economic_discovery/test_first_vertical_e2e_adversarial.py
uv run ruff check application/economic_discovery/first_vertical_e2e.py tests/economic_discovery/test_first_vertical_e2e.py tests/economic_discovery/test_first_vertical_e2e_adversarial.py
uv run mypy --cache-dir D:\AXIGNAL\Temp\axignal-046-mypy
git diff --check
```
git diff --check
```

Root confirmed the pre-implementation baseline as 1341 passing tests and eight governance checks. Run the focused economic tests and evidence-admission contracts first; root owns the full required gates and final convergence.
