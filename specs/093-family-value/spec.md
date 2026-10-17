# Feature Specification: What each family is worth, at a glance

**Created**: 2026-10-17

**Status**: Implemented (this PR)

**Input**: CTO, 2026-10-17, point 4 of the agency plan ("A todo SI"). The goal is a per-family value summary for every account, with Demand as one family among ten. An agency following 10 to 20 clients must see in the first minute what AXIGNAL observed in each family, not only demand.

## Census (12 real readings, self-check of 0689030)
- **Demand dominates:** 200 potential buyers and 122 open calls.
- **Thin families:** Activity has only the hiring channel, and Context has one organization with regulation.
- **Unknowns with no family:**
  - `LOCATION_NOT_DECLARED` belonged to no family.
  - A guard written for this spec then found two more: `DEMAND_NOT_ROUTABLE` and `NO_ROUTABLE_DEMAND_QUESTION`.

## What changes
- **"Lo que vale de cada familia"** sits in the Summary view, after "This week, what matters".
  - **One row per family**, in the fixed family order. Each row shows:
    - the family name, which opens the family view;
    - how many findings the family holds (a real count, never a score);
    - the finding to read first, with its epistemic state as text plus a shape.

    The row opens that finding's proof.
  - **The finding is chosen by a fixed, visible order per family** (`FAMILY_VALUE_ORDER` in `lib/observatory.ts`): the family's crossings (INXIGHT) first, then its changes, then its most telling measurements and facts. Ties go to "what matters" first, then the most recent.
    - For example, in Visibilidad an AI answer that does not name it comes before the languages its site publishes.
    - Nothing is generated or scored.
  - **A family with nothing observed:**
    - It names what is not known yet (its grounded unknown), with the UNKNOWN state.
    - If it has no unknown either, it is listed once at the end under "Nothing observed yet", with a link to each family.
    - It never borrows another family's value.
    - Calls set apart as "other possible" (spec 087/092) are never a family's headline.
- **Every grounded unknown has a family**, in Python (`families.py`) and on the web (`observation-families.ts`). A test reads the service's emitted unknown codes and requires both maps to place them identically.

## Doctrine
- No universal score.
- UNKNOWN is never FALSE, and an empty family says so instead of being hidden.
- Each row leads to its proof.
- The summary is a projection of attention, never canonical truth.
- It is shown in the 6 interface languages.
