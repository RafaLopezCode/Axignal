# ADR-0010: AXIGNAL Source Acquisition Architecture

- **Status:** **PROPOSED**; requires CTO acceptance. No production source
  acquisition implementation is authorized by this proposal.
- **Date:** 2026-09-25
- **Source doctrine:** MASTER §3, §6, §7, §23, §26, §39, §46;
  Engineering Constitution's evidence, epistemic, security, and provider
  boundary rules.
- **Evidence:** `docs/research/AXIGNAL_SOURCE_ACQUISITION_BAKEOFF.md`;
  `experiments/source-acquisition-bakeoff/results/candidate-runtime/latest-candidate-runtime.json`.

## Context

P0-SOURCE-01B compared five isolated Python acquisition runtimes against a
shared loopback-only fixture. All observations crossed the same experimental
request-to-observation boundary. The experiment showed that raw HTTP and
browser acquisition can be composed while retaining request identity and
artifact lineage. Candidate behavior varied materially: browser support,
failure reporting, redirect bounds, and resource use did not converge on one
winner. The fixture is synthetic and does not establish performance or policy
fitness on public sources.

## Decision

Propose that AXIGNAL own the source acquisition contract, source policy,
request identity, provenance, and failure semantics. Third-party tools may
only be replaceable adapters behind that boundary. Keep raw HTTP acquisition
and browser rendering as distinct capabilities so a future policy can request
browser work only when a declared capability need requires it.

No candidate engine is selected by this ADR. The runtime bakeoff remains
`SOURCE_ENGINE_SELECTION=DEFERRED`; all five candidates remain experimental.
This proposal does not authorize live-source access, production dependencies,
robots or rights decisions, semantic extraction, evidence admission, or
canonical mutation.

## Alternatives considered

- **Select a single crawler now:** rejected as unsupported by the synthetic
  fixture, candidate failures, and lack of representative public-source
  evidence.
- **Treat browser automation as the canonical acquisition contract:** rejected
  because it couples HTTP-only requests to browser cost and lifecycle, while
  omitting crawler and policy semantics.
- **Let each library define AXIGNAL observations:** rejected because observed
  field and failure differences would leak vendor-specific semantics upward.
- **Defer the ownership boundary itself:** less consistent with the existing
  AXIGNAL evidence and canonical-truth boundaries; CTO review is still needed
  before this proposed boundary can be treated as accepted architecture.

## Tradeoffs

AXIGNAL must maintain adapters and validate a stable observation contract.
Separating HTTP and browser capabilities permits targeted composition, but
requires explicit escalation policy, independent resource budgets, and
cross-adapter provenance checks. A replaceable boundary adds integration work
and does not make any candidate safe by itself.

## Consequences

- Candidate package dependencies stay in isolated experiment environments.
- Runtime selection requires a follow-up experiment with approved public
  sources, rights and robots policy, real redirect/egress controls, deadlines,
  and representative workloads.
- Raw fetched content remains untrusted evidence material and cannot itself
  update canonical AXIGLAND state.
- Until accepted, this ADR is a proposal and does not supersede the MASTER,
  Constitution, or accepted ADRs.
