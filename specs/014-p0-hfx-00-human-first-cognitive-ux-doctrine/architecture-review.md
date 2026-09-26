# Architecture Review: P0-HFX-00

## Decisions reviewed

- Human First is a product capability; its meaning is in MASTER §55 and
  ADR-0016.
- AXIGLAND, tenant/client/Xeed germination context and private cognitive
  continuity are distinct authorities; ADR-0017 records that boundary.
- AXENT gets minimum typed context only after deterministic authorization.
- Private client scope is resolved before exact, text or semantic retrieval.
- PostgreSQL + pgvector is a plausible initial evaluation direction only. No
  physical persistence choice is made without representative workload,
  filtering/security and deletion benchmarks.
- No runtime/schema/UI/provider is implemented or selected.

## Explicit review questions

| Question | Answer and evidence boundary |
|---|---|
| Can AXIGNAL reconstruct why an investigation began? | Only from actual origin/trigger records within retention; absent evidence stays UNKNOWN. |
| Can then-state differ from now-state? | Target checkpoint/revision references and deterministic diff preserve historical uncertainty; completeness depends on retention/rights. |
| Can AXENT access Xeed context safely? | Through typed broker operations after resolving tenant/client/Xeed/user authorization; no runtime exists in this slice. |
| Can a consultancy isolate 100 clients? | The contract requires client_context_id in every private query; 100-client performance is not measured and remains a future benchmark. |
| Are portfolio queries explicit and safe? | Explicit intent, permission, allowed client set, distinct visible scope and result attribution are required. |
| Can fuzzy recall avoid vector search becoming authority? | Yes in target design: exact/structured/text first, scoped vector only as locator, deterministic candidate validation. |
| Can the system start with PostgreSQL + pgvector? | Plausible architecture hypothesis, not selected. Validate RLS roles, vector filtering/recall and workload first. |
| Is a graph DB required? | Not established; recursive relational traversal is the initial candidate. |
| Is a separate vector DB required? | Not established; introduces an authority/sync boundary without measured need. |
| Can cognitive memory be deleted/offboarded? | Future storage must propagate deletion/retention to derived indexes; no implementation is claimed. |
| Can private memory contaminate truth? | Canonical FAXT remains EvidenceAdmission-only; future tests must prove runtime isolation. |
| Can AXENT function without arbitrary SQL? | Yes, typed Context Broker operations are the target and arbitrary SQL is disallowed. |

## Threats and controls

| Threat | Required future control |
|---|---|
| Client A row/embedding returned in Client B view | Scope envelope, service authorization, RLS and deterministic negative tests; vector retrieval scoped before ranking. |
| Model chooses tenant/client or expands scope | Router ignores generated identifiers; authorize every route; explicit portfolio permission. |
| Stale Client A response rendered after switch | Context generation/version invalidates stale response. |
| Historical UNKNOWN replaced by current knowledge | Immutable checkpoint/revision refs plus deterministic comparison. |
| AXENT invents why user followed item | Provenance query only; missing origin is UNKNOWN. |
| Private Xeed/context writes canonical truth | No private write path to canonical authority; EvidenceAdmission gate. |
| Embeddings outlive source or client offboarding | Derived data inherits source scope/retention/deletion; future deletion tests. |
| ANN filtering undermines recall or isolation assumptions | Official pgvector post-filter caveat; benchmark exact/approximate and enforce auth independently. |

## Resolution

The target architecture is coherent with MASTER, Constitution, ADR-0009 and
Xeed architecture when its physical database claims remain hypotheses and its
records remain conceptual. Any future implementation needs a separate
authorized slice, schema/security review, performance test and explicit data
retention/deletion design.
