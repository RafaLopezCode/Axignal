# P0-CORE-01 Reconciliation Research

**Base**: e431e71091d3d1a1e7765bc3d3d2dca36b186230  
**Mode**: Read-only canonical reconciliation

## Canonical questions A–J

| Question | Finding |
| --- | --- |
| A. Organization meaning | Global, observer-independent economic entity in AXIGLAND (domain/organizations/model.py). |
| B. Isolation boundary? | No. It has no tenant/owner fields; tests protect that invariant. |
| C. Separate Tenant? | CTO decision for this slice: yes, Tenant is the private ownership/isolation boundary. Before this decision, no model existed. |
| D. Separate Client? | No current canonical entity. Reserved until delegation/segmentation requires it. |
| E. Tenant/workspace/client/org distinctions | Organization is world identity; Tenant is private boundary; Client context is future; Workspace is presentation; scope is an authorization concept, not a current entity. |
| F. ObservationSeed meaning | Persistent observation/research assignment associated with an Organization; initiated_by is an unverified string. |
| G. Existing lifecycle relation | ObservationSeed references Organization. No established Xeed relation or knowledge-to-Xeed binding exists. FAXT and relationships reference world identities/evidence, not Xeed scope. |
| H. Identity pattern | Existing domain IDs are strings. Use distinct NewType aliases for static separation while preserving string representation. |
| I. Authorization pattern | None exists. EvidenceAdmission governs evidence canonicality, not actor access. CTO supplies the Principal–Tenant membership policy for this slice. |
| J. Persistence | None exists: no repositories, migrations, database or production store. CTO explicitly prohibits creating that subsystem; in-memory test/dev adapter only. |

## Evidence sources

- Executable domain: Organization, ObservationSeed, FAXT, Relationship,
  EvidenceAdmission, EpistemicState and KnowledgeFrontier models.
- Tests: canonical Organization scope, XIGNAL assignment, evidence admission,
  observed/potential separation and UNKNOWN semantics.
- Architecture: MASTER §§3–7 and §55; Constitution IV, VI, XIX–XXII;
  ADR-0017; Xeed germination architecture; Subscriber interaction catalog.
- Graphify query covered Principal, Tenant, Xeed, authorization, persistence
  and existing identity references.

## Authority classifications

| Authority | Before slice | This slice |
| --- | --- | --- |
| Organization identity | Implemented | Reused, typed as OrganizationId |
| Tenant identity | Absent | Domain identity only; no persistence |
| Principal identity | Absent | Domain identity only; no authentication |
| Principal–Tenant membership | Absent | Domain record + application read port |
| Xeed identity/ownership | Contract only | Domain record owned by one Tenant |
| Trusted request context | Absent | Application value object; does not authenticate |
| Authorized Xeed read | Absent | Application boundary checks membership and owner |
| Client/Workspace authority | Future/presentation only | Not implemented |
| Production persistence | Absent | Remains absent |
| Knowledge-to-Xeed binding | Absent | Remains absent |
