# AXIGNAL Adversarial Epistemic Remediation Roadmap — 2026-10-03

**Status:** ACTIVE EXECUTION GATE
**Authority:** MASTER PRODUCT MODEL -> Engineering Constitution -> accepted ADRs -> this remediation plan -> Admin roadmap.
**Source audit:** D:/AXIGNAL/.validation/adversarial-audit-2026-10-03/AXIGNAL_ADVERSARIAL_ARCHITECTURE_AUDIT_2026-10-03.md
**Frozen audit snapshot:** 5d20cc98732e963c95bd097f7fc6175f51b0a444
**Revalidated against:** 3669b7baf4e930c8c2231c7f0084ac244d2accde
**Revalidation evidence:** D:/AXIGNAL/.validation/adversarial-audit-2026-10-03/results-current-main.json

## 1. Why this gate exists

The adversarial audit found 7 HIGH and 3 MEDIUM findings across canonical truth admission, observed/potential boundaries, narrative/provenance, private reuse, temporal currentness, fiscal fail-closed semantics, legacy evidence identity, CI coverage and URL privacy.

The original audit harness was replayed against current main 3669b7b with loopback HTTP checks enabled. All audit assertions still reproduced. AO-24 did not remediate these boundaries.

AO-25 and later premium advisory work MUST NOT build on known broken truth/presentation boundaries.

## 2. Execution policy

- Fix root causes in dependency order.
- Preserve MASTER/Constitution semantics.
- Do not weaken Architecture Guard, governance, tests or negative scenarios.
- Prefer repair over new abstractions.
- Every fix requires a reproducer that fails before and passes after.
- Every task closes with full deterministic repository validation.
- No task is DONE solely because a unit test passes.
- Production deployment is separate from repository closure unless explicitly required.
- The frozen audit artifacts remain immutable evidence; new revalidation outputs use separate filenames.

## 3. Priority and dependency graph

AUD-01 -> AUD-02 -> AUD-03 -> AUD-04
AUD-02 -> AUD-05 -> AUD-06
AUD-01 -> AUD-08
AUD-07 independent HIGH
AUD-09 independent MEDIUM
AUD-05 -> AUD-10

AO-25 is blocked until AUD-01 through AUD-10 are closed and the adversarial harness no longer reproduces the repaired negative behaviors.

## AUD-01 — Proposition-Bound EvidenceAdmission

**Severity:** HIGH
**Status:** DONE
**Depends on:** none

### Completion evidence
- AdmissionDecision now binds deterministic evidence and proposition digests instead of evidence ID alone.
- AdmissionRequest binds exact evidence content, source authority, observed time, subject, predicate, object/value, extracted claim and predicate-authority policy.
- FAXT.create requires proposition-bound admission; evidence-only admission cannot authorize a FAXT.
- SourceAuthority validation is positive/fail-closed and predicate-specific under MASTER §15.3. Unknown authority and unknown predicate policy are rejected.
- claim_proposition must exactly match the normalized extracted evidence claim in this version; semantic judge/model paraphrase is not admission authority.
- Canonical FAXT observed_at cannot diverge from the admitted Evidence observed_at.
- Canonical token is init=False so dataclasses.replace/manual reconstruction does not preserve canonical authority.
- Legacy semantic germination independently performs proposition-bound admission after semantic judgment; erroneous SUPPORTED over contradictory evidence writes zero FAXTs.
- The exact adversarial same-ID/evidence-substitution attack now raises EvidenceAdmissionRequired; unknown runtime authority is not admitted.
- ADR-0072 records this boundary and explicitly leaves relationship/materialization hardening to AUD-02.
- Focused admission/FAXT/germination/consumer/HFX regressions pass; full deterministic gates must pass before integration.

### Problem
Admission currently proves an evidence identity/token, not the exact proposition/content/authority/subject/predicate/value/time being authorized. A prior valid decision can be reused against changed evidence and a different claim.

### Required change
- Make source-authority validation positive and fail-closed.
- Bind admission to an immutable request containing evidence content fingerprint, subject, predicate/value, authority, observed time and applicable policy.
- Consumers must verify the same binding before canonical materialization.
- LLM/support-judge output cannot be sufficient authorization.

### Required tests
- Same evidence_id with altered claim, authority, observed_at, subject, predicate or object/value fails.
- Unknown authority fails.
- Erroneous SUPPORTED model verdict over contradictory/negative evidence cannot produce the positive canonical FAXT.
- Exact replay remains idempotent.

### Acceptance
Current-main audit checks for admission and legacy model-error path no longer reproduce the unsafe behavior.

## AUD-02 — Canonical Construction and Relationship Admission Boundary

**Severity:** HIGH
**Status:** DONE
**Depends on:** AUD-01

### Completion evidence
- FAXT direct constructor is blocked; only FAXT.create can materialize canonical state after exact proposition admission.
- dataclasses.replace cannot manufacture altered canonical FAXTs.
- ObservedRelationship direct construction is blocked and exact create/replay requires Evidence + proposition-bound AdmissionDecision.
- Relationship evidence refs are derived/verified against exact admitted evidence; empty or unrelated refs fail closed.
- Relationship endpoint identity and observed interval are validated; evidence observed_at must fall inside that interval.
- Organization economic profile fields cannot be injected through the ordinary constructor; governed profile materialization accepts only same-subject OBSERVED/CORROBORATED FAXTs.
- INFERRED canonical FAXT cannot support an OBSERVED business subscriber projection.
- Accredited exact relationship replay remains valid.
- AUD-02 adversarial reproduction now blocks all tested bypasses: direct FAXT, unadmitted Organization profile, unrelated relationship decision, empty refs and INFERRED-to-OBSERVED promotion.
- ADR-0073 records the materialization boundary and leaves claim-kind observation governance to AUD-03.

### Problem
Canonical types can be directly constructed and relationships can consume unrelated admission decisions or empty evidence references.

### Required change
- Restrict effective canonical materialization/rehydration to verified factories/boundaries.
- Validate evidence references against the exact admission binding.
- Validate relationship endpoints/type/times and evidence compatibility.
- Prevent inferred canonical FAXT from projecting as OBSERVED.

### Required tests
- Direct unsupported canonical construction rejected at materialization/write boundary.
- Unrelated decision or empty refs rejected for OBSERVED relationship.
- INFERRED FAXT cannot become OBSERVED capability.
- Accredited replay remains valid.

## AUD-03 — Claim-Kind Governed OBSERVED Projection

**Severity:** HIGH
**Status:** DONE
**Depends on:** AUD-01, AUD-02

### Completion evidence
- Direct observation support now resolves through a GovernedObservationSupportResolver instead of trusting bare observation IDs in BasisDatum.
- ObservationSupport carries subject, phenomenon kind, instrument ref/version, scope, provenance, source, observed time and currentness.
- Direct observation policy is claim-kind specific: REPRESENTATION accepts PUBLIC_REPRESENTATION; business kinds do not inherit authority from surface observation.
- SUPPLY + OBSERVED + observation ID + no canonical FAXT now fails closed even when the observation is present in the supporting basis.
- Valid REPRESENTATION support must resolve, match subject/source/time, be CURRENT and carry governed instrument/scope/provenance.
- FR-30 first proof now supplies the resolver from its actual governed SourceObservation and remains OBSERVED for the condition-bound public representation only.
- Missing resolver, stale support and cross-subject support fail closed.
- ADR-0074 records the policy and leaves exact narrative verification to AUD-04.

### Problem
Observation-support IDs can currently authorize business-facing OBSERVED signals even where only a surface representation was directly measured.

### Required change
- Resolve support through a governed support port and explicit policy by claim/dimension kind.
- Direct observations may prove only the phenomenon actually measured.
- Business truths such as supply/capability/relationship require canonical compatible admission.
- Do not whitelist providers as a substitute for semantic authority.

### Required tests
- Commercial supply/capability without admitted FAXT fails even with observation IDs.
- Representation/page observation with instrument/scope/provenance may remain OBSERVED for representation only.

## AUD-04 — Exact Explainable Basis and Narrative Verification

**Severity:** HIGH
**Status:** DONE
**Depends on:** AUD-01, AUD-03

### Completion evidence
- Explainable Basis data can bind exact representation/extraction fingerprints.
- EvidenceNarrative requires a NarrativeMaterialResolver and verifies exact summary, source type/ref, observed time, contribution and material version.
- Resolver considered-evidence ledger makes material contradictions mandatory in the Basis; omission fails closed.
- Relationship and PATHX references require governed graph resolution and authorized subject scope before narrative rendering.
- Altered summary/type/version with unchanged IDs fails.
- Unresolved graph refs fail.
- Exact replay remains deterministic.
- FR-30 now binds narrative to its actual DocumentRepresentation fingerprint.
- ADR-0075 records the boundary and leaves private reuse/currentness to AUD-05/AUD-06.

### Problem
Narrative verifies bytes/IDs but can accept altered semantic summary/type/graph references while presenting a convincing evidence story.

### Required change
- Bind explainable basis to exact stored extraction/content versions.
- Derive or verify excerpt/type/time against stored governed material.
- Resolve relationship/PATHX references against authorized repositories or omit them as unverified.
- Preserve explicit considered-evidence and material-contradiction ledger.

### Required tests
- Altered summary/type with unchanged IDs fails.
- Missing graph refs fail or are omitted as unverified.
- Material contradiction cannot disappear merely because caller omitted it.
- Exact replay remains stable.

## AUD-05 — Tenant/Reuse Authorization Before Narrative Access

**Severity:** HIGH
**Status:** DONE
**Depends on:** AUD-03

### Completion evidence
- NarrativeAccessContext now binds subject, authorized Xeed, tenant, target scope, reuse purpose and as-of time.
- EvidenceNarrative applies the existing ADR-0050 reuse policy before resolving narrative material or artifact content.
- SqliteObservationMemory now provides metadata-only authorization lookup excluding raw content/artifact references; full observation load occurs only after ALLOW.
- Considered-evidence IDs are authorized before NarrativeMaterial is resolved, including contradictions omitted by the caller.
- Different private owner, PROHIBITED, UNKNOWN and RESTRICTED reuse all fail closed.
- Correct private owner + permitted purpose renders evidence explicitly TENANT_PRIVATE.
- TENANT_PRIVATE evidence is rejected for GLOBAL_WORLD projection and has no canonical write path.
- Subscriber narrative does not expose raw_content, raw_artifact_ref or CAS references.
- FR-30 now assigns explicit governed GLOBAL_PUBLIC reuse authority to its public homepage observation instead of relying on the restrictive default.
- ADR-0076 records the access ordering and leaves dynamic temporal aging to AUD-06.

### Problem
Reuse policy can reject tenant-private evidence while evidence narrative still retrieves and exposes it.

### Required change
- Apply scope/rights/currentness authorization before private material retrieval.
- Presentation/reuse context includes tenant, purpose and as_of.
- Public and private evidence remain explicitly separated.
- CAS/raw private artifacts never leak into subscriber payload.

### Required tests
- Different private owner rejected.
- PROHIBITED/UNKNOWN/RESTRICTED reuse rejected.
- Correct owner + permitted purpose may get clearly private projection only.
- No private evidence is promoted to global AXIGLAND truth.

## AUD-06 — Temporal Currentness Propagation

**Severity:** HIGH
**Status:** READY
**Depends on:** AUD-05

### Problem
Temporal aging can classify evidence HISTORICAL while reuse and visible read model still claim CURRENT.

### Required change
- Evaluate effective currentness at consumption time with as_of + policy.
- Reprojection marks visible state stale/historical without mutating historical observation.
- Invalidation propagates only to affected dependencies.
- Historical as-of views remain reproducible.

### Required tests
- 120-day evidence under 30/90 policy cannot be used as current.
- Visible currentness changes under future as_of.
- Historical authorized use remains available.
- New observation restores currentness.
- Old snapshot keeps old as-of meaning.

## AUD-07 — Fiscal Evidence Verification and As-Of Gate

**Severity:** HIGH
**Status:** READY
**Depends on:** none

### Problem
AO-22 can allow live/compliance claim from a complete set of opaque references, including evidence observed in the future relative to projection time.

### Required change
- Evidence must be observed on/before as_of.
- Resolve/verify evidence artifacts and effective human approval.
- Bind selected provider product version, adapter version, ruleset and approval context.
- Provider/version drift invalidates completeness until re-evidenced.
- Registry version is not presumed to equal deployed SIF binary/product version.

### Required tests
- Future evidence, missing artifact, mismatched effective version or absent approval cannot enable claims/live.
- Complete, verified same-version evidence at/before as_of may pass.

## AUD-08 — Legacy Evidence Identity Replay Conflict

**Severity:** MEDIUM
**Status:** BLOCKED
**Depends on:** AUD-01

### Problem
Legacy evidence ledger permits duplicated/contradictory content under reused evidence identity.

### Required change
- Exact replay idempotent.
- Existing evidence ID + different fingerprint -> conflict.
- New observation/version requires new ID.
- Reuse existing persistence; no new storage layer.

### Required tests
- Identical append stores once.
- Same ID with altered claim/time/authority fails.
- New ID preserves history.

## AUD-09 — CI Cognitive/Authority Coverage

**Severity:** MEDIUM
**Status:** READY
**Depends on:** none

### Problem
CI does not prove that all critical cognitive/epistemic suites are collected/executed.

### Required change
- Execute full deterministic suite in CI or explicitly enumerate all required suites with collection coverage validation.
- Permanently include adversarial negative cases.
- Keep network/LLM/provider calls out of deterministic CI.

### Required tests
- Deliberately failing test in each critical suite family causes CI failure.
- Admission mutation, tenant leak, stale currentness and model-error cases are collected.

## AUD-10 — Sensitive URL / Public Source Reference Redaction

**Severity:** MEDIUM
**Status:** BLOCKED
**Depends on:** AUD-05

### Problem
Credential-like query parameters can reach CAS metadata, persisted read models and visible sourceRefs.

### Required change
- Reject credential-bearing public acquisition URLs or separate private locator from redacted public source reference.
- Apply same policy across redirects.
- Preserve semantically useful non-sensitive query parameters.
- Errors/logs must not echo secret values.

### Required tests
- access_token/api_key/password/userinfo never appear in CAS metadata, persisted read model, logs or sourceRefs.
- Allowed public query parameters retain semantics and traceability.
- Sensitive redirects fail closed.

## 4. Closure gate before AO-25

AUD remediation is closed only when:

1. AUD-01 through AUD-10 are DONE.
2. Full deterministic suite, Ruff, mypy, Architecture Guard and governance pass.
3. The current-main replay harness is updated to expected repaired semantics and all negative regressions pass.
4. Frozen original audit evidence remains unchanged.
5. A concise re-audit delta records each finding as repaired or explicitly UNKNOWN.
6. AO-25 is then unblocked and becomes CURRENT_TASK again.