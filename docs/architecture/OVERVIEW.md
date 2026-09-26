# AXIGNAL Architecture Overview

> Derived from the MASTER PRODUCT MODEL. See
> `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md`.

## Logical target architecture and current implementation

The [AXIGNAL Logical Architecture Atlas](AXIGNAL_LOGICAL_ARCHITECTURE_ATLAS_V0.1.md)
specifies target logical responsibilities, boundaries and loops. It is
subordinate to the MASTER, Engineering Constitution and accepted ADRs; it does
not prove that a described component is implemented. Use the
[P0-ARCH-01 gap ledger](AXIGNAL_ARCHITECTURAL_GAP_LEDGER_P0_ARCH_01.md) for
current status and repository evidence. Source code and deterministic tests,
not architecture prose or Graphify output, establish implementation status.

## Canonical dependency direction

```
PUBLIC / EXTERNAL EVIDENCE
          ↓
       DISCOVERY
          ↓
NORMALIZATION / ENTITY RESOLUTION
          ↓
   EVIDENCE ADMISSION
          ↓
 FAXT / RELATIONSHIP CANONICAL STATE
          ↓
       AXIGLAND
          ↓
 PATHX / INXIGHT / PROJECTIONS
```

`XIGNAL` controls attention and compute allocation. It MUST NOT bypass evidence
admission. `AXENT` orchestrates investigation. `AXENT` MUST NOT itself become the
canonical truth authority.

## Layers

| Layer | Package(s) | May depend on | Must not |
| --- | --- | --- | --- |
| Domain | `domain/**` | stdlib + `domain` | import `pipeline`, `cognition`, `apps`, `tools` |
| Pipeline | `pipeline/**` | stdlib + `domain` | write canonical state directly; skip admission |
| Cognition | `cognition/**` | stdlib + `cognition` | import canonical writers; hard-wire a provider |
| App | `apps/web/**` | query/projection surfaces | write canonical state; expose an edit-profile path |
| Tools | `tools/**` | anything (governance only) | be imported by `domain` |

## Core invariants (enforced)

1. One canonical AXIGLAND; no per-customer Organization truth.
2. `XIGNAL` is observation allocation, never ownership or profile claiming.
3. Canonical FAXT / OBSERVED relationship state only via `EvidenceAdmission`.
4. Observed ≠ Potential; UNKNOWN never becomes FALSE.
5. INXIGHT is derived and explainable; it is never a FAXT.
6. PATHX is an explainable path, never a collapsed edge.
7. FAXT ≠ INXIGHT; Relationship ≠ PATHX.
8. Domain is provider-agnostic; providers depend inward through interfaces.
9. No CRM / workflow / sponsored truth in the core.
10. Reevaluation, not editing.

## Economic intelligence doctrine

AXIGNAL is an observing economic brain, not an economic index. Economic
Opportunity Intelligence and Compounding Economic Intelligence are core
product capabilities; graph/cartographic projections are cognitive substrate,
not the final product. Opportunity is derived and `POTENTIAL` by default, and
procurement/project activity does not establish a customer or relationship.
Economic Reach is capability-specific; geography informs reasoning and does
not reduce a market to an organization's headquarters jurisdiction. Economic
reasoning is typed, explainable and temporally grounded. Reuse preserves
provenance, epistemic state and currentness. See MASTER §53 and ADR-0012/0013.

Digital Representation Intelligence is another target observation capability
over search, generative, social/public conversation and public
reputation/experience surfaces. Every result is bound to an instrument,
version, conditions and time. Reviews, platform ratings and evaluator
classifications remain observations/derivations, not canonical business truth;
private first-party inputs stay tenant-private. RepresentationGap and
ExperienceSignal are conceptual derivations. These are product/architecture
constraints, not proof of implementation. This overview authorizes no DRI
runtime, source integration, score, schema or UI.

## Data model

Conceptual entities (MASTER §36): `Organization`, `FAXT`, `Evidence`,
`Relationship` (Observed / Potential), `PATHX`, `INXIGHT`, `TemporalEvent`,
`ObservationSeed`, `KnowledgeFrontier`. The Python skeleton implements the
boundary-critical primitives; the full ontology is a later milestone (MASTER
§50, P2).

## Repository layout

```
apps/web/                     presentation boundary (no features yet)
domain/
  evidence/                   evidence + admission + epistemic states
  organizations/              canonical organizations
  faxt/                       evidence-backed canonical units
  relationships/              observed / potential relationships
  pathx/                      explainable economic paths
  inxight/                    derived explainable knowledge
  xignal/                     observation allocation (no organization import)
  knowledge-frontier/         known vs unknown boundary
pipeline/
  discovery/ normalization/ enrichment/ entity-resolution/
  evidence/ features/ sync/
cognition/
  jobs/ router/ providers/ batch/
docs/
  product/ architecture/ adr/ governance/
tests/
  architecture/ contracts/ unit/
tools/
  architecture_guard/ governance/
```

## Enforcement

- `tools/architecture_guard` — AST import-boundary and drift guard (blocking).
- `tests/architecture` — repository boundary + guard negative tests.
- `tests/contracts` — runtime invariants (admission, observed/potential, unknown,
  provider abstraction, xignal isolation).
