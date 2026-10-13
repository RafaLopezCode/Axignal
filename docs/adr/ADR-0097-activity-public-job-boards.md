# ADR-0097: Activity and markets from the organization's public job board

**Status:** Proposed (needs CTO acceptance before integration).
**Date:** 2026-10-13
**Authority:** MASTER §15.4, §16.5 (observed ≠ potential), §20, §21; Constitution; ADR-0014/0015; roadmap phase B.

## Context

Activity was 0 % in the production baseline. Organizations everywhere publish their openings through applicant-tracking vendors, and those vendors offer open, unauthenticated board APIs for embedding the openings on the organization's own careers page.

## Decision

1. **Discovery on its own site.** The site reader records a public job board only when the organization's pages link or embed it, as `VENDOR:token`. The board is therefore the organization's own declaration, so its findings are **DECLARED**.
2. **Supported vendors:** Greenhouse, Lever, Ashby, Workable, Recruitee, SmartRecruiters and Personio. Teamtailor is recognised as a hiring channel but is not read (no public API).
3. **Minimal fields:**
   - Title, location, country, and a function label.
   - **A department label is kept only when it names a function** (multilingual function vocabulary); otherwise it is stored as `OTHER`. Some boards place a recruiter's name in that field, and a person's name is never stored.
   - Descriptions are never kept.
4. **Findings:**
   - `OPERATING_SIGNAL:OPEN_POSITIONS` (activity): count, functions, countries and sample titles.
   - `DECLARED_LOCATION:HIRING_IN_COUNTRIES` (markets): an operating presence, or the intention of one.
   - Stated limitation: *a posting is an intention to hire, not a hire.*
5. **Cadence:** every 3 days on the source thread; reads use stored results only; one board per organization, so openings are never counted twice.
6. **Timeline:** `activity.open_positions` and `markets.hiring_countries`.

## Consequences

- Activity and Markets gain a strong, dated, global signal. A live check found Alan with 119 openings (FR, ES, BE), Octopus Energy with 149 (GB, DE, IT, FR, ES, US, CN, JP) and Ekimetrics with 38 (FR, HK, US, CN, GB).
- Organizations without a public board stay UNKNOWN for this instrument.
