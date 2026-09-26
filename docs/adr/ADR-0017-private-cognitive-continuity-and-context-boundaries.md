# ADR-0017: Cognitive Continuity and Xeed Context Are Private Authorities Separate From AXIGLAND

- **Status:** Accepted target architecture boundary; pre-implementation
- **Date:** 2026-09-26
- **Authority:** MASTER §55; Engineering Constitution XX and XXI; existing Xeed architecture
- **Scope:** cognitive continuity/provenance and governed AXENT context routing

## Context

Long-running investigations need a person to recover what they were doing,
what remained open, what was known then and what changed. A list of pages or
transcript replay is not a structured continuity contract. An origin narrative
must not be invented when it was not recorded. Xeed germination has private
process context; a consultancy may hold many client contexts in one tenant.
Attention, process state and public economic truth have different authorities.

## Decision

Keep these three authorities distinct:

```text
AXIGLAND                  shared canonical economic truth
XEED GERMINATION CONTEXT  tenant/client/Xeed research process and private refs
PRIVATE COGNITIVE STATE   user/client/Xeed investigation/attention history
```

AXENT may read authorized context from each only through a deterministic,
typed Context Broker after resolving scope. Canonical public truth still enters
AXIGLAND through EvidenceAdmission. `UNKNOWN` attention origin remains
unknown. Historical checkpoints are not overwritten with current knowledge.

For consultancy retrieval, `tenant_id → client_context_id → xeed_id →
investigation_thread/object` is the target boundary. Client scope is default;
portfolio scope requires explicit user intent and authorization. Neither
embeddings nor model output may select scope, bypass RLS or silently switch
clients. AXENT receives no direct database credentials or arbitrary SQL.

Private cognitive memory is task/context state, not a psychological dossier.
No click-derived sensitive profiling is allowed. Retention, deletion,
offboarding and derived-index cleanup must be designed together.

## Alternatives considered

- **Treat Xeed process or attention as private AXIGLAND:** rejected; creates a
  competing or user-authored canonical truth source.
- **Use chat transcripts/browser history as continuity:** rejected; does not
  reliably encode then-state, open questions, provenance or structured scope.
- **Tenant-only retrieval:** rejected for multi-client consultancies because it
  does not distinguish private client contexts.
- **Retrieve all tenant data, then let the model filter:** rejected; model
  filtering is not authorization.
- **Vector similarity as routing/authority:** rejected; similarity cannot prove
  scope, identity, cause or truth.
- **Direct model SQL:** rejected; typed operations are auditable, bounded and
  deterministic.

## Persistence direction and explicit non-decision

PostgreSQL structured authority with an auxiliary pgvector retrieval index is a
plausible initial architecture recommendation from the CTO source package and
the existing relational direction. Official PostgreSQL RLS and recursive
queries and pgvector's exact/approximate retrieval are relevant capabilities;
RLS role behavior and approximate-index post-filtering require careful testing.
No HFX workload, cardinality or performance benchmark has selected that stack.

Therefore this ADR **does not select a database or extension**. A future
implementation slice must benchmark tenancy/client isolation, exact/approximate
retrieval, recursive provenance traversal, deletion, latency, volume, privacy,
retention and operational cost before choosing PostgreSQL/pgvector or adding a
separate vector/graph/search store.

## Consequences

- A future ContextEnvelope is resolved and authorized before any private read.
- Deep links reauthorize server-side; context-version changes invalidate stale
  in-flight responses.
- Typed broker operations provide minimum structured results with provenance.
- Future tests must prove client isolation, portfolio authorization,
  checkpoint integrity, unknown-origin behavior and private-to-canonical
  non-contamination.
- Cognitive state and any derived embedding inherit source privacy, retention,
  deletion and offboarding rules.

## Risks and rollback

Incomplete revision retention may limit exact then-state reconstruction. Missing
provenance is represented as unknown. If the authority boundary proves
operationally inadequate, revise through a superseding ADR; do not collapse
private state into canonical truth as a shortcut.

## Non-goals

No table, migration, RLS policy, pgvector extension, embedding, vector DB, graph
DB, broker/router runtime, AXENT tool, UI, provider or deployment is authorized.
