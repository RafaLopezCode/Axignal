# AXIGNAL Adversarial Re-Audit Delta — 2026-10-04

**Scope:** repository remediation delta for the frozen 2026-10-03 adversarial architecture audit.  
**Authority:** MASTER PRODUCT MODEL → Engineering Constitution → accepted ADRs → implementation/tests.  
**Production claim:** none. This document closes the repository remediation gate; deployment remains separately verifiable.

## Frozen evidence integrity

The original audit evidence was not edited. SHA-256 values verified immediately after the repaired current-main replay:

| Artifact | SHA-256 |
| --- | --- |
| `reproduce.py` | `1805b67948566d50227dedf463d6634160a01b8a87dbdb73de97dbd5a6836c15` |
| `results.json` | `3289d8ac2af10c81bfa2e5a636824ef3a53359011775a7eb8f8efcd473ef6d0c` |
| `source.zip` | `a30ccbc68567a3a5d5898a350d87151a824fc78305aa2ec6ece60c1d82d6c66f` |
| original audit report | `0dabf7810b3de46a61636fdb0a5b91bbd73f33658dfa769f762e8cedd9816c79` |
| `source-manifest.json` | `3d5fd2d5e47d4d81b3dd01bbaf819a5349ef72e4df1124cf8032032394e1b187` |

The mutable revalidation files remain outside the frozen snapshot:

- `D:/AXIGNAL/.validation/adversarial-audit-2026-10-03/reproduce-current-main.py`
- `D:/AXIGNAL/.validation/adversarial-audit-2026-10-03/results-current-main.json`

## Finding delta

| Finding | Re-audit result | Repaired boundary |
| --- | --- | --- |
| AUD-01 Proposition-Bound EvidenceAdmission | **REPAIRED** | admission is cryptographically/proposition bound; stale decisions cannot authorize changed evidence |
| AUD-02 Canonical Construction / Relationship Admission | **REPAIRED** | OBSERVED relationship materialization requires compatible canonical admission |
| AUD-03 Claim-Kind Governed OBSERVED Projection | **REPAIRED** | business OBSERVED projection requires claim-kind-compatible canonical support |
| AUD-04 Exact Explainable Basis / Narrative Verification | **REPAIRED** | narrative must match governed considered material, exact summaries/types/versions and graph refs |
| AUD-05 Tenant/Reuse Authorization Before Narrative Access | **REPAIRED** | private evidence authorization precedes material resolution and cross-tenant projection fails closed |
| AUD-06 Temporal Currentness Propagation | **REPAIRED** | currentness is derived as-of at consumption; aged evidence cannot masquerade as current |
| AUD-07 Fiscal Evidence Verification / As-Of Gate | **REPAIRED** | fiscal positive state requires exact binding, CAS-verified evidence and effective as-of human approval |
| AUD-08 Legacy Evidence Identity Replay Conflict | **REPAIRED** | exact replay is idempotent; same evidence ID with altered immutable content fails closed |
| AUD-09 CI Cognitive/Authority Coverage | **REPAIRED** | GitHub CI runs the complete deterministic pytest testpath and guards collection of negative authority cases |
| AUD-10 Sensitive URL / Public Source Reference | **REPAIRED** | sensitive public URLs fail before dispatch/persistence; redirects reauthorize; public refs redact historical contamination while preserving safe query semantics |

## Current-main replay

The mutable replay harness was updated from “reproduce the vulnerable semantics” to “verify the repaired semantics”.

Against the AUD-10 repaired worktree it returned:

```
AUD-01 PASS
AUD-02 PASS
AUD-03 PASS
AUD-04 PASS
AUD-05 PASS
AUD-06 PASS
AUD-07 PASS
AUD-08 PASS
AUD-09 PASS
AUD-10 PASS
all_pass = true
```

The harness is rerun against canonical `main` after integration; the exact integrated SHA is recorded in `results-current-main.json`.

## Closure

No original audit finding is left UNKNOWN at repository level. This does **not** claim that these changes are deployed in production.

The adversarial remediation execution gate is therefore eligible to close once the final full deterministic repository validation and canonical-main replay succeed.
