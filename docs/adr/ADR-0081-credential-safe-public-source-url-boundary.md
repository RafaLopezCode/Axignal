# ADR-0081 — Credential-Safe Public Source URL Boundary

**Status:** ACCEPTED  
**Date:** 2026-10-04  
**Scope:** AUD-10; public source acquisition; redirects; provenance/sourceRefs  
**Derives from:** MASTER provenance/privacy doctrine; ADR-0076 narrative authorization; source-acquisition policy

## Context

Public source acquisition previously authorized host/path/scheme and rejected URL userinfo, but it did not classify credential-like query parameter names. The complete request URI, redirect locations and final URI could therefore reach source-observation CAS metadata, FirstProof persistence, Observation Memory/Basis and subscriber-visible source references.

A credential-bearing URL is not appropriate public provenance merely because its host and path are otherwise authorized.

At the same time, ordinary public query parameters such as locale, page or view can be semantically relevant and must not be discarded indiscriminately.

## Decision

AXIGNAL separates acquisition eligibility from public provenance rendering.

### New public acquisition

HTTP(S) acquisition rejects a URI before DNS/fetch when it contains:

- URL username/password;
- credential-like query parameter names, including canonical token/key/password/secret/signature forms and governed suffix variants.

Classification examines normalized parameter names only. Secret values are never included in rejection reasons.

Safe query parameters remain unchanged, including ordering and raw encoding.

### Redirects

Every redirect target must pass the same policy gate before it becomes part of persisted lineage.

A rejected redirect URI is neither fetched nor appended to `redirect_chain`, and it cannot become `final_uri`. The last successfully authorized URI remains the persisted final source.

### Public provenance rendering

`public_source_reference()` is the defensive projection primitive for HTTP(S) source references.

For legacy or otherwise pre-existing contaminated references it:

- removes userinfo;
- removes credential-like query pairs;
- removes fragments;
- preserves non-sensitive query parameters;
- preserves non-HTTP(S) governed references unchanged.

This is defense-in-depth; new sensitive acquisition is rejected rather than silently sanitized and fetched.

### FirstProof

FR-30 validates URL privacy before creating a persisted first-proof session.

Sensitive targets fail before session persistence. Valid safe query parameters remain present in the stored target and visible provenance/sourceRefs.

FirstProof also applies public-source projection to source catalog, Basis, Observation reuse metadata and NarrativeMaterial.

### EvidenceNarrative

Subscriber source steps defensively apply the same public-source reference projection. A coherent historical record containing a sensitive query can therefore remain traceable without exposing the credential material.

Narrative source verification remains strict: source identities must still match across authorized Observation Memory, Basis and governed NarrativeMaterial before projection.

## Invariants

```
PRIVATE_ACQUISITION_LOCATOR != PUBLIC_SOURCE_REFERENCE
CREDENTIAL_QUERY != PUBLIC_PROVENANCE
REJECTED_REDIRECT != PERSISTED_LINEAGE
SAFE_QUERY_PARAMETER != SECRET
ERROR_REASON != SECRET_VALUE
HISTORICAL_CONTAMINATION != VISIBLE_SECRET
```

## Consequences

New credential-bearing public URLs fail closed before network dispatch and persistence.

Safe public query semantics remain observable and reproducible.

Historical provenance can be rendered safely without weakening evidence identity, narrative authorization or artifact integrity checks.
