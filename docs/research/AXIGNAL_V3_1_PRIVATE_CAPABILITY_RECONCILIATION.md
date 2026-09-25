# AXIGNAL V3.1 Private Capability Reconciliation

**Record type:** Product/architecture reconciliation evidence
**Product:** AXIGNAL V3 — Private Cross-Intelligence
**Document state:** Proposed doctrine; pre-implementation
**Authority:** Subordinate to the MASTER, Engineering Constitution, accepted
ADRs, Atlas and accepted product/architecture authorities
**Baseline:** `b15211bb1cd8f85aa0e74d4827e9b6201c80d921`

This record explains why V3.1 changes the proposed private-access experience.
It is not an independent product authority, architecture decision, provider
selection, implementation plan or evidence that runtime exists.

## Before reconciliation

The canonical V3 product specification (document version 1.0) already defined
Private Cross-Intelligence as a tenant-scoped analytical plane, with public /
private separation, vendor-neutral capability concepts, contextual
connection, minimum privilege, Private AEAP, provenance, revocation, retention
concerns and a full-value release gate. It did not explicitly say that V3 may
start without private connections, directly enter Ask AXENT after an explicit
V3 request, investigate before asking, reuse sufficient authorization, model
intent approval separately from provider authorization, or pause and resume
the originating analysis branch. Its connection language could be read as an
integration-first “Connect your company” step.

At the baseline, the repository had no V3 Spec Kit feature directory. Existing
feature directories were `001-axigland-graph-design`,
`002-source-acquisition-bakeoff`, `003-subscriber-experience-interaction` and
`004-p0-admin-observability`. No competing V3 feature was created during this
reconciliation. The canonical V3 spec and the existing interaction contract
catalogue are the relevant targets; the latter now has one subordinate C16
contract.

## Gap and reconciliation

| Gap | Change | Reason |
| --- | --- | --- |
| Entry could be read as connection-first | State direct Ask AXENT entry after explicit V3 request/purchase; private access is not a start prerequisite | Preserve customer choice and begin with evidence already available |
| No explicit investigate-first criterion | Tie a required private capability to a material Private Analytical Question / Knowledge Frontier gap and Research Planner evaluation | Do not ask for access because a provider happens to exist; do not create a duplicate gap engine |
| Access routing and epistemic authority were not separated in one contract | Define Required Private Capability, request, capability routing, authorization routing, discovery, adapter and projection responsibilities | AXIGNAL owns analytical meaning; infrastructure routes access only |
| Intent, provider grant, incremental scope and reuse lacked explicit states | Distinguish customer intent from provider verification; define access states, scope checks and no silent expansion | A connection does not grant all scopes and authorization is not evidence |
| Permission interaction was underspecified | Specify contextual inline Card, read-only/minimum scope, exclusions, decline and continuation; modals are exceptional | Keep the analytical reason in context and avoid mandatory integration setup |
| Access could interrupt or lose the analysis | Preserve the original branch continuation; pause only that branch and resume when capability is available | Customer should not restart V3; independent work can continue |
| Privacy, revocation and Admin references needed a unified boundary | Specify minimization, secret exclusion, operational references and separation of revocation from retention/deletion | Lifecycle observability must not expose private content or invent data policy |
| Friction ambition could be mistaken for a measured result | Define candidate lifecycle telemetry without thresholds or “zero friction” claims | Measurement requires definitions and observations first |

The V3 spec advances from document version 1.0 to 1.1 and adds §44. The
product generation remains V3; the spec remains `PROPOSED`,
`PRE_IMPLEMENTATION`, and `FULL_VALUE_ONLY`. The Subscriber Interaction
Architecture receives a minimal additive reconciliation and its contract
catalogue receives C16. Admin spec, Admin architecture and Admin contract
catalogue remain unchanged because they already admit bounded lifecycle
metadata while excluding private content by default. The docs map links this
research record.

Reconciliation result: no conflict was found with the MASTER, Constitution,
accepted ADRs, Atlas, Brain, Knowledge Frontier/Research Planner, Source
Architecture, V2, Subscriber Experience, Interaction Architecture, Admin or
Communication Strategy. The interaction architecture had an underspecified
V3 access lifecycle, not a contradictory invariant; its additive clarification
is subordinate. No new ADR or MASTER change is required, and no authority
escalation is indicated.

## Higher authorities checked

- MASTER Product Model and Engineering Constitution.
- Accepted ADRs 0001–0010, including one canonical AXIGLAND (0001),
  epistemic neutrality (0003), XIGNAL is observation not ownership (0004),
  no CRM/workflow drift (0008), accepted graph architecture (0009) and
  accepted source-acquisition boundary (0010).
- Logical Architecture Atlas, Brain / Xeed Germination Architecture V2,
  architecture overview and canonical terminology.
- AXIGNAL V2 Deep Report / AEAP specification and canonical V3 product spec.
- Subscriber Experience / Ask AXENT product spec, P0-INTERACTION-01
  interaction architecture and contract catalogue.
- P0-ADMIN-01 product spec, Admin Observability Architecture and contract
  catalogue.
- Source Acquisition architecture/bakeoff and active Communication Strategy /
  Living Xeed appendix.

Repository statuses and text were inspected at the authorized baseline. The
MASTER SHA-256 was
`37e734b277c945a0197dfb30097870b1602f6c66efedebb6dd032d39206d47b9`; no
higher authority was modified. The Admin documents and contracts were already
consistent with metadata-only operational observation.

## Why authority is not inverted

V3 remains a private analytical projection over one public AXIGLAND. Private
observations, hypotheses and findings stay tenant-scoped and provenance-distinct.
They may direct analytical attention or motivate new independent public-source
research, but cannot supply public canonical evidence or bypass AXIGLAND's
existing admission policy. Neither authorization broker, capability broker,
provider adapter, model, interaction renderer nor Admin acquires truth
authority. Customer authorization controls access; AXIGNAL controls method;
evidence controls supported conclusions.

Private AEAP derives capability need from its analytical question, while the
existing Knowledge Frontier and Research Planner supply shared gap and
research-priority policy; no duplicate gap/research engine is introduced.
Private AEAP consumes bounded projections and does not become a new public
research engine. Private capability adapters remain distinct from the public
`SourceRequest` / `SourceObservation` acquisition boundary.

## Decisions still open

- Provider-specific supported capabilities, real adapter coverage and the
  full-value status of any integration.
- Exact authorization protocol and mechanism, provider discovery interface,
  credential custody, callback validation and revocation enforcement design.
- Cloud and local/on-premise adapter implementation and any future name for a
  local access component.
- Exact data retention, deletion, derived-finding and report lifecycle policy.
- Concrete schemas, APIs, event transport, database, queue, workflow engine,
  hosting and observability transport.
- Metric definitions, denominators, sampling, targets and empirical friction
  or value results.
- Any implementation technology or release validation. V3's full-value gate
  remains specified and not validated.

## Provider examples and external facts

Provider and capability labels appearing in V3 (including commerce, CRM,
analytics or knowledge-system examples) illustrate domain-neutral capability
shapes only. This reconciliation makes no current factual claim about a
provider API, OAuth support, MCP support, platform restriction, coverage or
production connector. No provider documentation research was needed because
the contract remains provider-neutral. Example names do not establish an
adapter commitment or implementation.

## Implementation and Spec Kit status

The repository search at baseline found no existing V3 Spec Kit feature. No
new feature directory was created; therefore there are no V3 `spec`, `plan`,
`data-model` or `tasks` artifacts to reconcile. The existing product spec,
research record and subordinate interaction contract capture this
documentation-only decision. Future work must create or update a governed
Spec Kit feature only under its own authorized scope. No task is marked
complete and no runtime is authorized.

**Runtime changes:** none. **Production dependencies:** none. **Database
migrations:** none. **Admin semantics:** unchanged. **V3 implementation:**
pre-implementation.
