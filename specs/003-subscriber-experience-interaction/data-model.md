# Conceptual Projection Model

These named concepts describe contract payload meaning only. They are not
database tables, persisted schemas, API wire formats, or evidence that a
runtime exists. Concrete field schemas and retention rules require a later
authorized implementation design.

| Concept | Meaning | Authority / relation |
|---|---|---|
| Canonical AXIGLAND state | Domain-authoritative economic world and its epistemic/temporal state | Canonical domain authority; not owned by a UI/model |
| Subscriber Projection | Authorized, human-oriented, versioned view of a Xeed and a declared time/scope | Read projection over AXIGLAND |
| Germination State | Actual domain/operational state and event-backed stage of Xeed formation | Producers report state; UX projects it without synthetic completion |
| Attention Item | Candidate material change with reason, interval, lineage, eligibility and explanation references | Deterministic policy projection, not opaque score |
| Temporal View | Scoped state as of an instant/interval, with currentness and known gaps | Preserves historical meaning; does not backfill unknown observations |
| Evidence Trail | Ordered links from discovery/explanation/derivation to FAXTs, evidence and source | Inspectability projection over admitted evidence/derivation |
| Graph/Map View | Question-specific spatial projection of selected economic entities and relationships | AXIGNAL semantic cartography; renderer is mechanical |
| PATHX View | Ordered explainable path and constituent links between endpoints | Must not imply a direct edge unless domain state says so |
| Ask AXENT Request | Question, interaction class, view/selection, authorization scope and minimal structured context references | AXIGNAL builds context; provider receives only authorized minimum |
| Ask AXENT Response | Explanation/analysis with scope, epistemic caveats and inspectable AXIGNAL references | Noncanonical model-assisted output |
| Research Objective | Explicit request for new evidence and bounded question/scope | Enters governed research; user directs attention, not conclusion |
| Claim Review Request | Subscriber dispute/review signal linked to a claim and optional context | Triggers independent reinvestigation, never direct edit |
| Portable Xeed Projection | Versioned, scoped and temporal Markdown/JSON representation with epistemic/source references | Export projection, not canonical authority |
| Product MCP Read Result | Authorized query result from bounded read surface | Query only; no canonical mutation authority |
| Cognitive Telemetry Event | Minimized operational/cost/grounding/outcome observation linked to request policy/version | Operational telemetry; private identifiers protected; UNKNOWN cost retained |
| UX Observation | Interpretable event/measure such as time to evidence inspection or return rate | Observation only; no causal claim without analysis |

## Cross-concept invariants

- A projection carries enough identity, scope, time/currentness and status to
  interpret it without changing the referenced canonical state.
- Authorization is checked before retrieval and before release; every
  downstream projection inherits the permitted account/Xeed scope.
- `UNKNOWN`, absent, empty, stale, denied, contradictory, unavailable and
  failed are distinct states where the distinction is knowable.
- User input can focus attention or request review/research but is not admitted
  evidence or a canonical conclusion.
- Model output and export/agent output cannot write canonical AXIGLAND.
- A cost field with no reliable measurement is UNKNOWN, never zero.
