# AXIGNAL ENGINEERING CONSTITUTION

> **Nature:** Derived, binding, engineering-facing constitution. It is **not** a
> replacement for the product doctrine. The semantic authority is the MASTER
> PRODUCT MODEL. This document only translates that doctrine into enforceable
> engineering constraints.

**Version**: 1.0.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24

## Upstream Authority (READ FIRST)

| Rank | Document | Path | Role |
| --- | --- | --- | --- |
| 1 | MASTER PRODUCT MODEL V2 | `docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md` | Semantic authority. Doctrine. Not negotiable by engineering. |
| 2 | ENGINEERING CONSTITUTION | `.specify/memory/constitution.md` (this file) | Derives constraints from the MASTER. |
| 3 | ADRs | `docs/adr/` | Record engineering decisions; each cites MASTER sections. |
| 4 | FEATURE SPEC | `specs/NNN-*/spec.md` | Per-feature intent. |
| 5 | PLAN / TASKS | `specs/NNN-*/plan.md`, `tasks.md` | Execution detail. |

```
MASTER PRODUCT MODEL
        ↓
ENGINEERING CONSTITUTION
        ↓
FEATURE SPEC
        ↓
PLAN
        ↓
TASKS
        ↓
IMPLEMENTATION
```

**Precedence (FAIL CLOSED):** If any lower-ranked artifact conflicts with a
higher-ranked one, the lower-ranked artifact is wrong. A feature spec, plan, or
task MUST NOT override the MASTER or this constitution. On conflict: stop,
report the conflict, and do not implement. Never weaken a gate to make CI green.

The SHA-256 of the MASTER is pinned in
`docs/product/AXIGNAL_MASTER_PRODUCT_MODEL_2026-09-24_V2.md.sha256` and verified
by `.github` CI. Changing the MASTER requires an explicit, reviewed change to
the pinned hash.

## Core Principles

### I. One Canonical AXIGLAND

There is exactly one canonical, temporal, living economic world: AXIGLAND.
Users never own nodes and never create private versions of reality. No
per-customer duplicate Organization truth may exist. Isolated customer graphs
are FORBIDDEN. (MASTER §3, §7.3, §46.1, §46.13)

### II. Model, Do Not Manage

AXIGNAL models the observable real economy. It does not manage the customer's
business. CRM, pipeline, tasks, tickets, messaging, invoicing, negotiations,
payment escrow, a workflow engine, and general commercial automation are out of
the core. No CRM/workflow-suite drift. (MASTER §2.1, §46.2, §46.37, §48)

### III. Global Ontology, Demand-Driven Materialization

One world model. One canonical graph. Materialization follows demand; absence of
a materialized node is not non-existence. Depth before breadth. (MASTER §3.2,
§8, §46.3, §46.18)

### IV. Epistemic Neutrality (NON-NEGOTIABLE)

> Users may direct AXIGNAL's attention, but never its conclusions.

Perspective is a query, not a permission. Subscription buys observation, not
influence. The map cannot be bought; observation can. Hostile attention must not
poison canonical truth. ACCESS ≠ AUTHORITY; AUTHORITY ≠ TRUTH; USABLE ≠
LEARNABLE. (MASTER §5, §6, §23, §39, §46.4, §46.6, §46.7, §46.8, §46.12)

### V. XIGNAL Is Observation, Not Ownership

XIGNAL assigns persistent computational observation (`ObservationSeed`). It is
not a profile, not a claim, not ownership, and grants no ability to configure
canonical truth. One canonical Organization regardless of how many users Xignal
it. Agencies may Xignal many companies but cannot configure their canonical
truth. (MASTER §4.4, §7, §26, §33, §46.5, §46.14)

### VI. CLAIM ≠ WRITE / Evidence Admission

A claim does not become canonical state automatically. Canonical FAXT and
OBSERVED Relationship state may only be produced through `EvidenceAdmission`. No
direct canonical company-profile editing. Reevaluation, not editing. LLM output
must never perform a canonical write without admission. (MASTER §2.3, §15, §23,
§46.9, §46.10, §46.11)

### VII. FAXT / INXIGHT / PATHX Separation

FAXT is an evidence-backed canonical unit. INXIGHT is derived, explainable
knowledge and must degrade when its evidence goes stale. PATHX is an explainable
economic path and must not be collapsed into a single relationship. FAXT ≠
INXIGHT. Relationship ≠ PATHX. INXIGHT must never be silently treated as FAXT.
(MASTER §4.5, §4.6, §4.7, §17, §18, §46.20, §46.21)

### VIII. Observed ≠ Potential; UNKNOWN ≠ FALSE

Observed evidence outranks inferred compatibility when describing what exists.
A Potential relationship must never be presented or materialized as a real
relationship. UNKNOWN must never be coerced to FALSE. Raw JEV/model confidence
must not become fake user-facing precision. (MASTER §16.2, §16.5, §15.4, §19,
§21, §46.19, §46.22, §46.23, §46.27)

ASCII invariant: `UNKNOWN != FALSE`. `OBSERVED != POTENTIAL`.
`RELATIONSHIP != PATHX`. `FAXT != INXIGHT`.

### IX. Model Provider Abstraction

Foundation models and JEV are replaceable components, not the domain core.
Domain MUST NOT import a concrete model provider. Provider adapters depend
inward through interfaces. Provider-specific model logic in the domain core is
FORBIDDEN. AXENT orchestrates investigation and MUST NOT itself become canonical
truth authority. (MASTER §13, §14, §30, §46.28, §46.29, §46.31, §46.45)

### X. Deterministic Python Owns Truth Mechanics

Python/deterministic code owns normalization, canonicalization, entity
resolution, temporal validity, hard filters, candidate generation, graph
algorithms, PATHX, feature engineering, policies, and synchronization. Models
are not the canonical authority of truth. (MASTER §14, §35, §46.30)

### XI. FIRST_MAP_WOW Is P0; LIVE, Never DONE

FIRST_MAP_WOW is the primary product proof. `MAP_READINESS_GATE` precedes LIVE.
AXIGNAL has no `DONE` state; observation continues. Background compute must
maximize useful information gain. (MASTER §9, §10, §11, §12, §29, §46.15,
§46.16, §46.17, §46.32, §46.33)

### XII. Commercial Neutrality

No pay-to-appear, sponsored truth, boost, or sponsored/pay-to-rank canonical
graph mutation. Sponsor or advertising surfaces (if any) must be structurally
separated from the cartography. Pricing is an economic hypothesis, not an
architectural invariant: €9.95/month with one Xignal and €4.95 per additional
Xignal. (MASTER §27, §32, §39, §46.34, §46.36, §46.41)

### XIII. Thin Integrations, Invisible Infrastructure

AXIGNAL emits knowledge through thin primitives (API, webhooks, export, share).
It must not become HubSpot/Salesforce/Slack/Notion/n8n/Zapier or a workflow
suite. Infrastructure is invisible to normal users. UX semantics precede visual
spectacle. (MASTER §26, §38, §46.38, §46.39, §46.40)

### XIV. Anti-Poisoning by Design

User or agency input defines attention, not canonical state. There is no
`Edit company profile` button. The only canonical-mutation path is evidence
admission after independent investigation and reevaluation. (MASTER §5, §23,
§32, §46.9–§46.12)

### XV. Wrapper Risk Awareness

If AXIGLAND cannot improve independently of foundation-model progress, AXIGNAL
risks being a wrapper. Internal compute efficiency is not itself a moat. Treat
the AGI/model-owner/open-agent-network moat as unresolved. (MASTER §13.4, §30,
§31, §44, §46.42, §46.43, §46.44)

## Canonical Dependency Direction (enforced by Architecture Guard)

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

XIGNAL controls ATTENTION / COMPUTE ALLOCATION. It MUST NOT bypass evidence
admission. AXENT orchestrates investigation; AXENT MUST NOT itself become
canonical truth authority.

## Canonical Terminology (do not rename casually)

`AXIGNAL` (the system) · `AXIGLAND` (the one canonical living economic world) ·
`AXENT` (autonomous investigation agent, not merely a chatbot) · `XIGNAL`
(persistent observation allocation, not ownership) · `FAXT` (evidence-backed
canonical unit) · `INXIGHT` (derived, explainable knowledge) · `PATHX`
(explainable economic path). See `docs/architecture/TERMINOLOGY.md`.

## Architectural Constraints

- Domain packages (`domain/**`) are the innermost layer. They may import only
  the standard library and other `domain` packages.
- `domain/**` MUST NOT import `pipeline`, `cognition`, `apps`, or `tools`.
- Projection / view modules (`domain/pathx`, `domain/inxight`,
  `domain/knowledge_frontier`) MUST NOT write canonical truth.
- `domain/xignal/**` MUST NOT import `domain/organizations/**` and MUST NOT
  expose any Organization mutation.
- Concrete model providers live only under `cognition/providers/` and are
  reached through `cognition/router/` via interfaces.
- No module may import a third-party LLM provider SDK outside
  `cognition/providers/`.
- No `crm`, `workflow`, `sponsored`, `pay_to_rank`, or `advertising` package may
  appear in `domain/`, `pipeline/`, or `cognition/`.

## Deterministic Validation Gates

All required merge gates are deterministic and must pass before merge. Required
gates MUST NOT depend on nondeterministic LLM output. Semantic Graphify
extraction is separate from the blocking structural Graphify check. See
`docs/governance/DETERMINISTIC_CI.md`.

## Governance

- The MASTER supersedes this constitution; this constitution supersedes ADRs,
  specs, plans, and tasks.
- All PRs must pass the deterministic gates in `.github/workflows/ci.yml`.
- Complexity must be justified; never weaken a gate merely to get CI green.
- Architectural drift is rejected by `tools.architecture_guard` and the
  contract tests in `tests/architecture/` and `tests/contracts/`.
- Amendments to doctrine require an explicit CTO change to the MASTER, not to
  this file.
- Report and stop if a requested implementation conflicts with doctrine.

**Version**: 1.0.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
