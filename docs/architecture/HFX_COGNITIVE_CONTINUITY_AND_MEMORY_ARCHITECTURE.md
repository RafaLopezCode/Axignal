# HFX Cognitive Continuity, Provenance & Context Architecture

**Status:** target architecture recommendation; pre-implementation  
**Authority:** subordinate to MASTER, Constitution, ADR-0017 and existing Xeed/AXIGLAND contracts  
**Scope:** continuity/provenance, Xeed-context access, consultancy routing and retrieval boundaries  
**No runtime, schema, database selection or migration is defined here.**

## Objective

Support a returning user asking what they were investigating, why it entered
attention, what remained open, what AXIGNAL knew then, what changed and where
the evidence is. Reduce reconstruction without cloning AXIGLAND, inventing
provenance, leaking another client's private context or using similarity as
authority.

## Three separate authorities

```text
AXIGLAND                  shared canonical economic truth
XEED GERMINATION CONTEXT  tenant/client/Xeed research process and authorized private refs
PRIVATE COGNITIVE STATE   user/client/Xeed attention and investigation continuity
```

These authorities are related, not interchangeable. Xeed process state is not
a second company profile. Private attention is not economic truth or a
psychological profile. Public knowledge still enters AXIGLAND only through the
existing EvidenceAdmission path. Attention can direct permitted projection or
research; it cannot establish truth. This is consistent with
[`AXIGNAL_BRAIN_XEED_GERMINATION_ARCHITECTURE_V2.md`](AXIGNAL_BRAIN_XEED_GERMINATION_ARCHITECTURE_V2.md),
which distinguishes public-observable, derivable and private/non-observable
territories; private internal economics remain `UNKNOWN_PRIVATE` absent a
separately governed private-context capability.

## Continuity and provenance semantics

```text
COGNITIVE_CONTINUITY = where was I / what was open / what changed?
COGNITIVE_PROVENANCE  = why was I there / what triggered attention?
```

Candidate meaningful events are investigation opened/resumed/paused, question
opened/resolved, material object focused, comparison started, material evidence
inspected and material change acknowledged. Do not record every click, hover,
mouse movement or scroll as memory. Conversation text is not the continuity
model.

An `AttentionOrigin` points only to an actually persisted trigger, object,
question, signal or explicitly stated human reason. A generated explanation is
not an origin record. If origin is absent, expose `UNKNOWN`; do not infer a
plausible story from later state.

A checkpoint is a compact then-state reference, not a clone of the economic
database. Where rights and retention permit, it can identify capture time,
active investigation/question, canonical object/revision refs, Xeed revision,
epistemic states and unresolved questions, evidence the person inspected,
comparison conditions and a concise resume summary. Current state is compared
with the checkpoint by deterministic references/diff. Later knowledge never
rewrites historical `UNKNOWN` or `POTENTIAL`. AXENT may verbalize recorded
origin and computed delta, never invent either. If history, rights or evidence
are unavailable, state that limitation.

## Multi-client Context Router

```text
TENANT → CLIENT_CONTEXT → XEED → INVESTIGATION_THREAD / OBJECT
```

For an agency, `tenant_id` alone is insufficient. `client_context_id` is a
private security and semantic boundary distinct from canonical
`organization_id`. Default retrieval stays in the active client. Portfolio
scope requires explicit request, permission and clear user-visible scope.

Every future private AXENT request resolves a server-side envelope equivalent
to:

```text
ContextEnvelope {
  tenant_id, acting_user_id, client_context_id,
  active_xeed_id?, active_organization_id?, investigation_thread_id?,
  current_object_ref?, projection?, period?, geography?,
  scope_mode, authorized_client_contexts?, permissions,
  route_source, context_version
}
```

This is conceptual, not a frozen type. URL values and model output are hints,
never authorization. Resolve and authorize the envelope before retrieval, then
provide AXENT only the minimum structured context.

Route precedence:

1. Explicit authorized client/Xeed in UI/session.
2. Valid thread already bound to that context.
3. Explicit user-named client, if permitted and unambiguous.
4. Resolve human phrase inside the already authorized context.
5. Ask concise disambiguation without changing scope.

Only explicit, authorized portfolio intent expands client set. Never retrieve
all tenant-private data and filter afterward. Portfolio results attribute each
client and avoid spilling its raw private memory into another client view.
Deep links reauthorize tenant, client, Xeed, thread and object server-side.
Every request/response carries a context version. A client switch invalidates
old requests; delayed Client A responses cannot render in Client B.

## AXENT Context Broker boundary

AXENT has no unrestricted database credentials, direct database access or
arbitrary SQL tool. Future typed broker operations may include:

```text
resolve_context
get_xeed_germination_state / get_research_frontier
get_investigation_thread / explain_attention_origin
get_then_state / get_current_state / get_changes_since / compare_then_now
resolve_human_reference / search_private_cognitive_memory
get_axigland_projection / get_evidence_trace
portfolio_list_material_changes / portfolio_compare
```

Each operation receives a validated envelope and returns structured results
with scope and source refs. Any future writes use deterministic application
commands (open/pause investigation, record an explicit reason, checkpoint,
acknowledge change). Model text does not insert arbitrary memory.

## Fuzzy reference resolution

For “aquello de Francia,” search stays inside the active authorized scope:

```text
authorized envelope
 → exact object/thread/ref
 → structured filters and full-text candidates inside scope
 → vector similarity inside scope, only if needed
 → deterministic client/Xeed/object/date validation
 → resolve one candidate or ask for disambiguation
```

Similarity is a locator, never authorization, identity, causality, historical
ordering or epistemic authority. Ambiguity does not switch clients; the model
must not be expected to ignore another client's retrieved rows.

## Storage and search direction: hypothesis, not selection

The CTO source pack proposes PostgreSQL as structured authority, pgvector as an
auxiliary/rebuildable fuzzy retrieval index and object storage for permitted
large/raw artifacts. This is an **architectural recommendation to benchmark**,
not a canonical database/vendor selection. It is plausible given the existing
relational direction and avoids a second search authority before measured need.

Before implementation, benchmark tenant/client cardinality, exact and
approximate recall, filtered ANN behavior, RLS, deletion, provenance path
traversal, latency, write volume, retention and operational cost. Official
PostgreSQL documentation says RLS needs applicable policies and is default-deny
when none applies, while table owners usually bypass policies unless forced and
privileged roles need separate treatment. RLS alone is not a complete threat
model. Official pgvector documentation warns approximate-index filtering occurs
after index scanning and selective filters can yield fewer results. Enforce
scope deterministically and test it with the actual query/index plan. Exact
scoped search is a candidate for small corpora; no physical algorithm is chosen.

Do not add a separate vector store, graph database, Elasticsearch/OpenSearch or
Redis/Valkey without measured need. Relational edges and recursive SQL are a
starting candidate for provenance paths; benchmark before selecting a graph
store. Embeddings, if separately authorized, inherit source scope, retention,
deletion/offboarding and privacy restrictions. They are rebuildable derived
indices. No embedding generation or pgvector extension is authorized here.

## Future security, privacy and deletion tests

- Client A cannot retrieve Client B cognitive or Xeed-private state.
- Client A scoped vector search cannot rank/return Client B entries.
- Portfolio retrieval requires explicit intent, authorization and clear scope.
- Client switch invalidates old responses before render.
- Deep links reauthorize all private context; URLs are not trusted.
- Private Xeed/cognitive writes cannot create public truth; admission is required.
- Historical checkpoints do not change when current knowledge changes.
- Unknown attention origin remains unknown in AXENT wording.
- Memory and derived embeddings can be deleted/locked on request, expiry,
  offboarding or permission change.
- Clicks are not used to infer sensitive psychological traits.

These are future contract tests, not implemented safeguards or evidence of
runtime capability.

## Architecture review answers

| Question | P0-HFX-00 answer |
|---|---|
| Reconstruct why investigation began? | Only from actual origin/trigger data and within retention; otherwise `UNKNOWN`. |
| Distinguish then from now? | Target: immutable checkpoint/revision refs plus deterministic comparison; completeness depends on retained history/rights. |
| AXENT access to Xeed safely? | Typed broker after envelope authorization; runtime not implemented. |
| Isolate 100 consultancy clients? | `client_context_id` is mandatory private scope; 100-client workload remains unbenchmarked. |
| Explicit safe portfolio? | Explicit request, permission, allow-listed clients, visible scope and result attribution. |
| Fuzzy recall without vector authority? | Scope-first hybrid retrieval and deterministic validation; similarity never authorizes. |
| Start with PostgreSQL + pgvector? | Plausible initial evaluation recommendation, not selected or benchmarked. |
| Need a graph DB? | Not established; relational edges/recursive queries are candidates. |
| Need separate vector DB? | Not established; defer without measured need. |
| Delete/offboard cognitive memory? | Must propagate to derived indices; no runtime mechanism exists yet. |
| Prevent private memory contaminating canonical truth? | Evidence admission remains write authority; future tests must prove runtime. |
| AXENT without arbitrary SQL? | Yes; typed broker is target; SQL tool is prohibited. |

## Non-goals

No database schema/table, migration, RLS policy, pgvector extension, embedding,
vector/graph store, event pipeline, runtime router/broker, AXENT tool, API, UI,
dashboard, provider, analytics tracker or deployment is created by this document.
