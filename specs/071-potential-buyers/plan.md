# Plan and architecture review

## Inspection
Graphify and source inspection identify the first-observation read path (`tools/runtime/first_observation.py::view`) as the boundary. Every enrichment of a subscriber view happens there:
- awards;
- the value chain;
- groups;
- notoriety;
- job boards.

## Placement
The new derivation goes after the value chain and before INXIGHT crossings:
- **Domain module** `application/potential_buyers`: pure and deterministic. It builds signals from discoveries, combines them per organization, applies exclusions and orders by independent kinds.
- **Pipeline** `pipeline/potential_buyers/wikidata.py`: a world-level cached lookup (customer by exact name; peers by industry and country) run on the source thread, following the notoriety reader pattern.
- **Runtime** `_with_potential_buyers`: reads portfolio peers only through the same tenant's store, and customer groups through the existing GLEIF reader.
- **MCP**: one read-only tool over the same view.
- **Web**: one renderer for the finding and one for the unknown.

## Constitution check
PASS by design:
- no canonical writes;
- no identity admission;
- no provider or LLM dependency;
- no personal data;
- no score;
- the procurement source is not special-cased.

Required gates do not depend on the network: Wikidata is injected and faked in tests.
