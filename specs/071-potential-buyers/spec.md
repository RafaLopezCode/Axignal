# Potential buyers from every public route (v1)

## Authority
- MASTER §1, §11, §53.3, and rules 37, 47 and 48.
- Constitution.
- ADR-0012, ADR-0087, ADR-0095 and ADR-0099.

## Problem and acceptance
A subscriber wants to know which organizations could buy what it offers. Today, buyers are derived only from public procurement in a few countries.

Acceptance criteria for v1:
- Every candidate is one `DEMAND / POTENTIAL_BUYER` finding, in state POTENTIAL. It lists each signal separately, with its type, basis, route, source and date.
- Signals combine five routes:
  - competitors' public buyers and the clients shown by same-activity organizations in the same tenant's portfolio;
  - recurrent public buyers of its codes;
  - its customers' corporate groups (GLEIF);
  - organizations in its customers' industry and country (Wikidata);
  - sectors that buy from its sector.
- Ordering: number of independent signal kinds, then the strongest kind, then source order. There is no score.
- Never candidates: itself, its group, its clients, its partners, its public buyers or its contract partners.
- Organizations only; no personal data.
- The MCP tool `get_potential_buyers` is read-only and tenant-scoped, and denials fail closed.
- When no candidate can be derived, the finding is `NO_BUYER_SIGNALS`, an UNKNOWN.
- Web copy exists in es, en, de, pt, fr and it.

## Clarifications
- A customer name is looked up in Wikidata only by exact label or alias, and is accepted only when it is unique among organization items. It routes the search; it is not identity admission.
- Portfolio peers count only when their activity reading maps to the same industry.
- Wikidata lookups are asynchronous (source thread) and refreshed monthly. Reads never block on them.
