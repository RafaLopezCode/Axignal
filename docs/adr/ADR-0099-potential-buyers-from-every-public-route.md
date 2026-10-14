# ADR-0099: Potential buyers from every public route, each signal kept apart

**Status:** Proposed. Needs CTO acceptance before integration; the CTO asked for it on 2026-10-14.
**Date:** 2026-10-14
**Authority:**
- MASTER §1 (not a CRM), §11 (knowledge frontier: "potential customer C?"), §53.3 (opportunity is derived, POTENTIAL, never a lead), rules 37, 47 and 48.
- AGENTS.md: opportunity is POTENTIAL by default; do not special-case TED or a country source; no opaque score.
- ADR-0012 (Economic Opportunity Intelligence).
- ADR-0087 (only a registry admits identity).
- ADR-0095 (MCP: interpret everything).
- ADR-0097 (job boards).

## Context

Subscribers value most one thing: finding organizations that could buy what they offer. Until now AXIGNAL derived buyers only from public procurement (TED and PLACSP):
- recurrent public buyers of its codes;
- competitors' public buyers;
- companies winning public contracts in sectors that buy from its sector.

That covers the public sector of a few countries. Most of a B2B subscriber's buyers are private organizations that never publish a tender. AXIGNAL already reads other public signals that point to them, but used them only to describe the observed organization:
- clients shown on websites;
- corporate groups (GLEIF);
- industry and country (Wikidata);
- the subscriber's own portfolio.

## Decision

1. **One derived finding per candidate.** Each candidate gets one `DEMAND / POTENTIAL_BUYER` finding.
   - The candidate is an organization, never a person.
   - It carries every signal that points to it, each with its own source, date and route (`via`).
   - Its epistemic state is always POTENTIAL: not a customer, a lead, a relationship nor a probability.
2. **Signal types, strongest first.**

   | Signal | Meaning | Source |
   |---|---|---|
   | `CUSTOMER_OF_COMPETITOR` | It buys this activity from someone else | A public award to a competitor, or a client shown on the website of a same-activity organization in **the same subscriber's** portfolio |
   | `PUBLIC_BUYER_OF_CATEGORY` | It keeps awarding contracts under this activity's codes | Public awards |
   | `GROUP_OF_CUSTOMER` | The ultimate parent of an existing customer, or one of its subsidiaries in the subscriber's countries (amendment v1.1) | GLEIF Level 2 |
   | `SIMILAR_TO_CUSTOMERS` | Same industry (P452) and country (P17) as its customers; not dissolved | Wikidata |
   | `SECTOR_BUYS_FROM_ITS_SECTOR` | Active nearby in a sector that usually buys from its sector | Eurostat input-output, public awards |

   Public procurement is one route among several, not the centre.
3. **No score.** Candidates are ordered by how many *independent kinds* of signal agree, then by the strongest kind, then by the order each source gave. Nothing is summed into a number.
4. **Exclusions.** These are never candidates:
   - the organization itself and its group;
   - its declared clients and partners;
   - its public buyers and contract partners.
5. **A customer's name is not an identity.**
   - A name from a logo wall or an award is looked up in Wikidata by exact label or alias, ignoring legal form.
   - It is accepted only when exactly one *organization* item matches (one with an industry or an LEI).
   - Ambiguous names are recorded and not used.
   - The match only routes the search for groups and lookalikes. It never admits identity and never creates a relationship.
6. **Tenant isolation.** Portfolio peers are read only from the same tenant's own observations. World lookups (Wikidata, GLEIF) are cached at world level; they are public CC0 data and carry no tenant information.
7. **Cost and currentness.**
   - Wikidata lookups run on the source thread and are refreshed monthly. Reads use only what is stored.
   - GLEIF groups use the existing weekly cache.
   - Bounds per read: 50 portfolio peers, 8 customers, 3 customer profiles and 3 customer groups.
8. **Absence is UNKNOWN.** With no route available, one `NO_BUYER_SIGNALS` unknown explains why. It never says there is no demand.
9. **Surfaces.**
   - The Demand family on the web.
   - `get_potential_buyers` in the subscriber's web MCP: read-only, tenant-scoped, and AXIGNAL's own LLM is never called.

## Consequences

- Buyers become visible for private, B2B and non-EU subscribers. That depends on their customer profile being visible: clients on their website, public awards, or same-activity organizations in their portfolio.
- A subscriber that adds its competitors to its portfolio gets their declared clients as signals. This is an honest reason to observe more organizations.
- Name matching is strict. "Naturgy" and "Naturgy Energy Group" stay two candidates rather than risk merging distinct entities.

## Not decided here (later phases)

- **v2:** grants and subsidies, register events (new companies, capital increases), physical establishments (OpenStreetMap).
- **v3:**
  - regulatory and press triggers;
  - technology seen on websites;
  - hiring by candidates (job boards, ADR-0097);
  - non-EU procurement (USAspending/SAM, Find a Tender, CanadaBuys, AusTender).

Each new route enters as a new signal type with its own ADR line, licence and limitation.

## Amendment v1.1 (2026-10-14, after the golden-set measurement)

The first measurement found wrong candidates; see `docs/research/excellence/potential-buyers-golden-2026-10-14.md`. Three changes:

1. **Badges are not clients.** On client walls, badges, awards, ratings, review sites, social links and policy labels are rejected. A wall that is mostly such items is dropped entirely. The same check applies at read time, so observations stored earlier stop producing such "customers" at once.
2. **Peers share a specific activity.** Two portfolio organizations are peers only if they share at least one CPV class (four digits, below division level) in addition to the industry. A shared broad sector is not enough.
3. **A customer's group stays bounded.** Only the ultimate parent and the subsidiaries in the subscriber's own countries are signals. With no countries known, only the ultimate parent is.

## Amendment v1.2 (2026-10-14): a route that needs no visible customer

The v1.1 measurement found that 25 of 30 organizations show no customer, so the customer-based routes cannot fire for them. `SECTOR_BUYS_FROM_ITS_SECTOR` gains a global source.

- **Buying sectors.**
  - Up to 3 sectors that buy most from the organization's sector, according to the Eurostat input-output table.
  - Its own sector is excluded (those organizations compete with it).
  - Final uses and public sectors are excluded; public buyers come from awards.
  - Each sector buys at least 2% of its output.
- **Its own sector.** Read from the register activity or CPV activity, or else from its Wikidata industry (P452), translated through NACE.
- **Its countries.**
  - The jurisdictions where its demand is watched, and countries stated on its website.
  - Otherwise, its Wikidata country (P17).
  - At most 2 countries.
- **Organizations in those sectors.**
  - Wikidata industries are matched by their NACE Rev. 2 code (P4496): the exact division first, then its subdivisions. The map is built monthly on the source thread.
  - Organizations are searched by industry (P452) and country (P17).
  - Only current organizations with a website or an LEI are kept.
  - The most documented come first (number of Wikipedia articles). This is an inspectable order, not a judgement of fit.
  - Sectors alternate, up to 8 organizations each.
- **What it is and is not.** These candidates have the lowest strength and a single signal. They say that a sector buys, not that this organization has a need. They rise in the list only when another route agrees.
