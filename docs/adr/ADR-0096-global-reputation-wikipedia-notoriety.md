# ADR-0096: Global reputation: public notoriety from Wikipedia, identified by official website

**Status:** Proposed (needs CTO acceptance before integration).
**Date:** 2026-10-13
**Authority:** MASTER §15.4 (UNKNOWN ≠ FALSE), §20 (temporality), §21 (observability), §54 (public representation; attention is not opinion); Constitution; ADR-0014/0015 (instrument and version on every measurement); roadmap phase B (`docs/product/AXIGNAL_GLOBAL_FAMILY_EXCELLENCE_ROADMAP_2026-10-13.md`).

## Context

Reputation was 0 % in the production baseline across every country. The press index (46 feeds) is national and partial. GDELT DOC 2.0 was evaluated as a global press source and rejected for now: from our network it answered empty for well-known companies and rate-limited aggressively (HTTP 429). It may come back later as an opportunistic source with backoff.

## Decision

1. **Instrument `wikipedia-notoriety-v1`:**
   - Monthly user pageviews of the organization's Wikipedia articles in up to 12 languages, over the last 12 complete months.
   - Source: the Wikimedia REST API, open data, with an identifying User-Agent.
2. **Identity by official website, never by name:**
   - A Wikidata item is accepted only if its official website (P856) belongs to the organization's brand domain.
   - Candidates come from both an exact-website search and a name search. Among the items that match, the one with the most articles is chosen.
   - Homonyms ("Wise", "Alan") are therefore never taken for the organization.
3. **Finding `MENTION:WIKIPEDIA_NOTORIETY`** (reputation family):
   - **OBSERVED**, because both the identity and the measurement are observed.
   - Carries the monthly series, the 3-month trend, the languages, the item and the instrument.
   - Its limitation is explicit: **attention, not opinion or reputation quality.**
4. **Cadence:**
   - Requested on read and refreshed weekly on the source thread.
   - Reads use only stored results; nothing is fetched on the subscriber path.
   - A failure keeps the previous reading.
5. **Timeline:** `reputation.wikipedia_views` and `reputation.wikipedia_languages`.

## Consequences

- Reputation becomes measurable in any country for organizations notable enough to have an article. Organizations without one remain UNKNOWN for this instrument (it is not their absence from the world).
- No personal data: organizations' articles and aggregate counts only.
- Next phase-B work: wider governed press feeds per country, review platforms where terms allow, and INXIGHTs crossing notoriety with GEO and press.
