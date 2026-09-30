# P0 — Governed HTTP Source Observation Runtime

**Status:** IMPLEMENTATION SLICE
**Authority:** MASTER §56.1–§56.2 and Observation Memory doctrine; ADR-0010; Engineering Constitution.

## Objective

Implement the first replaceable deterministic source sensor that can acquire one explicitly authorized public HTTP(S) target, preserve exact acquisition lineage and raw material, persist the result in Observation Memory, and route its actual state impact into the existing cognitive-loop planner.

## Required behavior

- AXIGNAL owns SourceRequest, SourceObservation and dispatch policy semantics.
- Source policy MUST be resolved before any network operation.
- Each request is bound to the exact policy id and policy fingerprint.
- Only explicitly authorized host/path/scheme targets may be dispatched.
- IP literals, localhost, non-public DNS answers, non-standard or scheme-mismatched ports, fragments, layered/unsafe path encodings and dot-segment escapes fail closed.
- Every redirect is independently re-authorized before dispatch.
- The transport connects to the exact public IPs validated by policy, eliminating DNS re-resolution between authorization and connection.
- Response bytes and deadlines are bounded.
- Raw bytes are retained in an immutable content-addressed store.
- The immutable observation envelope preserves request, exact policy snapshot/fingerprint, instrument, time, redirect lineage, connected peer IPs, response metadata, body artifact/fingerprint and failure state.
- SourceObservation has no truth authority.
- A bound source observation enters Observation Memory and produces a StateChange only through deterministic normalized fields.
- Bound subject observations bypass semantic retrieval and flow to the existing dependency-aware Brain planner.

## Non-goals

No crawler, browser renderer, semantic extractor, robots/terms policy engine, JEV call, canonical EvidenceAdmission write, scheduler, queue, production database, deployment or broad internet crawl is authorized by this slice.

The stdlib pinned HTTP transport is a replaceable baseline adapter, not doctrine.

## Security boundary

A denied policy or unauthorized initial target performs no DNS or network work. Redirects may not widen authority. Network failures and HTTP failures are explicit observation outcomes; they are never converted to FALSE business facts.

## External smoke

A bounded smoke against `https://example.com/` was attempted from the authorized Windows workstation. It failed closed at DNS resolution because that workstation could not resolve external DNS. No external HTTP connection was made. This is recorded as `BLOCKED_ENV_DNS`, not a runtime PASS or product failure.
