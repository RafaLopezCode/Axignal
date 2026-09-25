# AXIGNAL Documentation Map

This is a navigation map, not product doctrine. Use it to find current
authority and supporting material.

## Authority / precedence

1. [MASTER Product Model](product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md)
2. [Engineering Constitution](../.specify/memory/constitution.md)
3. [Accepted ADRs](adr/README.md)
4. [Logical Architecture Atlas](architecture/AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md)
5. Active domain strategies
6. Strategy appendices and feature specifications (`../specs/`)
7. Plans, tasks, and implementation documentation
8. Research, experiments, and evidence

Research produces evidence; it does not silently change doctrine. Evidence can
trigger an ADR, strategy revision, or doctrine revision. Its lower normative
precedence does not mean lower evidentiary value. When documents conflict, do
not infer a compromise: use the higher applicable authority and surface the
conflict.

## Product

- The [MASTER Product Model](product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md)
  is semantic authority; its pinned hash is verified by CI.

### Product Specifications

- [AXIGNAL Admin Product Specification](product/AXIGNAL_ADMIN_PRODUCT_SPEC.md):
  Human-first operational, economic, epistemic and commercial governance
  specification for AXIGNAL Admin; PROPOSED / PRE_IMPLEMENTATION. Its active
  filename identifies the current specification; Git history records versions.
  It is subordinate to the MASTER, Constitution, accepted ADRs, and Atlas, and
  does not establish runtime implementation.
- [AXIGNAL Subscriber Experience & Ask AXENT Product Specification](product/AXIGNAL_SUBSCRIBER_EXPERIENCE_ASK_AXENT_PRODUCT_SPEC.md):
  Human-first subscriber interaction specification covering Xeed germination,
  evolution, evidence, progressive disclosure, Ask AXENT, portability and
  Product MCP; PROPOSED / PRE_IMPLEMENTATION. It is subordinate to the MASTER,
  Constitution, accepted ADRs, and Atlas, and does not establish runtime
  implementation.
- [AXIGNAL V2 Deep Report & Executive Analysis Specification](product/AXIGNAL_V2_DEEP_REPORT_EXECUTIVE_ANALYSIS_SPEC.md):
  Proposed full-value analytical product generation over the canonical AXIGLAND;
  PROPOSED / PRE_IMPLEMENTATION. It is subordinate to the MASTER, Constitution,
  accepted ADRs, and Atlas, and does not authorize implementation.
- [AXIGNAL V3 Private Cross-Intelligence Specification](product/AXIGNAL_V3_PRIVATE_CROSS_INTELLIGENCE_SPEC.md):
  Proposed full-value, tenant-scoped private analytical product generation;
  PROPOSED / PRE_IMPLEMENTATION. Private analysis does not create a private
  AXIGLAND or authorize implementation.

## Engineering governance

- The [Engineering Constitution](../.specify/memory/constitution.md) derives
  binding engineering constraints from the MASTER.
- [Governance guides](governance/README.md) cover deterministic CI, Architecture
  Guard, Graphify, and Spec Kit. See also [AGENTS.md](../AGENTS.md).

## Architecture

- The [Logical Architecture Atlas](architecture/AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md)
  describes target responsibilities, not proof of implementation. The
  [overview](architecture/OVERVIEW.md), [terminology](architecture/TERMINOLOGY.md),
  and [P0-ARCH-01 gap ledger](architecture/AXIGNAL_ARCHITECTURAL_GAP_LEDGER_P0_ARCH_01.md)
  explain boundaries and repository-evidenced status.
- The [ADR index](adr/README.md) links decisions by status. [ADR-0009](adr/ADR-0009-axigland-graph-architecture.md)
  is the accepted AXIGLAND graph architecture/design authority;
  [ADR-0010](adr/ADR-0010-axignal-source-acquisition-architecture.md) accepts
  the source boundary but does not authorize a runtime. The [graph decision
  research](research/AXIGLAND_GRAPH_ARCHITECTURE_DECISION.md) and [engine
  bakeoff](research/AXIGLAND_GRAPH_ENGINE_BAKEOFF.md) are supporting evidence.
- [Brain / Xeed Germination Architecture V2](architecture/AXIGNAL_BRAIN_XEED_GERMINATION_ARCHITECTURE_V2.md)
  is a **pre-implementation architecture reference**, subordinate to the
  MASTER, Constitution, accepted ADRs, and Atlas. It has no runtime or canonical
  write authority. **Specified != implemented; documented architecture !=
  runtime evidence.** Provider-specific execution descriptions do not select or
  implement a provider; ADR-0006 governs the replaceable provider boundary.
- [Subscriber Experience Interaction Architecture V0.1](architecture/AXIGNAL_SUBSCRIBER_EXPERIENCE_INTERACTION_ARCHITECTURE_V0.1.md)
  defines proposed pre-implementation contracts for P0-INTERACTION-01. It is
  subordinate to the authorities above; specified != implemented.
- [Admin Observability Architecture V0.1](architecture/AXIGNAL_ADMIN_OBSERVABILITY_ARCHITECTURE_V0.1.md)
  defines proposed, pre-implementation Admin observability boundaries and
  projection semantics. The [P0-ADMIN-01 feature spec](../specs/004-p0-admin-observability/spec.md)
  and [contract catalogue](../specs/004-p0-admin-observability/contracts/observability-contracts.md)
  define its semantic requirements.
  It selects no infrastructure and authorizes no runtime.
- [Structured Decision Intelligence Architecture V0.1](architecture/AXIGNAL_STRUCTURED_DECISION_INTELLIGENCE_ARCHITECTURE_V0.1.md)
  specifies AXIGNAL-owned decision grammar, minimal state compilation,
  deterministic composition and a pre-implementation Decision Laboratory.
  TypeSafe Jev is the proposed initial replaceable evaluator; no SDK, runtime,
  database, provider call or threshold is introduced. See the
  [P0-JEV-01 feature spec](../specs/005-p0-jev-01-structured-decision-intelligence/spec.md)
  and its [contract catalogue](../specs/005-p0-jev-01-structured-decision-intelligence/contracts/decision-contracts.md).

## Communication

- The [Communication Strategy](communication/AXIGNAL_COMMUNICATION_STRATEGY.md)
  is the active working strategy for explaining AXIGNAL to the market. It does
  not override product or architecture doctrine.
- The [Living Xeed / How It Works appendix](communication/AXIGNAL_COMMUNICATION_LIVING_XEED_APPENDIX.md)
  defines a proposed live-demonstration pillar and is subordinate to the
  strategy. It does not document an implemented runtime.

## Research and experiments

- `docs/research/` holds evidence and analysis, not canonical product
  authority by itself. Accepted decisions belong in ADRs.
- [AXIGNAL V3.1 Private Capability Reconciliation](research/AXIGNAL_V3_1_PRIVATE_CAPABILITY_RECONCILIATION.md)
  records the subordinate V3 contextual-access reconciliation and checked
  authorities; it does not authorize implementation.
- [P0-JEV-01 TypeSafe / Jev Research](research/AXIGNAL_P0_JEV_01_TYPESAFE_RESEARCH.md)
  records current official docs, source versions, API/SDK and cookbook evidence,
  and separates vendor facts from AXIGNAL decisions and unproven assumptions.
- [P0-JEV-01 Opportunity Map](research/AXIGNAL_P0_JEV_01_OPPORTUNITY_MAP.md)
  reconstructs current AXIGNAL owners and the proposed family-specific
  decision paths. [Community patterns](research/AXIGNAL_P0_JEV_01_COMMUNITY_PATTERNS.md)
  are recorded as non-authoritative evidence only.
- `experiments/` holds bounded harnesses and raw results.
  Experimental artifacts are not production implementations or architecture
  authority.

## Document classes

| Location | Classification | Status / role |
|---|---|---|
| `product/` | `CANONICAL_PRODUCT_AUTHORITY` | MASTER Product Model |
| `.specify/memory/`, `governance/` | `ENGINEERING_GOVERNANCE` | Binding constraints subordinate to MASTER |
| `adr/` | `ACCEPTED_ARCHITECTURAL_DECISION` | Check status in each ADR |
| `architecture/` | `ARCHITECTURE_REFERENCE` | Atlas, gap ledger, and pre-implementation domain architecture references |
| `communication/` | `ACTIVE_DOMAIN_STRATEGY`, `STRATEGY_APPENDIX` | Strategy is working; appendix is `PROPOSED` |
| `design/` | `ENGINEERING_GOVERNANCE` | Design guidance subordinate to product and architecture authorities |
| `research/` | `RESEARCH_EVIDENCE` | Analysis/evidence; not authority by itself |
| `specs/` | `FEATURE_SPECIFICATION` | Subject to higher authorities |
| `experiments/` | `EXPERIMENTAL` | Non-authoritative harnesses and results |

## Versioning rule

**ACTIVE DOCS = CURRENT AUTHORITY** — **GIT HISTORY = VERSION HISTORY**

Normally keep one current version of each living document in the active
surface. Recover older versions from Git instead of placing obsolete copies
beside it. Keep version metadata in the active document. Exceptions include
ADRs, immutable evidence, dated/versioned research, experiment results, and
provenance-sensitive records.

## Before changing AXIGNAL

Read this map, the MASTER, Engineering Constitution, relevant ADRs, and
`architecture/OVERVIEW.md` plus `architecture/TERMINOLOGY.md`. For architecture
work, inspect Graphify as directed by [its guide](governance/GRAPHIFY.md).
Implementation status comes from source and deterministic tests, not prose or
Graphify alone.
