# ADR-0030 — Prime Execution Composition Root

**Status:** Accepted
**Date:** 2026-09-30
**Authority:** MASTER §§14, 46, 53, 56.13–56.20; ADR-0025 through ADR-0029.

## Context

Observation Memory, governed acquisition, representation, semantic candidates, Prime routing, Xeed Bootstrap, Research Value and Learning Memory existed as bounded capabilities. The Frontier audit correctly identified that AXIGNAL still lacked one application composition root proving those organs can execute as one governed Brain path.

## Decision

Introduce `application/economic_discovery/prime_execution.py` as the smallest application composition root for one governed source-to-Prime slice.

The composition starts from an `AuthorizedXeedOrganization`, never raw subscriber-provided organization identity, and composes:

- governed source acquisition through an application-owned port;
- Observation Memory ingestion;
- deterministic document representation through an application-owned port;
- RichSubjectState compilation and exact state delta;
- optional grounded semantic extraction through an application-owned port;
- Prime planning/routing;
- Research Value decisions already bound to gaps;
- Execution Budget authorization before every routed work item;
- provider-neutral mechanism executor ports;
- append-only Learning Memory events and an exact execution trace.

`COMPOSITION ROOT != NEW TRUTH AUTHORITY`

`EXECUTION TRACE != AXIGLAND`

`EXECUTOR OUTPUT != EVIDENCE`

`PORT != PROVIDER`

## Binding and lineage

The root fails closed when Xeed/Organization, source request/policy, source observation, representation, semantic result, or state identities do not match.

The trace retains source request, source observation fingerprint, immutable artifact reference, representation id/fingerprint, rich-state fingerprint, optional semantic extraction/result fingerprints, Prime plan, budget stop reason and causal Learning Event ids.

Each execution receives an explicit `execution_id`. Learning-event identities are scoped to that execution so a real retry is a new operational event rather than an id collision.

## Budget and failures

Every executable Prime work item must pass the FR-03 Budget Controller immediately before dispatch. A STOP writes a PARTIAL Learning Memory event and prevents later work in that run.

Acquisition, representation, semantic-extraction and Prime-executor failures are recorded as FAILED Learning Memory events before the exception is re-raised. NO_CHANGE source/state replay is also recorded and does not re-execute Prime.

## Adapter direction

The application layer owns ports. Concrete adapters remain outside it:

- `HttpSourceSensor` satisfies the source-acquisition port;
- `HtmlDocumentRepresentationAdapter` wraps the deterministic HTML representation pipeline;
- `CognitiveSemanticExtractionAdapter` bridges the cognition router/job normalization to the semantic-extraction port;
- future deterministic/structured/adaptive mechanism executors may be swapped behind the same application port.

The composition root does not import provider SDKs or concrete cognition providers.

## Legacy semantic flow

`application/xeed_germination/semantic_flow.py` is explicitly isolated as a legacy governed experimental path. It is not imported or called by the Prime composition root. Its direct Retrieve→Investigate→EvidenceAdmission path is retained only for existing experiments/tests until a later slice deliberately retires or migrates it.

## Non-goals

FR-04 does not yet produce subscriber-facing Xignals or the `Show how AXIGNAL knows` projection; FR-05 and FR-06 own those outputs. It does not deploy production services and does not select a production evaluator/provider.

## Consequences

AXIGNAL now has one inspectable application-level execution path connecting the previously separate organs without weakening domain authority or provider replaceability. Future runtime/product work can extend this root instead of constructing a second orchestration stack.
