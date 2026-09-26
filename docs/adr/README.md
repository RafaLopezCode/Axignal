# Architecture Decision Records

Concise, immutable records of engineering decisions. Each ADR derives from the
MASTER PRODUCT MODEL and cites the sections it derives from.

Precedence: before an ADR, the MASTER; this ADR index is below the Engineering
Constitution (`.specify/memory/constitution.md`).

| ADR | Title | MASTER anchors |
| --- | --- | --- |
| [ADR-0001](ADR-0001-one-canonical-axigland.md) | One Canonical AXIGLAND | §3, §6.1, §7.3, §46.1, §46.13 |
| [ADR-0002](ADR-0002-demand-materialized-graph.md) | Demand-Materialized Graph | §3.2, §3.3, §8, §29, §46.3, §46.18 |
| [ADR-0003](ADR-0003-epistemic-neutrality.md) | Epistemic Neutrality | §5, §6, §23, §39, §46.4–§46.12 |
| [ADR-0004](ADR-0004-xignal-is-observation-not-ownership.md) | XIGNAL Is Observation, Not Ownership | §4.4, §7, §26, §32 |
| [ADR-0005](ADR-0005-faxt-inxight-pathx-separation.md) | FAXT/INXIGHT/PATHX Separation | §4.5–§4.7, §15–§18 |
| [ADR-0006](ADR-0006-model-provider-abstraction.md) | Model Provider Abstraction | §13, §14, §30, §43 |
| [ADR-0007](ADR-0007-deterministic-ci.md) | Deterministic CI | §14, §46.30; Constitution |
| [ADR-0008](ADR-0008-no-crm-no-workflow-drift.md) | No CRM / No Workflow Drift | §2.1, §22, §32, §38 |
| [ADR-0009](ADR-0009-axigland-graph-architecture.md) | AXIGLAND Graph Architecture (**ACCEPTED**) | §3, §8, §16–§18, §20, §24–§26 |
| [ADR-0010](ADR-0010-axignal-source-acquisition-architecture.md) | AXIGNAL Source Acquisition Architecture (**ACCEPTED**) | §3, §6, §7, §23, §26, §39, §46 |
| [ADR-0011](ADR-0011-jev-structured-decision-reconciliation.md) | Jev Structured Decision Reconciliation (**ACCEPTED EXPERIMENTAL ARCHITECTURE**) | §14, §15, §19, §30, §46 |
| [ADR-0012](ADR-0012-economic-opportunity-intelligence.md) | Economic Opportunity Intelligence Is a Core AXIGNAL Capability (**ACCEPTED PRODUCT DOCTRINE**) | §46, §53 |
| [ADR-0013](ADR-0013-compounding-economic-intelligence.md) | AXIGNAL Compounds Governed Economic Intelligence (**ACCEPTED PRODUCT DOCTRINE**) | §46, §53 |
| [ADR-0014](ADR-0014-digital-representation-intelligence.md) | Digital Representation Intelligence Is a Core AXIGNAL Observation Capability (**ACCEPTED PRODUCT DOCTRINE**) | §22, §46, §54 |
| [ADR-0015](ADR-0015-digital-measurement-instruments-and-observation-reuse.md) | Digital Measurements Are Instrument-Bound Reusable Observations (**ACCEPTED MEASUREMENT DOCTRINE**) | §20, §46, §53–§54 |

## Adding an ADR

1. Confirm the MASTER permits the decision; if not, fail closed and report.
2. Create `docs/adr/ADR-####-short-title.md` using the existing format.
3. Cite the MASTER section(s) the decision derives from.
4. Add the row above. `tools/governance` verifies the index and citations.
