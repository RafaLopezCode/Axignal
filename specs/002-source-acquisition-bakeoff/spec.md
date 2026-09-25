# Feature Specification: Source Acquisition Bakeoff (Experimental)

**Feature Branch**: `experiment/p0-source-01-acquisition-bakeoff`
**Status**: Experimental research; decision deferred
**Authority**: CTO order P0-SOURCE-01; subordinate to MASTER and Constitution.

## User problem

AXIGNAL needs to learn whether external-source acquisition can support targeted,
iterative research while preserving raw observations and provenance without
giving sources or tools canonical authority.

## Scope

Produce current candidate research, preliminary eligibility classification, an
isolated reproducible synthetic corpus/harness, explicit evidence-yield
definition, hostile-content/source-policy analysis, and a decision-quality
statement of what is and is not established.

## Out of scope

Production Source Router/capability, live third-party crawler integration,
JEV, Luna, Python intelligence stages, canonical persistence/admission
changes, graph runtime, UI, deployment, and unrelated cleanup.

## Acceptance criteria

1. Candidate dossier captures the requested candidate dimensions and sources.
2. Twelve deterministic workload classes are represented without live-site
   scraping, credentials, access-control bypass or source-content reuse.
3. Raw observations preserve source URI/identity, retrieve time, response
   metadata, raw artifact reference/hash, adapter/config provenance and failure.
4. A deterministic Q1 → O1 → structured gap → targeted Q2 → O2 scenario retains
   provenance linkage and creates no FAXT/canonical state.
5. Results distinguish fixture measurements from live measurements and do not
   claim comparative candidate performance absent candidate execution.
6. Source-rights/policy and hostile-content risks are explicit; no product
   dependency or runtime integration is added.
7. If candidate evidence is insufficient, state `DEFERRED` and create no ADR.

## Governing invariants

- `SOURCE != TRUTH`; adapter observations cannot admit canonical evidence.
- Technical fetchability and permission to fetch are distinct.
- Experimental artifacts remain experimental; no candidate engine is approved.
- Candidate libraries remain outside production manifests.
